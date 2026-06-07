# Stack Overflow Question Intelligence

**Multi-Task NLP Analysis Using PySpark and Tableau**

> 7082CEM — Big Data Management and Data Visualisation | Coventry University via Softwarica College

## Project Description

This project performs a comprehensive big data analytical pipeline on the **StackSample** dataset (a 10% subset of Stack Overflow's Q&A archive) using **Apache PySpark** for distributed computation and **Tableau** for interactive visualisation.

Three machine learning tasks are implemented:

| Task | Technique | Key Result |
|------|-----------|------------|
| **Tag Classification** | Random Forest (50 trees, depth 10) | 71.31% accuracy across 10 technology tags |
| **Score Prediction** | Linear Regression (TF-IDF + text length) | R² ≈ -0.0001 — scores driven by social factors, not text |
| **Topic Discovery** | Latent Dirichlet Allocation (k=10) | 10 coherent programming topics, log perplexity 2.8337 |

## Dataset

- **Source**: [StackSample: 10% of Stack Overflow Q&A](https://www.kaggle.com/datasets/stackoverflow/stacksample)
- **Files Used**: `Questions.csv` (1.26M rows), `Tags.csv` (3.75M rows)
- **Data Types**: Integers, strings, timestamps, long-form HTML text, categorical tags

## Project Structure

```
Project/
├── Data/                          # Raw dataset (not included in repo)
│   ├── Questions.csv              # 1,264,216 questions
│   ├── Answers.csv                # 2,014,516 answers
│   └── Tags.csv                   # 3,750,994 tag records
│
├── Outputs/                       # Generated results
│   ├── Plots/                     # 14 analytical PNG charts + 6 screenshots
│   ├── questions_clean.parquet/   # Cleaned Parquet output from Phase 0
│   ├── top_tags.csv               # Top 50 tags by question volume
│   ├── avg_score_by_tag.csv       # Average score per tag
│   ├── questions_per_year.csv     # Yearly question counts (2008–2016)
│   ├── confusion_matrix.csv       # 10×10 classification confusion matrix
│   ├── per_class_accuracy.csv     # Per-tag classification accuracy
│   ├── feature_importances.csv    # Top 20 Random Forest feature weights
│   ├── regression_predictions.csv # Actual vs predicted scores
│   ├── lda_topics.csv             # 10 LDA topics with top words
│   ├── lda_k_selection.csv        # Model selection perplexity/likelihood
│   ├── topic_distribution.csv     # Document counts per topic
│   └── ...                        # Additional CSV exports
│
├── phase0_setup.py                # Data loading, cleaning, join, Parquet export
├── phase1_eda.py                  # Exploratory data analysis & CSV exports
├── phase2_classification.py       # Random Forest tag classification pipeline
├── phase3_regression_lda.py       # Linear Regression + LDA topic modelling
├── generate_plots.py              # Matplotlib/Seaborn chart generation
├── generate_screenshots.py        # Simulated terminal screenshot generation
├── update_word_docs.py            # Automated Word report assembly
└── README.md                      # This file
```

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| **Java JDK** | 1.8 (Java 8) | Required by Apache Spark |
| **Apache Spark** | 3.5.x | Distributed computing engine |
| **Python** | 3.10+ | Programming language |
| **Hadoop winutils** | 3.x | Windows Spark compatibility |
| **Tableau Desktop/Public** | Latest | Dashboard visualisation |

## Setup

### 1. Install Java JDK 8

Download and install [Java JDK 8](https://www.oracle.com/java/technologies/javase/javase8-archive-downloads.html). Set the environment variable:

```bash
JAVA_HOME = C:\Program Files\Java\jdk1.8.0_xxx
```

### 2. Install Apache Spark

Download [Apache Spark 3.5.x](https://spark.apache.org/downloads.html) (pre-built for Hadoop). Extract and set:

```bash
SPARK_HOME = C:\spark\spark-3.5.8-bin-hadoop3
HADOOP_HOME = C:\spark\spark-3.5.8-bin-hadoop3
```

Add `%SPARK_HOME%\bin` to your system `PATH`.

### 3. Install Python Dependencies

```bash
pip install pyspark pandas numpy matplotlib seaborn python-docx
```

### 4. Download the Dataset

Download from [Kaggle StackSample](https://www.kaggle.com/datasets/stackoverflow/stacksample) and place the three CSV files into the `Data/` directory:

```
Data/
├── Questions.csv
├── Answers.csv
└── Tags.csv
```

## How to Run

Run the scripts **in order** from the project root directory. Each phase depends on the output of the previous one.

### Phase 0: Data Setup & Cleaning

```bash
python phase0_setup.py
```

- Loads `Questions.csv` and `Tags.csv`
- Cleans HTML from text columns
- Joins questions with tags
- Exports cleaned data to `Outputs/questions_clean.parquet/`
- **Runtime**: ~3–5 minutes

### Phase 1: Exploratory Data Analysis

```bash
python phase1_eda.py
```

- Computes tag frequencies, score distributions, yearly trends
- Exports analysis CSVs to `Outputs/`
- **Runtime**: ~2–3 minutes

### Phase 2: Tag Classification

```bash
python phase2_classification.py
```

- Builds NLP pipeline (Tokenizer → StopWords → HashingTF → IDF → Random Forest)
- Trains on 200K stratified samples across 10 tag classes
- Exports confusion matrix, per-class accuracy, and feature importances
- **Runtime**: ~6–8 minutes

### Phase 3: Regression & LDA Topic Modelling

```bash
python phase3_regression_lda.py
```

- Trains Linear Regression on TF-IDF features for score prediction
- Runs LDA model selection (k = 5, 8, 10, 12) and trains final model
- Exports regression predictions, LDA topics, and model selection metrics
- **Runtime**: ~5–7 minutes

### Generate Visualisation Plots

```bash
python generate_plots.py
```

- Reads all CSV outputs and generates 14 analytical PNG charts
- Saves to `Outputs/Plots/`

## Tableau Dashboards

After running all phases, connect the CSV files from `Outputs/` to Tableau to build:

| Dashboard | Sheets | Data Sources |
|-----------|--------|--------------|
| **EDA Dashboard** | Tag Treemap, Avg Score Bar, Growth Line | `top_tags.csv`, `avg_score_by_tag.csv`, `questions_per_year.csv` |
| **Model Performance** | Confusion Heatmap, LDA Heatmap, Regression Scatter | `confusion_matrix.csv`, `lda_topics.csv`, `regression_predictions.csv` |

## References

- Apache Spark (2024) *MLlib Guide*. https://spark.apache.org/docs/latest/ml-guide.html
- Blei, D.M., Ng, A.Y. and Jordan, M.I. (2003) 'Latent Dirichlet Allocation', *JMLR*, 3, pp. 993–1022.
- Breiman, L. (2001) 'Random Forests', *Machine Learning*, 45(1), pp. 5–32.
- Kaggle (2019) *StackSample: 10% of Stack Overflow Q&A*. https://www.kaggle.com/datasets/stackoverflow/stacksample

## License

This project is submitted as academic coursework for 7082CEM at Coventry University.
