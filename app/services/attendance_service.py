import pandas as pd
from datetime import datetime
import os

FILE_PATH = "data/attendance.csv"

def mark_attendance(name):
    print("MARKING:", name)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # ✅ Ensure data folder exists
    os.makedirs("data", exist_ok=True)

    # ✅ Ensure file exists with headers
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(FILE_PATH, index=False)

    # ✅ Handle empty or corrupted file safely
    try:
        df = pd.read_csv(FILE_PATH)
    except Exception:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])

    # ✅ Prevent duplicate attendance (same person same day)
    if not df.empty:
        if ((df["Name"] == name) & (df["Date"] == date_str)).any():
            return f"{name} already marked today"

    # ✅ Add new record
    new_entry = pd.DataFrame([{
        "Name": name,
        "Date": date_str,
        "Time": time_str
    }])

    df = pd.concat([df, new_entry], ignore_index=True)

    # ✅ Save back to CSV
    df.to_csv(FILE_PATH, index=False)

    return f"{name} marked present"