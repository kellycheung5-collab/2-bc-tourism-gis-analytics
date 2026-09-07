import geopandas as gpd
import pytest

def test_joined_gpkg_integrity(processed_dir):
    """Verify GeoPackage existence, EPSG:3005 projection, and joined income attributes."""
    joined_path = processed_dir / "bc_regional_tourism_income_joined.gpkg"
    assert joined_path.exists(), "Joined GeoPackage file is missing"
    
    gdf = gpd.read_file(joined_path)
    assert not gdf.empty, "Joined GeoPackage layer contains no features"
    assert gdf.crs.to_epsg() == 3005, f"Expected EPSG:3005, but got {gdf.crs}"
    
    # Check for normalized regional identifier and joined income attributes
    assert "Region Name" in gdf.columns
    assert "Ref_Year" in gdf.columns
    assert "Indicator_Name" in gdf.columns
    assert "Value" in gdf.columns