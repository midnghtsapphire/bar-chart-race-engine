#!/usr/bin/env python3
"""
render-multi.py — Render bar chart races for all fetched datasets.

Reads data/<slug>/<slug>.csv + config.json for each race and produces
MP4 videos (1080x1920 vertical for social media).

Usage:
    python scripts/render-multi.py
"""

import json
import sys
from pathlib import Path

import bar_chart_race as bcr
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Vertical video for social media (1080x1920)
FIG_WIDTH = 10.8   # 1080px at 100 dpi
FIG_HEIGHT = 19.2  # 1920px at 100 dpi
DPI = 100
TOP_N = 10


def load_pivot(csv_path: Path, sort_order: str) -> pd.DataFrame:
    """Load CSV and pivot to wide format for bar_chart_race."""
    df = pd.read_csv(csv_path)
    pivot = df.pivot_table(
        index="year",
        columns="country",
        values="value",
        aggfunc="first",
    )
    pivot = pivot.sort_index()

    # Keep top countries by max value (or min for "asc" races like literacy)
    if sort_order == "asc":
        # For "lowest wins" races, keep countries with lowest minimums
        min_per_country = pivot.min()
        keep = min_per_country.nsmallest(TOP_N * 3).index
    else:
        max_per_country = pivot.max()
        keep = max_per_country.nlargest(TOP_N * 3).index

    pivot = pivot[keep].fillna(0)
    return pivot


def render_race(slug_dir: Path) -> None:
    """Render one bar chart race from its data directory."""
    config_path = slug_dir / "config.json"
    if not config_path.exists():
        return

    with open(config_path) as f:
        config = json.load(f)

    slug = config["slug"]
    title = config["title"]
    sort_order = config["sort"]
    csv_path = slug_dir / config["csv_file"]

    if not csv_path.exists():
        print(f"  SKIP {slug}: CSV not found")
        return

    print(f"\n{'='*60}")
    print(f"Rendering: {title}")
    print(f"{'='*60}")

    pivot = load_pivot(csv_path, sort_order)
    print(f"  Pivot: {pivot.shape[0]} years x {pivot.shape[1]} countries")

    output_path = slug_dir / f"{slug}.mp4"

    try:
        bcr.bar_chart_race(
            df=pivot,
            filename=str(output_path),
            n_bars=TOP_N,
            sort="desc",
            title=title,
            title_size=24,
            period_label=True,
            period_fmt="{x:.0f}",
            bar_label_size=12,
            tick_label_size=10,
            bar_size=0.8,
            period_length=1500,
            steps_per_period=30,
            interpolate_period=True,
            figsize=(FIG_WIDTH, FIG_HEIGHT),
            dpi=DPI,
            bar_kwargs={
                "alpha": 0.9,
                "ec": "white",
                "lw": 1.5,
            },
            filter_column_colors=True,
        )
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Done! {output_path} ({size_mb:.1f} MB)")
    except Exception as exc:
        print(f"  ERROR rendering {slug}: {exc}", file=sys.stderr)


def main() -> None:
    if not DATA_DIR.exists():
        print("ERROR: data/ directory not found. Run wdi-multi-fetch.py first.", file=sys.stderr)
        sys.exit(1)

    slug_dirs = sorted([d for d in DATA_DIR.iterdir() if d.is_dir() and (d / "config.json").exists()])

    if not slug_dirs:
        print("No race configs found. Run wdi-multi-fetch.py first.")
        sys.exit(1)

    print(f"Found {len(slug_dirs)} races to render")

    for slug_dir in slug_dirs:
        render_race(slug_dir)

    print(f"\n{'='*60}")
    print(f"All renders complete.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
