# OS NGD Buildings — Completeness & Currency Profiling (Inverness)

A reproducible data quality investigation of the **OS National Geographic Database (NGD) Buildings** dataset for the Inverness sample area.

This project demonstrates a core workflow required for data quality assurance on national geospatial datasets: profiling completeness and currency, forming a defensible explanation for the gaps found, and producing a recommendation a data custodian can act on.

---

## 1. Objective

To quantify the **completeness** and **currency** of the OS NGD Buildings dataset for Inverness, and to investigate the root cause of any significant gaps.

Specifically:

- Which attributes are complete, and which are not?
- How current is the data?
- Is there a pattern to the missing data that explains *why* it occurs?

---

## 2. Data Source

| Property | Value |
|----------|-------|
| Product | OS NGD Buildings |
| Provider | Ordnance Survey, via OS Data Hub |
| Sample area | Inverness |
| Format | GeoPackage (`.gpkg`) |
| Source layer | `bld_fts_building` |
| Feature count | 37,586 building polygons |
| CRS | EPSG:27700 (British National Grid) |

---

## 3. Methodology

The workflow is fully scripted and reproducible in `inverness_completeness.py`.

### 3.1 Columns of interest

Ten attributes were selected for profiling, based on their importance for building analysis:

| Category | Columns |
|----------|---------|
| Identity | `osid`, `geometry_area_m2` |
| Core attributes | `numberoffloors`, `height_relativemax_m`, `height_absolutemax_m`, `buildingage_year`, `buildingage_period`, `roofmaterial_primarymaterial`, `constructionmaterial`, `basementpresence` |

### 3.2 Completeness

Null counts and null percentages were calculated per column across all 37,586 features.

### 3.3 Currency

Record age was derived from the `versiondate` field, and the proportion of records updated within 12, 24, and 36 months was calculated.

### 3.4 Building age distribution

The distribution of `buildingage_year` was plotted for records where it was populated.

---

## 4. Findings

### 4.1 Completeness — three tiers of quality

| Tier | Columns | Null % |
|------|---------|--------|
| **Complete** | `osid`, `geometry_area_m2` | 0.00% |
| **Nearly complete** | `roofmaterial_primarymaterial` | 0.13% |
| **Moderate gap** | `height_relativemax_m`, `height_absolutemax_m`, `buildingage_period`, `constructionmaterial`, `basementpresence`, `numberoffloors` | 17–40% |
| **Critical gap** | `buildingage_year` | **76.01%** |

**The pattern:** the null rate correlates with how difficult the attribute is to capture. Attributes visible from imagery (e.g. roof material) are almost always present. Attributes requiring survey, inference, or third-party records (e.g. building age) are frequently absent.

### 4.2 Currency — the dataset is a snapshot

| Metric | Value |
|--------|-------|
| Earliest record | 2025-03-11 |
| Latest record | 2025-08-11 |
| Updated within 12 months | **0%** |
| Updated within 24 months | 100% |

All records were created or last updated within a single five-month window in 2025. **This is a static snapshot, not a live feed.** No record has been updated in the last 12 months.

### 4.3 Building age — a biased sample

| Metric | Value |
|--------|-------|
| Records with a construction year | 9,018 of 37,586 (24.0%) |
| Earliest year | 1600 |
| Latest year | 2025 |
| Median year | **2018** |

When `buildingage_year` *is* populated, the median construction year is **2018** — heavily skewed toward recent buildings. Older buildings are disproportionately missing from the age data.

This is a second, subtler quality issue: the age data is not merely incomplete, it is **biased**. The buildings most relevant to heritage, retrofit, and asbestos planning are precisely the ones missing from the dataset.

---

## 5. Root-Cause Hypothesis

The completeness gaps are not random. They follow a clear pattern:

1. **Capture method drives completeness.** Attributes that can be derived from aerial imagery (roof material) or calculated (geometry area) are nearly complete. Attributes that require physical survey or third-party data linkage (building age, floor count) show the largest gaps.

2. **The currency finding suggests a snapshot release.** The narrow `versiondate` window implies this sample was extracted once, rather than maintained as a continuously updated feed.

3. **The age distribution is skewed.** Because building age is sourced from third-party records (e.g. HMLR, VOA), coverage is strongest for recent builds — where such records are more likely to exist — and weakest for older stock.

---

## 6. Recommendation

| Action | Rationale |
|--------|-----------|
| **Flag `buildingage_year` nulls for custodian review** | 76% of records are missing this attribute, and the missing values are biased toward older buildings |
| **Confirm whether `buildingage_year` is mandatory or optional** | If optional, the null rate may be acceptable. If mandatory, it is a significant quality failure |
| **Treat the dataset as a snapshot for downstream use** | Analysts should not assume the data is current |
| **Investigate the age bias** | If older buildings are systematically missing, any analysis of building stock will be skewed |

---

## 7. Reproducibility

| File | Purpose |
|------|---------|
| `inverness_completeness.py` | The full analysis script |
| `requirements.txt` | Python dependencies |
| `data/inverness.gpkg` | Source data (not committed if large) |
| `outputs/inverness_completeness_report.md` | Generated report |
| `outputs/inverness_null_report.csv` | Null counts per column |
| `outputs/inverness_record_age.png` | Record currency histogram |
| `outputs/inverness_building_age.png` | Building age histogram |

To reproduce:

```bash
conda activate geo
python inverness_completeness.py data/inverness.gpkg

## 8. Tools
Python 3.11**
GeoPandas 1.0.1
Pandas 2.3.1
Matplotlib 3.10.0
QGIS (visual inspection)


## 9. Environment Setup
This project uses a dedicated conda environment called geo.

To create it:
conda create -n geo python=3.11 geopandas matplotlib tabulate

To activate it:
conda activate geo