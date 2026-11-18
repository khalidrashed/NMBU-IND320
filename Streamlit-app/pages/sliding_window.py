"""Part 4: Sliding Window Correlation Analysis."""

import sys
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
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ==================================================
# LOADERS
# ==================================================

@st.cache_data(ttl=600)
def load_weather(region):
    """Load weather observations from MongoDB Atlas."""
    import os

    from pymongo import MongoClient

    try:
        from dotenv import load_dotenv

        for env_path in (
            APP_DIR.parent / ".env",
            APP_DIR / ".env",
            Path.cwd() / ".env",
        ):
            if env_path.exists():
                load_dotenv(env_path, override=False)
    except ImportError:
        pass

    uri = os.getenv("MONGODB_URI")
    if not uri:
        try:
            uri = st.secrets["MONGODB_URI"]
        except Exception:
            uri = None

    if not uri:
        raise RuntimeError(
            "MONGODB_URI is missing. Configure it in Streamlit Secrets "
            "or in the project .env file."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        collection = client["ind320"]["weather_data"]
        documents = list(
            collection.find(
                {"region": region},
                {
                    "_id": 0,
                    "time": 1,
                    "temperature_2m": 1,
                    "precipitation": 1,
                    "point_id": 1,
                    "region": 1,
                },
            )
        )
    finally:
        client.close()

    if not documents:
        raise ValueError(
            f"No weather observations found in ind320.weather_data for {region}."
        )

    df = pd.DataFrame(documents)
    required = {"time", "temperature_2m", "precipitation", "point_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Weather collection is missing fields: "
            + ", ".join(sorted(missing))
        )

    parsed_time = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df["time"] = parsed_time.dt.tz_convert(None)

    for column in ["temperature_2m", "precipitation", "point_id"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["time", "temperature_2m", "precipitation", "point_id"]
    )
    return df.sort_values("time").reset_index(drop=True)


@st.cache_data(show_spinner="Loading reservoir data from MongoDB…")
def load_reservoirs():
    """Use the app's shared data_loader, which reads MongoDB reservoir data."""
    from data_loader import load_data

    df = load_data().copy()

    # data_loader normalizes the MongoDB field names to English.
    # The fallback names support older versions of the collection.
    rename_fallbacks = {
        "dato_Id": "date",
        "dato": "date",
        "omrType": "area_type",
        "omr_type": "area_type",
        "omrnr": "area_nr",
        "omr_nr": "area_nr",
        "fyllingsgrad": "fill_ratio",
        "fylling_TWh": "filled_TWh",
        "fylling_twh": "filled_TWh",
    }
    df = df.rename(columns={
        old: new for old, new in rename_fallbacks.items()
        if old in df.columns and new not in df.columns
    })

    required = {"date", "area_type", "area_nr", "fill_ratio", "filled_TWh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Reservoir data from MongoDB is missing fields: "
            + ", ".join(sorted(missing))
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["area_type"] = df["area_type"].astype(str).str.strip().str.upper()

    for column in ["area_nr", "fill_ratio", "filled_TWh"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.dropna(subset=["date", "area_nr"]).sort_values("date")


# ==================================================
# SIDEBAR SETTINGS AND DATA LOADING
# ==================================================

st.sidebar.header("Analysis Settings")

weather_region = st.sidebar.selectbox(
    "Weather region",
    ["RM", "NO3"],
    index=0,
)

try:
    weather = load_weather(weather_region)
    reservoirs = load_reservoirs()
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

if weather.empty:
    st.warning(f"No valid weather observations are available for {weather_region}.")
    st.stop()

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
    ["fill_ratio", "filled_TWh"],
    format_func=lambda x: {
        "fill_ratio": "Filling level",
        "filled_TWh": "Filled energy (TWh)",
    }[x],
)

available_areas = sorted(
    reservoirs.loc[reservoirs["area_type"] == "VASS", "area_nr"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

if not available_areas:
    st.error("No VASS reservoir areas were found in MongoDB.")
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
    .dropna()
)


# ==================================================
# RESERVOIR AGGREGATION
# ==================================================

reservoir_area = reservoirs[
    (reservoirs["area_type"] == "VASS")
    & (reservoirs["area_nr"] == water_area)
].copy()

if reservoir_area.empty:
    st.warning("No reservoir observations for selected area.")
    st.stop()

reservoir_weekly = (
    reservoir_area.set_index("date")[reservoir_variable]
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
    right_on="date",
    how="inner",
)

combined = (
    combined.dropna(subset=["weather", "reservoir"])
    .sort_values("time")
    .reset_index(drop=True)
)

if combined.empty:
    st.warning(
        "No overlapping weekly observations were found between "
        "the selected weather region and reservoir area."
    )
    st.stop()

st.caption(
    f"Weather region: {weather_region} | "
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
c1.metric("Best lag", f"{best_lag} weeks")
c2.metric("Best correlation", f"{best_correlation:.3f}")

lag_fig = px.bar(
    lag_df,
    x="Lag (weeks)",
    y="Correlation",
    hover_data=["Observations"],
    title="Correlation for Different Weather Lags",
)
lag_fig.add_hline(y=0, line_dash="dash", line_color="gray")
lag_fig.update_layout(yaxis_range=[-1, 1])
st.plotly_chart(lag_fig, use_container_width=True)


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
    .rolling(window=window_weeks, min_periods=window_weeks)
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
c1.metric("Overall correlation", f"{overall_correlation:.3f}")
c2.metric("Latest rolling correlation", f"{latest_correlation:.3f}")
c3.metric("Overlapping weeks", len(analysis))


# ==================================================
# ROLLING CORRELATION CHART
# ==================================================

st.subheader("Rolling Window Correlation")

fig = px.line(
    analysis,
    x="time",
    y="rolling_correlation",
    title=f"Rolling Correlation: {weather_variable} and {reservoir_variable}",
    labels={"time": "Date", "rolling_correlation": "Correlation"},
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.update_layout(yaxis_range=[-1, 1], hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)


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
fig2.update_layout(hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)


# ==================================================
# DATA TABLE
# ==================================================

with st.expander("View analysis data"):
    st.dataframe(analysis, use_container_width=True)

with st.expander("View automatic lag comparison"):
    st.dataframe(lag_df, use_container_width=True)


# ==================================================
# METHODOLOGY
# ==================================================

st.subheader("Methodology")

st.markdown(f"""
    - Weather source: MongoDB Atlas (`ind320.weather_data`)
    - Weather region: {weather_region}
    - Weather sampling points: {weather['point_id'].nunique()}
    - Weather variable: {weather_variable}
    - Reservoir source: MongoDB Atlas (`ind320.nve_magasinstatistikk`)
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


