import os
import sys

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact,DataValidationArtifact
from NgxStockPrediction.entity.config_entity import ModelTrainerConfig,ModelPerformanceTrackerConfig

from NgxStockPrediction.utils.ml_utils.model.estimator import TimeNgxStockModel
from NgxStockPrediction.utils.main_utils.utils import save_object,load_object, load_numpy_array_data
from NgxStockPrediction.utils.ml_utils.metric.performance_metric import get_performance_score
from sklearn.metrics import confusion_matrix




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

    def create_performance_data(self):
        try:
            performance_data_path = self.model_performance_tracker_config.model_performance_data_path
            
            model_object_path = self.model_trainer_artifact.trained_model_file_path
            test_file_path = self.data_validation_artifact.valid_test_file_path
            train_file_path = self.data_validation_artifact.valid_train_file_path
            forecast_step = self.model_trainer_artifact.training_parameters['forecast_step']

            test_data = self.read_data(test_file_path)
            train_data = self.read_data(train_file_path)
            model_object = load_object(model_object_path)

            fcst = model_object.forecast(step=10 + forecast_step)
            y_test = test_data[self.target_name]

            performance_df = pd.DataFrame({
                'year': test_data['year'],
                'month': test_data['month'],
                'true': test_data[self.target_name],
                'predicted': fcst[:10]
            })

            if self.target_name == "close_price":
                # prepend last training price so the first pct_change isn't NaN
                last_train_price = train_data[self.target_name].iloc[-1]

                test_list_for_movement = [last_train_price] + y_test.tolist()
                fcst_list_for_movement = [last_train_price] + list(fcst[:10])

                true_pct_change = pd.Series(test_list_for_movement).pct_change().dropna().reset_index(drop=True)
                predicted_pct_change = pd.Series(fcst_list_for_movement).pct_change().dropna().reset_index(drop=True)

                performance_df['true_pct_change'] = true_pct_change
                performance_df['predicted_pct_change'] = predicted_pct_change

                performance_df['true_movement'] = np.where(performance_df['true_pct_change'] > 0, 'up', 'down')
                performance_df['predicted_movement'] = np.where(performance_df['predicted_pct_change'] > 0, 'up', 'down')

            elif self.target_name == "returns":
                performance_df['true_movement'] = np.where(performance_df['true'] > 0, 'up', 'down')
                performance_df['predicted_movement'] = np.where(performance_df['predicted'] > 0, 'up', 'down')

            else:
                raise ValueError(f"Unsupported target_name: {self.target_name}")

            movement_cm = confusion_matrix(performance_df['true_movement'], performance_df['predicted_movement'])
            print(movement_cm)
            performance_df.to_csv(performance_data_path)

            return {'confusion_matrix': movement_cm, f'next_month_{self.target_name}': fcst[10]}
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def update_performance_tracker(self, movement_cm, next_fcst):
        """Appends a new row to the performance tracker and flags metric degradation."""
        try:
            tracker_path = self.model_performance_tracker_config.model_performance_tracker_path
            performance_data_path = self.model_performance_tracker_config.model_performance_data_path

            if os.path.exists(performance_data_path):
                performance_df=self.read_data(performance_data_path)
            else:
                return "Performance Dataframe does not exist"
        
            
            tn, fp, fn, tp = movement_cm.ravel()
            movement_accuracy = (tp + tn) / (tp + tn + fp + fn)

            r2 = r2_score(performance_df['true'], performance_df['predicted'])
            rmse = np.sqrt(mean_squared_error(performance_df['true'], performance_df['predicted']))

            year = int(last_row['year'])
            month = int(last_row['month'])

            if month == 12:
                next_year, next_month = year + 1, 1
            else:
                next_year, next_month = year, month + 1

            last_row = performance_df.iloc[-1]

            new_row = {
                'year': next_year,
                'month_predicted': next_month,
                f"next_month_{self.target_name}_prediction": next_fcst,
                'r2_score': r2,
                'rmse': rmse,
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn,
                'movement_accuracy': movement_accuracy
            }

            if os.path.exists(tracker_path):
                tracker_df = self.read_data(tracker_path)
                previous_row = tracker_df.iloc[-1] if len(tracker_df) > 0 else None
            else:
                tracker_df = pd.DataFrame(columns=list(new_row.keys()))
                previous_row = None

            tracker_df = pd.concat([tracker_df, pd.DataFrame([new_row])], ignore_index=True)
            tracker_df.to_csv(tracker_path, index=False)

            if previous_row is not None:
                result = {
                    'r2_score': r2 < previous_row['r2_score'],
                    'rmse': rmse > previous_row['rmse']
                }
            else:
                result = {'r2_score': False, 'rmse': False}

            return result
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def initiate_performance_tracker(self):
        """
        Creates and updates the performance 
        """
        try:
            performance_dict=self.create_performance_data()
            performance_update=self.update_performance_tracker(movement_cm=performance_dict['confusion_matrix'],next_fcst=performance_dict[f'next_month_{self.target_name}'])

            print('performance update:', performance_update)
            return performance_update
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        





        


