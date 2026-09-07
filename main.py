from src.clean_data import run_pipeline as run_cleaning_pipeline
from src.hypothesis_tests import run_all_indicator_tests
from src.inspect_raw_data import inspect_all_raw_data
from src.regional_analysis import run_regional_analysis
from src.spatial_analysis import run_spatial_analysis
from src.visualizations import render_choropleth_maps
from src.visualize_tourism_trends import generate_all_visualizations


def main():
    print("=" * 65)
    print(" STARTING BC TOURISM GIS & ANALYTICS PIPELINE")
    print("=" * 65)

    # 1. Raw Data Inspection
    print("\n[1/6] Inspecting Raw Datasets...")
    inspect_all_raw_data()

    # 2. Data Cleaning & Feature Extraction
    print("\n[2/6] Running Data Cleaning & Feature Extraction Pipeline...")
    run_cleaning_pipeline()

    # 3. Regional Spatial & Attribute Join
    print("\n[3/6] Merging Spatial Boundaries with Employment Incomes...")
    run_spatial_analysis()

    # 4. Regional Income Summaries & Growth Analysis
    print("\n[4/6] Computing Regional Income Rankings & Growth Rates...")
    run_regional_analysis()

    # 5. Non-Parametric Statistical Testing
    print("\n[5/6] Executing Non-Parametric Hypothesis Tests...")
    run_all_indicator_tests(p_adjust="fdr_bh")

    # 6. Map & Trend Chart Rendering
    print("\n[6/6] Rendering Maps & Time-Series Trend Charts...")
    render_choropleth_maps()
    generate_all_visualizations()

    print("\n" + "=" * 65)
    print(" PIPELINE EXECUTION COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()