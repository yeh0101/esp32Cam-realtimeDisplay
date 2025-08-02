import datetime
import random
from random import randrange
from datetime import timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
import time

# Show app title and description.
st.set_page_config(page_title="Premise Security System", page_icon="🏠")
st.title("🏠Realtime Dashboard")
st.write(
    """
    This app displays the realtime image and data captured by ESP32 when the motion detected
    """
)

# Create a random Pandas dataframe with existing tickets.
if "df" not in st.session_state:
    # Set seed for reproducibility.
    np.random.seed(42)

    # Make up some fake issue descriptions.
    issue_descriptions = [
        "motion detected",
    ]

    # Generate random datetime between two dates.
    d_start = datetime.datetime.strptime('1/1/2025 3:00 PM', '%m/%d/%Y %I:%M %p')
    d_end = datetime.datetime.strptime('1/31/2025 5:00 AM', '%m/%d/%Y %I:%M %p')
    def random_date(start, end):
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = randrange(int_delta)
        return start + timedelta(seconds=random_second)
    
    # Generate the dataframe with 10 rows.
    data = {
        "ID": [f"ALERT-{i}" for i in range(10, 0, -1)],
        "Issue": np.random.choice(issue_descriptions, size=10),
        "Status": np.random.choice(["Uploaded successfully", "In Progress", "Uploaded failed"], size=10),
        "Detected time": [
            random_date(d_start, d_end)
            for _ in range(10)
        ],
    }
    df = pd.DataFrame(data)

    # Save the dataframe in session state
    st.session_state.df = df

# Editable table
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Image status",
            options=["Uploaded successfully", "In Progress", "Uploaded failed"],
            required=True,
        ),
    },
    disabled=["ID", "Date Submitted"],
)

# Stats section
st.header("Statistics")
col1, col2 = st.columns(2)
col1.metric(label="Number of motion detected", value=len(df[df['Issue'] == 'motion detected']))
col2.metric(label="Latest motion detected time", value=str(df['Detected time'].max()))

# Live motion detection logs from Flask server
st.header("Live Motion Log")
placeholder = st.empty()

while True:
    response = requests.get("http://localhost:5000/motion-data")
    if response.ok:
        logs = response.json()
        with placeholder.container():
            st.write("### Motion Timestamps:")
            for timestamp in reversed(logs):
                st.write(f"📍 {timestamp}")
    time.sleep(5)
