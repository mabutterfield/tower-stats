import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze runlog.json")
    parser.add_argument("--summary", action="store_true", help="Show per-hour summary by tier (last 7 days by default)")
    parser.add_argument("--daily", action="store_true", help="Show total daily resources")
    parser.add_argument("--days", type=int, default=7, help="Limit analysis to the past X days (default: 7)")
    parser.add_argument("--last", type=int, help="Limit analysis to the last X runs")
    return parser.parse_args()

def load_json():
    with open("runlog.json", "r") as f:
        return json.load(f)

def format_number(n):
    if n >= 1e18:
        return f"{n / 1e18:.1f}Q"
    elif n >= 1e15:
        return f"{n / 1e15:.1f}q"
    elif n >= 1e12:
        return f"{n / 1e12:.1f}T"
    elif n >= 1e9:
        return f"{n / 1e9:.1f}B"
    elif n >= 1e6:
        return f"{n / 1e6:.1f}M"
    elif n >= 1e3:
        return f"{n / 1e3:.1f}K"
    else:
        return str(n)

def print_ascii_table(headers, rows):
    col_widths = [max(len(str(val)) for val in col) for col in zip(headers, *rows)]
    sep = "+".join("-" * (w + 2) for w in col_widths)

    # Optional fancy merged center header
    title = headers[0] if isinstance(headers[0], str) else ""
    table_width = sum(col_widths) + len(col_widths) * 3 - 1
    print("-" * table_width)
    print(f"{title:^{table_width}}")
    print("-" * table_width)

    # Header
    header_row = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    print(header_row)
    print(sep.replace("-", "-"))

    for row in rows:
        print(" | ".join(f"{str(c):<{w}}" for c, w in zip(row, col_widths)))

def summarize_by_tier(runs, days=7, last=None):
    recent = []
    cutoff = datetime.now() - timedelta(days=days)

    for run in runs:
        run_date = datetime.strptime(run["date"], "%Y-%m-%d")
        if run.get("rerolldice", 0) > 0 and run_date >= cutoff:
            recent.append(run)

    if last:
        recent = recent[-last:]

    by_tier = defaultdict(list)
    for run in recent:
        by_tier[run["tier"]].append(run)

    rows = []
    for tier in sorted(by_tier.keys()):
        tier_runs = by_tier[tier]
        cph = [r["coins_per_hour"] for r in tier_runs]
        cellph = [r["cells_per_hour"] for r in tier_runs]
        diceph = [r["rerolldice_per_hour"] for r in tier_runs]

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
            len(tier_runs),
        ])

    headers = [
        "Tier", "MinCoin", "MaxCoin", "AvgCoin",
        "MinCell", "MaxCell", "AvgCell",
        "MinDice", "MaxDice", "AvgDice", "Runs"
    ]

    print_ascii_table(headers, rows)

def summarize_by_day(runs, days=7):
    cutoff = datetime.now() - timedelta(days=days)
    daysummary = defaultdict(lambda: {"coins": 0, "cells": 0, "dice": 0, "tiers": []})

    for run in runs:
        run_date = datetime.strptime(run["date"], "%Y-%m-%d")
        if run_date >= cutoff:
            date_str = run["date"]
            daysummary[date_str]["coins"] += run["coins"]
            daysummary[date_str]["cells"] += run["cells"]
            daysummary[date_str]["dice"] += run.get("rerolldice", 0)
            daysummary[date_str]["tiers"].append(str(run["tier"]))

    rows = []
    for date in sorted(daysummary):
        row = daysummary[date]
        rows.append([
            date,
            format_number(row["coins"]),
            format_number(row["cells"]),
            format_number(row["dice"]),
            " ".join(row["tiers"])
        ])

    headers = ["Date", "Coins", "Cells", "Dice", "Tiers"]
    print_ascii_table(headers, rows)

def main():
    args = parse_args()
    runs = load_json()

    if not args.summary and not args.daily:
        print("No output mode selected. Use --summary or --daily.")
        print("Optional: --days N (default 7), --last N")
        return

    if args.summary:
        print()
        print_ascii_table(["Per-Hour Summary for Last Runs Where Dice > 0:"], [])
        summarize_by_tier(runs, args.days, args.last)

    if args.daily:
        print()
        print_ascii_table(["Daily Totals (Last Runs):"], [])
        summarize_by_day(runs, args.days)

if __name__ == "__main__":
    main()
