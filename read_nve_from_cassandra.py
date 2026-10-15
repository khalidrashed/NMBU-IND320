
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("IND320-Read-NVE-from-Cassandra")
    .config(
        "spark.jars.packages",
        "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"
    )
    .config("spark.cassandra.connection.host", "localhost")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    # Les NVE-data fra Cassandra
    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(
            keyspace="ind320",
            table="nve_magasinstatistikk"
        )
        .load()
    )

    print("Antall rader i Cassandra:", df.count())

    print("\nKolonner:")
    df.printSchema()

    print("\nDe første fem radene:")
    df.orderBy("dato").show(5, truncate=False)

    # Enkel statistikk for fyllingsgrad
    print("\nStatistikk for fyllingsgrad:")
    df.select("fyllingsgrad").describe().show()

    # Antall rader per område
    print("\nAntall rader per område:")
    (
        df.groupBy("omr_type", "omr_nr")
        .count()
        .orderBy("omr_type", "omr_nr")
        .show()
    )

    # Lagre dataene fra Cassandra til CSV
    (
        df.orderBy("dato")
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv("nve_cassandra_export")
    )

    print("Dataene er eksportert til mappen nve_cassandra_export.")

finally:
    spark.stop()
