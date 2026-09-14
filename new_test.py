import pymongo
import certifi
from dotenv import load_dotenv
import os



load_dotenv()

if __name__=="__main__":
    uri = os.getenv("MONGO_DB_CLUSTER_URL")
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)

    try:
        print(client.admin.command('ping'))
        print("Connected successfully!")
    except Exception as e:
        print("Connection failed:", e)