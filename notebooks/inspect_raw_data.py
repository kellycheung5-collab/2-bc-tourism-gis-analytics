from pathlib import Path
import geopandas as gpd
import pandas as pd

# 1. Establish project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def inspect_csv_files():
    print("=" * 65)
    print(" 1. INSPECTING TABULAR CSV DATASETS")
    print("=" * 65)

    # A. Annual Macro Indicators
    annual_files = list(RAW_DATA_DIR.glob("bc_stats_tourism_annual*.csv"))
    if annual_files:
        annual_path = annual_files[0]
        print(f"\n--- Annual Macro Indicators: {annual_path.name} ---")
        df_annual = pd.read_csv(annual_path, skiprows=30)
        print(f"Shape: {df_annual.shape}")
        print(f"Columns: {df_annual.columns.tolist()[:5]} ...")
    else:
        print("\nAnnual indicators CSV not found in data/raw/")

    # B. Monthly Tourism Indicators
    monthly_files = list(RAW_DATA_DIR.glob("monthly_tourism_indicators*.csv"))
    if monthly_files:
        monthly_path = monthly_files[0]
        print(f"\n--- Monthly Tourism Indicators: {monthly_path.name} ---")
        df_monthly = pd.read_csv(monthly_path, encoding="latin1", header=None)
        print(f"Shape: {df_monthly.shape}")
    else:
        print("\nMonthly indicators CSV not found in data/raw/")

    # C. LAEP Average Incomes by Area
    laep_files = list(RAW_DATA_DIR.glob("laep-average-incomes*.csv"))
    if laep_files:
        laep_path = laep_files[0]
        print(f"\n--- Regional Income Dataset: {laep_path.name} ---")
        df_laep_raw = pd.read_csv(laep_path)
        print(f"Raw Shape: {df_laep_raw.shape}")

        # Extract true headers from row index 4
        headers = df_laep_raw.iloc[4].values
        df_laep = df_laep_raw.iloc[5:].copy()
        df_laep.columns = headers

        print(f"Geo_Type Breakdown:\n{df_laep['Geo_Type'].value_counts()}")

        # Regional District Sample
        rd_sample = df_laep[df_laep["Geo_Type"] == "RD"][
            ["Region Name", "Ref_Year", "Tourism Total", "Total"]
        ]
        print("\nUnique Regional Districts Sample (Geo_Type == 'RD'):")
        print(rd_sample.head(10).to_string(index=False))
    else:
        print("\nLAEP average incomes CSV not found in data/raw/")


def inspect_geopackage():
    print("\n" + "=" * 65)
    print(" 2. INSPECTING GEOPACKAGE BOUNDARY FILE")
    print("=" * 65)

    gpkg_files = list(RAW_DATA_DIR.glob("*.gpkg"))

    if not gpkg_files:
        print("\n[!] No .gpkg file found in data/raw/")
        return

    gpkg_path = gpkg_files[0]
    print(f"\n--- GeoPackage Boundary File: {gpkg_path.name} ---")

    gdf = gpd.read_file(gpkg_path)

    print(f"Total Spatial Features (Polygons): {len(gdf)}")
    print(f"Coordinate Reference System (CRS): {gdf.crs}")

    # Display region names
    name_col = "ADMIN_AREA_NAME"
    if name_col in gdf.columns:
        print(
            f"\nUnique Region Names in '{name_col}' ({len(gdf[name_col].unique())} total):"
        )
        for region in sorted(gdf[name_col].dropna().unique()):
            print(f" - {region}")

    print("\nSpatial Data Head Sample:")
    print(
        gdf[["OBJECTID", "ADMIN_AREA_NAME", "ADMIN_AREA_ABBREVIATION"]].head(5)
    )


if __name__ == "__main__":
    inspect_csv_files()
    inspect_geopackage()