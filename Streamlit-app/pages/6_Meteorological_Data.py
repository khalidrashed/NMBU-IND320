"""
Meteorological Data page for the IND320 Streamlit app.

Loads weather observations from MongoDB Atlas:
Database: ind320
Collection: weather_data

Expected fields:
point_id, region, time, latitude, longitude,
precipitation, temperature_2m
"""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Meteorological Data",
    page_icon="🌦️",
    layout="wide",
)

st.title("🌦️ Meteorological Data")
st.write(
    "Explore hourly temperature and precipitation "
    "for the selected electricity area."
)


# ==================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# dotenv is optional: Streamlit Cloud can provide MONGODB_URI
# directly through its environment/secrets configuration.
try:
    from dotenv import load_dotenv

    for env_path in [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT.parent / ".env",
    ]:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
except ImportError:
    pass

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    try:
        MONGODB_URI = st.secrets["MONGODB_URI"]
    except Exception:
        MONGODB_URI = None

if not MONGODB_URI:
    st.error(
        "MONGODB_URI was not found. Add it to the project .env file "
        "or to Streamlit secrets."
    )
    st.stop()


# ==================================================
# 3. MONGODB SETTINGS
# ==================================================

DATABASE_NAME = "ind320"
COLLECTION_NAME = "weather_data"

REQUIRED_COLUMNS = [
    "point_id",
    "region",
    "time",
    "latitude",
    "longitude",
    "precipitation",
    "temperature_2m",
]


# ==================================================
# 4. LOAD AVAILABLE REGIONS
# ==================================================

@st.cache_data(show_spinner="Connecting to MongoDB...")
def load_available_regions():
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )
    try:
        collection = client[DATABASE_NAME][COLLECTION_NAME]
        regions = collection.distinct("region")
        return sorted(
            [str(region) for region in regions if region is not None]
        )
    finally:
        client.close()


try:
    available_areas = load_available_regions()
except Exception as error:
    st.error(f"Could not connect to MongoDB: {error}")
    st.stop()

if not available_areas:
    st.error(
        f"No regions were found in "
        f"{DATABASE_NAME}.{COLLECTION_NAME}."
    )
    st.stop()


# ==================================================
# 5. AREA SELECTION
# ==================================================

default_area = "NO3" if "NO3" in available_areas else available_areas[0]

if (
    "selected_no_area" not in st.session_state
    or st.session_state["selected_no_area"] not in available_areas
):
    st.session_state["selected_no_area"] = default_area

selected_area = st.selectbox(
    "Select electricity area",
    options=available_areas,
    index=available_areas.index(st.session_state["selected_no_area"]),
    key="weather_area_selection",
)

# Share selected area with other Part 3 pages.
st.session_state["selected_no_area"] = selected_area


# ==================================================
# 6. LOAD WEATHER DATA FROM MONGODB
# ==================================================

@st.cache_data(show_spinner="Loading weather data from MongoDB...")
def load_weather(region):
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )

    try:
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        projection = {
            "_id": 0,
            "point_id": 1,
            "region": 1,
            "time": 1,
            "latitude": 1,
            "longitude": 1,
            "precipitation": 1,
            "temperature_2m": 1,
        }

        documents = list(
            collection.find({"region": region}, projection).sort("time", 1)
        )
    finally:
        client.close()

    if not documents:
        return pd.DataFrame()

    data = pd.DataFrame(documents)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "The MongoDB documents are missing these fields: "
            + ", ".join(missing_columns)
        )

    data["time"] = pd.to_datetime(
        data["time"],
        errors="coerce",
        utc=True,
    ).dt.tz_convert(None)

    for column in [
        "point_id",
        "latitude",
        "longitude",
        "precipitation",
        "temperature_2m",
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["time"])

    return data.sort_values("time").reset_index(drop=True)


try:
    raw_data = load_weather(selected_area)
except Exception as error:
    st.error(f"Could not load weather data: {error}")
    st.stop()

if raw_data.empty:
    st.warning(f"No weather observations were found for {selected_area}.")
    st.stop()

st.success(
    f"Successfully loaded {len(raw_data):,} records "
    f"for {selected_area} from MongoDB."
)


# ==================================================
# 7. AGGREGATE DATA BY HOUR
# ==================================================

hourly_data = (
    raw_data
    .groupby("time", as_index=False)
    .agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        number_of_points=("point_id", "nunique"),
    )
)

if hourly_data.empty:
    st.warning("No hourly observations are available.")
    st.stop()


# ==================================================
# 8. DATASET OVERVIEW
# ==================================================

st.subheader("Dataset overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Hourly observations",
    f"{len(hourly_data):,}",
)

col2.metric(
    "Geographical points",
    f"{raw_data['point_id'].nunique():,}",
)

col3.metric(
    "Average temperature",
    f"{hourly_data['temperature_2m'].mean():.2f} °C",
)

col4.metric(
    "Average hourly precipitation",
    f"{hourly_data['precipitation'].mean():.3f} mm",
)


# ==================================================
# 9. DATE FILTER
# ==================================================

st.subheader("Select time period")

min_date = hourly_data["time"].min().date()
max_date = hourly_data["time"].max().date()

date_range = st.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_data = hourly_data[
        (hourly_data["time"].dt.date >= start_date)
        & (hourly_data["time"].dt.date <= end_date)
    ].copy()
else:
    filtered_data = hourly_data.copy()

if filtered_data.empty:
    st.warning("No observations were found for the selected period.")
    st.stop()


# ==================================================
# 10. TEMPERATURE AND PRECIPITATION TABS
# ==================================================

tab1, tab2 = st.tabs([
    "🌡️ Temperature",
    "🌧️ Precipitation",
])


# --------------------------------------------------
# TAB 1: TEMPERATURE
# --------------------------------------------------

with tab1:
    st.subheader("Hourly temperature")

    fig_temp = px.line(
        filtered_data,
        x="time",
        y="temperature_2m",
        title=f"Hourly temperature - {selected_area}",
        labels={
            "time": "Date and time",
            "temperature_2m": "Temperature (°C)",
        },
    )

    fig_temp.update_layout(
        hovermode="x unified",
        xaxis_title="Date and time",
        yaxis_title="Temperature (°C)",
    )

    st.plotly_chart(fig_temp, width="stretch")

    st.subheader("Temperature statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean temperature",
        f"{filtered_data['temperature_2m'].mean():.2f} °C",
    )

    col2.metric(
        "Minimum temperature",
        f"{filtered_data['temperature_2m'].min():.2f} °C",
    )

    col3.metric(
        "Maximum temperature",
        f"{filtered_data['temperature_2m'].max():.2f} °C",
    )


# --------------------------------------------------
# TAB 2: PRECIPITATION
# --------------------------------------------------

with tab2:
    st.subheader("Hourly precipitation")

    fig_precip = px.bar(
        filtered_data,
        x="time",
        y="precipitation",
        title=f"Hourly precipitation - {selected_area}",
        labels={
            "time": "Date and time",
            "precipitation": "Precipitation (mm)",
        },
    )

    fig_precip.update_layout(
        hovermode="x unified",
        xaxis_title="Date and time",
        yaxis_title="Precipitation (mm)",
    )

    st.plotly_chart(fig_precip, width="stretch")

    st.subheader("Precipitation statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean per hour",
        f"{filtered_data['precipitation'].mean():.3f} mm",
    )

    col2.metric(
        "Maximum per hour",
        f"{filtered_data['precipitation'].max():.2f} mm",
    )

    col3.metric(
        "Hours with precipitation",
        f"{(filtered_data['precipitation'] > 0).sum():,}",
    )


# ==================================================
# 11. DATA TABLE AND DOWNLOAD
# ==================================================

st.divider()
st.subheader("Weather observations")

with st.expander("View hourly weather data"):
    st.dataframe(
        filtered_data,
        width="stretch",
        hide_index=True,
    )

    csv_data = filtered_data.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name=f"{selected_area}_weather_data.csv",
        mime="text/csv",
    )


# ==================================================
# 12. DATA INFORMATION
# ==================================================

with st.expander("About this dataset"):
    st.write(
        f"""
        **Source:** MongoDB Atlas.

        **Database:** `{DATABASE_NAME}`

        **Collection:** `{COLLECTION_NAME}`

        **Area:** `{selected_area}`

        **Frequency:** Hourly observations.

        **Variables:**

        - `time`: Observation timestamp.
        - `region`: Norwegian electricity area (NO1–NO5).
        - `point_id`: Geographical measurement point.
        - `temperature_2m`: Temperature at 2 metres (°C).
        - `precipitation`: Precipitation (mm).
        - `latitude`: Latitude.
        - `longitude`: Longitude.

        Measurements from multiple geographical points are
        averaged for each timestamp.
        """
    )



