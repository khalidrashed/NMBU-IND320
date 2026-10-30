import sys
from pathlib import Path

app_folder = Path(__file__).resolve().parent / "Streamlit-app"
sys.path.insert(0, str(app_folder))

from data_loader import load_data

df = load_data()

print("Antall rader:", len(df))
print("Kolonner:", df.columns.tolist())
print(df.head())

print("\nAntall rader per område:")
print(df.groupby(["area_type", "area_nr"]).size())