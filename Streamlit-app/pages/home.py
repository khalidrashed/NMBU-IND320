import streamlit as st
from data_loader import load_data

# --------------------------------------------------
# Page title
# --------------------------------------------------

st.title("⚡ IND320 Energy Dashboard")

st.markdown("""
Welcome to the **IND320 Energy Dashboard**.

This application combines energy market data, reservoir statistics,
meteorological observations and data quality analysis.

Use the navigation menu to explore the available datasets
and perform exploratory analysis.
""")

st.divider()

# --------------------------------------------------
# Load reservoir data from MongoDB
# --------------------------------------------------

st.subheader("📊 Data Overview")

try:
    # Shared loader reads from MongoDB Atlas:
    # database: ind320
    # collection: nve_magasinstatistikk
    df = load_data()

    if df is None or df.empty:
        st.warning("The reservoir collection in MongoDB contains no records.")
    else:
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
    st.error(f"Could not load reservoir data from MongoDB: {error}")
    st.caption(
        "Check that MONGODB_URI is configured in Streamlit Secrets "
        "and that the app can access the MongoDB Atlas cluster."
    )

st.divider()

# --------------------------------------------------
# Main application sections: Parts 1, 2 and 3 only
# --------------------------------------------------

st.subheader("Application Sections")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📊  – Dashboard Basics

    - Reservoir Data Table
    - Reservoir Plots
    - Reservoir Statistics

    ### ⚡  – Data Sources

    - ENTSO-E Energy Data
    - MongoDB Data
    """)

with col2:
    st.markdown("""
    ### 🌦️  – Data Quality

    - Meteorological Data
    - Time Series Analysis
    - Data Quality Analysis
    - Local Outlier Factor (LOF)
    - Sliding Window Correlation

    ### 🗺️ Shared Tools

    - Interactive Map
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
weather observations and data quality analysis in one
interactive application.
""")

st.info(
    "Select a page from the navigation menu on the left "
    "to explore Parts 1, 2 and 3."
)

# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption("IND320 – Energy Data Analysis | NMBU")


