"""Part 4: Reservoir Statistics with shared electricity-area selection."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import load_data

# --------------------------------------------------
# Page title
# --------------------------------------------------

st.title("💧 Reservoir Statistics")

st.write("Explore reservoir filling statistics by Norwegian " "electricity area.")


# --------------------------------------------------
# Load data
# --------------------------------------------------

try:
    df = load_data()

except Exception as exc:
    st.error(f"Could not load reservoir data: {exc}")
    st.stop()


# --------------------------------------------------
# Validate columns
# --------------------------------------------------

required = {
    "date",
    "area_type",
    "area_nr",
}

missing = required - set(df.columns)

if missing:
    st.error(f"Missing required columns: " f"{', '.join(sorted(missing))}")
    st.stop()


# --------------------------------------------------
# Prepare data
# --------------------------------------------------

df = df.copy()

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["area_nr"] = pd.to_numeric(df["area_nr"], errors="coerce")

df["area_type"] = df["area_type"].astype(str).str.strip().str.upper()

df = df.dropna(subset=["date", "area_nr"])


# --------------------------------------------------
# Filter electricity areas
# --------------------------------------------------

# EL represents the five electricity areas.
# EL1 = NO1, EL2 = NO2, etc.

electricity_df = df[df["area_type"] == "EL"].copy()

if electricity_df.empty:
    st.error("No EL electricity-area observations were found.")
    st.stop()

available = sorted(electricity_df["area_nr"].astype(int).unique().tolist())

labels = [f"NO{x}" for x in available]


# --------------------------------------------------
# Shared selection with Interactive Map
# --------------------------------------------------

map_area = st.session_state.get("selected_area")

map_area_type = st.session_state.get("selected_area_type")

previous_area = st.session_state.get("selected_no_area", labels[0])

if map_area_type == "EL" and map_area in labels:
    saved = map_area

else:
    saved = previous_area

if saved not in labels:
    saved = labels[0]


# --------------------------------------------------
# Selection callback
# --------------------------------------------------


def save_area():

    selected_area = st.session_state["reservoir_area_widget"]

    st.session_state["selected_no_area"] = selected_area

    st.session_state["selected_area"] = selected_area

    st.session_state["selected_area_type"] = "EL"


# --------------------------------------------------
# Electricity area selector
# --------------------------------------------------

selected = st.selectbox(
    "Select electricity area",
    labels,
    index=labels.index(saved),
    key="reservoir_area_widget",
    on_change=save_area,
)

st.session_state["selected_no_area"] = selected
st.session_state["selected_area"] = selected
st.session_state["selected_area_type"] = "EL"


# --------------------------------------------------
# Filter selected electricity area
# --------------------------------------------------

area_nr = int(selected.replace("NO", ""))

area = electricity_df[electricity_df["area_nr"] == area_nr].sort_values("date")


if area.empty:
    st.warning(f"No observations are available for {selected}.")
    st.stop()


# --------------------------------------------------
# Latest reservoir statistics
# --------------------------------------------------

latest = area.iloc[-1]

c1, c2, c3 = st.columns(3)


if "fill_ratio" in area.columns:

    filling = latest["fill_ratio"]

    c1.metric(
        "Latest filling level",
        f"{filling:.1%}" if pd.notna(filling) else "N/A",
    )

else:
    c1.metric("Latest filling level", "N/A")


if "filled_TWh" in area.columns:

    filled = latest["filled_TWh"]

    c2.metric(
        "Filled energy",
        f"{filled:.2f} TWh" if pd.notna(filled) else "N/A",
    )

else:
    c2.metric("Filled energy", "N/A")


if "capacity_TWh" in area.columns:

    capacity = latest["capacity_TWh"]

    c3.metric(
        "Capacity",
        f"{capacity:.2f} TWh" if pd.notna(capacity) else "N/A",
    )

else:
    c3.metric("Capacity", "N/A")


# --------------------------------------------------
# Reservoir filling chart
# --------------------------------------------------

if "fill_ratio" in area.columns:

    fig = px.line(
        area,
        x="date",
        y="fill_ratio",
        title=f"{selected} Reservoir Filling Level",
        labels={
            "date": "Date",
            "fill_ratio": "Filling level",
        },
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Filling level",
        yaxis_tickformat=".0%",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# --------------------------------------------------
# Data period
# --------------------------------------------------

st.caption(
    f"Data period: " f"{area['date'].min().date()} " f"to {area['date'].max().date()}"
)


# --------------------------------------------------
# Data table
# --------------------------------------------------

with st.expander("View reservoir data"):

    st.dataframe(
        area,
        use_container_width=True,
    )
