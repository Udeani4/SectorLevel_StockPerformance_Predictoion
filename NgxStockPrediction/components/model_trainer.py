import os
import sys

from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

from NgxStockPrediction.entity.artifact_entity import DataTransformationArtifact,ModelTrainerArtifact
from NgxStockPrediction.entity.config_entity import ModelTrainerConfig

from NgxStockPrediction.utils.ml_utils.model.estimator import NetworkModel
from NgxStockPrediction.utils.main_utils.utils import save_object,load_object, load_numpy_array_data, evaluate_models 
from NgxStockPrediction.utils.ml_utils.metric.performance_metric import get_performance_score

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    AdaBoostClassifier,
    GradientBoostingClassifier,
)

import mlflow ## For tracking and managing your machine learning project

import dagshub
dagshub.init(repo_owner='udeaniizu04', repo_name='NgxStockPrediction', mlflow=True) ## This is the template in dagshub(under experiment), after i have connected to my github repository. This part was copied only because the mlfow object is already here in ModelTrainer.track_mlflow

class ModelTrainer:
    def __init__(self,model_trainer_config:ModelTrainerConfig,data_transformation_artifact:DataTransformationArtifact):
        try:
            self.model_trainer_config=model_trainer_config
            self.data_transformation_artifact=data_transformation_artifact
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

    
    def sarima_train_model(self,train_data,test_data): ## we will do both train and evaluation here so we dont have to create another file for it
        model_report:dict
        model_objects:object

        model_report,_,model_objects=evaluate_models(X_train=X_train,y_train=y_train,X_test=X_test,y_test=y_test,models=models,params=params)

        ## To get the best model from the dictionary
        best_model_score=max(sorted(model_report.values()))

        ## to get the best model name
        best_model_name=list(model_report.keys())[
            list(model_report.values()).index(best_model_score)
        ]

        best_model = model_objects[best_model_name]

        ## Train classification score
        y_train_pred=best_model.predict(X_train)
        classification_train_metric=get_classification_score(y_true=y_train,y_pred=y_train_pred)

        ## track the experiments with flow
        self.track_mlflow(
            best_model,classification_train_metric
        ) ## a folder will be created called mlruns. You will be able to see the number of experiments (folder) that will contain the outputs of the entire run flow. inside the mlruns->0 (folder) contains the experiments. NOTE: It is advisable not to push mlruns folder to github unless it is very necessary for prodution. 
        
        ## But dagshub will now collect all the experiment files instead. since we have initialized it

        ## Test classification score
        y_test_pred=best_model.predict(X_test)
        classification_test_metric=get_classification_score(y_true=y_test,y_pred=y_test_pred)


        preprocessor=load_object(file_path=self.data_transformation_artifact.transformed_object_file_path)

        model_dir_path=os.path.dirname(self.model_trainer_config.trained_model_file_path)
        os.makedirs(model_dir_path,exist_ok=True)

        network_model=NetworkModel(preprocessor=preprocessor,model=best_model)

        ## save the trained model object
        save_object(self.model_trainer_config.trained_model_file_path,obj=NetworkModel) ## Krish did 'obj=NetworkModel'. check back incase you are wrong

        save_object("final_model/model.pkl", best_model)



        
        ## Model Trainer Artifact
        model_trainer_artifact=ModelTrainerArtifact(
            trained_model_file_path=self.model_trainer_config.trained_model_file_path,trained_metric_artifact=classification_train_metric,test_metric_artifact=classification_test_metric)
        logging.info(f"Model trainer artifact: {model_trainer_artifact}") 

        return model_trainer_artifact

        
    def initiate_model_trainer(self)->ModelTrainerArtifact:
        try:
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

