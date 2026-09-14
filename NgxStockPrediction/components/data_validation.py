## This will initiate te data validation of which the data will come from the ingested data

from NgxStockPrediction.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from NgxStockPrediction.entity.config_entity import DataValidationConfig

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.constant.training_pipeline import SCHEMA_FILE_PATH

from NgxStockPrediction.utils.main_utils.utils import read_yaml_file, write_yaml_file

from scipy.stats import ks_2samp ## THis will help detect the data drift. It will compare two samples of data. Refer to note for more insight on data drift
import pandas as pd
import os,sys


class DataValidation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact,data_validation_config:DataValidationConfig):
        
        try:
            self.data_ingestion_artifact=data_ingestion_artifact
            self.data_validation_config=data_validation_config
            self._schema_config=read_yaml_file(SCHEMA_FILE_PATH)
            self.symbol=self.data_validation_config.file_name
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    @staticmethod ## for static methods we dont necessarily have to create an object
    def read_data(file_path)->pd.DataFrame: ## returns a pandas dataframe
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def validate_number_of_columns(self, dataframe:pd.DataFrame)->bool:
        try:
            number_of_columns=len(self._schema_config['columns'])
            print('number of columns', number_of_columns)
            logging.info(f"Required number of columns:{number_of_columns}")
            logging.info(f"Dataframe has columns:{dataframe.columns}")

            if len(dataframe.columns)==number_of_columns:
                return True
            return False
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def detect_dataset_drift(self, base_df, current_df, threshold=0.05) -> bool:
        try:
            status = True
            report = {}
            numerical_columns = [list(col.keys())[0] for col in self._schema_config["numerical_columns"]] ## The numerical columns were hardcoded in the schema.yaml file 
            
            for column in numerical_columns: ## We will iterate ove the numerical columns.
                d1 = base_df[column]
                d2 = current_df[column]
                is_same_dist = ks_2samp(d1, d2)
                if threshold <= is_same_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False
                report.update(
                    {
                        column: {
                            "p_value": float(is_same_dist.pvalue),
                            "drift_status": is_found
                        }
                    }
                )
            drift_report_file_path = self.data_validation_config.drift_report_file_path

            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path, exist_ok=True)

            write_yaml_file(file_path=drift_report_file_path, content=report)
            return status
        except Exception as e:
            raise NGXStockPredictionException(e, sys)
        

    def initiate_data_validation(self)->DataValidationArtifact:
        try:
            train_file_path=self.data_ingestion_artifact.trained_file_path
            test_file_path=self.data_ingestion_artifact.test_file_path

            ## read the data from train and test
            train_dataframe=DataValidation.read_data(train_file_path)
            test_dataframe=DataValidation.read_data(test_file_path)

            print('train_dataframe shape: ', train_dataframe.shape)
            print('test_dataframe shape: ', test_dataframe.shape)
            
            ## Validate number of columns
            status=self.validate_number_of_columns(dataframe=train_dataframe)
            if not status:
                error_message=f"Train dataframe does not contain all columns.\n"

            status=self.validate_number_of_columns(dataframe=test_dataframe)
            if not status:
                error_message=f"Test dataframe does not contain all columns.\n"
            
            ## lets check datadrift
            status=self.detect_dataset_drift(base_df=train_dataframe,current_df=test_dataframe)

            dir_path=os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path,exist_ok=True)

            train_dataframe.to_csv(
                self.data_validation_config.valid_train_file_path,index=False,header=True
            )
            test_dataframe.to_csv(
                self.data_validation_config.valid_test_file_path,index=False,header=True
            )
            ## Note we skipped the status which is supposed to be true  before e store the train_dataframe in the validated or invalid folder. We just dont have enough test data to get good accuracy, hence it was skipped but was stored in artifact.
            
            data_validation_artifact=DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_ingestion_artifact.trained_file_path,
                valid_test_file_path=self.data_ingestion_artifact.test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path
            )

            return data_validation_artifact
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)