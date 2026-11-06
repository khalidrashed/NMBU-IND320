
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Quality Analysis",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Data Quality Analysis")

st.write(
    "Detect potential precipitation outliers "
    "and temperature anomalies."
)


# ==================================================
# 2. FIND WEATHER DATA DIRECTORY
# ==================================================

# Project structure:
# IND320/
# ├── Notbook/
# │   └── Part3/data/weather/
# └── Streamlit-app/
#     └── pages/8_Data_Quality_Analysis.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEATHER_DIR = (
    PROJECT_ROOT
    / "Notbook"
    / "Part3"
    / "data"
    / "weather"
)

if not WEATHER_DIR.exists():
    st.error("Weather data directory was not found.")
    st.code(str(WEATHER_DIR))
    st.stop()


# ==================================================
# 3. FIND AVAILABLE WEATHER FILES
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

    st.stop()


# ==================================================
# 4. SELECT AREA
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
    key="quality_area_selection"
)

st.session_state["selected_no_area"] = selected_area


# ==================================================
# 5. LOAD WEATHER DATA
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
        col for col in required_columns
        if col not in data.columns
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


# ==================================================
# 6. AGGREGATE WEATHER DATA
# ==================================================

# Average measurements from geographical points
# for each timestamp.

weather = (
    raw_data.groupby("time", as_index=False)
    .agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        number_of_points=("point_id", "nunique")
    )
    .sort_values("time")
)

st.success(
    f"Loaded {weather_file.name}: "
    f"{len(raw_data):,} hourly-point records."
)

col1, col2, col3 = st.columns(3)

col1.metric("Hourly observations", f"{len(weather):,}")

col2.metric(
    "Average temperature",
    f"{weather['temperature_2m'].mean():.2f} °C"
)

col3.metric(
    "Average precipitation",
    f"{weather['precipitation'].mean():.3f} mm"
)


# ==================================================
# 7. ANALYSIS SETTINGS
# ==================================================

st.sidebar.header("Analysis settings")

filter_coefficients = st.sidebar.slider(
    "DCT coefficients to remove",
    min_value=1,
    max_value=500,
    value=168,
    step=1
)

mad_threshold = st.sidebar.slider(
    "SPC MAD threshold",
    min_value=2.0,
    max_value=10.0,
    value=3.5,
    step=0.5
)

lof_contamination = st.sidebar.slider(
    "LOF contamination",
    min_value=0.001,
    max_value=0.10,
    value=0.01,
    step=0.001,
    format="%.3f"
)

lof_neighbors = st.sidebar.slider(
    "LOF number of neighbors",
    min_value=5,
    max_value=50,
    value=20
)


# ==================================================
# 8. HELPER FUNCTIONS
# ==================================================

def high_pass_dct(series, remove_coefficients):

    """
    Apply DCT high-pass filtering.

    The first coefficients are removed to reduce
    low-frequency components.
    """

    values = series.interpolate(
        limit_direction="both"
    ).to_numpy(dtype=float)

    if len(values) < 4:
        raise ValueError("Not enough observations for DCT.")

    coefficients = dct(values, type=2, norm="ortho")

    n_remove = min(
        remove_coefficients,
        len(coefficients) - 1
    )

    coefficients[:n_remove] = 0

    filtered = idct(
        coefficients,
        type=2,
        norm="ortho"
    )

    return filtered


def robust_spc(values, threshold):

    """
    Calculate robust control limits using
    median and Median Absolute Deviation (MAD).
    """

    median = np.median(values)

    mad = np.median(
        np.abs(values - median)
    )

    if mad == 0:
        return median, median, median, np.zeros(len(values), dtype=bool)

    robust_sigma = 1.4826 * mad

    upper_limit = median + threshold * robust_sigma
    lower_limit = median - threshold * robust_sigma

    outliers = (
        (values > upper_limit)
        | (values < lower_limit)
    )

    return median, lower_limit, upper_limit, outliers


# ==================================================
# 9. CREATE ANALYSIS TABS
# ==================================================

tab1, tab2 = st.tabs([
    "🌧️ Precipitation Outliers (DCT + SPC)",
    "🌡️ Temperature Anomalies (LOF)"
])


# ==================================================
# TAB 1: PRECIPITATION OUTLIERS
# ==================================================

with tab1:

    st.subheader("Precipitation outlier detection")

    st.write(
        "DCT high-pass filtering is used to examine "
        "short-term precipitation variations. "
        "Robust SPC limits are calculated using "
        "the median and MAD."
    )

    precipitation_data = weather.dropna(
        subset=["precipitation"]
    ).copy()

    if len(precipitation_data) < 4:

        st.warning("Not enough precipitation observations.")
    
    else:

        precipitation_values = (
            precipitation_data["precipitation"]
            .to_numpy(dtype=float)
        )

        filtered_precipitation = high_pass_dct(
            precipitation_data["precipitation"],
            filter_coefficients
        )

        median, lower, upper, outliers = robust_spc(
            filtered_precipitation,
            mad_threshold
        )

        precipitation_data["filtered_precipitation"] = (
            filtered_precipitation
        )

        precipitation_data["outlier"] = outliers

        precipitation_data["status"] = np.where(
            outliers,
            "Potential outlier",
            "Normal"
        )

        # Original precipitation
        st.markdown("### Original precipitation")

        fig_original = px.line(
            precipitation_data,
            x="time",
            y="precipitation",
            title="Original hourly precipitation",
            labels={
                "time": "Date and time",
                "precipitation": "Precipitation (mm)"
            }
        )

        st.plotly_chart(
            fig_original,
            use_container_width=True
        )

        # Filtered precipitation
        st.markdown("### DCT high-pass filtered signal")

        fig_filtered = px.line(
            precipitation_data,
            x="time",
            y="filtered_precipitation",
            title="High-pass filtered precipitation",
            labels={
                "time": "Date and time",
                "filtered_precipitation": "Filtered signal"
            }
        )

        fig_filtered.add_hline(
            y=median,
            line_dash="dash",
            annotation_text="Median"
        )

        fig_filtered.add_hline(
            y=upper,
            line_dash="dot",
            annotation_text="Upper control limit"
        )

        fig_filtered.add_hline(
            y=lower,
            line_dash="dot",
            annotation_text="Lower control limit"
        )

        st.plotly_chart(
            fig_filtered,
            use_container_width=True
        )

        # SPC results
        st.markdown("### Statistical Process Control (SPC)")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Median",
            f"{median:.4f}"
        )

        c2.metric(
            "Upper control limit",
            f"{upper:.4f}"
        )

        c3.metric(
            "Potential outliers",
            f"{outliers.sum():,}"
        )

        # Highlight detected outliers
        fig_spc = px.scatter(
            precipitation_data,
            x="time",
            y="filtered_precipitation",
            color="status",
            color_discrete_map={
                "Normal": "blue",
                "Potential outlier": "red"
            },
            title="Detected precipitation outliers",
            labels={
                "time": "Date and time",
                "filtered_precipitation": "Filtered signal"
            }
        )

        fig_spc.add_hline(
            y=upper,
            line_dash="dash"
        )

        fig_spc.add_hline(
            y=lower,
            line_dash="dash"
        )

        st.plotly_chart(
            fig_spc,
            use_container_width=True
        )

        st.markdown("### Detected precipitation outliers")

        detected = precipitation_data[
            precipitation_data["outlier"]
        ]

        if detected.empty:

            st.info("No potential precipitation outliers detected.")

        else:

            st.dataframe(
                detected[
                    [
                        "time",
                        "precipitation",
                        "filtered_precipitation",
                        "status"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "These are statistical flags, not confirmed measurement errors."
        )


# ==================================================
# TAB 2: TEMPERATURE ANOMALIES USING LOF
# ==================================================

with tab2:

    st.subheader("Temperature anomaly detection")

    st.write(
        "Local Outlier Factor (LOF) identifies observations "
        "that differ from their local neighbourhood."
    )

    temperature_data = weather.dropna(
        subset=["temperature_2m"]
    ).copy()

    if len(temperature_data) <= lof_neighbors:

        st.warning(
            "Not enough temperature observations for the "
            "selected number of LOF neighbours."
        )

    else:

        temperature_values = (
            temperature_data["temperature_2m"]
            .to_numpy(dtype=float)
        )

        # Use temperature and short-term change
        temperature_data["temperature_change"] = (
            temperature_data["temperature_2m"].diff()
        )

        temperature_data["temperature_change"] = (
            temperature_data["temperature_change"].fillna(0)
        )

        X = temperature_data[
            [
                "temperature_2m",
                "temperature_change"
            ]
        ].to_numpy()

        # Local Outlier Factor
        lof = LocalOutlierFactor(
            n_neighbors=min(
                lof_neighbors,
                len(temperature_data) - 1
            ),
            contamination=lof_contamination
        )

        predictions = lof.fit_predict(X)

        temperature_data["lof_score"] = (
            -lof.negative_outlier_factor_
        )

        temperature_data["anomaly"] = predictions == -1

        temperature_data["status"] = np.where(
            temperature_data["anomaly"],
            "Anomaly",
            "Normal"
        )

        # Temperature time series
        st.markdown("### Hourly temperature")

        fig_temperature = px.line(
            temperature_data,
            x="time",
            y="temperature_2m",
            title="Hourly temperature",
            labels={
                "time": "Date and time",
                "temperature_2m": "Temperature (°C)"
            }
        )

        st.plotly_chart(
            fig_temperature,
            use_container_width=True
        )

        # LOF anomaly detection
        st.markdown("### LOF anomaly detection")

        fig_lof = px.scatter(
            temperature_data,
            x="time",
            y="temperature_2m",
            color="status",
            color_discrete_map={
                "Normal": "blue",
                "Anomaly": "red"
            },
            hover_data=["lof_score", "temperature_change"],
            title="Temperature anomalies detected by LOF",
            labels={
                "time": "Date and time",
                "temperature_2m": "Temperature (°C)"
            }
        )

        st.plotly_chart(
            fig_lof,
            use_container_width=True
        )

        # LOF statistics
        st.markdown("### Anomaly statistics")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total observations",
            f"{len(temperature_data):,}"
        )

        c2.metric(
            "Detected anomalies",
            f"{temperature_data['anomaly'].sum():,}"
        )

        c3.metric(
            "Anomaly percentage",
            f"{temperature_data['anomaly'].mean() * 100:.2f}%"
        )

        # Anomaly table
        st.markdown("### Detected temperature anomalies")

        anomalies = temperature_data[
            temperature_data["anomaly"]
        ].sort_values(
            "lof_score",
            ascending=False
        )

        if anomalies.empty:

            st.info("No temperature anomalies detected.")

        else:

            st.dataframe(
                anomalies[
                    [
                        "time",
                        "temperature_2m",
                        "temperature_change",
                        "lof_score",
                        "status"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "LOF identifies unusual local patterns. "
            "Detected anomalies are not necessarily incorrect measurements."
        )


# ==================================================
# 10. DATA INFORMATION
# ==================================================

st.divider()

with st.expander("About this analysis"):

    st.write("""
    **Dataset:** Supplied IND320 weather observations.

    **Area:** Selected Norwegian electricity area.

    **Precipitation analysis:**
    - Discrete Cosine Transform (DCT).
    - High-pass filtering.
    - Median and Median Absolute Deviation (MAD).
    - Statistical Process Control (SPC).

    **Temperature analysis:**
    - Local Outlier Factor (LOF).
    - Temperature and short-term temperature changes.

    Statistical outliers and anomalies are potential
    unusual observations. They are not automatically
    confirmed data errors.
    """)
