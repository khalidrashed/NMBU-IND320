from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("IND320-Cassandra-test")
    .config(
        "spark.jars.packages",
        "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"
    )
    .config("spark.cassandra.connection.host", "localhost")
    .config("spark.cassandra.connection.port", "9042")
    .getOrCreate()
)

try:
    print("Spark version:", spark.version)
    print("Testing Cassandra connection...")

    keyspaces = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="system_schema.keyspaces", keyspace="system_schema") \
        .load()

    keyspaces.select("keyspace_name").show(truncate=False)
finally:
    spark.stop()
