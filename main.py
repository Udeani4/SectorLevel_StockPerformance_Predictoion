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
from NgxStockPrediction.components.data_transformation import DataTransformation
from NgxStockPrediction.components.model_trainer import ModelTrainer
from NgxStockPrediction.components.model_performance_tracker import ModelPerformanceTracker

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.entity.config_entity import TrainingPipelineConfig,DataIngestionConfig,DataValidationConfig,DataTransformationConfig,ModelTrainerConfig,ModelPerformanceTrackerConfig
# from NgxStockPrediction.entity.artifact_entity import DataIngestionArtifact
import sys, os


if __name__ == "__main__":
    try:
        filename="ZENITHBANK"
        targetname="close_price"

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

        datatransformationconfig=DataTransformationConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename)
        datatransformation=DataTransformation(data_validation_artifact=datavalidationartifact,data_transformation_config=datatransformationconfig)
        logging.info("Initiate data transformation")
        datatransformationartifact=datatransformation.initiate_data_transformation(TARGET_COLUMN=targetname)
        print(datatransformationartifact)

        modeltrainerconfig=ModelTrainerConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename,TARGET_NAME=targetname)
        modeltrainer=ModelTrainer(model_trainer_config=modeltrainerconfig,data_validation_artifact=datavalidationartifact,data_transformation_artifact=datatransformationartifact)
        logging.info("Initiate Model Trainer")
        # modeltrainerartifact=modeltrainer.initiate_model_trainer(
        #     model_type="sarima",
        #     order=(0,2,0), 
        #     seasonal_order=(2,1,0,12),
        #     forecast_step=2 ## This will predict the next two future values
        # )
        modeltrainerartifact=modeltrainer.initiate_model_trainer(
            model_type="sarimax",
            order=(0,2,0), 
            seasonal_order=(2,1,0,12),
            forecast_step=0 ## We cant forecast further like we did in sarima. Because we will need to provide the explanatory variables (exog) for that forcast.
        )
        print(modeltrainerartifact)

        ## activate performance tracker
        modelperformancetrackerconfig=ModelPerformanceTrackerConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename,TARGET_NAME=targetname)
        modelperformancetracker=ModelPerformanceTracker(model_performance_tracker_config=modelperformancetrackerconfig,model_trainer_artifact=modeltrainerartifact,data_validation_artifact=datavalidationartifact)
        logging.info("initiate model performance tracker")
        performance_update=modelperformancetracker.initiate_performance_tracker()
        print('performance_update: ',performance_update)

    except Exception as e:
        raise NGXStockPredictionException(e,sys)




