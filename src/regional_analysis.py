from pathlib import Path
import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_joined_dataset() -> gpd.GeoDataFrame:
    """Load the joined EPSG:3005 regional district tourism income layer."""
    file_path = PROCESSED_DIR / "bc_regional_tourism_income_joined.gpkg"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Joined layer not found at {file_path}. Run spatial_analysis.py first."
        )
    return gpd.read_file(file_path)


def load_base_boundaries() -> gpd.GeoDataFrame:
    """Load full BC regional district boundaries to serve as a complete basemap layer."""
    file_path = PROCESSED_DIR / "bc_regional_districts_clean.gpkg"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Clean boundaries layer not found at {file_path}. Run clean_data.py first."
        )
    return gpd.read_file(file_path)


def get_top_regions_by_year(
    gdf: gpd.GeoDataFrame, indicator: str = "Tourism Total", year: int = 2020, top_n: int = 5
) -> pd.DataFrame:
    """Extract and rank the top N regional districts by employment income for a specific year."""
    filtered = gdf[(gdf["Indicator_Name"] == indicator) & (gdf["Ref_Year"] == year)].copy()

    if filtered.empty:
        raise ValueError(f"No records found for indicator '{indicator}' in year {year}.")

    sorted_df = filtered.sort_values(by="Value", ascending=False).reset_index(drop=True)
    return sorted_df[["Region Name", "Value", "Ref_Year"]].head(top_n)


def compute_regional_summary_stats(
    gdf: gpd.GeoDataFrame, indicator: str = "Tourism Total"
) -> pd.DataFrame:
    """Calculate summary statistics for average employment income across all regional districts."""
    filtered = gdf[gdf["Indicator_Name"] == indicator].copy()

    summary = (
        filtered.groupby("Region Name")["Value"]
        .agg(["mean", "median", "std", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "mean": "Mean_Income",
                "median": "Median_Income",
                "std": "Std_Dev",
                "min": "Min_Income",
                "max": "Max_Income",
            }
        )
    )

    sorted_df = summary.sort_values(by="Mean_Income", ascending=False).reset_index(
        drop=True
    )
    return sorted_df.round(2)


def compute_growth_rates(
    gdf: gpd.GeoDataFrame, indicator: str = "Tourism Total"
) -> pd.DataFrame:
    """Calculate percentage growth in regional tourism average employment income between start and end years."""
    filtered = gdf[gdf["Indicator_Name"] == indicator].copy()

    filtered["Ref_Year"] = filtered["Ref_Year"].astype(int)
    start_year = int(filtered["Ref_Year"].min())
    end_year = int(filtered["Ref_Year"].max())

    filtered = filtered[filtered["Ref_Year"].isin([start_year, end_year])]

    pivoted = filtered.pivot(
        index="Region Name", columns="Ref_Year", values="Value"
    ).dropna()

    pivoted.columns = [str(int(col)) for col in pivoted.columns]

    col_name = f"Pct_Change_{start_year}_{end_year}"
    pivoted[col_name] = (
        (pivoted[str(end_year)] - pivoted[str(start_year)]) / pivoted[str(start_year)]
    ) * 100

    sorted_df = (
        pivoted.reset_index()
        .sort_values(by=col_name, ascending=False)
        .reset_index(drop=True)
    )
    return sorted_df.round(2)


def format_top_year_table(df: pd.DataFrame) -> str:
    """Format the top regions table for a specific year for clean terminal display."""
    formatted = df.copy()
    formatted = formatted.rename(
        columns={
            "Region Name": "Regional District",
            "Value": "Avg Employment Income ($)",
            "Ref_Year": "Year",
        }
    )
    formatted["Avg Employment Income ($)"] = formatted["Avg Employment Income ($)"].apply(
        lambda x: f"${x:,.2f}"
    )
    return formatted.to_string(index=False)


def format_summary_table(df: pd.DataFrame) -> str:
    """Format the summary statistics table for clean terminal display."""
    formatted = df.copy()

    formatted = formatted.rename(
        columns={
            "Region Name": "Regional District",
            "Mean_Income": "Mean Avg Income ($)",
            "Median_Income": "Median Avg Income ($)",
            "Std_Dev": "Std Dev ($)",
            "Min_Income": "Min Avg Income ($)",
            "Max_Income": "Max Avg Income ($)",
        }
    )

    currency_cols = [
        "Mean Avg Income ($)",
        "Median Avg Income ($)",
        "Std Dev ($)",
        "Min Avg Income ($)",
        "Max Avg Income ($)",
    ]
    for col in currency_cols:
        formatted[col] = formatted[col].apply(lambda x: f"${x:,.2f}")

    return formatted.to_string(index=False)


def format_growth_table(df: pd.DataFrame) -> str:
    """Format the growth table for clean terminal display."""
    formatted = df.copy()

    growth_col = [c for c in formatted.columns if c.startswith("Pct_Change")][0]

    formatted = formatted.rename(
        columns={
            "Region Name": "Regional District",
            "2010": "2010 Avg Income ($)",
            "2020": "2020 Avg Income ($)",
            growth_col: "10-Yr Growth (%)",
        }
    )

    formatted["2010 Avg Income ($)"] = formatted["2010 Avg Income ($)"].apply(
        lambda x: f"${x:,.2f}"
    )
    formatted["2020 Avg Income ($)"] = formatted["2020 Avg Income ($)"].apply(
        lambda x: f"${x:,.2f}"
    )
    formatted["10-Yr Growth (%)"] = formatted["10-Yr Growth (%)"].apply(
        lambda x: f"{x:.2f}%"
    )

    return formatted.to_string(index=False)


def run_regional_analysis():
    """Executes regional tourism income summaries, rankings, and growth rate computations."""
    print("=" * 65)
    print(" EXECUTING REGIONAL TOURISM INCOME ANALYSIS")
    print("=" * 65)

    gdf = load_joined_dataset()

    print("\nTop 5 Regional Districts by Average Tourism Employment Income in 2020:")
    top_2020_df = get_top_regions_by_year(gdf, indicator="Tourism Total", year=2020, top_n=5)
    print(format_top_year_table(top_2020_df))

    print("\nTop 5 Regional Districts by Historical Average Tourism Employment Income:")
    summary_df = compute_regional_summary_stats(gdf, indicator="Tourism Total")
    print(format_summary_table(summary_df.head(5)))

    print("\nTop 5 Fastest Growing Tourism Employment Income Districts (2010-2020):")
    growth_df = compute_growth_rates(gdf, indicator="Tourism Total")
    print(format_growth_table(growth_df.head(5)))


if __name__ == "__main__":
    run_regional_analysis()