import os
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from data_loader import load_data
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


# --------------------------------------------------
# Data loading
# --------------------------------------------------


def get_mongodb_uri():
    """Read MongoDB URI from Streamlit Secrets or environment variables."""
    try:
        uri = st.secrets.get("MONGODB_URI")
    except Exception:
        uri = None
    return uri or os.getenv("MONGODB_URI")


@st.cache_data(ttl=900)
def load_reservoirs():
    # Use the project's shared loader for ind320.nve_magasinstatistikk.
    uri = get_mongodb_uri()
    if uri:
        os.environ["MONGODB_URI"] = uri

    df = load_data().copy()

    # data_loader.py normalizes the original Norwegian field names.
    rename_fallbacks = {
        "omrType": "area_type",
        "dato_Id": "date",
        "omrnr": "area_nr",
        "fyllingsgrad": "fill_ratio",
        "fylling_TWh": "filled_TWh",
        "endring_fyllingsgrad": "fill_ratio_change",
    }
    for old_name, new_name in rename_fallbacks.items():
        if new_name not in df.columns and old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    required = {"area_type", "date", "area_nr"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(
            "Reservoir collection is missing columns: "
            + ", ".join(sorted(missing))
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["area_nr"] = pd.to_numeric(df["area_nr"], errors="coerce")
    for column in ["fill_ratio", "filled_TWh", "fill_ratio_change"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.dropna(subset=["date", "area_nr"])


@st.cache_data
def load_geodata(path):
    return gpd.read_file(path).to_crs("EPSG:4326")


@st.cache_data(ttl=900)
def load_weather_points():
    """Load unique weather sampling points from ind320.weather_data."""
    uri = get_mongodb_uri()
    if not uri:
        raise ValueError(
            "MONGODB_URI is not configured. Add it to Streamlit Secrets "
            "or the local .env/environment."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    try:
        collection = client["ind320"]["weather_data"]
        cursor = collection.find(
            {},
            {
                "_id": 0,
                "point_id": 1,
                "region": 1,
                "REGION": 1,
                "latitude": 1,
                "longitude": 1,
            },
        )
        points = pd.DataFrame(list(cursor))
    finally:
        client.close()

    if points.empty:
        return pd.DataFrame(columns=["point_id", "REGION", "latitude", "longitude"])

    if "REGION" not in points.columns:
        points["REGION"] = points["region"] if "region" in points.columns else None
    elif "region" in points.columns:
        points["REGION"] = points["REGION"].fillna(points["region"])

    points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
    points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
    points = points.dropna(subset=["latitude", "longitude"])

    # One marker per sampling point, rather than one per timestamp.
    if "point_id" in points.columns:
        points = points.drop_duplicates(subset=["point_id"])
    else:
        points = points.drop_duplicates(subset=["latitude", "longitude"])

    return points


# --------------------------------------------------
# Check and load files
# --------------------------------------------------

required_files = [PRICE_GEOJSON, WEATHER_GEOJSON]
missing = [str(path) for path in required_files if not path.exists()]

if missing:
    st.error("Missing geographical boundary files:")
    for file in missing:
        st.write(file)
    st.info(
        "Reservoir and weather-point records are loaded from MongoDB. "
        "The electricity-area and NVE-region GeoJSON boundary files "
        "must still be included in the project."
    )
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

reservoir_variable_labels = {
    "Filling level (%)": "fill_ratio",
    "Filled volume (TWh)": "filled_TWh",
    "Weekly change (percentage points)": "fill_ratio_change",
}
reservoir_variable_label = st.sidebar.selectbox(
    "Reservoir variable",
    list(reservoir_variable_labels.keys()),
)
reservoir_variable = reservoir_variable_labels[reservoir_variable_label]

if reservoir_variable not in reservoirs.columns:
    st.error(
        f"The selected variable '{reservoir_variable}' is not available "
        "in the MongoDB reservoir collection."
    )
    st.stop()

weather_variable = st.sidebar.selectbox(
    "Weather variable",
    ["temperature_2m", "precipitation"],
)

if reservoirs.empty:
    st.error("MongoDB returned no reservoir records.")
    st.stop()

date_min = reservoirs["date"].min().date()
date_max = reservoirs["date"].max().date()

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
        (reservoirs["area_type"].astype(str).str.upper() == "EL")
        & (reservoirs["date"].dt.date == selected_date)
    ].copy()

    price_data["area"] = "NO" + price_data["area_nr"].astype(int).astype(str)

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

    # Display the NVE region boundaries and the MongoDB sampling locations.
    weather_map["weather_value"] = 0.0

    map_object = create_polygon_map(
        weather_map,
        "REGIONNAVN",
        "weather_value",
    )

    # Plot the MongoDB sampling locations on top of the NVE polygons.
    points_layer = folium.FeatureGroup(name="Weather sampling points")
    for _, point_row in weather_points.iterrows():
        folium.CircleMarker(
            location=[point_row["latitude"], point_row["longitude"]],
            radius=3,
            color="#1f78b4",
            fill=True,
            fill_opacity=0.75,
            tooltip=(
                f"Region: {point_row.get('REGION', 'N/A')} | "
                f"Point ID: {point_row.get('point_id', 'N/A')}"
            ),
        ).add_to(points_layer)
    points_layer.add_to(map_object)
    folium.LayerControl().add_to(map_object)

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

        region_points = weather_points[
            weather_points["REGION"].astype(str).str.upper()
            == str(selected_region).upper()
        ]

        st.metric("Sampling points", len(region_points))

        if region_points.empty:
            st.info(
                "No MongoDB weather sampling points were found for this region. "
                "Check the region values in ind320.weather_data."
            )


# --------------------------------------------------
# Water Area
# --------------------------------------------------

else:

    st.subheader("Water Reservoir Regions")

    water_data = reservoirs[
        (reservoirs["area_type"].astype(str).str.upper() == "VASS")
        & (reservoirs["date"].dt.date == selected_date)
    ].copy()

    if water_data.empty:
        st.warning("No reservoir data is available for this date.")

    else:

        water_data["area"] = "VASS " + water_data["area_nr"].astype(int).astype(str)

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
