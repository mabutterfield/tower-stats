import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

RUNLOG_FILE = "runlog.json"

SUFFIXES = [
    (10**18, 'Q'),  # Quintillion
    (10**15, 'q'),  # Quadrillion
    (10**12, 'T'),  # Trillion
    (10**3, 'K'),   # Thousand
]

def format_number(n):
    for factor, suffix in SUFFIXES:
        if n >= factor:
            return f"{n / factor:.1f}{suffix}"
    return f"{n:.0f}"

def print_ascii_table(headers, rows):
    col_widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    row_fmt = " | ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "-+-".join("-" * w for w in col_widths)

    print(row_fmt.format(*headers))
    print(sep)
    for row in rows:
        print(row_fmt.format(*row))

def load_filtered_runs(days=None, last=None):
    if not os.path.exists(RUNLOG_FILE):
        raise FileNotFoundError(f"Missing {RUNLOG_FILE}")

    with open(RUNLOG_FILE, "r") as f:
        all_runs = json.load(f)

    runs = sorted(all_runs, key=lambda r: r['epoch'])
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        runs = [r for r in runs if datetime.fromtimestamp(r['epoch']) >= cutoff]
    if last:
        runs = runs[-last:]
    return runs

def summarize_by_tier(runs):
    tiers = defaultdict(list)
    for r in runs:
        if r.get("rerolldice", 0) == 0:
            continue
        tiers[r["tier"]].append(r)

    rows = []
    for tier, entries in sorted(tiers.items()):
        cph = [r["coins_per_hour"] for r in entries]
        cellph = [r["cells_per_hour"] for r in entries]
        diceph = [r["rerolldice_per_hour"] for r in entries]
        rows.append([
            tier,
            format_number(min(cph)),
            format_number(max(cph)),
            format_number(sum(cph)/len(cph)),
            format_number(min(cellph)),
            format_number(max(cellph)),
            format_number(sum(cellph)/len(cellph)),
            format_number(min(diceph)),
            format_number(max(diceph)),
            format_number(sum(diceph)/len(diceph)),
            len(entries)
        ])
    print("\nSummary by Tier:")
    print_ascii_table(
        ["Tier", "Min CPH", "Max CPH", "Avg CPH", "Min Cells", "Max Cells", "Avg Cells",
         "Min Dice", "Max Dice", "Avg Dice", "Runs"],
        rows
    )

def summarize_by_day(runs):
    days = defaultdict(lambda: {"coins": 0, "cells": 0, "dice": 0})
    for r in runs:
        day = r["date"]
        days[day]["coins"] += r["coins"]
        days[day]["cells"] += r["cells"]
        days[day]["dice"] += r.get("rerolldice", 0)

    rows = []
    for date in sorted(days):
        row = days[date]
        rows.append([
            date,
            format_number(row["coins"]),
            format_number(row["cells"]),
            format_number(row["dice"])
        ])
    print("\nDaily Totals:")
    print_ascii_table(["Date", "Coins", "Cells", "Dice"], rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze runlog.json")
    parser.add_argument("--days", type=int, help="Show runs from the past X days")
    parser.add_argument("--last", type=int, help="Show the last X runs")
    parser.add_argument("--summary", action="store_true", help="Summarize by tier")
    parser.add_argument("--daily", action="store_true", help="Summarize by day")
    args = parser.parse_args()

    data = load_filtered_runs(days=args.days, last=args.last)

    if args.summary:
        summarize_by_tier(data)

    if args.daily:
        summarize_by_day(data)

    if not args.summary and not args.daily:
        print("No output mode selected. Use --summary or --daily.")
