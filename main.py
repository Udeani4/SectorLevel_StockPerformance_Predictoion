# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# ngx_api_key=os.getenv("NGX_API_KEY")

# ngx_market_url = "https://www.ngxpulse.ng/api/ngxdata/market"
# ngx_stocks_url = "https://www.ngxpulse.ng/api/ngxdata/stocks"

# headers = {
#     "X-API-Key": f"{ngx_api_key}",
#     "Content-Type": "application/json"
# }

# response = requests.get(ngx_stocks_url, headers=headers)

# print(response.status_code)

# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print(response.text)


## let us test what we have done
from NgxStockPrediction.components.data_ingestion import DataIngestion
from NgxStockPrediction.components.data_validation import DataValidation
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.entity.config_entity import TrainingPipelineConfig,DataIngestionConfig, DataValidationConfig
# from NgxStockPrediction.entity.artifact_entity import DataIngestionArtifact
import sys, os


if __name__ == "__main__":
    try:
        filename="ZENITHBANK"

        trainingpipelineconfig=TrainingPipelineConfig()

        dataingestionconfig=DataIngestionConfig(training_pipeline_config=trainingpipelineconfig, FILE_NAME=filename)
        dataingestion=DataIngestion(data_ingestion_config=dataingestionconfig)
        logging.info("Initiate data ingestion")
        dataingestionartifact=dataingestion.initiate_data_ingestion()
        print(dataingestionartifact)

        datavalidationconfig=DataValidationConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename)
        datavalidation=DataValidation(data_ingestion_artifact=dataingestionartifact,data_validation_config=datavalidationconfig)
        logging.info("Initiate data validation")
        datavalidationartifact=datavalidation.initiate_data_validation()
        print(datavalidationartifact)
        
    except Exception as e:
        raise NGXStockPredictionException(e,sys)




