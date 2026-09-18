import streamlit as st

st.set_page_config(
    page_title="Reservoir Data Analysis",
    layout="wide"
)

st.title("Reservoir Data Analysis")

st.header("Welcome")

st.write(
    "This Streamlit application provides an interactive view "
    "of the Norwegian reservoir dataset."
)

st.write(
    "The application allows users to inspect the imported data "
    "and explore the reservoir time series interactively."
)

st.subheader("Navigation")

st.write(
    "Use the navigation menu in the sidebar to access the "
    "different pages."
)
