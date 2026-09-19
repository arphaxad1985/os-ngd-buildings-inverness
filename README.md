# OS NGD Buildings — Completeness & Currency Profiling (Inverness)

A reproducible data science investigation into the quality of the **OS National Geographic Database (NGD) Buildings** dataset, using the Inverness sample area.

This project answers a practical question that any data custodian faces: **is this dataset fit for purpose, and where are the gaps?** It profiles completeness and currency at scale, forms defensible hypotheses about why the gaps exist, and produces a recommendation a custodian can act on.

---

## 📊 Live Dashboard

Interactive Streamlit dashboard presenting the findings.

**Live demo:** https://os-ngd-buildings-inverness-8cwzuntbd6bwjrotntctwt.streamlit.app

**Run locally:**

```bash
conda activate geo
streamlit run app.py
```

The dashboard includes:

- **Executive Summary** — headline findings and recommendation
- **Completeness Analysis** — null profile with interpretation
- **Currency Analysis** — record age distribution and snapshot finding
- **Building Age Analysis** — coverage and distribution bias
- **Data** — supporting attribute table

---

## 🎯 Objective

To quantify the **completeness** and **currency** of the OS NGD Buildings dataset and investigate the root cause of any significant gaps.

Three research questions guided the investigation:

1. **Which attributes are complete, and which are not?**
2. **How current is the data?**
3. **Is there a pattern to the missing data that explains *why* it occurs?**

---

## 📁 Data

| Property | Value |
|----------|-------|
| Product | OS NGD Buildings |
| Provider | Ordnance Survey, via OS Data Hub |
| Sample area | Inverness |
| Format | GeoPackage (`.gpkg`) |
| Source layer | `bld_fts_building` |
| Feature count | 37,586 building polygons |
| CRS | EPSG:27700 (British National Grid) |

The source file (`data/inverness.gpkg`, 52 MB) is committed to this repository for reproducibility and to support the Streamlit deployment.

To re-download it:

1. Go to the OS Data Hub: https://osdatahub.os.uk/downloads/open
2. Search for **OS NGD Buildings**
3. Select the **Inverness** sample area
4. Download in **GeoPackage** format
5. Save as `data/inverness.gpkg`

---

## 🧪 Methodology

The workflow is fully scripted and reproducible in `inverness_completeness.py`.

### Step 1 — Define columns of interest

Ten attributes were selected for profiling based on their importance for building analysis:

| Category | Columns |
|----------|---------|
| Identity | `osid`, `geometry_area_m2` |
| Core attributes | `numberoffloors`, `height_relativemax_m`, `height_absolutemax_m`, `buildingage_year`, `buildingage_period`, `roofmaterial_primarymaterial`, `constructionmaterial`, `basementpresence` |

### Step 2 — Profile completeness

Null counts and null percentages were calculated per column across all 37,586 features.

### Step 3 — Profile currency

Record age was derived from the `versiondate` field. The proportion of records updated within 12, 24, and 36 months was calculated.

### Step 4 — Analyse building age distribution

The distribution of `buildingage_year` was plotted for records where it was populated.

### Step 5 — Form a root-cause hypothesis

The null pattern was examined for structure — does the missingness correlate with anything?

---

## 🔍 Findings

### Finding 1 — Completeness follows a capture-difficulty pattern

| Tier | Columns | Null % |
|------|---------|--------|
| **Complete** | `osid`, `geometry_area_m2` | 0.00% |
| **Nearly complete** | `roofmaterial_primarymaterial` | 0.13% |
| **Moderate gap** | `height_relativemax_m`, `height_absolutemax_m`, `buildingage_period`, `constructionmaterial`, `basementpresence`, `numberoffloors` | 17–40% |
| **Critical gap** | `buildingage_year` | **76.01%** |

**Interpretation:** the null rate correlates with how difficult the attribute is to capture. Attributes visible from imagery (roof material) are almost always present. Attributes requiring survey, inference, or third-party records (building age) are frequently absent.

### Finding 2 — The dataset is a snapshot, not a live feed

| Metric | Value |
|--------|-------|
| Earliest record | 2025-03-11 |
| Latest record | 2025-08-11 |
| Updated within 12 months | **0%** |
| Updated within 24 months | 100% |

All records were created or last updated within a single five-month window. **Analysts should not treat this dataset as current.**

### Finding 3 — The building age data is incomplete *and* biased

| Metric | Value |
|--------|-------|
| Records with a construction year | 9,018 of 37,586 (24.0%) |
| Earliest year | 1600 |
| Latest year | 2025 |
| Median year | **2018** |

When `buildingage_year` *is* populated, the median construction year is **2018** — heavily skewed toward recent buildings. Older buildings are disproportionately missing from the age data.

This is a second, subtler quality issue: the age data is not merely incomplete, it is **biased**. The buildings most relevant to heritage, retrofit, and asbestos planning are precisely the ones missing from the dataset.

---

## 🧠 Root-Cause Hypothesis

The completeness gaps are not random. They follow a clear structure:

1. **Capture method drives completeness.** Attributes derivable from imagery (roof material) or calculation (geometry area) are nearly complete. Attributes requiring physical survey or third-party data linkage (building age, floor count) show the largest gaps.

2. **The currency finding suggests a snapshot release.** The narrow `versiondate` window implies this sample was extracted once, rather than maintained as a continuously updated feed.

3. **The age distribution is skewed.** Because building age is sourced from third-party records, coverage is strongest for recent builds — where such records are more likely to exist — and weakest for older stock.

---

## ✅ Recommendation

| Action | Rationale |
|--------|-----------|
| **Flag `buildingage_year` nulls for custodian review** | 76% of records missing, and the missingness is biased toward older buildings |
| **Confirm whether `buildingage_year` is mandatory or optional** | If optional, the null rate may be acceptable. If mandatory, it is a significant quality failure |
| **Treat the dataset as a snapshot for downstream use** | Analysts should not assume the data is current |
| **Investigate the age bias** | If older buildings are systematically missing, any analysis of building stock will be skewed |

---

## 🛠️ Technical Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.11 |
| Geospatial | GeoPandas 1.0.1, Shapely 2.1.1 |
| Data | Pandas 2.3.1 |
| Visualisation | Matplotlib 3.10.0 |
| Dashboard | Streamlit |
| GIS (inspection) | QGIS |

---

## 📂 Project Structure

```
inverness_completeness/
├── app.py                        # Streamlit dashboard
├── inverness_completeness.py     # Analysis script
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── inverness.gpkg            # Source data (52 MB)
└── outputs/                      # Generated reports and plots
    ├── inverness_completeness_report.md
    ├── inverness_null_report.csv
    ├── inverness_record_age.png
    └── inverness_building_age.png
```

---

## 🚀 Reproducing the Analysis

### Environment setup

This project uses a dedicated conda environment called `geo`.

```bash
conda create -n geo python=3.11 geopandas matplotlib tabulate streamlit
conda activate geo
```

> **Note on mamba:** If you have `mamba` installed, use `conda activate geo`
> rather than `mamba activate geo`. Mamba 2.x looks for environments in its
> own directory (`~/.local/share/mamba/envs/`), but this environment was
> created in conda's default location (`/opt/anaconda3/envs/geo`).
> Only `conda activate` will find it.

### Run the analysis script

```bash
python inverness_completeness.py data/inverness.gpkg
```

Outputs are written to `outputs/`:

| File | Purpose |
|------|---------|
| `inverness_completeness_report.md` | Full written report |
| `inverness_null_report.csv` | Null counts per column |
| `inverness_record_age.png` | Record currency histogram |
| `inverness_building_age.png` | Building age histogram |

### Run the dashboard

```bash
streamlit run app.py
```

Then open `http://localhost:8501`.

---

## 📌 What This Project Demonstrates

| Skill | Evidence |
|-------|----------|
| **Data quality profiling** | Null analysis across 10 columns of interest |
| **Currency analysis** | Record age distribution and snapshot detection |
| **Root-cause investigation** | Capture-difficulty hypothesis, backed by the null pattern |
| **Statistical thinking** | Distribution analysis, coverage vs bias distinction |
| **Geospatial handling** | GeoPackage, GeoPandas, CRS awareness |
| **Reproducible workflow** | Scripted, documented, version-controlled |
| **Communication** | Written findings, dashboard, recommendation |

---

## 📜 Licence and Attribution

Data: © Ordnance Survey, OS NGD Buildings, used under the Open Government Licence.

Analysis, code, and documentation: © Arphaxad Nguka Owange, 2026.