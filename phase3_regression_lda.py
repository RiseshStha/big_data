import os
import time
import sys
import pandas as pd
import numpy as np

# Fix Windows console encoding: force UTF-8 to handle Unicode vocabulary
# words extracted from StackOverflow code blocks (e.g., box-drawing chars)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ==========================================
# FILE PATHS
# ==========================================
OUTPUT_DIR   = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
PARQUET_PATH = OUTPUT_DIR + "questions_clean.parquet"

print("=" * 60)
print("STARTING REGRESSION & LDA TOPIC MODELLING (PHASE 3)")
print("=" * 60)
global_start_time = time.time()

# Ensure output folder exists
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Confirmed output directory exists: {OUTPUT_DIR}")
except Exception as e:
    print(f"[WARNING] Could not create output directory: {e}")

# ==========================================
# 1. SETUP
# ==========================================
print("\n=== STEP 1: INITIALIZING SPARK SESSION ===")
step_start = time.time()
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, when, count, avg, round, log1p, expm1, udf
    from pyspark.sql.types import IntegerType, DoubleType
    
    # MLlib Pipeline, Vector, and Feature components
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import Tokenizer, StopWordsRemover, HashingTF, IDF, VectorAssembler, CountVectorizer
    
    # MLlib Algorithms & Evaluators
    from pyspark.ml.regression import LinearRegression
    from pyspark.ml.clustering import LDA
    from pyspark.ml.evaluation import RegressionEvaluator
    
    print("Required PySpark MLlib modules imported successfully.")
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import PySpark MLlib modules: {e}")
    sys.exit(1)

try:
    # Build SparkSession with the requested properties and multi-threading enabled
    spark = SparkSession.builder \
        .appName("SO_Regression_LDA") \
        .master("local[*]") \
        .config("spark.driver.memory", "6g") \
        .config("spark.sql.shuffle.partitions", "50") \
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
        .getOrCreate()
    
    print(f"SparkSession started successfully (Spark Version: {spark.version}).")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to start Spark Session: {e}")
    sys.exit(1)

# Load Questions Parquet dataset
print(f"Loading cleaned Questions Parquet from: {PARQUET_PATH}")
try:
    df_raw = spark.read.parquet(PARQUET_PATH)
    questions_count = df_raw.count()
    print(f"Full dataset loaded: {questions_count} rows")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Parquet dataset: {e}")
    sys.exit(1)

print(f"Setup and loading complete in {time.time() - step_start:.2f} seconds.")


# ==========================================
# TASK — PART A: LINEAR REGRESSION
# ==========================================

# 2. PREPARE REGRESSION SAMPLE
print("\n=== STEP 2: PREPARING REGRESSION DATA SAMPLE ===")
step_start = time.time()
try:
    # Filter for non-negative scores only
    df_filtered_reg = df_raw.filter(col("Score") >= 0)
    filtered_count = df_filtered_reg.count()
    
    # Sample exactly 100,000 rows randomly
    print(f"Non-negative score rows: {filtered_count}. Sampling 100,000 rows...")
    df_sampled_reg = df_filtered_reg.sample(
        withReplacement=False, 
        fraction=min(1.0, 100000.0 / filtered_count), 
        seed=42
    ).limit(100000)
    
    # Transform: Calculate log_score = log1p(Score) and text_length_double
    df_reg = df_sampled_reg \
        .withColumn("log_score", log1p(col("Score").cast("double"))) \
        .withColumn("text_length_double", col("text_length").cast("double"))
    
    # Print describe() for Score and log_score
    print("\nDescriptive statistics for Score and log_score:")
    df_reg.select("Score", "log_score").describe().show()
    
    # Cache regression sample
    df_reg.cache()
    reg_rows = df_reg.count()
    print(f"Regression sample ready: {reg_rows} rows (cached)")
    print(f"Regression prep complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Regression prep failed: {e}")
    sys.exit(1)

# 3. TRAIN/TEST SPLIT
print("\n=== STEP 3: PERFORMING REGRESSION SPLIT ===")
step_start = time.time()
try:
    train_reg, test_reg = df_reg.randomSplit([0.8, 0.2], seed=42)
    
    train_reg.cache()
    test_reg.cache()
    
    train_count = train_reg.count()
    test_count = test_reg.count()
    
    print(f"Training partition size: {train_count} rows")
    print(f"Testing partition size:  {test_count} rows")
    print(f"Split complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Train/Test split failed: {e}")
    sys.exit(1)

# 4. BUILD LINEAR REGRESSION PIPELINE
print("\n=== STEP 4: BUILDING LINEAR REGRESSION NLP PIPELINE ===")
step_start = time.time()
try:
    # Tokenizer
    tokenizer = Tokenizer(inputCol="text", outputCol="words")
    
    # StopWordsRemover with custom extra stopwords
    remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")
    default_stop_words = remover.getStopWords()
    extra_stop_words = [
        "use","used","using","want","need","know","like","get","one",
        "code","file","error","work","make","way","also","would",
        "could","run","try","line","set","value","add","new","see",
        "help","following","example","please","thanks","question"
    ]
    combined_stop_words = list(set(default_stop_words + extra_stop_words))
    remover.setStopWords(combined_stop_words)
    
    # HashingTF (16,384 features)
    hashingTF = HashingTF(inputCol="filtered_words", outputCol="raw_features", numFeatures=16384)
    
    # IDF (minDocFreq = 3)
    idf = IDF(inputCol="raw_features", outputCol="tfidf_features", minDocFreq=3)
    
    # VectorAssembler: Combine TF-IDF features and text_length_double
    assembler = VectorAssembler(inputCols=["tfidf_features", "text_length_double"], outputCol="features")
    
    # Linear Regression Model
    lr = LinearRegression(
        labelCol="log_score",
        featuresCol="features",
        maxIter=10,
        regParam=0.1,
        elasticNetParam=0.5
    )
    
    # Build Pipeline
    pipeline_reg = Pipeline(stages=[tokenizer, remover, hashingTF, idf, assembler, lr])
    print("Linear Regression pipeline built.")
    print(f"Pipeline construction complete in {time.time() - step_start:.4f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Regression pipeline assembly failed: {e}")
    sys.exit(1)

# 5. TRAIN REGRESSION MODEL
print("\n=== STEP 5: TRAINING LINEAR REGRESSION (estimated 2-5 mins) ===")
training_start = time.time()
try:
    model_reg = pipeline_reg.fit(train_reg)
    training_time_reg = time.time() - training_start
    print(f"Training complete! Elapsed time: {training_time_reg:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Regression model fitting failed: {e}")
    sys.exit(1)

# 6. EVALUATE REGRESSION MODEL
print("\n=== STEP 6: EVALUATING REGRESSION PERFORMANCE ===")
step_start = time.time()
try:
    predictions_reg = model_reg.transform(test_reg)
    
    # Convert log-predicted score back to original scale using expm1
    predictions_reg = predictions_reg \
        .withColumn("predicted_score", expm1(col("prediction"))) \
        .withColumn("actual_score", col("Score").cast("double"))
        
    predictions_reg.cache()
    predictions_reg.count()  # Trigger cache write
    
    # Evaluate in log-scale
    evaluator_log = RegressionEvaluator(labelCol="log_score", predictionCol="prediction")
    rmse_log = evaluator_log.evaluate(predictions_reg, {evaluator_log.metricName: "rmse"})
    r2_log = evaluator_log.evaluate(predictions_reg, {evaluator_log.metricName: "r2"})
    mae_log = evaluator_log.evaluate(predictions_reg, {evaluator_log.metricName: "mae"})
    
    # Evaluate RMSE on original scale
    evaluator_orig = RegressionEvaluator(labelCol="actual_score", predictionCol="predicted_score")
    rmse_orig = evaluator_orig.evaluate(predictions_reg, {evaluator_orig.metricName: "rmse"})
    
    print(f"RMSE (log scale):      {rmse_log:.4f}")
    print(f"R² Score:              {r2_log:.4f}  (model explains {r2_log * 100:.2f}% of variance)")
    print(f"MAE (log scale):       {mae_log:.4f}")
    print(f"RMSE (original scale): {rmse_orig:.4f}")
    
    # Save metrics to CSV
    metrics_data = [
        {"metric": "RMSE (log scale)", "value": rmse_log},
        {"metric": "R2 Score", "value": r2_log},
        {"metric": "MAE (log scale)", "value": mae_log},
        {"metric": "RMSE (original scale)", "value": rmse_orig}
    ]
    pd.DataFrame(metrics_data).to_csv(os.path.join(OUTPUT_DIR, "regression_metrics.csv"), index=False)
    print("Saved to regression_metrics.csv")
    print(f"Evaluation complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Regression evaluation failed: {e}")
    sys.exit(1)

# 7. EXPORT REGRESSION RESULTS & BUCKET ANALYSIS
print("\n=== STEP 7: EXPORTING REGRESSION PREDICTIONS & BUCKET ANALYSIS ===")
step_start = time.time()
try:
    # Save top 5000 prediction samples
    pred_sample_path = os.path.join(OUTPUT_DIR, "regression_predictions.csv")
    print(f"Exporting top 5,000 predictions to: {pred_sample_path}")
    predictions_reg.select("Id", "actual_score", "predicted_score", "log_score", "prediction") \
                   .limit(5000) \
                   .toPandas() \
                   .to_csv(pred_sample_path, index=False)
                   
    # Score Bucket Analysis
    print("Performing score bucket analysis...")
    predictions_bucket = predictions_reg.withColumn(
        "score_bucket",
        when(col("actual_score") == 0, "0")
        .when((col("actual_score") >= 1) & (col("actual_score") <= 5), "1-5")
        .when((col("actual_score") >= 6) & (col("actual_score") <= 20), "6-20")
        .when((col("actual_score") >= 21) & (col("actual_score") <= 100), "21-100")
        .otherwise("100+")
    )
    
    bucket_analysis = predictions_bucket.groupBy("score_bucket").agg(
        count("*").alias("count"),
        round(avg("actual_score"), 4).alias("avg_actual"),
        round(avg("predicted_score"), 4).alias("avg_predicted")
    )
    
    # Sort order column helper for printing
    bucket_order = when(col("score_bucket") == "0", 1) \
                  .when(col("score_bucket") == "1-5", 2) \
                  .when(col("score_bucket") == "6-20", 3) \
                  .when(col("score_bucket") == "21-100", 4) \
                  .otherwise(5)
                  
    bucket_analysis_sorted = bucket_analysis.withColumn("order", bucket_order).orderBy("order").drop("order")
    
    print("\nRegression Score Bucket Analysis:")
    bucket_df_pd = bucket_analysis_sorted.toPandas()
    print(bucket_df_pd.to_string(index=False))
    
    bucket_analysis_path = os.path.join(OUTPUT_DIR, "regression_bucket_analysis.csv")
    bucket_df_pd.to_csv(bucket_analysis_path, index=False)
    print(f"Saved to {bucket_analysis_path}")
    print(f"Export and bucket analysis complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Export and bucket analysis failed: {e}")
    sys.exit(1)


# ==========================================
# TASK — PART B: LDA TOPIC MODELLING
# ==========================================

# 8. PREPARE LDA SAMPLE
print("\n=== STEP 8: PREPARING LDA DATA SAMPLE ===")
step_start = time.time()
try:
    # Uncache regression datasets to free local JVM memory
    try:
        df_reg.unpersist()
        train_reg.unpersist()
        test_reg.unpersist()
        predictions_reg.unpersist()
    except:
        pass

    # Load fresh Questions parquet
    df_raw_lda = spark.read.parquet(PARQUET_PATH)
    total_raw_rows = df_raw_lda.count()
    
    # Sample exactly 100,000 rows randomly for topic modeling
    print(f"Sampling 100,000 rows randomly from raw dataset ({total_raw_rows} rows)...")
    df_lda = df_raw_lda.sample(
        withReplacement=False, 
        fraction=min(1.0, 100000.0 / total_raw_rows), 
        seed=42
    ).limit(100000)
    
    df_lda.cache()
    lda_rows = df_lda.count()
    print(f"LDA sample: {lda_rows} rows (cached)")
    print(f"LDA sample prep complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] LDA sample prep failed: {e}")
    sys.exit(1)

# 9. BUILD TEXT PREPROCESSING PIPELINE (fit once, reuse for all k values)
print("\n=== STEP 9: BUILDING TEXT PREPROCESSING PIPELINE ===")
step_start = time.time()
try:
    # Tokenizer
    tokenizer_lda = Tokenizer(inputCol="text", outputCol="words")
    
    # Combined StopWordsRemover for LDA topic modeling
    remover_lda = StopWordsRemover(inputCol="words", outputCol="filtered_words")
    default_stop_words_lda = remover_lda.getStopWords()
    lda_extra_stop_words = [
        "use","used","using","want","need","know","like","get","one",
        "code","file","error","work","make","way","also","would","could",
        "run","try","line","set","value","add","new","see","help",
        "following","example","please","thanks","question","function",
        "class","method","object","return","string","number","data",
        "list","array","type","null","true","false","com","http","www"
    ]
    combined_lda_stop_words = list(set(default_stop_words_lda + lda_extra_stop_words))
    remover_lda.setStopWords(combined_lda_stop_words)
    
    # CountVectorizer (vocabSize=5000, minDF=10.0)
    countVectorizer = CountVectorizer(inputCol="filtered_words", outputCol="features", vocabSize=5000, minDF=10.0)
    
    # Build preprocessing-only pipeline (no LDA yet — k will be determined next)
    preprocessing_pipeline = Pipeline(stages=[tokenizer_lda, remover_lda, countVectorizer])
    preprocessing_model = preprocessing_pipeline.fit(df_lda)
    
    # Transform data once — reuse for all k values
    df_vectorized = preprocessing_model.transform(df_lda)
    df_vectorized.cache()
    df_vectorized.count()  # Trigger cache write
    
    # Extract vocabulary for later topic word lookup
    vocab = preprocessing_model.stages[2].vocabulary
    
    print(f"Preprocessing pipeline fitted. Vocabulary size: {len(vocab)}")
    print(f"Preprocessing complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Preprocessing pipeline failed: {e}")
    sys.exit(1)

# 10. OPTIMAL K SELECTION — Determine the best number of topics (Elbow Method)
print("\n=== STEP 10: FINDING OPTIMAL NUMBER OF TOPICS (k) ===")
print("Testing multiple k values using Log Perplexity and Log Likelihood...")
print("(This is analogous to the Elbow Method in K-Means clustering)")
step_start = time.time()
try:
    k_values = [5, 8, 10, 12]
    k_results = []
    
    for k_val in k_values:
        k_start = time.time()
        print(f"\n  Training LDA with k={k_val}...", end=" ")
        
        lda_test = LDA(k=k_val, maxIter=5, featuresCol="features", optimizer="online", seed=42)
        lda_model_test = lda_test.fit(df_vectorized)
        
        # Compute evaluation metrics on the same vectorized data
        log_perplexity = lda_model_test.logPerplexity(df_vectorized)
        log_likelihood = lda_model_test.logLikelihood(df_vectorized)
        
        k_elapsed = time.time() - k_start
        print(f"Perplexity: {log_perplexity:.4f} | Likelihood: {log_likelihood:.4f} | Time: {k_elapsed:.1f}s")
        
        k_results.append({
            "k": k_val,
            "log_perplexity": log_perplexity,
            "log_likelihood": log_likelihood,
            "training_time_seconds": float(f"{k_elapsed:.2f}")
        })
    
    # Save k-selection results to CSV for documentation/plotting
    k_results_df = pd.DataFrame(k_results)
    k_selection_path = os.path.join(OUTPUT_DIR, "lda_k_selection.csv")
    k_results_df.to_csv(k_selection_path, index=False)
    print(f"\nSaved k-selection results to: {k_selection_path}")
    
    # Select optimal k = the k with the LOWEST log perplexity
    optimal_row = k_results_df.loc[k_results_df["log_perplexity"].idxmin()]
    optimal_k = int(optimal_row["k"])
    optimal_perplexity = optimal_row["log_perplexity"]
    optimal_likelihood = optimal_row["log_likelihood"]
    
    print(f"\n{'=' * 50}")
    print(f"  OPTIMAL k = {optimal_k}  (Log Perplexity: {optimal_perplexity:.4f})")
    print(f"{'=' * 50}")
    
    # Print full comparison table
    print("\nFull k-selection comparison:")
    print(k_results_df.to_string(index=False))
    
    print(f"\nK-selection complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] K-selection failed: {e}")
    sys.exit(1)

# 11. TRAIN FINAL LDA MODEL WITH OPTIMAL K
print(f"\n=== STEP 11: TRAINING FINAL LDA MODEL (k={optimal_k}, data-driven) ===")
training_start = time.time()
try:
    lda_final = LDA(k=optimal_k, maxIter=5, featuresCol="features", optimizer="online", seed=42)
    model_lda = lda_final.fit(df_vectorized)
    training_time_lda = time.time() - training_start
    print(f"Final LDA model (k={optimal_k}) trained in {training_time_lda:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Final LDA model fitting failed: {e}")
    sys.exit(1)

# 12. EXTRACT AND LABEL TOPICS DYNAMICALLY
print(f"\n=== STEP 12: EXTRACTING TOPICS (k={optimal_k}) ===")
step_start = time.time()
try:
    topics_df = model_lda.describeTopics(maxTermsPerTopic=10)
    topics_collected = topics_df.collect()
    
    # Dynamically generate topic labels from top meaningful words per topic
    # (no hardcoded labels — the data decides the topics AND the labels)
    TOPIC_LABELS = []
    
    def safe_word(w):
        """Replace unencodable chars with ? for safe console printing."""
        try:
            return w.encode('ascii', errors='replace').decode('ascii')
        except Exception:
            return '???'
    
    print(f"\nDiscovered {optimal_k} Topics:")
    for row in topics_collected:
        topic_idx = row["topic"]
        term_indices = row["termIndices"]
        term_weights = row["termWeights"]
        
        # Resolve indices to words
        words = [safe_word(vocab[idx]) for idx in term_indices]
        
        # Build a label from top-3 meaningful words (skip single-char/symbol tokens)
        meaningful_words = [w for w in words if len(w) > 2 and w.isalpha()][:3]
        if meaningful_words:
            topic_label = "Topic: " + " / ".join(meaningful_words)
        else:
            topic_label = f"Topic {topic_idx}"
        TOPIC_LABELS.append(topic_label)
        
        words_str = ", ".join(words)
        print("-" * 50)
        print(f"Topic {topic_idx}: [{topic_label}]")
        print(f"  Top words: {words_str}")
    
    print("-" * 50)
    print(f"Topic extraction complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] Topic extraction failed: {e}")
    sys.exit(1)

# 13. EVALUATE FINAL LDA MODEL
print("\n=== STEP 13: EVALUATING FINAL LDA MODEL PERFORMANCE ===")
step_start = time.time()
try:
    transformed_lda = model_lda.transform(df_vectorized)
    transformed_lda.cache()
    transformed_lda.count()  # Trigger cache write
    
    perplexity = model_lda.logPerplexity(df_vectorized)
    likelihood = model_lda.logLikelihood(df_vectorized)
    print(f"Log Perplexity: {perplexity:.4f} (lower = better)")
    print(f"Log Likelihood: {likelihood:.4f} (higher = better)")
    print(f"Evaluation complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[CRITICAL ERROR] LDA model evaluation failed: {e}")
    sys.exit(1)

# 14. EXPORT LDA RESULTS & TOPIC DISTRIBUTION
print("\n=== STEP 14: EXPORTING LDA TOPICS & TOPIC DISTRIBUTION ===")
step_start = time.time()
try:
    # Save Topics terms list
    topic_data_list = []
    for row in topics_collected:
        topic_idx = row["topic"]
        term_indices = row["termIndices"]
        term_weights = row["termWeights"]
        topic_label = TOPIC_LABELS[topic_idx]
        
        for rank, (idx, weight) in enumerate(zip(term_indices, term_weights), 1):
            # Use raw vocab word for CSV (preserves Unicode), safe version for print
            raw_word = vocab[idx]
            topic_data_list.append({
                "topic_number": topic_idx,
                "topic_label": topic_label,
                "word": raw_word,
                "weight": float(weight),
                "rank": rank
            })
            
    lda_topics_path = os.path.join(OUTPUT_DIR, "lda_topics.csv")
    pd.DataFrame(topic_data_list).to_csv(lda_topics_path, index=False)
    print(f"Saved topics breakdown to: {lda_topics_path}")
    
    # Calculate Dominant Topic per question using UDF
    @udf(returnType=IntegerType())
    def get_dominant_topic_udf(distribution):
        if distribution is not None:
            return int(np.argmax(distribution.toArray()))
        return -1
        
    df_dominant = transformed_lda.withColumn("dominant_topic", get_dominant_topic_udf(col("topicDistribution")))
    
    topic_counts = df_dominant.groupBy("dominant_topic").count().collect()
    
    # Assemble topic distribution mapping
    distribution_list = []
    for row in topic_counts:
        topic_idx = row["dominant_topic"]
        if topic_idx != -1:
            label = TOPIC_LABELS[topic_idx]
            distribution_list.append({
                "dominant_topic": topic_idx,
                "topic_label": label,
                "count": row["count"]
            })
            
    df_topic_dist_pd = pd.DataFrame(distribution_list).sort_values("dominant_topic")
    
    print("\nDominant Topic Distribution Table:")
    print(df_topic_dist_pd.to_string(index=False))
    
    lda_dist_path = os.path.join(OUTPUT_DIR, "topic_distribution.csv")
    df_topic_dist_pd.to_csv(lda_dist_path, index=False)
    print(f"Saved topic distributions to: {lda_dist_path}")
    
    print(f"LDA exports completed in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] LDA exports failed: {e}")
    sys.exit(1)

# Unpersist LDA datasets
try:
    df_lda.unpersist()
    df_vectorized.unpersist()
    transformed_lda.unpersist()
except:
    pass

# ==========================================
# 15. FINAL SUMMARY
# ==========================================
total_elapsed_time = time.time() - global_start_time
reg_minutes = int(training_time_reg // 60)
reg_seconds = int(training_time_reg % 60)
lda_minutes = int(training_time_lda // 60)
lda_seconds = int(training_time_lda % 60)

print("\n" + "=" * 60)
print("=== PHASE 3 COMPLETE ===")
print("=" * 60)
print(f"REGRESSION (Linear Regression):")
print(f"- Sample size:          {reg_rows} rows")
print(f"- Training rows:        {train_count}")
print(f"- Test rows:            {test_count}")
print(f"- RMSE (log scale):     {rmse_log:.4f}")
print(f"- R² Score:             {r2_log:.4f} (explains {r2_log * 100:.2f}% of variance)")
print(f"- MAE (log scale):      {mae_log:.4f}")
print(f"- RMSE (orig scale):    {rmse_orig:.4f}")
print(f"- Training time:        {reg_minutes} mins {reg_seconds} secs")
print()
print(f"LDA TOPIC MODELLING:")
print(f"- Sample size:          {lda_rows} rows")
print(f"- K values tested:      {k_values}")
print(f"- Optimal k selected:   {optimal_k} (data-driven, lowest perplexity)")
print(f"- Log Perplexity:       {perplexity:.4f}")
print(f"- Log Likelihood:       {likelihood:.4f}")
print(f"- Training time:        {lda_minutes} mins {lda_seconds} secs")
print()
print(f"FILES SAVED:")

expected_files = [
    "regression_metrics.csv",
    "regression_predictions.csv",
    "regression_bucket_analysis.csv",
    "lda_k_selection.csv",
    "lda_topics.csv",
    "topic_distribution.csv"
]

for filename in expected_files:
    filepath = os.path.join(OUTPUT_DIR, filename).replace("\\", "/")
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024.0
        print(f" - [CONFIRMED] {filename:<30} Size: {size_kb:.2f} KB")
    else:
        print(f" - [MISSING]   {filename:<30}")
        
print()
print(f"ALL PROJECT RESULTS:")
print(f"- Phase 2 Accuracy:     71.31%")
print(f"- Phase 2 F1:           0.7076")
print(f"- Phase 3 R²:           {r2_log:.4f}")
print(f"- Phase 3 Perplexity:   {perplexity:.4f}")
print(f"- Total pipeline runtime: {total_elapsed_time:.2f} seconds")
print("=" * 60)

# Stop Spark Session cleanly
spark.stop()
print("SparkSession stopped cleanly. Execution finished successfully.")
