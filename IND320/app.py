import streamlit as st

st.set_page_config(
    page_title="Reservoir Data",
    page_icon="💧",
    layout="wide"
)

st.title("Reservoir Data Analysis")
st.write("IND320 Streamlit application")

st.sidebar.title("Navigation")
st.sidebar.write("Use the pages above to explore the reservoir data.")

st.header("Welcome")
st.write(
    "This application provides an interactive view of the Norwegian "
    "reservoir dataset. The data can be explored in table and graphical form."
)