"""
csv_logger.py
--------------
Handles creation of data/visitors.csv and safe appending of new records.

This file lives outside of static/ so it is never reachable by a direct
browser request (see app.py, which does not register any route serving
the data/ directory, and .gitignore / server config notes in README.md).
"""

import csv
import os

from config import Config

FIELDNAMES = [
    "id",
    "user_name",
    "ip_address",
    "country",
    "region",
    "state",
    "city",
    "timezone",
    "created_at",
]


def ensure_csv():
    """Create the CSV file with a header row if it doesn't already exist."""
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    if not os.path.exists(Config.CSV_PATH):
        with open(Config.CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def append_visitor_row(record):
    """
    Append a single visitor record to the CSV.

    `record` must contain all keys in FIELDNAMES. Uses csv.DictWriter so
    values are correctly quoted/escaped regardless of content.
    """
    ensure_csv()
    with open(Config.CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({key: record.get(key, "") for key in FIELDNAMES})
