# NMBU-IND320

This project is part of the NMBU course IND320 Data to Decision. It explores Norwegian reservoir data and cross-border electricity flows using Python, APIs, data processing, databases, and interactive visualizations.

## Project Links

- **GitHub repository:** https://github.com/khalidrashed/NMBU-IND320
- **Streamlit app:** https://nmbu-ind320-sscdbwzeogng9oauvspozi.streamlit.app/

## Project Overview

The project has two main parts:

- **Part 1:** Explore Norwegian reservoir data through a Jupyter Notebook and an interactive Streamlit application.
- **Part 2:** Retrieve data from the NVE and ENTSO-E APIs, process and store data using Cassandra, Spark, and MongoDB, and visualize the results in Streamlit.

## Data Sources

### NVE Reservoir Data

Reservoir data is retrieved from the Norwegian Water Resources and Energy Directorate (NVE). The data includes reservoir filling levels, storage capacity, filled energy, and weekly changes.

The Streamlit application uses data stored in MongoDB rather than depending only on a local CSV file.

### ENTSO-E Cross-Border Electricity Flows

The project retrieves cross-border electricity flow data to and from Norway from the ENTSO-E API.

The data includes timestamps, electricity flow in MW, source and destination areas, connections, and flow direction. The data is processed and stored in Cassandra, extracted using Spark, and imported into MongoDB for visualization.

## Jupyter Notebook

The Jupyter Notebook documents the data analysis and project work.

It includes:

- Loading and exploring reservoir data
- Inspecting data types and missing values
- Calculating descriptive statistics
- Creating time-series plots and other visualizations
- Comparing numerical variables with different scales
- Documenting project work and AI usage

## Streamlit Application

The Streamlit application provides interactive data tables and visualizations.

The application includes:

1. **Home:** Introduction to the project.
2. **Data Table:** Displays reservoir data.
3. **Plot:** Interactive plots with controls for selecting data and time periods.
4. **About:** Project information and documentation.
5. **ENTSO-E:** Visualizes cross-border electricity flows using interactive charts.

The ENTSO-E page includes a pie chart showing estimated energy flow into and out of Norway for a selected connection and year, as well as a line chart for selected months.

## Data Processing and Storage

The project uses the following data pipeline:

1. Retrieve reservoir and electricity flow data from external APIs.
2. Load and process data using Python and Spark.
3. Store processed data in Cassandra.
4. Extract ENTSO-E data from Cassandra using Spark.
5. Import prepared data into MongoDB.
6. Load data from MongoDB into Streamlit for interactive visualization.

## Technologies

- Python
- Pandas and NumPy
- Matplotlib
- Streamlit
- Jupyter Notebook
- NVE API
- ENTSO-E API
- Apache Spark
- Apache Cassandra
- MongoDB
- Git and GitHub

## Project Structure

```text
NMBU-IND320/
├── Notbook/
│   └── IND320_project.ipynb
├── Streamlit-app/
│   ├── app.py
│   ├── data_loader.py
│   ├── load_entsoe_to_cassandra.py
│   ├── load_entsoe_to_mongodb.py
│   ├── load_entsoe_export_to_mongodb.py
│   ├── extract_entsoe_from_cassandra.py
│   └── pages/
│       ├── 1_Data_Table.py
│       ├── 2_Plot.py
│       ├── 3_About.py
│       └── 4_ENTSOE.py
├── entsoe_data.py
├── load_nve_to_cassandra.py
├── export_nve_to_mongodb.py
├── reservoirs.csv
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore
```

## Notes

API credentials and database connection strings should be stored in environment variables and must not be committed to GitHub.

The project uses a separate development branch for Part 2 until peer review is complete.