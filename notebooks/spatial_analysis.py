import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def perform_regional_spatial_join():
    # Load spatial boundary layer
    gdf = gpd.read_file(PROCESSED_DIR / "bc_regional_districts_clean.gpkg")
    
    # Load regional tabular data
    df_income = pd.read_csv(PROCESSED_DIR / "laep_regional_incomes_tidy.csv")
    
    # Clean up whitespace strings to ensure exact matches
    gdf["ADMIN_AREA_NAME"] = gdf["ADMIN_AREA_NAME"].astype(str).str.strip()
    df_income["Region Name"] = df_income["Region Name"].astype(str).str.strip()

    # Execute attribute join on Region Name
    joined_gdf = gdf.merge(
        df_income, 
        left_on="ADMIN_AREA_NAME", 
        right_on="Region Name", 
        how="left"
    )
    
    # Export joined GeoPackage layer
    output_path = PROCESSED_DIR / "bc_regional_tourism_income_joined.gpkg"
    joined_gdf.to_file(output_path, driver="GPKG")
    print(f"Successfully saved joined layer to {output_path}")

if __name__ == "__main__":
    perform_regional_spatial_join()