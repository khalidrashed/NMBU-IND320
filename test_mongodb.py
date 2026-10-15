import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGODB_URI")

if not uri:
    raise RuntimeError("Fant ikke MONGODB_URI i .env-filen.")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    print("MongoDB-tilkobling OK!")

    collection = client["ind320_test"]["connection_test"]
    result = collection.insert_one({
        "message": "IND320 test",
        "status": "ok"
    })
    print("Dokument lagret:", result.inserted_id)

    document = collection.find_one({"_id": result.inserted_id})
    print("Dokument lest:", document)

    collection.delete_one({"_id": result.inserted_id})
    print("Testdokument slettet.")
finally:
    client.close()
