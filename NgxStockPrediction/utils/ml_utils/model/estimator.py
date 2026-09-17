## This file will give you all the details with respect to the information required in the model
import os,sys
from NgxStockPrediction.constant.training_pipeline import SAVED_MODEL_DIR, MODEL_FILE_NAME
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

class NGXStockModel:
    """
    This class is used to create an instance. We can use it to predict any new data because it contains our preprocessor object and the trained model object
    """
    def __init__(self,preprocessor,model):
        try:
            self.preprocessor=preprocessor
            self.model=model
        except Exception as e:
            raise NGXStockPredictionException
        
    def predict(self,x):
        try:
            x_transform=self.preprocessor.transform(x)
            y_hat=self.model.predict(x_transform)
            return y_hat
        except Exception as e:
            raise NGXStockPredictionException(e,sys)

class TimeNgxStockModel:
    """
    This class is used to create an instance. We can use it to predict the time series data
    """
    def __init__(self,preprocessor,model):
        try:
            self.preprocessor=preprocessor
            self.model=model
        except Exception as e:
            raise NGXStockPredictionException
        
    def sarimax_predict(self,exog): ## For now we wont be using SARIMAX. That will require another data transformation to take place and Macroeconomic data will be ingested too.
        try:
            exog_transform=self.preprocessor.transform(exog)
            y_hat=self.model.forecast(step=10, exog=exog_transform[-10:])
            return y_hat
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    def sarima_predict(self):
        try:
            y_hat=self.model.forecast(steps=11)
            return y_hat
        except Exception as e:
            raise NGXStockPredictionException(e,sys)


