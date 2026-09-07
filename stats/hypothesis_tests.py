"""
stats/hypothesis_tests.py
-------------------------
Two-Stage Non-Parametric Hypothesis Testing Pipeline on BC Tourism Income Data.

Statistical Design Rationale:
-----------------------------
1. Stage 1 — Global Omnibus Test (Kruskal-Wallis H-Test):
   Evaluates whether overall median tourism employment income differs across BC's 
   regional districts.
   - Non-Normality: Regional income distributions exhibit positive skew.
   - Heteroscedasticity: High variance across industrial corridors (e.g., Kitimat-Stikine) 
     violates homoscedasticity.
   - Small, Unbalanced Samples: Regional subdivisions have small (n < 30) and unequal sample sizes.
   - Outlier Robustness: Rank-based evaluation prevents mega-project wage spikes 
     from distorting group-level inference.

2. Stage 2 — Pairwise Post-Hoc Test (Dunn's Test with Bonferroni Correction):
   If Stage 1 yields p < 0.05, Dunn's test identifies specific regional district pairs 
   driving the global variance.
   - Preserves Rank Mechanics: Aligns directly with Kruskal-Wallis non-parametric rankings.
   - FWER Control: Applies Bonferroni adjustment across all pairwise comparisons 
     to prevent Type I error inflation (false positives).
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
from scipy import stats

# Optional dependency for automated Dunn's post-hoc test
try:
    import scikit_posthocs as sp
    HAS_POSTHOCS = True
except ImportError:
    HAS_POSTHOCS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "bc_regional_tourism_income_joined.gpkg"


def load_dataset(data_path: Path) -> gpd.GeoDataFrame:
    """Load joined regional dataset from GeoPackage."""
    if not data_path.exists():
        raise FileNotFoundError(
            f"Joined dataset not found at: {data_path}. "
            f"Run perform_regional_spatial_join() first."
        )
    return gpd.read_file(data_path)


def run_regional_income_tests(gdf: gpd.GeoDataFrame = None):
    """
    Execute Kruskal-Wallis H-test followed by Dunn's post-hoc test 
    on regional tourism employment income data.
    """
    if gdf is None:
        gdf = load_dataset(DATA_PATH)

    print("\n" + "=" * 65)
    print(" EXECUTING TWO-STAGE HYPOTHESIS TESTING PIPELINE")
    print("=" * 65)

    # Standardize column mapping dynamically
    col_map = {col.lower(): col for col in gdf.columns}
    join_key = col_map.get("region name") or "Region Name"

    # Identify numeric income metric column
    income_col = (
        col_map.get("average_employment_income")
        or col_map.get("income")
        or col_map.get("value")
        or col_map.get("avg_income")
    )

    if not income_col:
        numeric_cols = gdf.select_dtypes(include=["float64", "int64"]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c.lower() not in ["id", "objectid", "ref_year", "year"]]
        if numeric_cols:
            income_col = numeric_cols[0]

    if not income_col or income_col not in gdf.columns:
        raise KeyError(
            f"Could not identify income metric column. Available columns: {gdf.columns.tolist()}"
        )

    # Clean data for statistical evaluation
    clean_data = gdf.dropna(subset=[join_key, income_col]).copy()

    # Stage 1: Group values by Regional District
    groups = [group[income_col].values for _, group in clean_data.groupby(join_key)]

    print(f" Target Indicator Column : {income_col}")
    print(f" Total Records Analyzed   : {len(clean_data)}")
    print(f" Unique Regional Groups   : {len(groups)}")

    if len(groups) <= 1:
        print("\n[!] Insufficient regional variance for testing.")
        return None, None

    # Run Stage 1: Kruskal-Wallis H-Test
    stat, p_val = stats.kruskal(*groups)
    
    print("-" * 65)
    print(" STAGE 1: GLOBAL OMNIBUS TEST (KRUSKAL-WALLIS)")
    print("-" * 65)
    print(f" Kruskal-Wallis H-Statistic : {stat:.4f}")
    print(f" p-value                    : {p_val:.4e}")

    if p_val >= 0.05:
        print(" Verdict: No statistically significant difference in median income across regions (p >= 0.05).")
        return stat, p_val

    print(" Verdict: Statistically significant difference in median income across regions (p < 0.05).")

    # Stage 2: Pairwise Post-Hoc Test (Dunn's Test)
    print("\n" + "-" * 65)
    print(" STAGE 2: PAIRWISE POST-HOC TEST (DUNN'S WITH BONFERRONI)")
    print("-" * 65)

    if HAS_POSTHOCS:
        dunn_df = sp.posthoc_dunn(
            clean_data,
            val_col=income_col,
            group_col=join_key,
            p_adjust="bonferroni"
        )

        # Unpivot matrix into structured pairwise comparisons
        pairs = (
            dunn_df.stack()
            .reset_index()
            .rename(columns={"level_0": "Region_A", "level_1": "Region_B", 0: "p_adj"})
        )
        # Filter for unique, statistically significant regional pairs
        sig_pairs = pairs[(pairs["Region_A"] < pairs["Region_B"]) & (pairs["p_adj"] < 0.05)]
        sig_pairs = sig_pairs.sort_values("p_adj")

        print(f" Total Significant Pairwise Differences (p_adj < 0.05): {len(sig_pairs)}")
        if not sig_pairs.empty:
            print("\n Top Significant Regional Disparities:")
            print(sig_pairs.head(10).to_string(index=False))
    else:
        print(" [!] scikit-posthocs package not installed.")
        print("     To view full pairwise post-hoc outputs, install via: pip install scikit-posthocs")

    print("=" * 65 + "\n")
    return stat, p_val


if __name__ == "__main__":
    run_regional_income_tests()