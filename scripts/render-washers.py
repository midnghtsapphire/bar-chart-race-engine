#!/usr/bin/env python3
"""
render-washers.py — Render non-HE washer comparison chart as MP4.

Since this is a 2-region comparison (US vs World) rather than a multi-country
race, we render it as a grouped bar chart animation showing the decline of
non-HE washers over time.

Output: data/non-he-washers/non-he-washers.mp4
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "non-he-washers"
CSV_PATH = DATA_DIR / "non-he-washers.csv"
OUTPUT_PATH = DATA_DIR / "non-he-washers.mp4"

FIG_WIDTH = 10.8
FIG_HEIGHT = 19.2
DPI = 100


def main() -> None:
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run washer-fetch.py first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    us = df[df["region"] == "United States"].sort_values("year").reset_index(drop=True)
    world = df[df["region"] == "World"].sort_values("year").reset_index(drop=True)

    # Get all unique years across both
    all_years = sorted(set(us["year"].tolist() + world["year"].tolist()))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        "Non-HE Washing Machines\nInstalled Base Over Time",
        fontsize=28,
        fontweight="bold",
        y=0.96,
    )

    def animate(frame_idx):
        ax1.clear()
        ax2.clear()

        current_year = all_years[frame_idx]

        # US chart
        us_up_to = us[us["year"] <= current_year]
        if not us_up_to.empty:
            colors_us = ["#e74c3c" if y == current_year else "#f5b7b1" for y in us_up_to["year"]]
            ax1.barh(
                us_up_to["year"].astype(str),
                us_up_to["non_he_millions"],
                color=colors_us,
                edgecolor="white",
                linewidth=1,
            )
            for idx, row in us_up_to.iterrows():
                ax1.text(
                    row["non_he_millions"] + 0.5,
                    str(row["year"]),
                    f'{row["non_he_millions"]:.0f}M ({100 - row["he_pct"]:.0f}%)',
                    va="center",
                    fontsize=10,
                    fontweight="bold" if row["year"] == current_year else "normal",
                )

        ax1.set_title(
            f"United States — {current_year}",
            fontsize=22,
            fontweight="bold",
            pad=15,
        )
        ax1.set_xlabel("Non-HE Washers (millions)", fontsize=14)
        ax1.set_xlim(0, 110)
        ax1.invert_yaxis()

        # World chart
        world_up_to = world[world["year"] <= current_year]
        if not world_up_to.empty:
            colors_world = ["#2980b9" if y == current_year else "#aed6f1" for y in world_up_to["year"]]
            ax2.barh(
                world_up_to["year"].astype(str),
                world_up_to["non_he_millions"],
                color=colors_world,
                edgecolor="white",
                linewidth=1,
            )
            for idx, row in world_up_to.iterrows():
                ax2.text(
                    row["non_he_millions"] + 5,
                    str(row["year"]),
                    f'{row["non_he_millions"]:.0f}M ({100 - row["he_pct"]:.0f}%)',
                    va="center",
                    fontsize=10,
                    fontweight="bold" if row["year"] == current_year else "normal",
                )

        ax2.set_title(
            f"World — {current_year}",
            fontsize=22,
            fontweight="bold",
            pad=15,
        )
        ax2.set_xlabel("Non-HE Washers (millions)", fontsize=14)
        ax2.set_xlim(0, 750)
        ax2.invert_yaxis()

        fig.text(
            0.5, 0.02,
            "Source: AHAM, DOE, Energy Star, IEA | Assembled estimates",
            ha="center", fontsize=10, color="#888888",
        )

        plt.tight_layout(rect=[0, 0.04, 1, 0.93])

    print(f"Rendering washer animation ({len(all_years)} frames) ...")
    anim = animation.FuncAnimation(
        fig, animate, frames=len(all_years), interval=1500, repeat=False,
    )
    anim.save(str(OUTPUT_PATH), writer="ffmpeg", dpi=DPI)
    plt.close()

    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Done! {OUTPUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
