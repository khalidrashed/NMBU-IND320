
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPORT_PATH = PROJECT_ROOT / "entsoe_mongodb_export"

load_dotenv(PROJECT_ROOT / ".env")

uri = os.getenv("MONGODB_URI")
if not uri:
    raise RuntimeError("MONGODB_URI mangler i .env-filen.")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    collection = client["ind320"]["entsoe_crossborder_flows"]

    # Create a unique key so rerunning the import does not create duplicates.
    collection.create_index(
        [
            ("connection", 1),
            ("timestamp", 1),
            ("from_area", 1),
            ("to_area", 1),
        ],
        unique=True,
    )

    total = 0
    batch_size = 2000

    for file in EXPORT_PATH.glob("*.parquet"):
        print(f"Leser fil: {file.name}")

        for chunk in pd.read_parquet(file).to_dict(orient="records"):
            # This loop is replaced below by batched writes.
            pass

        df = pd.read_parquet(file)

        for start in range(0, len(df), batch_size):
            records = df.iloc[start : start + batch_size].to_dict(
                orient="records"
            )

            operations = []
            for record in records:
                operations.append(
                    UpdateOne(
                        {
                            "connection": record["connection"],
                            "timestamp": record["timestamp"],
                            "from_area": record["from_area"],
                            "to_area": record["to_area"],
                        },
                        {"$set": record},
                        upsert=True,
                    )
                )

            if operations:
                collection.bulk_write(operations, ordered=False)
                total += len(operations)
                print(f"Behandlet {total:,} rader")

    print("Import ferdig.")
    print("Dokumenter i MongoDB:", collection.count_documents({}))

finally:
    client.close()
