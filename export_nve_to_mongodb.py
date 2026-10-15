
import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
if not uri:
    raise ValueError("MONGODB_URI mangler i .env-filen.")

df = pd.read_csv("nve_cassandra_export.csv")
df = df.astype(object).where(pd.notna(df), None)

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    print("Tilkobling til MongoDB fungerer.")

    db = client["ind320"]
    collection = db["nve_magasinstatistikk"]

    # Erstatt bare dokumentene i denne samlingen
    # med innholdet fra CSV-filen.
    collection.delete_many({})

    documents = df.to_dict("records")
    if documents:
        collection.insert_many(documents, ordered=False)

    print("Rader i CSV:", len(df))
    print("Dokumenter i MongoDB:", collection.count_documents({}))

finally:
    client.close()
