import os
import sys

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact,DataValidationArtifact
from NgxStockPrediction.entity.config_entity import ModelTrainerConfig,ModelPerformanceTrackerConfig

from NgxStockPrediction.utils.ml_utils.model.estimator import TimeNgxStockModel
from NgxStockPrediction.utils.main_utils.utils import save_object,load_object, load_numpy_array_data
from NgxStockPrediction.utils.ml_utils.metric.performance_metric import get_performance_score


import random
random.seed(12345)
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import json


## This is where we keep updating the data and track for performance drift

class ModelPerformanceTracker:
    def __init__(self,model_performance_tracker_config:ModelPerformanceTrackerConfig,model_trainer_artifact:ModelTrainerArtifact,data_validation_artifact:DataValidationArtifact):
        self.model_performance_tracker_config=model_performance_tracker_config
        self.model_trainer_artifact=model_trainer_artifact
        self.data_validation_artifact=data_validation_artifact
        self.target_name=self.model_performance_tracker_config.target_name
        self.symbol=self.model_performance_tracker_config.file_name

    @staticmethod
    def read_data(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys) 

    def create_performance_data_and_tracker(self):
        performance_data_path=self.model_performance_tracker_config.model_performance_data_path
        performance_tracker_path=self.model_performance_tracker_config.model_performance_tracker_path
        model_object_path=self.model_trainer_artifact.trained_model_file_path
        test_file_path=self.data_validation_artifact.valid_test_file_path

        test_data=self.read_data(test_file_path)
        model_object=load_object(model_object_path)

        


