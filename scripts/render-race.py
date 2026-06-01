#!/usr/bin/env python3
"""
render-race.py — Bar Chart Race Animation

Reads data/electricity_gap.csv and produces a bar chart race video showing
the top 10 countries by "people without electricity" from 1990 to latest year.

Output: data/bar_chart_race.mp4 (vertical 1080x1920 for LinkedIn/TikTok/Reels)

Requires: bar_chart_race, pandas, matplotlib
"""

import sys
from pathlib import Path

import bar_chart_race as bcr
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "electricity_gap.csv"
OUTPUT_PATH = DATA_DIR / "bar_chart_race.mp4"
OUTPUT_GIF = DATA_DIR / "bar_chart_race.gif"

# Top N countries to show per frame
TOP_N = 10

# Vertical video for social media (1080x1920)
FIG_WIDTH_INCHES = 10.8  # 1080px at 100 dpi
FIG_HEIGHT_INCHES = 19.2  # 1920px at 100 dpi
DPI = 100


def load_and_pivot(csv_path: Path) -> pd.DataFrame:
    """
    Load the electricity gap CSV and pivot to wide format:
    index=year, columns=country, values=people_without_electricity.
    Keep only the top countries by max value across all years.
    """
    df = pd.read_csv(csv_path)

    # Pivot: rows=year, columns=country, values=people_without_electricity
    pivot = df.pivot_table(
        index="year",
        columns="country",
        values="people_without_electricity",
        aggfunc="first",
    )
    pivot = pivot.sort_index()

    # Keep only countries that appear in the top N at some point
    max_per_country = pivot.max()
    top_countries = max_per_country.nlargest(TOP_N * 3).index  # keep 3x for variety
    pivot = pivot[top_countries]

    # Fill missing years with 0 (country may not have data for all years)
    pivot = pivot.fillna(0).astype(int)

    return pivot


def render_mp4(pivot: pd.DataFrame, output_path: Path) -> None:
    """Render bar chart race as MP4 video."""
    print(f"Rendering bar chart race to {output_path} ...")
    print(f"  Years: {pivot.index.min()} to {pivot.index.max()}")
    print(f"  Countries tracked: {len(pivot.columns)}")
    print(f"  Resolution: {int(FIG_WIDTH_INCHES * DPI)}x{int(FIG_HEIGHT_INCHES * DPI)}")

    bcr.bar_chart_race(
        df=pivot,
        filename=str(output_path),
        n_bars=TOP_N,
        sort="desc",
        title="People Without Electricity by Country",
        title_size=28,
        period_label=True,
        period_fmt="{x:.0f}",
        bar_label_size=14,
        tick_label_size=12,
        bar_size=0.8,
        period_length=1500,
        steps_per_period=30,
        interpolate_period=True,
        figsize=(FIG_WIDTH_INCHES, FIG_HEIGHT_INCHES),
        dpi=DPI,
        bar_kwargs={
            "alpha": 0.9,
            "ec": "white",
            "lw": 1.5,
        },
        filter_column_colors=True,
    )
    print(f"Done! Output: {output_path}")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  File size: {size_mb:.1f} MB")


def render_gif(pivot: pd.DataFrame, output_path: Path) -> None:
    """Render bar chart race as GIF (smaller, preview-friendly)."""
    print(f"Rendering GIF preview to {output_path} ...")
    bcr.bar_chart_race(
        df=pivot,
        filename=str(output_path),
        n_bars=TOP_N,
        sort="desc",
        title="People Without Electricity by Country",
        title_size=20,
        period_label=True,
        period_fmt="{x:.0f}",
        bar_label_size=10,
        tick_label_size=9,
        bar_size=0.8,
        period_length=800,
        steps_per_period=10,
        interpolate_period=True,
        figsize=(8, 12),
        dpi=72,
        bar_kwargs={
            "alpha": 0.9,
            "ec": "white",
            "lw": 1,
        },
        filter_column_colors=True,
    )
    print(f"Done! GIF preview: {output_path}")


def main() -> None:
    if not CSV_PATH.exists():
        print(
            f"ERROR: {CSV_PATH} not found. Run wdi-fetch.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    pivot = load_and_pivot(CSV_PATH)
    print(f"\nPivot table: {pivot.shape[0]} years x {pivot.shape[1]} countries\n")

    # Render MP4 (primary deliverable)
    try:
        render_mp4(pivot, OUTPUT_PATH)
    except Exception as exc:
        print(f"MP4 render failed: {exc}", file=sys.stderr)
        print("Falling back to GIF only...", file=sys.stderr)

    # Render GIF (preview)
    try:
        render_gif(pivot, OUTPUT_GIF)
    except Exception as exc:
        print(f"GIF render failed: {exc}", file=sys.stderr)

    # Print source footer for the video overlay
    print("\n--- Source Footer ---")
    print("Source: World Bank WDI | Calculation: population x electricity access gap")
    print("Indicators: EG.ELC.ACCS.ZS, SP.POP.TOTL")
    print("Anti-goal: No country hidden without footnote (see data/anomaly-report.md)")


if __name__ == "__main__":
    main()
