from pymongo import MongoClient
import os

uri = os.getenv("MONGODB_URI")
print("URI exists:", bool(uri))

client = MongoClient(uri)
db = client["aqi_system"]

print("Collections:", db.list_collection_names())
print("MongoDB connection successful ✅")
