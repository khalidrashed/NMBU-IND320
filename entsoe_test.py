
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

load_dotenv(Path(__file__).resolve().parent / ".env")

token = os.getenv("ENTSOE_API_TOKEN")
if not token:
    raise ValueError("ENTSOE_API_TOKEN mangler i .env")

client = EntsoePandasClient(api_key=token)

# Testperiode: én dag
start = pd.Timestamp("2025-01-15", tz="Europe/Oslo")
end = pd.Timestamp("2025-01-16", tz="Europe/Oslo")

connections = [
    ("NO_1", "SE_3"),
    ("NO_2", "DK_1"),
    ("NO_2", "NL"),
    ("NO_2", "DE_LU"),
    ("NO_2", "GB"),
    ("NO_4", "SE_1"),
]

results = []

for source, destination in connections:
    for origin, target in [
        (source, destination),
        (destination, source),
    ]:
        try:
            data = client.query_crossborder_flows(
                country_code_from=origin,
                country_code_to=target,
                start=start,
                end=end,
            )

            results.append({
                "from_area": origin,
                "to_area": target,
                "hours": len(data),
                "nonzero_hours": int((data != 0).sum()),
                "min_value": data.min(),
                "max_value": data.max(),
            })

        except Exception as exc:
            print(f"{origin} -> {target}: {type(exc).__name__}: {exc}")

df = pd.DataFrame(results)
print(df.to_string(index=False))
df.to_csv("entsoe_connection_test.csv", index=False)
print("\nSaved: entsoe_connection_test.csv")
