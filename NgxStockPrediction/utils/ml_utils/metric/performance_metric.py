import os, sys
from NgxStockPrediction.entity.artifact_entity import PerformanceMetricArtifact
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from sklearn.metrics import r2_score,mean_squared_error
import numpy as np

def get_performance_score(y_true,y_pred)->PerformanceMetricArtifact:
    try:
        model_accuracy=r2_score(y_true,y_pred)
        model_mse=mean_squared_error(y_true,y_pred)
        model_rmse=np.sqrt(model_mse)

        performance_metrics=PerformanceMetricArtifact(
            r2_score=model_accuracy,
            rmse=model_rmse
        )
        # {'accuracy':model_accuracy,'rmse':model_rmse}
        return performance_metrics
    except Exception as e:
        raise NGXStockPredictionException(e,sys)



