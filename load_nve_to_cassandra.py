
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date

# Start Spark og koble til Cassandra
spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("IND320-NVE-to-Cassandra")
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
    # Les alle NVE-dataene fra CSV-filen
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv("nve_magasinstatistikk_test.csv")
    )

    # Velg kolonnene og tilpass navn og datatyper
    df = df.select(
        to_date(col("dato_Id")).alias("dato"),
        col("omrType").alias("omr_type"),
        col("omrnr").cast("int").alias("omr_nr"),
        col("iso_aar").cast("int").alias("iso_aar"),
        col("iso_uke").cast("int").alias("iso_uke"),
        col("fyllingsgrad").cast("double").alias("fyllingsgrad"),
        col("kapasitet_TWh").cast("double").alias("kapasitet_twh"),
        col("fylling_TWh").cast("double").alias("fylling_twh"),
        col("neste_Publiseringsdato")
            .cast("string")
            .alias("neste_publiseringsdato"),
        col("fyllingsgrad_forrige_uke")
            .cast("double")
            .alias("fyllingsgrad_forrige_uke"),
        col("endring_fyllingsgrad")
            .cast("double")
            .alias("endring_fyllingsgrad")
    )

    # Kontroller dataene før innlasting
    antall_rader = df.count()

    print(f"Antall rader i CSV: {antall_rader}")
    df.show(5, truncate=False)

    # Skriv ALLE radene til Cassandra
    (
        df.write
        .format("org.apache.spark.sql.cassandra")
        .options(
            keyspace="ind320",
            table="nve_magasinstatistikk"
        )
        .mode("append")
        .save()
    )

    print(
        f"Ferdig! {antall_rader} rader er sendt "
        "til Cassandra."
    )

finally:
    spark.stop()
