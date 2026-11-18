"""
Page 7: Time Series Analysis — IND320 Energy Dashboard.

Features:
    - STL decomposition of reservoir filling
    - Spectrogram analysis
    - Selectable Norwegian electricity area
    - Selectable seasonal period
    - Robust STL estimation
    - Interactive Plotly visualisations
    - Consistent application theme
    - Cached analytical calculations
    - Error handling
"""

import sys
from pathlib import Path

# --------------------------------------------------
# Application path
# --------------------------------------------------

APP_DIR = Path(__file__).resolve().parent.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# --------------------------------------------------
# Imports
# --------------------------------------------------

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL

from data_loader import load_data

# --------------------------------------------------
# Page title
# --------------------------------------------------

st.title("📉 Time Series Analysis")

st.write("""
    Analyse Norwegian reservoir filling using
    Seasonal-Trend decomposition (STL) and spectrograms.
    """)


# --------------------------------------------------
# Application theme
# --------------------------------------------------

TEXT_COLOR = "#18343B"
PRIMARY_COLOR = "#008C95"
GRID_COLOR = "rgba(0,140,149,0.12)"


def apply_plot_theme(fig, height=600):
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
            r=50,
            t=80,
            b=50,
        ),
        height=height,
        hovermode="x unified",
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


# --------------------------------------------------
# Load reservoir data
# --------------------------------------------------


@st.cache_data(ttl=3600, show_spinner="Loading reservoir data...")
def get_reservoir_data():
    """Load and prepare reservoir data."""

    data = load_data()

    required = {
        "date",
        "area_type",
        "area_nr",
        "fill_ratio",
    }

    missing = required - set(data.columns)

    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    data = data.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    data["area_nr"] = pd.to_numeric(
        data["area_nr"],
        errors="coerce",
    )

    data["fill_ratio"] = pd.to_numeric(
        data["fill_ratio"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "date",
            "area_nr",
            "fill_ratio",
        ]
    )

    data = data[data["area_type"].astype(str).str.strip().str.upper() == "NO"]

    return data.sort_values("date")


try:
    df = get_reservoir_data()

except Exception as error:
    st.error(f"Could not load reservoir data: {error}")
    st.stop()


if df.empty:
    st.warning("No Norwegian reservoir observations were found.")
    st.stop()


# --------------------------------------------------
# Select electricity area
# --------------------------------------------------

available_areas = sorted(df["area_nr"].astype(int).unique().tolist())

area_labels = [f"NO{number}" for number in available_areas]

if "selected_no_area" not in st.session_state:
    st.session_state["selected_no_area"] = area_labels[0]

saved_area = st.session_state["selected_no_area"]

if saved_area not in area_labels:
    saved_area = area_labels[0]


def save_area():
    st.session_state["selected_no_area"] = st.session_state["ts_area_widget"]


selected_area = st.selectbox(
    "Select electricity area",
    options=area_labels,
    index=area_labels.index(saved_area),
    key="ts_area_widget",
    on_change=save_area,
)

st.session_state["selected_no_area"] = selected_area

area_number = int(selected_area.replace("NO", ""))


# --------------------------------------------------
# Prepare weekly reservoir series
# --------------------------------------------------

area_data = df[df["area_nr"] == area_number].copy()

series = (
    area_data.set_index("date")["fill_ratio"]
    .sort_index()
    .resample("W-SUN")
    .mean()
    .interpolate(limit_direction="both")
    .dropna()
)


if len(series) < 20:
    st.warning("Not enough weekly observations for time-series analysis.")
    st.stop()


# --------------------------------------------------
# Dataset information
# --------------------------------------------------

st.caption(
    f"Selected area: {selected_area} | "
    f"{len(series):,} weekly observations | "
    f"Period: {series.index.min().date()} "
    f"to {series.index.max().date()}"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Observations",
    f"{len(series):,}",
)

col2.metric(
    "Mean filling level",
    f"{series.mean():.3f}",
)

col3.metric(
    "Standard deviation",
    f"{series.std():.3f}",
)


# --------------------------------------------------
# Analysis tabs
# --------------------------------------------------

st.divider()

stl_tab, spec_tab = st.tabs(
    [
        "📊 STL Analysis",
        "🌊 Spectrogram",
    ]
)


# ==================================================
# STL ANALYSIS
# ==================================================


@st.cache_data(show_spinner="Calculating STL decomposition...")
def calculate_stl(values, period, robust):
    """Calculate STL decomposition using the weekly observations."""

    # Use a simple positional index for the cached calculation.
    # The actual dates are applied later when plotting the components.
    input_series = pd.Series(values)

    result = STL(
        input_series,
        period=period,
        robust=robust,
    ).fit()

    return (
        result.observed.to_numpy(),
        result.trend.to_numpy(),
        result.seasonal.to_numpy(),
        result.resid.to_numpy(),
    )


with stl_tab:

    st.subheader("Seasonal-Trend decomposition using LOESS")

    st.write("""
        STL separates the reservoir filling time series
        into observed, trend, seasonal and residual components.
        """)

    col1, col2 = st.columns(2)

    with col1:

        period = st.number_input(
            "Seasonal period (weeks)",
            min_value=2,
            max_value=min(260, len(series) // 2),
            value=min(52, len(series) // 2),
            step=1,
            key="stl_period",
        )

    with col2:

        robust = st.checkbox(
            "Use robust STL estimation",
            value=True,
            key="stl_robust",
        )

    if st.button(
        "Run STL decomposition",
        type="primary",
        key="run_stl",
    ):

        if len(series) <= 2 * int(period):

            st.warning(
                "STL requires more than two seasonal periods. "
                "Choose a shorter period."
            )

        else:

            try:

                observed, trend, seasonal, residual = calculate_stl(
                    series.to_numpy(),
                    int(period),
                    robust,
                )

                components = [
                    ("Observed", observed),
                    ("Trend", trend),
                    ("Seasonal", seasonal),
                    ("Residual", residual),
                ]

                fig = go.Figure()

                for name, values in components:

                    fig.add_trace(
                        go.Scatter(
                            x=series.index,
                            y=values,
                            mode="lines",
                            name=name,
                            line=dict(width=2),
                        )
                    )

                fig.update_layout(
                    title="STL decomposition of reservoir filling",
                    xaxis_title="Date",
                    yaxis_title="Filling level",
                    legend=dict(
                        orientation="h",
                        y=1.12,
                    ),
                )

                fig = apply_plot_theme(
                    fig,
                    height=700,
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    theme=None,
                )

                # Component statistics
                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Trend standard deviation",
                    f"{np.std(trend):.4f}",
                )

                c2.metric(
                    "Seasonal standard deviation",
                    f"{np.std(seasonal):.4f}",
                )

                c3.metric(
                    "Residual standard deviation",
                    f"{np.std(residual):.4f}",
                )

            except Exception as error:

                st.error(f"STL analysis failed: {error}")


# ==================================================
# SPECTROGRAM ANALYSIS
# ==================================================


@st.cache_data(show_spinner="Calculating spectrogram...")
def calculate_spectrogram(
    values,
    window,
    overlap,
):
    """Calculate the spectrogram of reservoir filling."""

    frequencies, times, power = spectrogram(
        np.asarray(values),
        fs=52,
        window="hann",
        nperseg=window,
        noverlap=overlap,
        scaling="density",
    )

    return frequencies, times, power


with spec_tab:

    st.subheader("Reservoir filling spectrogram")

    st.write("""
        The spectrogram shows how the frequency content
        of reservoir filling changes over time.
        """)

    window = st.selectbox(
        "Window size (weeks)",
        options=[26, 52, 104],
        index=1,
        key="spectrogram_window",
    )

    overlap = st.slider(
        "Overlap (weeks)",
        min_value=0,
        max_value=window - 1,
        value=window // 2,
        key="spectrogram_overlap",
    )

    if st.button(
        "Run spectrogram",
        type="primary",
        key="run_spectrogram",
    ):

        if len(series) <= window:

            st.warning(
                "The selected window must be shorter " "than the available time series."
            )

        else:

            try:

                frequencies, times, power = calculate_spectrogram(
                    series.to_numpy(),
                    window,
                    overlap,
                )

                positive = frequencies > 0

                power_db = 10 * np.log10(power[positive, :] + 1e-12)

                fig = go.Figure(
                    data=go.Heatmap(
                        x=times / 52,
                        y=frequencies[positive],
                        z=power_db,
                        colorscale="Teal",
                        colorbar={
                            "title": "Power (dB)",
                        },
                        hovertemplate=(
                            "Time: %{x:.2f} years"
                            "<br>Frequency: %{y:.3f}"
                            "<br>Power: %{z:.2f} dB"
                            "<extra></extra>"
                        ),
                    )
                )

                fig.update_layout(
                    title="Reservoir filling spectrogram",
                    xaxis_title="Time from start (years)",
                    yaxis_title="Frequency (cycles per year)",
                )

                fig = apply_plot_theme(
                    fig,
                    height=550,
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    theme=None,
                )

                st.caption(
                    "A shorter window improves time resolution, "
                    "while a longer window improves frequency resolution."
                )

            except Exception as error:

                st.error(f"Spectrogram calculation failed: {error}")


# --------------------------------------------------
# About the analysis
# --------------------------------------------------

with st.expander("ℹ️ About these analyses"):

    st.markdown("""
        **STL decomposition**

        STL decomposes a time series into:
        - Observed component
        - Trend component
        - Seasonal component
        - Residual component

        **Spectrogram**

        A spectrogram displays the distribution of signal
        power across frequencies and time.

        **Data source**

        Norwegian reservoir statistics from the NVE
        Magasinstatistikk dataset.
        """)
