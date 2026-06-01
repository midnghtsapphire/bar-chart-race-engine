#!/usr/bin/env python3
"""
wdi-multi-fetch.py — Multi-indicator World Bank WDI Data Pipeline

Fetches multiple WDI indicators, pivots each to wide format, and exports
CSV files ready for bar_chart_race rendering.

Usage:
    python scripts/wdi-multi-fetch.py
"""

import csv
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "https://api.worldbank.org/v2"
START_YEAR = 1990
END_YEAR = 2025
PER_PAGE = 20000
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Each race config: slug, indicator(s), title, transform
RACES = [
    {
        "slug": "literacy-rates",
        "title": "Adult Literacy Rate by Country",
        "indicator": "SE.ADT.LITR.ZS",
        "unit": "% of adults (15+)",
        "sort": "asc",  # lower = worse, show lowest
        "description": "Adult literacy rate, population 15+ years, both sexes (%)",
    },
    {
        "slug": "life-expectancy",
        "title": "Life Expectancy at Birth by Country",
        "indicator": "SP.DYN.LE00.IN",
        "unit": "years",
        "sort": "desc",  # higher = better, show highest
        "description": "Life expectancy at birth, total (years)",
    },
    {
        "slug": "internet-access",
        "title": "Individuals Using the Internet by Country",
        "indicator": "IT.NET.USER.ZS",
        "unit": "% of population",
        "sort": "desc",
        "description": "Individuals using the Internet (% of population)",
    },
    {
        "slug": "co2-emissions",
        "title": "CO2 Emissions by Country",
        "indicator": "EN.GHG.CO2.MT.CE.AR5",
        "unit": "million metric tons CO2 equivalent",
        "sort": "desc",  # highest emitters
        "description": "CO2 emissions (Mt CO2e, AR5 GWP)",
    },
    {
        "slug": "gdp-per-capita",
        "title": "GDP Per Capita by Country",
        "indicator": "NY.GDP.PCAP.CD",
        "unit": "current US$",
        "sort": "desc",
        "description": "GDP per capita (current US$)",
    },
    {
        "slug": "renewable-energy",
        "title": "Renewable Energy Consumption by Country",
        "indicator": "EG.FEC.RNEW.ZS",
        "unit": "% of total final energy consumption",
        "sort": "desc",
        "description": "Renewable energy consumption (% of total final energy consumption)",
    },
]

# Known World Bank aggregate codes to exclude
AGGREGATES = {
    "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS", "EMU",
    "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX",
    "INX", "LAC", "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA",
    "MIC", "MNA", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS",
    "SSA", "SSF", "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS",
    "UMC", "WLD",
}


def fetch_indicator(indicator: str) -> list[dict]:
    """Fetch all country-year data for a WDI indicator."""
    url = (
        f"{BASE_URL}/country/all/indicator/{indicator}"
        f"?date={START_YEAR}:{END_YEAR}"
        f"&format=json&per_page={PER_PAGE}"
    )
    print(f"  Fetching {indicator} ...")
    try:
        with urlopen(url, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError) as exc:
        print(f"  ERROR fetching {indicator}: {exc}", file=sys.stderr)
        return []

    if not isinstance(payload, list) or len(payload) < 2:
        print(f"  ERROR: unexpected API response for {indicator}", file=sys.stderr)
        return []

    meta, records = payload[0], payload[1]
    total = int(meta.get("total", 0))
    print(f"    {total} records, fetched {len(records)}")
    return records


def process_race(race: dict) -> None:
    """Fetch data and produce CSV + anomaly report for one race."""
    slug = race["slug"]
    indicator = race["indicator"]
    title = race["title"]
    unit = race["unit"]

    print(f"\n{'='*60}")
    print(f"Processing: {title}")
    print(f"{'='*60}")

    records = fetch_indicator(indicator)
    if not records:
        print(f"  SKIPPED: no data for {indicator}")
        return

    rows = []
    anomalies = []
    for rec in records:
        iso3 = rec.get("countryiso3code", "")
        if not iso3 or len(iso3) != 3 or iso3 in AGGREGATES:
            continue
        country_name = rec["country"]["value"]
        year = int(rec["date"])
        value = rec["value"]

        if value is None:
            anomalies.append({
                "country": country_name,
                "iso3": iso3,
                "year": year,
                "issue": "missing_data",
                "detail": f"{indicator} value is NULL",
            })
            continue

        rows.append({
            "country": country_name,
            "iso3": iso3,
            "year": year,
            "value": value,
        })

    # Write CSV
    slug_dir = DATA_DIR / slug
    slug_dir.mkdir(parents=True, exist_ok=True)

    csv_path = slug_dir / f"{slug}.csv"
    if rows:
        fieldnames = ["country", "iso3", "year", "value"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda r: (r["country"], r["year"])))
        print(f"  Wrote {len(rows)} rows to {csv_path}")
    else:
        print(f"  WARNING: no data rows for {slug}")

    # Write anomaly report
    anomaly_path = slug_dir / "anomaly-report.md"
    with open(anomaly_path, "w", encoding="utf-8") as f:
        f.write(f"# Data Anomaly Report: {title}\n\n")
        f.write(f"> Auto-generated by `wdi-multi-fetch.py`\n\n")
        f.write(f"## Source\n\n")
        f.write(f"- **Indicator:** `{indicator}` — {race['description']}\n")
        f.write(f"- **Unit:** {unit}\n")
        f.write(f"- **Date range:** {START_YEAR}–{END_YEAR}\n\n")

        if not anomalies:
            f.write("## Result\n\nNo anomalies detected.\n")
        else:
            f.write(f"## Anomalies Found: {len(anomalies)}\n\n")
            f.write("| Country | ISO3 | Year | Issue | Detail |\n")
            f.write("|---------|------|------|-------|--------|\n")
            for a in sorted(anomalies, key=lambda x: (x["country"], x["year"])):
                f.write(f"| {a['country']} | {a['iso3']} | {a['year']} | {a['issue']} | {a['detail']} |\n")
            f.write(f"\nEvery excluded country-year is listed above.\n")

    print(f"  Wrote anomaly report ({len(anomalies)} entries) to {anomaly_path}")

    # Write race config for the renderer
    config_path = slug_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({
            "slug": slug,
            "title": title,
            "indicator": indicator,
            "unit": unit,
            "sort": race["sort"],
            "description": race["description"],
            "csv_file": f"{slug}.csv",
            "rows": len(rows),
            "anomalies": len(anomalies),
        }, f, indent=2)

    countries = {r["iso3"] for r in rows}
    years = {r["year"] for r in rows}
    print(f"  Summary: {len(countries)} countries, {len(years)} years, {len(rows)} data points")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for race in RACES:
        process_race(race)

    print(f"\n{'='*60}")
    print(f"All {len(RACES)} races fetched. Run render-multi.py next.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
