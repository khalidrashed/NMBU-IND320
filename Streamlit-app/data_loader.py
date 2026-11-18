
"""
Data loading and caching for the IND320 Streamlit app.

Loads reservoir data from reservoirs.csv,
renames columns to English, parses dates,
converts numerical columns and caches the result.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


# ==================================================
# 1. PROJECT PATHS
# ==================================================

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent

# Search for reservoirs.csv in the original locations
_CANDIDATES = [
    _HERE / "reservoirs.csv",
    _PROJECT_ROOT / "reservoirs.csv",
    _PROJECT_ROOT / "Notebook" / "reservoirs.csv",
    _PROJECT_ROOT / "Notbook" / "reservoirs.csv",
    _PROJECT_ROOT / "data" / "reservoirs.csv",
    _PROJECT_ROOT / "Notbook" / "data" / "reservoirs.csv",
]


# ==================================================
# 2. COLUMN RENAMING
# ==================================================

RENAME_MAP = {
    "dato_Id": "date",
    "dato": "date",
    "omrType": "area_type",
    "omr_type": "area_type",
    "omrnr": "area_nr",
    "omr_nr": "area_nr",
    "iso_aar": "iso_year",
    "iso_uke": "iso_week",
    "fyllingsgrad": "fill_ratio",
    "kapasitet_TWh": "capacity_TWh",
    "kapasitet_twh": "capacity_TWh",
    "fylling_TWh": "filled_TWh",
    "fylling_twh": "filled_TWh",
    "neste_Publiseringsdato": "next_publication",
    "neste_publiseringsdato": "next_publication",
    "fyllingsgrad_forrige_uke": "fill_ratio_prev_week",
    "endring_fyllingsgrad": "fill_ratio_change",
}


# ==================================================
# 3. NUMERICAL COLUMNS
# ==================================================

NUMERIC_COLS = [
    "fill_ratio",
    "capacity_TWh",
    "filled_TWh",
    "fill_ratio_prev_week",
    "fill_ratio_change",
]


# ==================================================
# 4. FIND CSV FILE
# ==================================================

def csv_path() -> Path:
    """
    Find reservoirs.csv in the project directories.
    """

    for path in _CANDIDATES:
        if path.is_file():
            return path

    searched_paths = "\n".join(
        str(path) for path in _CANDIDATES
    )

    raise FileNotFoundError(
        "Could not find reservoirs.csv.\n"
        "Searched locations:\n"
        f"{searched_paths}"
    )


# ==================================================
# 5. LOAD AND CACHE DATA
# ==================================================

@st.cache_data(show_spinner="Loading reservoir data...")
def load_data() -> pd.DataFrame:
    """
    Load, clean and cache reservoir data from CSV.
    """

    path = csv_path()

    df = pd.read_csv(path)

    # Rename columns to English
    df = df.rename(
        columns=RENAME_MAP
    ).copy()

    # Parse dates
    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    if "next_publication" in df.columns:
        df["next_publication"] = pd.to_datetime(
            df["next_publication"],
            errors="coerce"
        )

    # Convert numerical columns
    for column in NUMERIC_COLS:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Sort by date
    if "date" in df.columns:

        df = (
            df.sort_values("date")
            .reset_index(drop=True)
        )

    return df
