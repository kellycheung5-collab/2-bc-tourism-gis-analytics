# Data Cleaning & Preprocessing Notes

## Project Datasets Summary
* `ABMS_REGIONAL_DISTRICTS_SP.gpkg` (Spatial Boundaries)
* `laep-average-incomes-by-area.csv` (Regional Sector Income Data)
* `monthly_tourism_indicators.csv` (High-Frequency Monthly Time Series)
* `bc_stats_tourism_annual_indicators_tables_2026.csv` (Macro Provincial Trends)

---

## 1. GeoPackage Boundaries (`ABMS_REGIONAL_DISTRICTS_SP.gpkg`)
* **CRS Alignment:** Confirm projection is set to `EPSG:3005` (BC Albers Equal Area).
* **Key Spatial Identifier:** The column `ADMIN_AREA_NAME` contains the 28 official regional district names (e.g., `Metro Vancouver Regional District`, `Capital Regional District`).
* **Name Standardizations for Join:**
  * Map `Capital` -> `Capital Regional District`
  * Map `Metro Vancouver` -> `Metro Vancouver Regional District`
  * Map `Nanaimo RD` -> `Regional District of Nanaimo`
  * Map `Powell River RD` -> `qathet Regional District` (Historical name update)
  * Map `Strathcona RD` -> `Strathcona Regional District`
  * Map `Sunshine Coast RD` -> `Sunshine Coast Regional District`

---

## 2. LAEP Average Incomes by Area (`laep-average-incomes-by-area.csv`)
* **Header Alignment:** Column names start at Excel Row 6 (`iloc[4]`). Data begins at Excel Row 7 (`iloc[5:]`).
* **Regional District Filter:** Filter strictly for `Geo_Type == 'RD'` to isolate the 28 Regional District aggregates and exclude provincial/EDA summaries.
* **Target Columns:** Extract `Region Name`, `Ref_Year`, `Total`, `Tourism Total`, `Tourism: Transportation`, `Tourism: Accommodation`, `Tourism: Food and beverage`, and `Tourism: Recreation and entertainment`.
* **Data Type Conversions:**
  * Strip commas from income strings (`30,200` -> `30200.0`).
  * Replace suppressed entries (`x`, `NA`, blank) with `np.nan`.
  * Cast numeric income fields to `float64`.

---

## 3. Monthly Tourism Indicators (`monthly_tourism_indicators.csv`)
* **Encoding Requirement:** Must read with `encoding='latin1'` (or `cp1252`) to avoid `UnicodeDecodeError` caused by footnote symbols (`\x86`).
* **Header & Footer Stripping:**
  * Strip title block (Rows 0–3) and metadata notes at the bottom.
  * Flatten multi-tier headers across domain categories (*Traveller Entries*, *Food Services Receipts*, *Transportation Indicators*, *Tourism Sector Indicators*).
* **Splitting Granularities:**
  * **Annual Summary Table (Rows 5–30):** Full calendar years (`2000`–`2025`). Export as `monthly_indicators_annual_summary.csv`.
  * **Monthly Time Series (Rows 32+):** Monthly data points (`Jan '00`, `Feb`, `Mar`...). Export as `monthly_tourism_time_series.csv`.
* **Date Parsing Logic:**
  * Year markers only appear on January rows (`Jan '00`). Intermediate rows (`Feb`, `Mar`) only list month abbreviations.
  * Logic required: Extract year string `'00` -> `2000`, forward-fill across subsequent 11 months, and construct standard ISO datetime strings (`YYYY-MM-01`).
* **Suppressed Data Handling:**
  * Replace `'x'` (suppressed/confidential data in hotel metrics) and `'NA'` with `np.nan`.

---

## 4. BC Stats Annual Indicators (`bc_stats_tourism_annual_indicators_tables_2026.csv`)
* **Header/Footer Removal:** Skip initial metadata rows (`skiprows=30`) and remove trailing methodology footnotes.
* **Methodology Break Adjustment:** Strip `***` from `'2022***'` (denotes the 2022 BC Stats Input-Output model methodology shift).
* **Numeric Cleaning:**
  * Remove commas (`13,495` -> `13495.0`).
  * Convert percentage strings (`10.1%` -> `0.101`).
* **Data Reshaping:** Unpivot wide matrix (metrics x year columns `2010`–`2024`) into a tidy, long-format DataFrame (`year`, `indicator_name`, `value`).