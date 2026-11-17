"""
Page 3: Interactive Plot — IND320 Energy Dashboard.

Features:
    - Download reservoir data directly from the NVE API
    - Radio buttons for EL, NO and VASS
    - Area-number filter
    - Select one numeric column or all numeric columns
    - Month-range slider
    - Interactive Plotly charts and small multiples
    - Consistent application theme
    - Shared session state for selected area and date range
    - Error handling and cached API requests
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

import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from plotly.subplots import make_subplots

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.title("📈 Interactive Plot")

st.write("""
    Explore historical Norwegian reservoir statistics
    using interactive Plotly visualisations.
    """)


# --------------------------------------------------
# Theme configuration
# --------------------------------------------------

PLOT_TEMPLATE = "plotly_white"

TEXT_COLOR = "#18343B"
PRIMARY_COLOR = "#008C95"
GRID_COLOR = "rgba(0,140,149,0.12)"


def apply_plot_theme(fig, height=600):
    """Apply the common IND320 application theme."""

    fig.update_layout(
        template=PLOT_TEMPLATE,
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
        hovermode="x unified",
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
    )

    return fig


# --------------------------------------------------
# NVE API configuration
# --------------------------------------------------

NVE_API_URL = (
    "https://biapi.nve.no/magasinstatistikk/api/" "Magasinstatistikk/HentOffentligData"
)

NUMERIC_COLS = [
    "fill_ratio",
    "capacity_TWh",
    "filled_TWh",
    "fill_ratio_prev_week",
    "fill_ratio_change",
]

RENAME_MAP = {
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


# --------------------------------------------------
# Download and prepare NVE data
# --------------------------------------------------


@st.cache_data(
    ttl=3600,
    show_spinner="Downloading reservoir data from NVE...",
)
def load_nve_data():
    """
    Download reservoir statistics from the NVE API
    and standardise column names.
    """

    response = requests.get(
        NVE_API_URL,
        timeout=60,
    )

    response.raise_for_status()

    data = pd.DataFrame(response.json())

    if data.empty:
        return data

    data = data.rename(columns=RENAME_MAP)

    required_columns = [
        "date",
        "area_type",
        "area_nr",
    ]

    missing_columns = [
        column for column in required_columns if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required NVE columns: {missing_columns}")

    # Convert dates
    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
    )

    # Convert numerical columns
    for column in [
        "area_nr",
        "iso_year",
        "iso_week",
        *NUMERIC_COLS,
    ]:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

    # Remove invalid dates
    data = data.dropna(subset=["date"])

    # Sort chronologically
    data = data.sort_values("date").reset_index(drop=True)

    return data


# --------------------------------------------------
# Load data with error handling
# --------------------------------------------------

try:

    df = load_nve_data()

except requests.exceptions.Timeout:

    st.error("The connection to the NVE API timed out. " "Please try again later.")

    st.stop()

except requests.exceptions.RequestException as error:

    st.error(f"Could not connect to the NVE API: {error}")

    st.stop()

except (ValueError, KeyError) as error:

    st.error(f"Could not process NVE data: {error}")

    st.stop()

except Exception as error:

    st.error(f"Unexpected error while loading data: {error}")

    st.stop()


if df.empty:

    st.warning("The NVE API returned no usable data.")

    st.stop()


# --------------------------------------------------
# Data source information
# --------------------------------------------------

st.caption(
    f"Source: NVE Magasinstatistikk API | "
    f"Available period: {df['date'].min().date()} "
    f"to {df['date'].max().date()}"
)


# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------

st.sidebar.header("📊 Plot filters")


# Area type
area_type_choice = st.sidebar.radio(
    "Select area type",
    options=["EL", "NO", "VASS"],
    key="plot_area_type",
)


# Filter by area type
df_type = df.loc[
    df["area_type"].astype(str).str.strip().str.upper() == area_type_choice
].copy()


if df_type.empty:

    st.warning(f"No data available for area type {area_type_choice}.")

    st.stop()


# Available area numbers
available_area_nrs = sorted(df_type["area_nr"].dropna().astype(int).unique().tolist())


area_nr_options = ["All"] + available_area_nrs


# Shared selected area
if "selected_area" not in st.session_state:
    st.session_state.selected_area = "EL1"


# Convert area number to the shared area identifier
default_area_nr = "All"

if area_type_choice == "EL":

    selected_area = str(st.session_state.selected_area)

    if selected_area.startswith("EL"):

        try:
            possible_area_nr = int(selected_area.replace("EL", ""))

            if possible_area_nr in available_area_nrs:
                default_area_nr = possible_area_nr

        except ValueError:
            pass


# Area selector
area_nr_choice = st.sidebar.selectbox(
    "Select area number",
    options=area_nr_options,
    index=area_nr_options.index(default_area_nr),
)


# Update shared area selection
if area_nr_choice != "All":

    st.session_state.selected_area = f"{area_type_choice}{int(area_nr_choice)}"


# Apply area filter
if area_nr_choice == "All":

    df_f = df_type.copy()

else:

    df_f = df_type.loc[df_type["area_nr"] == area_nr_choice].copy()


if df_f.empty:

    st.warning("No data available for the selected area.")

    st.stop()


# --------------------------------------------------
# Month selector
# --------------------------------------------------

df_f["month"] = df_f["date"].dt.to_period("M").astype(str)

months = sorted(df_f["month"].dropna().unique().tolist())


if not months:

    st.warning("No valid dates available for the selected filters.")

    st.stop()


# Default to the complete available period
month_range = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[-1]),
    key="plot_month_range",
)


start_month, end_month = month_range


# Filter selected period
subset = df_f.loc[(df_f["month"] >= start_month) & (df_f["month"] <= end_month)].copy()


if subset.empty:

    st.warning("No data available for the selected month range.")

    st.stop()


# Update shared date range
st.session_state.selected_date = (
    start_month,
    end_month,
)


# Information about selected data
st.caption(
    f"Showing {len(subset):,} observations | "
    f"Area type: {area_type_choice} | "
    f"Area number: {area_nr_choice} | "
    f"Period: {start_month} to {end_month}"
)


# --------------------------------------------------
# Dataset summary
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Observations",
    f"{len(subset):,}",
)

col2.metric(
    "Selected area",
    str(area_nr_choice),
)

col3.metric(
    "Available months",
    f"{subset['month'].nunique()}",
)


# --------------------------------------------------
# Numeric column selector
# --------------------------------------------------

numeric_cols = [
    column
    for column in NUMERIC_COLS
    if column in subset.columns and subset[column].notna().any()
]


if not numeric_cols:

    st.warning("No usable numerical columns are available.")

    st.stop()


choice = st.selectbox(
    "Select variable to visualise",
    options=["All numeric columns"] + numeric_cols,
    key="plot_numeric_column",
)


st.divider()


# --------------------------------------------------
# Main Plotly chart
# --------------------------------------------------

st.subheader("Reservoir data visualisation")


if choice == "All numeric columns":

    fig = go.Figure()

    # Fill ratios
    ratio_columns = [
        column
        for column in [
            "fill_ratio",
            "fill_ratio_prev_week",
        ]
        if column in subset.columns
    ]

    for column in ratio_columns:

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                connectgaps=False,
                line=dict(
                    width=2,
                ),
            )
        )

    # Weekly filling change
    if "fill_ratio_change" in subset.columns:

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset["fill_ratio_change"] * 100,
                mode="lines",
                name="Fill ratio change × 100",
                connectgaps=False,
                opacity=0.7,
                line=dict(
                    dash="dot",
                ),
            )
        )

    # Energy values on secondary axis
    energy_columns = [
        column
        for column in [
            "filled_TWh",
            "capacity_TWh",
        ]
        if column in subset.columns
    ]

    for column in energy_columns:

        fig.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                yaxis="y2",
                connectgaps=False,
                line=dict(
                    width=2,
                ),
            )
        )

    fig.update_layout(
        title=f"Reservoir statistics: {start_month} to {end_month}",
        xaxis_title="Date",
        yaxis=dict(
            title="Fill ratio / weekly change",
            side="left",
        ),
        yaxis2=dict(
            title="Energy (TWh)",
            overlaying="y",
            side="right",
        ),
    )

else:

    fig = px.line(
        subset,
        x="date",
        y=choice,
        title=f"{choice}: {start_month} to {end_month}",
        labels={
            "date": "Date",
            choice: choice,
        },
        markers=True,
    )


# Apply common theme
fig = apply_plot_theme(
    fig,
    height=600,
)


# Display chart
st.plotly_chart(
    fig,
    use_container_width=True,
    theme=None,
)


# --------------------------------------------------
# Small multiples
# --------------------------------------------------

with st.expander("📊 Show small multiples"):

    st.write("Compare all available numerical variables " "in separate charts.")

    small_multiples = make_subplots(
        rows=len(numeric_cols),
        cols=1,
        shared_xaxes=True,
        subplot_titles=numeric_cols,
        vertical_spacing=0.04,
    )

    for index, column in enumerate(
        numeric_cols,
        start=1,
    ):

        small_multiples.add_trace(
            go.Scatter(
                x=subset["date"],
                y=subset[column],
                mode="lines",
                name=column,
                connectgaps=False,
                line=dict(
                    width=1.8,
                ),
            ),
            row=index,
            col=1,
        )

        small_multiples.update_yaxes(
            title_text=column,
            row=index,
            col=1,
        )

    small_multiples.update_layout(
        title="Small multiples — reservoir variables",
        showlegend=False,
    )

    small_multiples = apply_plot_theme(
        small_multiples,
        height=220 * len(numeric_cols) + 120,
    )

    st.plotly_chart(
        small_multiples,
        use_container_width=True,
        theme=None,
    )


# --------------------------------------------------
# Missing values information
# --------------------------------------------------

with st.expander("🔍 Data quality information"):

    missing_values = subset[numeric_cols].isna().sum().reset_index()

    missing_values.columns = [
        "Variable",
        "Missing values",
    ]

    st.dataframe(
        missing_values,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Data preview
# --------------------------------------------------

with st.expander("📋 Preview selected data"):

    st.dataframe(
        subset.drop(columns=["month"]),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Data source information
# --------------------------------------------------

with st.expander("ℹ️ About the data source"):

    st.markdown("""
        **Source:** NVE Magasinstatistikk API.

        The application retrieves reservoir statistics
        directly from the Norwegian Water Resources and
        Energy Directorate (NVE).

        The API response is cached for one hour to reduce
        unnecessary requests.

        The month selector filters the downloaded data.

        **Visualisation:** Plotly interactive charts.
        """)

    st.markdown(
        "[NVE Magasinstatistikk API documentation]"
        "(https://biapi.nve.no/magasinstatistikk/swagger/index.html)"
    )
