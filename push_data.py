import os,sys,json
from dotenv import load_dotenv
import os
import requests
import pandas as pd


load_dotenv()

mongo_db_username = os.getenv("MONGO_DB_CLUSTER_USERNAME")
mongo_db_password = os.getenv("MONGO_DB_CLUSTER_PASSWORD")
mongo_db_uri=os.getenv("MONGO_DB_CLUSTER_URL")
ngx_api_key = os.getenv("NGX_API_KEY")



import certifi ## This is a pyhton package that provides a set of root certificate. It is commonly used by python libraries that needs to make a secure HTTP connection

## right now we are trying to make a HTTP conection.  This is just to ensure  this is from trusted certified authorities

## So, whenever we are trying to connect with the MongoDB, if certifi() has been imported, it knows it is a valid request that is probably being made

ca=certifi.where() ## this will retrieve the path to the bundle of cs certificates provided b ceritify and store it in a variable 'ca' (certificate authorities). This is usually done to verify that the server you are connecting to has a trusted certificate ensured (Krish)


import pandas as pd
import numpy as np
import pymongo
from pymongo import UpdateOne
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

class NGXStockDataExtract:
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NGXStockPredictionException(e, sys)
        
    def get_all_stock_data_info(self,ngx_api_key):
        os.makedirs("stock_data", exist_ok=True)

        all_stocks_url = "https://www.ngxpulse.ng/api/ngxdata/stocks"

        headers = {
            "X-API-Key": ngx_api_key
        }

        all_stocks = requests.get(all_stocks_url, headers=headers).json()

        df = pd.DataFrame(all_stocks['stocks'])
        df.to_csv("stock_data/All_Stocks_Info",index=False)

    def get_stock_data_from_ngx_pulse(self, ticker, ngx_api_key):

        os.makedirs("stock_data", exist_ok=True)

        url = f"https://www.ngxpulse.ng/api/ngxdata/prices/{ticker}" 

        headers = {
            "X-API-Key": ngx_api_key
        }

        params = {
            "from": "2017-01-01",
            "to": "2026-07-18"
        }
        
        try:            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            print(f"{ticker}: {response.status_code}")

            if response.status_code != 200:
                print(response.text)
                return

            data = response.json()

            if "prices" not in data:
                print(f"{ticker}: No prices returned")
                return

            df = pd.DataFrame(data["prices"])
            df.to_csv(f"stock_data/{ticker}.csv", index=False)

            print(f"{ticker}: Saved {len(df)} rows")

        except Exception as e:
            print(f"{ticker}: {e}")

    def load_stock_data_to_local_storage(self, ngx_api_key):
        df=pd.read_csv('stock_data/All_Stocks_Info')

        list_of_tickers=df['symbol'].tolist()

        for ticker in list_of_tickers[:10]:
            self.get_stock_data_from_ngx_pulse(ticker,ngx_api_key)

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
            raise NGXStockPredictionException(e, sys)

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
            self.mongo_client = pymongo.MongoClient(mongo_db_uri)

            # Access the specified database.
            self.database = self.mongo_client[self.database]

            # Access the specified collection within the database.
            self.collection = self.database[self.collection]

            # Insert all records into the collection.
            self.collection.insert_many(self.records)

            # Return the number of records successfully processed.
            return len(self.records)

        except Exception as e:
            raise NGXStockPredictionException(e, sys)


if __name__ == '__main__':
    DATABASE = "NGX_Stock_ME_Database"
    Collection = "stock_data"

    ngxstockobj = NGXStockDataExtract()
    stock_files = os.listdir('stock_data')

    for data in stock_files:

        if data.endswith(".csv"):

            FILE_PATH = f"stock_data/{data}"

            records = ngxstockobj.csv_to_json_converter(
                file_path=FILE_PATH
            )

            no_of_records = ngxstockobj.insert_data_to_mongodb(
                records,
                DATABASE,
                Collection
            )

            print(f"{data} inserted to mongodb: {no_of_records} records")