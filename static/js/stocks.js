(function () {
  const params = new URLSearchParams(window.location.search);
  const sector = params.get("sector") || "";
  document.getElementById("sector-crumb").textContent =
    sector || "Unknown sector";
  document.getElementById("sector-title").textContent = sector || "Stocks";

  const container = document.getElementById("stock-rows");
  let stocks = [];
  let sortKey = null;
  let sortDir = 1;

  function pct(n) {
    const sign = n > 0 ? "+" : "";
    return `${sign}${(n * 100).toFixed(1)}%`;
  }

  function movementIcon(dir) {
    return dir === "up"
      ? `<svg viewBox="0 0 12 12" fill="none"><path d="M6 10V2M2 5.5L6 1.5L10 5.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`
      : `<svg viewBox="0 0 12 12" fill="none"><path d="M6 2V10M2 6.5L6 10.5L10 6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  function render() {
    if (!stocks.length) {
      container.innerHTML = `<div class="state-note"><strong>No stocks in this sector yet</strong> Once models are trained for this sector, stocks will appear here.</div>`;
      return;
    }

    const rows = [...stocks];
    if (sortKey) {
      rows.sort(
        (a, b) =>
          (a[sortKey] > b[sortKey] ? 1 : a[sortKey] < b[sortKey] ? -1 : 0) *
          sortDir,
      );
    }

    container.innerHTML = rows
      .map((s) => {
        const returnClass = s.predicted_return >= 0 ? "pos" : "neg";
        const accPct = Math.round(s.accuracy * 100);
        const moveAccPct = Math.round(s.movement_accuracy * 100);
        return `
        <div class="row-item stocks">
          <div class="row-name">
            <span class="primary">${s.symbol}</span>
            <span class="secondary">${s.name || ""}</span>
          </div>
          <span class="pct ${returnClass}">${s.predicted_return.toFixed(1)}%</span>
          <div class="meter">
            <span class="meter-track"><span class="meter-fill" style="--fill:${accPct}%"></span></span>
            <span class="meter-label">${accPct}%</span>
          </div>
          <span class="move ${s.movement}">${movementIcon(s.movement)} ${s.movement === "up" ? "Up" : "Down"}</span>
          <div class="meter">
            <span class="meter-track"><span class="meter-fill" style="--fill:${moveAccPct}%"></span></span>
            <span class="meter-label">${moveAccPct}%</span>
          </div>
        </div>`;
      })
      .join("");
  }

  document.querySelectorAll("[data-sortable]").forEach((el) => {
    el.addEventListener("click", () => {
      const key = el.getAttribute("data-sortable");
      sortDir = sortKey === key ? sortDir * -1 : 1;
      sortKey = key;
      render();
    });
  });

  NGX.getStocksForSector(sector).then((data) => {
    stocks = data;
    render();
  });
})();
