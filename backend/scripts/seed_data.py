import os
import sys
import csv
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas.data import DataItemCreate
from backend.services.data_service import DataService

def find_csv_path() -> Path:
    candidates = [
        PROJECT_ROOT / "data" / "samsung_stock_2024_present.csv",
        PROJECT_ROOT.parent / "3-1" / "data" / "samsung_stock_2024_present.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Could not locate samsung_stock_2024_present.csv")

def seed_database(limit: int = 656, clear_first: bool = False):
    csv_path = find_csv_path()
    print(f"[Seed] Reading dataset from {csv_path}")

    data_service = DataService()

    # Clear existing if requested
    if clear_first:
        print("[Seed] Clearing existing data...")
        existing_items, _ = data_service.get_items(limit=1000)
        for item in existing_items:
            data_service.delete_item(item.id)

    inserted_count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if inserted_count >= limit:
                break
            
            date_str = row["Date"].strip()
            close_val = round(float(row["Close"]), 0)
            open_val = round(float(row.get("Open", close_val)), 0)
            high_val = round(float(row.get("High", close_val)), 0)
            low_val = round(float(row.get("Low", close_val)), 0)
            volume = int(float(row.get("Volume", 0)))

            memo = (
                f"시가 {open_val:,.0f} | 고가 {high_val:,.0f} | "
                f"저가 {low_val:,.0f} | 거래량 {volume:,.0f}주"
            )

            item = DataItemCreate(
                date=date_str,
                value=close_val,
                memo=memo
            )
            data_service.add_item(item)
            inserted_count += 1

            if inserted_count % 100 == 0:
                print(f"[Seed] Inserted {inserted_count} records...")

    print(f"[Seed] Finished! Successfully seeded {inserted_count} records into 'data' collection.")
    summary = data_service.get_summary()
    print(f"[Seed] Current Summary: {summary.period}, Count: {summary.count}, Avg: {summary.metrics.average:,.0f}원, Trend: {summary.trend}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed 3-1 Samsung stock dataset into Firestore")
    parser.add_argument("--limit", type=int, default=656, help="Maximum number of rows to insert (default: 656)")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()

    seed_database(limit=args.limit, clear_first=args.clear)
