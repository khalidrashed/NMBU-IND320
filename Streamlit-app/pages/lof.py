import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient

from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

st.title("🔎 Local Outlier Factor (LOF)")
st.write(
    "Detect unusual observations in meteorological data "
    "using the Local Outlier Factor algorithm."
)


# ---------------------------------------------------------
# MongoDB configuration
# ---------------------------------------------------------

try:
    from dotenv import load_dotenv

    # Search common project locations for the local .env file.
    current_dir = Path(__file__).resolve().parent
    for env_path in (
        current_dir / ".env",
        current_dir.parent / ".env",
        current_dir.parent.parent / ".env",
        Path.cwd() / ".env",
    ):
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
            "MONGODB_URI is missing. Add it to your .env file "
            "or configure it in Streamlit secrets."
        )

    return uri


# ---------------------------------------------------------
# Load data from MongoDB Atlas
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def load_weather_data():
    client = None

    try:
        client = MongoClient(
            get_mongodb_uri(),
            serverSelectionTimeoutMS=10000,
        )
        collection = client["ind320"]["weather_data"]

        documents = list(
            collection.find(
                {"region": {"$in": ["NO3", "RM"]}},
                {
                    "_id": 0,
                    "time": 1,
                    "temperature_2m": 1,
                    "precipitation": 1,
                    "point_id": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "region": 1,
                },
            )
        )

        if not documents:
            raise ValueError(
                "No weather records found in ind320.weather_data "
                "for regions NO3 or RM."
            )

        df = pd.DataFrame(documents)

        required_columns = {
            "time",
            "temperature_2m",
            "precipitation",
            "region",
        }
        missing = required_columns - set(df.columns)
        if missing:
            raise ValueError(
                f"MongoDB weather data is missing columns: {', '.join(sorted(missing))}"
            )

        # Support MongoDB datetime values and ISO-formatted strings.
        parsed_time = pd.to_datetime(df["time"], errors="coerce", utc=True)
        df["time"] = parsed_time.dt.tz_convert(None)

        for column in ["temperature_2m", "precipitation"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df["region"] = df["region"].astype(str).str.upper()
        df = df[df["region"].isin(["NO3", "RM"])]
        df = df.dropna(
            subset=["time", "temperature_2m", "precipitation"]
        )

        if df.empty:
            raise ValueError("No valid weather observations are available.")

        return df.sort_values("time").reset_index(drop=True)

    finally:
        if client is not None:
            client.close()


try:
    weather = load_weather_data()
except Exception as exc:
    st.error(f"Could not load weather data from MongoDB: {exc}")
    st.stop()


if weather.empty:
    st.warning("No valid weather observations are available.")
    st.stop()


# ---------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------

st.sidebar.header("LOF settings")

available_regions = sorted(weather["region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox(
    "Weather dataset",
    ["All datasets"] + available_regions,
)

weather_variable = st.sidebar.selectbox(
    "Meteorological property",
    ["temperature_2m", "precipitation"],
    format_func=lambda x: {
        "temperature_2m": "Temperature (°C)",
        "precipitation": "Precipitation (mm)",
    }[x],
    index=0,
)

n_neighbors = st.sidebar.slider(
    "Number of neighbors", min_value=5, max_value=100, value=20
)

contamination = st.sidebar.slider(
    "Expected proportion of outliers",
    min_value=0.005,
    max_value=0.10,
    value=0.02,
    step=0.005,
    format="%.3f",
)

# Limit the number of observations to keep the app responsive.
max_observations = st.sidebar.selectbox(
    "Maximum observations", [5000, 10000, 20000, 50000], index=2
)

run_analysis = st.sidebar.button("Detect outliers", type="primary")


# ---------------------------------------------------------
# Prepare data
# ---------------------------------------------------------

if selected_region != "All datasets":
    weather = weather[weather["region"] == selected_region].copy()

analysis_data = weather[["time", weather_variable]].copy()
analysis_data = analysis_data.sort_values("time")
analysis_data = analysis_data.dropna(subset=[weather_variable])

if len(analysis_data) > max_observations:
    analysis_data = analysis_data.sample(
        n=max_observations, random_state=42
    ).sort_values("time")

values = analysis_data[[weather_variable]].to_numpy()

if analysis_data.empty:
    st.warning("No valid observations are available for the selected dataset and variable.")
    st.stop()

st.subheader("Weather data overview")

col1, col2, col3 = st.columns(3)

col1.metric("Observations", f"{len(analysis_data):,}")
col2.metric("Mean", f"{analysis_data[weather_variable].mean():.2f}")
col3.metric("Standard deviation", f"{analysis_data[weather_variable].std():.2f}")


# ---------------------------------------------------------
# Original weather plot
# ---------------------------------------------------------

fig_original = go.Figure()

fig_original.add_trace(
    go.Scatter(
        x=analysis_data["time"],
        y=analysis_data[weather_variable],
        mode="lines",
        name="Weather observations",
    )
)

fig_original.update_layout(
    title="Meteorological time series",
    xaxis_title="Time",
    yaxis_title=weather_variable,
    hovermode="x unified",
)

st.plotly_chart(fig_original, use_container_width=True)


# ---------------------------------------------------------
# Local Outlier Factor
# ---------------------------------------------------------

if run_analysis:

    if len(analysis_data) <= n_neighbors:
        st.error(
            "The number of observations must be greater "
            "than the number of neighbors."
        )
        st.stop()

    try:
        with st.spinner("Detecting unusual observations..."):

            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(values)

            lof_model = LocalOutlierFactor(
                n_neighbors=n_neighbors,
                contamination=contamination,
            )

            predictions = lof_model.fit_predict(scaled_values)
            scores = lof_model.negative_outlier_factor_

            results = analysis_data.copy()
            results["outlier"] = predictions == -1
            results["lof_score"] = scores

        st.success("LOF analysis completed.")

        # Metrics
        outliers = results[results["outlier"]].copy()
        outlier_count = len(outliers)
        outlier_percentage = outlier_count / len(results) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Detected outliers", f"{outlier_count:,}")
        c2.metric("Outlier percentage", f"{outlier_percentage:.2f}%")
        c3.metric("Normal observations", f"{len(results) - outlier_count:,}")

        # Plot results
        fig = go.Figure()
        normal = results[~results["outlier"]]

        fig.add_trace(
            go.Scatter(
                x=normal["time"],
                y=normal[weather_variable],
                mode="markers",
                name="Normal observations",
                marker=dict(size=4),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=outliers["time"],
                y=outliers[weather_variable],
                mode="markers",
                name="Detected outliers",
                marker=dict(size=8, symbol="x"),
            )
        )

        fig.update_layout(
            title="Local Outlier Factor – detected anomalies",
            xaxis_title="Time",
            yaxis_title=weather_variable,
            hovermode="closest",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Outlier table
        st.subheader("Detected unusual observations")
        st.dataframe(
            outliers.sort_values("lof_score"),
            use_container_width=True,
        )

        # Download
        st.download_button(
            "Download outlier results",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name="lof_weather_results.csv",
            mime="text/csv",
        )

    except Exception as exc:
        st.error(f"LOF analysis failed: {exc}")


# ---------------------------------------------------------
# Methodology
# ---------------------------------------------------------

with st.expander("Methodology and limitations"):
    st.markdown("""
    **Algorithm:** Local Outlier Factor (LOF).

    **Data source:** MongoDB Atlas, database `ind320`,
    collection `weather_data`.

    **Available datasets:** NO3 and RM.

    **Input:** Selected meteorological variable.

    **Temperature:** Temperature observations in degrees Celsius.

    **Precipitation:** Hourly precipitation observations in millimetres.

    **Number of neighbors:** Determines how many nearby observations
    are used to estimate local density.

    **Contamination:** Expected proportion of outliers used by the
    algorithm to determine the decision threshold.

    **Interpretation:** LOF identifies observations with substantially
    lower local density than their neighbors.

    **Important limitation:** This implementation uses one
    meteorological variable at a time. LOF identifies unusual values,
    but an unusual observation is not necessarily an erroneous
    measurement or a meteorological event.
    """)


