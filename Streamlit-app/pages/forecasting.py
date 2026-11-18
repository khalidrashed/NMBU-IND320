from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from statsmodels.tsa.statespace.sarimax import SARIMAX

from data_loader import load_data

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------


st.set_page_config(page_title="Reservoir Forecasting", page_icon="📈", layout="wide")

st.title("📈 Reservoir Filling Forecast")
st.write(
    "Forecast weekly reservoir filling levels using "
    "SARIMAX or a Random Forest model."
)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------


@st.cache_data
def load_reservoir_data():
    # Shared loader reads from MongoDB: ind320.nve_magasinstatistikk.
    # It also normalizes the original Norwegian field names to English.
    df = load_data().copy()

    required_columns = {"area_type", "date", "fill_ratio", "area_nr"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(
            "MongoDB reservoir data is missing required columns: "
            + ", ".join(sorted(missing))
        )

    df = df[df["area_type"].astype(str).str.upper() == "VASS"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["fill_ratio"] = pd.to_numeric(df["fill_ratio"], errors="coerce")
    df["area_nr"] = pd.to_numeric(df["area_nr"], errors="coerce")
    df = df.dropna(subset=["date", "fill_ratio", "area_nr"])

    return df.sort_values("date")


try:
    data = load_reservoir_data()
except Exception as exc:
    st.error(f"Could not load reservoir data: {exc}")
    st.stop()


if data.empty:
    st.error("No VASS reservoir data is available.")
    st.stop()


# ---------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------


def create_calendar_features(index):
    features = pd.DataFrame(index=index)

    week = index.isocalendar().week.astype(int)

    features["week_sin"] = np.sin(2 * np.pi * week / 52.18)

    features["week_cos"] = np.cos(2 * np.pi * week / 52.18)

    features["year"] = index.year

    return features


def prepare_area_data(area_number, history_years):
    area = data[data["area_nr"] == area_number].copy()

    area = area.sort_values("date")
    area = area.set_index("date")

    area = area[["fill_ratio"]]

    latest_date = area.index.max()

    start_date = latest_date - pd.DateOffset(years=history_years)

    area = area[area.index >= start_date]

    # The source observations are weekly.
    area = area.resample("W-SUN").mean()

    area["fill_ratio"] = area["fill_ratio"].interpolate(method="time")

    return area.dropna()


# ---------------------------------------------------------
# Random Forest recursive forecasting
# ---------------------------------------------------------


def train_random_forest(series, horizon, use_calendar):
    frame = pd.DataFrame({"target": series})

    for lag in [1, 2, 3, 4, 8, 12, 26, 52]:
        frame[f"lag_{lag}"] = series.shift(lag)

    calendar = create_calendar_features(series.index)

    if use_calendar:
        frame = frame.join(calendar)

    frame = frame.dropna()

    if len(frame) < 100:
        raise ValueError(
            "Not enough observations for Random Forest. "
            "Choose a longer training period."
        )

    feature_columns = [column for column in frame.columns if column != "target"]

    split = int(len(frame) * 0.8)

    train = frame.iloc[:split]
    test = frame.iloc[split:]

    model = RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=-1
    )

    model.fit(train[feature_columns], train["target"])

    predictions = model.predict(test[feature_columns])

    mae = mean_absolute_error(test["target"], predictions)

    rmse = np.sqrt(mean_squared_error(test["target"], predictions))

    # Refit using all available observations.
    model.fit(frame[feature_columns], frame["target"])

    history = list(series.values)
    future_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(days=7), periods=horizon, freq="W-SUN"
    )

    forecast_values = []

    for date in future_dates:
        row = {}

        for lag in [1, 2, 3, 4, 8, 12, 26, 52]:
            row[f"lag_{lag}"] = history[-lag]

        if use_calendar:
            calendar_row = create_calendar_features(pd.DatetimeIndex([date])).iloc[0]

            row["week_sin"] = calendar_row["week_sin"]
            row["week_cos"] = calendar_row["week_cos"]
            row["year"] = calendar_row["year"]

        X_future = pd.DataFrame([row], columns=feature_columns)

        prediction = float(model.predict(X_future)[0])

        # Filling level is constrained to 0–1.
        prediction = float(np.clip(prediction, 0, 1))

        forecast_values.append(prediction)
        history.append(prediction)

    forecast = pd.Series(forecast_values, index=future_dates, name="forecast")

    return forecast, mae, rmse


# ---------------------------------------------------------
# SARIMAX forecasting
# ---------------------------------------------------------


def train_sarimax(series, horizon, use_calendar, order):
    split = int(len(series) * 0.8)

    train = series.iloc[:split]
    test = series.iloc[split:]

    train_exog = None
    test_exog = None

    if use_calendar:
        train_exog = create_calendar_features(train.index)

        test_exog = create_calendar_features(test.index)

    evaluation_model = SARIMAX(
        train,
        exog=train_exog,
        order=order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    evaluation_result = evaluation_model.fit(disp=False, maxiter=100)

    test_prediction = evaluation_result.get_forecast(
        steps=len(test), exog=test_exog
    ).predicted_mean

    mae = mean_absolute_error(test, test_prediction)

    rmse = np.sqrt(mean_squared_error(test, test_prediction))

    # Refit using the complete historical series.
    full_exog = None

    if use_calendar:
        full_exog = create_calendar_features(series.index)

    final_model = SARIMAX(
        series,
        exog=full_exog,
        order=order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    final_result = final_model.fit(disp=False, maxiter=100)

    future_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(days=7), periods=horizon, freq="W-SUN"
    )

    future_exog = None

    if use_calendar:
        future_exog = create_calendar_features(future_dates)

    result = final_result.get_forecast(steps=horizon, exog=future_exog)

    forecast = result.predicted_mean
    confidence = result.conf_int()

    forecast.index = future_dates
    confidence.index = future_dates

    forecast = forecast.clip(0, 1)

    lower = confidence.iloc[:, 0].clip(0, 1)
    upper = confidence.iloc[:, 1].clip(0, 1)

    return forecast, lower, upper, mae, rmse


# ---------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------

st.sidebar.header("Forecast settings")

area_number = st.sidebar.selectbox(
    "Water area", [1, 2, 3], format_func=lambda x: f"VASS {x}"
)

model_name = st.sidebar.selectbox("Forecasting model", ["SARIMAX", "Random Forest"])

history_years = st.sidebar.slider(
    "Training history (years)", min_value=3, max_value=30, value=15
)

horizon = st.sidebar.slider(
    "Forecast horizon (weeks)", min_value=4, max_value=26, value=12
)

use_calendar = st.sidebar.checkbox("Use calendar-based exogenous variables", value=True)

p = 1
d = 1
q = 1

if model_name == "SARIMAX":
    st.sidebar.subheader("SARIMAX parameters")

    p = st.sidebar.selectbox("AR order (p)", [0, 1, 2, 3], index=1)

    d = st.sidebar.selectbox("Differencing (d)", [0, 1, 2], index=1)

    q = st.sidebar.selectbox("MA order (q)", [0, 1, 2, 3], index=1)

run_forecast = st.sidebar.button("Run forecast", type="primary")


# ---------------------------------------------------------
# Prepare selected area
# ---------------------------------------------------------

area_data = prepare_area_data(area_number, history_years)

if len(area_data) < 100:
    st.warning(
        "The selected training period contains too few "
        "observations. Choose a longer history."
    )
    st.stop()

series = area_data["fill_ratio"]


# ---------------------------------------------------------
# Historical data
# ---------------------------------------------------------

st.subheader(f"Historical reservoir filling – VASS {area_number}")

fig_history = go.Figure()

fig_history.add_trace(
    go.Scatter(x=series.index, y=series.values, mode="lines", name="Historical filling")
)

fig_history.update_layout(
    xaxis_title="Date",
    yaxis_title="Filling level",
    yaxis=dict(tickformat=".0%"),
    hovermode="x unified",
)

st.plotly_chart(fig_history, use_container_width=True)

st.caption(
    f"Training period: {series.index.min().date()} "
    f"to {series.index.max().date()} "
    f"({len(series)} weekly observations)"
)


# ---------------------------------------------------------
# Forecast
# ---------------------------------------------------------

if run_forecast:

    try:
        with st.spinner("Training model and generating forecast..."):

            if model_name == "SARIMAX":

                forecast, lower, upper, mae, rmse = train_sarimax(
                    series=series,
                    horizon=horizon,
                    use_calendar=use_calendar,
                    order=(p, d, q),
                )

            else:

                forecast, mae, rmse = train_random_forest(
                    series=series, horizon=horizon, use_calendar=use_calendar
                )

                lower = None
                upper = None

        st.success("Forecast completed.")

        # Metrics
        col1, col2 = st.columns(2)

        col1.metric("Mean Absolute Error (MAE)", f"{mae:.4f}")

        col2.metric("Root Mean Squared Error (RMSE)", f"{rmse:.4f}")

        # Forecast plot
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=series.index, y=series.values, mode="lines", name="Historical filling"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast.index,
                y=forecast.values,
                mode="lines+markers",
                name="Forecast",
            )
        )

        if lower is not None and upper is not None:

            fig.add_trace(
                go.Scatter(
                    x=forecast.index,
                    y=upper,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=forecast.index,
                    y=lower,
                    mode="lines",
                    fill="tonexty",
                    name="95% confidence interval",
                    line=dict(width=0),
                    hoverinfo="skip",
                )
            )

        fig.update_layout(
            title=f"{model_name} forecast – VASS {area_number}",
            xaxis_title="Date",
            yaxis_title="Filling level",
            yaxis=dict(tickformat=".0%", range=[0, 1]),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Forecast values")

        forecast_table = pd.DataFrame(
            {"Date": forecast.index, "Forecast filling level": forecast.values}
        )

        if lower is not None:
            forecast_table["Lower confidence limit"] = lower.values
            forecast_table["Upper confidence limit"] = upper.values

        st.dataframe(
            forecast_table.style.format(
                {
                    "Forecast filling level": "{:.1%}",
                    "Lower confidence limit": "{:.1%}",
                    "Upper confidence limit": "{:.1%}",
                }
            ),
            use_container_width=True,
        )

        st.download_button(
            "Download forecast CSV",
            data=forecast_table.to_csv(index=False).encode("utf-8"),
            file_name=f"VASS_{area_number}_forecast.csv",
            mime="text/csv",
        )

    except Exception as exc:
        st.error(f"Forecast failed: {exc}")


# ---------------------------------------------------------
# Methodology
# ---------------------------------------------------------

with st.expander("Methodology and limitations"):

    st.markdown("""
    **Data source:** Norges vassdrags- og energidirektorat (NVE)
    Magasinstatistikk dataset.

    **Time resolution:** Weekly observations.

    **Target variable:** Reservoir filling level (`fill_ratio`).

    **SARIMAX:** Uses autoregressive, differencing and moving-average
    parameters. Optional calendar variables represent annual seasonality.

    **Random Forest:** Uses historical lagged filling levels and,
    optionally, calendar-based features. Forecasts are generated
    recursively.

    **Evaluation:** The earliest 80% of observations are used for
    training and the latest 20% for testing.

    **Limitations:** Calendar features do not represent future weather
    conditions. Random Forest does not provide statistical confidence
    intervals in this implementation. Forecasts are constrained to
    the physical filling range of 0–100%.
    """)
