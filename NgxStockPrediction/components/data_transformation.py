import sys
import os
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline

from NgxStockPrediction.constant.training_pipeline import TARGET_RETURNS_COLUMN,TARGET_PRICE_COLUMN
from NgxStockPrediction.constant.training_pipeline import DATA_TRANSFORMATION_IMPUTER_PARAMS
from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact, DataValidationArtifact
from NgxStockPrediction.entity.config_entity import DataTransformationConfig
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.constant.training_pipeline import SCHEMA_FILE_PATH
from NgxStockPrediction.utils.main_utils.utils import read_yaml_file

from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.exception.exception import NGXStockPredictionException

from NgxStockPrediction.utils.main_utils.utils import save_numpy_array_data,save_object


class DataTransformation:
    def __init__(self,data_validation_artifact:DataValidationArtifact, data_transformation_config:DataTransformationConfig):
        try:
            self.data_validation_artifact=data_validation_artifact
            self.data_transformation_config=data_transformation_config
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    @staticmethod
    def read_data(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def get_data_transformer_object(cls)->Pipeline: ## The pipeline we are going to use is the knn imputer
        """
        It initializes a KNNImputer object with the parameters specified in the training_pipeline.py file and returns a Pipeline object with the KNNImputer object as the first step.

        Args:
            cls: DataTransformation

        Returns:
            A Pipeline object
        """

        logging.info(
            "Enter get_data_transforme_object method of Transformation class"
        )
        try:
            imputer:KNNImputer=KNNImputer(**DATA_TRANSFORMATION_IMPUTER_PARAMS)## The double star (**) tells the parameter to consider the argument as key-value pairs.
            logging.info(
                f"Initialize KNNImputer with {DATA_TRANSFORMATION_IMPUTER_PARAMS}"
            )
            processor:Pipeline=Pipeline([("Imputer",imputer)])
            return processor
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        

        
    def initiate_data_transformation(self, TARGET_COLUMN:str)->DataTransformationArtifact:
        """
        NOTE: THIS WILL ONLY BE INITIATED FOR TESTING OR WHEN WE WANT TO DO MULTIVARIATE TIME SERIES (SARIMAX). This is a time series project
        """
        logging.info("Entered initiate_data_transformation method of DataTransformation class")
        try:
            self.target_column=TARGET_COLUMN
            self._schema_config=read_yaml_file(SCHEMA_FILE_PATH)
            numerical_columns = [
                key for col in self._schema_config["numerical_columns"]
                for key in col.keys() if key != 'id'
            ] ## The numerical columns were hardcoded in the schema.yaml file
            print('numerical columns for transformation: ', numerical_columns)

            logging.info("Starting Data Transformation")
            ## Note the data for transformation comes from the data validation artifact because We will transform only the valid data
            train_df=DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df=DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)

            ## training dataframe (recall we have already removed non-numeric columns from the data when validating)
            input_feature_train_df=train_df[numerical_columns].drop(columns=[TARGET_PRICE_COLUMN,TARGET_RETURNS_COLUMN]) ## We are dropping the close_price and returns
            target_feature_train_df=train_df[self.target_column] ## We will choose this on initiation.

            ## testing dataframe
            input_feature_test_df=test_df[numerical_columns].drop(columns=[TARGET_PRICE_COLUMN,TARGET_RETURNS_COLUMN])
            target_feature_test_df=test_df[self.target_column]

            preprocessor=self.get_data_transformer_object()

            preprocessor_object=preprocessor.fit(input_feature_train_df)
            transformed_input_train_feature=preprocessor_object.transform(input_feature_train_df) ## Dont get confused here we could have just used fit_transform() directly for the train data.We just want to show how it is done separately
            transformed_input_test_feature=preprocessor_object.transform(input_feature_test_df) 

            ## recall the transformed output will be an array

            train_arr=np.c_[transformed_input_train_feature,np.array(target_feature_train_df)]

            test_arr=np.c_[transformed_input_test_feature,np.array(target_feature_test_df)]

            ## save numpy array data
            save_numpy_array_data(self.data_transformation_config.transformed_train_file_path,array=train_arr)

            save_numpy_array_data(self.data_transformation_config.transformed_test_file_path,array=test_arr)

            save_object(self.data_transformation_config.transformed_object_file_path,preprocessor_object)

            save_object("final_model/preprocessor.pkl", preprocessor_object)

            ##preparing artifacts

            data_transformation_artifact=DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )
            
            return data_transformation_artifact

        except Exception as e:
            raise NGXStockPredictionException(e,sys)




