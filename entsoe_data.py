
from pathlib import Path
import os
import time

import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# Load token from .env in the project root
PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

token = os.getenv("ENTSOE_API_TOKEN")
if not token:
    raise ValueError(
        "ENTSOE_API_TOKEN is missing from the project's .env file."
    )

client = EntsoePandasClient(api_key=token)

# Two-year period ending today (Norwegian local time)
end = pd.Timestamp.now(tz="Europe/Oslo").normalize()
start = end - pd.DateOffset(years=2)

# Candidate connections to test.
# These are bidding-zone pairs, not a guarantee of every physical cable.
connections = [
    ("NO_1", "SE_3"),
    ("NO_1", "SE_2"),
    ("NO_2", "DK_1"),
    ("NO_2", "NL"),
    ("NO_2", "DE_LU"),
    ("NO_2", "GB"),
    ("NO_3", "SE_2"),
    ("NO_4", "SE_1"),
    ("NO_4", "FI"),
]

rows = []
errors = []

def fetch_connection(source, destination, start, end):
    """Fetch one direction in monthly chunks to avoid oversized requests."""
    chunks = []
    cursor = start

    while cursor < end:
        next_month = cursor + pd.DateOffset(months=1)
        chunk_end = min(next_month, end)

        data = client.query_crossborder_flows(
            country_code_from=source,
            country_code_to=destination,
            start=cursor,
            end=chunk_end,
        )

        if not data.empty:
            chunk = data.rename("flow_mw").to_frame()
            chunk.index.name = "timestamp"
            chunk = chunk.reset_index()
            chunk["from_area"] = source
            chunk["to_area"] = destination
            chunk["connection"] = f"{source}-{destination}"
            chunk["direction"] = (
                "from_Norway"
                if source.startswith("NO")
                else "to_Norway"
            )
            chunks.append(chunk)

        cursor = chunk_end
        time.sleep(0.2)

    if chunks:
        return pd.concat(chunks, ignore_index=True)

    return pd.DataFrame(
        columns=[
            "timestamp", "flow_mw", "from_area", "to_area",
            "connection", "direction"
        ]
    )

print(f"Period: {start} to {end}")
print("Fetching ENTSO-E cross-border flows...")

for area_a, area_b in connections:
    for source, destination in [
        (area_a, area_b),
        (area_b, area_a),
    ]:
        print(f"Fetching {source} -> {destination} ...")
        try:
            result = fetch_connection(
                source, destination, start, end
            )

            if not result.empty:
                rows.append(result)
                print(
                    f"  Received {len(result)} rows; "
                    f"non-zero values: "
                    f"{int((result['flow_mw'] != 0).sum())}"
                )
            else:
                print("  No rows returned.")

        except Exception as exc:
            message = (
                f"{source} -> {destination}: "
                f"{type(exc).__name__}: {exc}"
            )
            errors.append(message)
            print(f"  ERROR: {message}")

        time.sleep(0.5)

if rows:
    df = pd.concat(rows, ignore_index=True)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    df["flow_mw"] = pd.to_numeric(
        df["flow_mw"], errors="coerce"
    )

    df = df.dropna(subset=["timestamp", "flow_mw"])
    df = df.drop_duplicates(
        subset=["timestamp", "from_area", "to_area"]
    )
    df = df.sort_values(
        ["timestamp", "from_area", "to_area"]
    ).reset_index(drop=True)

    output_file = PROJECT_DIR / "entsoe_crossborder_flows.csv"
    df.to_csv(output_file, index=False)

    print("\nDownload finished.")
    print(f"Rows: {len(df):,}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Connections: {df['connection'].nunique()}")
    print(f"Saved to: {output_file}")
    print("\nRows per direction:")
    print(df.groupby("direction").size().to_string())
else:
    print("\nNo data was downloaded. Check the errors above.")

if errors:
    error_file = PROJECT_DIR / "entsoe_errors.txt"
    error_file.write_text("\n".join(errors), encoding="utf-8")
    print(f"\nSome requests failed. Details saved to: {error_file}")
