import numpy as np
import pandas as pd
import pytest

from notebooks.clean_data import (
    apply_indicator_decomposition,
    build_clean_column_headers,
    decompose_food_services,
    decompose_tourism_sector,
    decompose_transportation,
    decompose_traveller_entries,
    normalize_text,
)

# =============================================================================
# 1. TEXT NORMALIZATION TESTS
# =============================================================================


def test_normalize_text_footnote_removal():
    """Verify stripping of footnote numbers attached to words and separated by commas."""
    assert normalize_text("Places1") == "Places"
    assert normalize_text("Index1") == "Index"
    assert normalize_text("BC2") == "BC"
    assert normalize_text("meals5") == "meals"
    assert normalize_text("Air Passenger Traffic 1,2") == "Air Passenger Traffic"


def test_normalize_text_hyphenation_fixes():
    """Verify fixing of line-wrap hyphenation artifacts."""
    assert normalize_text("Accom-modation Services") == "Accommodation Services"
    assert normalize_text("accom-modation") == "Accommodation"
    assert normalize_text("entertain-ment") == "Entertainment"


def test_normalize_text_whitespace_and_newlines():
    """Verify cleaning of embedded newlines and collapsing of whitespace."""
    dirty = "   Vancouver \n   Air  Passenger   Traffic1  "
    clean = normalize_text(dirty)
    assert clean == "Vancouver Air Passenger Traffic"


def test_normalize_text_nan_handling():
    """Verify NaN / None handling without raising exceptions."""
    assert pd.isna(normalize_text(np.nan))
    assert pd.isna(normalize_text(None))


# =============================================================================
# 2. FEATURE DECOMPOSITION TESTS
# =============================================================================


def test_decompose_food_services(sample_food_services_df):
    """Verify parsing of Region and Category dimensions for food services."""
    df = sample_food_services_df.rename(columns={"Indicator": "Indicator_Clean"})
    result = decompose_food_services(df)

    assert "Region" in result.columns
    assert "Category" in result.columns
    assert list(result["Region"]) == ["BC", "Canada", "BC"]
    assert list(result["Category"]) == [
        "Total",
        "Drinking Places",
        "All Services",
    ]


def test_decompose_tourism_sector(sample_tourism_sector_df):
    """Verify parsing of Domain, Sub_Indicator, and Unit dimensions across all rows."""
    df = sample_tourism_sector_df.rename(columns={"Indicator": "Indicator_Clean"})
    result = decompose_tourism_sector(df)

    assert list(result["Domain"]) == [
        "Employment",
        "Hotel Industry",
        "Hotel Industry",
        "Consumer Price Index",
    ]
    assert list(result["Sub_Indicator"]) == [
        "Accommodation",
        "Occupancy Rate",
        "Room Rate",
        "Restaurant meals (2017=100)",
    ]
    assert list(result["Unit"]) == ["000s", "%", "$", "Index (2017=100)"]


def test_decompose_transportation(sample_transportation_df):
    """Verify parsing of Transport_Mode, Location, and Segment dimensions across all rows."""
    df = sample_transportation_df.rename(columns={"Indicator": "Indicator_Clean"})
    result = decompose_transportation(df)

    assert list(result["Transport_Mode"]) == [
        "Air Passenger Traffic",
        "Air Passenger Traffic",
        "Ferry Traffic",
    ]
    assert list(result["Location"]) == ["Vancouver", "Victoria", "BC Ferries"]
    assert list(result["Segment"]) == [
        "Enplaned & Deplaned",
        "Total",
        "Passengers",
    ]


def test_decompose_traveller_entries(sample_traveller_entries_df):
    """Verify parsing of Origin_Region and Entry_Type dimensions across all rows."""
    df = sample_traveller_entries_df.rename(columns={"Indicator": "Indicator_Clean"})
    result = decompose_traveller_entries(df)

    assert list(result["Origin_Region"]) == ["USA", "Overseas", "Total"]
    assert list(result["Entry_Type"]) == [
        "Same Day Automobile",
        "Europe Direct",
        "Total",
    ]


# =============================================================================
# 3. PIPELINE DECOMPOSITION INTEGRATION TESTS
# =============================================================================


def test_apply_indicator_decomposition():
    """Verify end-to-end indicator normalization and column reordering."""
    raw_df = pd.DataFrame(
        {
            "Year": [2022, 2023],
            "Indicator_Name": [
                "Employment in key tourism industries (000s) - Accom-modation1",
                "Hotel Industry - Occupancy Rate 1,2",
            ],
            "Value": [15.2, 65.4],
        }
    )

    processed_df = apply_indicator_decomposition(
        raw_df, domain_name="tourism_sector"
    )

    assert "Indicator" in processed_df.columns
    assert "Indicator_Name" not in processed_df.columns
    assert (
        processed_df["Indicator"].iloc[0]
        == "Employment in key tourism industries (000s) - Accommodation"
    )
    assert processed_df["Domain"].iloc[0] == "Employment"
    assert processed_df["Unit"].iloc[1] == "%"
    assert processed_df.columns[-1] == "Value"


# =============================================================================
# 4. COMPOSITE HEADER BUILDING TESTS
# =============================================================================


def test_build_clean_column_headers():
    """Verify multi-tier header building with forward-fill and deduplication."""
    mock_raw = pd.DataFrame(
        [
            ["Period", "Food Services Receipts", "Food Services Receipts"],
            [np.nan, "British Columbia", "Canada"],
            [np.nan, "Food Services", "Drinking Places"],
            [np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan],
        ]
    )

    headers = build_clean_column_headers(mock_raw)

    assert len(headers) == 3
    assert headers[0] == "indicator_col_0"
    assert headers[1] == "Food Services Receipts - British Columbia - Food Services"
    assert headers[2] == "Food Services Receipts - Canada - Drinking Places"