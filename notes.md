# BC Tourism Data Pipeline - Cleaning & Preprocessing Notes

## Pipeline Overview
The data pipeline standardizes, cleans, and transforms raw BC tourism and macro-economic datasets into normalized, long-format CSVs and clean spatial layers in `data/processed/`. The entire process is executed via `clean_data.py`.

---

## 1. GeoPackage Boundaries (`data/processed/bc_regional_districts_clean.gpkg`)
* **Spatial Alignment:** Re-projected vector boundaries to **EPSG:3005** (BC Albers Equal Area).
* **Key Spatial Identifier:** The column `ADMIN_AREA_NAME` contains official regional district names.
* **Standardized Regional Mapping:** Standardized name variations across tabular datasets to match spatial boundary names:
  * `Capital` → `Capital Regional District`
  * `Metro Vancouver` → `Metro Vancouver Regional District`
  * `Nanaimo RD` → `Regional District of Nanaimo`
  * `Powell River RD` → `qathet Regional District`
  * `Strathcona RD` → `Strathcona Regional District`
  * `Sunshine Coast RD` → `Sunshine Coast Regional District`
  * `Alberni-Clayoquot` → `Regional District of Alberni-Clayoquot`
  * `Bulkley-Nechako` → `Regional District of Bulkley-Nechako`
  * `Central Kootenay` → `Regional District of Central Kootenay`
  * `Central Okanagan` → `Regional District of Central Okanagan`
  * `East Kootenay` → `Regional District of East Kootenay`
  * `Fraser-Fort George` → `Regional District of Fraser-Fort George`
  * `Kitimat-Stikine` → `Regional District of Kitimat-Stikine`
  * `Kootenay Boundary` → `Regional District of Kootenay Boundary`
  * `Mount Waddington` → `Regional District of Mount Waddington`
  * `North Okanagan` → `Regional District of North Okanagan`
  * `Okanagan-Similkameen` → `Regional District of Okanagan-Similkameen`
  * `Cariboo` → `Cariboo Regional District`
  * `Central Coast RD` → `Central Coast Regional District`
  * `Columbia-Shuswap` → `Columbia Shuswap Regional District`
  * `Comox Valley` → `Comox Valley Regional District`
  * `Cowichan Valley` → `Cowichan Valley Regional District`
  * `Fraser Valley` → `Fraser Valley Regional District`
  * `Peace River` → `Peace River Regional District`
  * `Squamish-Lillooet` → `Squamish-Lillooet Regional District`
  * `Stikine Region` → `Stikine Region (Unincorporated)`
  * `Thompson-Nicola` → `Thompson-Nicola Regional District`
  * `Northern Rockies RD` → `Northern Rockies Regional Municipality`
  * `Skeena-Queen Charlotte` → `North Coast Regional District`

---

## 2. LAEP Average Incomes (`data/processed/laep_regional_incomes_tidy.csv`)
* **Extraction:** Parsed composite header at `iloc[4]` and isolated regional district rows (`Geo_Type == 'RD'`).
* **Unpivoting:** Reshaped wide income matrix into long format across 8 sector metrics (`Total`, `Tourism Total`, and 6 sub-sector indicators).
* **Sanitization:** Sanitized suppressed/missing data markers (`x`, `NA`, `None`, blank) to `np.nan` and converted values to `float64`.

---

## 3. High-Frequency Monthly & Annual Tourism Indicators
* **Header Building & Cleaning (`build_clean_column_headers` & `normalize_text`):**
  * Handled encoding (`utf-8-sig` / `latin1`) and removed symbol artifacts (`\x86`, `Â`, `†`).
  * Stripped trailing/embedded footnote indices (e.g., `Places1` → `Places`, `Index1` → `Index`, `BC2` → `BC`, `Traffic 1,2` → `Traffic`).
  * Resolved hyphenation line-break artifacts (e.g., `Accom-modation` → `Accommodation`, `entertain-ment` → `Entertainment`).
  * Filtered out percent change calculations to focus on primary volume/currency metrics.
* **Date & Period Logic:** Forward-filled year contexts across monthly cycles (`Jan '00`, `Feb '00` ... `Dec '00`).
* **Multidimensional Feature Extraction (`apply_indicator_decomposition`):**
  * **Food Services Receipts:** Decomposed into `Region` (`BC`, `Canada`) and `Category` (`Food Services`, `Drinking Places`, `Total`).
  * **Tourism Sector Indicators:** Decomposed into `Domain` (`Employment`, `Hotel Industry`, `Consumer Price Index`), `Sub_Indicator`, and `Unit` (`000s`, `%`, `$`, `Index`).
  * **Transportation Indicators:** Decomposed into `Transport_Mode` (`Air Passenger Traffic`, `Ferry Traffic`), `Location` (`Vancouver`, `Victoria`, `BC Ferries`), and `Segment` (`Domestic`, `Trans-border`, `Other Int'l`, `Vehicles`, `Passengers`).
  * **Traveller Entries:** Decomposed into `Origin_Region` (`USA`, `Overseas`, `Total`) and `Entry_Type` (`Same-day`, `Overnight`, `Asia`, `Europe`, `Other`).

> **`Employment` domain:** This domain (`Accommodation`, `Air transport`, `Arts, Entertainment & recreation`, `Food & beverage services`) reflects **total NAICS industry-wide employment** that is everyone employed in that industry, regardless of whether the customer they served was a tourist or a local resident. It is not the tourism-attributable employment figure and should not be summed against, or interpreted as a breakdown of, the `Employment (thousands)` indicator in `bc_stats_annual_indicators_tidy.csv`. The two use different definitional scopes

> **Unit mislabeling: `Employment` domain:** The `Unit` column for all `Employment` sub-indicators is recorded as `000s`, but the stored `Value` is the raw headcount, not a value already divided by 1,000 (e.g. Accommodation employment in 2000 is stored as `28171.83`, i.e. ~28,172 people, not `28.17`).

---

## 4. BC Stats Macro Indicators (`data/processed/bc_stats_annual_indicators_tidy.csv`)
* **Header & Break Normalization:** Dynamically located header rows, removed methodology break markers (`'2022***'` → `'2022'`), and stripped footnotes/title blocks.
* **Filtered Calculation Noise:** Removed interleaved `% change` and footnote rows (`*Includes...`, `**Excludes...`).
* **Reshaping:** Unpivoted metric matrix (`2010`–`2024`) into long format (`Year`, `Indicator`, `Value`).

> **`Employment (thousands)`:** This indicator reflects **direct tourism-attributed employment** under the BC Tourism Satellite Account methodology (the tourism-share portion of employment across all industries), not total industry employment.

---

## 5. Non-Parametric Hypothesis Testing (`src/hypothesis_tests.py`)

* **Stage 1 — Multi-Indicator Significance Test:** 5 of 8 indicators cleared Stage 1 significance (p < 0.05):
  * Total (p = 0.0484)
  * Tourism: Accommodation (p = 0.0196)
  * Tourism: Recreation and Entertainment (p = 0.0022)
  * Tourism: Retail (p = 0.0242)
  * Tourism: Transportation (p = 0.0130)

  Only **Tourism Total**, **Tourism: Food and beverage**, and **Tourism: Other** were non-significant in Stage 1.

* **Stage 2 — Post-Hoc Dunn's Test:** `run_regional_income_tests()` now defaults to **Benjamini-Hochberg FDR correction** (`p_adjust="fdr_bh"`) instead of standard Bonferroni.

* **Zero-Pair Rationale:** Stage 2 returns 0 significant pairwise Dunn comparisons across all indicators despite Stage 1 significance. Evaluating C(29, 2) = 406 pairwise combinations with a small sample size (n = 3 years per region) creates a statistical power bottleneck that survives even under FDR adjustment. The omnibus test can detect that some regional difference exists, but there isn't enough statistical power per pairwise comparison to identify which specific regions differ.

---

## Output Schema Summary (`data/processed/`)

| Processed Output File | Primary Structural Columns | Extracted Feature Dimensions |
| :--- | :--- | :--- |
| `laep_regional_incomes_tidy.csv` | `Region Name`, `Ref_Year`, `Indicator_Name`, `Value` | Regional Income by Sector |
| `indicator_food_services_receipts_annual_tidy.csv` | `Year`, `Indicator`, `Value` | `Metric`, `Region`, `Category` |
| `indicator_food_services_receipts_monthly_tidy.csv` | `Year`, `Period_Label`, `Indicator`, `Value` | `Metric`, `Region`, `Category` |
| `indicator_tourism_sector_indicators_annual_tidy.csv` | `Year`, `Indicator`, `Value` | `Domain`, `Sub_Indicator`, `Unit` |
| `indicator_tourism_sector_indicators_monthly_tidy.csv` | `Year`, `Period_Label`, `Indicator`, `Value` | `Domain`, `Sub_Indicator`, `Unit` |
| `indicator_transportation_indicators_annual_tidy.csv` | `Year`, `Indicator`, `Value` | `Transport_Mode`, `Location`, `Segment` |
| `indicator_transportation_indicators_monthly_tidy.csv` | `Year`, `Period_Label`, `Indicator`, `Value` | `Transport_Mode`, `Location`, `Segment` |
| `indicator_traveller_entries_annual_tidy.csv` | `Year`, `Indicator`, `Value` | `Origin_Region`, `Entry_Type` |
| `indicator_traveller_entries_monthly_tidy.csv` | `Year`, `Period_Label`, `Indicator`, `Value` | `Origin_Region`, `Entry_Type` |
| `bc_stats_annual_indicators_tidy.csv` | `Year`, `Indicator`, `Value` | Macro Economic Metrics |
| `bc_regional_districts_clean.gpkg` | Spatial Geometry (`EPSG:3005`) | Regional District Boundaries |