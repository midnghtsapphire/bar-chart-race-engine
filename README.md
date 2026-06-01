# Bar Chart Race Engine

> Animated bar chart race videos from public data — vertical 1080x1920 for LinkedIn / TikTok / Reels

A data pipeline that fetches World Bank indicators (and custom datasets), generates
anomaly reports, and renders animated bar chart race MP4 videos for social media.

**WR:** RIS-001 (tracked in `midnghtsapphire/revvel-standards`)

## Available Races

| Race | Data Source | Script |
|------|------------|--------|
| People Without Electricity | World Bank `EG.ELC.ACCS.ZS` + `SP.POP.TOTL` | `wdi-fetch.py` → `render-race.py` |
| Adult Literacy Rates | World Bank `SE.ADT.LITR.ZS` | `wdi-multi-fetch.py` → `render-multi.py` |
| Life Expectancy | World Bank `SP.DYN.LE00.IN` | `wdi-multi-fetch.py` → `render-multi.py` |
| Internet Access | World Bank `IT.NET.USER.ZS` | `wdi-multi-fetch.py` → `render-multi.py` |
| CO2 Emissions | World Bank `EN.GHG.CO2.MT.CE.AR5` | `wdi-multi-fetch.py` → `render-multi.py` |
| GDP Per Capita | World Bank `NY.GDP.PCAP.CD` | `wdi-multi-fetch.py` → `render-multi.py` |
| Renewable Energy | World Bank `EG.FEC.RNEW.ZS` | `wdi-multi-fetch.py` → `render-multi.py` |
| Non-HE Washers (US + World) | AHAM, DOE, IEA (assembled estimates) | `washer-fetch.py` → `render-washers.py` |

## Quick Start

```bash
pip install -r requirements.txt

# Electricity access gap (original race)
python scripts/wdi-fetch.py        # fetch World Bank data → data/electricity_gap.csv
python scripts/render-race.py      # render MP4 → data/bar_chart_race.mp4

# All 6 World Bank races at once
python scripts/wdi-multi-fetch.py  # fetch all indicators → data/<slug>/<slug>.csv
python scripts/render-multi.py     # render all MP4s → data/<slug>/<slug>.mp4

# Non-HE washing machines (US vs World)
python scripts/washer-fetch.py     # assemble estimates → data/non-he-washers/
python scripts/render-washers.py   # render comparison animation
```

## Generated Output (not tracked in git)

All generated files go into `data/` and are gitignored. Re-generate with the scripts above.

| Pattern | Description |
|---------|-------------|
| `data/*.csv` | Raw datasets |
| `data/anomaly-report.md` | Excluded country-years with specific missing indicators |
| `data/*.mp4` | Vertical 1080x1920 videos |
| `data/<slug>/<slug>.csv` | Per-race datasets |
| `data/<slug>/anomaly-report.md` | Per-race anomaly documentation |
| `data/<slug>/<slug>.mp4` | Per-race videos |
| `data/<slug>/config.json` | Per-race render configuration |

## Anti-Goals

Per RIS-001:
- Do NOT hide countries with missing data without an explicit footnote
- Every excluded country-year is documented in the generated `anomaly-report.md`
- Missing data = excluded from animation + listed in anomaly report (not silently dropped)

## Requirements

- Python 3.10+
- ffmpeg (for MP4 rendering)

```
pip install -r requirements.txt
```

## Project Structure

```
bar-chart-race-engine/
├── scripts/
│   ├── wdi-fetch.py           # Electricity access gap pipeline
│   ├── render-race.py         # Single-race renderer
│   ├── wdi-multi-fetch.py     # Multi-indicator World Bank fetcher
│   ├── render-multi.py        # Multi-race batch renderer
│   ├── washer-fetch.py        # Non-HE washer data assembler
│   └── render-washers.py      # Washer comparison animation
├── data/                      # Generated (gitignored) — re-run scripts to produce
│   ├── electricity_gap.csv
│   ├── bar_chart_race.mp4
│   ├── anomaly-report.md
│   ├── literacy-rates/
│   ├── life-expectancy/
│   ├── internet-access/
│   ├── co2-emissions/
│   ├── gdp-per-capita/
│   ├── renewable-energy/
│   └── non-he-washers/
├── requirements.txt
└── README.md
```

## Data Sources

- [World Bank Open Data](https://data.worldbank.org/) — 6 WDI indicators
- AHAM, DOE, Energy Star, IEA — non-HE washer estimates (see `washer-fetch.py` for methodology)

## Credit

- Data: [World Bank Open Data](https://data.worldbank.org/)
- Visualization: [bar_chart_race](https://github.com/dexplo/bar_chart_race)
- Inspiration: [world_of_infographics on LinkedIn](https://www.linkedin.com/posts/the-energy-shift_energyaccess-electrification-energytransition-activity-7467101100073213952-IzR7)
