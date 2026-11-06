"""Part 3: STL and spectrogram analyses of reservoir filling data."""
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL
from data_loader import load_data

st.title("📉 Time Series Analysis")
st.write("Analyse reservoir filling using STL decomposition and spectrograms.")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Could not load reservoir data: {exc}")
    st.stop()

required = {"date", "area_type", "area_nr", "fill_ratio"}
missing = required - set(df.columns)
if missing:
    st.error(f"Missing required columns: {', '.join(sorted(missing))}")
    st.stop()

df = df.copy()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["area_nr"] = pd.to_numeric(df["area_nr"], errors="coerce")
df["fill_ratio"] = pd.to_numeric(df["fill_ratio"], errors="coerce")
df = df.dropna(subset=["date", "area_nr", "fill_ratio"])
df = df[df["area_type"].astype(str).str.strip().str.upper() == "NO"]

available = sorted(df["area_nr"].astype(int).unique().tolist())
if not available:
    st.warning("No NO-area reservoir observations found.")
    st.stop()

labels = [f"NO{x}" for x in available]
saved = st.session_state.get("selected_no_area", labels[0])
if saved not in labels:
    saved = labels[0]

def save_area():
    st.session_state["selected_no_area"] = st.session_state["ts_area_widget"]

selected = st.selectbox(
    "Electricity area",
    labels,
    index=labels.index(saved),
    key="ts_area_widget",
    on_change=save_area,
)
st.session_state["selected_no_area"] = selected
area_nr = int(selected.replace("NO", ""))
series = (
    df[df["area_nr"] == area_nr]
    .set_index("date")["fill_ratio"]
    .sort_index()
    .resample("W-SUN")
    .mean()
    .interpolate(limit_direction="both")
    .dropna()
)

if len(series) < 20:
    st.warning("Not enough weekly observations for time-series analysis.")
    st.stop()

st.caption(f"{len(series):,} weekly observations, {series.index.min().date()} to {series.index.max().date()}.")

stl_tab, spec_tab = st.tabs(["STL Analysis", "Spectrogram"])

with stl_tab:
    st.subheader("Seasonal-Trend decomposition using LOESS")
    period = st.number_input("Seasonal period (weeks)", min_value=2, max_value=260, value=52, step=1)
    robust = st.checkbox("Use robust STL estimation", value=True)
    if len(series) <= 2 * int(period):
        st.warning("STL needs more than two seasonal periods. Choose a shorter period or an area with more data.")
    elif st.button("Run STL", key="run_stl"):
        result = STL(series, period=int(period), robust=robust).fit()
        fig = go.Figure()
        for name, values in [
            ("Observed", series),
            ("Trend", result.trend),
            ("Seasonal", result.seasonal),
            ("Residual", result.resid),
        ]:
            fig.add_trace(go.Scatter(x=values.index, y=values.values, mode="lines", name=name))
        fig.update_layout(title="STL components", xaxis_title="Date", yaxis_title="Filling level", height=700)
        st.plotly_chart(fig, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Trend standard deviation", f"{result.trend.std():.4f}")
        c2.metric("Seasonal standard deviation", f"{result.seasonal.std():.4f}")
        c3.metric("Residual standard deviation", f"{result.resid.std():.4f}")

with spec_tab:
    st.subheader("Spectrogram")
    window = st.selectbox("Window size (weeks)", [26, 52, 104], index=1)
    overlap = st.slider("Overlap (weeks)", min_value=0, max_value=window - 1, value=window // 2)
    if len(series) <= window:
        st.warning("The selected window must be shorter than the available time series.")
    elif st.button("Run spectrogram", key="run_spectrogram"):
        frequencies, times, power = spectrogram(
            series.to_numpy(), fs=52, window="hann",
            nperseg=window, noverlap=overlap, scaling="density"
        )
        positive = frequencies > 0
        fig = go.Figure(data=go.Heatmap(
            x=times, y=frequencies[positive],
            z=10 * np.log10(power[positive, :] + 1e-12),
            colorbar={"title": "Power (dB)"},
        ))
        fig.update_layout(
            title="Reservoir filling spectrogram",
            xaxis_title="Time from start (years)",
            yaxis_title="Frequency (cycles per year)",
            height=550,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("A shorter window improves time resolution; a longer window improves frequency resolution.")
