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
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ca=certifi.where()

mongodb_uri=os.getenv("MONGO_DB_CLUSTER_URL")
client = pymongo.MongoClient(mongodb_uri,tlsCAFile=ca)

database=client[DATA_INGESTION_DATABASE_NAME]
collection=database[DATA_INGESTION_COLLECTION_NAME]


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
            f"actual": actual,
            f"predicted": predicted,
            "error": error,
        })

    latest = performance_tracker_df.sort_values(['year', 'month_predicted']).iloc[-1]
    tracker = [
        {"metric": "R² score", "value": f"{latest['r2_score']:.3f}"},
        {"metric": "RMSE", "value": f"{latest['rmse']:.3f}"},
        {"metric": "Movement accuracy", "value": f"{latest['movement_accuracy'] * 100:.0f}%"},
        {"metric": f"Next month's {target} prediction", "value": f"{latest[f'next_month_{target}_prediction']:.2f}"},
        {"metric": "Forecast month", "value": f"{int(latest['year'])}-{int(latest['month_predicted']):02d}"},
        {"metric": "SARIMA order", "value": latest['order']},
        {"metric": "Seasonal order", "value": latest['seasonal_order']},
    ]

    return {"performance_data": rows, "performance_tracker": tracker}



def get_stock_sector_name(stock: str):
    try:
        for sector in os.listdir('feature_engineering/stocks_sectors'):
            sector_path = f'feature_engineering/stocks_sectors/{sector}'
            for filename in os.listdir(sector_path):
                if filename.split('_')[0] == stock:
                    return sector
        return None  # stock not found in any sector
    except Exception as e:
        raise NGXStockPredictionException(e, sys)

def find_stock(symbol: str):
    """Look up a stock's metadata (and the sector it belongs to) by symbol."""
    try:
        stock_sector = get_stock_sector_name(stock=symbol)

        params_df = pd.read_csv("model_parameters/current_model_parameters.csv")
        target = params_df.loc[params_df["stock"] == symbol, "target"].iloc[0]

        all_stock_df = pd.read_csv("stock_data/All_Stocks_Info")
        stock_name = all_stock_df.loc[all_stock_df["symbol"] == symbol, "name"].iloc[0]

        performance_data = pd.read_csv(f"Artifacts/{symbol}/performance_tracker/{target}/performance_data.csv")
        performance_tracker = pd.read_csv(f"Artifacts/{symbol}/performance_tracker/{target}/performance_tracker.csv")

        # performance_data / performance_tracker are already scoped to this one
        # stock by the folder path — there's no "stock" column to filter on.
        next_month_pred = performance_tracker[f"next_month_{target}_prediction"].iloc[-1]
        pred_accuracy = performance_tracker["r2_score"].iloc[-1]
        movement_accuracy = performance_tracker["movement_accuracy"].iloc[-1]

        if target == "close_price":
            current_value = performance_data["true"].iloc[-1]
            predicted_return = (next_month_pred - current_value) / current_value  # fraction, not a percent
            movement = "up" if predicted_return > 0 else "down"
        else:
            predicted_return = next_month_pred/100 ## just to align with the JS backend stock.js
            movement = "up" if next_month_pred > 0 else "down"

        return {
            "symbol": symbol,
            "name": stock_name,
            "sector": stock_sector,
            "predicted_return": float(predicted_return),   # cast off numpy types for jsonify
            "accuracy": float(pred_accuracy),
            "movement": movement,
            "movement_accuracy": float(movement_accuracy),
        }

    except Exception as e:
        print(f"[find_stock] couldn't build metadata for {symbol}: {e}")
        return None


def sample_trend(symbol: str):
    meta = find_stock(symbol) or {
        "symbol": symbol, "name": symbol, "sector": "", "predicted_return": 0,
        "accuracy": 0, "movement": "up", "movement_accuracy": 0,
    }

    history = []
    target = None
    try:
        params_df = pd.read_csv("model_parameters/current_model_parameters.csv")
        target = params_df.loc[params_df["stock"] == symbol, "target"].iloc[0]

        performance_data = pd.read_csv(
            f"Artifacts/{symbol}/performance_tracker/{target}/performance_data.csv"
        )
        stock_rows = performance_data.copy()
        stock_rows["date"] = pd.to_datetime(
            stock_rows["year"].astype(str) + "-" + stock_rows["month"].astype(str) + "-01"
        )
        stock_rows = stock_rows.sort_values("date").tail(10)

        history = [
            {"date": row["date"].date().isoformat(), "price": round(float(row["true"]), 2)}
            for _, row in stock_rows.iterrows()
        ] if target=="close_price" else [
            {"date": row["date"].date().isoformat(), "return": round(float(row["true"]), 2)}
            for _, row in stock_rows.iterrows()
        ] ## made change here
    except Exception as e:
        print(f"[sample_trend] couldn't load history for {symbol}: {e}")

    forecast = []
    if history:
        try:
            last_price = history[-1]["price"] if target=="close_price" else history[-1]["return"] ## made change here
            last_date = date.fromisoformat(history[-1]["date"])
            next_price = round(last_price * (1 + meta["predicted_return"]), 2) if target=="close_price" else meta["predicted_return"]*100 ## to account for the former division. This is just to align with the JS. We will make the appropriate adjustments in due time
            next_date = last_date + relativedelta(months=1)
            forecast = [{"date": next_date.isoformat(), "price": next_price}] if target=="close_price" else [{"date": next_date.isoformat(), "return": next_price}]
        except Exception as e:
            print(f"[sample_trend] couldn't build forecast for {symbol}: {e}")

    if target == "close_price":
        value_type = "price"
    elif target:
        value_type = "returns"
    else:
        value_type = "unknown"  # target lookup itself failed — see note below

    return {**meta, "history": history, "forecast": forecast, "value_type": value_type}
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
    

@app.route("/api/stocks/<symbol>/trend")
def api_stock_trend(symbol):
    trend = sample_trend(symbol)  # let it crash with the real traceback
    print(trend)
    return jsonify(trend)
    



if __name__ == "__main__":
    app.run(debug=True)