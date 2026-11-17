from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.title("Interactive Energy and Weather Map")
st.caption(
    "Explore Norwegian electricity areas, NVE weather regions "
    "and reservoir statistics."
)

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent
DATA_DIR = PROJECT_DIR / "Notbook" / "Part3"

PRICE_GEOJSON = (
    DATA_DIR / "shapefiles" / "electricity_areas" / "electricity_areas_wgs84.geojson"
)

WEATHER_GEOJSON = (
    DATA_DIR / "shapefiles" / "precipitation_areas" / "nve_regions.geojson"
)

RESERVOIR_CSV = PROJECT_DIR / "reservoirs.csv"
POINTS_CSV = DATA_DIR / "data" / "weather" / "random_points_2024.csv"


# --------------------------------------------------
# Data loading
# --------------------------------------------------


@st.cache_data
def load_reservoirs():
    df = pd.read_csv(RESERVOIR_CSV)
    df["dato_Id"] = pd.to_datetime(df["dato_Id"])
    return df


@st.cache_data
def load_geodata(path):
    return gpd.read_file(path).to_crs("EPSG:4326")


@st.cache_data
def load_weather_points():
    return pd.read_csv(POINTS_CSV)


# --------------------------------------------------
# Check and load files
# --------------------------------------------------

required_files = [
    PRICE_GEOJSON,
    WEATHER_GEOJSON,
    RESERVOIR_CSV,
    POINTS_CSV,
]

missing = [str(path) for path in required_files if not path.exists()]

if missing:
    st.error("Missing data files:")
    for file in missing:
        st.write(file)
    st.stop()

try:
    reservoirs = load_reservoirs()
    price_areas = load_geodata(PRICE_GEOJSON)
    weather_regions = load_geodata(WEATHER_GEOJSON)
    weather_points = load_weather_points()

except Exception as error:
    st.error(f"Could not load data: {error}")
    st.stop()


# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------

st.sidebar.header("Map settings")

map_type = st.sidebar.selectbox(
    "Select map layer",
    ["Price Area", "Weather Area", "Water Area"],
)

reservoir_variable = st.sidebar.selectbox(
    "Reservoir variable",
    ["fyllingsgrad", "fylling_TWh", "endring_fyllingsgrad"],
)

weather_variable = st.sidebar.selectbox(
    "Weather variable",
    ["temperature_2m", "precipitation"],
)

date_min = reservoirs["dato_Id"].min().date()
date_max = reservoirs["dato_Id"].max().date()

selected_date = st.sidebar.date_input(
    "Select date",
    value=date_max,
    min_value=date_min,
    max_value=date_max,
)


# --------------------------------------------------
# Helper: Create map with clickable polygons
# --------------------------------------------------


def create_polygon_map(gdf, area_column, value_column):
    map_center = [64.5, 12]

    map_object = folium.Map(
        location=map_center,
        zoom_start=4,
        tiles="CartoDB positron",
    )

    values = pd.to_numeric(gdf[value_column], errors="coerce").dropna()

    if not values.empty:
        minimum = float(values.min())
        maximum = float(values.max())

        if minimum == maximum:
            maximum = minimum + 0.001

        colormap = LinearColormap(
            colors=["#edf8fb", "#66c2a4", "#006d2c"],
            vmin=minimum,
            vmax=maximum,
        )
        colormap.caption = value_column
        colormap.add_to(map_object)

    else:
        colormap = None

    def style_function(feature):
        value = feature["properties"].get(value_column)

        if value is None or colormap is None:
            fill_color = "#bdbdbd"
        else:
            fill_color = colormap(float(value))

        return {
            "fillColor": fill_color,
            "color": "#263238",
            "weight": 2,
            "fillOpacity": 0.7,
        }

    tooltip_fields = [area_column, value_column]

    folium.GeoJson(
        gdf.to_json(),
        name="Geographical areas",
        style_function=style_function,
        highlight_function=lambda feature: {
            "weight": 4,
            "color": "#ff7800",
            "fillOpacity": 0.9,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=["Area:", "Value:"],
            sticky=True,
        ),
    ).add_to(map_object)

    return map_object


# --------------------------------------------------
# Price Area Map
# --------------------------------------------------

if map_type == "Price Area":

    st.subheader("Electricity Price Areas")

    price_data = reservoirs[
        (reservoirs["omrType"] == "EL")
        & (reservoirs["dato_Id"].dt.date == selected_date)
    ].copy()

    price_data["area"] = "NO" + price_data["omrnr"].astype(int).astype(str)

    map_data = price_areas.merge(
        price_data[["area", reservoir_variable]],
        left_on="ElSpotOmr",
        right_on="area",
        how="left",
    )

    map_object = create_polygon_map(
        map_data,
        "ElSpotOmr",
        reservoir_variable,
    )

    result = st_folium(
        map_object,
        width=None,
        height=600,
        key="price_area_map",
    )

    # Identify clicked polygon from its coordinates
    clicked = result.get("last_object_clicked")

    if clicked:
        point = gpd.GeoSeries(
            gpd.points_from_xy(
                [clicked["lng"]],
                [clicked["lat"]],
            ),
            crs="EPSG:4326",
        ).iloc[0]

        matches = map_data[map_data.geometry.intersects(point)]

        if not matches.empty:
            selected = matches.iloc[0]["ElSpotOmr"]
            st.session_state["selected_area"] = selected
            st.session_state["selected_area_type"] = "EL"

    current_selection = st.session_state.get("selected_area")

    if current_selection in map_data["ElSpotOmr"].values:
        st.success(f"Selected electricity area: {current_selection}")

        selected_value = map_data.loc[
            map_data["ElSpotOmr"] == current_selection,
            reservoir_variable,
        ]

        if not selected_value.empty and pd.notna(selected_value.iloc[0]):
            st.metric(
                reservoir_variable,
                f"{selected_value.iloc[0]:.3f}",
            )


# --------------------------------------------------
# Weather Area Map
# --------------------------------------------------

elif map_type == "Weather Area":

    st.subheader("NVE Weather Regions")

    weather_map = weather_regions.copy()

    # Weather measurements are not yet available in this CSV.
    # The map therefore shows the geographical regions only.

    weather_map["weather_value"] = 0.0

    map_object = create_polygon_map(
        weather_map,
        "REGIONNAVN",
        "weather_value",
    )

    result = st_folium(
        map_object,
        width=None,
        height=600,
        key="weather_area_map",
    )

    clicked = result.get("last_object_clicked")

    if clicked:
        point = gpd.GeoSeries(
            gpd.points_from_xy(
                [clicked["lng"]],
                [clicked["lat"]],
            ),
            crs="EPSG:4326",
        ).iloc[0]

        matches = weather_map[weather_map.geometry.intersects(point)]

        if not matches.empty:
            selected = matches.iloc[0]["REGION"]
            st.session_state["selected_area"] = selected
            st.session_state["selected_area_type"] = "WEATHER"

    selected_region = st.session_state.get("selected_area")

    if (
        st.session_state.get("selected_area_type") == "WEATHER"
        and selected_region is not None
    ):
        st.success(f"Selected weather region: {selected_region}")

        region_points = weather_points[weather_points["REGION"] == selected_region]

        st.metric("Sampling points", len(region_points))

        st.caption(
            "Historical weather measurements must be connected "
            "before this map can display actual weather values."
        )


# --------------------------------------------------
# Water Area
# --------------------------------------------------

else:

    st.subheader("Water Reservoir Regions")

    water_data = reservoirs[
        (reservoirs["omrType"] == "VASS")
        & (reservoirs["dato_Id"].dt.date == selected_date)
    ].copy()

    if water_data.empty:
        st.warning("No reservoir data is available for this date.")

    else:

        water_data["area"] = "VASS " + water_data["omrnr"].astype(int).astype(str)

        import plotly.express as px

        fig = px.bar(
            water_data,
            x="area",
            y=reservoir_variable,
            title=f"Water Reservoir Regions – {selected_date}",
            labels={
                "area": "Water area",
                reservoir_variable: reservoir_variable,
            },
        )

        st.plotly_chart(fig, use_container_width=True)

        selected_area = st.selectbox(
            "Select water area",
            sorted(water_data["area"].unique()),
        )

        st.session_state["selected_area"] = selected_area
        st.session_state["selected_area_type"] = "VASS"

        selected_value = water_data.loc[
            water_data["area"] == selected_area,
            reservoir_variable,
        ]

        if not selected_value.empty:
            st.metric(
                reservoir_variable,
                f"{selected_value.iloc[0]:.3f}",
            )
