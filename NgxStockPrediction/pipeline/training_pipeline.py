## This will resemble our main.py steps but we will use classes
import os,sys
import pandas as pd

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.components.data_ingestion import DataIngestion
from NgxStockPrediction.components.data_validation import DataValidation
from NgxStockPrediction.components.data_transformation import DataTransformation
from NgxStockPrediction.components.model_trainer import ModelTrainer
from NgxStockPrediction.components.model_performance_tracker import ModelPerformanceTracker

from NgxStockPrediction.constant.training_pipeline import TRAINING_BUCKET_NAME
# from NgxStockPrediction.cloud.s3_syncer import S3Sync

from NgxStockPrediction.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelPerformanceTrackerConfig
)

from NgxStockPrediction.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
    PerformanceMetricArtifact,
    PerformanceMetricTrackerArtifact
)

class TrainingPipeline:
    def __init__(self, file_name:str, target_name:str, model_type:str,order=(1,1,1), 
                seasonal_order=(1,1,1,12),
                forecast_step=1):
        self.training_pipeline_config=TrainingPipelineConfig()
        self.file_name=file_name
        self.target_name=target_name
        self.model_type=model_type
        self.order=order
        self.seasonal_order=seasonal_order
        self.forecast_step=forecast_step
        # self.s3_sync=S3Sync()

    @staticmethod
    def read_data(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def start_data_ingestion(self):
        try:
            self.data_ingestion_config=DataIngestionConfig(training_pipeline_config=self.training_pipeline_config, FILE_NAME=self.file_name)

            logging.info("start data ingestion")
            data_ingestion=DataIngestion(data_ingestion_config=self.data_ingestion_config)
            data_ingestion_artifact=data_ingestion.initiate_data_ingestion()
            logging.info(f'Data Ingestion complete and artifact: {data_ingestion_artifact}')

            return data_ingestion_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def start_data_validation(
            self, data_ingestion_artifact:DataIngestionArtifact
        ):
        try:
            data_validation_config=DataValidationConfig(training_pipeline_config=self.training_pipeline_config, FILE_NAME=self.file_name)
            data_validation=DataValidation(data_ingestion_artifact=data_ingestion_artifact,data_validation_config=data_validation_config)

            logging.info("Initiate the data Validation")
            data_validation_artifact=data_validation.initiate_data_validation()
            logging.info("Data Validation complete")

            return data_validation_artifact

        except Exception as e:
            raise NGXStockPredictionException(e,sys)  

    def start_data_transformation(
            self,data_validation_artifact:DataValidationArtifact
        ):
        try:
            data_transformation_config=DataTransformationConfig(training_pipeline_config=self.training_pipeline_config, FILE_NAME=self.file_name)
            data_transformation=DataTransformation(data_transformation_config=data_transformation_config,data_validation_artifact=data_validation_artifact)

            logging.info("Initiate data transformation")
            data_transformation_artifact=data_transformation.initiate_data_transformation(TARGET_COLUMN=self.target_name) 
            logging.info("Data transformation complete")

            return data_transformation_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
    
    def start_model_trainer(
            self,data_transformation_artifact:DataTransformationArtifact,data_validation_artifact:DataValidationArtifact, grid_search=False
        ):
        try:
            self.model_trainer_config: ModelTrainerConfig = ModelTrainerConfig(training_pipeline_config=self.training_pipeline_config, FILE_NAME=self.file_name,TARGET_NAME=self.target_name)

            model_trainer=ModelTrainer(model_trainer_config=self.model_trainer_config,data_validation_artifact=data_validation_artifact,data_transformation_artifact=data_transformation_artifact)

            if grid_search==True:
                ## run a grid search
                train_data=self.read_data(file_path=data_validation_artifact.valid_train_file_path)
                test_data=self.read_data(file_path=data_validation_artifact.valid_test_file_path)

                grid_search_params=model_trainer.sarima_grid_search_model_trainer(
                    train_data=train_data, test_data=test_data,
                    grid={'p':3,'i':3,'q':3,'P':3,'D':3,'Q':3}
                )

                if grid_search_params['r2_score'] <= 0:
                    return None
                
                ## train on best param
                logging.info("train on best param")
                logging.info("initiate model trainer")
                model_trainer_artifact=model_trainer.initiate_model_trainer(
                    model_type=self.model_type,
                    order=grid_search_params['order'], 
                    seasonal_order=grid_search_params['seasonal_order'],
                    forecast_step=self.forecast_step
                )

                return model_trainer_artifact

            logging.info("initiate Model trainer")
            model_trainer_artifact=model_trainer.initiate_model_trainer(
                model_type=self.model_type,
                order=self.order, 
                seasonal_order=self.seasonal_order,
                forecast_step=self.forecast_step
            )
            logging.info("Model Training complete")

            return model_trainer_artifact
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def start_performance_tracker(self, model_trainer_artifact:ModelTrainerArtifact,data_validation_artifact:DataValidationArtifact):
        try:
            modelperformancetrackerconfig=ModelPerformanceTrackerConfig(training_pipeline_config=self.training_pipeline_config,FILE_NAME=self.file_name,TARGET_NAME=self.target_name)

            modelperformancetracker=ModelPerformanceTracker(model_performance_tracker_config=modelperformancetrackerconfig,model_trainer_artifact=model_trainer_artifact,data_validation_artifact=data_validation_artifact)

            logging.info("initiate model performance tracker")
            performance_metric_artifact=modelperformancetracker.initiate_performance_tracker()

            return performance_metric_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    ## local artifact is going to s3 bucket  
    def sync_artifact_dir_to_s3(self):
        try:
            aws_bucket_url=f"s3://{TRAINING_BUCKET_NAME}/artifact/{self.training_pipeline_config.timestamp}"
            self.s3_sync.sync_folder_to_s3(
                folder=self.training_pipeline_config.artifact_dir,
                aws_bucket_url=aws_bucket_url
            )
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
    
    ## my local final model is pushed to s3 bucket
    def sync_saved_model_dir_to_s3(self):
        try:
            aws_bucket_url=f"s3://{TRAINING_BUCKET_NAME}/final_model/{self.training_pipeline_config.timestamp}"
            self.s3_sync.sync_folder_to_s3(
                folder=self.training_pipeline_config.model_dir,
                aws_bucket_url=aws_bucket_url
            )
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def run_pipeline(self):
        try:
            logging.info("Initiating Machine learning pipeline")
            data_ingestion_artifact=self.start_data_ingestion()
            data_validation_artifact=self.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)

            data_transformation_artifact=self.start_data_transformation(data_validation_artifact=data_validation_artifact)

            model_trainer_artifact=self.start_model_trainer(data_transformation_artifact=data_transformation_artifact,data_validation_artifact=data_validation_artifact, grid_search=False
            )

            model_performance_tracker_artifact=self.start_performance_tracker(model_trainer_artifact=model_trainer_artifact,data_validation_artifact=data_validation_artifact)

            print(model_performance_tracker_artifact)

            if model_performance_tracker_artifact.r2_score == True:
                logging.info("R2_score below previous performance. Beginning Grid search")
                ## This means that new data has changed the performance for worse.
                ## begin grid search to find optimal performance.
                model_trainer_artifact=self.start_model_trainer(
                    data_validation_artifact=data_validation_artifact,
                    data_transformation_artifact=data_transformation_artifact,
                    grid_search=True
                )

                if model_trainer_artifact==None:
                    return
                
                model_performance_tracker_artifact=self.start_performance_tracker(model_trainer_artifact=model_trainer_artifact,data_validation_artifact=data_validation_artifact)
                
                print(model_performance_tracker_artifact)

            logging.info("Machine learning pipeline excecuted")

            # logging.info("Pushing Artifact and Saved Model to AWS S3 Bucket")
            # self.sync_artifact_dir_to_s3()
            # self.sync_saved_model_dir_to_s3()
            # logging.info("Syncing to AWS S3 Bucket successful")

            return model_trainer_artifact
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)




    