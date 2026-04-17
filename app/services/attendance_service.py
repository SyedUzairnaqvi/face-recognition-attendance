import os
import pandas as pd
from datetime import datetime

FILE_PATH = "data/attendance.csv"

def mark_attendance(name):
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(FILE_PATH, index=False)

    df = pd.read_csv(FILE_PATH)

    now = datetime.now()
    new_entry = {
        "Name": name,
        "Date": now.strftime("%Y-%m-%d"),
        "Time": now.strftime("%H:%M:%S")
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)