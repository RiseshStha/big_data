"""
Replace Section 2.6 figures with actual Tableau images from the appendix.

Section 2.6 rIds (body): rId14-rId19
Tableau sources in appendix:
  - rId22: Tag Frequency Treemap
  - rId25: Closed vs Open Questions
  - rId26: Yearly Growth of Top 5 Tags
  - rId28: Score Category Distribution
  - rId29: Full EDA dashboard (crop Growth + Avg Score sheets)
"""
import os
import shutil
import docx
from PIL import Image
import io

DOC_PATH = r"D:/Data Science/Big Data and Data Visualization/Assignment/Documents/Big Data only Intro to ref.docx"
BACKUP_PATH = r"D:/Data Science/Big Data and Data Visualization/Assignment/Documents/Big Data only Intro to ref_pre_tableau.docx"
APPENDIX_DIR = r"D:/Data Science/Big Data and Data Visualization/Assignment/Project/appendix_tableau_extracted"
CROP_DIR = r"D:/Data Science/Big Data and Data Visualization/Assignment/Project/tableau_crops"
os.makedirs(CROP_DIR, exist_ok=True)


def blob_from_path(path):
    with open(path, "rb") as f:
        return f.read()


def blob_from_image(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def crop_dashboard_charts():
    """Extract individual Tableau sheets from the EDA dashboard PNG."""
    dash_path = os.path.join(APPENDIX_DIR, "appendix_rId29.png")
    img = Image.open(dash_path)
    w, h = img.size

    # Approximate layout of the 1366x768 dashboard scaled to 1431x580 export
    crops = {
        "tableau_growth_over_time.png": (int(w * 0.02), int(h * 0.52), int(w * 0.52), int(h * 0.98)),
        "tableau_avg_score_by_tag.png": (int(w * 0.34), int(h * 0.08), int(w * 0.66), int(h * 0.52)),
    }
    out = {}
    for name, box in crops.items():
        path = os.path.join(CROP_DIR, name)
        cropped = img.crop(box)
        cropped.save(path)
        out[name] = path
        print(f"  [CROP] {name} {cropped.size}")
    return out


def get_appendix_blob(doc, rid):
    """Read image bytes from an appendix relationship already in the document."""
    return doc.part.related_parts[rid]._blob


def main():
    print("=" * 70)
    print("  FIX SECTION 2.6 — USE TABLEAU IMAGES FROM APPENDIX")
    print("=" * 70)

    if not os.path.exists(DOC_PATH):
        print(f"ERROR: Document not found: {DOC_PATH}")
        return

    shutil.copy2(DOC_PATH, BACKUP_PATH)
    print(f"[BACKUP] {BACKUP_PATH}")

    doc = docx.Document(DOC_PATH)

    print("\n[CROP] Extracting Growth + Avg Score from EDA dashboard (rId29)...")
    crop_paths = crop_dashboard_charts()

    # Map section 2.6 body rIds -> Tableau image source
    replacements = {
        "rId14": ("crop", crop_paths["tableau_growth_over_time.png"], "Fig 2.8 Growth Over Time"),
        "rId15": ("crop", crop_paths["tableau_avg_score_by_tag.png"], "Fig 2.9 Avg Score by Tag"),
        "rId16": ("appendix", "rId22", "Fig 2.10 Tag Frequency Treemap"),
        "rId17": ("appendix", "rId28", "Fig 2.11 Score Category Distribution"),
        "rId18": ("appendix", "rId25", "Fig 2.12 Closed vs Open"),
        "rId19": ("appendix", "rId26", "Fig 2.13 Yearly Growth Top 5 Tags"),
    }

    print("\n[REPLACE] Section 2.6 images:")
    for rid, (source_type, source, label) in replacements.items():
        if rid not in doc.part.related_parts:
            print(f"  [WARN] {rid} not found in document")
            continue

        if source_type == "crop":
            data = blob_from_path(source)
        else:
            if source not in doc.part.related_parts:
                print(f"  [WARN] appendix source {source} not found")
                continue
            data = get_appendix_blob(doc, source)

        doc.part.related_parts[rid]._blob = data
        print(f"  [OK] {rid} <- {source} ({label})")

    try:
        doc.save(DOC_PATH)
        print(f"\n[SAVED] {DOC_PATH}")
    except PermissionError:
        alt = DOC_PATH.replace(".docx", "_TABLEAU_FIXED.docx")
        doc.save(alt)
        print(f"\n[LOCKED] Original file open in Word.")
        print(f"[SAVED] Alternate file: {alt}")
    print("=" * 70)


if __name__ == "__main__":
    main()
