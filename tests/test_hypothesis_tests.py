import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.hypothesis_tests import (
    load_dataset,
    run_regional_income_tests,
    run_all_indicator_tests,
    format_all_indicator_summary,
    DEFAULT_INDICATOR,
)


@pytest.fixture
def mock_laep_df():
    """Generates a synthetic LAEP regional income DataFrame for testing."""
    regions = ["Region A", "Region B", "Region C"]
    indicators = ["Tourism Total", "Transportation"]
    years = [2018, 2019, 2020]

    rows = []
    np.random.seed(42)
    for reg in regions:
        base_val = 30000 if reg == "Region A" else (40000 if reg == "Region B" else 50000)
        for ind in indicators:
            for yr in years:
                val = base_val + np.random.randint(-1000, 1000)
                rows.append({
                    "Region Name": reg,
                    "Ref_Year": yr,
                    "Indicator_Name": ind,
                    "Value": float(val)
                })

    return pd.DataFrame(rows)


def test_load_dataset_file_not_found(tmp_path):
    """Verify FileNotFoundError is raised when data file does not exist."""
    fake_path = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError, match="Tidy LAEP dataset not found"):
        load_dataset(data_path=fake_path)


def test_run_regional_income_tests_invalid_indicator(mock_laep_df):
    """Verify ValueError is raised when specifying an indicator not present in dataset."""
    with pytest.raises(ValueError, match="Indicator 'NonExistent' not found"):
        run_regional_income_tests(df=mock_laep_df, indicator="NonExistent", verbose=False)


def test_run_regional_income_tests_single_indicator(mock_laep_df):
    """Verify Kruskal-Wallis and Dunn's tests run on a single valid indicator."""
    stat, p_val, sig_pairs = run_regional_income_tests(
        df=mock_laep_df, 
        indicator="Tourism Total", 
        verbose=False
    )

    assert stat is not None
    assert p_val is not None
    assert isinstance(stat, float)
    assert isinstance(p_val, float)
    assert 0.0 <= p_val <= 1.0
    assert isinstance(sig_pairs, pd.DataFrame)
    assert set(sig_pairs.columns) == {"Region_A", "Region_B", "p_adj"}


def test_run_regional_income_tests_insufficient_groups():
    """Verify handling when dataset contains one or fewer regional groups."""
    single_group_df = pd.DataFrame([
        {"Region Name": "Region A", "Ref_Year": 2020, "Indicator_Name": "Tourism Total", "Value": 35000.0},
        {"Region Name": "Region A", "Ref_Year": 2021, "Indicator_Name": "Tourism Total", "Value": 36000.0},
    ])
    
    stat, p_val, sig_pairs = run_regional_income_tests(
        df=single_group_df, 
        indicator="Tourism Total", 
        verbose=False
    )

    assert stat is None
    assert p_val is None
    assert sig_pairs.empty


def test_run_all_indicator_tests(mock_laep_df):
    """Verify running hypothesis tests independently across all indicator categories."""
    summary = run_all_indicator_tests(df=mock_laep_df, verbose=False)

    assert isinstance(summary, pd.DataFrame)
    assert len(summary) == 2  # Tourism Total, Transportation
    expected_cols = {"Indicator", "H_Statistic", "p_value", "Significant (p<0.05)", "Significant_Dunn_Pairs"}
    assert set(summary.columns) == expected_cols


def test_format_all_indicator_summary(mock_laep_df):
    """Verify summary table formatting function outputs clean string representation."""
    summary = run_all_indicator_tests(df=mock_laep_df, verbose=False)
    formatted_str = format_all_indicator_summary(summary)

    assert isinstance(formatted_str, str)
    assert "Stage 1 Significant?" in formatted_str
    assert "H-Statistic" in formatted_str