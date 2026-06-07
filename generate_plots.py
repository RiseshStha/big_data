import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# Set paths
OUTPUT_DIR = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/"
PLOT_DIR = os.path.join(OUTPUT_DIR, "Plots")
os.makedirs(PLOT_DIR, exist_ok=True)
# Set visual style
sns.set_theme(style="whitegrid", context="talk", palette="muted")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Liberation Sans', 'DejaVu Sans', 'sans-serif'],
    'figure.titlesize': 20,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.dpi': 300,
    'savefig.bbox': 'tight'
})
# Custom Color Palette
MAIN_COLOR = "#2c7fb8"
ACCENT_COLOR = "#7fcdbb"
HIGHLIGHT_COLOR = "#31a354"
DARK_GREY = "#4f4f4f"

print("STARTING ALL PLOT GENERATION")

# 1. SCORE DISTRIBUTION

print("Generating Plot 1: Score Distribution...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "score_distribution.csv"))
    plt.figure(figsize=(8, 5))
    # Order buckets logically
    order = ["negative", "zero", "low", "high"]
    df['score_bucket'] = pd.Categorical(df['score_bucket'], categories=order, ordered=True)
    df = df.sort_values('score_bucket')
    
    ax = sns.barplot(x="score_bucket", y="count", data=df, color=MAIN_COLOR, edgecolor="black", linewidth=1.2)
    plt.title("Stack Overflow Question Score Distribution", pad=15, fontweight="bold")
    plt.xlabel("Score Category (Negative, Zero, Low: 1-10, High: >10)", labelpad=10)
    plt.ylabel("Number of Questions", labelpad=10)
    
    # Add values on top of bars
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height()):,}", 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', xytext=(0, 8), 
                    textcoords='offset points', fontsize=10, fontweight="bold")
    
    plt.savefig(os.path.join(PLOT_DIR, "eda_1_score_dist.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 1: {e}")

# 2. TOP 20 TAGS

print("Generating Plot 2: Top 20 Tags...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "top_tags.csv"))
    df_top20 = df.head(20).copy()
    df_top20 = df_top20.sort_values("count", ascending=True)
    
    plt.figure(figsize=(10, 7))
    ax = sns.barplot(x="count", y="Tag", data=df_top20, color=MAIN_COLOR, edgecolor="black", linewidth=0.8)
    plt.title("Top 20 Stack Overflow Programming Tags by Volume", pad=15, fontweight="bold")
    plt.xlabel("Question Count", labelpad=10)
    plt.ylabel("Technology Tag", labelpad=10)
    
    # Annotate bar values
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width()):,}", 
                    (p.get_width(), p.get_y() + p.get_height() / 2.),
                    xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=9, fontweight="bold")
                    
    plt.savefig(os.path.join(PLOT_DIR, "eda_2_top_tags.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 2: {e}")

# 3. AVERAGE SCORE BY TAG

print("Generating Plot 3: Average Score by Tag...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "avg_score_by_tag.csv"))
    df_top20 = df.head(20).copy()
    df_top20 = df_top20.sort_values("avg_score", ascending=True)
    
    plt.figure(figsize=(10, 7))
    ax = sns.barplot(x="avg_score", y="Tag", data=df_top20, color=MAIN_COLOR, edgecolor="black", linewidth=0.8)
    plt.title("Average Upvote Score by Top 20 Programming Tags", pad=15, fontweight="bold")
    plt.xlabel("Average Score (Upvotes - Downvotes)", labelpad=10)
    plt.ylabel("Technology Tag", labelpad=10)
    
    # Annotate values
    for p in ax.patches:
        ax.annotate(f"{p.get_width():.2f}", 
                    (p.get_width(), p.get_y() + p.get_height() / 2.),
                    xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=9, fontweight="bold")
                    
    plt.savefig(os.path.join(PLOT_DIR, "eda_3_avg_score.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 3: {e}")

# 4. TEXT LENGTH VS SCORE

print("Generating Plot 4: Text Length vs Score...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "length_vs_score.csv"))
    plt.figure(figsize=(9, 6))
    
    # Pearson correlation computation
    corr_val = df['text_length'].corr(df['Score'])
    
    sns.scatterplot(x="text_length", y="Score", data=df, alpha=0.3, color=MAIN_COLOR, edgecolor="none")
    plt.title(f"Question Body Length vs. Community Score\n(Pearson Correlation r = {corr_val:.6f})", pad=15, fontweight="bold")
    plt.xlabel("Question Word/Character Count (text_length)", labelpad=10)
    plt.ylabel("Community Score", labelpad=10)
    
    plt.savefig(os.path.join(PLOT_DIR, "eda_4_length_vs_score.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 4: {e}")

# 5. QUESTIONS PER YEAR

print("Generating Plot 5: Questions per Year...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "questions_per_year.csv"))
    df = df.sort_values("year")
    
    plt.figure(figsize=(9, 5))
    plt.plot(df["year"], df["count"], marker='o', color=MAIN_COLOR, linewidth=2.5, markersize=8)
    plt.title("Stack Overflow Question Growth Over Time (2008-2016)", pad=15, fontweight="bold")
    plt.xlabel("Year of Question Submission", labelpad=10)
    plt.ylabel("Number of Questions", labelpad=10)
    plt.xticks(df["year"])
    
    # Annotate values
    for x, y in zip(df["year"], df["count"]):
        plt.annotate(f"{y:,}", (x, y), xytext=(0, 10), textcoords="offset points", ha="center", va="bottom",
                     fontsize=9, fontweight="bold")
                     
    plt.savefig(os.path.join(PLOT_DIR, "eda_5_growth.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 5: {e}")

# 6. TOP TAGS TRENDS

print("Generating Plot 6: Top Tags Trends...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "top_tags_over_time.csv"))
    plt.figure(figsize=(10, 6))
    
    # Draw a line for each of the top 5 tags
    tags = ["python", "javascript", "java", "c#", "php"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    
    for tag, color in zip(tags, colors):
        tag_df = df[df["tag"] == tag].sort_values("year")
        plt.plot(tag_df["year"], tag_df["count"], marker='o', label=tag, color=color, linewidth=2)
        
    plt.title("Yearly Growth Trends of Top 5 Programming Tags", pad=15, fontweight="bold")
    plt.xlabel("Year", labelpad=10)
    plt.ylabel("Number of Questions", labelpad=10)
    plt.legend(title="Programming Tag")
    
    plt.savefig(os.path.join(PLOT_DIR, "eda_6_trends.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 6: {e}")

# 7. CLOSED VS OPEN

print("Generating Plot 7: Closed vs Open...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "closed_vs_open.csv"))
    
    # If open is missing because of dataset filtering, we can check or mock
    # Let's see if we have multiple categories, if not let's add one if missing
    if len(df) == 1 and df.iloc[0]["status"] == "closed":
        # We only have closed (probably due to Spark schema parsing/data). Let's plot it
        plt.figure(figsize=(6, 5))
        ax = sns.barplot(x="status", y="count", data=df, color=MAIN_COLOR, edgecolor="black", linewidth=1.2)
        plt.title("Closed vs Open Questions Volume Comparison", pad=15, fontweight="bold")
        plt.xlabel("Status", labelpad=10)
        plt.ylabel("Count", labelpad=10)
        for p in ax.patches:
            ax.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', xytext=(0, 8), textcoords='offset points', fontweight="bold")
    else:
        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax2 = ax1.twinx()
        
        sns.barplot(x="status", y="count", data=df, ax=ax1, color=MAIN_COLOR, alpha=0.8, edgecolor="black")
        sns.lineplot(x="status", y="avg_score", data=df, ax=ax2, marker="o", color="red", linewidth=2.5, markersize=8)
        
        ax1.set_title("Closed vs. Open Questions Volume & Avg Score", pad=15, fontweight="bold")
        ax1.set_xlabel("Question Status", labelpad=10)
        ax1.set_ylabel("Number of Questions", color=MAIN_COLOR, labelpad=10)
        ax2.set_ylabel("Average Score", color="red", labelpad=10)
        ax1.tick_params(axis='y', labelcolor=MAIN_COLOR)
        ax2.tick_params(axis='y', labelcolor="red")
        
    plt.savefig(os.path.join(PLOT_DIR, "eda_7_closed_open.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 7: {e}")

# 8. CONFUSION MATRIX HEATMAP

print("Generating Plot 8: Confusion Matrix Heatmap...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "confusion_matrix.csv"))
    df = df.set_index("primary_tag_predicted_label")
    df = df.reindex(index=df.columns)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt="d", cmap="Blues", cbar=True, linewidths=0.5, linecolor="#eeeeee")
    plt.title("Random Forest Classification Confusion Matrix Heatmap", pad=20, fontweight="bold")
    plt.xlabel("Actual Label (Target)", labelpad=15)
    plt.ylabel("Predicted Label (Model)", labelpad=15)
    plt.xticks(rotation=45, ha="right")
    
    plt.savefig(os.path.join(PLOT_DIR, "model_1_confusion_matrix.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 8: {e}")

# 9. PER-CLASS ACCURACY

print("Generating Plot 9: Per-Class Accuracy...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "per_class_accuracy.csv"))
    df["accuracy_percent"] = df["accuracy"] * 100
    df = df.sort_values("accuracy_percent", ascending=True)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="accuracy_percent", y="tag", data=df, color=MAIN_COLOR, edgecolor="black", linewidth=0.8)
    plt.title("Classifier Per-Class Accuracy by Tag Category", pad=15, fontweight="bold")
    plt.xlabel("Accuracy Percentage (%)", labelpad=10)
    plt.ylabel("Technology Tag", labelpad=10)
    plt.xlim(0, 105)
    
    # Annotate percentage values
    for p in ax.patches:
        ax.annotate(f"{p.get_width():.2f}%", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=9, fontweight="bold")
                    
    plt.savefig(os.path.join(PLOT_DIR, "model_2_class_accuracy.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 9: {e}")

# 10. FEATURE IMPORTANCES

print("Generating Plot 10: Feature Importances...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "feature_importances.csv"))
    df_top20 = df.head(20).copy()
    df_top20 = df_top20.sort_values("importance", ascending=True)
    
    plt.figure(figsize=(10, 7))
    ax = sns.barplot(x="importance", y="word", data=df_top20, color=MAIN_COLOR, edgecolor="black", linewidth=0.8)
    plt.title("Random Forest NLP Feature Importances (Top 20 Terms)", pad=15, fontweight="bold")
    plt.xlabel("Relative Importance Score", labelpad=10)
    plt.ylabel("Vocabulary Term", labelpad=10)
    
    # Annotate values
    for p in ax.patches:
        ax.annotate(f"{p.get_width():.5f}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=8, fontweight="bold")
                    
    plt.savefig(os.path.join(PLOT_DIR, "model_3_feature_importance.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 10: {e}")

# 11. REGRESSION PREDICTIONS SCATTER

print("Generating Plot 11: Regression Predictions Scatter...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "regression_predictions.csv"))
    
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x="log_score", y="prediction", data=df, alpha=0.3, color=MAIN_COLOR, edgecolor="none")
    
    # Draw reference line y = x
    min_val = min(df["log_score"].min(), df["prediction"].min())
    max_val = max(df["log_score"].max(), df["prediction"].max())
    plt.plot([min_val, max_val], [min_val, max_val], color="red", linestyle="--", linewidth=1.5, label="Perfect Fit (y = x)")
    
    plt.title("Linear Regression Score Prediction: Actual vs. Predicted\n(Log-Scaled score: log1p)", pad=15, fontweight="bold")
    plt.xlabel("Actual Log Score", labelpad=10)
    plt.ylabel("Predicted Log Score", labelpad=10)
    plt.legend()
    
    plt.savefig(os.path.join(PLOT_DIR, "model_4_regression_predictions.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 11: {e}")

# 12. LDA MODEL SELECTION CURVES

print("Generating Plot 12: LDA Model Selection curves...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "lda_k_selection.csv"))
    df = df.sort_values("k")
    
    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    ax2 = ax1.twinx()
    
    line1, = ax1.plot(df["k"], df["log_perplexity"], marker='s', color="red", linewidth=2, label="Log Perplexity")
    line2, = ax2.plot(df["k"], df["log_likelihood"], marker='o', color="blue", linewidth=2, label="Log Likelihood")
    
    ax1.set_title("Latent Dirichlet Allocation (LDA) Model Selection Curves", pad=15, fontweight="bold")
    ax1.set_xlabel("Number of Latent Topics (k)", labelpad=10)
    ax1.set_ylabel("Log Perplexity (Lower is Better)", color="red", labelpad=10)
    ax2.set_ylabel("Log Likelihood (Higher is Better)", color="blue", labelpad=10)
    
    ax1.tick_params(axis='y', labelcolor="red")
    ax2.tick_params(axis='y', labelcolor="blue")
    ax1.set_xticks(df["k"])
    
    # Add combined legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper center")
    
    plt.savefig(os.path.join(PLOT_DIR, "model_5_lda_elbow.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 12: {e}")

# 13. LDA TOPIC KEYWORD HEATMAP

print("Generating Plot 13: LDA Topic Keyword Heatmap...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "lda_topics.csv"), keep_default_na=False)
    
    # Clean vocabulary strings in case there are nan words saved as string 'NaN'
    df["word"] = df["word"].astype(str)
    
    # Pivot weights
    pivot_df = df.pivot(index='topic_label', columns='word', values='weight').fillna(0)
    
    # Select top 30 terms by overall weight across all topics
    top_words = df.groupby('word')['weight'].sum().nlargest(30).index.tolist()
    pivot_sub = pivot_df[top_words]
    
    plt.figure(figsize=(14, 8))
    sns.heatmap(pivot_sub, annot=True, fmt=".4f", cmap="YlGnBu", cbar=True, linewidths=0.5)
    plt.title("LDA Topic-Word Weight Distribution (Top 30 Overall Terms)", pad=20, fontweight="bold")
    plt.xlabel("Vocabulary Word", labelpad=15)
    plt.ylabel("Latent Topic", labelpad=15)
    plt.xticks(rotation=45, ha="right")
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "model_6_lda_topics_heatmap.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 13: {e}")

# 14. DOMINANT TOPIC DISTRIBUTION

print("Generating Plot 14: Dominant Topic Distribution...")
try:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "topic_distribution.csv"))
    df = df.sort_values("count", ascending=True)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="count", y="topic_label", data=df, color=MAIN_COLOR, edgecolor="black", linewidth=0.8)
    plt.title("Document Distribution across Latent LDA Topics", pad=15, fontweight="bold")
    plt.xlabel("Number of Questions (Dominant Topic)", labelpad=10)
    plt.ylabel("Latent Topic Label", labelpad=10)
    
    # Annotate values
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width()):,}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    xytext=(8, 0), textcoords="offset points", ha="left", va="center", fontsize=9, fontweight="bold")
        
    plt.savefig(os.path.join(PLOT_DIR, "model_7_topic_dist.png"))
    plt.close()
except Exception as e:
    print(f"Error Plot 14: {e}")
print("=" * 60)
print("ALL PLOTS GENERATED SUCCESSFULLY UNDER Outputs/Plots/")
print("=" * 60)