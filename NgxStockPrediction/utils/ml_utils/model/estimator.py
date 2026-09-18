## This file will give you all the details with respect to the information required in the model
import os,sys
from NgxStockPrediction.constant.training_pipeline import SAVED_MODEL_DIR, MODEL_FILE_NAME
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging

class TimeNgxStockModel:
    """
    This class is used to create an instance. We can use it to predict the time series data
    """
    def __init__(self,preprocessor,model,exog):
        try:
            self.preprocessor=preprocessor
            self.model=model
            self.exog=exog
        except Exception as e:
            raise NGXStockPredictionException
        
    def sarimax_predict(self): ## For now we wont be using SARIMAX. That will require another data transformation to take place and Macroeconomic data will be ingested too.
        try:
            exog_transform=self.preprocessor.transform(self.exog)
            y_hat=self.model.forecast(step=10, exog=exog_transform[-10:])
            return y_hat
        except Exception as e:
            raise NGXStockPredictionException(e,sys)
        
    


