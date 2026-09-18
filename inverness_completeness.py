"""
Inverness — Completeness & Currency Profiling
OS NGD Buildings Data Quality Case Study

Usage:
    python inverness_completeness.py data/inverness.gpkg
"""

import os
import sys
import geopandas as gpd
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


def run_completeness_analysis(gpkg_path, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load Data
    # ------------------------------------------------------------------
    print(f"Loading: {gpkg_path}")
    layers = gpd.list_layers(gpkg_path)
    print(f"Layers found:\n{layers}\n")

    layer_name = "bld_fts_building"
    gdf = gpd.read_file(gpkg_path, layer=layer_name)

    total_features = len(gdf)
    print(f"Features: {total_features:,}")

    report_lines = [
        f"# Completeness & Currency Report — Inverness\n",
        f"**Total Features:** {total_features:,}\n",
        f"**Source layer:** `{layer_name}`\n",
    ]

    # ------------------------------------------------------------------
    # 2. Completeness: Null Count per Column of Interest
    # ------------------------------------------------------------------
    report_lines.append("\n## 1. Completeness: Null Analysis\n")

    columns_of_interest = [
        # Identity
        'osid',
        'geometry_area_m2',
        # Core building attributes
        'numberoffloors',
        'height_relativemax_m',
        'height_absolutemax_m',
        'buildingage_year',
        'buildingage_period',
        'roofmaterial_primarymaterial',
        'constructionmaterial',
        'basementpresence',
    ]

    # Only keep columns that actually exist in the dataset
    cols_present = [c for c in columns_of_interest if c in gdf.columns]
    cols_missing = [c for c in columns_of_interest if c not in gdf.columns]

    if cols_missing:
        report_lines.append(f"**Columns not found in dataset:** {', '.join(cols_missing)}\n")

    null_summary = []
    for col in cols_present:
        null_count = gdf[col].isna().sum()
        null_pct = (null_count / total_features) * 100
        null_summary.append({
            "Column": col,
            "Null Count": null_count,       # integer for correct sorting
            "Null %": round(null_pct, 2),   # float for correct sorting
        })

    null_df = pd.DataFrame(null_summary).sort_values("Null Count", ascending=False)
    report_lines.append(null_df.to_markdown(index=False))
    report_lines.append("")

    # Save CSV
    null_df.to_csv(f"{output_dir}/inverness_null_report.csv", index=False)

    # ------------------------------------------------------------------
    # 3. Currency: Record Age Analysis
    # ------------------------------------------------------------------
    report_lines.append("\n## 2. Currency: Record Age\n")

    date_col = 'versiondate'

    if date_col in gdf.columns:
        report_lines.append(f"Using date column: `{date_col}`\n")

        # Parse dates
        dates = pd.to_datetime(gdf[date_col], errors='coerce')
        valid_dates = dates.dropna()

        if len(valid_dates) > 0:
            now = datetime.now()
            age_days = (now - valid_dates).dt.days

            within_12 = (age_days <= 365).sum()
            within_24 = (age_days <= 730).sum()
            within_36 = (age_days <= 1095).sum()

            report_lines.append(f"- **Earliest Record:** {valid_dates.min().date()}")
            report_lines.append(f"- **Latest Record:** {valid_dates.max().date()}")
            report_lines.append(f"- **Updated within 12 months:** {within_12:,} ({within_12/total_features*100:.1f}%)")
            report_lines.append(f"- **Updated within 24 months:** {within_24:,} ({within_24/total_features*100:.1f}%)")
            report_lines.append(f"- **Updated within 36 months:** {within_36:,} ({within_36/total_features*100:.1f}%)")
            report_lines.append(f"- **No parseable date:** {dates.isna().sum():,} ({dates.isna().sum()/total_features*100:.1f}%)")

            # Histogram — Record Age
            fig, ax = plt.subplots(figsize=(10, 5))
            age_years = age_days / 365.25
            ax.hist(age_years, bins=30, edgecolor='black', color='steelblue')
            ax.set_xlabel("Record Age (Years)")
            ax.set_ylabel("Count")
            ax.set_title("Record Age Distribution — Inverness")
            plt.tight_layout()
            hist_path = f"{output_dir}/inverness_record_age.png"
            plt.savefig(hist_path, dpi=150)
            plt.close()
            report_lines.append(f"\nHistogram saved: `{hist_path}`\n")
        else:
            report_lines.append("No valid dates found in versiondate column.\n")
    else:
        report_lines.append(f"Column `{date_col}` not found in dataset. Currency analysis skipped.\n")

    # ------------------------------------------------------------------
    # 3b. Building Age Distribution
    # ------------------------------------------------------------------
    report_lines.append("\n## 3. Building Age Distribution\n")

    if 'buildingage_year' in gdf.columns:
        ages = gdf['buildingage_year'].dropna()
        report_lines.append(
            f"- Buildings with a recorded construction year: "
            f"{len(ages):,} of {total_features:,} "
            f"({len(ages)/total_features*100:.1f}%)"
        )

        if len(ages) > 0:
            report_lines.append(f"- Earliest year: {int(ages.min())}")
            report_lines.append(f"- Latest year: {int(ages.max())}")
            report_lines.append(f"- Median year: {int(ages.median())}")

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.hist(ages, bins=40, edgecolor='black', color='seagreen')
            ax.set_xlabel("Building construction year")
            ax.set_ylabel("Count")
            ax.set_title("Building Age Distribution — Inverness")
            plt.tight_layout()
            age_path = f"{output_dir}/inverness_building_age.png"
            plt.savefig(age_path, dpi=150)
            plt.close()
            report_lines.append(f"\nHistogram saved: `{age_path}`\n")
        else:
            report_lines.append("No valid years found.\n")
    else:
        report_lines.append("Column `buildingage_year` not found in dataset.\n")

    # ------------------------------------------------------------------
    # 4. Findings & Recommendation (The Root-Cause Part)
    # ------------------------------------------------------------------
    report_lines.append("\n## 4. Findings & Recommendation\n")

    worst_nulls = null_df[null_df["Null Count"] > 0] if len(null_df) > 0 else pd.DataFrame()

    if len(worst_nulls) > 0:
        top_gap = worst_nulls.iloc[0]
        report_lines.append(
            f"- The largest completeness gap is in `{top_gap['Column']}` "
            f"({top_gap['Null %']}% null)."
        )
        report_lines.append(
            "- **Hypothesis:** The null rate correlates with how difficult the attribute "
            "is to capture. Attributes visible from imagery (e.g. roof material) are nearly "
            "complete, while attributes requiring survey or third-party records "
            "(e.g. building age) show the largest gaps."
        )
        report_lines.append(
            f"- **Recommendation:** Investigate whether `{top_gap['Column']}` is mandatory "
            "for all building types. If yes, flag affected features for custodian review."
        )
    else:
        report_lines.append("- No significant nulls detected in the columns of interest.")

    # ------------------------------------------------------------------
    # 5. Write Report
    # ------------------------------------------------------------------
    report_path = f"{output_dir}/inverness_completeness_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\nReport written: {report_path}")
    return report_path


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/inverness.gpkg"
    run_completeness_analysis(path)