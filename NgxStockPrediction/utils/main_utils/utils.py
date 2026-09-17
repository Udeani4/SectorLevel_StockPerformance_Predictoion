## Here we will define the functions we will use across the project.

import yaml
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

import pandas as pd
import numpy as np
import os,sys
import dill
import pickle
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score

## Mainly for Validation report
def read_yaml_file(file_path:str)->dict: ## returns the value in a dictionary form
    try:
        with open(file_path,"rb") as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e
    
def write_yaml_file(file_path:str,content:object,replace:bool=False)->None:
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,"w") as file:
            yaml.dump(content,file)
    except Exception as e:
        raise NGXStockPredictionException(e,sys)


## Mainly for transformation
def save_numpy_array_data(file_path:str,array:np.array):
    """
    Save numpy array data to file
    file_path: str location of file to save
    array: np.array data to save
    """
    try:
        dir_path=os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)
        with open(file_path,"wb") as file_obj:
            np.save(file_obj,array)
    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e
    
def load_numpy_array_data(file_path:str)->np.array:
    """
    load numpy array data from file 
    file_path: str location of file to load
    return: np.array data loaded
    """
    try:
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e

def save_object(file_path:str, obj:object)->None:
    try:
        logging.info("Entered the save_object method of MainUtils class")
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,"wb") as file_obj:
            pickle.dump(obj,file_obj)

        logging.info("Exited the save_object method or MAinUtils class")
    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e
    

def load_object(file_path:str,)->object:
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exists")
        with open(file_path,"rb") as file_obj:
            print(file_obj)
            return pickle.load(file_obj)
    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e


## THis should be under ml_utils
def evaluate_models(X_train,y_train,X_test,y_test,models,params):
    try:
        test_report={}
        train_report={}
        model_object_dict={}

        for i in range(len(list(models))):
            model=list(models.values())[i]
            model_params=params[list(models.keys())[i]]

            gs=GridSearchCV(model,model_params,cv=3)
            gs.fit(X_train,y_train)

            model.set_params(**gs.best_params_) ## or you could just use model=gs.best_estimator_ and go straight to predicting. because the gs.best_estimator_ is the best fitted model
            model.fit(X_train,y_train)

            y_train_pred=model.predict(X_train)
            y_test_pred=model.predict(X_test)

            train_model_score=r2_score(y_train,y_train_pred)
            test_model_score=r2_score(y_test,y_test_pred)

            test_report[list(models.keys())[i]]=test_model_score

            train_report[list(models.keys())[i]]=train_model_score

            model_object_dict[list(models.keys())[i]]=model

        return test_report, train_report, model_object_dict

    except Exception as e:
        raise NGXStockPredictionException(e,sys) from e


