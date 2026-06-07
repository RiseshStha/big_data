"""Map appendix Tableau images to section 2.6 figures by hash comparison."""
import os
import hashlib

APPENDIX = r"D:/Data Science/Big Data and Data Visualization/Assignment/Project/appendix_tableau_extracted"
BACKUP = r"D:/Data Science/Big Data and Data Visualization/Assignment/Project/extracted_images"
PLOTS = r"D:/Data Science/Big Data and Data Visualization/Assignment/Project/Outputs/Plots"


def md5path(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_hashes(folder, prefix=""):
    out = {}
    if not os.path.isdir(folder):
        return out
    for f in sorted(os.listdir(folder)):
        if f.endswith(".png"):
            key = prefix + f if prefix else f
            out[key] = md5path(os.path.join(folder, f))
    return out


def find_match(target_hash, pools):
    for name, h in pools.items():
        if h == target_hash:
            return name
    return None


def main():
    appendix = load_hashes(APPENDIX)
    backup = load_hashes(BACKUP, "backup/")
    plots = load_hashes(PLOTS, "plot/")
    all_pools = {**appendix, **backup, **plots}

    section26_labels = {
        "rId14": "Fig 2.8 Growth Over Time",
        "rId15": "Fig 2.9 Top 20 Avg Score",
        "rId16": "Fig 2.10 Top 20 Tags Volume",
        "rId17": "Fig 2.11 Score Category Dist",
        "rId18": "Fig 2.12 Closed vs Open",
        "rId19": "Fig 2.13 Top 5 Tag Trends",
    }

    # Current section 2.6 blobs from doc
    import docx
    doc = docx.Document(r"D:/Data Science/Big Data and Data Visualization/Assignment/Documents/Big Data only Intro to ref.docx")

    print("=== CURRENT SECTION 2.6 IMAGE SOURCES ===")
    for rid, label in section26_labels.items():
        blob = doc.part.related_parts[rid]._blob
        h = hashlib.md5(blob).hexdigest()
        match = find_match(h, all_pools)
        print(f"{rid} {label}")
        print(f"  hash={h[:16]}... -> {match or 'NO MATCH'}")

    print("\n=== APPENDIX TABLEAU CANDIDATES (P#145-P#151 area) ===")
    tableau_rids = ["rId22", "rId15", "rId14", "rId23", "rId24", "rId25", "rId26", "rId27", "rId28", "rId29", "rId30"]
    for rid in tableau_rids:
        fname = f"appendix_{rid}.png"
        path = os.path.join(APPENDIX, fname)
        if os.path.exists(path):
            h = md5path(path)
            plot_match = find_match(h, plots)
            backup_match = find_match(h, backup)
            print(f"{rid}: plot={plot_match or '-'} backup={backup_match or '-'} size={os.path.getsize(path)}")

    print("\n=== BACKUP image10-15 vs PLOTS eda_* ===")
    pairs = [
        ("image10.png", "eda_5_growth.png"),
        ("image11.png", "eda_3_avg_score.png"),
        ("image12.png", "eda_2_top_tags.png"),
        ("image13.png", "eda_1_score_dist.png"),
        ("image14.png", "eda_7_closed_open.png"),
        ("image15.png", "eda_6_trends.png"),
    ]
    for b, p in pairs:
        bh = md5path(os.path.join(BACKUP, b))
        ph = md5path(os.path.join(PLOTS, p))
        same = "SAME(matplotlib)" if bh == ph else "DIFFERENT(Tableau vs matplotlib)"
        print(f"  {b} vs {p}: {same}")


if __name__ == "__main__":
    main()
