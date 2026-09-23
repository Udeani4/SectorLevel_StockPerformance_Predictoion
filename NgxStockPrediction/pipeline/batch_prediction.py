## If you want to make any prediction from the front end.import os
import sys
import os

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
from sklearn.metrics import confusion_matrix
import numpy as np
import pandas as pd
import json


## Recall this is built strictly for sarima (UNIVARIATE)
class Predict:
    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    @staticmethod
    def read_data(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    @staticmethod
    def get_stock_sector_name(stock: str):
        try:
            for sector in os.listdir('feature_engineering/stocks_sectors'):
                sector_path = f'feature_engineering/stocks_sectors/{sector}'
                for filename in os.listdir(sector_path):
                    if filename.split('_')[0] == stock:
                        return sector
            return None  # stock not found in any sector
        except Exception as e:
            raise NGXStockPredictionException(e, sys)
        
    def predict_stock_returns_and_movement(self, target_name: str, stock: str, forecast_step: int):
        try:
            model_file_path = f'Artifacts/{stock}/model_trainer/trained_model/{target_name}_model.pkl'
            performance_file_path = f'Artifacts/{stock}/performance_tracker/{target_name}/performance_data.csv'

            model_obj = load_object(model_file_path)
            performance_data = self.read_data(performance_file_path)

            stock_preds = model_obj.forecast(steps=10 + forecast_step)
            last_pred = stock_preds.iloc[-1] if hasattr(stock_preds, 'iloc') else stock_preds[-1]

            if target_name == 'close_price':
                returns = last_pred - performance_data['true'].iloc[-1]
            elif target_name == 'returns':
                returns = last_pred
            else:
                raise ValueError(f"Unsupported target_name: {target_name}")

            stock_movement = "up" if returns >= 0 else "down"

            movement_cm = confusion_matrix(
                performance_data['true_movement'],
                performance_data['predicted_movement'],
                labels=["up", "down"]  # forces a 2x2 matrix even if one class is missing
            )
            tn, fp, fn, tp = movement_cm.ravel()
            movement_accuracy = (tp + tn) / (tp + tn + fp + fn)

            r2_ = r2_score(y_true=performance_data['true'], y_pred=performance_data['predicted'])

            predictions = {
                'returns': returns,
                'movement': stock_movement,
                'returns_accuracy': r2_,
                'movement_accuracy': movement_accuracy,
                'next_forecast': last_pred
            }

            return predictions

        except Exception as e:
            raise NGXStockPredictionException(e, sys)

    def predict_sector_returns_and_movement(self, sector: str):
        try:
            sector_path=f"feature_engineering/stocks_sectors/{sector}"
            current_params_path="model_parameters/current_model_parameters.csv"
            current_params_df=self.read_data(current_params_path)


            for filename in os.listdir(sector_path):
                stock = filename.split('_')[0]
                target_name=current_params_df.loc[stock,'target']
                


                    

        except Exception as e:
            raise NGXStockPredictionException(e,sys)

