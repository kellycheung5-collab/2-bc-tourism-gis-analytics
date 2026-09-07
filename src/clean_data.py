import re
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.validation import make_valid

# Set up project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# HELPER & TEXT DECOMPOSITION FUNCTIONS
# =============================================================================

def normalize_text(text: str) -> str:
    """Cleans embedded newlines, line-break hyphens, footnote indices, and irregular spaces."""
    if pd.isna(text):
        return text

    s = str(text).replace("\n", " ")

    # Fix line-wrap hyphenation artifacts
    s = re.sub(r"Accom-modation", "Accommodation", s, flags=re.IGNORECASE)
    s = re.sub(r"accom-modation", "Accommodation", s, flags=re.IGNORECASE)
    s = re.sub(r"entertain-ment", "Entertainment", s, flags=re.IGNORECASE)

    # Strip footnote numbers attached directly to words
    s = re.sub(r"(\b[A-Za-z]+)\d+", r"\1", s)

    # Remove trailing/separated footnote indices
    s = re.sub(r"\s+\d+,\d+", "", s)

    # Collapse multiple spaces into a single space
    return " ".join(s.split())


def decompose_food_services(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts Region and Category columns for food services datasets."""

    def parse_region(text):
        if " BC " in f" {text} " or text.endswith(" BC"):
            return "BC"
        elif "Canada" in text:
            return "Canada"
        return "Total"

    def parse_category(text):
        if text.endswith("Drinking Places"):
            return "Drinking Places"
        elif text.endswith("Food Services"):
            return "Food Services"
        elif text.endswith("Total"):
            return "Total"
        return "All Services"

    df["Metric"] = "Food Services and Drinking Places Receipts"
    df["Region"] = df["Indicator_Clean"].apply(parse_region)
    df["Category"] = df["Indicator_Clean"].apply(parse_category)
    return df


def decompose_tourism_sector(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts Domain, Sub_Indicator, and Unit columns for tourism sector datasets."""

    def parse_sector(text):
        if "Employment" in text:
            domain = "Employment"
            unit = "000s"
            sub = text.replace(
                "Employment in key tourism industries (000s) -", ""
            ).strip()
        elif "Hotel Industry" in text:
            domain = "Hotel Industry"
            if "Occupancy Rate" in text:
                unit = "%"
                sub = "Occupancy Rate"
            elif "Room Rate" in text:
                unit = "$"
                sub = "Room Rate"
            elif "Room Revenue" in text:
                unit = "$"
                sub = "Room Revenue"
            else:
                unit = "Unknown"
                sub = text.replace("Hotel Industry -", "").strip()
        elif "Consumer Price Index" in text:
            domain = "Consumer Price Index"
            unit = "Index (2017=100)" if "2017" in text else "Index"
            sub = text.replace("Consumer Price Index -", "").strip()
        else:
            domain, sub, unit = "General Indicator", text, "Numeric"
        return pd.Series([domain, sub, unit])

    df[["Domain", "Sub_Indicator", "Unit"]] = df["Indicator_Clean"].apply(
        parse_sector
    )
    return df


def decompose_transportation(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts Transport_Mode, Location, and Segment columns for transportation datasets."""

    def parse_transport(text):
        if "Air Passenger Traffic" in text:
            mode = "Air Passenger Traffic"
            if "Vancouver" in text:
                loc = "Vancouver"
                seg = text.replace(
                    "Air Passenger Traffic - Vancouver -", ""
                ).strip()
            elif "Victoria" in text:
                loc = "Victoria"
                seg = text.replace(
                    "Air Passenger Traffic - Victoria -", ""
                ).strip()
            else:
                loc, seg = "Other Airport", "Total"
        elif "BC Ferries" in text:
            mode = "Ferry Traffic"
            loc = "BC Ferries"
            seg = text.replace("Other Transportation - BC Ferries -", "").strip()
        else:
            mode, loc, seg = "Other", "Other", "Total"
        return pd.Series([mode, loc, seg])

    df[["Transport_Mode", "Location", "Segment"]] = df["Indicator_Clean"].apply(
        parse_transport
    )
    return df


def decompose_traveller_entries(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts Origin_Region and Entry_Type columns for traveller entries datasets."""

    def parse_entries(text):
        if "USA" in text:
            origin = "USA"
            entry_type = text.replace("USA -", "").strip()
        elif "Overseas" in text:
            origin = "Overseas"
            entry_type = text.replace("Overseas -", "").strip()
        else:
            origin = "Total"
            entry_type = "Total"
        return pd.Series([origin, entry_type])

    df[["Origin_Region", "Entry_Type"]] = df["Indicator_Clean"].apply(
        parse_entries
    )
    return df


def apply_indicator_decomposition(df: pd.DataFrame, domain_name: str) -> pd.DataFrame:
    """Standardizes indicator strings and splits them into distinct dimension columns."""
    indicator_col = (
        "Indicator"
        if "Indicator" in df.columns
        else ("Indicator_Name" if "Indicator_Name" in df.columns else None)
    )

    if not indicator_col:
        return df

    df["Indicator_Clean"] = df[indicator_col].apply(normalize_text)

    if "food_services" in domain_name:
        df = decompose_food_services(df)
    elif "tourism_sector" in domain_name:
        df = decompose_tourism_sector(df)
    elif "transportation" in domain_name:
        df = decompose_transportation(df)
    elif "traveller_entries" in domain_name:
        df = decompose_traveller_entries(df)

    df = df.drop(columns=[indicator_col]).rename(
        columns={"Indicator_Clean": "Indicator"}
    )

    base_cols = [
        c
        for c in ["Year", "Period_Label", "Ref_Year", "Region Name"]
        if c in df.columns
    ]
    other_cols = [c for c in df.columns if c not in base_cols and c != "Value"]
    return df[base_cols + other_cols + ["Value"]]


# =============================================================================
# DATASET EXTRACTION PIPELINE FUNCTIONS
# =============================================================================

def clean_laep_income_data():
    """Cleans LAEP regional district average employment income data, standardizes names, and unpivots."""
    print("Processing LAEP Average Tourism Employment Income Data...")
    laep_files = list(RAW_DIR.glob("laep-average-incomes*.csv"))
    if not laep_files:
        print(" [!] Skipping: LAEP CSV file not found in data/raw/")
        return

    df_raw = pd.read_csv(laep_files[0])
    headers = df_raw.iloc[4].values
    df = df_raw.iloc[5:].copy()
    df.columns = headers

    df_rd = df[df["Geo_Type"] == "RD"].copy()

    indicator_cols = [
        "Total",
        "Tourism Total",
        "Tourism: Transportation",
        "Tourism: Accommodation",
        "Tourism: Food and beverage",
        "Tourism: Recreation and entertainment",
        "Tourism: Retail",
        "Tourism: Other",
    ]

    name_map = {
        "Capital": "Capital Regional District",
        "Metro Vancouver": "Metro Vancouver Regional District",
        "Nanaimo RD": "Regional District of Nanaimo",
        "Powell River RD": "qathet Regional District",
        "Strathcona RD": "Strathcona Regional District",
        "Sunshine Coast RD": "Sunshine Coast Regional District",
        "Alberni-Clayoquot": "Regional District of Alberni-Clayoquot",
        "Bulkley-Nechako": "Regional District of Bulkley-Nechako",
        "Central Kootenay": "Regional District of Central Kootenay",
        "Central Okanagan": "Regional District of Central Okanagan",
        "East Kootenay": "Regional District of East Kootenay",
        "Fraser-Fort George": "Regional District of Fraser-Fort George",
        "Kitimat-Stikine": "Regional District of Kitimat-Stikine",
        "Kootenay Boundary": "Regional District of Kootenay Boundary",
        "Mount Waddington": "Regional District of Mount Waddington",
        "North Okanagan": "Regional District of North Okanagan",
        "Okanagan-Similkameen": "Regional District of Okanagan-Similkameen",
        "Cariboo": "Cariboo Regional District",
        "Central Coast RD": "Central Coast Regional District",
        "Columbia-Shuswap": "Columbia Shuswap Regional District",
        "Comox Valley": "Comox Valley Regional District",
        "Cowichan Valley": "Cowichan Valley Regional District",
        "Fraser Valley": "Fraser Valley Regional District",
        "Peace River": "Peace River Regional District",
        "Skeena-Queen Charlotte": "North Coast Regional District",
        "Squamish-Lillooet": "Squamish-Lillooet Regional District",
        "Stikine Region": "Stikine Region (Unincorporated)",
        "Thompson-Nicola": "Thompson-Nicola Regional District",
        "Northern Rockies RD": "Northern Rockies Regional Municipality",
    }

    df_rd["Region Name"] = df_rd["Region Name"].replace(name_map)

    df_tidy = pd.melt(
        df_rd,
        id_vars=["Region Name", "Ref_Year"],
        value_vars=[c for c in indicator_cols if c in df_rd.columns],
        var_name="Indicator_Name",
        value_name="Value",
    )

    df_tidy["Value"] = pd.to_numeric(
        df_tidy["Value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace(["x", "NA", "None", "nan", ""], np.nan),
        errors="coerce",
    )

    df_tidy["Ref_Year"] = df_tidy["Ref_Year"].astype(int)
    df_tidy = df_tidy.dropna(subset=["Value"]).reset_index(drop=True)

    output_path = PROCESSED_DIR / "laep_regional_incomes_tidy.csv"
    df_tidy.to_csv(output_path, index=False)
    print(f" Saved: {output_path.name} ({len(df_tidy)} rows)")


def build_clean_column_headers(df_raw: pd.DataFrame) -> list:
    """Safely builds composite headers without letting section titles bleed across boundaries."""
    header_block = df_raw.iloc[0:5].astype(object).copy()

    header_block = header_block.map(
        lambda x: (
            str(x)
            .encode("ascii", "ignore")
            .decode("ascii")
            .replace("Â", "")
            .replace("†", "")
            .strip()
            if pd.notna(x) and str(x).strip() != ""
            else None
        )
    )

    header_block.iloc[1:4] = header_block.iloc[1:4].ffill(axis=1)

    composite_cols = []
    for col_idx in range(header_block.shape[1]):
        raw_levels = (
            header_block.iloc[:, col_idx]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        clean_levels = [
            lvl
            for lvl in raw_levels
            if lvl.lower()
            not in [
                "nan",
                "",
                "none",
                "annual data",
                "monthly data",
                "unnamed",
                "period",
            ]
        ]

        dedup_levels = []
        for lvl in clean_levels:
            if not dedup_levels or dedup_levels[-1] != lvl:
                dedup_levels.append(lvl)

        col_name = (
            " - ".join(dedup_levels)
            if dedup_levels
            else f"indicator_col_{col_idx}"
        )
        composite_cols.append(col_name)

    return composite_cols


def clean_monthly_indicators_modular():
    """Extracts monthly and annual tourism data, normalizes strings, and decomposes dimensions."""
    print("Processing Monthly & Annual Tourism Indicators...")

    monthly_files = list(RAW_DIR.glob("monthly_tourism_indicators*.csv"))
    if not monthly_files:
        print(" [!] Skipping: Monthly indicators CSV not found in data/raw/")
        return

    monthly_path = monthly_files[0]
    try:
        df_raw = pd.read_csv(monthly_path, encoding="utf-8-sig", header=None)
    except UnicodeDecodeError:
        df_raw = pd.read_csv(monthly_path, encoding="latin1", header=None)

    composite_headers = build_clean_column_headers(df_raw)
    df_data = df_raw.copy()
    df_data.columns = composite_headers

    domain_configs = {
        "food_services_receipts": {"period_col": 23, "col_start": 24, "col_end": 30},
        "traveller_entries": {"period_col": 0, "col_start": 1, "col_end": 12},
        "transportation_indicators": {"period_col": 40, "col_start": 41, "col_end": 49},
        "tourism_sector_indicators": {"period_col": 61, "col_start": 62, "col_end": 72},
    }

    RAW_DATA_START = 5
    MONTH_NAMES = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

    for domain_name, config in domain_configs.items():
        period_col_idx = config["period_col"]
        col_start = config["col_start"]
        col_end = min(config["col_end"], df_data.shape[1] - 1)

        if col_start >= df_data.shape[1] or period_col_idx >= df_data.shape[1]:
            continue

        annual_records = []
        monthly_records = []

        for col_idx in range(col_start, col_end + 1):
            col_name = df_data.columns[col_idx]

            full_header_context = " ".join(
                df_raw.iloc[0:5, col_idx].dropna().astype(str).tolist()
            ).lower()

            if any(
                k in full_header_context
                for k in [
                    "percent change",
                    "% change",
                    "annual percent",
                    "month-over-month percent",
                ]
            ):
                continue

            col_df = df_data.iloc[RAW_DATA_START:, [period_col_idx, col_idx]].copy()
            col_df.columns = ["Period_Label", "Value_Raw"]

            col_df["Value"] = pd.to_numeric(
                col_df["Value_Raw"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace("$", "", regex=False)
                .replace(
                    ["x", "NA", "None", "nan", "", "Annual data", "Monthly data"],
                    np.nan,
                ),
                errors="coerce",
            )

            current_year = None

            for _, row in col_df.iterrows():
                period_str = str(row["Period_Label"]).strip()
                val = row["Value"]

                if pd.isna(val) or period_str in ["nan", "None", "", "Monthly data", "Annual data"]:
                    continue

                if period_str.isdigit() and len(period_str) == 4:
                    annual_records.append(
                        {"Year": int(period_str), "Indicator": col_name, "Value": val}
                    )

                elif "'" in period_str or "-" in period_str:
                    yr_part = (
                        period_str.split("'")[-1]
                        if "'" in period_str
                        else period_str.split("-")[-1]
                    ).strip()
                    if yr_part.isdigit():
                        yr_num = int(yr_part)
                        current_year = 2000 + yr_num if yr_num < 50 else 1900 + yr_num
                        monthly_records.append(
                            {
                                "Year": current_year,
                                "Period_Label": period_str,
                                "Indicator": col_name,
                                "Value": val,
                            }
                        )

                elif (
                    any(m in period_str.lower() for m in MONTH_NAMES)
                    and current_year is not None
                ):
                    yr_short = str(current_year)[-2:]
                    formatted_period = f"{period_str} '{yr_short}"
                    monthly_records.append(
                        {
                            "Year": current_year,
                            "Period_Label": formatted_period,
                            "Indicator": col_name,
                            "Value": val,
                        }
                    )

        if annual_records:
            df_annual = pd.DataFrame(annual_records)
            df_annual = apply_indicator_decomposition(df_annual, domain_name)
            df_annual = df_annual.sort_values(by=["Indicator", "Year"]).reset_index(
                drop=True
            )

            annual_out = PROCESSED_DIR / f"indicator_{domain_name}_annual_tidy.csv"
            df_annual.to_csv(annual_out, index=False)
            print(f" Saved: {annual_out.name} ({len(df_annual)} rows)")

        if monthly_records:
            df_monthly = pd.DataFrame(monthly_records)
            df_monthly = apply_indicator_decomposition(df_monthly, domain_name)

            monthly_out = PROCESSED_DIR / f"indicator_{domain_name}_monthly_tidy.csv"
            df_monthly.to_csv(monthly_out, index=False)
            print(f" Saved: {monthly_out.name} ({len(df_monthly)} rows)")


def clean_annual_macro_indicators():
    """Cleans provincial macro annual metrics and decomposes indicator text."""
    print("Processing BC Stats Annual Indicators...")

    annual_files = list(RAW_DIR.glob("bc_stats_tourism_annual*.csv"))
    if not annual_files:
        print(" [!] Skipping: Annual macro indicators CSV not found in data/raw/")
        return

    annual_path = annual_files[0]
    df_raw = pd.read_csv(annual_path, header=None)

    header_idx = None
    for idx, row in df_raw.iterrows():
        if any("2010" in str(cell) for cell in row.values):
            header_idx = idx
            break

    if header_idx is not None:
        df = pd.read_csv(annual_path, skiprows=header_idx)
    else:
        df = df_raw.copy()

    df.rename(columns={df.columns[0]: "Indicator_Name"}, inplace=True)
    df["Indicator_Name"] = df["Indicator_Name"].astype(str).str.strip()

    df = df[
        df["Indicator_Name"].notna()
        & ~df["Indicator_Name"].str.lower().eq("% change")
        & ~df["Indicator_Name"].str.lower().str.startswith("british columbia")
        & ~df["Indicator_Name"].str.contains(
            "Annual percent change", case=False, na=False
        )
        & ~df["Indicator_Name"].str.startswith("*", na=False)
        & (df["Indicator_Name"] != "")
    ].copy()

    cleaned_cols = [str(c).replace("***", "").strip() for c in df.columns]
    df.columns = cleaned_cols

    valid_cols = [
        c
        for c in df.columns
        if not c.startswith("Unnamed") and c != "Indicator_Name"
    ]
    year_cols = [c for c in valid_cols if c.isdigit()]

    df_tidy = pd.melt(
        df,
        id_vars=["Indicator_Name"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Value",
    )

    df_tidy["Value"] = pd.to_numeric(
        df_tidy["Value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace(["x", "NA", "None", "nan", ""], np.nan),
        errors="coerce",
    )

    df_tidy["Year"] = df_tidy["Year"].astype(int)
    df_tidy = df_tidy.dropna(subset=["Value"]).reset_index(drop=True)

    df_tidy["Indicator"] = df_tidy["Indicator_Name"].apply(normalize_text)
    df_tidy = df_tidy.drop(columns=["Indicator_Name"])

    output_path = PROCESSED_DIR / "bc_stats_annual_indicators_tidy.csv"
    df_tidy.to_csv(output_path, index=False)
    print(f" Saved: {output_path.name} ({len(df_tidy)} rows)")


def verify_gpkg_layer():
    """Cleans regional districts and explicitly appends Northern Rockies with a valid Region Name."""
    print("Processing Regional District boundaries & appending Northern Rockies...")

    districts_path = RAW_DIR / "ABMS_REGIONAL_DISTRICTS_SP.gpkg"
    muni_path = RAW_DIR / "ABMS_MUNICIPALITIES_SP.gpkg"

    if not districts_path.exists():
        print(f" [!] Skipping: {districts_path.name} not found in data/raw/")
        return

    # 1. Load primary Regional Districts layer
    gdf_rd = gpd.read_file(districts_path)

    # Standardize column name to 'Region Name' immediately on RD layer
    rd_name_col = "ADMIN_AREA_NAME" if "ADMIN_AREA_NAME" in gdf_rd.columns else gdf_rd.columns[0]
    gdf_rd = gdf_rd.rename(columns={rd_name_col: "Region Name"})
    gdf_rd["Region Name"] = gdf_rd["Region Name"].astype(str).str.strip()

    # 2. Extract and append Northern Rockies from Municipalities layer
    if muni_path.exists():
        gdf_muni = gpd.read_file(muni_path)

        # Filter for Northern Rockies features
        nr_mask = gdf_muni["ADMIN_AREA_NAME"].str.contains(
            "Northern Rockies", case=False, na=False
        ) | gdf_muni["ADMIN_AREA_GROUP_NAME"].str.contains(
            "Northern Rockies", case=False, na=False
        )
        gdf_nr = gdf_muni[nr_mask].copy()

        if not gdf_nr.empty:
            print(" Found Northern Rockies feature in municipalities dataset.")

            # Explicitly set the 'Region Name' to match the LAEP income dataset key
            gdf_nr["Region Name"] = "Northern Rockies Regional Municipality"

            # Dissolve if Northern Rockies consists of multiple municipal features
            gdf_nr = gdf_nr.dissolve(by="Region Name").reset_index()

            # Align CRS
            if gdf_nr.crs != gdf_rd.crs:
                gdf_nr = gdf_nr.to_crs(gdf_rd.crs)

            # Retain only matching columns to keep schema clean
            gdf_nr = gdf_nr[["Region Name", "geometry"]]

            # Remove any existing blank/dash placeholder row in gdf_rd if present
            gdf_rd = gdf_rd[~gdf_rd["Region Name"].isin(["-", "nan", "None", ""])]

            # Append Northern Rockies
            gdf_rd = pd.concat([gdf_rd, gdf_nr], ignore_index=True)

    # 3. Standardize CRS to EPSG:3005
    if gdf_rd.crs is None or gdf_rd.crs.to_epsg() != 3005:
        gdf_rd = gdf_rd.to_crs(epsg=3005)

    # 4. Repair invalid geometries
    invalid_mask = ~gdf_rd.geometry.is_valid
    if invalid_mask.any():
        gdf_rd.loc[invalid_mask, "geometry"] = gdf_rd.loc[
            invalid_mask, "geometry"
        ].apply(make_valid)

    # Save clean complete layer
    rd_out = PROCESSED_DIR / "bc_regional_districts_clean.gpkg"
    gdf_rd.to_file(rd_out, driver="GPKG")
    print(f" Saved Complete Regional District Layer: {rd_out.name} ({len(gdf_rd)} features)")


def run_pipeline():
    """Main execution function for the data cleaning pipeline."""
    print("=" * 60)
    print(" RUNNING BC TOURISM DATA CLEANING & FEATURE EXTRACTION PIPELINE")
    print("=" * 60)
    clean_laep_income_data()
    clean_monthly_indicators_modular()
    clean_annual_macro_indicators()
    verify_gpkg_layer()
    print("\nPipeline execution complete. All clean datasets saved in data/processed/")


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

if __name__ == "__main__":
    run_pipeline()