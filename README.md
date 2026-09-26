
# NMBU-IND320

IND320 project for analyzing reservoir data using Python, Jupyter Notebook, Pandas, Matplotlib, and Streamlit. The project includes data visualization, interactive analysis, and a Streamlit web application.

## Project Links

- **GitHub repository:** https://github.com/khalidrashed/NMBU-IND320
- **Streamlit app:**  https://nmbu-ind320-sscdbwzeogng9oauvspozi.streamlit.app/

## Project

This project is part of the NMBU course IND320 Data to Decision.

The project uses Norwegian reservoir data to explore reservoir levels and related time-series data. The analysis was developed in a Jupyter Notebook, while the interactive version of the analysis was implemented as a Streamlit application.

## Jupyter Notebook

The Jupyter Notebook contains the main data analysis and documentation.

The notebook includes:

- Loading the `reservoirs.csv` dataset using Pandas
- Renaming Norwegian column names to understandable English names
- Inspecting the dataset structure
- Checking data types
- Checking categorical values
- Checking missing values
- Examining the date range
- Calculating descriptive statistics
- Plotting individual variables
- Plotting categorical variables
- Plotting all numerical variables together
- Using a twin-axis plot for variables with different scales
- Using small multiples to compare numerical variables
- Project log
- Description of AI usage

## Streamlit Application

The Streamlit application provides an interactive version of the reservoir data analysis.

The application contains four pages:

1. **Home**  
   Provides an introduction to the project and navigation to the other pages.

2. **Data Table**  
   Displays the imported reservoir data and provides a row-wise visualization of the first month using `LineChartColumn()`.

3. **Plot**  
   Provides an interactive plot where the user can select a data column and a month range.

4. **About**  
   Provides information about the project, AI usage, and project work.

The application reads the reservoir data from a local CSV file and uses Streamlit caching to improve loading performance.

## Dataset

The project uses the Norwegian `reservoirs.csv` dataset.

The dataset contains:

- 14,877 observations
- 11 columns
- Data from 1995 to 2026

The main variables include:

- `date`
- `area_type`
- `area_nr`
- `iso_year`
- `iso_week`
- `fill_ratio`
- `capacity_TWh`
- `filled_TWh`
- `next_publication`
- `fill_ratio_prev_week`
- `fill_ratio_change`

The dataset contains information about reservoir filling levels, storage capacity, filled energy, previous-week filling levels, and weekly changes.

## Data Analysis

The analysis shows seasonal patterns in the reservoir data, particularly in `fill_ratio` and `filled_TWh`.

The notebook also examines the differences in scale between the numerical variables. A twin-axis visualization is used to compare filling ratios and energy values, while a small-multiples visualization provides separate panels for the main numerical variables.

Because the dataset contains observations from different reservoir areas, filtering and selecting specific areas can provide clearer time-series visualizations.

## Technologies

The project uses:

- Python
- Pandas
- NumPy
- Matplotlib
- Streamlit
- Jupyter Notebook
- Git
- GitHub
- uv

## Project Structure

```text
NMBU-IND320/
├── Notbook/
│   └── IND320_project.ipynb
│
├── Streamlit-app/
│   ├── app.py
│   ├── data_loader.py
│   ├── reservoirs.csv
│   └── pages/
│       ├── 1_Data_Table.py
│       ├── 2_Plot.py
│       └── 3_About.py
│
├── reservoirs.csv
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── README.md
└── .gitignore
