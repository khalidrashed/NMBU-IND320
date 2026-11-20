# NMBU-IND320 – Data to Decision

This project is part of the **IND320 – Data to Decision** course at the Norwegian University of Life Sciences (NMBU).

The project focuses on Norwegian reservoir data, electricity flows, weather data and machine learning for energy consumption forecasting. It uses Python, APIs, databases, data analysis, machine learning and interactive visualizations.

## Project Links

**Streamlit:** https://nmbu-ind320-sscdbwzeogng9oauvspozi.streamlit.app/

## Project Overview

The project is divided into four main parts.

### Part 1 – Reservoir Data Analysis

Part 1 focuses on exploring Norwegian reservoir statistics from NVE.

The work includes:

- Loading and exploring reservoir data
- Checking data types and missing values
- Calculating descriptive statistics
- Creating time-series plots
- Comparing reservoir variables
- Building an interactive Streamlit application

### Part 2 – Energy Data and Databases

Part 2 focuses on retrieving, processing and storing energy data.

The work includes:

- Retrieving data from the NVE and ENTSO-E APIs
- Processing data using Python and Apache Spark
- Storing data in Apache Cassandra
- Extracting data from Cassandra
- Importing prepared data into MongoDB
- Visualizing energy data in Streamlit

### Part 3 – Weather Data and Advanced Analysis

Part 3 focuses on weather data and its relationship with Norwegian energy and reservoir data.

The work includes:

- Selecting 1,000 sampling points per precipitation region
- Retrieving historical weather data from the Open-Meteo API using ERA5
- Processing temperature and precipitation data
- Applying DCT and SATV methods with SPC analysis
- Detecting anomalies using Local Outlier Factor (LOF)
- Performing STL decomposition
- Performing spectrogram analysis
- Creating plots and interactive analysis tools in Streamlit

### Part 4 – Machine Learning and Energy Consumption Forecasting

Part 4 focuses on using machine learning and time-series methods to predict future energy consumption in cooperation with Indre Salten Energi AS.

The main objective is to develop models that can forecast energy consumption for the coming days.

The analysis focuses on patterns and factors that influence energy consumption, including:

- Day of the week and weekday patterns
- Hour of the day and daily consumption patterns
- Monthly and seasonal variations
- Temperature and weather conditions
- Historical energy consumption
- Electricity prices and relevant external factors

The planned work includes:

- Exploring and preparing energy consumption data
- Performing exploratory data analysis (EDA)
- Identifying daily, weekly and seasonal patterns
- Creating time-based and weather-related features
- Developing and evaluating forecasting models
- Comparing statistical and machine learning approaches
- Visualizing forecasting results

Potential forecasting methods include:

- ARIMA and SARIMA
- Exponential Smoothing (ETS)
- Holt-Winters
- Random Forest
- XGBoost
- LSTM and GRU neural networks

The goal is to compare different approaches and identify suitable models for short-term energy consumption forecasting.

## Data Sources

### NVE Reservoir Statistics

Reservoir data is retrieved from the Norwegian Water Resources and Energy Directorate (NVE).

The dataset includes:

- Reservoir filling levels
- Storage capacity
- Filled energy in TWh
- Weekly changes
- Water and electricity area information

The Streamlit application loads reservoir data from MongoDB instead of depending on a local CSV file.

### ENTSO-E Electricity Data

Electricity flow data is retrieved from the ENTSO-E API.

The data includes:

- Timestamps
- Electricity flow in MW
- Source and destination areas
- Connections between countries
- Flow direction

The data is processed and stored using Cassandra, Spark and MongoDB.

### Weather Data – Open-Meteo and ERA5

Historical weather data is retrieved using the Open-Meteo API and ERA5 data.

The main weather variables are:

- Temperature at 2 metres
- Precipitation
- Geographic coordinates
- Observation time
- Weather sampling point and region

The weather data is used for time-series analysis, anomaly detection and visualization. It can also support energy consumption forecasting.

### Energy Consumption Data – Indre Salten Energi AS

Part 4 uses energy consumption data provided in cooperation with Indre Salten Energi AS.

The data is intended for analysing historical consumption and developing short-term forecasting models.

The analysis focuses on:

- Historical energy consumption
- Daily and weekly consumption patterns
- Seasonal variations
- Weather-related effects
- Time-based consumption patterns

Weather and calendar information can be combined with historical consumption to improve forecasting performance.

## Data Processing and Storage

The project uses different tools to collect, process, store and analyse data.

The main workflow is:

1. Retrieve data from the NVE, ENTSO-E and Open-Meteo APIs.
2. Process and prepare the data using Python and Pandas.
3. Use Apache Spark for data processing where required.
4. Store energy data in Cassandra.
5. Extract and transfer prepared data to MongoDB.
6. Load reservoir and weather data from MongoDB into Streamlit.
7. Prepare historical energy consumption data for machine learning.
8. Analyse and visualize the data using interactive charts, maps and forecasting models.

## Streamlit Application

The Streamlit application brings the project's datasets and analysis tools together.

It includes the following sections:

### Home
Introduction to the IND320 project and an overview of the available data.

### Data

- Data Table
- ENTSO-E
- Reservoir Statistics
- Meteorological Data
- Currency Rates

### Analysis

- Plot
- Time Series Analysis
- Data Quality Analysis
- SATV
- Local Outlier Factor (LOF)
- Sliding Window Correlation

### Geographic Analysis

- Interactive Map
- Norwegian electricity price areas
- NVE weather regions
- Reservoir statistics

### Machine Learning

- Reservoir Forecasting
- SARIMAX
- Random Forest

Part 4 also includes a separate machine learning notebook for energy consumption forecasting.

The application uses MongoDB Atlas to load stored data. This reduces its dependence on local CSV files and makes the data available to the deployed Streamlit application.

## Analysis Methods

The project uses several statistical and machine learning methods.

| Method | Purpose |
|---|---|
| DCT | Frequency-based analysis of time-series data |
| SATV | Signal processing and noise reduction |
| SPC | Statistical process control and anomaly analysis |
| LOF | Detection of unusual observations |
| STL | Separating trend, seasonal and residual components |
| Spectrogram | Studying frequency changes over time |
| ARIMA/SARIMA | Statistical time-series forecasting |
| ETS | Exponential smoothing for forecasting |
| Holt-Winters | Forecasting with trend and seasonality |
| Random Forest | Machine learning forecasting |
| XGBoost | Gradient boosting for forecasting |
| LSTM/GRU | Neural network models for sequential data |

## Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Plotly
- Streamlit
- GeoPandas
- Folium
- Scikit-learn
- Statsmodels
- XGBoost
- TensorFlow/Keras
- Jupyter Notebook
- Open-Meteo API
- ERA5
- NVE API
- ENTSO-E API
- Apache Spark
- Apache Cassandra
- MongoDB Atlas
- Git and GitHub

## Project Structure

The main project structure is organized as follows:

```text
NMBU-IND320/
├── devcontainer/
├── Notbook/
│   ├── Part1/
│   ├── Part2/
│   ├── Part3/
│   └── Part4/
│──shapefiles/      
│
├── Streamlit-app/
│   ├── app.py
│   ├── data_loader.py
│   │
│   └── pages/
│       ├── home.py
│       ├── about.py
│       ├── 1_Data_Table.py
│       ├── 2_Plot.py
│       ├── 4_ENTSOE.py
│       ├── 5_Reservoir_Statistics.py
│       ├── 6_Meteorological_Data.py
│       ├── 7_Time_Series_Analysis.py
│       ├── 8_Data_Quality_Analysis.py
│       ├── interactive_map.py
│       ├── forecasting.py
│       ├── satv.py
│       ├── lof.py
│       ├── sliding_window.py
│       └── currency_rates.py
│
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

Note: The folder and file names above should match the final structure in the GitHub repository.

## Running the Streamlit Application

Clone the repository:

```bash
git clone https://github.com/khalidrashed/NMBU-IND320.git
```

Open the project folder:

```bash
cd NMBU-IND320
```

Install the required dependencies:

```bash
pip install -r Streamlit-app/requirements.txt
```

Configure the MongoDB connection string using the `MONGODB_URI` environment variable or Streamlit Secrets.

Start the application:

```bash
streamlit run Streamlit-app/app.py
```

## AI Usage

AI tools were used as support during the project.

They helped with:

- Understanding Python code and error messages
- Debugging and improving code
- Explaining statistical and machine learning methods
- Improving data visualizations
- Structuring documentation
- Supporting the development of the Streamlit application

The data processing, analysis, implementation and interpretation were reviewed as part of the project work.

## Conclusion

This project combines energy data, reservoir statistics, weather observations and machine learning in one data analysis and visualization project.

Across its four parts, the project demonstrates how APIs, databases, statistical methods and machine learning can be used to explore Norwegian energy-related data, identify patterns, detect anomalies and develop forecasting models.

The project also provides practical experience with data engineering, time-series analysis, interactive visualization and predictive modelling.

**Course:** IND320 – Data to Decision, Student Khalid Rashed 
**University:** Norwegian University of Life Sciences (NMBU)
