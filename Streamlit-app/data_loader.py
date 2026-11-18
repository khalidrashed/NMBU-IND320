
"""
Page 2: Data Table
Source: MongoDB Atlas

Requirement:
- One row for each column of imported data.
- LineChartColumn() displays the first 30 observations.
"""

import pandas as pd
import streamlit as st
from pymongo import MongoClient


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Data Table",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Data Table")
st.write("Explore reservoir data imported from MongoDB Atlas.")


# ==================================================
# 2. MONGODB CONNECTION
# ==================================================

@st.cache_resource
def get_mongodb_client():

    client = MongoClient(
        st.secrets["mongo"]["uri"],
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    return client


# ==================================================
# 3. LOAD DATA FROM MONGODB
# ==================================================

@st.cache_data(ttl=300, show_spinner="Loading data from MongoDB...")
def load_data():

    client = get_mongodb_client()

    database_name = st.secrets["mongo"]["database"]
    collection_name = st.secrets["mongo"]["collection"]

    db = client[database_name]
    collection = db[collection_name]

    # Retrieve all documents
    records = list(
        collection.find({}, {"_id": 0})
    )

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


# ==================================================
# 4. CHECK DATABASE CONNECTION
# ==================================================

try:

    client = get_mongodb_client()

    df = load_data()

    if df.empty:
        st.warning("No records found in MongoDB.")
        st.stop()

    st.success("Successfully connected to MongoDB Atlas!")

except Exception as error:

    st.error(f"MongoDB connection failed: {error}")

    st.info(
        "Check your MongoDB URI, database name, "
        "collection name and Atlas network access."
    )

    st.stop()


# ==================================================
# 5. DATA PREPARATION
# ==================================================

# Detect timestamp column
date_column = next(
    (
        col for col in ["date", "time", "timestamp"]
        if col in df.columns
    ),
    None
)

if date_column:

    df[date_column] = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    df = df.sort_values(
        date_column,
        na_position="last"
    ).reset_index(drop=True)


# ==================================================
# 6. DATASET OVERVIEW
# ==================================================

st.subheader("Dataset overview")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total records",
    f"{len(df):,}"
)

col2.metric(
    "Total columns",
    f"{df.shape[1]:,}"
)

col3.metric(
    "Data source",
    "MongoDB Atlas"
)

if date_column:

    valid_dates = df[date_column].dropna()

    if not valid_dates.empty:

        st.write(
            f"**Period:** "
            f"{valid_dates.min().date()} → "
            f"{valid_dates.max().date()}"
        )


# ==================================================
# 7. FIRST 30 OBSERVATIONS
# ==================================================

first_month = df.head(30)


# ==================================================
# 8. CREATE ONE ROW PER DATA COLUMN
# ==================================================

rows = []

for col in df.columns:

    series = df[col]

    if pd.api.types.is_numeric_dtype(series):

        spark = (
            first_month[col]
            .dropna()
            .astype(float)
            .tolist()
        )

        mean_val = series.mean()
        min_val = series.min()
        max_val = series.max()

    else:

        spark = []

        mean_val = None
        min_val = None
        max_val = None

    rows.append({
        "Column": col,
        "Dtype": str(series.dtype),
        "Mean": mean_val,
        "Min": min_val,
        "Max": max_val,
        "First month": spark
    })


table_df = pd.DataFrame(rows)


# ==================================================
# 9. DISPLAY DATA TABLE
# ==================================================

st.subheader("Imported data – Column overview")

st.dataframe(
    table_df,
    column_config={

        "First month": st.column_config.LineChartColumn(
            "First month",
            width="large",
            help="First 30 time-ordered observations."
        ),

        "Mean": st.column_config.NumberColumn(
            "Mean",
            format="%.4f"
        ),

        "Min": st.column_config.NumberColumn(
            "Min",
            format="%.4f"
        ),

        "Max": st.column_config.NumberColumn(
            "Max",
            format="%.4f"
        )
    },
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Each row represents one column from the MongoDB dataset. "
    "The sparkline displays the first 30 observations."
)


# ==================================================
# 10. RAW DATA
# ==================================================

st.divider()

with st.expander("Show raw first 20 rows"):

    st.dataframe(
        df.head(20),
        use_container_width=True,
        hide_index=True
    )


# ==================================================
# 11. DOWNLOAD DATA
# ==================================================

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download MongoDB data as CSV",
    data=csv_data,
    file_name="reservoirs_mongodb.csv",
    mime="text/csv"
)


# ==================================================
# 12. REFRESH DATA
# ==================================================

if st.button("🔄 Refresh MongoDB data"):

    load_data.clear()
    st.rerun()
