from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "legend.fontsize": 9.5,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
})

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "reference"


def load_all_datasets() -> dict[str, pd.DataFrame]:
    datasets = {
        "annual_macro": PROCESSED_DIR / "bc_stats_annual_indicators_tidy.csv",
        "transportation": PROCESSED_DIR / "indicator_transportation_indicators_annual_tidy.csv",
        "sector_indicators": PROCESSED_DIR / "indicator_tourism_sector_indicators_annual_tidy.csv",
        "food_services": PROCESSED_DIR / "indicator_food_services_receipts_annual_tidy.csv",
    }

    loaded_dfs = {}
    for name, path in datasets.items():
        if path.exists():
            loaded_dfs[name] = pd.read_csv(path)
        else:
            print(f"[!] Warning: Dataset {path.name} not found in {PROCESSED_DIR}")

    return loaded_dfs


def plot_annual_macro_trends(df_annual: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(12, 6.5), dpi=300)

    year_col = "Year" if "Year" in df_annual.columns else "Ref_Year"
    df_annual[year_col] = df_annual[year_col].astype(int)

    if "Indicator" in df_annual.columns and "Value" in df_annual.columns:
        pivoted = df_annual.pivot(index=year_col, columns="Indicator", values="Value").reset_index()
    else:
        pivoted = df_annual.sort_values(year_col)

    color_nom = "#1F77B4"
    color_real = "#2CA02C"
    color_emp = "#C05621"

    lines = []

    if "GDP at Basic Prices ($ million)" in pivoted.columns:
        l1 = ax1.plot(
            pivoted[year_col],
            pivoted["GDP at Basic Prices ($ million)"],
            color=color_nom,
            marker="o",
            linewidth=2.2,
            label="Nominal GDP (Current Prices)",
        )
        lines.extend(l1)

    if "Real GDP ($2017 million)" in pivoted.columns:
        l2 = ax1.plot(
            pivoted[year_col],
            pivoted["Real GDP ($2017 million)"],
            color=color_real,
            marker="^",
            linestyle="--",
            linewidth=2.2,
            label="Real GDP (Chained 2017 $)",
        )
        lines.extend(l2)

    ax1.set_xlabel("Year", fontweight="bold", labelpad=10, color="#2D3748")
    ax1.set_ylabel("Tourism GDP ($ Millions CAD)", fontweight="bold", labelpad=10, color="#2D3748")
    ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
    ax1.tick_params(colors="#2D3748")
    ax1.set_ylim(3500, 10800)

    if "Employment (thousands)" in pivoted.columns:
        ax2 = ax1.twinx()
        l3 = ax2.plot(
            pivoted[year_col],
            pivoted["Employment (thousands)"],
            color=color_emp,
            marker="s",
            linestyle=":",
            linewidth=2.2,
            label="Direct Tourism Employment (Thousands)",
        )
        ax2.set_ylabel("Direct Tourism Employment (Thousands)", color=color_emp, fontweight="bold", labelpad=12)
        ax2.tick_params(axis="y", labelcolor=color_emp, colors=color_emp)
        ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        ax2.set_ylim(55, 150)
        lines.extend(l3)

    ax1.axvspan(2019.8, 2021.2, color="#718096", alpha=0.15, linestyle="--")

    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", frameon=True, facecolor="white", framealpha=0.95, edgecolor="#CBD5E0")

    ax1.set_title(
        "British Columbia Tourism Economic Indicators: Real vs. Nominal GDP and Direct Employment",
        fontsize=14,
        fontweight="bold",
        pad=15,
        color="#1A202C",
    )
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.set_xticks(pivoted[year_col].unique())

    fig.text(
        0.08,
        -0.02,
        "Source: BC Stats Annual Tourism Indicators. Note: Employment reflects direct tourism-attributed workforce (BC Tourism Satellite Account methodology).",
        fontsize=9,
        color="#4A5568",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "bc_tourism_annual_macro_trends.png"
    pdf_path = OUTPUT_DIR / "bc_tourism_annual_macro_trends.pdf"

    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.25)
    plt.savefig(pdf_path, bbox_inches="tight", pad_inches=0.25)
    plt.close()

    print(f"Macro trends chart saved:\n - {png_path}\n - {pdf_path}")


def plot_broader_economic_indicators(dfs: dict[str, pd.DataFrame]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), dpi=300)

    for ax in axes.flat:
        ax.margins(y=0.12)

    # Panel 1: Transportation Mobility
    if "transportation" in dfs:
        df_trans = dfs["transportation"]
        vancouver_air = df_trans[(df_trans["Location"] == "Vancouver") & (df_trans["Segment"] == "Total")]
        bc_ferries = df_trans[(df_trans["Location"] == "BC Ferries") & (df_trans["Segment"] == "Passengers")]

        axes[0, 0].plot(
            vancouver_air["Year"],
            vancouver_air["Value"] / 1000,
            marker="o",
            label="Vancouver Air Passengers",
            color="#1F77B4",
            linewidth=2,
        )
        axes[0, 0].plot(
            bc_ferries["Year"],
            bc_ferries["Value"] / 1000,
            marker="s",
            label="BC Ferries Passengers",
            color="#DD6B20",
            linewidth=2,
        )
        axes[0, 0].axvspan(2019.8, 2021.2, color="#718096", alpha=0.15)
        axes[0, 0].set_title("Transportation & Passenger Mobility", fontweight="bold")
        axes[0, 0].set_xlabel("Year")
        axes[0, 0].set_ylabel("Passengers (Millions)")
        axes[0, 0].legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)
        axes[0, 0].grid(True, linestyle=":", alpha=0.6)

    # Panel 2: Service Sector Employment Breakdown (Full NAICS Industry Totals)
    if "sector_indicators" in dfs:
        df_sec = dfs["sector_indicators"]
        emp_df = df_sec[df_sec["Domain"] == "Employment"]

        for sub_ind in emp_df["Sub_Indicator"].unique():
            subset = emp_df[emp_df["Sub_Indicator"] == sub_ind]
            axes[0, 1].plot(
                subset["Year"],
                subset["Value"] / 1000,
                marker="o",
                label=sub_ind,
                linewidth=2,
            )

        axes[0, 1].axvspan(2019.8, 2021.2, color="#718096", alpha=0.15)
        axes[0, 1].set_title("Service Sector Total Employment (NAICS Industry Wide)", fontweight="bold")
        axes[0, 1].set_xlabel("Year")
        axes[0, 1].set_ylabel("Employment (Thousands)")
        axes[0, 1].legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9, fontsize=8.5)
        axes[0, 1].grid(True, linestyle=":", alpha=0.6)

    # Panel 3: Food & Beverage Industry Receipts
    if "food_services" in dfs:
        df_food = dfs["food_services"]
        food_agg = df_food.groupby(["Year", "Category"])["Value"].sum().reset_index()
        food_pivot = food_agg.pivot(index="Year", columns="Category", values="Value")

        ax_food = axes[1, 0]
        lines_food = []

        if "Food Services" in food_pivot.columns:
            l1 = ax_food.plot(
                food_pivot.index,
                food_pivot["Food Services"] / 1_000_000,
                marker="^",
                color="#2CA02C",
                label="Food Services Receipts ($M)",
                linewidth=2,
            )
            lines_food.extend(l1)

        ax_food.set_ylabel("Food Services ($ Millions CAD)", color="#2CA02C", fontweight="bold")
        ax_food.tick_params(axis="y", labelcolor="#2CA02C")
        ax_food.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))

        if "Drinking Places" in food_pivot.columns:
            ax_drink = ax_food.twinx()
            ax_drink.margins(y=0.12)
            l2 = ax_drink.plot(
                food_pivot.index,
                food_pivot["Drinking Places"] / 1_000_000,
                marker="v",
                color="#D62728",
                label="Drinking Places Receipts ($M)",
                linewidth=2,
                linestyle="--",
            )
            ax_drink.set_ylabel("Drinking Places ($ Millions CAD)", color="#D62728", fontweight="bold", labelpad=12)
            ax_drink.tick_params(axis="y", labelcolor="#D62728")
            ax_drink.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
            lines_food.extend(l2)

        ax_food.axvspan(2019.8, 2021.2, color="#718096", alpha=0.15)
        ax_food.set_title("Food & Beverage Industry Receipts (Nominal)", fontweight="bold")
        ax_food.set_xlabel("Year")

        labs = [l.get_label() for l in lines_food]
        ax_food.legend(lines_food, labs, loc="center left", frameon=True, facecolor="white", framealpha=0.9)
        ax_food.grid(True, linestyle=":", alpha=0.6)

    # Panel 4: Consumer Price Index (Inflation)
    if "sector_indicators" in dfs:
        cpi_df = dfs["sector_indicators"][dfs["sector_indicators"]["Domain"] == "Consumer Price Index"]
        cpi_rest = cpi_df[cpi_df["Sub_Indicator"] == "Restaurant meals"]
        cpi_hotel = cpi_df[cpi_df["Sub_Indicator"] == "Traveller Accommodation"]

        axes[1, 1].plot(
            cpi_rest["Year"],
            cpi_rest["Value"],
            color="#8C564B",
            marker="d",
            label="CPI: Restaurant Meals",
            linewidth=2,
        )
        axes[1, 1].plot(
            cpi_hotel["Year"],
            cpi_hotel["Value"],
            color="#E377C2",
            marker="p",
            label="CPI: Traveller Accommodation",
            linewidth=2,
        )
        axes[1, 1].axvspan(2019.8, 2021.2, color="#718096", alpha=0.15)

        axes[1, 1].set_title("Hospitality Inflation (CPI Index, 2002 Baseline = 100)", fontweight="bold")
        axes[1, 1].set_xlabel("Year")
        axes[1, 1].set_ylabel("Consumer Price Index (2002=100)")
        axes[1, 1].legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9)
        axes[1, 1].grid(True, linestyle=":", alpha=0.6)

    fig.text(
        0.05,
        -0.01,
        "Source: Statistics Canada & BC Stats. Note: Employment panel shows total BC industry-wide employment (NAICS level), not direct tourism-attributed shares.",
        fontsize=9.5,
        color="#4A5568",
    )

    plt.tight_layout()

    png_path = OUTPUT_DIR / "broader_economic_indicators_clean.png"
    pdf_path = OUTPUT_DIR / "broader_economic_indicators_clean.pdf"

    plt.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.25)
    plt.savefig(pdf_path, bbox_inches="tight", pad_inches=0.25)
    plt.close()

    print(f"Broader economic dashboard saved:\n - {png_path}\n - {pdf_path}")


def generate_all_visualizations() -> None:
    print("=" * 65)
    print(" RENDERING TIME-SERIES & ECONOMIC INDICATOR CHARTS")
    print("=" * 65)

    dfs = load_all_datasets()

    if "annual_macro" in dfs:
        plot_annual_macro_trends(dfs["annual_macro"])

    plot_broader_economic_indicators(dfs)


if __name__ == "__main__":
    generate_all_visualizations()