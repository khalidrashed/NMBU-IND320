
"""
Data loading and caching for the IND320 Streamlit app.

Loads reservoir data from MongoDB Atlas, renames columns to English,
parses dates and caches the result.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

# Find the project root and load its .env file.
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)

RENAME_MAP = {
    "dato": "date",
    "omr_type": "area_type",
    "omr_nr": "area_nr",
    "iso_aar": "iso_year",
    "iso_uke": "iso_week",
    "fyllingsgrad": "fill_ratio",
    "kapasitet_twh": "capacity_TWh",
    "fylling_twh": "filled_TWh",
    "neste_publiseringsdato": "next_publication",
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


@st.cache_data(show_spinner="Loading reservoir data from MongoDB…")
def load_data() -> pd.DataFrame:
    """Load, clean and cache reservoir data from MongoDB."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is missing. Check the .env file in the project root."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)

    try:
        collection = client["ind320"]["nve_magasinstatistikk"]
        documents = list(collection.find({}, {"_id": 0}))
    finally:
        client.close()

    if not documents:
        raise RuntimeError(
            "No documents found in MongoDB collection ind320.nve_magasinstatistikk."
        )

    df = pd.DataFrame(documents).rename(columns=RENAME_MAP).copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")

    if "next_publication" in df.columns:
        df["next_publication"] = pd.to_datetime(
            df["next_publication"], errors="coerce", format="mixed"
        )

    for column in NUMERIC_COLS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "date" in df.columns:
        df = df.sort_values("date").reset_index(drop=True)

    return df


def csv_path() -> Path:
    """Kept for compatibility with existing app code."""
    return _HERE / "reservoirs.csv"
