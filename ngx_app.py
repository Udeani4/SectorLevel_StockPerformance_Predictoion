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
from NgxStockPrediction.exception.exception import NGXStockPredictionException
from NgxStockPrediction.logging.logger import logging
from NgxStockPrediction.pipeline.training_pipeline import TrainingPipeline
# from NgxStockPrediction.utils.main_utils.utils import load_object
from NgxStockPrediction.pipeline.batch_prediction import Predict
from NgxStockPrediction.pipeline.create_all_stock_model import CreateAllStockModel

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




# def sample_performance(symbol: str):
#     base = 100 + (ord(symbol[0]) % 20)
#     rows = []
#     today = date.today()
#     for i in range(9, -1, -1):
#         d = today - timedelta(days=i * 7)
#         actual = round(base + random.uniform(-3, 3) + i * 0.6, 2)
#         predicted = round(actual + random.uniform(-2, 2), 2)
#         error = round((predicted - actual) / actual * 100, 2)
#         rows.append({"date": d.isoformat(), "actual": actual, "predicted": predicted, "error": error})

#     tracker = [
#         {"metric": "MAE", "value": "1.84"},
#         {"metric": "RMSE", "value": "2.41"},
#         {"metric": "MAPE", "value": "2.1%"},
#         {"metric": "Directional accuracy", "value": "76%"},
#         {"metric": "Last trained", "value": (today - timedelta(days=2)).isoformat()},
#         {"metric": "Training rows", "value": "105"},
#         {"metric": "Test rows", "value": "10"},
#     ]
#     return {"performance_data": rows, "performance_tracker": tracker}

def sample_performance(symbol: str):
    try:
        df = pd.read_csv('model_parameters/current_model_parameters.csv')
        target = df.loc[df['stock'] == symbol, 'target'].iloc[0]
    except Exception as e:
        print(f"Target error occured with {symbol} stock")
        return {"performance_data": [], "performance_tracker": []}

    performance_data_path = f'Artifacts/{symbol.upper()}/performance_tracker/{target}/performance_data.csv'
    performance_tracker_path = f'Artifacts/{symbol.upper()}/performance_tracker/{target}/performance_tracker.csv'

    performance_data_df = pd.read_csv(performance_data_path)
    performance_tracker_df = pd.read_csv(performance_tracker_path)

    rows = []
    for _, row in performance_data_df.iterrows():
        actual = row['true']
        predicted = row['predicted']
        error = round((predicted - actual) / actual * 100, 2) if actual != 0 else None
        rows.append({
            "date": f"{int(row['year'])}-{int(row['month']):02d}",  # e.g. "2025-10"
            "actual": actual,
            "predicted": predicted,
            "error": error,
        })

    latest = performance_tracker_df.sort_values(['year', 'month_predicted']).iloc[-1]
    tracker = [
        {"metric": "R² score", "value": f"{latest['r2_score']:.3f}"},
        {"metric": "RMSE", "value": f"{latest['rmse']:.3f}"},
        {"metric": "Movement accuracy", "value": f"{latest['movement_accuracy'] * 100:.0f}%"},
        {"metric": "Next month prediction", "value": f"{latest['next_month_close_price_prediction']:.2f}"},
        {"metric": "Forecast month", "value": f"{int(latest['year'])}-{int(latest['month_predicted']):02d}"},
        {"metric": "SARIMA order", "value": latest['order']},
        {"metric": "Seasonal order", "value": latest['seasonal_order']},
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
    try:
        STOCK_LIST = []

        working_stock_df = pd.read_csv('model_parameters/current_model_parameters.csv')
        working_stocks = working_stock_df['stock'].tolist()

        all_stock_df = pd.read_csv('stock_data/All_Stocks_Info')

        for stock in working_stocks:
            stock_name = all_stock_df.loc[all_stock_df['symbol'] == stock, 'name'].iloc[0]
            STOCK_LIST.append({'symbol':stock,'name':stock_name})

        return jsonify(STOCK_LIST)
    except Exception as e:
        raise NGXStockPredictionException(e,sys)


@app.route("/api/performance/<symbol>")
def api_performance(symbol):
    return jsonify(sample_performance(symbol))


@app.route("/api/train", methods=["POST"])
def api_train():
    try:
        payload = request.get_json(silent=True) or {}
        symbol = payload.get("symbol")
        target = payload.get("target")

        if not symbol or not target:
            return jsonify({"ok": False, "message": "Stock symbol and target are required."}), 400

        symbol = symbol.upper()
        target = target.lower()

        if not symbol:
            return jsonify({"ok": False, "message": "Stock symbol is required."}), 400

        order = (
            int(payload.get("order_p", 1)),
            int(payload.get("order_d", 1)),
            int(payload.get("order_q", 1)),
        )
        seasonal_order = (
            int(payload.get("order_P", 1)),
            int(payload.get("order_D", 1)),
            int(payload.get("order_Q", 1)),
            int(payload.get("order_s", 12)),
        )

        try:
            train_pipeline = TrainingPipeline(
                file_name=symbol,
                target_name=target,
                model_type="sarima",
                order=order,
                seasonal_order=seasonal_order,
                forecast_step=int(payload.get("forecast_horizon", 1)),
            )

            artifact = train_pipeline.run_pipeline()

            return jsonify({
                "ok": True,
                "message": f"Training complete for {symbol}. R²: {artifact.test_metric_artifact.r2_score:.3f}. RMSE: {artifact.test_metric_artifact.rmse:.3f}"
            })
        except Exception as e:
            return jsonify({"ok": False, "message": f"Training failed for {symbol}: {str(e)}"}), 500
    except Exception as e:
        raise NGXStockPredictionException(e,sys)
    

@app.route("/api/train_all", methods=["POST"])
def api_train_all():
    try:
        train_all_stock_obj = CreateAllStockModel()
        train_all_stock_obj.create_all_models()

        return jsonify({
            "ok": True,
            "message": f"Training complete. {len(train_all_stock_obj.problem_stocks)} stock(s) failed."
                       if train_all_stock_obj.problem_stocks
                       else "Training complete for all stocks."
        })
    except Exception as e:
        return jsonify({"ok": False, "message": f"Training all stocks failed: {str(e)}"}), 500
    


if __name__ == "__main__":
    app.run(debug=True)