import csv
from pathlib import Path
from app.db.database import init_db
from app.db.crud import create_attendance

CSV_PATH = Path("data/attendance.csv")


def main():
    init_db()
    if not CSV_PATH.exists():
        print("No legacy CSV found.")
        return
    imported = 0
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("Name") or not row.get("Date") or not row.get("Time"):
                continue
            imported += int(create_attendance(row["Name"], row["Date"], row["Time"]))
    print(f"Imported {imported} valid attendance records.")


if __name__ == "__main__":
    main()
