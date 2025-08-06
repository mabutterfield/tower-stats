#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def load_data(path="runlog.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Analyze runlog performance stats"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Show top N runs by coins per hour"
    )
    parser.add_argument(
        "--tier",
        type=int,
        help="Filter runs by tier"
    )
    parser.add_argument(
        "--type",
        choices=["farm - day", "farm - overnight", "milestone"],
        help="Filter by run_type"
    )
    args = parser.parse_args()

    data = load_data()
    if not data:
        print("No data loaded.")
        return

    filtered = data
    if args.tier:
        filtered = [r for r in filtered if r["tier"] == args.tier]
    if args.type:
        filtered = [r for r in filtered if r["run_type"] == args.type]

    sorted_runs = sorted(
        filtered,
        key=lambda r: r["coins_per_hour"],
        reverse=True
    )[:args.top]

    print(f"\nTop {len(sorted_runs)} Runs:")
    for run in sorted_runs:
        print(f"- {run['date']} | Tier {run['tier']} | {run['coins_per_hour']} coins/hr")

if __name__ == "__main__":
    main()
    main()
