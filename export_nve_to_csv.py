from cassandra.cluster import Cluster
import csv

cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect("ind320")

query = """
SELECT omr_type, omr_nr, dato, iso_aar, iso_uke,
       fyllingsgrad, kapasitet_twh, fylling_twh,
       neste_publiseringsdato, fyllingsgrad_forrige_uke,
       endring_fyllingsgrad
FROM nve_magasinstatistikk
"""

try:
    rows = session.execute(query)

    with open("nve_cassandra_export.csv", "w",
              newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "omr_type", "omr_nr", "dato", "iso_aar", "iso_uke",
            "fyllingsgrad", "kapasitet_twh", "fylling_twh",
            "neste_publiseringsdato", "fyllingsgrad_forrige_uke",
            "endring_fyllingsgrad"
        ])

        count = 0
        for row in rows:
            writer.writerow(row)
            count += 1

    print(f"Ferdig! Eksporterte {count} rader.")

finally:
    cluster.shutdown()