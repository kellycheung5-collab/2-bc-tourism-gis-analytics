from pathlib import Path
import geopandas as gpd
import pandas as pd

# Set up project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def perform_regional_spatial_join() -> gpd.GeoDataFrame:
    """Merges clean regional district spatial boundaries with LAEP average employment income metrics."""
    print("=" * 65)
    print(" EXECUTING REGIONAL SPATIAL & ATTRIBUTE JOIN")
    print("=" * 65)

    gpkg_path = PROCESSED_DIR / "bc_regional_districts_clean.gpkg"
    csv_path = PROCESSED_DIR / "laep_regional_incomes_tidy.csv"

    # 1. File existence validation
    if not gpkg_path.exists():
        raise FileNotFoundError(
            f"Spatial layer not found: {gpkg_path}. Run clean_data.py first."
        )
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Tabular dataset not found: {csv_path}. Run clean_data.py first."
        )

    # 2. Load layers
    gdf = gpd.read_file(gpkg_path)
    df_income = pd.read_csv(csv_path)

    # Ensure join key exists in spatial layer
    join_key = "Region Name"
    if join_key not in gdf.columns:
        raise KeyError(
            f"Join column '{join_key}' not found in {gpkg_path.name}. "
            f"Available columns: {gdf.columns.tolist()}"
        )

    # 3. Standardize string formatting on join keys
    gdf[join_key] = gdf[join_key].astype(str).str.strip()
    df_income[join_key] = df_income[join_key].astype(str).str.strip()

    # 4. Check key alignment before merging
    spatial_regions = set(gdf[join_key].unique())
    income_regions = set(df_income[join_key].unique())

    unmatched_spatial = spatial_regions - income_regions
    unmatched_income = income_regions - spatial_regions

    if unmatched_spatial:
        print(f"[!] Warning: {len(unmatched_spatial)} spatial regions have no employment income data:")
        for r in sorted(unmatched_spatial):
            print(f"    - {r}")

    if unmatched_income:
        print(f"[!] Warning: {len(unmatched_income)} employment income data regions could not be mapped spatially:")
        for r in sorted(unmatched_income):
            print(f"    - {r}")

    # 5. Execute attribute join
    joined_gdf = gdf.merge(
        df_income,
        on=join_key,
        how="inner",  # Inner join retains matched spatial records across years
    )

    # 6. Save joined GeoPackage layer
    output_path = PROCESSED_DIR / "bc_regional_tourism_income_joined.gpkg"
    joined_gdf.to_file(output_path, driver="GPKG")

    print("\n" + "-" * 65)
    print(f"Successfully created joined spatial layer:")
    print(f" Output File     : {output_path.name}")
    print(f" Total Features  : {len(joined_gdf)}")
    print(f" Unique Regions  : {joined_gdf[join_key].nunique()}")
    print(f" Active CRS      : {joined_gdf.crs}")
    print("-" * 65)

    return joined_gdf


def run_spatial_analysis() -> gpd.GeoDataFrame:
    """Wrapper entry point for running spatial analysis tasks in main.py."""
    return perform_regional_spatial_join()


if __name__ == "__main__":
    run_spatial_analysis()