import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="IND320 Energy Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Shared session state
# --------------------------------------------------

if "selected_area" not in st.session_state:
    st.session_state["selected_area"] = "NO1"

if "selected_area_type" not in st.session_state:
    st.session_state["selected_area_type"] = "EL"

if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None

if "weather_variable" not in st.session_state:
    st.session_state["weather_variable"] = "temperature_2m"

if "forecast_horizon" not in st.session_state:
    st.session_state["forecast_horizon"] = 12


# --------------------------------------------------
# Navigation
# --------------------------------------------------

pages = {
    "Home": [
        st.Page(
            "pages/home.py",
            title="Home",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/about.py",
            title="About the Project",
            icon="ℹ️",
        ),
    ],
    "Data": [
        st.Page(
            "pages/1_Data_Table.py",
            title="Data Table",
            icon="📋",
        ),
        st.Page(
            "pages/4_ENTSOE.py",
            title="ENTSO-E",
            icon="⚡",
        ),
        st.Page(
            "pages/5_Reservoir_Statistics.py",
            title="Reservoir Statistics",
            icon="💧",
        ),
        st.Page(
            "pages/6_Meteorological_Data.py",
            title="Meteorological Data",
            icon="🌦️",
        ),
        st.Page(
            "pages/currency_rates.py",
            title="Currency Rates",
            icon="💱",
        ),
    ],
    "Analysis": [
        st.Page(
            "pages/2_Plot.py",
            title="Plot",
            icon="📈",
        ),
        st.Page(
            "pages/7_Time_Series_Analysis.py",
            title="Time Series Analysis",
            icon="📊",
        ),
        st.Page(
            "pages/8_Data_Quality_Analysis.py",
            title="Data Quality Analysis",
            icon="🔍",
        ),
        st.Page(
            "pages/satv.py",
            title="SATV",
            icon="🌡️",
        ),
        st.Page(
            "pages/lof.py",
            title="Local Outlier Factor",
            icon="📉",
        ),
        st.Page(
            "pages/sliding_window.py",
            title="Sliding Window Correlation",
            icon="🔗",
        ),
    ],
    "Geographic Analysis": [
        st.Page(
            "pages/interactive_map.py",
            title="Interactive Map",
            icon="🗺️",
        ),
    ],
    "Machine Learning": [
        st.Page(
            "pages/forecasting.py",
            title="Reservoir Forecasting",
            icon="🔮",
        ),
    ],
}


# --------------------------------------------------
# Run navigation
# --------------------------------------------------

navigation = st.navigation(pages)

navigation.run()
