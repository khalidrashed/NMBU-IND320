
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("IND320-Extract-ENTSOE")
    .config("spark.cassandra.connection.host", "my_cassandra")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

try:
    # Hent data fra Cassandra ved hjelp av Spark
    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(
            keyspace="ind320",
            table="entsoe_crossborder_flows"
        )
        .load()
    )

    # Velg kolonnene vi trenger
    selected_df = df.select(
        "timestamp",
        "connection",
        "from_area",
        "to_area",
        "direction",
        "flow_mw"
    )

    print("Antall rader hentet fra Cassandra:", selected_df.count())

    selected_df.show(10, truncate=False)

finally:
    spark.stop()
