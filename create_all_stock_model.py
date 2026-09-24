from NgxStockPrediction.pipeline.training_pipeline import TrainingPipeline
from NgxStockPrediction.exception.exception import NGXStockPredictionException
import pandas as pd
import os
import sys

default_parameters_dict={ ## The ones commented out are too small
    'ACADEMY': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)},
    # 'ACCESSCORP': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, 
    # 'AFRINSURE': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, 
    'AFRIPRUD': {'target_name':'close_price','order':(1,0,1),'seasonal_order':(1,0,1,12)}, 
    'AIICO': {'target_name':'close_price','order':(2,1,2),'seasonal_order':(1,0,0,12)}, 
    'BERGER': {'target_name':'returns','order':(0,2,2),'seasonal_order':(2,1,0,12)}, 
    'BETAGLAS': {'target_name':'close_price','order':(0,1,1),'seasonal_order':(2,1,0,12)}, 
    'BUACEMENT': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(1,0,1,12)}, 
    'CADBURY': {'target_name':'returns','order':(1,1,0),'seasonal_order':(2,0,2,12)}, 
    'CAP': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(2,2,0,12)}, 
    'CHAMS': {'target_name':'close_price','order':(2,2,2),'seasonal_order':(1,2,0,12)}, 
    # 'CONOIL': {'target_name':'close_price','order':(0,2,1),'seasonal_order':(0,0,0,12)}, ## not good enough
    'CORNERST': {'target_name':'returns','order':(1,0,1),'seasonal_order':(0,0,0,12)}, 
    'CUSTODIAN': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(0,0,0,12)}, 
    'CUTIX': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(0,0,2,12)}, 
    'DAARCOMM': {'target_name':'close_price','order':(1,2,0),'seasonal_order':(0,2,2,12)}, 
    'DANGCEM': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(0,2,1,12)}, 
    'DANGSUGAR': {'target_name':'close_price','order':(2,2,2),'seasonal_order':(1,1,1,12)}, 
    # 'EKOCORP': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, ## too static
    'ELLAHLAKES': {'target_name':'close_price','order':(2,0,0),'seasonal_order':(0,0,1,12)}, 
    'ETERNA': {'target_name':'returns','order':(2,0,2),'seasonal_order':(0,0,0,12)}, 
    # 'ETI': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, ## no good model
    'FCMB': {'target_name':'close_price','order':(0,0,0),'seasonal_order':(1,2,2,12)}, 
    'FIDELITYBK': {'target_name':'returns','order':(1,0,1),'seasonal_order':(0,2,2,12)}, 
    'FIDSON': {'target_name':'close_price','order':(1,2,2),'seasonal_order':(0,2,0,12)}, 
    'FTNCOCOA': {'target_name':'close_price','order':(0,2,2),'seasonal_order':(2,1,2,12)}, 
    # 'GUINEAINS': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, ## no good model
    'GUINNESS': {'target_name':'close_price','order':(2,2,1),'seasonal_order':(0,0,2,12)}, 
    'IKEJAHOTEL': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(2,2,1,12)}, 
    'INFINITY': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(1,2,1,12)}, 
    'INTBREW': {'target_name':'returns','order':(2,1,0),'seasonal_order':(0,0,0,12)}, 
    'JAIZBANK': {'target_name':'returns','order':(2,1,0),'seasonal_order':(2,1,2,12)}, 
    'JBERGER': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(2,2,0,12)}, 
    'JOHNHOLT': {'target_name':'close_price','order':(1,2,0),'seasonal_order':(2,0,0,12)}, 
    'LASACO': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(0,0,1,12)}, 
    'LEARNAFRCA': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(2,1,2,12)}, 
    # 'LINKASSURE': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)},  ## no good model
    'LIVESTOCK': {'target_name':'returns','order':(1,2,0),'seasonal_order':(0,0,1,12)}, 
    'MAYBAKER': {'target_name':'close_price','order':(2,2,2),'seasonal_order':(0,1,0,12)}, 
    'MBENEFIT': {'target_name':'returns','order':(1,0,2),'seasonal_order':(0,0,0,12)}, 
    'MCNICHOLS': {'target_name':'returns','order':(0,2,1),'seasonal_order':(2,2,2,12)}, 
    'MEYER': {'target_name':'returns','order':(1,1,2),'seasonal_order':(2,0,1,12)}, 
    # 'MORISON': {'target_name':'close_price','order':(2,0,2),'seasonal_order':(1,0,0,12)}, ## no good model
    'NAHCO': {'target_name':'close_price','order':(1,2,2),'seasonal_order':(2,2,0,12)}, 
    'NASCON': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(1,1,0,12)}, 
    'NB': {'target_name':'returns','order':(2,0,2),'seasonal_order':(0,0,2,12)}, 
    'NCR': {'target_name':'returns','order':(0,1,0),'seasonal_order':(0,2,0,12)}, 
    'NEIMETH': {'target_name':'close_price','order':(2,2,1),'seasonal_order':(0,1,1,12)}, 
    # 'NEM': {'target_name':'returns','order':(0,0,2),'seasonal_order':(0,0,0,12)}, No good model
    'NESTLE': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(2,2,2,12)}, 
    'NNFM': {'target_name':'returns','order':(1,0,0),'seasonal_order':(0,0,2,12)}, 
    'NPFMCRFBK': {'target_name':'returns','order':(1,2,2),'seasonal_order':(2,1,1,12)}, 
    'OANDO': {'target_name':'returns','order':(1,0,2),'seasonal_order':(2,0,2,12)}, 
    'OKOMUOIL': {'target_name':'close_price','order':(0,2,1),'seasonal_order':(0,0,0,12)}, 
    # 'PHARMDEKO': {'target_name':'close_price','order':(1,1,0),'seasonal_order':(0,1,0,12)}, overfitting
    'PRESTIGE': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(0,1,2,12)}, 
    'PZ': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(0,2,0,12)}, 
    'REDSTAREX': {'target_name':'close_price','order':(2,2,2),'seasonal_order':(2,1,2,12)}, 
    'ROYALEX': {'target_name':'close_price','order':(1,0,0),'seasonal_order':(2,1,0,12)}, 
    'RTBRISCOE': {'target_name':'returns','order':(0,1,0),'seasonal_order':(0,2,2,12)}, 
    'SOVRENINS': {'target_name':'returns','order':(2,0,2),'seasonal_order':(1,0,0,12)}, 
    'STANBIC': {'target_name':'close_price','order':(1,2,0),'seasonal_order':(0,0,0,12)}, 
    'SUNUASSUR': {'target_name':'returns','order':(1,0,2),'seasonal_order':(2,1,0,12)}, 
    # 'TOTAL': {'target_name':'close_price','order':(1,1,0),'seasonal_order':(0,0,0,12)}, Its overfitting
    'TRANSCOHOT': {'target_name':'close_price','order':(2,2,1),'seasonal_order':(0,2,1,12)}, 
    'TRANSEXPR': {'target_name':'close_price','order':(2,1,2),'seasonal_order':(0,2,0,12)}, 
    'UACN': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(2,1,0,12)}, 
    # 'UBA': {'target_name':'returns','order':(1,0,0),'seasonal_order':(0,0,0,12)}, Not good enough
    'UCAP': {'target_name':'returns','order':(2,0,0),'seasonal_order':(0,0,1,12)}, 
    'UNILEVER': {'target_name':'close_price','order':(2,2,2),'seasonal_order':(2,0,1,12)}, 
    'UNIONDICON': {'target_name':'returns','order':(2,1,0),'seasonal_order':(2,1,0,12)}, 
    # 'UNITYBNK': {'target_name':'close_price','order':(2,2,0),'seasonal_order':(0,0,0,12)}, 
    'UPDCREIT': {'target_name':'close_price','order':(0,2,1),'seasonal_order':(0,1,0,12)}, 
    'VERITASKAP': {'target_name':'returns','order':(0,1,0),'seasonal_order':(2,1,2,12)}, 
    'VITAFOAM': {'target_name':'close_price','order':(0,2,1),'seasonal_order':(1,2,0,12)}, 
    'WAPIC': {'target_name':'returns','order':(0,1,0),'seasonal_order':(1,1,0,12)}, 
    'WEMABANK': {'target_name':'close_price','order':(1,2,2),'seasonal_order':(0,1,1,12)}, 
    'ZENITHBANK': {'target_name':'close_price','order':(0,2,0),'seasonal_order':(2,1,0,12)}
    }

data = []
problem_stocks=[]

for key,value in default_parameters_dict.items():
    try:
        train_pipeline=TrainingPipeline(
            file_name=key,
            target_name=value['target_name'],
            model_type="sarima",
            order=value['order'], 
            seasonal_order=value['seasonal_order'],
            forecast_step=1
        )

        model_trainer_artifact=train_pipeline.run_pipeline()

        r2_score=model_trainer_artifact.test_metric_artifact.r2_score
        rmse=model_trainer_artifact.test_metric_artifact.rmse

        rows_dict={'stock': key, 'target': value['target_name'], 'order': value['order'], 'seasonal_order': value['seasonal_order'], 'r2_score':r2_score, 'rmse':rmse}

        data.append(rows_dict)

        # return {"message":"Training endpoint reached"} ##comment out later
    except Exception as e:
        print(f'Error occured with {key}')
        problem_stocks.append(key)
        # raise NGXStockPredictionException(e,sys)

dataframe = pd.DataFrame(data=data)
dataframe.to_csv('model_parameters/current_model_parameters.csv')
print('problem stocks', problem_stocks)