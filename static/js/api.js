/* ===================================================================
   NGX Predictions — API client
   ---------------------------------------------------------------
   Every function below tries a real fetch() against the Flask API
   first. If the endpoint isn't there yet (or errors), it falls back
   to mock data so the UI is fully clickable while the backend is
   built. Once your route exists, the fetch just starts working and
   the mock silently stops being used — nothing else to change.

   EXPECTED ENDPOINTS (adjust paths here if yours differ):
     GET  /api/sectors
          -> [{ sector, predicted_return, accuracy }]
     GET  /api/sectors/<sector>/stocks
          -> [{ symbol, name, predicted_return, accuracy,
                movement: "up"|"down", movement_accuracy }]
     POST /api/train                body: { symbol, ...params }
          -> { ok, message }
     POST /api/train_all
          -> { ok, message }
     GET  /api/stocks                (symbol list for Performance tab)
          -> [{ symbol, name }]
     GET  /api/performance/<symbol>
          -> { performance_data: [ {date, actual, predicted, error} ],
               performance_tracker: [ {metric, value} ] }
   =================================================================== */

const NGX = (() => {
  const MOCK_SECTORS = [
    { sector: "Banking", predicted_return: 0.048, accuracy: 0.81 },
    { sector: "Consumer Goods", predicted_return: 0.021, accuracy: 0.74 },
    { sector: "Oil & Gas", predicted_return: -0.014, accuracy: 0.69 },
    { sector: "Industrial Goods", predicted_return: 0.033, accuracy: 0.77 },
    { sector: "Insurance", predicted_return: 0.012, accuracy: 0.63 },
    { sector: "Agriculture", predicted_return: -0.006, accuracy: 0.58 },
  ];

  const MOCK_STOCKS = {
    "Banking": [
      { symbol: "ZENITHBANK", name: "Zenith Bank Plc", predicted_return: 0.052, accuracy: 0.83, movement: "up", movement_accuracy: 0.88 },
      { symbol: "GTCO", name: "Guaranty Trust Holding Co.", predicted_return: 0.041, accuracy: 0.80, movement: "up", movement_accuracy: 0.79 },
      { symbol: "UBA", name: "United Bank for Africa", predicted_return: 0.037, accuracy: 0.76, movement: "up", movement_accuracy: 0.74 },
      { symbol: "ACCESSCORP", name: "Access Holdings Plc", predicted_return: 0.028, accuracy: 0.72, movement: "down", movement_accuracy: 0.61 },
      { symbol: "FBNH", name: "FBN Holdings Plc", predicted_return: -0.011, accuracy: 0.65, movement: "down", movement_accuracy: 0.69 },
    ],
    "Consumer Goods": [
      { symbol: "NESTLE", name: "Nestle Nigeria Plc", predicted_return: 0.031, accuracy: 0.78, movement: "up", movement_accuracy: 0.75 },
      { symbol: "BUAFOODS", name: "BUA Foods Plc", predicted_return: 0.024, accuracy: 0.71, movement: "up", movement_accuracy: 0.70 },
      { symbol: "NB", name: "Nigerian Breweries Plc", predicted_return: -0.009, accuracy: 0.66, movement: "down", movement_accuracy: 0.64 },
    ],
    "Oil & Gas": [
      { symbol: "SEPLAT", name: "Seplat Energy Plc", predicted_return: -0.018, accuracy: 0.70, movement: "down", movement_accuracy: 0.72 },
      { symbol: "OANDO", name: "Oando Plc", predicted_return: -0.009, accuracy: 0.62, movement: "down", movement_accuracy: 0.58 },
    ],
    "Industrial Goods": [
      { symbol: "DANGCEM", name: "Dangote Cement Plc", predicted_return: 0.036, accuracy: 0.79, movement: "up", movement_accuracy: 0.81 },
      { symbol: "BUACEMENT", name: "BUA Cement Plc", predicted_return: 0.029, accuracy: 0.74, movement: "up", movement_accuracy: 0.70 },
    ],
    "Insurance": [
      { symbol: "AIICO", name: "AIICO Insurance Plc", predicted_return: 0.014, accuracy: 0.60, movement: "up", movement_accuracy: 0.55 },
      { symbol: "NEM", name: "NEM Insurance Plc", predicted_return: 0.009, accuracy: 0.64, movement: "up", movement_accuracy: 0.59 },
    ],
    "Agriculture": [
      { symbol: "OKOMUOIL", name: "Okomu Oil Palm Plc", predicted_return: -0.004, accuracy: 0.59, movement: "down", movement_accuracy: 0.53 },
      { symbol: "PRESCO", name: "Presco Plc", predicted_return: -0.008, accuracy: 0.57, movement: "down", movement_accuracy: 0.55 },
    ],
  };

  const MOCK_STOCK_LIST = Object.values(MOCK_STOCKS).flat().map(s => ({ symbol: s.symbol, name: s.name }));

  function mockPerformance(symbol) {
    const base = 100 + (symbol.charCodeAt(0) % 20);
    const rows = [];
    for (let i = 9; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i * 7);
      const actual = +(base + Math.sin(i) * 4 + i * 0.6).toFixed(2);
      const predicted = +(actual + (Math.random() - 0.5) * 3).toFixed(2);
      const error = +(((predicted - actual) / actual) * 100).toFixed(2);
      rows.push({ date: d.toISOString().slice(0, 10), actual, predicted, error });
    }
    return {
      performance_data: rows,
      performance_tracker: [
        { metric: "MAE", value: "1.84" },
        { metric: "RMSE", value: "2.41" },
        { metric: "MAPE", value: "2.1%" },
        { metric: "Directional accuracy", value: "76%" },
        { metric: "Last trained", value: new Date(Date.now() - 86400000 * 2).toISOString().slice(0, 10) },
        { metric: "Training rows", value: "105" },
        { metric: "Test rows", value: "10" },
      ],
    };
  }

  async function getJSON(url, fallback) {
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`[NGX] ${url} unavailable, using mock data (${err.message})`);
      return fallback;
    }
  }

  async function postJSON(url, body, fallback) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`[NGX] ${url} unavailable, using mock response (${err.message})`);
      return fallback;
    }
  }

  return {
    getSectors: () => getJSON("/api/sectors", MOCK_SECTORS),

    getStocksForSector: (sector) =>
      getJSON(`/api/sectors/${encodeURIComponent(sector)}/stocks`, MOCK_STOCKS[sector] || []),

    getStockList: () => getJSON("/api/stocks", MOCK_STOCK_LIST),

    getPerformance: (symbol) =>
      getJSON(`/api/performance/${encodeURIComponent(symbol)}`, mockPerformance(symbol)),

    trainStock: (payload) =>
      postJSON("/api/train", payload, {
        ok: true,
        message: `(demo) Training request queued for ${payload.symbol}. Wire up /api/train to run it for real.`,
      }),

    trainAll: () =>
      postJSON("/api/train_all", {}, {
        ok: true,
        message: "(demo) Training request queued for all stocks. Wire up /api/train_all to run it for real.",
      }),

    allSectorNames: () => Object.keys(MOCK_STOCKS),
  };
})();
