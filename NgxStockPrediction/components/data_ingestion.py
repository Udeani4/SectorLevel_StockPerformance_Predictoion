from NgxStockPrediction.exception.exception import NGXStockPredictionException

from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.config_entity import DataIngestionConfig ## call configurations of the Data Ingestion Config
from NgxStockPrediction.entity.artifact_entity import DataIngestionArtifact

import os
import sys
import numpy as np
import pandas as pd
import pymongo 
from typing import List
from sklearn.model_selection import train_test_split

from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_DB_CLUSTER_URL")

## We will read from the mongodb url

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config=data_ingestion_config ## This variable will now have access to all the variables defined in the DataIngestionConfig class
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def export_collection_as_dataframe(self):
        """
        Read data from MongoDB
        """
        try:
            self.symbol=self.data_ingestion_config.file_name
            database_name=self.data_ingestion_config.database_name
            collection_name=self.data_ingestion_config.collection_name
            self.mongo_client=pymongo.MongoClient(uri)
            collection=self.mongo_client[database_name][collection_name] ## This will give us the collection from the database in our mongodb object. 
            df=pd.DataFrame(list(collection.find({"symbol": self.symbol}))) ## this will give the particular symbol we want to work with.
            if '_id' in df.columns.to_list():
                df=df.drop(columns=['_id'])

            df.replace({'na':np.nan},inplace=True)
            return df
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def export_data_into_feature_store(self,dataframe:pd.DataFrame): ## cool down and grab it
        try:
            feature_store_file_path=self.data_ingestion_config.feature_store_file_path
            # creating folder
            dir_path=os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path,exist_ok=True)
            dataframe.to_csv(feature_store_file_path,index=False,header=True)
            return dataframe

        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def clean_and_create_monthly_data(self, dataframe:pd.DataFrame):
        try:
            df=dataframe
            df=df.drop(columns=['high_price','low_price'])
            df.rename(columns={'trade_date':'date'},inplace=True)
            df['date']=pd.to_datetime(df['date'])
            df['month']=df['date'].dt.month
            df['quarter']=df['date'].dt.quarter
            df['year']=df['date'].dt.year

            end_month_df = (
                df
                .sort_values("date")
                .groupby(df["date"].dt.to_period("M"))
                .tail(1)
                .reset_index(drop=True)
            )

            end_month_df['returns']=end_month_df['close_price'].pct_change()*100

            return end_month_df

        except Exception as e:
            raise NGXStockPredictionException(e,sys)

        
    def split_data_as_train_test(self, dataframe:pd.DataFrame):
        try:
            train_set,test_set=train_test_split(
                dataframe,test_size=self.data_ingestion_config.train_test_split_ratio,shuffle=False
            )
            logging.info("Performed train test split on the dataframe")
            logging.info("Exited split_data_as_train_test method of Data_Ingestion class")

            dir_path=os.path.dirname(self.data_ingestion_config.training_file_path)## to get the directory name

            os.makedirs(dir_path,exist_ok=True)

            logging.info(f"Exporting train and test file path")

            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )
            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )
            logging.info(f"Exported train and test file path")
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

        
    def initiate_data_ingestion(self):
        try:
            dataframe=self.export_collection_as_dataframe()
            dataframe=self.export_data_into_feature_store(dataframe)
            clean_monthly_dataframe=self.clean_and_create_monthly_data(dataframe=dataframe)

            self.split_data_as_train_test(clean_monthly_dataframe)

            data_ingestion_artifact=DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,test_file_path=self.data_ingestion_config.testing_file_path)

            return data_ingestion_artifact ## figure out what we used this for

        except Exception as e:
            raise NGXStockPredictionException(e,sys)
