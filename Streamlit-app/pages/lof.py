from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent

DATA_PATH = PROJECT_DIR / "Notbook" / "Part4" / "RM_weather_2024.csv"

st.title("🔎 Local Outlier Factor (LOF)")
st.write(
    "Detect unusual observations in meteorological data "
    "using the Local Outlier Factor algorithm."
)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------


@st.cache_data
def load_weather_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Weather data file not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "time",
        "temperature_2m",
        "precipitation",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    for column in ["temperature_2m", "precipitation"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["time", "temperature_2m", "precipitation"])

    return df.sort_values("time")


try:
    weather = load_weather_data()

except Exception as exc:
    st.error(f"Could not load weather data: {exc}")
    st.stop()


if weather.empty:
    st.warning("No valid weather observations are available.")
    st.stop()


# ---------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------

st.sidebar.header("LOF settings")

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

analysis_data = weather[["time", weather_variable]].copy()

analysis_data = analysis_data.sort_values("time")

if len(analysis_data) > max_observations:
    analysis_data = analysis_data.sample(
        n=max_observations, random_state=42
    ).sort_values("time")

values = analysis_data[[weather_variable]].to_numpy()

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
                n_neighbors=n_neighbors, contamination=contamination
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

        st.dataframe(outliers.sort_values("lof_score"), use_container_width=True)

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
