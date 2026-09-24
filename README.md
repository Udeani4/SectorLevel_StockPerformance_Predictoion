# NGX Predictions — front-end

Plain HTML/CSS/JS, no build step. Pages fetch JSON from your Flask API and
fall back to built-in mock data if an endpoint isn't ready yet, so every
page is clickable right now.

## Files

```
index.html         landing page — User / Developer
user.html           sector list (predicted return, accuracy)
stocks.html         stocks within a sector (?sector=Banking)
developer.html      train a stock / train all / performance tabs
static/css/style.css
static/js/api.js        all fetch() calls + mock-data fallbacks — READ THIS FIRST
static/js/user.js       renders + sorts the sector list
static/js/stocks.js     renders + sorts the stock list
static/js/developer.js  tabs, both train forms, performance tables
```

## Wiring into Flask

Simplest setup — serve these as static files and let the JS hit a JSON API:

```python
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__, static_folder="static")

@app.route("/")
@app.route("/<page>.html")
def pages(page="index"):
    return send_from_directory(".", f"{page}.html")

@app.route("/api/sectors")
def sectors():
    return jsonify([
        {"sector": "Banking", "predicted_return": 0.048, "accuracy": 0.81},
        ...
    ])

@app.route("/api/sectors/<sector>/stocks")
def sector_stocks(sector):
    return jsonify([
        {"symbol": "ZENITHBANK", "name": "Zenith Bank Plc",
         "predicted_return": 0.052, "accuracy": 0.83,
         "movement": "up", "movement_accuracy": 0.88},
        ...
    ])

@app.route("/api/stocks")
def stock_list():
    return jsonify([{"symbol": "ZENITHBANK", "name": "Zenith Bank Plc"}, ...])

@app.route("/api/performance/<symbol>")
def performance(symbol):
    return jsonify({
        "performance_data": [
            {"date": "2026-09-01", "actual": 31.2, "predicted": 31.6, "error": 1.28},
            ...
        ],
        "performance_tracker": [
            {"metric": "MAE", "value": "1.84"},
            {"metric": "Last trained", "value": "2026-09-22"},
            ...
        ],
    })

@app.route("/api/train", methods=["POST"])
def train():
    payload = request.get_json()  # symbol, start_date, end_date,
                                    # forecast_horizon, order_p, order_d, order_q
    # kick off your pipeline here
    return jsonify({"ok": True, "message": f"Training started for {payload['symbol']}."})

@app.route("/api/train_all", methods=["POST"])
def train_all():
    # kick off your pipeline for every stock
    return jsonify({"ok": True, "message": "Training started for all stocks."})
```

## Notes

- All field names in the mock data (`predicted_return`, `accuracy`, `movement`,
  `movement_accuracy`, `performance_data`, `performance_tracker`, etc.) match
  exactly what you asked for — keep your API responses to the same shape and
  nothing else needs to change.
- `movement` is expected as the string `"up"` or `"down"`.
- The "Train a stock" form posts: `symbol`, `start_date`, `end_date`,
  `forecast_horizon`, `order_p`, `order_d`, `order_q` (SARIMA order). Add or
  remove fields in `developer.html` to match what your trainer actually needs.
- Once a real endpoint responds, the matching mock data in `api.js` is simply
  never used — no other file needs to change.
