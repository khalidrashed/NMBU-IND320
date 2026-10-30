
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

spark = (
    SparkSession.builder
    .appName("IND320-ENTSOE-to-Cassandra")
    .config("spark.cassandra.connection.host", "my_cassandra")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

try:
    # Les CSV-filen med Spark
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv("/workspace/entsoe_crossborder_flows.csv")
    )

    # Velg kolonnene som finnes i Cassandra-tabellen
    df = df.select(
        col("connection").cast("string"),
        to_timestamp(col("timestamp")).alias("timestamp"),
        col("from_area").cast("string"),
        col("to_area").cast("string"),
        col("direction").cast("string"),
        col("flow_mw").cast("double")
    )

    # Fjern rader med manglende verdier i nøkkelkolonnene
    df = df.dropna(
        subset=["connection", "timestamp", "from_area", "to_area"]
    )

    print("Antall rader som skal skrives:", df.count())

    # Skriv dataene til Cassandra
    (
        df.write
        .format("org.apache.spark.sql.cassandra")
        .mode("append")
        .options(
            keyspace="ind320",
            table="entsoe_crossborder_flows"
        )
        .save()
    )

    print("ENTSO-E-dataene er skrevet til Cassandra!")

finally:
    spark.stop()
