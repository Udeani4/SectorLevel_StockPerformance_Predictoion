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

import mlflow ## For tracking and managing your machine learning project

import dagshub
dagshub.init(repo_owner='udeaniizu04', repo_name='NgxStockPrediction', mlflow=True) ## This is the template in dagshub(under experiment), after i have connected to my github repository. This part was copied only because the mlfow object is already here in ModelTrainer.track_mlflow

class ModelTrainer:
    def __init__(self,model_trainer_config:ModelTrainerConfig,data_validation_artifact: DataValidationArtifact,data_transformation_artifact:DataTransformationArtifact):
        try:
            self.model_trainer_config=model_trainer_config
            self.data_transformation_artifact=data_transformation_artifact ## We will use this for SARIMAX
            self.data_validation_artifact=data_validation_artifact ## We will use this for SARIMA
            self.target_name=model_trainer_config.target_name

        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def track_mlflow(self,best_model,classification_metric):
        with mlflow.start_run():
            f1_score=classification_metric.f1_score
            precision_score=classification_metric.precision_score
            recall_score=classification_metric.recall_score

            mlflow.log_metric('f1_score',f1_score) ## logging in the local environment but because we are now connected to dagshub it will all be pushed to the remote repository instead
            mlflow.log_metric('precision_score',precision_score)
            mlflow.log_metric('recall_score',recall_score)
            mlflow.sklearn.log_model(best_model,'model')

    
    def sarima_train_model(self,train_data,test_data,order,seasonal_order,forcast_step): ## we will do both train and evaluation here so we dont have to create another file for it
        
        y_train=train_data[self.target_name].dropna()
        y_test=test_data[self.target_name].dropna()

        mod = SARIMAX(
        y_train,
        order=order, 
        seasonal_order=seasonal_order,
        )

        model = mod.fit(disp=False)
        fcst=model.forecast(step=10+forcast_step)

        y_pred=fcst[:10] ## We just need the first 10 predictions to evaluate the model because the test size is 10

        performance_metric=get_performance_score(y_true=y_test,y_pred=y_pred)

        ## track the experiments with flow
        self.track_mlflow(
            f"{self.target_name}",performance_metric
        ) ## a folder will be created called mlruns. You will be able to see the number of experiments (folder) that will contain the outputs of the entire run flow. inside the mlruns->0 (folder) contains the experiments. NOTE: It is advisable not to push mlruns folder to github unless it is very necessary for prodution. 
        
        ## But dagshub will now collect all the experiment files instead. since we have initialized it

        model_dir_path=os.path.dirname(self.model_trainer_config.trained_model_file_path)
        os.makedirs(model_dir_path,exist_ok=True)

        ## save the trained model object
        save_object(self.model_trainer_config.trained_model_file_path,obj=model) ## Krish did 'obj=NetworkModel'. check back incase you are wrong

        ## Model Trainer Artifact
        model_trainer_artifact=ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,test_metric_artifact=performance_metric)
        logging.info(f"Model trainer artifact: {model_trainer_artifact}") 

        return model_trainer_artifact

    def sarimax_train_model(self,X_train,y_train,X_test,y_test,order,seasonal_order,forcast_step): ## we will do both train and evaluation here so we dont have to create another file for it

        endog = y_train.dropna()
        exog = X_train.dropna()

        # 2, 1, 1, 3, 2, 2
        mod = SARIMAX(
        endog=endog,
        exog=exog,
        order=order,
        seasonal_order=seasonal_order,
        )

        model = mod.fit(disp=False)
        fcst = model.forecast(steps=10+forcast_step, exog = X_test)

        y_pred=fcst[:10] ## We just need the first 10 predictions to evaluate the model because the test size is 10

        performance_metric=get_performance_score(y_true=y_test,y_pred=y_pred)

        ## track the experiments with flow
        self.track_mlflow(
            model,performance_metric
        ) ## a folder will be created called mlruns. You will be able to see the number of experiments (folder) that will contain the outputs of the entire run flow. inside the mlruns->0 (folder) contains the experiments. NOTE: It is advisable not to push mlruns folder to github unless it is very necessary for prodution. 
        
        ## But dagshub will now collect all the experiment files instead. since we have initialized it

        model_dir_path=os.path.dirname(self.model_trainer_config.trained_model_file_path)
        os.makedirs(model_dir_path,exist_ok=True)

        ## save the trained model object
        save_object(self.model_trainer_config.trained_model_file_path,obj=model) ## Krish did 'obj=NetworkModel'. check back incase you are wrong

        ## Model Trainer Artifact
        model_trainer_artifact=ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,test_metric_artifact=performance_metric)
        logging.info(f"Model trainer artifact: {model_trainer_artifact}") 

        return model_trainer_artifact
    

        
    def initiate_model_trainer(self, model_type:str,order=(1,1,1),seasonal_order=(1,1,1,12), forcast_step=1)->ModelTrainerArtifact:
        try:
            if model_type.lower()=="sarima":
                train_file_path=self.data_validation_artifact.valid_train_file_path

                test_file_path=self.data_validation_artifact.valid_test_file_path

                model_trainer_artifact=self.sarima_train_model(
                    train_data=train_file_path,
                    test_data=test_file_path,
                    order=order,
                    seasonal_order=seasonal_order,
                    forcast_step=forcast_step
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

                model_trainer_artifact=self.train_model(x_train,y_train,x_test,y_test)

                return model_trainer_artifact
            
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

