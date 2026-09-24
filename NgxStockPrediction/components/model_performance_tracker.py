import os
import sys

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact,DataValidationArtifact,PerformanceMetricTrackerArtifact
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

    @staticmethod
    def _values_close(a, b):
        try:
            return np.isclose(float(a), float(b))
        except (ValueError, TypeError):
            return str(a) == str(b) ## since order and seasonal_order are tuples 

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

            fcst = model_object.forecast(steps=10 + forecast_step)
            fcst=list(fcst)

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

                true_pct_change = (pd.Series(test_list_for_movement).pct_change()*100).dropna().reset_index(drop=True)
                predicted_pct_change = (pd.Series(fcst_list_for_movement).pct_change()*100).dropna().reset_index(drop=True)

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

            os.makedirs(os.path.dirname(performance_data_path), exist_ok=True)
            performance_df.to_csv(performance_data_path)

            return {'confusion_matrix': movement_cm, f'next_month_{self.target_name}': float(fcst[10])}
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def update_performance_tracker(self, movement_cm, next_fcst):
        performance_data_path = self.model_performance_tracker_config.model_performance_data_path
        tracker_path = self.model_performance_tracker_config.model_performance_tracker_path
        model_parameters = self.model_trainer_artifact.training_parameters

        if os.path.exists(performance_data_path):
            performance_df = self.read_data(performance_data_path)
        else:
            return "Performance Dataframe does not exist"

        tn, fp, fn, tp = movement_cm.ravel()
        movement_accuracy = (tp + tn) / (tp + tn + fp + fn)

        r2 = r2_score(performance_df['true'], performance_df['predicted'])
        rmse = np.sqrt(mean_squared_error(performance_df['true'], performance_df['predicted']))

        last_row = performance_df.iloc[-1]
        year = int(last_row['year'])
        month = int(last_row['month'])

        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

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
            'movement_accuracy': movement_accuracy,
            'order': model_parameters['order'],
            'seasonal_order': model_parameters['seasonal_order']
        }

        numeric_cols = ['r2_score', 'rmse', 'tp', 'tn', 'fp', 'fn', 'movement_accuracy',
                        f'next_month_{self.target_name}_prediction']

        if os.path.exists(tracker_path):
            tracker_df = pd.read_csv(tracker_path)
            for c in numeric_cols:
                if c in tracker_df.columns:
                    tracker_df[c] = pd.to_numeric(tracker_df[c], errors='coerce')
        else:
            tracker_df = pd.DataFrame(columns=list(new_row.keys()))

        # check if an entry for this year/month already exists
        existing_mask = (
            (tracker_df['year'] == next_year) &
            (tracker_df['month_predicted'] == next_month) &
            (tracker_df['order'].astype(str) == str(new_row['order'])) &
            (tracker_df['seasonal_order'].astype(str) == str(new_row['seasonal_order']))
        )
        
        if existing_mask.any():
            existing_row = tracker_df.loc[existing_mask].iloc[0]

            # compare all fields except year/month_predicted (the key itself)
            compare_cols = [c for c in new_row.keys() if c not in ('year', 'month_predicted')]
            is_identical = all(
                self._values_close(existing_row[c], new_row[c]) for c in compare_cols
            )

            if is_identical:
                # nothing changed — skip write entirely, just recompute the comparison result
                previous_row = tracker_df.iloc[tracker_df.index.get_loc(existing_mask.idxmax()) - 1] \
                    if existing_mask.idxmax() > 0 else None
            else:
                # data changed — replace the existing row in place
                row_idx = tracker_df.loc[existing_mask].index[0]

                scalar_cols = [c for c in new_row.keys() if c not in ('order', 'seasonal_order')]
                tracker_df.loc[row_idx, scalar_cols] = [new_row[c] for c in scalar_cols]
                tracker_df.loc[row_idx, 'order'] = str(new_row['order'])
                tracker_df.loc[row_idx, 'seasonal_order'] = str(new_row['seasonal_order'])

                tracker_df.to_csv(tracker_path, index=False)
                prev_idx = existing_mask.idxmax() - 1
                previous_row = tracker_df.loc[prev_idx] if prev_idx >= 0 else None
        else:
            # brand new entry — append
            previous_row = tracker_df.iloc[-1] if len(tracker_df) > 0 else None

            new_row_for_storage = dict(new_row)
            new_row_for_storage['order'] = str(new_row['order'])
            new_row_for_storage['seasonal_order'] = str(new_row['seasonal_order'])

            tracker_df = pd.concat([tracker_df, pd.DataFrame([new_row_for_storage])], ignore_index=True)
            tracker_df.to_csv(tracker_path, index=False)

        if previous_row is not None:
            result = {
                'r2_score': r2 < previous_row['r2_score'],
                'rmse': rmse > previous_row['rmse']
            }
        else:
            result = {'r2_score': False, 'rmse': False}

        return result
    
    def initiate_performance_tracker(self)->PerformanceMetricTrackerArtifact:
        """
        Creates and updates the performance 
        """
        try:
            performance_dict=self.create_performance_data()
            performance_metric_tracker_artifact=self.update_performance_tracker(movement_cm=performance_dict['confusion_matrix'],next_fcst=performance_dict[f'next_month_{self.target_name}'])

            return performance_metric_tracker_artifact
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        





        


