import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(page_title="About IND320", page_icon="ℹ️", layout="wide")


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("ℹ️ About the IND320 Project")

st.markdown("""
# Norwegian Energy and Reservoir Data Analysis

This project explores Norwegian hydropower reservoirs, electricity
markets, meteorological conditions and energy-related data.

The project is divided into four parts. Each part builds on the
previous work, from initial data exploration to data integration,
advanced analysis and machine learning.
""")

st.divider()


# --------------------------------------------------
# Project overview
# --------------------------------------------------

st.header("Project Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Project Parts", "4")

with col2:
    st.metric("Main Programming Language", "Python")

with col3:
    st.metric("Main Application", "Streamlit")

with col4:
    st.metric("Main Data Domain", "Energy")


st.divider()


# --------------------------------------------------
# Part 1
# --------------------------------------------------

st.header("Part 1 – Data Exploration and Visualization")

st.markdown("""
The first part focused on exploring and understanding Norwegian
reservoir statistics.

The main objective was to become familiar with the dataset,
investigate its structure and create meaningful visualizations.
""")

with st.expander("Explore Part 1", expanded=True):

    st.markdown("""
    **Main activities:**

    - Loaded and inspected the reservoir dataset using Pandas.
    - Examined dataset dimensions, columns and data types.
    - Converted date columns into datetime format.
    - Renamed columns to improve readability.
    - Explored reservoir filling levels and available capacity.
    - Created separate and combined visualizations.
    - Used categorical plots, time-series plots and small multiples.
    - Investigated relationships between reservoir variables.

    **Technologies:**

    - Python
    - Pandas
    - Matplotlib
    - Streamlit

    **Outcome:**

    An initial data analysis and visualization application
    for exploring Norwegian reservoir statistics.
    """)


# --------------------------------------------------
# Part 2
# --------------------------------------------------

st.header("Part 2 – Data Sources and Data Integration")

st.markdown("""
The second part expanded the project by integrating data from
multiple energy-related sources.

The objective was to collect, process and store data that could
be used for further analysis and visualization.
""")

with st.expander("Explore Part 2"):

    st.markdown("""
    **Main activities:**

    - Retrieved reservoir statistics from the NVE data source.
    - Worked with different reservoir area types:
      EL, NO and VASS.
    - Retrieved electricity cross-border flow data from ENTSO-E.
    - Investigated electricity flows to and from Norway.
    - Worked with Cassandra for data storage.
    - Used Spark for data processing.
    - Integrated MongoDB for application data access.
    - Recreated reservoir and electricity-flow visualizations.

    **Technologies:**

    - Python
    - Pandas
    - NVE API
    - ENTSO-E API
    - Apache Cassandra
    - Apache Spark
    - MongoDB

    **Outcome:**

    A broader data foundation combining reservoir statistics
    and electricity-market information.
    """)


# --------------------------------------------------
# Part 3
# --------------------------------------------------

st.header("Part 3 – Meteorological Data and Advanced Analysis")

st.markdown("""
The third part extended the project with meteorological and
geographical information.

The objective was to investigate how weather conditions,
reservoir statistics and electricity-related data can be
analysed together.
""")

with st.expander("Explore Part 3"):

    st.markdown("""
    **Main activities:**

    - Retrieved meteorological data using Open-Meteo.
    - Worked with temperature and precipitation observations.
    - Processed and analysed weather datasets.
    - Worked with geographical shapefiles and GeoJSON.
    - Investigated Norwegian electricity and precipitation regions.
    - Performed time-series analysis.
    - Conducted data-quality analysis.
    - Explored relationships between weather and reservoir data.
    - Added meteorological and statistical pages to Streamlit.

    **Technologies:**

    - Python
    - Pandas
    - Open-Meteo API
    - GeoPandas
    - GeoJSON
    - Plotly
    - Streamlit

    **Outcome:**

    An expanded application with meteorological data,
    geographical information, time-series analysis
    and data-quality investigations.
    """)



# --------------------------------------------------
# Data sources
# --------------------------------------------------

st.header("Main Data Sources")

sources = [
    {
        "name": "NVE – Norwegian Water Resources and Energy Directorate",
        "description": "Reservoir statistics and hydrological information.",
    },
    {
        "name": "ENTSO-E",
        "description": "European electricity market and cross-border flow data.",
    },
    {
        "name": "Open-Meteo",
        "description": "Meteorological observations such as temperature and precipitation.",
    },
    {"name": "Norges Bank", "description": "Exchange-rate data used in the project."},
]

for source in sources:

    with st.container(border=True):

        st.subheader(source["name"])
        st.write(source["description"])


# --------------------------------------------------
# Technologies
# --------------------------------------------------

st.header("Technologies and Tools")

technologies = [
    "Python",
    "Pandas",
    "NumPy",
    "Scikit-learn",
    "Statsmodels",
    "Plotly",
    "Streamlit",
    "Folium",
    "GeoPandas",
    "Apache Spark",
    "Apache Cassandra",
    "MongoDB",
    "Git and GitHub",
]

st.markdown(" | ".join(technologies))


# --------------------------------------------------
# Final section
# --------------------------------------------------

st.divider()

st.header("Project Development")

st.markdown("""
The four project parts demonstrate a gradual development
from basic data exploration to an interactive analytical
application with data integration and machine learning.

The final application brings together reservoir statistics,
electricity information, meteorological observations,
geographical visualization and forecasting.

**IND320 – Energy Data Analysis and Machine Learning**
""")

st.caption(
    "Project documentation and application developed as part "
    "of the IND320 course at NMBU."
)
