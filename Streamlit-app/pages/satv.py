import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient

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
# MongoDB configuration
# --------------------------------------------------

# Load .env when python-dotenv is installed. Streamlit secrets are
# also supported for deployment.
try:
    from dotenv import load_dotenv

    project_root = Path(__file__).resolve().parents[2]
    for env_path in (project_root / ".env", Path.cwd() / ".env"):
        if env_path.exists():
            load_dotenv(env_path)
except ImportError:
    pass


def get_mongodb_uri():
    uri = os.getenv("MONGODB_URI")

    if not uri:
        try:
            uri = st.secrets["MONGODB_URI"]
        except Exception:
            uri = None

    if not uri:
        raise ValueError(
            "MONGODB_URI is missing. Add it to your .env file or Streamlit secrets."
        )

    return uri


# --------------------------------------------------
# Load weather data from MongoDB Atlas
# --------------------------------------------------

@st.cache_data(ttl=600)
def load_weather_data():
    client = None

    try:
        client = MongoClient(get_mongodb_uri(), serverSelectionTimeoutMS=10000)
        collection = client["ind320"]["weather_data"]

        documents = list(
            collection.find(
                {"region": {"$in": ["NO3", "RM"]}},
                {
                    "_id": 0,
                    "point_id": 1,
                    "region": 1,
                    "time": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "temperature_2m": 1,
                    "precipitation": 1,
                },
            )
        )

        if not documents:
            raise ValueError(
                "No weather observations were found in ind320.weather_data "
                "for regions NO3 or RM."
            )

        weather = pd.DataFrame(documents)

        required_columns = ["time", "temperature_2m", "precipitation", "region"]
        missing_columns = [
            column for column in required_columns if column not in weather.columns
        ]
        if missing_columns:
            raise ValueError(
                "MongoDB weather data is missing required fields: "
                + ", ".join(missing_columns)
            )

        # MongoDB values may be stored as ISO strings or datetime values.
        parsed_time = pd.to_datetime(weather["time"], errors="coerce", utc=True)
        weather["time"] = parsed_time.dt.tz_convert(None)

        for column in ("temperature_2m", "precipitation"):
            weather[column] = pd.to_numeric(weather[column], errors="coerce")

        weather["region"] = weather["region"].astype(str)
        weather = weather.dropna(subset=["time"])
        weather = weather[weather["region"].isin(["NO3", "RM"])]

        if weather.empty:
            raise ValueError("No valid weather observations were found.")

        return weather

    finally:
        if client is not None:
            client.close()


try:
    weather = load_weather_data()
except Exception as error:
    st.error(f"Could not load weather data from MongoDB: {error}")
    st.stop()

if weather.empty:
    st.warning("No weather observations are available.")
    st.stop()

# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------

st.sidebar.header("SATV Settings")

variable_labels = {
    "Temperature": "temperature_2m",
    "Precipitation": "precipitation",
}

selected_variable = st.sidebar.selectbox(
    "Select meteorological property",
    options=list(variable_labels.keys()),
    index=0,
)
variable = variable_labels[selected_variable]

available_regions = sorted(weather["region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox(
    "Select weather dataset",
    options=["All datasets"] + available_regions,
)

time_resolution = st.sidebar.selectbox(
    "Time resolution",
    options=["Daily", "Weekly", "Monthly"],
    index=0,
)

# --------------------------------------------------
# Filter dataset
# --------------------------------------------------

if selected_region != "All datasets":
    weather = weather[weather["region"] == selected_region].copy()

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

weather_data = weather_data.dropna().reset_index()
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
    f"Dataset: {selected_region} | "
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
    **Data source:** MongoDB Atlas, database `ind320`, collection `weather_data`.

    **Available datasets:** NO3 and RM.

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

