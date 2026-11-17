import streamlit as st
import pandas as pd
from pathlib import Path

st.title("💱 Currency Exchange Rates")

st.write("Explore daily EUR and USD exchange rates from Norges Bank.")

# Locate currency data
DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "currency"
    / "currency_rates_2025.csv"
)

if DATA_PATH.exists():
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    currency = st.selectbox(
        "Select currency",
        ["EUR", "USD"],
    )

    filtered_df = df[df["currency"] == currency]

    st.metric(
        f"{currency} exchange rate",
        (
            f"{filtered_df['exchange_rate'].iloc[-1]:.4f} NOK"
            if not filtered_df.empty
            else "No data"
        ),
    )

    st.line_chart(
        filtered_df.set_index("date")["exchange_rate"],
        y_label="Exchange rate (NOK)",
    )

    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning(f"Currency data file not found: {DATA_PATH}")
