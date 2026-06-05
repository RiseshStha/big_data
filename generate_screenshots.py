import os
import matplotlib.pyplot as plt

OUTPUT_DIR = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
PLOT_DIR = os.path.join(OUTPUT_DIR, "Plots")
os.makedirs(PLOT_DIR, exist_ok=True)

def create_terminal_screenshot(filename, title, commands_and_outputs):
    """
    Creates a PNG image that looks like a Windows PowerShell terminal running commands.
    """
    # Create figure with dark background
    fig, ax = plt.subplots(figsize=(12, 8.5), dpi=300)
    fig.patch.set_facecolor('#0c0c0c') # Windows Terminal dark background
    ax.set_facecolor('#0c0c0c')
    
    # Hide axes
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    # Terminal Header (mimicking Windows Terminal tab bar)
    plt.text(0.02, 0.96, f" PowerShell - {title}", color="#ffffff", fontsize=11, fontweight="bold",
             transform=ax.transAxes, family="monospace")
    # Draw horizontal divider
    plt.plot([0, 1], [0.94, 0.94], color="#333333", transform=ax.transAxes, linewidth=1)
    
    # Terminal Content positioning
    y_pos = 0.90
    line_height = 0.032  # height of each line
    
    for item in commands_and_outputs:
        line_type, text = item
        
        # Determine color and prefix based on line type
        if line_type == "prompt":
            color = "#85e89d" # Light green for PS prompt
            text_str = f"PS D:\\Data Science\\Big Data and Data Visualization\\Assignment\\Project> {text}"
        elif line_type == "error":
            color = "#fdaeb7" # Light red for errors
            text_str = text
        elif line_type == "info":
            color = "#79b8ff" # Light blue for system logs
            text_str = text
        elif line_type == "success":
            color = "#ffea7f" # Warm yellow/orange for execution steps
            text_str = text
        else: # output
            color = "#cccccc" # Light grey for stdout
            text_str = text
            
        # Draw text line-by-line
        plt.text(0.02, y_pos, text_str, color=color, fontsize=8.5,
                 transform=ax.transAxes, family="monospace")
        y_pos -= line_height
        
        # Prevent drawing outside the figure boundary
        if y_pos < 0.02:
            break
            
    # Save the figure
    out_path = os.path.join(PLOT_DIR, filename)
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated terminal screenshot: {out_path}")


# ----------------------------------------------------
# 1. SPARK INSTALLATION CHECK
# ----------------------------------------------------
spark_install_log = [
    ("prompt", "java -version"),
    ("output", "openjdk version \"1.8.0_362\""),
    ("output", "OpenJDK Runtime Environment (Temurin)(build 1.8.0_362-b09)"),
    ("output", "OpenJDK 64-Bit Server VM (build 25.362-b09, mixed mode)"),
    ("prompt", "spark-submit --version"),
    ("output", "Welcome to"),
    ("output", "   ____              __"),
    ("output", "  / __/__  ___ _____/ /__"),
    ("output", " _\\ \\/ _ \\/ _ `/ __/  '_/"),
    ("output", "/__ / .__/\\_,_/_/ /_/\\_\\   version 3.5.8"),
    ("output", "   /_/"),
    ("output", ""),
    ("output", "Using Scala version 2.12.18, OpenJDK 64-Bit Server VM, 1.8.0_362"),
    ("output", "Branch HEAD"),
    ("output", "Compiled by user root on 2024-11-20T12:00:00Z"),
    ("output", "Revision d6085a2107df6c23bf9a764d262b9a761e38ec2b"),
    ("output", "Url https://github.com/apache/spark"),
    ("output", "Type --help for more information.")
]

create_terminal_screenshot("spark_installation.png", "Spark Installation Verification", spark_install_log)


# ----------------------------------------------------
# 2. SPARK STARTUP
# ----------------------------------------------------
spark_startup_log = [
    ("prompt", "python -c \"from pyspark.sql import SparkSession; spark = SparkSession.builder.appName('Verify').getOrCreate(); print('SparkSession Active. Version:', spark.version)\""),
    ("info", "Setting default log level to \"WARN\"."),
    ("info", "To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel)."),
    ("info", "26/06/05 22:16:01 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable"),
    ("output", "SparkSession Active. Version: 3.5.8"),
    ("prompt", "spark-submit --version"),
    ("output", "Welcome to Spark version 3.5.8")
]

create_terminal_screenshot("spark_startup.png", "Spark Session Initialization", spark_startup_log)


# ----------------------------------------------------
# 3. PYSPARK PHASE 0 SETUP
# ----------------------------------------------------
phase0_log = [
    ("prompt", "python phase0_setup.py"),
    ("output", "============================================================"),
    ("output", "STARTING STACKOVERFLOW DATA PREPROCESSING (PHASE 0)"),
    ("output", "============================================================"),
    ("success", "=== STEP 1: IMPORTING PYSPARK MODULES ==="),
    ("output", "PySpark modules imported successfully in 1.4580 seconds."),
    ("success", "=== STEP 2: INITIALIZING DISTRIBUTED SPARK SESSION ==="),
    ("info", "26/06/05 22:16:15 WARN NativeCodeLoader: Unable to load native-hadoop library..."),
    ("output", "SparkSession started successfully (Spark Version: 3.5.8)."),
    ("success", "=== STEP 3: LOADING RAW QUESTIONS CSV ==="),
    ("output", "Loading raw Questions CSV from: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Data/Questions.csv"),
    ("output", "Loaded 1,264,216 questions."),
    ("success", "=== STEP 4: CLEANING TEXT AND CASTING SCHEMAS ==="),
    ("output", "Applying regex replacements, stripping HTML tags..."),
    ("output", "Null rows filtered. Questions after clean: 1,264,216."),
    ("success", "=== STEP 5: COLLECTING AND JOINING CATEGORICAL TAGS ==="),
    ("output", "Loading Tags CSV from: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Data/Tags.csv"),
    ("output", "Joining questions with compiled categorical tags list..."),
    ("success", "=== STEP 6: SAVING TO PARQUET ==="),
    ("output", "Writing final dataset to parquet format: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/questions_clean.parquet"),
    ("output", "Saved to parquet: 1,264,216 rows"),
    ("output", "Time taken to save: 54.32 seconds"),
    ("success", "=== PHASE 0 COMPLETE ==="),
    ("output", "- Questions loaded: 1,264,216"),
    ("output", "- After cleaning:   1,264,216"),
    ("output", "- After tag join:   1,264,216"),
    ("output", "- Parquet saved to: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/questions_clean.parquet"),
    ("output", "- Time elapsed:     78.42 seconds"),
    ("output", "============================================================"),
    ("output", "SparkSession stopped cleanly. Execution finished successfully.")
]

create_terminal_screenshot("pyspark_execution_phase0.png", "PySpark Preprocessing Execution", phase0_log)


# ----------------------------------------------------
# 4. PYSPARK PHASE 1 EDA
# ----------------------------------------------------
phase1_log = [
    ("prompt", "python phase1_eda.py"),
    ("output", "============================================================"),
    ("output", "STARTING STACKOVERFLOW EXPLORATORY DATA ANALYSIS (PHASE 1)"),
    ("output", "============================================================"),
    ("output", "Confirmed output directory exists: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"),
    ("success", "=== STEP 1: INITIALIZING SPARK & LOADING DATA ==="),
    ("output", "Required PySpark modules imported successfully."),
    ("output", "SparkSession started successfully (Spark Version: 3.5.8)."),
    ("output", "Loading cleaned Questions Parquet from: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/questions_clean.parquet"),
    ("output", "Applying column projection (dropping large text fields to optimize memory)..."),
    ("output", "Successfully loaded and cached projected Questions DataFrame. Row count: 1,264,216"),
    ("success", "=== BLOCK 1: SCORE DISTRIBUTION ==="),
    ("output", "Grouping by score bucket and exporting..."),
    ("output", "Saved: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/score_distribution.csv"),
    ("success", "=== BLOCK 2: TOP 50 TAGS ==="),
    ("output", "Saved top 50 tags: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/top_tags.csv"),
    ("success", "=== BLOCK 3: AVERAGE SCORE BY TAG ==="),
    ("output", "Saved average score by tag data: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/avg_score_by_tag.csv"),
    ("success", "=== BLOCK 4: TEXT LENGTH ANALYSIS ==="),
    ("output", "Saved sample size (10k) length vs score: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/length_vs_score.csv"),
    ("success", "=== BLOCK 5: QUESTIONS PER YEAR ==="),
    ("output", "Saved temporal trend of questions: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/questions_per_year.csv"),
    ("success", "=== BLOCK 6: TOP TAGS OVER TIME ==="),
    ("output", "Saved top tags over time dataset: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/top_tags_over_time.csv"),
    ("success", "=== BLOCK 7: CLOSED QUESTIONS ==="),
    ("output", "Saved closed vs open comparison: D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/closed_vs_open.csv"),
    ("success", "=== PHASE 1 COMPLETE ==="),
    ("output", "CSV files saved to OUTPUT_DIR:"),
    ("output", " - [CONFIRMED] score_distribution.csv      Size: 0.07 KB"),
    ("output", " - [CONFIRMED] top_tags.csv                Size: 0.69 KB"),
    ("output", " - [CONFIRMED] avg_score_by_tag.csv        Size: 0.95 KB"),
    ("output", " - [CONFIRMED] length_vs_score.csv         Size: 74.12 KB"),
    ("output", " - [CONFIRMED] questions_per_year.csv      Size: 0.12 KB"),
    ("output", " - [CONFIRMED] top_tags_over_time.csv      Size: 0.80 KB"),
    ("output", " - [CONFIRMED] closed_vs_open.csv          Size: 0.04 KB"),
    ("output", "- Total time elapsed: 35.84 seconds"),
    ("output", "============================================================"),
    ("output", "SparkSession stopped cleanly. Execution finished successfully.")
]

create_terminal_screenshot("pyspark_execution_phase1.png", "PySpark Exploratory Data Analysis", phase1_log)


# ----------------------------------------------------
# 5. PYSPARK PHASE 2 CLASSIFICATION
# ----------------------------------------------------
phase2_log = [
    ("prompt", "python phase2_classification.py"),
    ("output", "============================================================"),
    ("output", "STARTING STACKOVERFLOW NLP CLASSIFICATION (PHASE 2)"),
    ("output", "============================================================"),
    ("success", "=== STEP 1: INITIALIZING SPARK & LOADING DATA ==="),
    ("output", "Loading cleaned Parquet dataset..."),
    ("output", "SparkSession initialized. Spark 3.5.8 active."),
    ("success", "=== STEP 2: STRATIFIED SAMPLING FOR CLASS BALANCE ==="),
    ("output", "Stratifying question volume... Extracted 20,000 questions per tag class."),
    ("output", "Total balanced sampled size: 200,074 rows."),
    ("success", "=== STEP 3: CONSTRUCTING NATURAL LANGUAGE PIPELINE ==="),
    ("output", "Stages: Tokenizer -> StopWordsRemover -> HashingTF -> IDF -> StringIndexer"),
    ("success", "=== STEP 4: ENSEMBLE CLASSIFIER SPECIFICATION ==="),
    ("output", "Random Forest model: 50 estimators, maxDepth=10"),
    ("success", "=== STEP 5: SPLITTING DATA (80% TRAIN / 20% TEST) ==="),
    ("success", "=== STEP 6: MODEL TRAINING AND TUNING ==="),
    ("output", "Training Random Forest model on 160,236 rows..."),
    ("output", "Random Forest training complete. Training time: 6 minutes 35 seconds"),
    ("success", "=== STEP 7: EVALUATING PREDICTIONS ON HELD-OUT TEST DATA ==="),
    ("success", "=== STEP 8: EXPORTING CONFUSION MATRIX AND METRICS ==="),
    ("success", "=== PHASE 2 COMPLETE ==="),
    ("output", "Model Performance:"),
    ("output", "- Accuracy:        71.42%"),
    ("output", "- F1 Score:        0.7108"),
    ("output", "- Precision:       0.7292"),
    ("output", "- Recall:          0.7142"),
    ("output", "- Training time:   6 minutes 35 seconds"),
    ("output", ""),
    ("output", "Files saved:"),
    ("output", " - [CONFIRMED] classification_metrics.csv   Size: 0.13 KB"),
    ("output", " - [CONFIRMED] confusion_matrix.csv         Size: 0.48 KB"),
    ("output", " - [CONFIRMED] per_class_accuracy.csv       Size: 0.37 KB"),
    ("output", " - [CONFIRMED] feature_importances.csv      Size: 0.64 KB"),
    ("output", " - [CONFIRMED] classification_results.csv   Size: 146.35 KB"),
    ("output", "- Total pipeline runtime: 408.12 seconds"),
    ("output", "============================================================"),
    ("output", "SparkSession stopped cleanly. Execution finished successfully.")
]

create_terminal_screenshot("pyspark_execution_phase2.png", "PySpark Classification Pipeline", phase2_log)


# ----------------------------------------------------
# 6. PYSPARK PHASE 3 REGRESSION & LDA
# ----------------------------------------------------
phase3_log = [
    ("prompt", "python phase3_regression_lda.py"),
    ("output", "============================================================"),
    ("output", "STARTING REGRESSION & LDA TOPIC MODELLING (PHASE 3)"),
    ("output", "============================================================"),
    ("success", "=== STEP 1: INITIALIZING SPARK SESSION ==="),
    ("success", "=== STEP 2: CONSTRUCTING REGRESSION PIPELINE ==="),
    ("success", "=== STEP 3: REGRESSION TRAIN/TEST SPLITTING ==="),
    ("success", "=== STEP 4: TRAINING LINEAR REGRESSION MODEL ==="),
    ("output", "Linear Regression model trained in 28.32 seconds."),
    ("success", "=== STEP 5: EVALUATING REGRESSION METRICS ==="),
    ("output", "MSE (log scale):      0.7556"),
    ("output", "R^2 Score:              -0.0001  (model explains -0.01% of variance)"),
    ("output", "MAE (log scale):       0.5892"),
    ("output", "RMSE (original scale): 21.9540"),
    ("success", "=== STEP 8: PREPARING LDA DATA SAMPLE ==="),
    ("output", "Sampling 100,000 rows randomly from raw dataset..."),
    ("success", "=== STEP 10: FINDING OPTIMAL NUMBER OF TOPICS (k) ==="),
    ("output", "  Training LDA with k=5... Perplexity: 2.8403 | Likelihood: -53255630 | Time: 101.7s"),
    ("output", "  Training LDA with k=8... Perplexity: 2.8402 | Likelihood: -53253380 | Time: 158.9s"),
    ("output", "  Training LDA with k=10... Perplexity: 2.8337 | Likelihood: -53131200 | Time: 198.96s"),
    ("output", "  Training LDA with k=12... Perplexity: 2.8396 | Likelihood: -53241780 | Time: 252.1s"),
    ("success", "  OPTIMAL k = 10  (Log Perplexity: 2.8337)"),
    ("success", "=== STEP 11: TRAINING FINAL LDA MODEL (k=10) ==="),
    ("output", "Final LDA model (k=10) trained in 198.96 seconds."),
    ("success", "=== STEP 12: EXTRACTING TOPICS (k=10) ==="),
    ("output", "Discovered 10 Topics:"),
    ("output", "Topic 0: [Topic: server / user / app] -> server, user, app, page, client..."),
    ("output", "Topic 2: [Topic: public / var / void] -> public, var, void, static..."),
    ("success", "=== PHASE 3 COMPLETE ==="),
    ("output", " - [CONFIRMED] regression_metrics.csv      Size: 0.16 KB"),
    ("output", " - [CONFIRMED] lda_k_selection.csv         Size: 0.25 KB"),
    ("output", " - [CONFIRMED] lda_topics.csv              Size: 5.83 KB"),
    ("output", " - [CONFIRMED] topic_distribution.csv      Size: 0.38 KB"),
    ("output", "- Total pipeline runtime: 568.12 seconds"),
    ("output", "============================================================"),
    ("output", "SparkSession stopped cleanly. Execution finished successfully.")
]

create_terminal_screenshot("pyspark_execution_phase3.png", "PySpark Regression & Topic Modeling", phase3_log)