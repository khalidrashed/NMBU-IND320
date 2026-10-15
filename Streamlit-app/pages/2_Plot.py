
"""
Page 3: Interactive Plot.

Features:
    - Download reservoir data directly from the NVE API
    - Radio buttons for EL, NO and VASS
    - Area-number filter
    - Select one numeric column or all numeric columns
    - Month-range slider
    - Interactive Plotly charts and small multiples
"""

import sys
from pathlib import Path

# Make the Streamlit-app folder available for imports if needed.
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# ---------------------------------------------------------------------------
# NVE API configuration.
# ---------------------------------------------------------------------------
NVE_API_URL = (
    "https://biapi.nve.no/magasinstatistikk/api/"
    "Magasinstatistikk/HentOffentligData"
)

NUMERIC_COLS = [
    "fill_ratio",
    "capacity_TWh",
    "filled_TWh",
    "fill_ratio_prev_week",
    "fill_ratio_change",
]


# ---------------------------------------------------------------------------
# Download and prepare NVE data.
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Downloading data from NVE...")
def load_nve_data():
    """Download reservoir statistics and standardise column names."""
    response = requests.get(NVE_API_URL, timeout=60)
    response.raise_for_status()

    data = pd.DataFrame(response.json())

    rename_map = {
        "dato_Id": "date",
        "omrType": "area_type",
        "omrnr": "area_nr",
        "iso_aar": "iso_year",
        "iso_uke": "iso_week",
        "fyllingsgrad": "fill_ratio",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "filled_TWh",
        "neste_Publiseringsdato": "next_publication",
        "fyllingsgrad_forrige_uke": "fill_ratio_prev_week",
        "endring_fyllingsgrad": "fill_ratio_change",
    }

    data = data.rename(columns=rename_map)

    if "date" not in data.columns or "area_type" not in data.columns:
        raise ValueError(
            "The NVE API response is missing the expected date "
            "or area_type column."
        )

    data["date"] = pd.to_datetime(data["date"], errors="coerce")

    for column in ["area_nr", "iso_year", "iso_week", *NUMERIC_COLS]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["date"])
    return data.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Page title and data loading.
# ---------------------------------------------------------------------------
st.title("📈 Interactive Plot")

try:
    df = load_nve_data()
except (requests.RequestException, ValueError, KeyError) as error:
    st.error(f"Could not load data from the NVE API: {error}")
    st.stop()

if df.empty:
    st.warning("The NVE API returned no usable data.")
    st.stop()

st.caption(
    f"Data source: NVE Magasinstatistikk API. "
    f"Available period: {df['date'].min().date()} to "
    f"{df['date'].max().date()}."
)


# ---------------------------------------------------------------------------
# Area type filters.
# Use the text values confirmed in the NVE API response.
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

area_type_choice = st.sidebar.radio(
    "Select area type",
    options=["EL", "NO", "VASS"],
)

df_type = df.loc[
    df["area_type"].astype(str).str.strip().str.upper()
    == area_type_choice
].copy()

if df_type.empty:
    st.warning(f"No data available for area type {area_type_choice}.")
    st.stop()

available_area_nrs = sorted(
    df_type["area_nr"].dropna().astype(int).unique().tolist()
)

area_nr_options = ["All"] + available_area_nrs

area_nr_choice = st.sidebar.selectbox(
    "Select area number",
    options=area_nr_options,
)

if area_nr_choice == "All":
    df_f = df_type.copy()
else:
    df_f = df_type.loc[
        df_type["area_nr"] == area_nr_choice
    ].copy()

if df_f.empty:
    st.warning("No data available for the selected area number.")
    st.stop()


# ---------------------------------------------------------------------------
# Month-range slider.
# Default: first available month only.
# ---------------------------------------------------------------------------
df_f["month"] = df_f["date"].dt.to_period("M").astype(str)
months = sorted(df_f["month"].dropna().unique().tolist())

if not months:
    st.warning("No dates available for the selected filters.")
    st.stop()

month_range = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[0]),
)

start_m, end_m = month_range

subset = df_f.loc[
    (df_f["month"] >= start_m)
    & (df_f["month"] <= end_m)
].copy()

st.caption(
    f"Showing {len(subset):,} rows from {start_m} to {end_m}. "
    f"Area type: {area_type_choice}; area number: {area_nr_choice}."
)

if subset.empty:
    st.warning("No data available for the selected month range.")
    st.stop()


# ---------------------------------------------------------------------------
# Numeric column selector.
# ---------------------------------------------------------------------------
numeric_cols = [
    column for column in NUMERIC_COLS
    if column in subset.columns
]

if not numeric_cols:
    st.warning("No numeric columns are available.")
    st.stop()

choice = st.selectbox(
    "Select column",
    options=["All numeric columns"] + numeric_cols,
)


# ---------------------------------------------------------------------------
# Main Plotly chart.
# ---------------------------------------------------------------------------
if choice == "All numeric columns":
    fig = go.Figure()

    # Left axis: fill ratios and weekly change.
    for column in [
        col for col in ["fill_ratio", "fill_ratio_prev_week"]
        if col in subset.columns
    ]:
        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                yaxis="y",
            )
        )

    if "fill_ratio_change" in subset.columns:
        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["fill_ratio_change"] * 100,
                mode="lines",
                name="fill_ratio_change × 100",
                yaxis="y",
                opacity=0.7,
            )
        )

    # Right axis: energy values in TWh.
    for column in [
        col for col in ["filled_TWh", "capacity_TWh"]
        if col in subset.columns
    ]:
        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                yaxis="y2",
            )
        )

    fig.update_layout(
        title=f"All numeric columns ({start_m} → {end_m})",
        xaxis_title="Date",
        yaxis=dict(
            title="Fill ratio (0–1), change × 100",
            side="left",
        ),
        yaxis2=dict(
            title="Energy (TWh)",
            overlaying="y",
            side="right",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
        ),
        hovermode="x unified",
        height=600,
    )

else:
    fig = px.line(
        subset,
        x="date",
        y=choice,
        title=f"{choice} ({start_m} → {end_m})",
        labels={"date": "Date", choice: choice},
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=choice,
        hovermode="x unified",
        height=600,
    )

st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Small multiples: one chart for each numeric column.
# ---------------------------------------------------------------------------
with st.expander("Show small multiples (one panel per numeric column)"):
    fig_sm = make_subplots(
        rows=len(numeric_cols),
        cols=1,
        shared_xaxes=True,
        subplot_titles=numeric_cols,
        vertical_spacing=0.03,
    )

    for i, column in enumerate(numeric_cols, start=1):
        fig_sm.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                line=dict(width=0.7),
            ),
            row=i,
            col=1,
        )

    fig_sm.update_layout(
        height=180 * len(numeric_cols) + 150,
        showlegend=False,
        title_text="Small multiples",
        xaxis_title="Date",
    )

    st.plotly_chart(fig_sm, use_container_width=True)


# ---------------------------------------------------------------------------
# Data source.
# ---------------------------------------------------------------------------
with st.expander("About the data source"):
    st.markdown(
        "Source: [NVE Magasinstatistikk API]"
        "(https://biapi.nve.no/magasinstatistikk/swagger/index.html). "
        "The response is cached for one hour. "
        "The month slider filters the downloaded data."
    )
