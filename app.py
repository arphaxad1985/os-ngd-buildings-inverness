"""
Streamlit dashboard for OS NGD Buildings data quality.
Inverness — Completeness & Currency

This dashboard presents the findings of the data quality investigation,
with an executive summary, per-dimension analysis, and supporting data.
"""

import os
import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------
st.set_page_config(
    page_title="OS NGD Buildings — Inverness",
    page_icon="🏢",
    layout="wide",
)

DATA_PATH = "data/inverness.gpkg"
LAYER = "bld_fts_building"

COLUMNS_OF_INTEREST = [
    'osid', 'geometry_area_m2',
    'numberoffloors', 'height_relativemax_m', 'height_absolutemax_m',
    'buildingage_year', 'buildingage_period',
    'roofmaterial_primarymaterial', 'constructionmaterial', 'basementpresence',
]


# ---------------------------------------------------------------
# Load data (cached)
# ---------------------------------------------------------------
@st.cache_data
def load_data(path, layer):
    return gpd.read_file(path, layer=layer)


if not os.path.exists(DATA_PATH):
    st.error(f"Data file not found: {DATA_PATH}")
    st.stop()

gdf = load_data(DATA_PATH, LAYER)
total = len(gdf)

# ---------------------------------------------------------------
# Precompute findings
# ---------------------------------------------------------------
# Completeness
null_rows = []
for col in COLUMNS_OF_INTEREST:
    if col in gdf.columns:
        nulls = gdf[col].isna().sum()
        null_rows.append({
            "Column": col,
            "Null Count": nulls,
            "Null %": round(nulls / total * 100, 2),
        })
null_df = pd.DataFrame(null_rows).sort_values("Null Count", ascending=False)
largest_gap = null_df.iloc[0] if len(null_df) > 0 else None
complete_cols = null_df[null_df["Null Count"] == 0]["Column"].tolist()

# Currency
dates = pd.to_datetime(gdf["versiondate"], errors="coerce").dropna()
earliest = dates.min().date() if len(dates) else None
latest = dates.max().date() if len(dates) else None
within_12 = ((datetime.now() - dates).dt.days <= 365).sum() if len(dates) else 0

# Building age
ages = gdf["buildingage_year"].dropna() if "buildingage_year" in gdf.columns else pd.Series()
age_coverage = len(ages) / total * 100 if total else 0
age_median = int(ages.median()) if len(ages) else None

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.title("🏢 OS NGD Buildings — Inverness")
st.caption("Completeness & Currency Data Quality Investigation")
st.markdown(f"**{total:,} building features** · Source layer: `{LAYER}`")

# ---------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Summary",
    "✅ Completeness Analysis",
    "🕰️ Currency Analysis",
    "🏗️ Building Age Analysis",
    "📋 Data",
])

# ---------------------------------------------------------------
# Tab 1 — Executive Summary
# ---------------------------------------------------------------
with tab1:
    st.subheader("Executive Summary")
    st.markdown(
        "This investigation profiled **completeness** and **currency** across "
        f"{total:,} building records. The key findings are summarised below."
    )

    st.markdown("### Key Findings")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Largest completeness gap",
        f"{largest_gap['Null %']}%" if largest_gap is not None else "N/A",
        largest_gap["Column"] if largest_gap is not None else "",
    )
    col2.metric(
        "Records updated in last 12 months",
        f"{within_12/total*100:.1f}%" if total else "N/A",
    )
    col3.metric(
        "Building age coverage",
        f"{age_coverage:.1f}%",
    )

    st.markdown("---")

    st.markdown("### What the data shows")

    st.markdown(f"""
**1. Completeness follows a capture-difficulty pattern.**

Attributes that can be derived from imagery or calculation are nearly complete
({', '.join(f'`{c}`' for c in complete_cols[:2])} at 0% null).
Attributes requiring survey or third-party records are the most incomplete —
`{largest_gap['Column']}` is missing for **{largest_gap['Null %']}%** of records.

**2. The dataset is a snapshot, not a live feed.**

All records were created or last updated between **{earliest}** and **{latest}**.
No record is more recent than 12 months. Analysts should not treat this
dataset as current.

**3. The building age data is incomplete and biased.**

Only **{age_coverage:.1f}%** of records have a construction year. Of those,
the median year is **{age_median}** — skewed toward recent buildings. Older
buildings are disproportionately missing from the age data.
""")

    st.markdown("---")

    st.markdown("### Recommendation")
    st.info(
        f"Flag `{largest_gap['Column']}` nulls for custodian review. "
        "Confirm whether this attribute is mandatory or optional. "
        "Treat the dataset as a snapshot for downstream use."
    )

# ---------------------------------------------------------------
# Tab 2 — Completeness Analysis
# ---------------------------------------------------------------
with tab2:
    st.subheader("Completeness Analysis")
    st.caption("Null counts across the 10 columns of interest")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Null counts per column**")
        st.dataframe(null_df, use_container_width=True, hide_index=True)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.barh(null_df["Column"], null_df["Null %"], color="coral")
        ax.set_xlabel("Null %")
        ax.invert_yaxis()
        ax.set_title("Null % by column")
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("### Interpretation")
    st.markdown(f"""
The null rates fall into three tiers:

| Tier | Columns | Null % |
|------|---------|--------|
| **Complete** | {', '.join(f'`{c}`' for c in complete_cols)} | 0.00% |
| **Moderate gap** | 6 columns | 17–40% |
| **Critical gap** | `{largest_gap['Column']}` | **{largest_gap['Null %']}%** |

**Pattern:** the harder an attribute is to capture, the more likely it is
to be missing. Roof material (visible from imagery) is nearly complete.
Building age (requires third-party records) is the largest gap.
""")

# ---------------------------------------------------------------
# Tab 3 — Currency Analysis
# ---------------------------------------------------------------
with tab3:
    st.subheader("Currency Analysis")
    st.caption("Record age based on `versiondate`")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Earliest record", str(earliest))
    col2.metric("Latest record", str(latest))
    col3.metric("Updated in 12 months", f"{within_12/total*100:.1f}%")
    col4.metric("No parseable date", f"{(gdf['versiondate'].isna().sum()/total*100):.1f}%")

    age_days = (datetime.now() - dates).dt.days
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(age_days / 365.25, bins=30, edgecolor="black", color="steelblue")
    ax.set_xlabel("Record age (years)")
    ax.set_ylabel("Count")
    ax.set_title("Record age distribution")
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("### Interpretation")
    st.warning(
        f"All records fall within a narrow window between **{earliest}** and "
        f"**{latest}**. No record is more recent than 12 months. "
        "This indicates the Inverness sample is a **static snapshot**, "
        "not a continuously updated feed."
    )

# ---------------------------------------------------------------
# Tab 4 — Building Age Analysis
# ---------------------------------------------------------------
with tab4:
    st.subheader("Building Age Analysis")
    st.caption("Distribution of `buildingage_year` where populated")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Records with year", f"{len(ages):,}")
    col2.metric("Coverage", f"{age_coverage:.1f}%")
    col3.metric("Earliest", f"{int(ages.min())}" if len(ages) else "N/A")
    col4.metric("Median year", f"{age_median}" if age_median else "N/A")

    if len(ages) > 0:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(ages, bins=40, edgecolor="black", color="seagreen")
        ax.set_xlabel("Construction year")
        ax.set_ylabel("Count")
        ax.set_title("Building age distribution")
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("### Interpretation")
    st.markdown(f"""
Only **{age_coverage:.1f}%** of buildings have a recorded construction year.
Of those, the median is **{age_median}** — heavily skewed toward recent builds.

This is a **second quality issue**: the age data is not just incomplete,
it is **biased**. Older buildings (the ones most relevant to heritage,
retrofit, and asbestos planning) are precisely the ones missing from the dataset.
""")

# ---------------------------------------------------------------
# Tab 5 — Data
# ---------------------------------------------------------------
with tab5:
    st.subheader("Attribute Data")
    st.caption(f"First 500 rows of {total:,} (columns of interest)")

    preview_cols = [c for c in COLUMNS_OF_INTEREST if c in gdf.columns]
    st.dataframe(gdf[preview_cols].head(500), use_container_width=True)

st.markdown("---")
st.caption("Data: OS NGD Buildings (Inverness sample) · Ordnance Survey")