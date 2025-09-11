import csv
import json
import os
import re
import shutil
from datetime import datetime
from difflib import get_close_matches

INPUT_CSV = "runlog.csv"
OUTPUT_JSON = "runlog.json"
DATE_SUFFIX = datetime.now().strftime("%Y%m%d")
BACKUP_JSON = f"{OUTPUT_JSON}.{DATE_SUFFIX}"

MANDATORY_FIELDS = ["date", "tier", "time", "waves", "coins", "cells"]
OPTIONAL_FIELDS = ["run_type", "comments", "rerolldice"]

VALID_RUN_TYPES = ["farm - overnight", "farm - day", "milestone", "tournament"]
DEFAULT_RUN_TYPE = "other"

KNOWN_DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%m-%d-%y", "%m/%d/%y"]

def fuzzy_match_run_type(value):
    if not value:
        return DEFAULT_RUN_TYPE
    matches = get_close_matches(value.lower(), VALID_RUN_TYPES, n=1, cutoff=0.6)
    return matches[0] if matches else DEFAULT_RUN_TYPE

def parse_date(raw):
    for fmt in KNOWN_DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{raw}'")

def parse_coin_value(raw):
    value = raw.strip()
    if value.endswith("q"):
        return float(value[:-1]) * 1_000_000_000_000_000  # Quadrillion
    elif value.endswith("Q"):
        return float(value[:-1]) * 1_000_000_000_000_000_000  # Quintillion
    elif value.endswith("T"):
        return float(value[:-1]) * 1_000_000_000_000  # Trillion
    elif value.endswith("B"):
        return float(value[:-1]) * 1_000_000_000  # Billion
    else:
        return float(value) * 1_000_000_000_000  # Default to Trillions

def parse_cell_or_dice_value(raw):
    value = raw.strip()
    if value.endswith("M"):
        return float(value[:-1]) * 1_000_000
    elif value.endswith("K"):
        return float(value[:-1]) * 1_000
    else:
        return float(value) * 1_000  # Default to Thousands




def parse_time(value):
    try:
        # If it's already a float, just return it
        return float(value)
    except ValueError:
        pass

    # Look for h/m format
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?'
    match = re.fullmatch(pattern, value.strip().lower())
    if not match:
        raise ValueError(f"Invalid time format: '{value}'")

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    return round(hours + minutes / 60, 2)


def validate_row(row, index):
    try:
        # print(f"Validating row {index + 2}: {row}")

        for field in MANDATORY_FIELDS:
            if field not in row or row[field].strip() == "":
                print(f"Validation error in row {index + 2}: {row}")
                raise ValueError(f"Missing value for '{field}'")
            
        dt = parse_date(row["date"])
        row["date"] = dt.strftime("%Y-%m-%d")
        row["epoch"] = int(dt.timestamp())

        row["tier"] = int(row["tier"])
        row["time"] = parse_time(row["time"])
        row["waves"] = int(row["waves"])
        row["coins"] = int(parse_coin_value(row["coins"]))
        row["cells"] = int(parse_cell_or_dice_value(row["cells"]))

        reroll_raw = row.get("rerolldice", "").strip()
        if reroll_raw:
            row["rerolldice"] = int(parse_cell_or_dice_value(reroll_raw))
            row["rerolldice_per_hour"] = int(row["rerolldice"] / row["time"])
        else:
            row["rerolldice"] = 0
            row["rerolldice_per_hour"] = 0.0

        run_type = row.get("run_type", "").strip()
        row["run_type"] = fuzzy_match_run_type(run_type)
        # row["comments"] = row.get("comments", "").strip()

        row["coins_per_hour"] = int(row["coins"] / row["time"])
        row["cells_per_hour"] = int(row["cells"] / row["time"])

        return row
    except Exception as e:
        raise ValueError(f"Row {index + 2}: {e}")







def backup_existing_json():
    if os.path.exists(OUTPUT_JSON):
        try:
            shutil.move(OUTPUT_JSON, BACKUP_JSON)
        except Exception as e:
            print(f"Warning: Failed to backup {OUTPUT_JSON} to {BACKUP_JSON}: {e}")

def main():
    parsed_data = []
    error_count = 0

    if not os.path.exists(INPUT_CSV):
        print(f"Error: '{INPUT_CSV}' not found.")
        return

    with open(INPUT_CSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        print("CSV headers detected:", reader.fieldnames)

        for idx, row in enumerate(reader):
            try:
                validated_row = validate_row(row, idx)
                parsed_data.append(validated_row)
            except ValueError as e:
                print("Validation error:", e)
                error_count += 1

    if not parsed_data:
        print("No valid entries found. Aborting.")
        return

    try:
        backup_existing_json()
        with open(OUTPUT_JSON, "w", encoding='utf-8') as jf:
            json.dump(parsed_data, jf, indent=2)
        print(f"Successfully parsed {len(parsed_data)} entries into '{OUTPUT_JSON}'.")
        if error_count:
            print(f"Ignored {error_count} invalid row(s).")
    except Exception as e:
        print(f"Unexpected error while writing JSON: {e}")

if __name__ == "__main__":
    main()
