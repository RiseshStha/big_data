import os
import time
import sys

#
# FILE PATHS
#
DATA_DIR       = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Data/"
OUTPUT_DIR     = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
QUESTIONS_FILE = DATA_DIR + "Questions.csv"
ANSWERS_FILE   = DATA_DIR + "Answers.csv"
TAGS_FILE      = DATA_DIR + "Tags.csv"
PARQUET_OUTPUT = OUTPUT_DIR + "questions_clean.parquet"


print("STARTING STACKOVERFLOW DATA PREPROCESSING (PHASE 0)")

global_start_time = time.time()

#
# 1. IMPORTS
#
print("\n STEP 1: IMPORTING PYSPARK MODULES ")
step_start = time.time()
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, regexp_replace, concat_ws, length, collect_list
    from pyspark.sql.types import IntegerType
    print(f"PySpark modules imported successfully in {time.time() - step_start:.4f} seconds.")
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import PySpark modules: {e}")
    print("Troubleshooting suggestions:")
    print("1. Check if PySpark is installed in the active environment: 'pip show pyspark'")
    print("2. Ensure your Python interpreter matches the one where PySpark was installed.")
    sys.exit(1)

#
# 2. SPARK SESSION
#
print("\n STEP 2: CREATING SPARK SESSION ")
step_start = time.time()
try:
    # Build SparkSession with the requested properties
    spark = SparkSession.builder \
        .appName("StackOverflow_NLP") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.driver.extraJavaOptions", "-Dfile.encoding=UTF-8") \
        .getOrCreate()
    
    print("SparkSession created successfully.")
    print(f"Spark Version: {spark.version}")
    print(f"Time taken to start Spark: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to initialize Spark Session: {e}")
    print("\nTroubleshooting suggestions for Spark Startup issues on Windows:")
    print("1. Confirm Java is installed and JAVA_HOME is configured. (java -version succeeded)")
    print("2. Ensure that no other process is blocking the Spark ports (e.g., 4040).")
    print("3. Check that your environment variables do not contain spaces or invalid characters in PATH.")
    sys.exit(1)

#
# 3. LOAD DATA
#
print("\n STEP 3: LOADING DATASETS ")

# Create OUTPUT_DIR if missing
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Confirmed output directory exists: {OUTPUT_DIR}")
except Exception as e:
    print(f"[WARNING] Could not create output directory: {e}")

# Load Questions
print(f"Loading Questions from: {QUESTIONS_FILE}")
questions_load_start = time.time()
try:
    df_questions = spark.read.csv(
        QUESTIONS_FILE,
        header=True,
        inferSchema=True,
        multiLine=True,
        escape='"'
    )
    # We trigger count to get the row count and measure actual loading time
    questions_count = df_questions.count()
    questions_load_time = time.time() - questions_load_start
    print(f"Successfully loaded Questions. Row count: {questions_count}")
    print(f"Time taken to load Questions: {questions_load_time:.2f} seconds")
    
    print("\nQuestions Schema:")
    df_questions.printSchema()
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Questions.csv: {e}")
    print("Troubleshooting suggestions:")
    print(f"1. Verify that the file exists at: {QUESTIONS_FILE}")
    print("2. Check if the CSV format is correct and not locked by another application.")
    sys.exit(1)

# Load Tags
print(f"\nLoading Tags from: {TAGS_FILE}")
tags_load_start = time.time()
try:
    df_tags = spark.read.csv(
        TAGS_FILE,
        header=True,
        inferSchema=True
    )
    tags_count = df_tags.count()
    tags_load_time = time.time() - tags_load_start
    print(f"Successfully loaded Tags. Row count: {tags_count}")
    print(f"Time taken to load Tags: {tags_load_time:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to load Tags.csv: {e}")
    print("Troubleshooting suggestions:")
    print(f"1. Verify that the file exists at: {TAGS_FILE}")
    sys.exit(1)


#
# 4. DATA CLEANING
#
print("\n STEP 4: DATA CLEANING ")

# To optimize intermediate counting operations on a 1.9GB file,
# we will cache the initial cleaned DataFrame.
current_df = df_questions

# Step 4a: Drop rows where Title, Body, or Score is null
print("\n[Step 4a] Dropping rows where Title, Body, or Score is null...")
step_start = time.time()
try:
    current_df = current_df.na.drop(subset=["Title", "Body", "Score"])
    
    # We cache here because we will perform multiple actions/counts downstream
    current_df.cache()
    
    after_drop_count = current_df.count()
    rows_dropped = questions_count - after_drop_count
    print(f"Dropped {rows_dropped} rows containing null values.")
    print(f"Remaining row count: {after_drop_count}")
    print(f"Time taken: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 4a (dropping nulls): {e}")
    sys.exit(1)

# Step 4b: Remove HTML tags from Body using regexp_replace
print("\n[Step 4b] Removing HTML tags from Body using pattern '<[^>]+>'...")
step_start = time.time()
try:
    current_df = current_df.withColumn("Body_clean", regexp_replace(col("Body"), "<[^>]+>", ""))
    after_html_count = current_df.count()
    print("HTML tags removed. Column 'Body_clean' created.")
    print(f"Row count: {after_html_count}")
    print(f"Time taken: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 4b (HTML stripping): {e}")
    sys.exit(1)

# Step 4c: Concatenate Title and Body_clean into column "text"
print("\n[Step 4c] Concatenating Title and Body_clean into 'text' column...")
step_start = time.time()
try:
    current_df = current_df.withColumn("text", concat_ws(" ", col("Title"), col("Body_clean")))
    after_concat_count = current_df.count()
    print("Title and Body_clean concatenated.")
    print(f"Row count: {after_concat_count}")
    print(f"Time taken: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 4c (concatenation): {e}")
    sys.exit(1)

# Step 4d: Add column "text_length" = length(col("text"))
print("\n[Step 4d] Calculating and adding 'text_length' column...")
step_start = time.time()
try:
    current_df = current_df.withColumn("text_length", length(col("text")))
    after_length_count = current_df.count()
    print("Column 'text_length' added successfully.")
    print(f"Row count: {after_length_count}")
    print(f"Time taken: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 4d (text length calculation): {e}")
    sys.exit(1)

# Step 4e: Cast Score to IntegerType explicitly
print("\n[Step 4e] Casting Score to IntegerType...")
step_start = time.time()
try:
    current_df = current_df.withColumn("Score", col("Score").cast(IntegerType()))
    after_cast_count = current_df.count()
    print("Score successfully cast to IntegerType.")
    print(f"Row count: {after_cast_count}")
    print(f"Time taken: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 4e (casting Score): {e}")
    sys.exit(1)


#
# 5. JOIN TAGS
#
print("\n STEP 5: JOINING TAGS")
step_start = time.time()
try:
    print("Grouping Tags by 'Id' to aggregate tags list and string...")
    # Group Tags by Id:
    # - collect_list("Tag") -> "tag_list"
    # - concat_ws(" ", collect_list("Tag")) -> "tags_string"
    df_tags_grouped = df_tags.groupBy("Id").agg(
        collect_list("Tag").alias("tag_list"),
        concat_ws(" ", collect_list("Tag")).alias("tags_string")
    )
    
    print("Performing inner join with cleaned Questions DataFrame on 'Id'...")
    df_joined = current_df.join(df_tags_grouped, on="Id", how="inner")
    
    final_count = df_joined.count()
    print(f"Inner join complete. Row count: {final_count}")
    print(f"Time taken to join: {time.time() - step_start:.2f} seconds")
    
    print("\nShowing 5 sample rows from the final joined DataFrame:")
    df_joined.select("Id", "Title", "Score", "text_length", "tags_string").show(5, truncate=False)
except Exception as e:
    print(f"[CRITICAL ERROR] Error during Step 5 (join tags): {e}")
    sys.exit(1)


#
# 6. SAVE AS PARQUET
#
print("\n STEP 6: SAVING TO PARQUET ")
step_start = time.time()
try:
    print(f"Writing final dataset to parquet format: {PARQUET_OUTPUT}")
    # Save as parquet using overwrite mode
    df_joined.write.mode("overwrite").parquet(PARQUET_OUTPUT)
    print(f"Saved to parquet: {final_count} rows")
    print(f"Time taken to save: {time.time() - step_start:.2f} seconds")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to save output to Parquet: {e}")
    print("\nTroubleshooting suggestions for write issues on Windows:")
    print("1. Ensure there is enough free disk space on drive D:.")
    print("2. Check if a folder/file permission issue is blocking write access.")
    print("3. Sometimes Winutils configurations trigger errors when writing. If so, configure HADOOP_HOME.")
    sys.exit(1)

# Uncache the dataframe to free memory
try:
    current_df.unpersist()
except:
    pass

#
# 7. SUMMARY
#
total_elapsed_time = time.time() - global_start_time
print("\n" + "=" * 60)
print(" PHASE 0 COMPLETE ")
print("=" * 60)
print(f"- Questions loaded: {questions_count}")
print(f"- After cleaning:   {after_cast_count}")
print(f"- After tag join:   {final_count}")
print(f"- Parquet saved to: {PARQUET_OUTPUT}")
print(f"- Time elapsed:     {total_elapsed_time:.2f} seconds")
print("=" * 60)

# Stop the Spark session cleanly
spark.stop()
print("SparkSession stopped cleanly. Execution finished successfully.")
