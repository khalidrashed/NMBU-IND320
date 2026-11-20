from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(page_title="SATV Analysis", page_icon="🌦️", layout="wide")

st.title("🌦️ SATV – Weather Analysis")

st.markdown(
    "Explore meteorological observations using interactive "
    "time-series plots and statistical summaries."
)


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEATHER_DIR = PROJECT_ROOT / "Notbook" / "Part3" / "data" / "weather"


# --------------------------------------------------
# Load weather data
# --------------------------------------------------


@st.cache_data
def load_weather_data():

    files = list(WEATHER_DIR.glob("*_weather_2024.csv"))

    if not files:
        raise FileNotFoundError(f"No weather CSV files found in {WEATHER_DIR}")

    frames = []

    for file in files:

        try:
            df = pd.read_csv(file)

            required_columns = ["time", "temperature_2m", "precipitation"]

            if not all(col in df.columns for col in required_columns):
                continue

            df = df[required_columns].copy()

            df["time"] = pd.to_datetime(df["time"], errors="coerce")

            df["temperature_2m"] = pd.to_numeric(df["temperature_2m"], errors="coerce")

            df["precipitation"] = pd.to_numeric(df["precipitation"], errors="coerce")

            df["source_file"] = file.name

            df = df.dropna(subset=["time"])

            frames.append(df)

        except Exception:
            continue

    if not frames:
        raise ValueError("No valid weather datasets were found.")

    weather = pd.concat(frames, ignore_index=True)

    return weather


try:

    weather = load_weather_data()

except Exception as error:

    st.error(f"Could not load weather data: {error}")

    st.stop()


if weather.empty:

    st.warning("No weather observations are available.")

    st.stop()


# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------

st.sidebar.header("SATV Settings")

variable_labels = {"Temperature": "temperature_2m", "Precipitation": "precipitation"}

selected_variable = st.sidebar.selectbox(
    "Select meteorological property", options=list(variable_labels.keys()), index=0
)

variable = variable_labels[selected_variable]

selected_file = st.sidebar.selectbox(
    "Select weather dataset",
    options=["All datasets"] + sorted(weather["source_file"].unique()),
)

time_resolution = st.sidebar.selectbox(
    "Time resolution", options=["Daily", "Weekly", "Monthly"], index=0
)


# --------------------------------------------------
# Filter dataset
# --------------------------------------------------

if selected_file != "All datasets":

    weather = weather[weather["source_file"] == selected_file].copy()


weather = weather.sort_values("time")

weather = weather.dropna(subset=[variable])


if weather.empty:

    st.warning("No valid observations exist for the selected variable.")

    st.stop()


# --------------------------------------------------
# Aggregate data
# --------------------------------------------------

weather = weather.set_index("time")

if time_resolution == "Daily":

    weather_data = weather[variable].resample("D").mean()

elif time_resolution == "Weekly":

    weather_data = weather[variable].resample("W-SUN").mean()

else:

    weather_data = weather[variable].resample("ME").mean()


weather_data = weather_data.dropna()

weather_data = weather_data.reset_index()

weather_data.columns = ["time", variable]


if weather_data.empty:

    st.warning("No observations are available for this time resolution.")

    st.stop()


# --------------------------------------------------
# Units
# --------------------------------------------------

unit = "°C" if variable == "temperature_2m" else "mm"

variable_name = "Temperature" if variable == "temperature_2m" else "Precipitation"


# --------------------------------------------------
# Summary statistics
# --------------------------------------------------

st.subheader("Weather statistics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Observations", f"{len(weather_data):,}")

col2.metric(f"Average ({unit})", f"{weather_data[variable].mean():.2f}")

col3.metric(f"Maximum ({unit})", f"{weather_data[variable].max():.2f}")

col4.metric(f"Minimum ({unit})", f"{weather_data[variable].min():.2f}")


st.caption(
    f"Dataset: {selected_file} | "
    f"Resolution: {time_resolution} | "
    f"Period: {weather_data['time'].min().date()} "
    f"to {weather_data['time'].max().date()}"
)


# --------------------------------------------------
# Time series plot
# --------------------------------------------------

st.subheader(f"{time_resolution} {variable_name}")

fig = px.line(
    weather_data,
    x="time",
    y=variable,
    title=f"{time_resolution} {variable_name}",
    labels={"time": "Date", variable: f"{variable_name} ({unit})"},
)

fig.update_layout(
    template="plotly_white",
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title=f"{variable_name} ({unit})",
)

st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# Distribution plot
# --------------------------------------------------

st.subheader(f"{variable_name} distribution")

fig_distribution = px.histogram(
    weather_data,
    x=variable,
    nbins=40,
    title=f"Distribution of {variable_name}",
    labels={variable: f"{variable_name} ({unit})"},
)

fig_distribution.update_layout(template="plotly_white")

st.plotly_chart(fig_distribution, use_container_width=True)


# --------------------------------------------------
# Data preview
# --------------------------------------------------

with st.expander("Show aggregated weather data"):

    st.dataframe(weather_data, use_container_width=True)


# --------------------------------------------------
# Methodology
# --------------------------------------------------

with st.expander("Methodology and data information"):

    st.markdown("""
    **Data source:** Weather CSV files from Part 3.

    **Meteorological properties:**
    - Temperature (`temperature_2m`), measured in °C.
    - Precipitation (`precipitation`), measured in mm.

    **Aggregation:**
    - Daily: Mean of available observations per day.
    - Weekly: Mean of available observations per week.
    - Monthly: Mean of available observations per month.

    **Default property:** Temperature.

    Missing values are excluded from the aggregation.
    """)
