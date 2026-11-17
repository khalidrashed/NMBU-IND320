"""
Page 8: Data Quality Analysis — IND320 Energy Dashboard.

Features:
    - Precipitation outlier detection using DCT and SPC
    - Weather anomaly detection using Local Outlier Factor
    - Selectable meteorological variable for LOF
    - Selectable Norwegian electricity area
    - Interactive Plotly visualisations
    - Consistent application theme
    - Cached weather data
    - Error handling
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.title("🧪 Data Quality Analysis")

st.write("""
    Detect potential precipitation outliers and
    meteorological anomalies using statistical methods
    and machine learning.
    """)


# ==================================================
# 2. APPLICATION THEME
# ==================================================

TEXT_COLOR = "#18343B"
PRIMARY_COLOR = "#008C95"
GRID_COLOR = "rgba(0,140,149,0.12)"


def apply_plot_theme(fig, height=500):
    """Apply the common IND320 Plotly theme."""

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            color=TEXT_COLOR,
        ),
        margin=dict(
            l=50,
            r=40,
            t=80,
            b=50,
        ),
        hovermode="x unified",
        height=height,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
    )

    return fig


# ==================================================
# 3. FIND WEATHER DATA DIRECTORY
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEATHER_DIR = PROJECT_ROOT / "Notbook" / "Part3" / "data" / "weather"

if not WEATHER_DIR.exists():

    st.error("Weather data directory was not found.")

    st.code(str(WEATHER_DIR))

    st.info("Check that the weather data directory exists " "in the project structure.")

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

    st.stop()


# ==================================================
# 5. SELECT ELECTRICITY AREA
# ==================================================

default_area = "NO3" if "NO3" in available_areas else available_areas[0]

if (
    "selected_no_area" not in st.session_state
    or st.session_state["selected_no_area"] not in available_areas
):
    st.session_state["selected_no_area"] = default_area


def save_area():
    st.session_state["selected_no_area"] = st.session_state["quality_area_selection"]


selected_area = st.selectbox(
    "Select electricity area",
    options=available_areas,
    index=available_areas.index(st.session_state["selected_no_area"]),
    key="quality_area_selection",
    on_change=save_area,
)

st.session_state["selected_no_area"] = selected_area


# ==================================================
# 6. LOAD WEATHER DATA
# ==================================================


@st.cache_data(
    ttl=3600,
    show_spinner="Loading weather data...",
)
def load_weather(file_path):

    data = pd.read_csv(file_path)

    required_columns = [
        "time",
        "temperature_2m",
        "precipitation",
        "point_id",
    ]

    missing_columns = [
        column for column in required_columns if column not in data.columns
    ]

    if missing_columns:

        raise ValueError("Missing columns: " + ", ".join(missing_columns))

    data["time"] = pd.to_datetime(
        data["time"],
        errors="coerce",
    )

    for column in [
        "temperature_2m",
        "precipitation",
    ]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
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
# 7. AGGREGATE WEATHER DATA
# ==================================================

# Average measurements from geographical points
# for each timestamp.

weather = (
    raw_data.groupby("time", as_index=False)
    .agg(
        temperature_2m=("temperature_2m", "mean"),
        precipitation=("precipitation", "mean"),
        number_of_points=("point_id", "nunique"),
    )
    .sort_values("time")
)

st.success(f"Loaded {weather_file.name}: " f"{len(raw_data):,} hourly-point records.")


# ==================================================
# 8. DATASET SUMMARY
# ==================================================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Hourly observations",
    f"{len(weather):,}",
)

col2.metric(
    "Average temperature",
    f"{weather['temperature_2m'].mean():.2f} °C",
)

col3.metric(
    "Average precipitation",
    f"{weather['precipitation'].mean():.3f} mm",
)


st.caption(
    f"Area: {selected_area} | "
    f"Period: {weather['time'].min()} to {weather['time'].max()}"
)


# ==================================================
# 9. ANALYSIS SETTINGS
# ==================================================

st.sidebar.header("Analysis settings")

filter_coefficients = st.sidebar.slider(
    "DCT coefficients to remove",
    min_value=1,
    max_value=min(500, max(1, len(weather) - 1)),
    value=min(168, max(1, len(weather) - 1)),
    step=1,
)

mad_threshold = st.sidebar.slider(
    "SPC MAD threshold",
    min_value=2.0,
    max_value=10.0,
    value=3.5,
    step=0.5,
)

lof_contamination = st.sidebar.slider(
    "LOF contamination",
    min_value=0.001,
    max_value=0.10,
    value=0.01,
    step=0.001,
    format="%.3f",
)

lof_neighbors = st.sidebar.slider(
    "LOF number of neighbors",
    min_value=5,
    max_value=min(50, max(5, len(weather) - 1)),
    value=min(20, max(5, len(weather) - 1)),
)


# ==================================================
# 10. HELPER FUNCTIONS
# ==================================================


def high_pass_dct(series, remove_coefficients):
    """
    Apply DCT high-pass filtering.

    The first coefficients are removed to reduce
    low-frequency components.
    """

    values = series.interpolate(limit_direction="both").to_numpy(dtype=float)

    if len(values) < 4:

        raise ValueError("Not enough observations for DCT.")

    coefficients = dct(
        values,
        type=2,
        norm="ortho",
    )

    n_remove = min(
        remove_coefficients,
        len(coefficients) - 1,
    )

    coefficients[:n_remove] = 0

    filtered = idct(
        coefficients,
        type=2,
        norm="ortho",
    )

    return filtered


def robust_spc(values, threshold):
    """
    Calculate robust control limits using
    median and Median Absolute Deviation (MAD).
    """

    median = np.median(values)

    mad = np.median(np.abs(values - median))

    if mad == 0:

        return (
            median,
            median,
            median,
            np.zeros(len(values), dtype=bool),
        )

    robust_sigma = 1.4826 * mad

    upper_limit = median + threshold * robust_sigma

    lower_limit = median - threshold * robust_sigma

    outliers = (values > upper_limit) | (values < lower_limit)

    return (
        median,
        lower_limit,
        upper_limit,
        outliers,
    )


@st.cache_data(show_spinner="Running LOF anomaly detection...")
def detect_weather_anomalies(
    values,
    timestamps,
    neighbors,
    contamination,
):
    """Detect local anomalies using LOF."""

    data = pd.DataFrame(
        {
            "time": pd.to_datetime(timestamps),
            "value": values,
        }
    )

    data["value_change"] = data["value"].diff().fillna(0)

    X = data[["value", "value_change"]].to_numpy()

    lof = LocalOutlierFactor(
        n_neighbors=neighbors,
        contamination=contamination,
    )

    predictions = lof.fit_predict(X)

    data["lof_score"] = -lof.negative_outlier_factor_

    data["anomaly"] = predictions == -1

    data["status"] = np.where(
        data["anomaly"],
        "Anomaly",
        "Normal",
    )

    return data


# ==================================================
# 11. CREATE ANALYSIS TABS
# ==================================================

tab1, tab2 = st.tabs(
    [
        "🌧️ Precipitation Outliers (DCT + SPC)",
        "🌡️ Weather Anomalies (LOF)",
    ]
)


# ==================================================
# TAB 1: PRECIPITATION OUTLIERS
# ==================================================

with tab1:

    st.subheader("Precipitation outlier detection")

    st.write("""
        DCT high-pass filtering is used to examine
        short-term precipitation variations.
        Robust SPC limits are calculated using
        the median and MAD.
        """)

    precipitation_data = weather.dropna(subset=["precipitation"]).copy()

    if len(precipitation_data) < 4:

        st.warning("Not enough precipitation observations.")

    else:

        precipitation_values = precipitation_data["precipitation"].to_numpy(dtype=float)

        filtered_precipitation = high_pass_dct(
            precipitation_data["precipitation"],
            filter_coefficients,
        )

        median, lower, upper, outliers = robust_spc(
            filtered_precipitation,
            mad_threshold,
        )

        precipitation_data["filtered_precipitation"] = filtered_precipitation

        precipitation_data["outlier"] = outliers

        precipitation_data["status"] = np.where(
            outliers,
            "Potential outlier",
            "Normal",
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
                "precipitation": "Precipitation (mm)",
            },
        )

        fig_original = apply_plot_theme(fig_original)

        st.plotly_chart(
            fig_original,
            use_container_width=True,
            theme=None,
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
                "filtered_precipitation": "Filtered signal",
            },
        )

        fig_filtered.add_hline(
            y=median,
            line_dash="dash",
            annotation_text="Median",
        )

        fig_filtered.add_hline(
            y=upper,
            line_dash="dot",
            annotation_text="Upper control limit",
        )

        fig_filtered.add_hline(
            y=lower,
            line_dash="dot",
            annotation_text="Lower control limit",
        )

        fig_filtered = apply_plot_theme(fig_filtered)

        st.plotly_chart(
            fig_filtered,
            use_container_width=True,
            theme=None,
        )

        # SPC results

        st.markdown("### Statistical Process Control (SPC)")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Median",
            f"{median:.4f}",
        )

        c2.metric(
            "Upper control limit",
            f"{upper:.4f}",
        )

        c3.metric(
            "Potential outliers",
            f"{outliers.sum():,}",
        )

        # Highlight detected outliers

        fig_spc = px.scatter(
            precipitation_data,
            x="time",
            y="filtered_precipitation",
            color="status",
            color_discrete_map={
                "Normal": PRIMARY_COLOR,
                "Potential outlier": "#D1495B",
            },
            title="Detected precipitation outliers",
            labels={
                "time": "Date and time",
                "filtered_precipitation": "Filtered signal",
            },
        )

        fig_spc.add_hline(
            y=upper,
            line_dash="dash",
        )

        fig_spc.add_hline(
            y=lower,
            line_dash="dash",
        )

        fig_spc = apply_plot_theme(fig_spc)

        st.plotly_chart(
            fig_spc,
            use_container_width=True,
            theme=None,
        )

        # Outlier table

        st.markdown("### Detected precipitation outliers")

        detected = precipitation_data[precipitation_data["outlier"]]

        if detected.empty:

            st.info("No potential precipitation outliers detected.")

        else:

            st.dataframe(
                detected[
                    [
                        "time",
                        "precipitation",
                        "filtered_precipitation",
                        "status",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.caption("These are statistical flags, not confirmed measurement errors.")


# ==================================================
# TAB 2: WEATHER ANOMALIES USING LOF
# ==================================================

with tab2:

    st.subheader("Weather anomaly detection")

    st.write("""
        Local Outlier Factor (LOF) identifies observations
        that differ from their local neighbourhood.

        You can select the meteorological variable
        used by the anomaly detection algorithm.
        """)

    # Weather variable selector

    weather_variables = {
        "Temperature": {
            "column": "temperature_2m",
            "unit": "°C",
        },
        "Precipitation": {
            "column": "precipitation",
            "unit": "mm",
        },
    }

    selected_variable = st.selectbox(
        "Select meteorological variable",
        options=list(weather_variables.keys()),
        index=0,
        key="lof_weather_variable",
    )

    variable_info = weather_variables[selected_variable]

    variable_column = variable_info["column"]

    variable_unit = variable_info["unit"]

    temperature_data = weather.dropna(subset=[variable_column]).copy()

    temperature_data = temperature_data.sort_values("time")

    if len(temperature_data) <= lof_neighbors:

        st.warning(
            "Not enough observations for the selected " "number of LOF neighbours."
        )

    else:

        variable_values = temperature_data[variable_column].to_numpy(dtype=float)

        try:

            anomaly_data = detect_weather_anomalies(
                variable_values,
                temperature_data["time"].astype(str).tolist(),
                min(
                    lof_neighbors,
                    len(temperature_data) - 1,
                ),
                lof_contamination,
            )

            anomaly_data["original_value"] = variable_values

            anomaly_data["variable"] = selected_variable

            # Main weather time series

            st.markdown(f"### Hourly {selected_variable.lower()}")

            fig_weather = px.line(
                anomaly_data,
                x="time",
                y="original_value",
                title=f"Hourly {selected_variable.lower()}",
                labels={
                    "time": "Date and time",
                    "original_value": (f"{selected_variable} ({variable_unit})"),
                },
            )

            fig_weather = apply_plot_theme(fig_weather)

            st.plotly_chart(
                fig_weather,
                use_container_width=True,
                theme=None,
            )

            # LOF anomaly detection

            st.markdown("### LOF anomaly detection")

            fig_lof = px.scatter(
                anomaly_data,
                x="time",
                y="original_value",
                color="status",
                color_discrete_map={
                    "Normal": PRIMARY_COLOR,
                    "Anomaly": "#D1495B",
                },
                hover_data=[
                    "lof_score",
                    "value_change",
                ],
                title=(f"{selected_variable} anomalies detected by LOF"),
                labels={
                    "time": "Date and time",
                    "original_value": (f"{selected_variable} ({variable_unit})"),
                    "lof_score": "LOF score",
                },
            )

            fig_lof = apply_plot_theme(fig_lof)

            st.plotly_chart(
                fig_lof,
                use_container_width=True,
                theme=None,
            )

            # Statistics

            st.markdown("### Anomaly statistics")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total observations",
                f"{len(anomaly_data):,}",
            )

            c2.metric(
                "Detected anomalies",
                f"{anomaly_data['anomaly'].sum():,}",
            )

            c3.metric(
                "Anomaly percentage",
                f"{anomaly_data['anomaly'].mean() * 100:.2f}%",
            )

            # Anomaly table

            st.markdown("### Detected weather anomalies")

            anomalies = anomaly_data[anomaly_data["anomaly"]].sort_values(
                "lof_score",
                ascending=False,
            )

            if anomalies.empty:

                st.info("No weather anomalies detected.")

            else:

                st.dataframe(
                    anomalies[
                        [
                            "time",
                            "original_value",
                            "value_change",
                            "lof_score",
                            "status",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            st.caption(
                "LOF identifies unusual local patterns. "
                "Detected anomalies are not necessarily incorrect measurements."
            )

        except Exception as error:

            st.error(f"LOF analysis failed: {error}")


# ==================================================
# 12. DATA INFORMATION
# ==================================================

st.divider()

with st.expander("ℹ️ About this analysis"):

    st.markdown("""
        **Dataset:** Supplied IND320 weather observations.

        **Area:** Selected Norwegian electricity area.

        **Precipitation analysis:**
        - Discrete Cosine Transform (DCT).
        - High-pass filtering.
        - Median and Median Absolute Deviation (MAD).
        - Statistical Process Control (SPC).

        **Weather anomaly analysis:**
        - Local Outlier Factor (LOF).
        - Selectable temperature or precipitation.
        - Variable values and short-term changes.

        Statistical outliers and anomalies are potential
        unusual observations. They are not automatically
        incorrect measurements.

        **Data source:** Open-Meteo weather observations.
        """)
