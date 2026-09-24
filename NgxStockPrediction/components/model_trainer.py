import os
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


import mlflow ## For tracking and managing your machine learning project

import dagshub

# dagshub.init(repo_owner='udeaniizu04', repo_name='SectorLevel_StockPerformance_Predictoion', mlflow=True) ## This is the template in dagshub(under experiment), after i have connected to my github repository. This part was copied only because the mlfow object is already here in ModelTrainer.track_mlflow

class ModelTrainer:
    def __init__(self,model_trainer_config:ModelTrainerConfig,data_validation_artifact: DataValidationArtifact,data_transformation_artifact:DataTransformationArtifact):
        try:
            self.model_trainer_config=model_trainer_config
            self.data_transformation_artifact=data_transformation_artifact ## We will use this for SARIMAX
            self.data_validation_artifact=data_validation_artifact ## We will use this for SARIMA
            self.target_name=model_trainer_config.target_name
            self.symbol=model_trainer_config.file_name

        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    @staticmethod
    def read_data(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NGXStockPredictionException(e,sys) 
         
    def track_mlflow(self,model_type:str,best_model,performance_metric,model_parameters):
        with mlflow.start_run():
            model_type=model_type
            r2_score=performance_metric.r2_score
            rmse=performance_metric.rmse
            order=model_parameters['order']
            seasonal_order=model_parameters['seasonal_order']

            mlflow.log_metric('r2_score',r2_score) ## logging in the local environment but because we are now connected to dagshub it will all be pushed to the remote repository instead
            mlflow.log_metric('rmse',rmse) ## .log_metric is for float data
            mlflow.log_param('model_type',model_type)
            mlflow.log_param('target_feature',self.target_name)
            mlflow.log_param('order',order) ## .log_param is for others. in this case we are logging a tuple
            mlflow.log_param('seasonal_order',seasonal_order)
            mlflow.statsmodels.log_model(best_model,f'{self.symbol}_model')

    def update_current_model_parameter(self, stock: str, target: str, order, seasonal_order, r2_score, rmse):
        try:
            path = 'model_parameters/current_model_parameters.csv'

            if os.path.exists(path) and os.path.getsize(path) > 0:
                params_df = self.read_data(path)
            else:
                params_df = pd.DataFrame(columns=['stock', 'target', 'order', 'seasonal_order', 'r2_score', 'rmse'])

            mask = (params_df['stock'] == stock) if 'stock' in params_df.columns else pd.Series(dtype=bool)

            if mask.any():
                idx = params_df.index[mask][0]  # the single matching row's index label
                params_df.at[idx, 'target'] = target
                params_df.at[idx, 'order'] = str(order)
                params_df.at[idx, 'seasonal_order'] = str(seasonal_order)
                params_df.at[idx, 'r2_score'] = float(r2_score)
                params_df.at[idx, 'rmse'] = float(rmse)
            else:
                new_row = {
                    'stock': stock,
                    'target': target,
                    'order': str(order),
                    'seasonal_order': str(seasonal_order),
                    'r2_score': float(r2_score),
                    'rmse': float(rmse)
                }
                params_df = pd.concat([params_df, pd.DataFrame([new_row])], ignore_index=True)

            os.makedirs(os.path.dirname(path), exist_ok=True)
            params_df.to_csv(path, index=False)

            return params_df

        except Exception as e:
            raise NGXStockPredictionException(e, sys)
        
    def sarima_train_model(self,train_data,test_data,order,seasonal_order,forecast_step): ## we will do both train and evaluation here so we dont have to create another file for it
        try:
            ## store model parameters for the artifact
            model_parameters={'order':order,'seasonal_order':seasonal_order,'forecast_step':forecast_step}

            y_train=train_data[self.target_name].dropna()
            y_test=test_data[self.target_name].dropna()

            mod = SARIMAX(
            y_train,
            order=order, 
            seasonal_order=seasonal_order,
            )

            model = mod.fit(disp=False)
            fcst=model.forecast(steps=10+forecast_step)

            y_pred = fcst.iloc[:10] ## We just need the first 10 predictions to evaluate the model because the test size is 10
            future  = fcst.iloc[-forecast_step:]

            print(f'complete forecast {self.target_name}: ', fcst)
            print(f'The next two months {self.target_name}: ',future)

            performance_metric = get_performance_score(
                y_true=np.asarray(y_test), y_pred=np.asarray(y_pred)
            )
            # track the experiments with flow
            # self.track_mlflow(
            #     model_type='sarima',
            #     best_model=model,
            #     performance_metric=performance_metric,
            #     model_parameters=model_parmeters
            # ) ## a folder will be created called mlruns. You will be able to see the number of experiments (folder) that will contain the outputs of the entire run flow. inside the mlruns->0 (folder) contains the experiments. NOTE: It is advisable not to push mlruns folder to github unless it is very necessary for prodution. 
            
            ## But dagshub will now collect all the experiment files instead. since we have initialized it

            model_dir_path=os.path.dirname(self.model_trainer_config.trained_model_file_path)
            os.makedirs(model_dir_path,exist_ok=True)

            ## save the trained model object
            save_object(self.model_trainer_config.trained_model_file_path,obj=model) ## Krish did 'obj=NetworkModel'. check back incase you are wrong

            ## Model Trainer Artifact
            model_trainer_artifact=ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,test_metric_artifact=performance_metric,
                training_parameters=model_parameters)
            logging.info(f"Model trainer artifact: {model_trainer_artifact}") 

            self.update_current_model_parameter(
                stock=self.symbol,
                target=self.target_name,
                order=model_parameters['order'],
                seasonal_order=model_parameters['seasonal_order'],
                r2_score=performance_metric.r2_score,
                rmse=performance_metric.rmse
            )

            return model_trainer_artifact
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def sarimax_train_model(self,X_train,y_train,X_test,y_test,order,seasonal_order,forecast_step): ## we will do both train and evaluation here so we dont have to create another file for it
        try:
            ## store model parameters for the artifact
            model_parmeters={'order':order,'seasonal_order':seasonal_order,'forecast_step':forecast_step}
            

            mod = SARIMAX(
                endog=y_train,
                exog=X_train,
                order=order,
                seasonal_order=seasonal_order,
            )

            model = mod.fit(disp=False)
            fcst = model.forecast(steps=10+forecast_step, exog = X_test)

            y_pred = fcst[:10] ## We just need the first 10 predictions to evaluate the model because the test size is 10

            print(f'complete forecast {self.target_name}: ', fcst)

            performance_metric = get_performance_score(
                y_true=np.asarray(y_test), y_pred=np.asarray(y_pred)
            )

            # track the experiments with flow
            # self.track_mlflow(
            #     model_type='sarimax',
            #     best_model=model,
            #     performance_metric=performance_metric,
            #     model_parameters=model_parmeters
            # ) ## a folder will be created called mlruns. You will be able to see the number of experiments (folder) that will contain the outputs of the entire run flow. inside the mlruns->0 (folder) contains the experiments. NOTE: It is advisable not to push mlruns folder to github unless it is very necessary for prodution. 
            
            ## But dagshub will now collect all the experiment files instead. since we have initialized it

            model_dir_path=os.path.dirname(self.model_trainer_config.trained_model_file_path)
            os.makedirs(model_dir_path,exist_ok=True)

            ## save the trained model object
            save_object(self.model_trainer_config.trained_model_file_path,obj=model) ## Krish did 'obj=NetworkModel'. check back incase you are wrong

            ## Model Trainer Artifact
            model_trainer_artifact=ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,test_metric_artifact=performance_metric,
                training_parameters=model_parmeters)
            logging.info(f"Model trainer artifact: {model_trainer_artifact}") 

            return model_trainer_artifact
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    
    def sarima_grid_search_model_trainer(self, train_data, test_data,grid={'p':1,'i':1,'q':1,'P':1,'D':1,'Q':1},
                                            season=12):
        try:
            y_train = train_data[self.target_name].dropna()
            y_test = test_data[self.target_name].dropna()

            scores = []
            for p in range(grid['p']):
                for i in range(grid['i']):
                    for q in range(grid['q']):
                        for P in range(grid['P']):
                            for D in range(grid['D']):
                                for Q in range(grid['Q']):
                                    try:
                                        mod = SARIMAX(y_train, order=(p, i, q),
                                                    seasonal_order=(P, D, Q, season))
                                        res = mod.fit(disp=False)
                                        fcst = res.forecast(steps=10)

                                        performance_metric = get_performance_score(
                                                    y_true=np.asarray(y_test), y_pred=np.asarray(fcst)
                                                )
                                        
                                        score = [p, i, q, P, D, Q,
                                                performance_metric.r2_score,
                                                performance_metric.rmse]
                                        
                                        print(score)
                                        scores.append(score)
                                        del mod
                                        del res
                                    except Exception as e:
                                        print(f'errored: (p={p},i={i},q={q},P={P},D={D},Q={Q}) -> {e}')

            if not scores:
                raise ValueError("No SARIMAX combination succeeded — check for a systematic error above.")


            result_df = pd.DataFrame(scores, columns=['p', 'i', 'q', 'P', 'D', 'Q', 'score', 'rmse'])
            result_df = result_df.sort_values('score', ascending=False)

            best_row = result_df.iloc[0]
            best_param = {
                'order': (int(best_row['p']), int(best_row['i']), int(best_row['q'])),
                'seasonal_order': (int(best_row['P']), int(best_row['D']), int(best_row['Q']), season),
                'r2_score': float(best_row['score']),
                'rmse': float(best_row['rmse']),
            }
            print('best_param',best_param)

            return best_param
        
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

    def sarimax_grid_search_model_trainer(self, X_train,y_train,X_test,y_test,grid={'p':1,'i':1,'q':1,'P':1,'D':1,'Q':1},season=12):
        try:
            scores = []
            for p in range(grid['p']):
                for i in range(grid['i']):
                    for q in range(grid['q']):
                        for P in range(grid['P']):
                            for D in range(grid['D']):
                                for Q in range(grid['Q']):
                                    try:
                                        mod = SARIMAX(endog=y_train,
                                                    exog=X_train, 
                                                    order=(p, i, q),
                                                    seasonal_order=(P, D, Q, season))
                                        res = mod.fit(disp=False)
                                        fcst = res.forecast(steps=10, exog=X_test)
                                        performance_metric = get_performance_score(
                                                    y_true=np.asarray(y_test), y_pred=np.asarray(fcst)
                                                )
                                        
                                        score = [p, i, q, P, D, Q,
                                                performance_metric.r2_score,
                                                performance_metric.rmse]
                                        
                                        print(score)
                                        scores.append(score)
                                        del mod
                                        del res
                                    except Exception as e:
                                        print(f'errored: (p={p},i={i},q={q},P={P},D={D},Q={Q}) -> {e}')

            if not scores:
                raise ValueError("No SARIMAX combination succeeded — check for a systematic error above.")
            
            result_df = pd.DataFrame(scores, columns=['p', 'i', 'q', 'P', 'D', 'Q', 'score', 'rmse'])
            result_df = result_df.sort_values('score', ascending=False)

            best_row = result_df.iloc[0]
            best_param = {
                'order': (int(best_row['p']), int(best_row['i']), int(best_row['q'])),
                'seasonal_order': (int(best_row['P']), int(best_row['D']), int(best_row['Q']), season),
                'r2_score': float(best_row['score']),
                'rmse': float(best_row['rmse']),
            }
            print('best_param',best_param)

            return best_param
        
        except Exception as e:
                    raise NGXStockPredictionException(e,sys)

        
    def initiate_model_trainer(self, model_type:str,order=(1,1,1),seasonal_order=(1,1,1,12), forecast_step=1)->ModelTrainerArtifact:
        try:
            if model_type.lower()=="sarima":
                train_file_path=self.data_validation_artifact.valid_train_file_path

                test_file_path=self.data_validation_artifact.valid_test_file_path

                train_data=self.read_data(train_file_path)
                test_data=self.read_data(test_file_path)

                model_trainer_artifact=self.sarima_train_model(
                    train_data=train_data,
                    test_data=test_data,
                    order=order,
                    seasonal_order=seasonal_order,
                    forecast_step=forecast_step
                )

                return model_trainer_artifact

            
            elif model_type.lower()=="sarimax":
                train_file_path=self.data_transformation_artifact.transformed_train_file_path

                test_file_path=self.data_transformation_artifact.transformed_test_file_path

                ## loaading training array and testing array
                train_arr=load_numpy_array_data(train_file_path)
                test_arr=load_numpy_array_data(test_file_path)

                x_train,y_train,x_test,y_test=(
                    train_arr[:,:-1],
                    train_arr[:,-1],
                    test_arr[:,:-1],
                    test_arr[:,-1],
                )

                model_trainer_artifact=self.sarimax_train_model(
                    X_train=x_train,
                    y_train=y_train,
                    X_test=x_test,
                    y_test=y_test,
                    order=order,
                    seasonal_order=seasonal_order,
                    forecast_step=forecast_step
                )

                return model_trainer_artifact
            
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

