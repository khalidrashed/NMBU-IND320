"""
Currency Exchange Rates page for the IND320 Streamlit app.

Loads daily EUR and USD exchange rates from MongoDB Atlas.
Database: ind320
Collection: currency_rates
Expected fields: date, currency, exchange_rate
"""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Currency Exchange Rates",
    page_icon="💱",
    layout="wide",
)

st.title("💱 Currency Exchange Rates")
st.write("Explore daily EUR and USD exchange rates from Norges Bank.")


# ==================================================
# 2. LOAD MONGODB CONNECTION STRING
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env if python-dotenv is installed.
# It is optional when MONGODB_URI is configured in the environment
# or in Streamlit secrets.
try:
    from dotenv import load_dotenv

    for env_path in [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT.parent / ".env",
    ]:
        if env_path.is_file():
            load_dotenv(env_path, override=False)
except ImportError:
    pass

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    try:
        MONGODB_URI = st.secrets["MONGODB_URI"]
    except Exception:
        MONGODB_URI = None

if not MONGODB_URI:
    st.error(
        "MONGODB_URI was not found. Add it to the project .env file "
        "or configure it in Streamlit secrets."
    )
    st.stop()


# ==================================================
# 3. MONGODB SETTINGS
# ==================================================

DATABASE_NAME = "ind320"
COLLECTION_NAME = "currency_rates"


# ==================================================
# 4. LOAD CURRENCY DATA
# ==================================================

@st.cache_data(show_spinner="Loading currency rates from MongoDB...")
def load_currency_data():
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )

    try:
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        documents = list(
            collection.find(
                {},
                {
                    "_id": 0,
                    "date": 1,
                    "currency": 1,
                    "exchange_rate": 1,
                },
            ).sort("date", 1)
        )
    finally:
        client.close()

    if not documents:
        return pd.DataFrame()

    data = pd.DataFrame(documents)

    required_columns = ["date", "currency", "exchange_rate"]
    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "The MongoDB collection is missing these fields: "
            + ", ".join(missing_columns)
        )

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce",
        utc=True,
    ).dt.tz_convert(None)

    data["currency"] = data["currency"].astype(str).str.upper().str.strip()
    data["exchange_rate"] = pd.to_numeric(
        data["exchange_rate"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["date", "exchange_rate", "currency"]
    )

    data = data[data["currency"].isin(["EUR", "USD"])]

    return data.sort_values(
        ["currency", "date"]
    ).reset_index(drop=True)


try:
    df = load_currency_data()
except Exception as error:
    st.error(f"Could not load currency data from MongoDB: {error}")
    st.stop()

if df.empty:
    st.warning(
        f"No EUR or USD records were found in "
        f"{DATABASE_NAME}.{COLLECTION_NAME}."
    )
    st.stop()


# ==================================================
# 5. CURRENCY SELECTION
# ==================================================

available_currencies = [
    currency for currency in ["EUR", "USD"]
    if currency in df["currency"].unique()
]

currency = st.selectbox(
    "Select currency",
    options=available_currencies,
)

filtered_df = (
    df[df["currency"] == currency]
    .sort_values("date")
    .copy()
)

if filtered_df.empty:
    st.warning(f"No data is available for {currency}.")
    st.stop()


# ==================================================
# 6. DATASET OVERVIEW
# ==================================================

st.subheader("Dataset overview")

latest_record = filtered_df.iloc[-1]
first_record = filtered_df.iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    f"Latest {currency} exchange rate",
    f"{latest_record['exchange_rate']:.4f} NOK",
)

col2.metric(
    "Number of observations",
    f"{len(filtered_df):,}",
)

col3.metric(
    "First observation",
    first_record["date"].strftime("%d %b %Y"),
)

col4.metric(
    "Latest observation",
    latest_record["date"].strftime("%d %b %Y"),
)


# ==================================================
# 7. EXCHANGE RATE CHART
# ==================================================

st.subheader(f"{currency} exchange rate over time")

fig = px.line(
    filtered_df,
    x="date",
    y="exchange_rate",
    title=f"Daily {currency}/NOK exchange rate",
    labels={
        "date": "Date",
        "exchange_rate": "Exchange rate (NOK)",
    },
)

fig.update_layout(
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Exchange rate (NOK)",
)

st.plotly_chart(fig, width="stretch")


# ==================================================
# 8. DATA TABLE AND DOWNLOAD
# ==================================================

st.divider()
st.subheader("Currency observations")

with st.expander("View currency data"):
    st.dataframe(
        filtered_df,
        width="stretch",
        hide_index=True,
    )

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=f"Download {currency} data as CSV",
        data=csv_data,
        file_name=f"{currency}_exchange_rates.csv",
        mime="text/csv",
    )


# ==================================================
# 9. DATA INFORMATION
# ==================================================

with st.expander("About this dataset"):
    st.write(
        f"""
        **Source:** Norges Bank exchange rate data.

        **Database:** `{DATABASE_NAME}`

        **Collection:** `{COLLECTION_NAME}`

        **Selected currency:** `{currency}`

        **Exchange rate unit:** NOK per unit of foreign currency.

        **Variables:**

        - `date`: Observation date.
        - `currency`: Currency code (EUR or USD).
        - `exchange_rate`: Exchange rate against NOK.
        """
    )

