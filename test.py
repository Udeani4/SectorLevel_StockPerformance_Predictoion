import os,sys,json
from dotenv import load_dotenv


load_dotenv()

mongo_db_username = os.getenv("MONGO_DB_USERNAME")
mongo_db_password = os.getenv("MONGO_DB_PASSWORD")

uri = f"mongodb+srv://{mongo_db_username}:{mongo_db_password}@cluster0.gf0burp.mongodb.net/?appName=Cluster0"

import certifi ## This is a pyhton package that provides a set of root certificate. It is commonly used by python libraries that needs to make a secure HTTP connection

## right now we are trying to make a HTTP conection.  This is just to ensure  this is from trusted certified authorities

## So, whenever we are trying to connect with the MongoDB, if certifi() has been imported, it knows it is a valid request that is probably being made

ca=certifi.where() ## this will retrieve the path to the bundle of cs certificates provided b ceritify and store it in a variable 'ca' (certificate authorities). This is usually done to verify that the server you are connecting to has a trusted certificate ensured (Krish)


import pandas as pd
import numpy as np
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

class NetworkDataExtract:
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def csv_to_json_converter(self, file_path):
        """
        Reads a CSV file and converts it into a list of JSON-like records.
        """
        try:
            data = pd.read_csv(file_path)

            # Remove the default index and create a clean sequential index.
            data.reset_index(drop=True, inplace=True)

            # Convert the DataFrame into a list of dictionaries.
            # Each dictionary represents one row in the CSV file.
            records = list(json.loads(data.T.to_json()).values())

            return records

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def insert_data_to_mongodb(self, records, database, collection):
        """
        Inserts records into a MongoDB collection.

        Args:
            records (list): List of documents to insert.
            database (str): Target database name.
            collection (str): Target collection name.
        """
        try:
            self.database = database
            self.collection = collection
            self.records = records

            # Create a connection to the MongoDB server.
            self.mongo_client = pymongo.MongoClient(uri)

            # Access the specified database.
            self.database = self.mongo_client[self.database]

            # Access the specified collection within the database.
            self.collection = self.database[self.collection]

            # Insert all records into the collection.
            self.collection.insert_many(self.records)

            # Return the number of records successfully processed.
            return len(self.records)

        except Exception as e:
            raise NetworkSecurityException(e, sys)


if __name__=='__main__':
    FILE_PATH="./prediction_output/output.csv"
    DATABASE="Donatus_ML_Database"
    Collection="NetworkData"
    networkobj=NetworkDataExtract()
    records=networkobj.csv_to_json_converter(file_path=FILE_PATH)
    no_of_records=networkobj.insert_data_to_mongodb(records,DATABASE,Collection)
    print(no_of_records)
