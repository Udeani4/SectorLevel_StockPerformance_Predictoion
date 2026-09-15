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

SCHEMA_FILE_PATH=os.path.join("data_schema","schema.yaml") ## The schema file will be created manually or if you like you can automate it

SAVED_MODEL_DIR=os.path.join("saved_models") ## It will join to whatever directory you attach it to, creating a folder
MODEL_FILE_NAME:str="model.pkl"

"""
Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""

DATA_INGESTION_COLLECTION_NAME:str="stock_data"
DATA_INGESTION_DATABASE_NAME:str="NGX_Stock_ME_Database"
DATA_INGESTION_DIR_NAME:str="data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR:str="feature_store"
DATA_INGESTION_INGESTED_DIR:str="ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATIO:float = 0.1

"""
Data Validation related constant start with DATA_VALIDATION VAR NAME
"""
DATA_VALIDATION_DIR_NAME:str="data_valdation"
DATA_VALIDATION_VALID_DIR:str="validated"
DATA_VALIDATION_INVALID_DIR:str="invalid"
DATA_VALIDATION_DRIFT_REPORT_DIR:str="drift_report"
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME:str="report.yaml"

"""
Data transformation related constant stast with DATA_TRANSFORMATION VAR NAME
"""
DATA_TRANSFORMATION_DIR_NAME:str="data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR:str="transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR:str="transformed_object"
PREPROCESSING_OBJECT_FILE_NAME:str="preprocessing.pkl"
## for knn imputer to replace nan values. This will replace the nan values with the average of the 3 nearest neighbors
DATA_TRANSFORMATION_IMPUTER_PARAMS: dict={
    "missing_values":np.nan,
    "n_neighbors":3,
    "weights":"uniform"
}
