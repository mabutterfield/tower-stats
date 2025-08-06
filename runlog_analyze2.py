import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

### Utility Functions ###

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze runlog.json")
    parser.add_argument("--summary", action="store_true", help="Show summary by tier")
    parser.add_argument("--daily", action="store_true", help="Show daily totals")
    parser.add_argument("--days", type=int, default=7, help="How many days back to include")
    return parser.parse_args()

def format_number(value):
    if value >= 1_000_000_000_000_000_000:
        return f"{value / 1_000_000_000_000_000:.1f}Q"
    elif value >= 1_000_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}q"
    elif value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}T"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(round(value))

def print_ascii_table(headers, rows):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = " | ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "-+-".join("-" * w for w in col_widths)

    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*row))


def load_json():
    with open("runlog.json") as f:
        return json.load(f)


### Summary by Tier ###

def summarize_by_tier(runs, days):
    cutoff = datetime.now() - timedelta(days=days)
    tier_data = defaultdict(list)

    for r in runs:
        run_date = datetime.strptime(r["date"], "%Y-%m-%d")
        if run_date >= cutoff and r.get("rerolldice", 0) > 0:
            tier_data[r["tier"]].append(r)

    rows = []
    for tier in sorted(tier_data):
        entries = tier_data[tier]
        cph = [e["coins_per_hour"] for e in entries]
        cellph = [e["cells_per_hour"] for e in entries]
        diceph = [e.get("rerolldice_per_hour", 0) for e in entries]

        rows.append([
            tier,
            format_number(min(cph)),
            format_number(max(cph)),
            format_number(sum(cph) / len(cph)),
            format_number(min(cellph)),
            format_number(max(cellph)),
            format_number(sum(cellph) / len(cellph)),
            format_number(min(diceph)),
            format_number(max(diceph)),
            format_number(sum(diceph) / len(diceph)),
            len(entries)
        ])

    print(f"\nPer-Hour Summary for Last {days} Days Where Dice > 0:")
    print_ascii_table([
        "Tier", "MinCoin", "MaxCoin", "AvgCoin",
        "MinCell", "MaxCell", "AvgCell",
        "MinDice", "MaxDice", "AvgDice", "Runs"
    ], rows)


### Daily Totals ###

def summarize_by_day(runs, days):
    cutoff = datetime.now() - timedelta(days=days)
    days_summary = defaultdict(lambda: {"coins": 0, "cells": 0, "dice": 0, "tiers": []})

    for r in runs:
        run_date = datetime.strptime(r["date"], "%Y-%m-%d")
        if run_date >= cutoff:
            d = r["date"]
            days_summary[d]["coins"] += r["coins"]
            days_summary[d]["cells"] += r["cells"]
            days_summary[d]["dice"] += r.get("rerolldice", 0)
            days_summary[d]["tiers"].append(str(r["tier"]))

    rows = []
    for d in sorted(days_summary):
        row = days_summary[d]
        rows.append([
            d,
            format_number(row["coins"]),
            format_number(row["cells"]),
            format_number(row["dice"]),
            " ".join(row["tiers"])
        ])

    print(f"\nDaily Totals (Last {days} Days):")
    print_ascii_table(["Date", "Coins", "Cells", "Dice", "Tiers"], rows)


### Main ###

def main():
    args = parse_args()
    runs = load_json()

    if args.summary:
        summarize_by_tier(runs, args.days)

    if args.daily:
        summarize_by_day(runs, args.days)

if __name__ == "__main__":
    main()
