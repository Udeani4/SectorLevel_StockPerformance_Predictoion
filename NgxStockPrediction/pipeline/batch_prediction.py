## If you want to make any prediction from the front end.import os
import sys

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact,DataValidationArtifact
from NgxStockPrediction.entity.config_entity import ModelTrainerConfig

from NgxStockPrediction.utils.ml_utils.model.estimator import TimeNgxStockModel
from NgxStockPrediction.utils.main_utils.utils import save_object,load_object, load_numpy_array_data
from NgxStockPrediction.utils.ml_utils.metric.performance_metric import get_performance_score


import random
random.seed(12345)
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import json


