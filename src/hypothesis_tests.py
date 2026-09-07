"""
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

2. Stage 2 — Pairwise Post-Hoc Test (Dunn's Test with Benjamini-Hochberg FDR):
   If Stage 1 yields p < 0.05, Dunn's test identifies specific regional district pairs 
   driving the global variance.
   - Preserves Rank Mechanics: Aligns directly with Kruskal-Wallis non-parametric rankings.
   - FDR Control: Applies Benjamini-Hochberg adjustment ('fdr_bh') across all C(29,2)=406 
     pairwise comparisons. This avoids the severe loss of statistical power caused by standard 
     Bonferroni correction when sample sizes per region are small (n = 3 years).

The tidy CSV contains eight distinct indicator types per region per year (`Total`,
`Tourism Total`, and six tourism sub-sectors). These categories have very different
typical magnitudes, so a single test run must be restricted to one indicator at a time.
This module supports both: testing a single named indicator, or looping across all 
indicators independently.
"""

from pathlib import Path
import pandas as pd
from scipy import stats

# Optional dependency for automated Dunn's post-hoc test
try:
    import scikit_posthocs as sp
    HAS_POSTHOCS = True
except ImportError:
    HAS_POSTHOCS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "laep_regional_incomes_tidy.csv"

# Default indicator to test when none is specified.
DEFAULT_INDICATOR = "Tourism Total"


def load_dataset(data_path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the tidy LAEP regional income dataset (no geometry required)."""
    if not data_path.exists():
        raise FileNotFoundError(
            f"Tidy LAEP dataset not found at: {data_path}. "
            f"Run clean_data.py first to generate it."
        )
    return pd.read_csv(data_path)


def run_regional_income_tests(
    df: pd.DataFrame = None, 
    indicator: str = DEFAULT_INDICATOR, 
    p_adjust: str = "fdr_bh",
    verbose: bool = True
):
    """
    Execute Kruskal-Wallis H-test followed by Dunn's post-hoc test on regional
    tourism employment income data, restricted to a single indicator.

    Parameters
    ----------
    df : DataFrame, optional
        Pre-loaded tidy LAEP dataset. If None, loads from DATA_PATH.
    indicator : str, default "Tourism Total"
        The single Indicator_Name value to test.
    p_adjust : str, default "fdr_bh"
        Multiple testing correction method passed to scikit-posthocs Dunn test.
        Uses Benjamini-Hochberg FDR ('fdr_bh') by default to maintain statistical
        power across 406 pairwise comparisons with n=3 per group. Alternatives include
        'holm' or 'bonferroni'.
    verbose : bool, default True
        Whether to print progress and results to the console.

    Returns
    -------
    (stat, p_val, sig_pairs) : tuple
        Kruskal-Wallis H-statistic, p-value, and a DataFrame of significant
        Dunn's post-hoc pairs (empty if Stage 1 was not significant or
        scikit-posthocs is unavailable).
    """
    if df is None:
        df = load_dataset()

    available = sorted(df["Indicator_Name"].dropna().unique().tolist())
    if indicator not in available:
        raise ValueError(
            f"Indicator '{indicator}' not found in 'Indicator_Name' column. "
            f"Available indicators: {available}"
        )

    subset = df[df["Indicator_Name"] == indicator].copy()
    clean_data = subset.dropna(subset=["Region Name", "Value"]).copy()

    groups = [group["Value"].values for _, group in clean_data.groupby("Region Name")]

    if verbose:
        print("\n" + "=" * 65)
        print(f" EXECUTING TWO-STAGE HYPOTHESIS TESTING PIPELINE — '{indicator}'")
        print("=" * 65)
        print(f" Target Indicator          : {indicator}")
        print(f" Total Records Analyzed    : {len(clean_data)}")
        print(f" Unique Regional Groups    : {len(groups)}")
        print(f" Post-Hoc Adjustment       : {p_adjust.upper()}")

    empty_pairs = pd.DataFrame(columns=["Region_A", "Region_B", "p_adj"])

    if len(groups) <= 1:
        if verbose:
            print("\n[!] Insufficient regional variance for testing.")
        return None, None, empty_pairs

    # Stage 1: Kruskal-Wallis H-Test
    stat, p_val = stats.kruskal(*groups)

    if verbose:
        print("-" * 65)
        print(" STAGE 1: GLOBAL OMNIBUS TEST (KRUSKAL-WALLIS)")
        print("-" * 65)
        print(f" Kruskal-Wallis H-Statistic : {stat:.4f}")
        print(f" p-value                    : {p_val:.4e}")

    if p_val >= 0.05:
        if verbose:
            print(" Verdict: No statistically significant difference in median income across regions (p >= 0.05).")
        return stat, p_val, empty_pairs

    if verbose:
        print(" Verdict: Statistically significant difference in median income across regions (p < 0.05).")

    # Stage 2: Pairwise Post-Hoc Test (Dunn's Test)
    if verbose:
        print("\n" + "-" * 65)
        print(f" STAGE 2: PAIRWISE POST-HOC TEST (DUNN'S WITH {p_adjust.upper()})")
        print("-" * 65)

    sig_pairs = empty_pairs

    if HAS_POSTHOCS:
        dunn_df = sp.posthoc_dunn(
            clean_data,
            val_col="Value",
            group_col="Region Name",
            p_adjust=p_adjust,
        )

        pairs = (
            dunn_df.stack()
            .reset_index()
            .rename(columns={"level_0": "Region_A", "level_1": "Region_B", 0: "p_adj"})
        )
        sig_pairs = pairs[(pairs["Region_A"] < pairs["Region_B"]) & (pairs["p_adj"] < 0.05)]
        sig_pairs = sig_pairs.sort_values("p_adj").reset_index(drop=True)

        if verbose:
            print(f" Total Significant Pairwise Differences (p_adj < 0.05): {len(sig_pairs)}")
            if not sig_pairs.empty:
                print("\n Top Significant Regional Disparities:")
                print(sig_pairs.head(10).to_string(index=False))
    else:
        if verbose:
            print(" [!] scikit-posthocs package not installed.")
            print("     To view full pairwise post-hoc outputs, install via: pip install scikit-posthocs")

    if verbose:
        print("=" * 65 + "\n")

    return stat, p_val, sig_pairs


def format_all_indicator_summary(summary_df: pd.DataFrame) -> str:
    """Format the all-indicators summary table for clean terminal/README-style display."""
    formatted = summary_df.copy()

    formatted["H_Statistic"] = formatted["H_Statistic"].apply(
        lambda x: f"{x:.4f}" if pd.notna(x) else "—"
    )
    formatted["p_value"] = formatted["p_value"].apply(
        lambda x: f"{x:.4f}" if pd.notna(x) else "—"
    )
    formatted["Significant (p<0.05)"] = formatted["Significant (p<0.05)"].apply(
        lambda x: "Yes" if x else "No"
    )

    formatted = formatted.rename(
        columns={
            "Indicator": "Indicator",
            "H_Statistic": "H-Statistic",
            "p_value": "p-value",
            "Significant (p<0.05)": "Stage 1 Significant?",
            "Significant_Dunn_Pairs": "Significant Dunn Pairs",
        }
    )

    return formatted.to_string(index=False)


def run_all_indicator_tests(
    df: pd.DataFrame = None, 
    p_adjust: str = "fdr_bh", 
    verbose: bool = True
) -> pd.DataFrame:
    """
    Run the two-stage test independently for every indicator in the dataset
    (Total, Tourism Total, and each of the 6 tourism sub-sectors).

    Returns a summary DataFrame with one row per indicator: H-statistic,
    p-value, significance flag, and count of significant Dunn's pairs.
    """
    if df is None:
        df = load_dataset()

    indicators = sorted(df["Indicator_Name"].dropna().unique().tolist())
    rows = []

    for ind in indicators:
        stat, p_val, sig_pairs = run_regional_income_tests(
            df, indicator=ind, p_adjust=p_adjust, verbose=False
        )
        rows.append(
            {
                "Indicator": ind,
                "H_Statistic": stat,
                "p_value": p_val,
                "Significant (p<0.05)": (p_val is not None and p_val < 0.05),
                "Significant_Dunn_Pairs": len(sig_pairs),
            }
        )

    summary = pd.DataFrame(rows)

    if verbose:
        print("\n" + "=" * 65)
        print(f" SUMMARY — ALL INDICATORS TESTED INDEPENDENTLY ({p_adjust.upper()})")
        print("=" * 65)
        print(format_all_indicator_summary(summary))
        print("-" * 65)
        print(
            f" Note: Multiple testing correction applied using '{p_adjust}' adjustment.\n"
            " Benjamini-Hochberg (fdr_bh) controls the False Discovery Rate to maintain\n"
            " statistical power across C(29,2)=406 regional pairs."
        )
        print("=" * 65 + "\n")

    return summary


if __name__ == "__main__":
    run_all_indicator_tests(p_adjust="fdr_bh")