import pandas as pd

df = pd.read_csv("nve_magasinstatistikk_test.csv")
df["dato_Id"] = pd.to_datetime(df["dato_Id"], errors="coerce")

keys = ["dato_Id", "omrType", "omrnr"]

print("Duplikater på dato, områdetype og områdenummer:")
print(df.duplicated(subset=keys).sum())

print("\nAntall rader med plassholderdato:")
print((df["neste_Publiseringsdato"] == "0001-01-01T00:00:00").sum())

print("\nAntall rader per områdetype og områdenummer:")
print(df.groupby(["omrType", "omrnr"]).size().to_string())

print("\nSortert datoutvalg:")
print(df.sort_values("dato_Id")[["dato_Id", "omrType", "omrnr"]].head())
