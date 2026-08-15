import pandas as pd
import streamlit as st
from datetime import date
from app.db.database import init_db
from app.db.crud import list_attendance

st.set_page_config(page_title="Attendance Analytics", layout="wide")
init_db()

st.title("Secure Vision Attendance — Analytics")
records = list_attendance(str(date.today()))
df = pd.DataFrame(records)

c1, c2, c3 = st.columns(3)
c1.metric("Present today", len(df))
c2.metric("Unique people", df["name"].nunique() if not df.empty else 0)
c3.metric("Records stored", len(list_attendance()))

st.subheader("Today's attendance")
if df.empty:
    st.info("No attendance records yet.")
else:
    cols = [c for c in ["name", "date", "time", "match_score", "match_distance", "quality_blur", "quality_brightness"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True)
