import os
import shutil
import docx

doc_dir = "D:/Data Science/Big Data and Data Visualization/Assignment/Documents"
doc_name = "Big Data only Intro to ref.docx"
doc_path = os.path.join(doc_dir, doc_name)
backup_path = os.path.join(doc_dir, "Big Data only Intro to ref_backup.docx")

# Mapping of relationship IDs to the correct plot filenames
# Verified against document structure (rId7-rId19 in main body figures)
plot_dir = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/Plots"
tableau_dir = "D:/Data Science/Big Data and Data Visualization/Assignment/Project/extracted_images"

image_mapping = {
    # Section 2.3 (Random Forest classification)
    "rId7": (plot_dir, "model_1_confusion_matrix.png"),       # Figure 2.1 Confusion Matrix
    "rId8": (plot_dir, "model_2_class_accuracy.png"),          # Figure 2.2 Per-Class Accuracy
    "rId9": (plot_dir, "model_3_feature_importance.png"),      # Figure 2.3 Feature Importances
    # Section 2.4 (Linear Regression)
    "rId10": (plot_dir, "model_4_regression_predictions.png"),  # Figure 2.4 Regression Scatter
    # Section 2.5 (LDA topic modelling)
    "rId11": (plot_dir, "model_5_lda_elbow.png"),              # Figure 2.5 LDA Elbow Curves
    "rId12": (plot_dir, "model_6_lda_topics_heatmap.png"),     # Figure 2.6 LDA Topics Heatmap
    "rId13": (plot_dir, "model_7_topic_dist.png"),             # Figure 2.7 Topic Distribution
    # Section 2.6 (Tableau visualisation — backup screenshots)
    "rId14": (tableau_dir, "image10.png"),                     # Figure 2.8 Growth Over Time
    "rId15": (tableau_dir, "image11.png"),                     # Figure 2.9 Top 20 by Avg Score
    "rId16": (tableau_dir, "image12.png"),                     # Figure 2.10 Top 20 Tags Distribution
    "rId17": (tableau_dir, "image13.png"),                     # Figure 2.11 Score Category Distribution
    "rId18": (tableau_dir, "image14.png"),                     # Figure 2.12 Closed vs Open
    "rId19": (tableau_dir, "image15.png"),                     # Figure 2.13 Yearly Growth Trends
}

if not os.path.exists(doc_path):
    print("Error: Document not found at:", doc_path)
    exit(1)

# Step 1: Create backup copy
print(f"Creating backup of the original document at: {backup_path}")
shutil.copy2(doc_path, backup_path)

# Step 2: Load document using python-docx
print("Loading document...")
doc = docx.Document(doc_path)

# Step 3: Overwrite image parts in-place
print("\n=== Updating Figures in Document ===")
updated_count = 0
for rid, (img_dir, plot_name) in image_mapping.items():
    plot_path = os.path.join(img_dir, plot_name)
    if not os.path.exists(plot_path):
        print(f"Warning: Plot file not found at: {plot_path}. Skipping.")
        continue
        
    if rid in doc.part.related_parts:
        part = doc.part.related_parts[rid]
        print(f"Replacing relationship {rid} with {plot_name}...")
        try:
            # Overwrite the binary blob of the image part
            with open(plot_path, "rb") as img_file:
                part._blob = img_file.read()
            print(f"  Successfully updated relationship {rid} with {plot_name}.")
            updated_count += 1
        except Exception as e:
            print(f"  Failed to update relationship {rid}: {e}")
    else:
        print(f"Warning: Relationship {rid} not found in the document parts.")

# Step 4: Save the modified document
print(f"\nSaving updated document to: {doc_path}")
doc.save(doc_path)
print(f"Updated {updated_count} figures successfully!")
