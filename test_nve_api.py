import requests
import pandas as pd

url = (
    "https://biapi.nve.no/magasinstatistikk/"
    "api/Magasinstatistikk/HentOffentligData"
)

response = requests.get(url, timeout=60)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data)

print("Antall rader og kolonner:", df.shape)
print("\nKolonner:")
print(df.columns.tolist())

df["dato_Id"] = pd.to_datetime(df["dato_Id"], errors="coerce")

print("\nDatatyper:")
print(df.dtypes)

print("\nDatoområde:")
print("Fra:", df["dato_Id"].min())
print("Til:", df["dato_Id"].max())

print("\nOmrådetyper:")
print(df["omrType"].value_counts(dropna=False))

print("\nAntall manglende verdier:")
print(df.isna().sum())

print("\nDe første radene:")
print(df.head())

df.to_csv("nve_magasinstatistikk_test.csv", index=False)
print("\nLagret nve_magasinstatistikk_test.csv")
