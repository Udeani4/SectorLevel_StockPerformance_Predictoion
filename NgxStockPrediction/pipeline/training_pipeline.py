## This will resemble our main.py steps but we will use classes
import os,sys

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
    def __init__(self):
        self.training_pipeline_config=TrainingPipelineConfig()
        # self.s3_sync=S3Sync()
    
    def start_data_ingestion(self):
        try:
            self.data_ingestion_config=DataIngestionConfig(training_pipeline_config=self.training_pipeline_config)

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
            data_validation_config=DataValidationConfig(training_pipeline_config=self.training_pipeline_config)
            data_validation=DataValidation(data_ingestion_artifact=data_ingestion_artifact,data_valdation_config=data_validation_config)

            logging.info("Initiate the data Validation")
            data_validation_artifact=data_validation.initiate_data_validation()
            logging.info("Dta Validation complete")

            return data_validation_artifact

        except Exception as e:
            raise NGXStockPredictionException(e,sys)  

    def start_data_transformation(
            self,data_validation_artfact:DataValidationArtifact
        ):
        try:
            data_transformation_config=DataTransformationConfig(training_pipeline_config=self.training_pipeline_config)
            data_transformation=DataTransformation(data_transformation_config=data_transformation_config,data_validation_artifact=data_validation_artfact)

            logging.info("Initiate data transformation")
            data_transformation_artifact=data_transformation.initiate_data_transformation() 
            logging.info("Data transformation complete")

            return data_transformation_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
    
    def start_model_trainer(
            self,data_transformation_artifact:DataTransformationArtifact
        ):
        try:
            self.model_trainer_config: ModelTrainerConfig = ModelTrainerConfig(training_pipeline_config=self.training_pipeline_config)

            model_trainer=ModelTrainer(model_trainer_config=self.model_trainer_config,data_transformation_artifact=data_transformation_artifact)

            logging.info("initiate Model trainer")
            model_trainer_artifact=model_trainer.initiate_model_trainer()
            logging.info("Model Training complete")

            return model_trainer_artifact
        
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
            data_validaton_artifact=self.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)
            data_transformtion_artifact=self.start_data_transformation(data_validation_artfact=data_validaton_artifact)
            model_trainer_artifact=self.start_model_trainer(data_transformation_artifact=data_transformtion_artifact)
            logging.info("Machine learning pipeline excecuted")

            logging.info("Pushing Artifact and Saved Model to AWS S3 Bucket")
            self.sync_artifact_dir_to_s3()
            self.sync_saved_model_dir_to_s3()
            logging.info("Syncing to AWS S3 Bucket successful")

            return model_trainer_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)




    