"""Part 3: Reservoir statistics and shared electricity-area selector."""
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st
from data_loader import load_data

st.title("💧 Reservoir Statistics")
st.write("Explore reservoir filling statistics by Norwegian electricity area.")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Could not load reservoir data: {exc}")
    st.stop()

required = {"date", "area_type", "area_nr"}
missing = required - set(df.columns)
if missing:
    st.error(f"Missing required columns: {', '.join(sorted(missing))}")
    st.stop()

df = df.copy()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["area_nr"] = pd.to_numeric(df["area_nr"], errors="coerce")
df = df.dropna(subset=["date", "area_nr"])

no_df = df[df["area_type"].astype(str).str.strip().str.upper() == "NO"].copy()
available = sorted(no_df["area_nr"].astype(int).unique().tolist())
if not available:
    st.warning("No NO-area observations were found in the reservoir dataset.")
    st.stop()

labels = [f"NO{x}" for x in available]
saved = st.session_state.get("selected_no_area", labels[0])
if saved not in labels:
    saved = labels[0]

def save_area():
    st.session_state["selected_no_area"] = st.session_state["reservoir_area_widget"]

selected = st.selectbox(
    "Select electricity area",
    labels,
    index=labels.index(saved),
    key="reservoir_area_widget",
    on_change=save_area,
)
st.session_state["selected_no_area"] = selected
area_nr = int(selected.replace("NO", ""))
area = no_df[no_df["area_nr"] == area_nr].sort_values("date")

if area.empty:
    st.info("No observations are available for this area.")
    st.stop()

latest = area.iloc[-1]
c1, c2, c3 = st.columns(3)
c1.metric("Latest filling level", f"{latest['fill_ratio']:.1%}" if pd.notna(latest.get("fill_ratio")) else "N/A")
c2.metric("Filled energy", f"{latest['filled_TWh']:.2f} TWh" if pd.notna(latest.get("filled_TWh")) else "N/A")
c3.metric("Capacity", f"{latest['capacity_TWh']:.2f} TWh" if pd.notna(latest.get("capacity_TWh")) else "N/A")

if "fill_ratio" in area.columns:
    fig = px.line(area, x="date", y="fill_ratio", title=f"{selected} reservoir filling level")
    fig.update_layout(xaxis_title="Date", yaxis_title="Filling level")
    st.plotly_chart(fig, use_container_width=True)

st.caption(f"Data period: {area['date'].min().date()} to {area['date'].max().date()}")
st.dataframe(area, use_container_width=True)
