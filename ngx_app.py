"""
Minimal Flask app for viewing the NGX Predictions front-end.

This just serves the HTML/CSS/JS pages (now in templates/) and returns
sample JSON from the same endpoints the front-end already calls (see
static/js/api.js), so you can click through the whole UI with no real
pipeline wired up yet.

Run:
    pip install flask
    python apptest.py
Then open http://127.0.0.1:5000
"""
## We will use fast api

import sys,os,io

from dotenv import load_dotenv
load_dotenv()

import certifi

import pymongo
# from NgxStockPrediction.exception.exception import NGXStockPredictionException
# from NgxStockPrediction.logging.logger import logging
# from NgxStockPrediction.pipeline.training_pipeline import TrainingPipeline
# from NgxStockPrediction.utils.main_utils.utils import load_object
from NgxStockPrediction.pipeline.batch_prediction import Predict
# from NgxStockPrediction.pipeline.create_all_stock_model import CreateAllStockModel

from NgxStockPrediction.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME, DATA_INGESTION_COLLECTION_NAME

import pandas as pd
import random
from datetime import date, timedelta

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ca=certifi.where()

mongodb_uri=os.getenv("MONGO_DB_CLUSTER_URL")
client = pymongo.MongoClient(mongodb_uri,tlsCAFile=ca)

database=client[DATA_INGESTION_DATABASE_NAME]
collection=database[DATA_INGESTION_COLLECTION_NAME]

# ---------------------------------------------------------------------------
# Sample data — replace with real pipeline output whenever you're ready.
# Field names match exactly what static/js/api.js expects.
# ---------------------------------------------------------------------------

# SECTORS = [
#     {"sector": "Banking", "predicted_return": 0.048, "accuracy": 0.81},
#     {"sector": "Consumer Goods", "predicted_return": 0.021, "accuracy": 0.74},
#     {"sector": "Oil & Gas", "predicted_return": -0.014, "accuracy": 0.69},
#     {"sector": "Industrial Goods", "predicted_return": 0.033, "accuracy": 0.77},
#     {"sector": "Insurance", "predicted_return": 0.012, "accuracy": 0.63},
#     {"sector": "Agriculture", "predicted_return": -0.006, "accuracy": 0.58},
# ]

STOCKS_BY_SECTOR = {
    "Banking": [
        {"symbol": "ZENITHBANK", "name": "Zenith Bank Plc", "predicted_return": 0.052,
         "accuracy": 0.83, "movement": "up", "movement_accuracy": 0.88},
        {"symbol": "GTCO", "name": "Guaranty Trust Holding Co.", "predicted_return": 0.041,
         "accuracy": 0.80, "movement": "up", "movement_accuracy": 0.79},
        {"symbol": "UBA", "name": "United Bank for Africa", "predicted_return": 0.037,
         "accuracy": 0.76, "movement": "up", "movement_accuracy": 0.74},
        {"symbol": "ACCESSCORP", "name": "Access Holdings Plc", "predicted_return": 0.028,
         "accuracy": 0.72, "movement": "down", "movement_accuracy": 0.61},
        {"symbol": "FBNH", "name": "FBN Holdings Plc", "predicted_return": -0.011,
         "accuracy": 0.65, "movement": "down", "movement_accuracy": 0.69},
    ],
    "Consumer Goods": [
        {"symbol": "NESTLE", "name": "Nestle Nigeria Plc", "predicted_return": 0.031,
         "accuracy": 0.78, "movement": "up", "movement_accuracy": 0.75},
        {"symbol": "BUAFOODS", "name": "BUA Foods Plc", "predicted_return": 0.024,
         "accuracy": 0.71, "movement": "up", "movement_accuracy": 0.70},
        {"symbol": "NB", "name": "Nigerian Breweries Plc", "predicted_return": -0.009,
         "accuracy": 0.66, "movement": "down", "movement_accuracy": 0.64},
    ],
    "Oil & Gas": [
        {"symbol": "SEPLAT", "name": "Seplat Energy Plc", "predicted_return": -0.018,
         "accuracy": 0.70, "movement": "down", "movement_accuracy": 0.72},
        {"symbol": "OANDO", "name": "Oando Plc", "predicted_return": -0.009,
         "accuracy": 0.62, "movement": "down", "movement_accuracy": 0.58},
    ],
    "Industrial Goods": [
        {"symbol": "DANGCEM", "name": "Dangote Cement Plc", "predicted_return": 0.036,
         "accuracy": 0.79, "movement": "up", "movement_accuracy": 0.81},
        {"symbol": "BUACEMENT", "name": "BUA Cement Plc", "predicted_return": 0.029,
         "accuracy": 0.74, "movement": "up", "movement_accuracy": 0.70},
    ],
    "Insurance": [
        {"symbol": "AIICO", "name": "AIICO Insurance Plc", "predicted_return": 0.014,
         "accuracy": 0.60, "movement": "up", "movement_accuracy": 0.55},
        {"symbol": "NEM", "name": "NEM Insurance Plc", "predicted_return": 0.009,
         "accuracy": 0.64, "movement": "up", "movement_accuracy": 0.59},
    ],
    "Agriculture": [
        {"symbol": "OKOMUOIL", "name": "Okomu Oil Palm Plc", "predicted_return": -0.004,
         "accuracy": 0.59, "movement": "down", "movement_accuracy": 0.53},
        {"symbol": "PRESCO", "name": "Presco Plc", "predicted_return": -0.008,
         "accuracy": 0.57, "movement": "down", "movement_accuracy": 0.55},
    ],
}

STOCK_LIST = [
    {"symbol": s["symbol"], "name": s["name"]}
    for stocks in STOCKS_BY_SECTOR.values()
    for s in stocks
]


def sample_performance(symbol: str):
    base = 100 + (ord(symbol[0]) % 20)
    rows = []
    today = date.today()
    for i in range(9, -1, -1):
        d = today - timedelta(days=i * 7)
        actual = round(base + random.uniform(-3, 3) + i * 0.6, 2)
        predicted = round(actual + random.uniform(-2, 2), 2)
        error = round((predicted - actual) / actual * 100, 2)
        rows.append({"date": d.isoformat(), "actual": actual, "predicted": predicted, "error": error})

    tracker = [
        {"metric": "MAE", "value": "1.84"},
        {"metric": "RMSE", "value": "2.41"},
        {"metric": "MAPE", "value": "2.1%"},
        {"metric": "Directional accuracy", "value": "76%"},
        {"metric": "Last trained", "value": (today - timedelta(days=2)).isoformat()},
        {"metric": "Training rows", "value": "105"},
        {"metric": "Test rows", "value": "10"},
    ]
    return {"performance_data": rows, "performance_tracker": tracker}


# ---------------------------------------------------------------------------
# Pages — templates/*.html, served through Flask's template loader
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/<page>.html")
def page(page):
    return render_template(f"{page}.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/sectors")
def api_sectors():
    SECTORS_LIST=[]
    predict_obj=Predict()
    sectors_path='feature_engineering/stocks_sectors'
    for sector in os.listdir(sectors_path):
        sector_prediction=predict_obj.predict_sector_returns_and_movement(
            sector=sector,
            forecast_step=1
        )
        SECTORS_LIST.append({"sector": sector, "predicted_return": sector_prediction['sector_returns'], "accuracy": sector_prediction['sector_accuracy']})
    return jsonify(SECTORS_LIST)


@app.route("/api/sectors/<sector>/stocks")
def api_sector_stocks(sector):

    STOCKS_BY_SECTOR_LIST=[]
    predict_obj=Predict()
    # working_stocks_dir = 'each_stock_model_notebook' ## wont use this because some of the files were skipped to be revisited later
    sector_path=f'feature_engineering/stocks_sectors/{sector}'
    all_stocks_info_path=f'stock_data/All_Stocks_Info'


    # if os.path.exists(working_stocks_dir):
    #     working_stocks = [f.split('_')[0] for f in os.listdir(working_stocks_dir)]

    # if not working_stocks:
    #     raise ValueError(f"No working stocks found in {working_stocks_dir} — check the path.")
    
    ## we will use this working stock for now
    working_stock_df = pd.read_csv('model_parameters/current_model_parameters.csv')
    working_stocks = working_stock_df['stock'].tolist()

    for stocks in os.listdir(sector_path):
        stock=stocks.split("_")[0]

        if stock == 'INFINITY' or stock not in working_stocks:
            continue

        try:
            df = pd.read_csv('model_parameters/current_model_parameters.csv')
            target = df.loc[df['stock'] == stock, 'target'].iloc[0]
        except Exception as e:
            print(f"Target error occured with {stock} stock")

        try:
            all_stock_df = pd.read_csv(all_stocks_info_path)
            stock_name = all_stock_df.loc[all_stock_df['symbol'] == stock, 'name'].iloc[0]  
        except Exception as e:
            print(f"Stock Name error occured with {stock} stock")
        
        stock_prediction=predict_obj.predict_stock_returns_and_movement(
            target_name=target,
            stock=stock,
            forecast_step=1
        )
        
        STOCKS_BY_SECTOR_LIST.append(
            {"symbol": stock, "name": stock_name, "predicted_return": stock_prediction['returns'],
             "accuracy": stock_prediction['returns_accuracy'], "movement": stock_prediction['movement'], "movement_accuracy": stock_prediction['movement_accuracy']}
        )

    return jsonify(STOCKS_BY_SECTOR_LIST)


@app.route("/api/stocks")
def api_stock_list():
    return jsonify(STOCK_LIST)


@app.route("/api/performance/<symbol>")
def api_performance(symbol):
    return jsonify(sample_performance(symbol))


@app.route("/api/train", methods=["POST"])
def api_train():
    payload = request.get_json(silent=True) or {}
    symbol = payload.get("symbol", "unknown stock")
    return jsonify({"ok": True, "message": f"(demo) Training request received for {symbol}."})


@app.route("/api/train_all", methods=["POST"])
def api_train_all():
    return jsonify({"ok": True, "message": "(demo) Training request received for all stocks."})


if __name__ == "__main__":
    app.run(debug=True)