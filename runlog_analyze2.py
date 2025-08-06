import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze runlog.json")
    parser.add_argument("--summary", action="store_true", help="Show per-hour summary by tier (last 7 days by default)")
    parser.add_argument("--daily", action="store_true", help="Show total daily resources")
    parser.add_argument("--days", type=int, default=7, help="Limit analysis to the past X days (default: 7)")
    parser.add_argument("--last", type=int, help="Limit analysis to the last X runs")
    parser.add_argument("--coin", action="store_true", help="Include coin stats")
    parser.add_argument("--cell", action="store_true", help="Include cell stats")
    parser.add_argument("--dice", action="store_true", help="Include dice stats")
    parser.add_argument("--time", action="store_true", help="Include time stats (formatted as XhYYm)")
    parser.add_argument("--wave", action="store_true", help="Include wave stats")
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

def format_time(n):
    hours = int(n)
    minutes = int((n - hours) * 60)
    return f"{hours}h{minutes:02}m"

def print_ascii_table(headers, rows, title=None):
    col_widths = [max(len(str(val)) for val in col) for col in zip(headers, *rows)]
    table_width = sum(col_widths) + len(col_widths) * 3 - 1
    ### sep is a separator line
    sep = "+".join("-" * (w + 2) for w in col_widths)

    if title:
        print("-" * table_width)
        print(f"{title:^{table_width}}")
        print("-" * table_width)

    header_row = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    print(header_row)
    print(sep)

    for row in rows:
        print(" | ".join(f"{str(c):<{w}}" for c, w in zip(row, col_widths)))
    
    print(sep)




def summarize_by_tier(runs, days=7, last=None, include=None):
    if include is None:
        include = {"coin": True, "cell": True, "dice": True, "time": False, "wave": False}

    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in runs if datetime.strptime(r["date"], "%Y-%m-%d") >= cutoff]
    if last:
        recent = recent[-last:]

    by_tier = defaultdict(list)
    for r in recent:
        by_tier[r["tier"]].append(r)

    rows = []
    for tier in sorted(by_tier):
        data = by_tier[tier]
        row = [tier]
        
        if include["coin"]:
            cph = [r["coins_per_hour"] for r in data]
            row += [format_number(min(cph)), format_number(max(cph)), format_number(sum(cph)/len(cph))]

        if include["cell"]:
            cellph = [r["cells_per_hour"] for r in data]
            row += [format_number(min(cellph)), format_number(max(cellph)), format_number(sum(cellph)/len(cellph))]

        if include["dice"]:
            diceph = [r.get("rerolldice_per_hour", 0) for r in data]
            row += [format_number(min(diceph)), format_number(max(diceph)), format_number(sum(diceph)/len(diceph))]

        if include["time"]:
            time = [r["time"] for r in data]
            row += [format_time(min(time)), format_time(max(time)), format_time(sum(time)/len(time))]

        if include["wave"]:
            waves = [r["waves"] for r in data]
            row += [min(waves), max(waves), round(sum(waves)/len(waves), 1)]

        row.append(len(data))
        rows.append(row)

    headers = ["Tier"]
    if include["coin"]:
        headers += ["MinCoin", "MaxCoin", "AvgCoin"]
    if include["cell"]:
        headers += ["MinCell", "MaxCell", "AvgCell"]
    if include["dice"]:
        headers += ["MinDice", "MaxDice", "AvgDice"]
    if include["time"]:
        headers += ["MinTime", "MaxTime", "AvgTime"]
    if include["wave"]:
        headers += ["MinWave", "MaxWave", "AvgWave"]
    headers.append("Runs")

    title_parts = ["Per-Hour Summary"]
    if last:
        title_parts.append(f"for Last {last} Runs")
    else:
        title_parts.append(f"for Last {days} Days")
    
    title=" ".join(title_parts)
    print_ascii_table(headers, rows, title )

def summarize_by_day(runs, days=7):
    cutoff = datetime.now() - timedelta(days=days)
    daysummary = defaultdict(lambda: {"coins": 0, "cells": 0, "dice": 0, "tiers": []})

    for run in runs:
        run_date = datetime.strptime(run["date"], "%Y-%m-%d")
        if run_date >= cutoff:
            d = run["date"]
            daysummary[d]["coins"] += run["coins"]
            daysummary[d]["cells"] += run["cells"]
            daysummary[d]["dice"] += run.get("rerolldice", 0)
            daysummary[d]["tiers"].append(str(run["tier"]))

    rows = []
    for date in sorted(daysummary):
        day = daysummary[date]
        rows.append([
            date,
            format_number(day["coins"]),
            format_number(day["cells"]),
            format_number(day["dice"]),
            " ".join(day["tiers"])
        ])

    title = "Daily Totals (Last {} Days):".format(days)
    headers = ["Tier", "Coins", "Cells", "Dice", "Tiers"]
    print_ascii_table(headers, rows, title=title)


def main():
    args = parse_args()
    runs = load_json()

    if not args.summary and not args.daily:
        print("No output mode selected. Use --summary or --daily.")
        print("Optional: --days N (default 7), --last N")
        return

    # Default columns
    fields = {"coin": args.coin, "cell": args.cell, "dice": args.dice, "time": args.time, "wave": args.wave}
    if not any(fields.values()):
        fields["coin"] = fields["cell"] = fields["dice"] = True

    if args.summary:
        summarize_by_tier(runs, days=args.days, last=args.last, include=fields)

    if args.daily:
        summarize_by_day(runs, args.days)

if __name__ == "__main__":
    main()
