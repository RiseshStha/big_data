import os
import time
import sys
import pandas as pd


# FILE PATHS

DATA_DIR       = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Data/"
OUTPUT_DIR     = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
PARQUET_PATH   = OUTPUT_DIR + "questions_clean.parquet"


print("STARTING STACKOVERFLOW NLP CLASSIFICATION (PHASE 2)")

global_start_time = time.time()

# Ensure the output directory exists
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Confirmed output directory exists: {OUTPUT_DIR}")
except Exception as e:
    print(f"[WARNING] Could not create output directory: {e}")


# 1. SETUP

print("\n STEP 1: INITIALIZING SPARK & LOADING DATA ")
step_start = time.time()
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, desc, element_at, udf
    from pyspark.sql.types import StringType, DoubleType
    
    # MLlib pipeline and classifier modules
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import StringIndexer, Tokenizer, StopWordsRemover, CountVectorizer, IDF
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator
    
    print("Required PySpark MLlib modules imported successfully.")
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import PySpark MLlib: {e}")
    sys.exit(1)

try:
    # Build SparkSession with the requested properties.
    # We set master local[*] here to automatically multi-thread tree training using all CPU cores.
    spark = SparkSession.builder \
        .appName("SO_Classification") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "100") \
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
        .getOrCreate()
    
    print(f"SparkSession started successfully (Spark Version: {spark.version}).")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to start Spark Session: {e}")
    sys.exit(1)

# Load questions parquet file
print(f"Loading cleaned Questions Parquet from: {PARQUET_PATH}")
try:
    df_raw = spark.read.parquet(PARQUET_PATH)
    questions_count = df_raw.count()
    print(f"Full dataset loaded: {questions_count} rows")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Parquet dataset: {e}")
    sys.exit(1)

print(f"Setup and loading complete in {time.time() - step_start:.2f} seconds.")


# 2. PREPARE LABELS AND STRATIFIED SAMPLE

print("\n STEP 2: PREPARING CLASS LABELS AND STRATIFIED SAMPLING ")
step_start = time.time()
# Note: Using stratified sampling by primary_tag is still highly representative big data,
# while keeping local training execution times computationally feasible!
try:
    TOP10 = ["python","javascript","java","c#","php",
             "android","html","jquery","c++","ios"]
    print(f"Target multi-class tags: {TOP10}")
    
    # Extract the first item in tag_list as the primary label tag
    df_labels = df_raw.withColumn("primary_tag", element_at(col("tag_list"), 1))
    
    # Filter dataset to rows where primary_tag is in TOP10
    df_filtered = df_labels.filter(col("primary_tag").isin(TOP10))
    filtered_count = df_filtered.count()
    print(f"After tag filter: {filtered_count} rows")
    
    # Stratified Sampling:
    # Target: 100,000 rows total (~10,000 per tag)
    print("Calculating sampling fractions per tag...")
    tag_counts = df_filtered.groupBy("primary_tag").count().collect()
    
    fractions_dict = {}
    for row in tag_counts:
        tag = row["primary_tag"]
        count_val = row["count"]
        # target 10,000 rows per tag
        fraction = 10000.0 / count_val
        if fraction > 1.0:
            fraction = 1.0
        fractions_dict[tag] = fraction
        
    print(f"Stratification fractions applied: {fractions_dict}")
    
    # Execute stratified sampling
    df_sampled = df_filtered.sampleBy("primary_tag", fractions=fractions_dict, seed=42)
    
    # Cache the sampled dataset
    df_sampled.cache()
    sampled_count = df_sampled.count()
    print(f"Sampled dataset: {sampled_count} rows (cached)")
    
    print("\nNew class distribution after stratified sampling:")
    df_sampled.groupBy("primary_tag").count().orderBy(desc("count")).show()
    
    print(f"Label prep and stratified sampling complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Stratified sampling failed: {e}")
    sys.exit(1)


# 3. PREPARE FEATURES

print("\n STEP 3: PREPARING FEATURES ")
step_start = time.time()
try:
    # Cast text_length to double
    df_features = df_sampled.withColumn("text_length_double", col("text_length").cast("double"))
    
    # Select feature columns
    df_ml = df_features.select("Id", "text", "primary_tag", "text_length_double")
    
    print("Feature columns selected.")
    df_ml.printSchema()
    print(f"Feature preparation complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Feature preparation failed: {e}")
    sys.exit(1)


# 4. TRAIN/TEST SPLIT

print("\n STEP 4: PERFORMING TRAIN/TEST SPLIT ")
step_start = time.time()
try:
    train, test = df_ml.randomSplit([0.8, 0.2], seed=42)
    
    # Cache split sets
    train.cache()
    test.cache()
    
    train_count = train.count()
    test_count = test.count()
    print(f"Training dataset: {train_count} rows")
    print(f"Testing dataset:  {test_count} rows")
    print(f"Train/Test split complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Train/Test split failed: {e}")
    sys.exit(1)


# 5. BUILD NLP PIPELINE

print("\n STEP 5: BUILDING NLP PIPELINE ")
step_start = time.time()
try:
    # StringIndexer
    indexer = StringIndexer(inputCol="primary_tag", outputCol="label", handleInvalid="skip")
    
    # Tokenizer
    tokenizer = Tokenizer(inputCol="text", outputCol="words")
    
    # StopWordsRemover
    remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")
    
    # CountVectorizer
    countVectorizer = CountVectorizer(inputCol="filtered_words", outputCol="raw_features", vocabSize=32768, minDF=3.0)
    
    # IDF
    idf = IDF(inputCol="raw_features", outputCol="features", minDocFreq=3)
    
    # RandomForestClassifier: numThreads removed as it is not supported in the PySpark API wrapper.
    # The SparkSession is configured with master local[*] which automatically parallelizes 
    # tree building across all CPU cores.
    rf = RandomForestClassifier(
        numTrees=50,
        maxDepth=10,
        labelCol="label",
        featuresCol="features",
        seed=42,
        subsamplingRate=0.8
    )
    
    # Assemble stages
    pipeline = Pipeline(stages=[indexer, tokenizer, remover, countVectorizer, idf, rf])
    
    print("Pipeline built successfully.")
    print(f"Pipeline construction complete in {time.time() - step_start:.4f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Pipeline assembly failed: {e}")
    sys.exit(1)


# 6. TRAIN MODEL

print("\n STEP 6: TRAINING RANDOM FOREST (estimated 2-5 mins on 100K rows) ")
training_start = time.time()
try:
    model = pipeline.fit(train)
    training_time = time.time() - training_start
    print(f"Training complete! Time elapsed: {training_time:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Model training failed: {e}")
    sys.exit(1)


# 7. PREDICT

print("\n STEP 7: MAKING PREDICTIONS ")
step_start = time.time()
try:
    predictions = model.transform(test)
    predictions.cache()
    
    # Extract indexer labels
    labels = model.stages[0].labels
    prediction_to_tag = {float(i): label for i, label in enumerate(labels)}
    print(f"Label-to-tag dictionary: {prediction_to_tag}")
    
    # Register UDF
    @udf(returnType=StringType())
    def map_prediction_udf(pred):
        if pred is not None:
            return prediction_to_tag.get(float(pred), "unknown")
        return "unknown"
        
    predictions = predictions.withColumn("predicted_label", map_prediction_udf(col("prediction")))
    
    print("\nSample Predictions (15 rows):")
    predictions.select("primary_tag", "predicted_label", "label", "prediction").show(15, truncate=False)
    print(f"Prediction complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Prediction stage failed: {e}")
    sys.exit(1)


# 8. EVALUATE MODEL

print("\n STEP 8: EVALUATING PERFORMANCE ")
step_start = time.time()
try:
    evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction")
    
    accuracy  = evaluator.evaluate(predictions, {evaluator.metricName: "accuracy"})
    f1        = evaluator.evaluate(predictions, {evaluator.metricName: "f1"})
    precision = evaluator.evaluate(predictions, {evaluator.metricName: "weightedPrecision"})
    recall    = evaluator.evaluate(predictions, {evaluator.metricName: "weightedRecall"})
    
    print(f"Accuracy:  {accuracy:.4f}  ({accuracy * 100:.2f}%)")
    print(f"F1 Score:  {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    
    # Save metrics to CSV
    metrics_data = [
        {"metric": "Accuracy", "value": accuracy},
        {"metric": "F1 Score", "value": f1},
        {"metric": "Precision", "value": precision},
        {"metric": "Recall", "value": recall}
    ]
    pd.DataFrame(metrics_data).to_csv(os.path.join(OUTPUT_DIR, "classification_metrics.csv"), index=False)
    print("Saved to classification_metrics.csv")
    print(f"Evaluation complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Evaluation failed: {e}")
    sys.exit(1)


# 9. CONFUSION MATRIX

print("\n STEP 9: GENERATING CONFUSION MATRIX ")
step_start = time.time()
try:
    crosstab_df = predictions.stat.crosstab("primary_tag", "predicted_label")
    
    print("Confusion Matrix:")
    crosstab_df.show(truncate=False)
    
    # Save to CSV
    crosstab_df.toPandas().to_csv(os.path.join(OUTPUT_DIR, "confusion_matrix.csv"), index=False)
    print("Saved to confusion_matrix.csv")
    print(f"Confusion matrix complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Confusion matrix failed: {e}")
    sys.exit(1)


# 10. PER-CLASS ACCURACY

print("\n STEP 10: PER-CLASS ACCURACY ")
step_start = time.time()
try:
    per_class_data = []
    print("Calculating accuracy per class tag...")
    
    for tag in TOP10:
        df_class = predictions.filter(col("primary_tag") == tag)
        total = df_class.count()
        if total > 0:
            correct = df_class.filter(col("predicted_label") == tag).count()
            acc = correct / total
        else:
            correct = 0
            acc = 0.0
            
        print(f"  {tag:<12}: {acc * 100:6.2f}% ({correct}/{total})")
        per_class_data.append({
            "tag": tag,
            "accuracy": acc,
            "correct": correct,
            "total": total
        })
        
    # Save to CSV
    pd.DataFrame(per_class_data).to_csv(os.path.join(OUTPUT_DIR, "per_class_accuracy.csv"), index=False)
    print("Saved to per_class_accuracy.csv")
    print(f"Per-class accuracy calculations complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Per-class accuracy calculations failed: {e}")
    sys.exit(1)


# 11. FEATURE IMPORTANCE

print("\n STEP 11: EXTRACTING FEATURE IMPORTANCE ")
step_start = time.time()
try:
    rf_model = model.stages[-1]
    importances = rf_model.featureImportances.toArray()
    top20_indices = importances.argsort()[-20:][::-1]
    
    cv_model = model.stages[3]
    vocab = cv_model.vocabulary
    
    print("Top 10 Features by Importance:")
    feature_data = []
    for rank, idx in enumerate(top20_indices, 1):
        importance_val = importances[idx]
        word = vocab[idx] if idx < len(vocab) else f"Feature {idx}"
        feature_data.append({
            "rank": rank,
            "feature_index": int(idx),
            "word": word,
            "importance": float(importance_val)
        })
        if rank <= 10:
            print(f"  Rank {rank:2d}: '{word}' (Index: {idx:<5d}, Importance: {importance_val:.6f})")
            
    # Save top 20 to CSV
    pd.DataFrame(feature_data).to_csv(os.path.join(OUTPUT_DIR, "feature_importances.csv"), index=False)
    print("Saved to feature_importances.csv")
    print(f"Feature importance complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Feature importance failed: {e}")
    sys.exit(1)


# 12. EXPORT RESULTS

print("\n STEP 12: EXPORTING SAMPLE RESULTS ")
step_start = time.time()
try:
    results_path = os.path.join(OUTPUT_DIR, "classification_results.csv")
    print(f"Exporting top 5,000 predictions to {results_path}...")
    predictions.select("Id", "primary_tag", "predicted_label", "label", "prediction") \
               .limit(5000) \
               .toPandas() \
               .to_csv(results_path, index=False)
               
    print("Saved to classification_results.csv")
    print(f"Results export complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Results export failed: {e}")
    sys.exit(1)

# Clean cached DataFrames
try:
    df_sampled.unpersist()
    train.unpersist()
    test.unpersist()
    predictions.unpersist()
except:
    pass


# 13. SUMMARY

total_elapsed_time = time.time() - global_start_time
training_minutes = int(training_time // 60)
training_seconds = int(training_time % 60)

print("\n" + "=" * 60)
print(" PHASE 2 COMPLETE ")
print("=" * 60)
print(f"Dataset:")
print(f"- Full dataset:    1,264,216 rows")
print(f"- Sampled to:      {sampled_count} rows (stratified by tag)")
print(f"- Training rows:   {train_count}")
print(f"- Test rows:       {test_count}")
print()
print(f"Model Performance:")
print(f"- Accuracy:        {accuracy * 100:.2f}%")
print(f"- F1 Score:        {f1:.4f}")
print(f"- Precision:       {precision:.4f}")
print(f"- Recall:          {recall:.4f}")
print(f"- Training time:   {training_minutes} minutes {training_seconds} seconds")
print()
print(f"Files saved:")

expected_files = [
    "classification_metrics.csv",
    "confusion_matrix.csv",
    "per_class_accuracy.csv",
    "feature_importances.csv",
    "classification_results.csv"
]

for filename in expected_files:
    filepath = os.path.join(OUTPUT_DIR, filename).replace("\\", "/")
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024.0
        print(f" - [CONFIRMED] {filename:<28} Size: {size_kb:.2f} KB")
    else:
        print(f" - [MISSING]   {filename:<28}")

print(f"- Total pipeline runtime: {total_elapsed_time:.2f} seconds")
print("=" * 60)

# Stop the Spark session cleanly
spark.stop()
print("SparkSession stopped cleanly. Execution finished successfully.")
