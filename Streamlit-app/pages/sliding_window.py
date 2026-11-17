"""Part 4: Sliding Window Correlation Analysis."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.title("Sliding Window Correlation")

st.write(
    "Investigate the relationship between weather conditions "
    "and reservoir filling using lagged rolling correlations."
)

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent
PART4_DIR = PROJECT_DIR / "Notbook" / "Part4"

WEATHER_FILE = PART4_DIR / "RM_weather_2024.csv"
RESERVOIR_FILE = PART4_DIR / "reservoirs.csv"


# ==================================================
# LOAD DATA
# ==================================================


@st.cache_data
def load_weather(path):

    df = pd.read_csv(path)

    required = {
        "time",
        "temperature_2m",
        "precipitation",
        "point_id",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Weather file is missing columns: {missing}")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    for column in ["temperature_2m", "precipitation"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.dropna(subset=["time"])


@st.cache_data
def load_reservoirs(path):

    df = pd.read_csv(path)

    required = {
        "dato_Id",
        "omrType",
        "omrnr",
        "fyllingsgrad",
        "fylling_TWh",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Reservoir file is missing columns: {missing}")

    df["dato_Id"] = pd.to_datetime(df["dato_Id"], errors="coerce")

    for column in [
        "omrnr",
        "fyllingsgrad",
        "fylling_TWh",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["omrType"] = df["omrType"].astype(str).str.strip().str.upper()

    return df.dropna(subset=["dato_Id", "omrnr"])


# ==================================================
# FILE VALIDATION
# ==================================================

if not WEATHER_FILE.exists():
    st.error(f"Weather file not found: {WEATHER_FILE}")
    st.stop()

if not RESERVOIR_FILE.exists():
    st.error(f"Reservoir file not found: {RESERVOIR_FILE}")
    st.stop()

try:

    weather = load_weather(str(WEATHER_FILE))
    reservoirs = load_reservoirs(str(RESERVOIR_FILE))

except Exception as exc:

    st.error(f"Could not load data: {exc}")
    st.stop()


# ==================================================
# SIDEBAR SETTINGS
# ==================================================

st.sidebar.header("Analysis Settings")

weather_variable = st.sidebar.selectbox(
    "Weather variable",
    ["temperature_2m", "precipitation"],
    format_func=lambda x: {
        "temperature_2m": "Temperature",
        "precipitation": "Precipitation",
    }[x],
)

reservoir_variable = st.sidebar.selectbox(
    "Reservoir variable",
    ["fyllingsgrad", "fylling_TWh"],
    format_func=lambda x: {
        "fyllingsgrad": "Filling level",
        "fylling_TWh": "Filled energy (TWh)",
    }[x],
)

available_areas = sorted(
    reservoirs.loc[reservoirs["omrType"] == "VASS", "omrnr"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

if not available_areas:
    st.error("No VASS reservoir areas were found.")
    st.stop()

water_area = st.sidebar.selectbox(
    "Water area",
    available_areas,
    format_func=lambda x: f"VASS {x}",
)

lag_weeks = st.sidebar.slider(
    "Weather lag (weeks)",
    min_value=0,
    max_value=12,
    value=0,
)

window_weeks = st.sidebar.slider(
    "Rolling window (weeks)",
    min_value=4,
    max_value=52,
    value=12,
)


# ==================================================
# WEATHER AGGREGATION
# ==================================================

st.subheader("Weather and Reservoir Data")

# Aggregate weather observations across sampling points.
# First calculate daily means, then weekly means.

weather_daily = (
    weather.groupby(pd.Grouper(key="time", freq="D"))[weather_variable]
    .mean()
    .rename("weather")
    .reset_index()
)

weather_weekly = (
    weather_daily.set_index("time")["weather"]
    .resample("W-SUN")
    .mean()
    .rename("weather")
    .reset_index()
)

weather_weekly = weather_weekly.dropna()


# ==================================================
# RESERVOIR AGGREGATION
# ==================================================

reservoir_area = reservoirs[
    (reservoirs["omrType"] == "VASS") & (reservoirs["omrnr"] == water_area)
].copy()

if reservoir_area.empty:
    st.warning("No reservoir observations for selected area.")
    st.stop()

reservoir_weekly = (
    reservoir_area.set_index("dato_Id")[reservoir_variable]
    .resample("W-SUN")
    .mean()
    .rename("reservoir")
    .reset_index()
)


# ==================================================
# MERGE WEATHER AND RESERVOIR DATA
# ==================================================

combined = pd.merge(
    weather_weekly,
    reservoir_weekly,
    left_on="time",
    right_on="dato_Id",
    how="inner",
)

combined = (
    combined.dropna(subset=["weather", "reservoir"])
    .sort_values("time")
    .reset_index(drop=True)
)

if combined.empty:
    st.warning("No overlapping observations were found.")
    st.stop()

st.caption(
    f"Analysis period: {combined['time'].min().date()} "
    f"to {combined['time'].max().date()}"
)


# ==================================================
# AUTOMATIC LAG COMPARISON
# ==================================================

st.subheader("Automatic Lag Comparison")

lag_results = []

for lag in range(13):

    temp = combined[["time", "weather", "reservoir"]].copy()

    temp["weather_lagged"] = temp["weather"].shift(lag)

    temp = temp.dropna(subset=["weather_lagged", "reservoir"])

    if len(temp) >= 4:

        correlation = temp[["weather_lagged", "reservoir"]].corr().iloc[0, 1]

        lag_results.append(
            {
                "Lag (weeks)": lag,
                "Correlation": correlation,
                "Absolute correlation": abs(correlation),
                "Observations": len(temp),
            }
        )

lag_df = pd.DataFrame(lag_results)

if lag_df.empty:
    st.warning("Not enough data for lag comparison.")
    st.stop()

valid_lags = lag_df.dropna(subset=["Correlation"])

if valid_lags.empty:
    st.warning("Correlation could not be calculated.")
    st.stop()

best_index = valid_lags["Absolute correlation"].idxmax()

best_lag = int(lag_df.loc[best_index, "Lag (weeks)"])

best_correlation = float(lag_df.loc[best_index, "Correlation"])

c1, c2 = st.columns(2)

c1.metric(
    "Best lag",
    f"{best_lag} weeks",
)

c2.metric(
    "Best correlation",
    f"{best_correlation:.3f}",
)

lag_fig = px.bar(
    lag_df,
    x="Lag (weeks)",
    y="Correlation",
    hover_data=["Observations"],
    title="Correlation for Different Weather Lags",
)

lag_fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray",
)

lag_fig.update_layout(
    yaxis_range=[-1, 1],
)

st.plotly_chart(
    lag_fig,
    use_container_width=True,
)


# ==================================================
# APPLY SELECTED LAG
# ==================================================

analysis = combined.copy()

analysis["weather_lagged"] = analysis["weather"].shift(lag_weeks)

analysis = analysis.dropna(subset=["weather_lagged", "reservoir"]).copy()

if len(analysis) < window_weeks:
    st.warning(
        "Not enough observations for the selected rolling window. "
        "Reduce the window size or lag."
    )
    st.stop()


# ==================================================
# ROLLING CORRELATION
# ==================================================

analysis["rolling_correlation"] = (
    analysis["weather_lagged"]
    .rolling(
        window=window_weeks,
        min_periods=window_weeks,
    )
    .corr(analysis["reservoir"])
)

valid_correlation = analysis["rolling_correlation"].dropna()

if valid_correlation.empty:
    st.warning("No rolling correlations could be calculated.")
    st.stop()


# ==================================================
# SUMMARY METRICS
# ==================================================

overall_correlation = analysis[["weather_lagged", "reservoir"]].corr().iloc[0, 1]

latest_correlation = valid_correlation.iloc[-1]

c1, c2, c3 = st.columns(3)

c1.metric(
    "Overall correlation",
    f"{overall_correlation:.3f}",
)

c2.metric(
    "Latest rolling correlation",
    f"{latest_correlation:.3f}",
)

c3.metric(
    "Overlapping weeks",
    len(analysis),
)


# ==================================================
# ROLLING CORRELATION CHART
# ==================================================

st.subheader("Rolling Window Correlation")

fig = px.line(
    analysis,
    x="time",
    y="rolling_correlation",
    title=(f"Rolling Correlation: " f"{weather_variable} and {reservoir_variable}"),
    labels={
        "time": "Date",
        "rolling_correlation": "Correlation",
    },
)

fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray",
)

fig.update_layout(
    yaxis_range=[-1, 1],
    hovermode="x unified",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ==================================================
# WEATHER AND RESERVOIR TIME SERIES
# ==================================================

st.subheader("Weather and Reservoir Time Series")

comparison = analysis[["time", "weather_lagged", "reservoir"]].melt(
    id_vars="time",
    var_name="Variable",
    value_name="Value",
)

fig2 = px.line(
    comparison,
    x="time",
    y="Value",
    color="Variable",
    title="Weekly Weather and Reservoir Observations",
)

fig2.update_layout(
    hovermode="x unified",
)

st.plotly_chart(
    fig2,
    use_container_width=True,
)


# ==================================================
# DATA TABLE
# ==================================================

with st.expander("View analysis data"):

    st.dataframe(
        analysis,
        use_container_width=True,
    )

with st.expander("View automatic lag comparison"):

    st.dataframe(
        lag_df,
        use_container_width=True,
    )


# ==================================================
# METHODOLOGY
# ==================================================

st.subheader("Methodology")

st.markdown(f"""
    - Weather region: RM
    - Weather sampling points: {weather['point_id'].nunique()}
    - Weather variable: {weather_variable}
    - Reservoir area: VASS {water_area}
    - Reservoir variable: {reservoir_variable}
    - Time resolution: Weekly
    - Selected lag: {lag_weeks} weeks
    - Rolling window: {window_weeks} weeks
    - Best tested lag: {best_lag} weeks
    - Best tested correlation: {best_correlation:.3f}

    Weather observations are averaged across the available
    sampling points. Reservoir observations are aggregated
    weekly. Only overlapping dates are included.

    Correlation indicates statistical association and does
    not establish causation.
    """)
