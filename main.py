# ## let us test what we have done
# from NgxStockPrediction.components.data_ingestion import DataIngestion
# from NgxStockPrediction.components.data_validation import DataValidation
# from NgxStockPrediction.components.data_transformation import DataTransformation
# from NgxStockPrediction.components.model_trainer import ModelTrainer
# from NgxStockPrediction.components.model_performance_tracker import ModelPerformanceTracker

# from NgxStockPrediction.exception.exception import NGXStockPredictionException
# from NgxStockPrediction.logging.logger import logging
# from NgxStockPrediction.entity.config_entity import TrainingPipelineConfig,DataIngestionConfig,DataValidationConfig,DataTransformationConfig,ModelTrainerConfig,ModelPerformanceTrackerConfig
# # from NgxStockPrediction.entity.artifact_entity import DataIngestionArtifact
# import sys, os


# if __name__ == "__main__":
#     try:
#         filename="CHAMS"
#         targetname="close_price"
#         targetname2="returns"

#         trainingpipelineconfig=TrainingPipelineConfig()

#         dataingestionconfig=DataIngestionConfig(training_pipeline_config=trainingpipelineconfig, FILE_NAME=filename)
#         dataingestion=DataIngestion(data_ingestion_config=dataingestionconfig)
#         logging.info("Initiate data ingestion")
#         dataingestionartifact=dataingestion.initiate_data_ingestion()
#         print(dataingestionartifact)

#         datavalidationconfig=DataValidationConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename)
#         datavalidation=DataValidation(data_ingestion_artifact=dataingestionartifact,data_validation_config=datavalidationconfig)
#         logging.info("Initiate data validation")
#         datavalidationartifact=datavalidation.initiate_data_validation()
#         print(datavalidationartifact)

#         datatransformationconfig=DataTransformationConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename)
#         datatransformation=DataTransformation(data_validation_artifact=datavalidationartifact,data_transformation_config=datatransformationconfig)
#         logging.info("Initiate data transformation")
#         datatransformationartifact=datatransformation.initiate_data_transformation(TARGET_COLUMN=targetname)
#         print(datatransformationartifact)

#         modeltrainerconfig=ModelTrainerConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename,TARGET_NAME=targetname)
#         modeltrainer=ModelTrainer(model_trainer_config=modeltrainerconfig,data_validation_artifact=datavalidationartifact,data_transformation_artifact=datatransformationartifact)
#         logging.info("Initiate Model Trainer")

#         modeltrainerartifact=modeltrainer.initiate_model_trainer(
#             model_type="sarima",
#             order=(2,2,0),
#             seasonal_order=(1,2,1,12),
#             forecast_step=1 ## We cant forecast further FOR SARIMAX like we do in sarima. Because we will need to provide the explanatory variables (exog) for that forcast.
#         )
#         print(modeltrainerartifact)

#         ## activate performance tracker
#         modelperformancetrackerconfig=ModelPerformanceTrackerConfig(training_pipeline_config=trainingpipelineconfig,FILE_NAME=filename,TARGET_NAME=targetname)
#         modelperformancetracker=ModelPerformanceTracker(model_performance_tracker_config=modelperformancetrackerconfig,model_trainer_artifact=modeltrainerartifact,data_validation_artifact=datavalidationartifact)
#         logging.info("initiate model performance tracker")
#         performance_metric_artifact=modelperformancetracker.initiate_performance_tracker()
#         print(performance_metric_artifact)

#     except Exception as e:
#         raise NGXStockPredictionException(e,sys)




