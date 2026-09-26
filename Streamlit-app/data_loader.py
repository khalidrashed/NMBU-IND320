"""
Data loading and caching for the IND320 Streamlit app.

Loads reservoirs.csv, renames Norwegian columns to English,
parses the date columns and caches the result for app speed.
"""
from pathlib import Path
import pandas as pd
import streamlit as st

# Look for reservoirs.csv in several likely locations.
_HERE = Path(__file__).resolve().parent
_CANDIDATES = [
    _HERE / "reservoirs.csv",
    _HERE.parent / "Notbook" / "reservoirs.csv",
    _HERE.parent / "Notebook" / "reservoirs.csv",
    _HERE.parent / "data" / "reservoirs.csv",
    _HERE.parent / "reservoirs.csv",
]
CSV_PATH = next((p for p in _CANDIDATES if p.exists()), _CANDIDATES[0])

RENAME_MAP = {
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
    "endring_fyllingsgrad": "fill_ratio_change",
}

NUMERIC_COLS = [
    "fill_ratio",
    "capacity_TWh",
    "filled_TWh",
    "fill_ratio_prev_week",
    "fill_ratio_change",
]


@st.cache_data(show_spinner="Loading reservoir data…")
def load_data() -> pd.DataFrame:
    """Load, clean and cache the reservoir CSV."""
    df = pd.read_csv(CSV_PATH)
    df = df.rename(columns=RENAME_MAP).copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    if "next_publication" in df.columns:
        df["next_publication"] = pd.to_datetime(
            df["next_publication"], errors="coerce", format="mixed"
        )
    if "date" in df.columns:
        df = df.sort_values("date").reset_index(drop=True)

    return df


def csv_path() -> Path:
    return CSV_PATH