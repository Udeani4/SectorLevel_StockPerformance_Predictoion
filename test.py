import os,sys,json
from dotenv import load_dotenv
from NgxStockPrediction.pipeline.batch_prediction import Predict


load_dotenv()

stock='ACADEMY'

sector="consumer_goods"

predict_obj=Predict()

sector_name=predict_obj.get_stock_sector_name(stock)

print(f'{stock} sector: ', sector_name)

predict_next_month=predict_obj.predict_stock_returns_and_movement(
    stock=stock,
    target_name='close_price',
    forecast_step=1
)

print(f'{stock} next month prediction: ', predict_next_month)

next_month_sector_prediction=predict_obj.predict_sector_returns_and_movement(
    sector=sector,
    forecast_step=1
)

print(f'{sector} next month prediction: ', next_month_sector_prediction)