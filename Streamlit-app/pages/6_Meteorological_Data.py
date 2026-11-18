"""Meteorological data explorer using the project's hourly weather CSV files."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Meteorological Data", page_icon="🌦️", layout="wide")
st.title("🌦️ Meteorological Data")
st.write("Explore hourly temperature and precipitation for the selected electricity area.")

# Expected project structure:
# IND320/
# ├── Notbook/Part3/data/weather/NO3_weather_2024.csv
# └── Streamlit-app/pages/6_Meteorological_Data.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEATHER_DIR_CANDIDATES = [
    PROJECT_ROOT / "Notbook" / "Part3" / "data" / "weather",
    Path.home() / "OneDrive" / "Desktop" / "IND320" / "Notbook" / "Part3" / "data" / "weather",
]
WEATHER_DIR = next((path for path in WEATHER_DIR_CANDIDATES if path.is_dir()), WEATHER_DIR_CANDIDATES[0])

if not WEATHER_DIR.is_dir():
    st.error("Weather data directory was not found.")
    st.write("Searched locations:")
    for path in WEATHER_DIR_CANDIDATES:
        st.code(str(path))
    st.info("Place the weather CSV files in `Notbook/Part3/data/weather/` or update WEATHER_DIR_CANDIDATES.")
    st.stop()

areas = ["NO1", "NO2", "NO3", "NO4", "NO5"]
weather_file_map = {
    area: WEATHER_DIR / f"{area}_weather_2024.csv"
    for area in areas
    if (WEATHER_DIR / f"{area}_weather_2024.csv").is_file()
}
available_areas = list(weather_file_map)

if not available_areas:
    st.error("No Norwegian weather files were found.")
    st.write("Files found in the weather directory:")
    for path in WEATHER_DIR.iterdir():
        if path.is_file():
            st.write(path.name)
    st.stop()

# Share the selected area with other pages if they use the same session-state key.
default_area = "NO3" if "NO3" in available_areas else available_areas[0]
if st.session_state.get("selected_no_area") not in available_areas:
    st.session_state["selected_no_area"] = default_area

selected_area = st.selectbox(
    "Select electricity area",
    options=available_areas,
    index=available_areas.index(st.session_state["selected_no_area"]),
    key="weather_area_selection",
)
st.session_state["selected_no_area"] = selected_area


@st.cache_data(show_spinner="Loading weather data...")
def load_weather(file_path: str) -> pd.DataFrame:
    data = pd.read_csv(file_path)
    required_columns = ["time", "temperature_2m", "precipitation", "point_id"]
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    data["time"] = pd.to_datetime(data["time"], errors="coerce")
    for column in ["temperature_2m", "precipitation"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["time"])
    return data.sort_values("time").reset_index(drop=True)


weather_file = weather_file_map[selected_area]
try:
    raw_data = load_weather(str(weather_file))
except Exception as error:
    st.error(f"Could not load weather data: {error}")
    st.stop()

if raw_data.empty:
    st.warning("The weather file contains no valid observations.")
    st.stop()

st.success(f"Successfully loaded {weather_file.name}: {len(raw_data):,} records.")

# Average measurements from all geographical points for each timestamp.
hourly_data = (
    raw_data.groupby("time", as_index=False)
    .agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        number_of_points=("point_id", "nunique"),
    )
)

if hourly_data.empty:
    st.warning("No hourly observations are available.")
    st.stop()

st.subheader("Dataset overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Hourly observations", f"{len(hourly_data):,}")
col2.metric("Geographical points", f"{raw_data['point_id'].nunique():,}")
col3.metric("Average temperature", f"{hourly_data['temperature_2m'].mean():.2f} °C")
col4.metric("Average hourly precipitation", f"{hourly_data['precipitation'].mean():.3f} mm")

st.subheader("Select time period")
min_date = hourly_data["time"].min().date()
max_date = hourly_data["time"].max().date()
date_range = st.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_data = hourly_data[
        hourly_data["time"].dt.date.between(start_date, end_date)
    ].copy()
else:
    filtered_data = hourly_data.copy()

if filtered_data.empty:
    st.warning("No observations were found for the selected period.")
    st.stop()

tab1, tab2 = st.tabs(["🌡️ Temperature", "🌧️ Precipitation"])

with tab1:
    st.subheader("Hourly temperature")
    fig_temp = px.line(
        filtered_data,
        x="time",
        y="temperature_2m",
        title=f"Hourly temperature - {selected_area}",
        labels={"time": "Date and time", "temperature_2m": "Temperature (°C)"},
    )
    fig_temp.update_layout(hovermode="x unified", xaxis_title="Date and time", yaxis_title="Temperature (°C)")
    st.plotly_chart(fig_temp, width="stretch")

    st.subheader("Temperature statistics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean temperature", f"{filtered_data['temperature_2m'].mean():.2f} °C")
    c2.metric("Minimum temperature", f"{filtered_data['temperature_2m'].min():.2f} °C")
    c3.metric("Maximum temperature", f"{filtered_data['temperature_2m'].max():.2f} °C")

with tab2:
    st.subheader("Hourly precipitation")
    fig_precip = px.bar(
        filtered_data,
        x="time",
        y="precipitation",
        title=f"Hourly precipitation - {selected_area}",
        labels={"time": "Date and time", "precipitation": "Precipitation (mm)"},
    )
    fig_precip.update_layout(hovermode="x unified", xaxis_title="Date and time", yaxis_title="Precipitation (mm)")
    st.plotly_chart(fig_precip, width="stretch")

    st.subheader("Precipitation statistics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean per hour", f"{filtered_data['precipitation'].mean():.3f} mm")
    c2.metric("Maximum per hour", f"{filtered_data['precipitation'].max():.2f} mm")
    c3.metric("Hours with precipitation", f"{(filtered_data['precipitation'] > 0).sum():,}")

st.divider()
st.subheader("Weather observations")
with st.expander("View hourly weather data"):
    st.dataframe(filtered_data, width="stretch", hide_index=True)
    csv_data = filtered_data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered data as CSV",
        data=csv_data,
        file_name=f"{selected_area}_weather_2024_filtered.csv",
        mime="text/csv",
    )

with st.expander("About this dataset"):
    st.markdown(
        """
        **Source:** Supplied IND320 project weather data.  
        **Frequency:** Hourly observations.  
        **Variables:**
        - `time`: Observation timestamp.
        - `temperature_2m`: Temperature at 2 metres (°C).
        - `precipitation`: Precipitation (mm).
        - `point_id`: Geographical measurement point.
        - `latitude` and `longitude`: Geographical coordinates, when present.

        Measurements from multiple geographical points are averaged for each timestamp.
        """
    )


