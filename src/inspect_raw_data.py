from pathlib import Path
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def inspect_csv_files():
    print("=" * 65)
    print(" 1. INSPECTING TABULAR CSV DATASETS")
    print("=" * 65)

    # Annual Macro Indicators
    annual_files = list(RAW_DATA_DIR.glob("bc_stats_tourism_annual*.csv"))
    if annual_files:
        print(f"\n--- Annual Macro Indicators: {annual_files[0].name} ---")
        df_raw = pd.read_csv(annual_files[0], header=None)
        
        # Dynamically locate header row containing sample year
        header_idx = None
        for idx, row in df_raw.iterrows():
            if any("2010" in str(cell) for cell in row.values):
                header_idx = idx
                break

        if header_idx is not None:
            df_annual = pd.read_csv(annual_files[0], skiprows=header_idx)
        else:
            df_annual = df_raw

        print(f"Shape: {df_annual.shape}")
        print(f"Columns: {df_annual.columns.tolist()[:5]} ...")

    # Monthly Tourism Indicators
    monthly_files = list(RAW_DATA_DIR.glob("monthly_tourism_indicators*.csv"))
    if monthly_files:
        print(f"\n--- Monthly Tourism Indicators: {monthly_files[0].name} ---")
        try:
            df_monthly = pd.read_csv(monthly_files[0], encoding="utf-8-sig", header=None)
        except UnicodeDecodeError:
            df_monthly = pd.read_csv(monthly_files[0], encoding="latin1", header=None)
        print(f"Shape: {df_monthly.shape}")

    # LAEP Average Incomes by Area
    laep_files = list(RAW_DATA_DIR.glob("laep-average-incomes*.csv"))
    if laep_files:
        print(f"\n--- LAEP Average Tourism Employment Income Dataset: {laep_files[0].name} ---")
        df_laep_raw = pd.read_csv(laep_files[0])
        headers = df_laep_raw.iloc[4].values
        df_laep = df_laep_raw.iloc[5:].copy()
        df_laep.columns = headers

        print(f"Geo_Type Breakdown:\n{df_laep['Geo_Type'].value_counts()}")
        rd_sample = df_laep[df_laep["Geo_Type"] == "RD"][
            ["Region Name", "Ref_Year", "Tourism Total", "Total"]
        ]
        print("\nRegional District Sample (Geo_Type == 'RD'):")
        print(rd_sample.head(10).to_string(index=False))


def inspect_geopackage():
    print("\n" + "=" * 65)
    print(" 2. INSPECTING GEOPACKAGE BOUNDARY FILES")
    print("=" * 65)

    gpkg_files = list(RAW_DATA_DIR.glob("*.gpkg"))
    if not gpkg_files:
        print("[!] No .gpkg files found in data/raw/")
        return

    print(f"Found {len(gpkg_files)} GeoPackage file(s).\n")

    for i, gpkg_path in enumerate(gpkg_files, start=1):
        print("-" * 65)
        print(f"File {i}/{len(gpkg_files)}: {gpkg_path.name}")
        print("-" * 65)

        layer_info = gpd.list_layers(gpkg_path)
        print("Available Layers:")
        print(layer_info.to_string(index=False))

        for _, row in layer_info.iterrows():
            layer_name = row["name"]
            gdf = gpd.read_file(gpkg_path, layer=layer_name)

            print(f"\n  [Layer]: {layer_name}")
            print(f"  Total Features: {len(gdf)}")
            print(f"  CRS: {gdf.crs} (EPSG: {gdf.crs.to_epsg() if gdf.crs else 'None'})")
            print(f"  Valid Geometries: {gdf.geometry.is_valid.sum()} / {len(gdf)}")

            cols_to_show = [
                "ADMIN_AREA_NAME",
                "ADMIN_AREA_GROUP_NAME",
                "FEATURE_AREA_SQM",
            ]
            avail_cols = [c for c in cols_to_show if c in gdf.columns]

            if avail_cols:
                print("\n  Attribute Preview:")
                print(gdf[avail_cols].head(5).to_string(index=False))
            else:
                print(f"\n  Columns: {gdf.columns.tolist()[:5]} ...")
        print("\n")


def inspect_all_raw_data():
    """Master entrypoint to inspect both CSV and GeoPackage raw datasets."""
    inspect_csv_files()
    inspect_geopackage()


if __name__ == "__main__":
    inspect_all_raw_data()