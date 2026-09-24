(function () {
  /* ---------------- tabs ---------------- */
  const tabs = document.querySelectorAll(".tab");
  const sections = document.querySelectorAll(".panel-section");

  function activateTab(name) {
    tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    sections.forEach((s) => s.classList.toggle("active", s.id === `tab-${name}`));
    if (name === "performance" && !symbolsLoaded) loadSymbols();
  }

  tabs.forEach((t) => t.addEventListener("click", () => activateTab(t.dataset.tab)));

  const initialTab = window.location.hash.replace("#", "");
  if (["train", "train-all", "performance"].includes(initialTab)) activateTab(initialTab);

  /* ---------------- train a stock ---------------- */
  const trainForm = document.getElementById("train-form");
  const trainStatus = document.getElementById("train-status");
  const trainSubmit = document.getElementById("train-submit");

  trainForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(trainForm).entries());

    trainSubmit.disabled = true;
    trainSubmit.textContent = "Training…";
    trainStatus.className = "status-line show pending";
    trainStatus.textContent = `Training ${payload.symbol}…`;

    try {
      const res = await NGX.trainStock(payload);
      trainStatus.className = `status-line show ${res.ok ? "ok" : "pending"}`;
      trainStatus.textContent = res.message || "Done.";
    } finally {
      trainSubmit.disabled = false;
      trainSubmit.textContent = "Train stock";
    }
  });

  /* ---------------- train all stocks ---------------- */
  const trainAllBtn = document.getElementById("train-all-btn");
  const trainAllStatus = document.getElementById("train-all-status");
  const trainAllLog = document.getElementById("train-all-log");

  trainAllBtn.addEventListener("click", async () => {
    trainAllBtn.disabled = true;
    trainAllBtn.textContent = "Training all stocks…";
    trainAllStatus.className = "status-line show pending";
    trainAllStatus.textContent = "Running the pipeline across all tracked stocks…";
    trainAllLog.className = "log show";
    trainAllLog.textContent = "Starting training run…\n";

    try {
      const res = await NGX.trainAll();
      trainAllLog.textContent += `${res.message || "Training run finished."}\n`;
      trainAllStatus.className = `status-line show ${res.ok ? "ok" : "pending"}`;
      trainAllStatus.textContent = res.ok ? "Training complete." : "Training finished with issues.";
    } finally {
      trainAllBtn.disabled = false;
      trainAllBtn.textContent = "Train all stocks";
    }
  });

  /* ---------------- performance ---------------- */
  const symbolGrid = document.getElementById("symbol-grid");
  const resultsEl = document.getElementById("performance-results");
  let symbolsLoaded = false;

  async function loadSymbols() {
    symbolsLoaded = true;
    const stocks = await NGX.getStockList();
    if (!stocks.length) {
      symbolGrid.innerHTML = `<div class="state-note" style="border:none; padding:0.5rem 0;"><strong>No stocks trained yet</strong> Train a stock first to see its performance here.</div>`;
      return;
    }
    symbolGrid.innerHTML = stocks
      .map((s) => `<button class="symbol-chip" data-symbol="${s.symbol}">${s.symbol}</button>`)
      .join("");

    symbolGrid.querySelectorAll(".symbol-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        symbolGrid.querySelectorAll(".symbol-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        showPerformance(chip.dataset.symbol);
      });
    });
  }

  async function showPerformance(symbol) {
    resultsEl.innerHTML = `<div class="state-note"><strong>Loading performance for ${symbol}…</strong></div>`;
    const data = await NGX.getPerformance(symbol);

    const dataRows = (data.performance_data || [])
      .map(
        (r) => `<tr>
          <td>${r.date}</td>
          <td>${r.actual}</td>
          <td>${r.predicted}</td>
          <td>${r.error > 0 ? "+" : ""}${r.error}%</td>
        </tr>`
      )
      .join("");

    const trackerRows = (data.performance_tracker || [])
      .map((r) => `<tr><td>${r.metric}</td><td>${r.value}</td></tr>`)
      .join("");

    resultsEl.innerHTML = `
      <div class="table-wrap">
        <table class="data">
          <caption>${symbol} — performance data</caption>
          <thead><tr><th>Date</th><th>Actual</th><th>Predicted</th><th>Error</th></tr></thead>
          <tbody>${dataRows || `<tr><td colspan="4">No performance data yet.</td></tr>`}</tbody>
        </table>
      </div>
      <div class="table-wrap">
        <table class="data">
          <caption>${symbol} — performance tracker</caption>
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>${trackerRows || `<tr><td colspan="2">No tracker data yet.</td></tr>`}</tbody>
        </table>
      </div>
    `;
  }
})();
