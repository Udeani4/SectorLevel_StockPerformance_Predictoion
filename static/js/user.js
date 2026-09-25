(function () {
  const container = document.getElementById("sector-rows");
  let sectors = [];
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
    if (!sectors.length) {
      container.innerHTML = `<div class="state-note"><strong>No sectors yet</strong> Once the pipeline has trained models, sectors will appear here.</div>`;
      return;
    }

    const rows = [...sectors];
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
        return `
        <a class="row-item" href="/stocks.html?sector=${encodeURIComponent(s.sector)}">
          <div class="row-name">
            <span class="primary">${s.sector}</span>
            <span class="secondary">View stocks in this sector</span>
          </div>
          <span class="pct ${returnClass}">${s.predicted_return.toFixed(1)}%</span>
          <div class="meter">
            <span class="meter-track"><span class="meter-fill" style="--fill:${accPct}%"></span></span>
            <span class="meter-label">${accPct}%</span>
          </div>
          <span></span>
          <span class="chev">›</span>
        </a>`;
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

  NGX.getSectors().then((data) => {
    sectors = data;
    render();
  });
})();
