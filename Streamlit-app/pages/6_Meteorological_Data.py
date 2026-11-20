
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Meteorological Data",
    page_icon="🌦️",
    layout="wide"
)

st.title("🌦️ Meteorological Data")

st.write(
    "Explore hourly temperature and precipitation "
    "for the selected electricity area."
)


# ==================================================
# 2. FIND PROJECT AND WEATHER DIRECTORY
# ==================================================

# Project structure:
# IND320/
# ├── Notbook/
# │   └── Part3/data/weather/
# └── Streamlit-app/
#     └── pages/6_Meteorological_Data.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEATHER_DIR = (
    PROJECT_ROOT
    / "Notbook"
    / "Part3"
    / "data"
    / "weather"
)


# ==================================================
# 3. CHECK WEATHER DIRECTORY
# ==================================================

if not WEATHER_DIR.exists():

    st.error("Weather data directory was not found.")

    st.write("Expected directory:")
    st.code(str(WEATHER_DIR))

    st.stop()


# ==================================================
# 4. FIND AVAILABLE WEATHER FILES
# ==================================================

areas = ["NO1", "NO2", "NO3", "NO4", "NO5"]

weather_file_map = {}

for area in areas:

    file_path = WEATHER_DIR / f"{area}_weather_2024.csv"

    if file_path.is_file():
        weather_file_map[area] = file_path


available_areas = list(weather_file_map.keys())


if not available_areas:

    st.error("No Norwegian weather files were found.")

    st.write("Files found in weather directory:")

    for file in WEATHER_DIR.iterdir():
        st.write(file.name)

    st.info(
        "Available project files should include "
        "NO3_weather_2024.csv."
    )

    st.stop()


# ==================================================
# 5. AREA SELECTION
# ==================================================

default_area = (
    "NO3" if "NO3" in available_areas
    else available_areas[0]
)

if (
    "selected_no_area" not in st.session_state
    or st.session_state["selected_no_area"] not in available_areas
):
    st.session_state["selected_no_area"] = default_area


selected_area = st.selectbox(
    "Select electricity area",
    options=available_areas,
    index=available_areas.index(
        st.session_state["selected_no_area"]
    ),
    key="weather_area_selection"
)

# Share selected area with other Part 3 pages
st.session_state["selected_no_area"] = selected_area


# ==================================================
# 6. LOAD WEATHER DATA
# ==================================================

@st.cache_data(show_spinner="Loading weather data...")
def load_weather(file_path):

    data = pd.read_csv(file_path)

    required_columns = [
        "time",
        "temperature_2m",
        "precipitation",
        "point_id"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns: "
            + ", ".join(missing_columns)
        )

    data["time"] = pd.to_datetime(
        data["time"],
        errors="coerce"
    )

    data["temperature_2m"] = pd.to_numeric(
        data["temperature_2m"],
        errors="coerce"
    )

    data["precipitation"] = pd.to_numeric(
        data["precipitation"],
        errors="coerce"
    )

    data = data.dropna(subset=["time"])

    return data.sort_values("time")


weather_file = weather_file_map[selected_area]

try:

    raw_data = load_weather(str(weather_file))

except Exception as error:

    st.error(f"Could not load weather data: {error}")
    st.stop()


if raw_data.empty:

    st.warning("The weather file contains no valid observations.")
    st.stop()


st.success(
    f"Successfully loaded {weather_file.name}: "
    f"{len(raw_data):,} records."
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
        number_of_points=("point_id", "nunique")
    )
)

if hourly_data.empty:

    st.warning("No hourly observations available.")
    st.stop()


# ==================================================
# 8. DATASET OVERVIEW
# ==================================================

st.subheader("Dataset overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Hourly observations",
    f"{len(hourly_data):,}"
)

col2.metric(
    "Geographical points",
    f"{raw_data['point_id'].nunique():,}"
)

col3.metric(
    "Average temperature",
    f"{hourly_data['temperature_2m'].mean():.2f} °C"
)

col4.metric(
    "Average hourly precipitation",
    f"{hourly_data['precipitation'].mean():.3f} mm"
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
    max_value=max_date
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

    st.warning("No observations found for the selected period.")
    st.stop()


# ==================================================
# 10. TEMPERATURE AND PRECIPITATION TABS
# ==================================================

tab1, tab2 = st.tabs([
    "🌡️ Temperature",
    "🌧️ Precipitation"
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
            "temperature_2m": "Temperature (°C)"
        }
    )

    fig_temp.update_layout(
        hovermode="x unified",
        xaxis_title="Date and time",
        yaxis_title="Temperature (°C)"
    )

    st.plotly_chart(
        fig_temp,
        use_container_width=True
    )

    st.subheader("Temperature statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean temperature",
        f"{filtered_data['temperature_2m'].mean():.2f} °C"
    )

    col2.metric(
        "Minimum temperature",
        f"{filtered_data['temperature_2m'].min():.2f} °C"
    )

    col3.metric(
        "Maximum temperature",
        f"{filtered_data['temperature_2m'].max():.2f} °C"
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
            "precipitation": "Precipitation (mm)"
        }
    )

    fig_precip.update_layout(
        hovermode="x unified",
        xaxis_title="Date and time",
        yaxis_title="Precipitation (mm)"
    )

    st.plotly_chart(
        fig_precip,
        use_container_width=True
    )

    st.subheader("Precipitation statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean per hour",
        f"{filtered_data['precipitation'].mean():.3f} mm"
    )

    col2.metric(
        "Maximum per hour",
        f"{filtered_data['precipitation'].max():.2f} mm"
    )

    col3.metric(
        "Hours with precipitation",
        f"{(filtered_data['precipitation'] > 0).sum():,}"
    )


# ==================================================
# 11. DATA TABLE AND DOWNLOAD
# ==================================================

st.divider()

st.subheader("Weather observations")

with st.expander("View hourly weather data"):

    st.dataframe(
        filtered_data,
        use_container_width=True,
        hide_index=True
    )

    csv_data = filtered_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv_data,
        file_name=f"{selected_area}_weather_2024.csv",
        mime="text/csv"
    )


# ==================================================
# 12. DATA INFORMATION
# ==================================================

with st.expander("About this dataset"):

    st.write("""
    **Source:** Supplied IND320 project weather data.

    **Area:** NO3 when NO3 is selected.

    **Frequency:** Hourly observations.

    **Variables:**

    - `time`: Observation timestamp.
    - `temperature_2m`: Temperature at 2 metres (°C).
    - `precipitation`: Precipitation (mm).
    - `point_id`: Geographical measurement point.
    - `latitude`: Latitude.
    - `longitude`: Longitude.

    Measurements from multiple geographical points are
    averaged for each timestamp.
    """)
