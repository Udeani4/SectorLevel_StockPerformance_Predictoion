## If you want to make any prediction from the front end.import os
import sys
import os

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.utils.main_utils.utils import save_object,load_object, load_numpy_array_data

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

    @staticmethod
    def get_stock_mkt_cap(stock: str):
        try:
            all_stock_file_path = "stock_data/All_Stocks_Info"

            all_stocks_info = pd.read_csv(all_stock_file_path)

            match = all_stocks_info.loc[all_stocks_info['symbol'] == stock, 'market_cap']

            if match.empty:
                raise ValueError(f"No market cap data found for stock: {stock}")

            return match.values[0]

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
                returns = ((last_pred - performance_data['true'].iloc[-1]) / performance_data['true'].iloc[-1])*100
            elif target_name == 'returns':
                returns = last_pred
            else:
                raise ValueError(f"Unsupported target_name: {target_name}")

            stock_movement = "up" if returns > 0 else "down"

            movement_cm = confusion_matrix(
                performance_data['true_movement'],
                performance_data['predicted_movement'],
                labels=["up", "down"]  # forces a 2x2 matrix even if one class is missing
            )
            tn, fp, fn, tp = movement_cm.ravel()
            movement_accuracy = (tp + tn) / (tp + tn + fp + fn)

            r2_ = r2_score(y_true=performance_data['true'], y_pred=performance_data['predicted'])

            predictions = {
                'returns': returns, ## this is the next months returns
                'movement': stock_movement,
                'returns_accuracy': r2_,
                'movement_accuracy': movement_accuracy,
                # 'next_forecast': last_pred
            }
            print(f"{stock} predictions: ", predictions)
            
            return predictions

        except Exception as e:
            raise NGXStockPredictionException(e, sys)

    def predict_sector_returns_and_movement(self, sector: str, forecast_step: int):
        try:
            sector_path = f"feature_engineering/stocks_sectors/{sector}"
            current_params_path = "model_parameters/current_model_parameters.csv"
            current_params_df = self.read_data(current_params_path)
            
            working_stocks_dir = 'each_stock_model_notebook'  # anchor this properly relative to a known root, not '../../'

            working_stocks = []
            if os.path.exists(working_stocks_dir):
                working_stocks = [f.split('_')[0] for f in os.listdir(working_stocks_dir)]

            if not working_stocks:
                raise ValueError(f"No working stocks found in {working_stocks_dir} — check the path.")

            stocks_mkt_cap = {}
            stocks_returns = {}
            returns_accuracy_list = []

            for filename in os.listdir(sector_path):
                stock = filename.split('_')[0]
                if stock == 'INFINITY' or stock not in working_stocks:
                    continue

                target_match = current_params_df.loc[current_params_df['stock'] == stock, 'target']
                if target_match.empty:
                    continue  # stock hasn't been trained yet, skip it

                target_name = target_match.values[0]

                stock_predictions = self.predict_stock_returns_and_movement(
                    target_name=target_name,
                    stock=stock,
                    forecast_step=forecast_step
                )

                stock_mkt_cap = self.get_stock_mkt_cap(stock=stock)
                stocks_mkt_cap[stock] = stock_mkt_cap
                stocks_returns[stock] = stock_predictions['returns']
                returns_accuracy_list.append(stock_predictions['returns_accuracy'])

            total_mkt_cap = sum(stocks_mkt_cap.values())
            print(f'{sector} total market cap: ', total_mkt_cap)
            print(f"{sector} stocks market cap: ", stocks_mkt_cap)
            print(f"{sector} stock returns: ", stocks_returns)

            weighted_stock_returns = {}
            if total_mkt_cap > 0:
                for stock, returns in stocks_returns.items():
                    weighted_stock_returns[stock] = returns * (stocks_mkt_cap[stock] / total_mkt_cap)

            print(f"{sector} weighted stock returns: ", weighted_stock_returns)

            # Already a weighted average — do NOT divide by len() again
            sector_returns = sum(weighted_stock_returns.values()) if weighted_stock_returns else 0
            sector_movement = "up" if sector_returns > 0 else "down"
            sector_accuracy = sum(returns_accuracy_list) / len(returns_accuracy_list) if returns_accuracy_list else 0

            sector_predictions = {
                'sector_returns': sector_returns,
                'sector_movement': sector_movement,
                'sector_accuracy': sector_accuracy
            }

            return sector_predictions

        except Exception as e:
            raise NGXStockPredictionException(e, sys)


