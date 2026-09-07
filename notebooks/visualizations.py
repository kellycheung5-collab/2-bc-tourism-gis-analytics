from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from shapely.geometry import MultiPolygon

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "reference"


def get_land_representative_point(geom):
    """Select representative point from the primary landmass for multi-part coastal polygons."""
    if isinstance(geom, MultiPolygon):
        largest_poly = max(geom.geoms, key=lambda p: p.area)
        return largest_poly.representative_point()
    return geom.representative_point()


def generate_choropleth_map(
    gdf: gpd.GeoDataFrame,
    base_gdf: gpd.GeoDataFrame,
    indicator: str = "Tourism Total",
    year: int = 2020,
    output_filename: str = "regional_tourism_income_2020.png",
):
    """Generate production-ready choropleth map with customized label placement and callouts."""
    
    # Standardize column search across raw and cleaned schema variants
    ind_col = "Indicator" if "Indicator" in gdf.columns else "Indicator_Name"
    year_col = "Ref_Year" if "Ref_Year" in gdf.columns else "Year"

    subset = gdf[(gdf[ind_col] == indicator) & (gdf[year_col] == year)].copy()

    if subset.empty:
        print(f"No data available for indicator '{indicator}' and year {year}.")
        return

    fig, ax = plt.subplots(1, 1, figsize=(16, 14))

    # Base boundary layer
    base_gdf.plot(
        ax=ax,
        color="#f2f2f2",
        edgecolor="#b0b0b0",
        linewidth=0.5,
        linestyle="--",
    )

    # Choropleth thematic layer
    subset.plot(
        column="Value",
        cmap="YlGnBu",
        legend=True,
        legend_kwds={
            "label": f"Average Tourism Employment Income ($ CAD)",
            "orientation": "horizontal",
            "pad": 0.025,
            "shrink": 0.55,
            "aspect": 30,
        },
        ax=ax,
        edgecolor="#333333",
        linewidth=0.5,
    )

    CONGESTED_REGIONS = {
        "Alberni-Clayoquot": "1",
        "Capital": "2",
        "Central Okanagan": "3",
        "Comox Valley": "4",
        "Cowichan Valley": "5",
        "Fraser Valley": "6",
        "Kootenay Boundary": "7",
        "Metro Vancouver": "8",
        "Nanaimo": "9",
        "North Okanagan": "10",
        "Okanagan-Similkameen": "11",
        "qathet": "12",
        "Squamish-Lillooet": "13",
        "Strathcona": "14",
        "Sunshine Coast": "15",
    }

    # Badge coordinate adjustments (CRS units / meters)
    BADGE_ADJUSTMENTS = {
        "Capital": (24000, -22000),
        "Cowichan Valley": (0, 6000),
        "qathet": (10000, -20000),
        "Sunshine Coast": (-6000, -14000),
    }

    # Text label coordinate adjustments
    TEXT_LABEL_OFFSETS = {
        "Stikine Region (Unincorporated)": (-200000, 120000),
        "Peace River": (-40000, 85000),
        "North Coast": (30000, 75000),
        "Central Coast": (-25000, -20000),
        "Mount Waddington": (25000, -15000),
        "Fraser-Fort George": (0, -18000),
        "Thompson-Nicola": (15000, -12000),
        "Kitimat-Stikine": (-13000, -15000),
        "Northern Rockies RM": (-20000, 20000),
    }

    callout_items = []

    for _, row in subset.iterrows():
        region_full = str(row.get("Region Name", ""))
        label = (
            region_full.replace("Regional District of ", "")
            .replace(" Regional District", "")
            .replace("Regional District", "RD")
            .replace(" Regional Municipality", " RM")
        )

        base_point = get_land_representative_point(row.geometry)

        if label in CONGESTED_REGIONS:
            num_id = CONGESTED_REGIONS[label]
            callout_items.append((int(num_id), label))

            dx, dy = BADGE_ADJUSTMENTS.get(label, (0, 0))
            px, py = base_point.x + dx, base_point.y + dy

            pad_val = 0.12 if len(num_id) > 1 else 0.20

            ax.annotate(
                text=num_id,
                xy=(px, py),
                ha="center",
                va="center",
                fontsize=5.5,
                fontweight="bold",
                color="#8b0000",
                bbox=dict(
                    boxstyle=f"circle,pad={pad_val}",
                    facecolor="white",
                    edgecolor="#8b0000",
                    linewidth=0.7,
                    alpha=0.95,
                ),
            )
        else:
            dx, dy = TEXT_LABEL_OFFSETS.get(label, (0, 0))
            px, py = base_point.x + dx, base_point.y + dy

            ann = ax.annotate(
                text=label,
                xy=(px, py),
                ha="center",
                va="center",
                fontsize=7.5,
                fontweight="bold",
                color="#111111",
            )
            ann.set_path_effects([
                path_effects.withStroke(linewidth=2.2, foreground="white")
            ])

    # Southwestern Districts Key Table
    callout_items.sort(key=lambda x: x[0])
    half = (len(callout_items) + 1) // 2
    col1_items = callout_items[:half]
    col2_items = callout_items[half:]

    table_data = []
    for i in range(half):
        c1_str = f" {col1_items[i][0]:>2}. {col1_items[i][1]}" if i < len(col1_items) else ""
        c2_str = f" {col2_items[i][0]:>2}. {col2_items[i][1]}" if i < len(col2_items) else ""
        table_data.append([c1_str, c2_str])

    table = ax.table(
        cellText=table_data,
        colLabels=[" Southwestern Districts Key", ""],
        loc="lower left",
        bbox=[0.01, 0.06, 0.28, 0.16],
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(6.5)

    for col in (0, 1):
        cell = table[(0, col)]
        cell.set_facecolor("#e2e2e2")
        cell.set_edgecolor("#cccccc")
        if col == 0:
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_fontsize(7.0)

    for row in range(1, len(table_data) + 1):
        for col in (0, 1):
            cell = table[(row, col)]
            cell.set_facecolor("white")
            cell.set_edgecolor("#e0e0e0")
            cell.set_linewidth(0.5)

    ax.set_title(
        f"British Columbia Regional Districts: Average Tourism Employment Income ({year})",
        fontsize=16,
        pad=15,
        fontweight="bold",
    )
    ax.set_axis_off()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save raster (PNG)
    png_path = OUTPUT_DIR / output_filename
    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    
    # Save vector (PDF)
    pdf_path = png_path.with_suffix(".pdf")
    plt.savefig(pdf_path, bbox_inches="tight")
    
    plt.close()
    print(f"Map rendered successfully:\n - {png_path}\n - {pdf_path}")


if __name__ == "__main__":
    try:
        from regional_analysis import load_base_boundaries, load_joined_dataset
        gdf = load_joined_dataset()
        base_gdf = load_base_boundaries()
        generate_choropleth_map(gdf, base_gdf, indicator="Tourism Total", year=2020)
    except ImportError:
        print("Run `visualizations.py` from the root pipeline module or via `main.py`.")