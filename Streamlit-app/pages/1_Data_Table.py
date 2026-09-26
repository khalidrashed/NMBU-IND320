"""
Page 2: Data Table.

Requirement:
    "A table showing the imported data. Use the row-wise LineChartColumn()
     to display the first month of the data series. There should be one row
     in the table for each column of the imported data."
"""
import pandas as pd
import streamlit as st

from data_loader import load_data

st.title("📋 Data Table")

df = load_data()

st.write(
    f"Loaded **{len(df):,}** rows and **{df.shape[1]}** columns. "
    f"Period: **{df['date'].min().date()}** → **{df['date'].max().date()}**."
)

# ---------------------------------------------------------------------------
# One row per column of the imported data.
# "First month" = first 30 time-ordered observations of that column,
# shown as an inline LineChartColumn sparkline.
# ---------------------------------------------------------------------------
first_month = df.head(30)

rows = []
for col in df.columns:
    series = df[col]
    fm = first_month[col]

    if pd.api.types.is_numeric_dtype(series):
        spark = fm.dropna().astype(float).tolist()
        mean_val = float(series.mean())
        min_val = float(series.min())
        max_val = float(series.max())
    else:
        spark = []
        mean_val = min_val = max_val = None

    rows.append(
        {
            "Column": col,
            "Dtype": str(series.dtype),
            "Mean": mean_val,
            "Min": min_val,
            "Max": max_val,
            "First month": spark,
        }
    )

table_df = pd.DataFrame(rows)

st.dataframe(
    table_df,
    column_config={
        "First month": st.column_config.LineChartColumn(
            "First month",
            width="large",
            help="First 30 time-ordered observations of each column.",
        ),
        "Mean": st.column_config.NumberColumn(format="%.4f"),
        "Min": st.column_config.NumberColumn(format="%.4f"),
        "Max": st.column_config.NumberColumn(format="%.4f"),
    },
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Each row corresponds to one column from the imported CSV. "
    "The 'First month' sparkline shows the first 30 observations."
)

with st.expander("Show raw first 20 rows"):
    st.dataframe(df.head(20), use_container_width=True)