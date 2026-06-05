import os
import time
import sys

# ==========================================
# FILE PATHS
# ==========================================
DATA_DIR       = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Data/"
OUTPUT_DIR     = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
PARQUET_PATH   = OUTPUT_DIR + "questions_clean.parquet"
TAGS_FILE      = DATA_DIR + "Tags.csv"

print("=" * 60)
print("STARTING STACKOVERFLOW EXPLORATORY DATA ANALYSIS (PHASE 1)")
print("=" * 60)
global_start_time = time.time()

# Ensure the output directory exists
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Confirmed output directory exists: {OUTPUT_DIR}")
except Exception as e:
    print(f"[WARNING] Could not create output directory: {e}")

# ==========================================
# 1. SETUP & LOADING DATA
# ==========================================
print("\n=== STEP 1: INITIALIZING SPARK & LOADING DATA ===")
step_start = time.time()
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, desc, avg, count, round, when, year, lit
    print("Required PySpark modules imported successfully.")
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import PySpark: {e}")
    sys.exit(1)

try:
    # Build SparkSession with the requested properties
    spark = SparkSession.builder \
        .appName("StackOverflow_EDA") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
        .getOrCreate()
    
    print(f"SparkSession started successfully (Spark Version: {spark.version}).")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to start Spark Session: {e}")
    sys.exit(1)

# Load questions parquet file
print(f"Loading cleaned Questions Parquet from: {PARQUET_PATH}")
try:
    # Read the full dataset
    df_raw = spark.read.parquet(PARQUET_PATH)
    
    # PERFORMANCE OPTIMIZATION (Column Projection):
    # Select only the light metadata columns needed for EDA.
    # We explicitly drop the massive text columns (Body, Title, Body_clean, text)
    # to avoid Java OutOfMemory (OOM) heap space errors during caching.
    print("Applying column projection (dropping large text fields to optimize memory)...")
    df = df_raw.select("Id", "Score", "CreationDate", "ClosedDate", "text_length", "tags_string")
    
    # Now it is completely safe to cache the lightweight projected dataset.
    df.cache()
    
    questions_count = df.count()
    print(f"Successfully loaded and cached projected Questions DataFrame. Row count: {questions_count}")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Parquet dataset: {e}")
    sys.exit(1)

# Load tags CSV file
print(f"Loading Tags CSV from: {TAGS_FILE}")
try:
    df_tags = spark.read.csv(TAGS_FILE, header=True, inferSchema=True)
    tags_count = df_tags.count()
    print(f"Successfully loaded Tags. Row count: {tags_count}")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Tags.csv: {e}")
    sys.exit(1)

print(f"Setup and loading complete in {time.time() - step_start:.2f} seconds.")

# ==========================================
# 2. BLOCK 1 — SCORE DISTRIBUTION
# ==========================================
print("\n=== BLOCK 1: SCORE DISTRIBUTION ===")
step_start = time.time()
try:
    # Print basic summary statistics of Score
    df.select("Score").describe().show()
    
    # Calculate distributions
    neg_count = df.filter(col("Score") < 0).count()
    zero_count = df.filter(col("Score") == 0).count()
    low_count = df.filter((col("Score") >= 1) & (col("Score") <= 10)).count()
    high_count = df.filter(col("Score") > 10).count()
    
    print(f"Questions with Score < 0:                  {neg_count}")
    print(f"Questions with Score = 0:                  {zero_count}")
    print(f"Questions with Score between 1 and 10:     {low_count}")
    print(f"Questions with Score > 10:                 {high_count}")
    
    # Create bucket column
    df_with_bucket = df.withColumn(
        "score_bucket",
        when(col("Score") < 0, "negative")
        .when(col("Score") == 0, "zero")
        .when((col("Score") >= 1) & (col("Score") <= 10), "low")
        .otherwise("high")
    )
    
    # Group by bucket, count, and export to CSV
    print("Grouping by score bucket and exporting...")
    df_score_dist = df_with_bucket.groupBy("score_bucket").count()
    df_score_dist.show()
    
    csv_file = OUTPUT_DIR + "score_distribution.csv"
    df_score_dist.toPandas().to_csv(csv_file, index=False)
    print(f"Saved: {csv_file}")
    print(f"Block 1 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 1 failed: {e}")
    sys.exit(1)

# ==========================================
# 3. BLOCK 2 — TOP 50 TAGS
# ==========================================
print("\n=== BLOCK 2: TOP 50 TAGS ===")
step_start = time.time()
try:
    print("Calculating top tags counts...")
    df_top_tags = df_tags.groupBy("Tag").count().orderBy(desc("count"))
    
    # Show top 20 in terminal
    print("Top 20 Tags:")
    df_top_tags.show(20)
    
    # Save top 50 to CSV
    csv_file = OUTPUT_DIR + "top_tags.csv"
    df_top_tags.limit(50).toPandas().to_csv(csv_file, index=False)
    print(f"Saved top 50 tags: {csv_file}")
    print(f"Block 2 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 2 failed: {e}")
    sys.exit(1)

# ==========================================
# 4. BLOCK 3 — AVERAGE SCORE BY TAG
# ==========================================
print("\n=== BLOCK 3: AVERAGE SCORE BY TAG ===")
step_start = time.time()
try:
    print("Joining Tags with cleaned Questions to analyze average scores...")
    df_joined_tags = df_tags.join(df, on="Id", how="inner")
    
    df_avg_score_by_tag = df_joined_tags.groupBy("Tag").agg(
        round(avg("Score"), 2).alias("avg_score"),
        count("*").alias("num_questions")
    ).orderBy(desc("num_questions"))
    
    # Show top 20 in terminal
    print("Average Score by Top 20 Tags:")
    df_avg_score_by_tag.show(20)
    
    # Save top 50 to CSV
    csv_file = OUTPUT_DIR + "avg_score_by_tag.csv"
    df_avg_score_by_tag.limit(50).toPandas().to_csv(csv_file, index=False)
    print(f"Saved average score by tag data: {csv_file}")
    print(f"Block 3 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 3 failed: {e}")
    sys.exit(1)

# ==========================================
# 5. BLOCK 4 — TEXT LENGTH ANALYSIS
# ==========================================
print("\n=== BLOCK 4: TEXT LENGTH ANALYSIS ===")
step_start = time.time()
try:
    print("Summary statistics for text_length:")
    df.select("text_length").describe().show()
    
    # Compute correlation
    print("Computing Pearson correlation between text_length and Score...")
    corr_val = df.stat.corr("text_length", "Score")
    print(f"Correlation value: {corr_val:.6f}")
    
    # Interpret correlation
    abs_corr = abs(corr_val)
    if abs_corr > 0.5:
        interpretation = "Strong correlation"
    elif abs_corr > 0.3:
        interpretation = "Moderate correlation"
    else:
        interpretation = "Weak correlation"
    print(f"Interpretation: {interpretation}")
    
    # Export sample of 10,000 to CSV
    csv_file = OUTPUT_DIR + "length_vs_score.csv"
    df.select("text_length", "Score").limit(10000).toPandas().to_csv(csv_file, index=False)
    print(f"Saved sample size (10k) length vs score: {csv_file}")
    print(f"Block 4 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 4 failed: {e}")
    sys.exit(1)

# ==========================================
# 6. BLOCK 5 — TEMPORAL TREND
# ==========================================
print("\n=== BLOCK 5: QUESTIONS PER YEAR ===")
step_start = time.time()
try:
    print("Extracting year and grouping questions...")
    df_temporal = df.withColumn("year", year(col("CreationDate")))
    df_per_year = df_temporal.groupBy("year").count().orderBy("year")
    
    # Show in terminal
    df_per_year.show()
    
    # Save to CSV
    csv_file = OUTPUT_DIR + "questions_per_year.csv"
    df_per_year.toPandas().to_csv(csv_file, index=False)
    print(f"Saved temporal trend of questions: {csv_file}")
    print(f"Block 5 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 5 failed: {e}")
    sys.exit(1)

# ==========================================
# 7. BLOCK 6 — TOP 5 TAGS OVER TIME
# ==========================================
print("\n=== BLOCK 6: TOP TAGS OVER TIME ===")
step_start = time.time()
try:
    target_tags = ["python", "javascript", "java", "c#", "php"]
    dfs = []
    
    print("Filtering and computing yearly counts for target tags...")
    for tag in target_tags:
        print(f"  Processing tag: {tag}")
        df_tag_time = df.filter(col("tags_string").contains(tag)) \
                        .withColumn("year", year(col("CreationDate"))) \
                        .groupBy("year").count() \
                        .withColumn("tag", lit(tag)) \
                        .select("tag", "year", "count")
        dfs.append(df_tag_time)
        
    # Union all 5 DataFrames
    from functools import reduce
    df_top_tags_time = reduce(lambda df1, df2: df1.union(df2), dfs)
    
    # Show first 20 rows in terminal
    print("Top 5 Tags Yearly Counts:")
    df_top_tags_time.show(20)
    
    # Save to CSV
    csv_file = OUTPUT_DIR + "top_tags_over_time.csv"
    df_top_tags_time.toPandas().to_csv(csv_file, index=False)
    print(f"Saved top tags over time dataset: {csv_file}")
    print(f"Block 6 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 6 failed: {e}")
    sys.exit(1)

# ==========================================
# 8. BLOCK 7 — CLOSED QUESTIONS ANALYSIS
# ==========================================
print("\n=== BLOCK 7: CLOSED QUESTIONS ===")
step_start = time.time()
try:
    print("Calculating closed vs open questions metrics...")
    
    closed_count = df.filter(col("ClosedDate").isNotNull()).count()
    open_count = df.filter(col("ClosedDate").isNull()).count()
    
    print(f"Closed questions count: {closed_count}")
    print(f"Open questions count:   {open_count}")
    
    # Segment status and calculate aggregate metrics
    df_status = df.withColumn("status", when(col("ClosedDate").isNotNull(), "closed").otherwise("open"))
    df_closed_vs_open = df_status.groupBy("status").agg(
        count("*").alias("count"),
        round(avg("Score"), 2).alias("avg_score")
    )
    
    df_closed_vs_open.show()
    
    # Save to CSV
    csv_file = OUTPUT_DIR + "closed_vs_open.csv"
    df_closed_vs_open.toPandas().to_csv(csv_file, index=False)
    print(f"Saved closed vs open comparison: {csv_file}")
    print(f"Block 7 complete in {time.time() - step_start:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] Block 7 failed: {e}")
    sys.exit(1)

# Clean cached DataFrame
try:
    df.unpersist()
except:
    pass

# ==========================================
# 9. SUMMARY & VERIFICATION
# ==========================================
total_elapsed_time = time.time() - global_start_time
print("\n" + "=" * 60)
print("=== PHASE 1 COMPLETE ===")
print("=" * 60)
print("CSV files saved to OUTPUT_DIR:")

expected_files = [
    "score_distribution.csv",
    "top_tags.csv",
    "avg_score_by_tag.csv",
    "length_vs_score.csv",
    "questions_per_year.csv",
    "top_tags_over_time.csv",
    "closed_vs_open.csv"
]

all_exist = True
for f in expected_files:
    full_path = os.path.join(OUTPUT_DIR, f).replace("\\", "/")
    if os.path.exists(full_path):
        size_kb = os.path.getsize(full_path) / 1024.0
        print(f" - [CONFIRMED] {f:<25} Size: {size_kb:.2f} KB")
    else:
        print(f" - [MISSING]   {f:<25}")
        all_exist = False

print(f"Total time elapsed: {total_elapsed_time:.2f} seconds")
print("=" * 60)

# Stop the Spark session cleanly
spark.stop()
print("SparkSession stopped cleanly. Execution finished successfully.")

if not all_exist:
    print("Warning: One or more CSV files were not found.")
    sys.exit(1)
