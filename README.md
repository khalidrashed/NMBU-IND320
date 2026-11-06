# IND320 – Project Work Part 3: Data Quality
## streamlit.app: https://nmbu-ind320-fm3pwfab9yikhurblf3xns.streamlit.app/
## Project Description

This project investigates data quality in geographical, weather, and reservoir filling datasets. The objective is to explore different methods for identifying unusual observations and analysing patterns in time series data.

The project combines geographical analysis, weather data processing, anomaly detection, time series decomposition, and frequency analysis.

## Methods

The following methods are used in the project:

- **Geographical analysis:** Loading and visualizing geographical datasets, generating random geographical points, and assigning points to electricity areas using spatial joins.
- **Weather data collection:** Retrieving historical temperature and precipitation data from the Open-Meteo Historical Weather API using ERA5 data.
- **Precipitation anomaly detection:** Applying the Discrete Cosine Transform (DCT) and Statistical Process Control (SPC).
- **Temperature anomaly detection:** Using Local Outlier Factor (LOF).
- **Time series decomposition:** Applying Seasonal-Trend decomposition using LOESS (STL) to reservoir filling data.
- **Frequency analysis:** Using spectrograms to investigate frequency patterns in reservoir filling data.

## Technologies and Libraries

The project uses Python and the following libraries:

- NumPy
- Pandas
- Matplotlib
- GeoPandas
- Shapely
- SciPy
- Statsmodels
- Scikit-learn
- Requests

## Project Structure

```text
IND320_data_quality/
│
├── IND320_data_quality.ipynb
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── geographical/
│   ├── weather/
│   └── reservoirs/
│
└── figures/
```

## How to Run the Project

1. Clone the repository:

   ```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   ```

2. Navigate to the project directory:

   ```bash
   cd IND320_data_quality
   ```

3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment.

   **Windows PowerShell:**

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

5. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Start Jupyter Notebook:

   ```bash
   jupyter notebook
   ```

7. Open `IND320_data_quality.ipynb` and run the notebook cells in order.

## Data Sources

- **Open-Meteo Historical Weather API:** Historical weather data based on the ERA5 reanalysis model.
- **Geographical datasets:** Used to analyse precipitation regions and electricity areas.
- **Reservoir filling dataset:** Used for time series decomposition and spectrogram analysis.

The required input datasets must be placed in the appropriate folders before running the notebook. Some datasets may need to be obtained separately.

## Results

The project demonstrates how different methods can be used to investigate data quality:

- DCT and SPC identify potential precipitation anomalies.
- LOF identifies potential temperature anomalies.
- STL separates reservoir filling data into trend, seasonal, and residual components.
- Spectrogram analysis investigates frequency patterns over time.

Detected anomalies are not necessarily incorrect measurements. They require further investigation and interpretation.

## Reproducibility

The notebook contains the analysis steps and visualizations. To reproduce the results, use the required input datasets and install the dependencies listed in `requirements.txt`.


