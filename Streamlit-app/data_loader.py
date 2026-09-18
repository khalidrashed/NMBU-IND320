import pandas as pd
import streamlit as st
from pathlib import Path


@st.cache_data
def load_data():

    file_path = Path(__file__).resolve().parent / "reservoirs.csv"

    df_raw = pd.read_csv(file_path)

    rename_map = {
        "dato_Id": "date",
        "omrType": "area_type",
        "omrnr": "area_nr",
        "iso_aar": "iso_year",
        "iso_uke": "iso_week",
        "fyllingsgrad": "fill_ratio",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "filled_TWh",
        "neste_Publiseringsdato": "next_publication",
        "fyllingsgrad_forrige_uke": "fill_ratio_prev_week",
        "endring_fyllingsgrad": "fill_ratio_change"
    }

    df = df_raw.rename(columns=rename_map).copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
        format="mixed"
    )

    df["next_publication"] = pd.to_datetime(
        df["next_publication"],
        errors="coerce",
        format="mixed"
    )

    df = df.sort_values("date").reset_index(drop=True)

    return df