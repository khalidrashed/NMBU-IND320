
from pathlib import Path

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("IND320-Extract-ENTSOE-for-MongoDB")
    .config("spark.cassandra.connection.host", "my_cassandra")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

output_path = "/workspace/entsoe_mongodb_export"

try:
    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(
            keyspace="ind320",
            table="entsoe_crossborder_flows"
        )
        .load()
        .select(
            "timestamp",
            "connection",
            "from_area",
            "to_area",
            "direction",
            "flow_mw"
        )
    )

    print("Antall rader fra Cassandra:", df.count())

    (
        df.write
        .mode("overwrite")
        .parquet(output_path)
    )

    print("Eksporten til Parquet er ferdig:", output_path)

finally:
    spark.stop()
