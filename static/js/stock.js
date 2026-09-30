(function () {
  const params = new URLSearchParams(window.location.search);
  const symbol = params.get("symbol") || "";
  const sectorParam = params.get("sector") || "";

  const crumbLink = document.getElementById("sector-crumb-link");
  crumbLink.textContent = sectorParam || "Sector";
  crumbLink.href = sectorParam
    ? `/stocks.html?sector=${encodeURIComponent(sectorParam)}`
    : "/user.html";
  document.getElementById("symbol-crumb").textContent = symbol || "Stock";

  function pct(n) {
    const sign = n > 0 ? "+" : "";
    return `${sign}${(n * 100).toFixed(1)}%`;
  }

  function labelsFor(valueType) {
    return valueType === "returns"
      ? {
          noun: "returns",
          axisTitle: "Return",
          legendActual: "Actual returns (past 10 months)",
          legendForecast: "Predicted returns (ahead)",
          hover: "%{y:.2f}",
        }
      : {
          noun: "price",
          axisTitle: "Price (₦)",
          legendActual: "Actual price (past 10 months)",
          legendForecast: "Predicted price (ahead)",
          hover: "₦%{y:.2f}",
        };
  }

  function renderStats(data) {
    const labels = labelsFor(data.value_type);
    document.getElementById("stock-title").textContent =
      `${data.symbol} — ${data.name || ""}`;
    document.getElementById("stock-subtitle").textContent =
      `${data.sector || sectorParam || "Sector"} · past 10 months of actual ${labels.noun} alongside the model's predicted ${labels.noun} ahead.`;
    document.getElementById("legend-actual-label").textContent =
      labels.legendActual;
    document.getElementById("legend-forecast-label").textContent =
      labels.legendForecast;

    const returnEl = document.getElementById("stat-return");
    returnEl.textContent = pct(data.predicted_return);
    returnEl.className =
      "value " + (data.predicted_return >= 0 ? "pos" : "neg");

    document.getElementById("stat-accuracy").textContent =
      `${Math.round(data.accuracy * 100)}%`;

    const moveEl = document.getElementById("stat-movement");
    moveEl.textContent = data.movement === "up" ? "Up" : "Down";
    moveEl.className = "value " + data.movement;

    document.getElementById("stat-movement-accuracy").textContent =
      `${Math.round(data.movement_accuracy * 100)}%`;
  }

  function renderChart(data) {
    const chartEl = document.getElementById("trend-chart");
    const history = data.history || [];
    const forecast = data.forecast || [];
    const labels = labelsFor(data.value_type);

    if (!history.length && !forecast.length) {
      chartEl.innerHTML = `<div class="state-note" style="border:none; padding:0.5rem 0;"><strong>No trend data yet</strong> Train this stock to see its price history and forecast here.</div>`;
      return;
    }
    if (typeof Plotly === "undefined") {
      chartEl.innerHTML = `<div class="state-note" style="border:none; padding:0.5rem 0;"><strong>Chart library didn't load</strong> This page loads Plotly from cdn.plot.ly — check that this device/container has internet access to that domain, then reload.</div>`;
      console.error(
        "[stock.js] Plotly is undefined — the CDN script tag in stock.html didn't load.",
      );
      return;
    }

    chartEl.innerHTML = "";

    // Bridge the two traces so the predicted line visually continues from
    // the last actual price instead of starting with a gap.
    const bridgePoint = history.length ? [history[history.length - 1]] : [];
    const forecastTrace = bridgePoint.concat(forecast);

    const traces = [
      {
        x: history.map((r) => r.date),
        y: history.map((r) => r.price ?? r.return) /* made changes here */,
        name: `Actual ${labels.noun}`,
        mode: "lines",
        line: { color: "#0E5E3D", width: 2.2 },
        hovertemplate: `%{x}<br>${labels.hover}<extra>Actual</extra>`,
      },
      {
        x: forecastTrace.map((r) => r.date),
        y: forecastTrace.map(
          (r) => r.price ?? r.return,
        ) /* made changes here */,
        name: `Predicted ${labels.noun}`,
        mode: "lines",
        line: { color: "#B9862F", width: 2.2, dash: "dot" },
        hovertemplate: `%{x}<br>${labels.hover}<extra>Predicted</extra>`,
      },
    ];

    const shapes = [];
    if (history.length) {
      shapes.push({
        type: "line",
        x0: history[history.length - 1].date,
        x1: history[history.length - 1].date,
        y0: 0,
        y1: 1,
        yref: "paper",
        line: { color: "#C4CDBB", width: 1, dash: "dash" },
      });
    }

    const layout = {
      margin: { t: 20, r: 20, b: 40, l: 55 },
      height: 420,
      font: { family: "IBM Plex Sans, sans-serif", size: 12, color: "#37453D" },
      legend: { orientation: "h", y: -0.18 },
      xaxis: { gridcolor: "#EDF0E8", title: { text: "" } },
      yaxis: { gridcolor: "#EDF0E8", title: { text: labels.axisTitle } },
      shapes,
      paper_bgcolor: "#FFFFFF",
      plot_bgcolor: "#FFFFFF",
      hovermode: "x unified",
    };

    Plotly.newPlot(chartEl, traces, layout, {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
      displaylogo: false,
    });
  }

  if (!symbol) {
    document.getElementById("trend-chart").innerHTML =
      `<div class="state-note" style="border:none; padding:0.5rem 0;"><strong>No stock selected</strong> Go back and pick a stock from a sector.</div>`;
  } else {
    NGX.getStockTrend(symbol)
      .then((data) => {
        renderStats(data);
        renderChart(data);
      })
      .catch((err) => {
        console.error("[stock.js] failed to render trend for", symbol, err);
        document.getElementById("trend-chart").innerHTML =
          `<div class="state-note" style="border:none; padding:0.5rem 0;"><strong>Couldn't load this stock's data</strong> ${err.message || "Check the browser console for details."}</div>`;
      });
  }
})();
