import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Page title
# --------------------------------------------------

st.title("⚡ IND320 Energy Dashboard")

st.markdown("""
Welcome to the **IND320 Energy Dashboard**.

This application combines energy market data, reservoir statistics,
meteorological observations and machine learning tools.

Use the navigation menu to explore the available datasets,
perform exploratory analysis and investigate forecasting methods.
""")

st.divider()

# --------------------------------------------------
# Load reservoir data
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "reservoirs.csv"


@st.cache_data
def load_reservoir_data(file_path):
    return pd.read_csv(file_path)


st.subheader("📊 Data Overview")

if DATA_FILE.exists():
    try:
        df = load_reservoir_data(str(DATA_FILE))

        col1, col2, col3 = st.columns(3)

        col1.metric("Total observations", f"{len(df):,}")

        col2.metric("Number of variables", len(df.columns))

        if "area_type" in df.columns:
            col3.metric("Area types", df["area_type"].nunique())
        else:
            col3.metric("Area types", "Not available")

        with st.expander("Preview reservoir dataset"):
            st.dataframe(df.head(10), use_container_width=True)

    except Exception as error:
        st.error(f"Could not load reservoir data: {error}")

else:
    st.warning(f"Reservoir dataset was not found: {DATA_FILE}")

st.divider()

# --------------------------------------------------
# Main application sections
# --------------------------------------------------

st.subheader("Application Sections")

col1, col2 = st.columns(2)

with col1:

    st.markdown("""
    ### 📊 Data Overview

    - Reservoir Statistics
    - ENTSO-E Energy Data
    - Meteorological Data
    - Currency Rates

    ### 📈 Exploratory Analysis

    - Time Series Analysis
    - SATV
    - Local Outlier Factor (LOF)
    - Data Quality Analysis
    """)

with col2:

    st.markdown("""
    ### 🗺️ Geographic Analysis

    - Interactive GeoJSON Map
    - Price and Water Areas
    - Weather Data Visualization

    ### 🔮 Predictive Analysis

    - Reservoir Forecasting
    - SARIMAX
    - Machine Learning
    - Exogenous Variables
    """)

st.divider()

# --------------------------------------------------
# Project information
# --------------------------------------------------

st.subheader("About the Project")

st.write("""
This dashboard was developed as part of the IND320 project
at the Norwegian University of Life Sciences (NMBU).

It brings together energy data, reservoir information,
weather observations, data visualisation and machine learning
in one interactive application.
""")

st.info(
    "Select a page from the navigation menu on the left "
    "to explore the different features."
)

# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption("IND320 – Energy Data Analysis and Machine Learning | NMBU")
