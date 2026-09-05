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

---

## 4. BC Stats Macro Indicators (`data/processed/bc_stats_annual_indicators_tidy.csv`)
* **Header & Break Normalization:** Dynamically located header rows, removed methodology break markers (`'2022***'` → `'2022'`), and stripped footnotes/title blocks.
* **Filtered Calculation Noise:** Removed interleaved `% change` and footnote rows (`*Includes...`, `**Excludes...`).
* **Reshaping:** Unpivoted metric matrix (`2010`–`2024`) into long format (`Year`, `Indicator`, `Value`).

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