import os
import sys
import numpy as np
import pandas as pd


"""
Defining common constant variable for training pipeline
"""
## close_price
TARGET_PRICE_COLUMN="close_price"
FILE_NAME:str="PhisingData.csv"

## returns
TARGET_RETURNS_COLUMN="returns"
FILE_NAME:str="PhisingData.csv"

PIPELINE_NAME:str="NGXStockPrediction"
ARTIFACT_DIR:str="Artifacts"
TRAIN_FILE_NAME:str="train.csv"
TEST_FILE_NAME:str="test.csv"


"""
Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""

DATA_INGESTION_COLLECTION_NAME:str="stock_data"
DATA_INGESTION_DATABASE_NAME:str="NGX_Stock_ME_Database"
DATA_INGESTION_DIR_NAME:str="data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR:str="feature_store"
DATA_INGESTION_INGESTED_DIR:str="ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO:float = 0.1