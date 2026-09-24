## We will use fast api

import sys,os,io

import certifi
ca=certifi.where()

from dotenv import load_dotenv
load_dotenv()

import pymongo
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.pipeline.training_pipeline import TrainingPipeline
from NgxStockPrediction.utils.main_utils.utils import load_object
from NgxStockPrediction.pipeline.batch_prediction import Predict
# from NgxStockPrediction.utils.ml_utils.model.estimator import NetworkModel

from NgxStockPrediction.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME, DATA_INGESTION_COLLECTION_NAME

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,File,UploadFile,Request
from uvicorn import run as app_run ## The app_run will run the app by still using > python app.py (we were using uvicorn keyword). So any will still work
from fastapi.responses import Response

from starlette.responses import RedirectResponse
import pandas as pd

mongodb_uri=os.getenv("MONGO_DB_CLUSTER_URL")
client = pymongo.MongoClient(mongodb_uri,tlsCAFile=ca)

database=client[DATA_INGESTION_DATABASE_NAME]
collection=database[DATA_INGESTION_COLLECTION_NAME]


##steps to using fastapi

app=FastAPI()
origins =["*"]

app.add_middleware( ## This will allow access to the browser
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from fastapi.templating import Jinja2Templates ## this is responsible for picking up the html files in the template
templates = Jinja2Templates(directory="templates") ## define the templates


@app.get("/",tags=["authentication"]) ## a get request
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    ##initiate training pipeline
    try:
        train_pipeline=TrainingPipeline(
            file_name="CHAMS",
            target_name="close_price",
            model_type="sarima",
            order=(2,2,2), 
            seasonal_order=(1,2,0,12),
            forecast_step=1
        )

        train_pipeline.run_pipeline()
        return Response('training is successful')
        # return {"message":"Training endpoint reached"} ##comment out later
    except Exception as e:
        raise NGXStockPredictionException(e,sys)


# @app.post("/predict")
# async def predict_route(request:Request, file:UploadFile=File(...)):
#     try:
#         df=pd.read_csv(file.file)
#         ##print(df)
#         preprocessor=load_object("final_model/preprocessor.pkl")
#         final_model=load_object("final_model/model.pkl")
#         network_model=NetworkModel(preprocessor=preprocessor,model=final_model)
#         print(df.iloc[0])
#         y_pred=network_model.predict(df)
#         print(y_pred)
#         df['predicted_column']=y_pred
#         print(df['predicted_column'])

#         df.to_csv("prediction_output/output.csv")
#         table_html=df.to_html(classes='table table-striped')
#         return templates.TemplateResponse(
#             "table.html",
#             {
#                 "request":request,
#                 "table":table_html
#             }
#         )
#     except Exception as e:
#         raise NGXStockPredictionException(e,sys)

if __name__=="__main__":
    app_run(app=app,host="0.0.0.0",port=8000)    