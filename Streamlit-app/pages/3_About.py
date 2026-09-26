"""
Page 4: About — project description, AI usage, work log, links.
"""
import streamlit as st

st.title("ℹ️ About")

st.header("IND320 Reservoir Data Analysis")

st.write(
    "This Streamlit application was developed as part of the IND320 project "
    "at NMBU. It provides an interactive way to explore the Norwegian "
    "reservoir dataset."
)

st.subheader("Application features")
st.write("- Imported reservoir data")
st.write("- Data table with first-month visualisations using LineChartColumn")
st.write("- Interactive time-series plots")
st.write("- Column selection (single column or all numeric columns)")
st.write("- Month-range selection")
st.write("- Filtering by area_type and area_nr")

st.subheader("Technologies")
st.write("- Python")
st.write("- Pandas")
st.write("- Matplotlib")
st.write("- Plotly")
st.write("- Streamlit")
st.write("- Jupyter Notebook")
st.write("- uv")

# ---------------------------------------------------------------------------
# Project links
# ---------------------------------------------------------------------------
st.header("Project links")

st.markdown(
    "- [GitHub repository](https://github.com/khalidrashed/NMBU-IND320)\n"
    "- [Streamlit application](https://nmbu-ind320-khalid-rashed.streamlit.app/)"
)