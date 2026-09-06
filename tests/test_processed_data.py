from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


@pytest.mark.parametrize(
    "filename,expected_cols",
    [
        (
            "laep_regional_incomes_tidy.csv",
            ["Region Name", "Ref_Year", "Indicator_Name", "Value"],
        ),
        (
            "indicator_food_services_receipts_annual_tidy.csv",
            ["Year", "Indicator", "Metric", "Region", "Category", "Value"],
        ),
        (
            "indicator_tourism_sector_indicators_annual_tidy.csv",
            ["Year", "Indicator", "Domain", "Sub_Indicator", "Unit", "Value"],
        ),
        (
            "indicator_transportation_indicators_monthly_tidy.csv",
            [
                "Year",
                "Period_Label",
                "Indicator",
                "Transport_Mode",
                "Location",
                "Segment",
                "Value",
            ],
        ),
    ],
)
def test_csv_schema_and_non_empty(filename, expected_cols):
    file_path = PROCESSED_DIR / filename
    assert file_path.exists(), f"Missing processed file: {filename}"

    df = pd.read_csv(file_path)
    assert not df.empty, f"File is empty: {filename}"
    for col in expected_cols:
        assert col in df.columns, f"Missing column '{col}' in {filename}"


def test_no_null_keys_in_laep_incomes():
    df = pd.read_csv(PROCESSED_DIR / "laep_regional_incomes_tidy.csv")
    assert df["Region Name"].notna().all()
    assert df["Ref_Year"].notna().all()
    assert df["Value"].notna().all()


def test_spatial_gpkg_integrity():
    """Verify GeoPackage existence, non-emptiness, and BC Albers (EPSG:3005) CRS alignment."""
    gpkg_path = PROCESSED_DIR / "bc_regional_districts_clean.gpkg"
    assert gpkg_path.exists(), "Cleaned GeoPackage file is missing"

    gdf = gpd.read_file(gpkg_path)
    assert not gdf.empty, "GeoPackage layer contains no features"
    
    # .to_epsg() directly checks the EPSG integer code regardless of string formatting
    assert gdf.crs.to_epsg() == 3005, f"Expected EPSG:3005, but got {gdf.crs}"