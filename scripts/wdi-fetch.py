#!/usr/bin/env python3
"""
wdi-fetch.py — World Bank WDI Data Pipeline

Fetches electricity access (%) and population data from the World Bank API,
calculates people without electricity by country and year, and exports CSV.

Indicators:
  - EG.ELC.ACCS.ZS  (Access to electricity, % of population)
  - SP.POP.TOTL     (Population, total)

Formula:
  people_without_electricity = population * (100 - electricity_access_pct) / 100

Output: data/electricity_gap.csv
"""

import csv
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "https://api.worldbank.org/v2"
INDICATORS = {
    "EG.ELC.ACCS.ZS": "electricity_access_pct",
    "SP.POP.TOTL": "population",
}
START_YEAR = 1990
END_YEAR = 2025
PER_PAGE = 20000

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def fetch_indicator(indicator: str) -> list[dict]:
    """Fetch all country-year data for a single WDI indicator."""
    url = (
        f"{BASE_URL}/country/all/indicator/{indicator}"
        f"?date={START_YEAR}:{END_YEAR}"
        f"&format=json&per_page={PER_PAGE}"
    )
    print(f"Fetching {indicator} ...")
    try:
        with urlopen(url, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError) as exc:
        print(f"ERROR fetching {indicator}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(payload, list) or len(payload) < 2:
        print(f"ERROR: unexpected API response for {indicator}", file=sys.stderr)
        sys.exit(1)

    meta, records = payload[0], payload[1]
    total = int(meta.get("total", 0))
    print(f"  -> {total} records, fetched {len(records)}")
    return records


def is_country(record: dict) -> bool:
    """Filter out aggregates (regions, income groups, world)."""
    country_info = record.get("country", {})
    country_id = record.get("countryiso3code", "")
    # World Bank aggregates have region id == "" or specific aggregate codes
    # Countries have 3-letter ISO codes and are not in the aggregate list
    if not country_id or len(country_id) != 3:
        return False
    # Filter out known aggregate ids
    aggregates = {
        "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS", "EMU",
        "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX",
        "INX", "LAC", "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA",
        "MIC", "MNA", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS",
        "SSA", "SSF", "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS",
        "UMC", "WLD",
    }
    return country_id not in aggregates


def build_dataset() -> tuple[list[dict], list[dict]]:
    """
    Merge indicators into per-country-year rows.
    Returns (rows, anomalies) where anomalies are missing/interpolated data points.
    """
    # Fetch raw data
    raw: dict[str, dict[str, dict]] = {}  # {indicator_col: {(iso3, year): value}}
    for indicator, col_name in INDICATORS.items():
        records = fetch_indicator(indicator)
        for rec in records:
            if not is_country(rec):
                continue
            iso3 = rec["countryiso3code"]
            year = rec["date"]
            value = rec["value"]
            key = (iso3, year)
            if key not in raw:
                raw[key] = {}
            raw[key][col_name] = value
            raw[key]["country_name"] = rec["country"]["value"]
            raw[key]["country_iso3"] = iso3
            raw[key]["year"] = int(year)

    # Build merged rows
    rows = []
    anomalies = []
    for key, data in sorted(raw.items()):
        iso3, year = key
        country_name = data.get("country_name", iso3)
        yr = data.get("year", int(year))
        elec = data.get("electricity_access_pct")
        pop = data.get("population")

        if elec is None or pop is None:
            anomalies.append({
                "country": country_name,
                "iso3": iso3,
                "year": yr,
                "issue": "missing_data",
                "detail": (
                    f"electricity_access={'present' if elec else 'MISSING'}, "
                    f"population={'present' if pop else 'MISSING'}"
                ),
            })
            continue

        people_without = int(pop * (100 - elec) / 100)
        rows.append({
            "country": country_name,
            "iso3": iso3,
            "year": yr,
            "population": int(pop),
            "electricity_access_pct": round(elec, 2),
            "people_without_electricity": people_without,
        })

    return rows, anomalies


def write_csv(rows: list[dict], path: Path) -> None:
    """Write dataset to CSV."""
    if not rows:
        print("WARNING: no rows to write", file=sys.stderr)
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def write_anomaly_report(anomalies: list[dict], path: Path) -> None:
    """Write anomaly report as markdown."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Data Anomaly Report\n\n")
        f.write("> Auto-generated by `wdi-fetch.py`\n\n")
        f.write("## Source\n\n")
        f.write("- **Electricity access:** World Bank WDI indicator `EG.ELC.ACCS.ZS`\n")
        f.write("- **Population:** World Bank WDI indicator `SP.POP.TOTL`\n")
        f.write(f"- **Date range:** {START_YEAR}–{END_YEAR}\n")
        f.write(f"- **Formula:** `people_without = population * (100 - access_pct) / 100`\n\n")

        if not anomalies:
            f.write("## Result\n\nNo anomalies detected. All country-year pairs have both indicators.\n")
            return

        f.write(f"## Anomalies Found: {len(anomalies)}\n\n")
        f.write("Countries with missing electricity access or population data are listed below.\n")
        f.write("These countries are **excluded** from the bar chart race to avoid incorrect rankings.\n")
        f.write("They are NOT hidden — they are explicitly documented here.\n\n")

        f.write("| Country | ISO3 | Year | Issue | Detail |\n")
        f.write("|---------|------|------|-------|--------|\n")
        for a in sorted(anomalies, key=lambda x: (x["country"], x["year"])):
            f.write(f"| {a['country']} | {a['iso3']} | {a['year']} | {a['issue']} | {a['detail']} |\n")

        f.write("\n## Anti-Goal Compliance\n\n")
        f.write("Per RIS-001: **Do not hide countries due to missing data without noting it.**\n")
        f.write("Every excluded country-year is listed above with the specific missing indicator.\n")

    print(f"Wrote anomaly report ({len(anomalies)} entries) to {path}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rows, anomalies = build_dataset()

    csv_path = DATA_DIR / "electricity_gap.csv"
    anomaly_path = DATA_DIR / "anomaly-report.md"

    write_csv(rows, csv_path)
    write_anomaly_report(anomalies, anomaly_path)

    # Summary stats
    if rows:
        countries = {r["iso3"] for r in rows}
        years = {r["year"] for r in rows}
        print(f"\nSummary: {len(countries)} countries, {len(years)} years, {len(rows)} data points")
        print(f"Anomalies: {len(anomalies)} country-year pairs with missing data")


if __name__ == "__main__":
    main()
