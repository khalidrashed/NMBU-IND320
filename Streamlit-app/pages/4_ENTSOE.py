
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

st.set_page_config(
    page_title="ENTSO-E Electricity Flows",
    page_icon="âš¡",
    layout="wide",
)

st.title("âš¡ ENTSO-E â€“ Electricity Flows")
st.write("Explore electricity transfers to and from Norway.")

# Load the MongoDB connection string from the project's .env file.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
MONGODB_URI = os.getenv("MONGODB_URI")


@st.cache_data(ttl=300)
def load_entsoe_data():
    """Load ENTSO-E observations stored in MongoDB."""
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI is missing from the .env file.")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)

    try:
        collection = client["ind320"]["entsoe_crossborder_flows"]

        projection = {
            "_id": 0,
            "timestamp": 1,
            "connection": 1,
            "from_area": 1,
            "to_area": 1,
            "direction": 1,
            "flow_mw": 1,
        }

        return pd.DataFrame(collection.find({}, projection))
    finally:
        client.close()


try:
    with st.spinner("Loading data from MongoDB..."):
        df = load_entsoe_data()
except Exception as error:
    st.error(f"Could not load ENTSO-E data: {error}")
    st.stop()

if df.empty:
    st.warning("No ENTSO-E data was found.")
    st.stop()

# Clean and prepare the data.
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["flow_mw"] = pd.to_numeric(df["flow_mw"], errors="coerce")
df = df.dropna(
    subset=[
        "timestamp",
        "flow_mw",
        "connection",
        "direction",
    ]
)

if df.empty:
    st.warning("No valid observations are available.")
    st.stop()

# Create a year column for the year selector.
df["year"] = df["timestamp"].dt.year
years = sorted(df["year"].unique().tolist(), reverse=True)
connections = sorted(df["connection"].unique().tolist())

# Two-column layout as required by the assignment.
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("1. Annual electricity transfer")

    selected_connection = st.radio(
        "Select a connection",
        options=connections,
        key="selected_connection",
    )

    selected_year = st.selectbox(
        "Select a year",
        options=years,
        key="selected_year",
    )

    # Filter the selected connection and year.
    annual = df[
        (df["connection"] == selected_connection)
        & (df["year"] == selected_year)
    ].copy()

    # Estimate transferred energy using the time until the next observation.
    # This avoids treating every MW observation as one full MWh.
    annual = annual.sort_values(["direction", "timestamp"])

    annual["next_timestamp"] = (
        annual.groupby("direction")["timestamp"].shift(-1)
    )

    annual["interval_hours"] = (
        annual["next_timestamp"] - annual["timestamp"]
    ).dt.total_seconds() / 3600

    # Use only positive intervals no longer than one hour.
    # This handles hourly and 15-minute observations conservatively.
    annual["interval_hours"] = annual["interval_hours"].where(
        annual["interval_hours"].between(0, 1)
    )

    annual["estimated_mwh"] = (
        annual["flow_mw"].abs() * annual["interval_hours"]
    )

    pie_data = (
        annual.dropna(subset=["estimated_mwh"])
        .groupby("direction", as_index=False)["estimated_mwh"]
        .sum()
    )

    # Translate the stored direction labels into readable labels.
    direction_labels = {
        "to_Norway": "Import to Norway",
        "from_Norway": "Export from Norway",
    }

    pie_data["direction"] = pie_data["direction"].map(
        lambda value: direction_labels.get(value, value)
    )

    if not pie_data.empty:
        fig_pie = px.pie(
            pie_data,
            names="direction",
            values="estimated_mwh",
            hole=0.3,
            title=f"{selected_connection} â€“ {selected_year}",
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption(
            "Energy is estimated from absolute MW values and the time "
            "to the next observation. Missing intervals are excluded."
        )
    else:
        st.info("There is not enough consecutive data for this pie chart.")

with right_col:
    st.subheader("2. Electricity flow by month")

    # Streamlit pills allow selection of one or more months.
    months = st.pills(
        "Select months",
        options=list(range(1, 13)),
        format_func=lambda month: pd.Timestamp(
            year=2000, month=month, day=1
        ).strftime("%B"),
        selection_mode="multi",
        default=[1],
        key="selected_months",
    )

    if not months:
        st.info("Select at least one month.")
    else:
        # Use the selected year and chosen months for the line chart.
        line_data = df[
            (df["year"] == selected_year)
            & (df["timestamp"].dt.month.isin(months))
        ].copy()

        if line_data.empty:
            st.warning("No data exists for the selected months and year.")
        else:
            line_data["series"] = (
                line_data["connection"].astype(str)
                + " â€“ "
                + line_data["direction"].astype(str)
            )

            # Sort timestamps to make the lines easier to interpret.
            line_data = line_data.sort_values("timestamp")

            fig_line = px.line(
                line_data,
                x="timestamp",
                y="flow_mw",
                color="series",
                labels={
                    "timestamp": "Time",
                    "flow_mw": "Flow (MW)",
                    "series": "Connection and direction",
                },
                title=f"Cross-border flow â€“ {selected_year}",
            )

            st.plotly_chart(fig_line, use_container_width=True)

            st.caption(
                "Each line represents a connection and direction. "
                "Positive and negative readings are shown as reported."
            )

# Document the data source below both columns.
with st.expander("About the data source"):
    st.write(
        """
        **Source:** ENTSO-E Transparency Platform.

        The data represents cross-border electricity flow observations
        involving Norway. The observations were retrieved using the
        ENTSO-E API, inserted into Cassandra using Spark, extracted with
        Spark, and stored in MongoDB for use by this Streamlit app.

        Flow values are reported in MW. The annual pie chart estimates
        energy in MWh from the observation intervals. Intervals longer
        than one hour are excluded from this estimate, so the result
        should be interpreted as an estimate rather than a complete
        official energy total.
        """
    )
