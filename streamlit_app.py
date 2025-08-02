import datetime
import time
from random import randrange
from datetime import timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests

st.set_page_config(page_title="Premise Security System", page_icon="🏠")
st.title("🏠 Realtime Dashboard")
st.write("This app displays the realtime image and data captured by ESP32 when motion is detected.")

# Initialize table
if "df" not in st.session_state:
    np.random.seed(42)
    d_start = datetime.datetime.strptime('1/1/2025 3:00 PM', '%m/%d/%Y %I:%M %p')
    d_end = datetime.datetime.strptime('1/31/2025 5:00 AM', '%m/%d/%Y %I:%M %p')
    def random_date(start, end):
        delta = end - start
        int_delta = delta.days * 86400 + delta.seconds
        return start + timedelta(seconds=randrange(int_delta))
    data = {
        "ID": [f"ALERT-{i}" for i in range(10, 0, -1)],
        "Issue": ["motion detected"] * 10,
        "Status": np.random.choice(["Uploaded successfully", "In Progress", "Uploaded failed"], size=10),
        "Detected time": [random_date(d_start, d_end) for _ in range(10)],
    }
    st.session_state.df = pd.DataFrame(data)

# Editable table
st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status", help="Image status",
            options=["Uploaded successfully", "In Progress", "Uploaded failed"],
            required=True,
        )
    },
    disabled=["ID", "Date Submitted"],
)

# Metrics
st.header("Statistics")
col1, col2 = st.columns(2)
col1.metric("Number of motion detected", len(st.session_state.df))
col2.metric("Latest motion detected time", str(st.session_state.df["Detected time"].max()))

# Realtime data appending + chart
st.header("Live Motion Log")
log_url = "http://localhost:5000/motion-data"
last_log_count = len(st.session_state.df)
placeholder = st.empty()

while True:
    try:
        response = requests.get(log_url)
        if response.ok:
            logs = response.json()
            new_logs = logs[last_log_count:]
            for ts in new_logs:
                new_id = f"ALERT-{len(st.session_state.df)+1}"
                st.session_state.df.loc[len(st.session_state.df)] = {
                    "ID": new_id,
                    "Issue": "motion detected",
                    "Status": "Uploaded successfully",
                    "Detected time": pd.to_datetime(ts)
                }
            last_log_count = len(logs)

            with placeholder.container():
                st.write("### Updated Motion Log Table")
                st.dataframe(st.session_state.df)

                # Charts
                chart_df = st.session_state.df.copy()
                chart_df["Date"] = pd.to_datetime(chart_df["Detected time"]).dt.date
                chart_df["Hour"] = pd.to_datetime(chart_df["Detected time"]).dt.hour

                daily_counts = chart_df.groupby("Date").size().reset_index(name="Count")
                bar_chart = alt.Chart(daily_counts).mark_bar().encode(
                    x="Date:T",
                    y="Count:Q"
                ).properties(title="Motion Detections per Day")

                heatmap = alt.Chart(chart_df).mark_rect().encode(
                    x=alt.X("Hour:O", title="Hour of Day"),
                    y=alt.Y("Date:T", title="Date"),
                    color=alt.Color("count():Q", scale=alt.Scale(scheme="orange")),
                    tooltip=["Date:T", "Hour:O", "count():Q"]
                ).properties(title="Heatmap of Motion Detections by Hour")

                st.altair_chart(bar_chart, use_container_width=True)
                st.altair_chart(heatmap, use_container_width=True)

        time.sleep(5)

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        break
