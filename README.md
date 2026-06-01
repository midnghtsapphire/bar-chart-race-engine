# Bar Chart Race: Electricity Access Gap

> Number of People Without Access to Electricity by Country (1990–2025)

A data pipeline that fetches World Bank indicators, calculates the electricity
access gap per country, and renders an animated bar chart race video for social media.

**WR:** RIS-001 (tracked in `midnghtsapphire/revvel-standards`)

## Quick Start

```bash
pip install bar_chart_race pandas requests matplotlib

# 1. Fetch World Bank data
python scripts/wdi-fetch.py

# 2. Render bar chart race
python scripts/render-race.py
```

## Output

| File | Description |
|------|-------------|
| `data/electricity_gap.csv` | Full dataset: country, year, population, access %, people without electricity |
| `data/anomaly-report.md` | Every excluded country-year with the specific missing indicator |
| `data/bar_chart_race.mp4` | Vertical 1080x1920 video for LinkedIn / TikTok / Reels |
| `data/bar_chart_race.gif` | Smaller GIF preview |

## Data Source

- **Electricity access:** World Bank WDI indicator `EG.ELC.ACCS.ZS`
- **Population:** World Bank WDI indicator `SP.POP.TOTL`
- **Formula:** `people_without = population * (100 - access_pct) / 100`
- **Range:** 1990 to latest available year

## Anti-Goals

Per RIS-001:
- Do NOT hide countries with missing data without an explicit footnote
- Every excluded country-year is documented in `data/anomaly-report.md`
- Missing data = excluded from animation + listed in anomaly report (not silently dropped)

## Requirements

- Python 3.10+
- ffmpeg (for MP4 rendering)
- ImageMagick (for GIF rendering, optional)

```
pip install bar_chart_race pandas requests matplotlib
```

## Project Structure

```
bar-chart-race-engine/
├── scripts/
│   ├── wdi-fetch.py         # World Bank data pipeline
│   └── render-race.py       # Bar chart race renderer
├── data/
│   ├── electricity_gap.csv  # Generated dataset
│   ├── anomaly-report.md    # Generated anomaly documentation
│   ├── bar_chart_race.mp4   # Generated video
│   └── bar_chart_race.gif   # Generated GIF preview
└── README.md
```

## Credit

- Data: [World Bank Open Data](https://data.worldbank.org/)
- Visualization: [bar_chart_race](https://github.com/dexplo/bar_chart_race)
- Inspiration: [world_of_infographics on LinkedIn](https://www.linkedin.com/posts/the-energy-shift_energyaccess-electrification-energytransition-activity-7467101100073213952-IzR7)
