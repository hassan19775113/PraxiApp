(() => {
  const chartsJson = document.getElementById("scheduling-charts-json");
  const heatmapJson = document.getElementById("scheduling-heatmap-json");
  const funnelJson = document.getElementById("scheduling-funnel-json");
  if (!chartsJson || !heatmapJson || !funnelJson) {
    return;
  }

  const parseJson = (raw, fallback) => {
    if (!raw) return fallback;
    try {
      return JSON.parse(raw);
    } catch (err) {
      return fallback;
    }
  };

  const chartsData = parseJson(chartsJson.textContent, {});
  const heatmapMatrix = parseJson(heatmapJson.textContent, []);
  const funnelData = parseJson(funnelJson.textContent, {});

  const clearPlaceholder = (container) => {
    container?.querySelectorAll(".prx-chart-placeholder").forEach((el) => el.remove());
  };

  const renderMessage = (canvasId, message) => {
    const el = document.getElementById(canvasId);
    const container = el?.parentElement;
    if (container) {
      clearPlaceholder(container);
      container.innerHTML = `<p class="text-muted text-sm prx-text-center">${message}</p>`;
    }
  };

  const renderChart = (canvasId, config) => {
    if (!window.Chart || !config?.data) {
      renderMessage(canvasId, "Chartdaten fehlen");
      return;
    }
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      return;
    }
    clearPlaceholder(canvas.parentElement);
    new Chart(canvas, config);
  };

  if (chartsData.completion_rate_trend?.datasets) {
    chartsData.completion_rate_trend.datasets.forEach((ds, i) => {
      ds.borderColor = PRX_COLORS.palette[i];
      ds.backgroundColor = PRX_COLORS.paletteLight[i];
      ds.fill = true;
    });
  }

  if (chartsData.lead_time_distribution?.datasets?.[0]) {
    chartsData.lead_time_distribution.datasets[0].backgroundColor = PRX_COLORS.primary;
  }

  if (chartsData.hourly_load?.datasets?.[0]) {
    chartsData.hourly_load.datasets[0].backgroundColor = PRX_COLORS.primary;
  }

  if (chartsData.weekday_load?.datasets?.[0]) {
    chartsData.weekday_load.datasets[0].backgroundColor = PRX_COLORS.palette;
  }

  renderChart("trendChart", {
    type: "line",
    data: chartsData.completion_rate_trend,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 12, padding: 16 } },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: (v) => `${v}%` },
          grid: { color: PRX_COLORS.neutralLight },
        },
        x: { grid: { display: false } },
      },
    },
  });

  renderChart("leadTimeChart", {
    type: "bar",
    data: chartsData.lead_time_distribution,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: PRX_COLORS.neutralLight } },
        x: { grid: { display: false } },
      },
    },
  });

  renderChart("hourlyChart", {
    type: "bar",
    data: chartsData.hourly_load,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: PRX_COLORS.neutralLight } },
        x: { grid: { display: false } },
      },
    },
  });

  renderChart("weekdayChart", {
    type: "bar",
    data: chartsData.weekday_load,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: PRX_COLORS.neutralLight } },
        x: { grid: { display: false } },
      },
    },
  });

  const funnelContainer = document.getElementById("funnelContainer");
  const maxFunnel = funnelData.total || 1;
  const funnelColors = [
    PRX_COLORS.primary,
    PRX_COLORS.secondary,
    PRX_COLORS.success,
    PRX_COLORS.neutralMedium,
  ];

  if (Array.isArray(funnelData.funnel)) {
    clearPlaceholder(funnelContainer);
    funnelData.funnel.forEach((stage, idx) => {
      const width = Math.max(30, (stage.count / maxFunnel) * 100);
      const rate =
        idx > 0
          ? Math.round((stage.count / funnelData.funnel[idx - 1].count) * 100)
          : 100;
      const color = funnelColors[idx] || PRX_COLORS.neutralMedium;

      funnelContainer.innerHTML += `
        <div style="display: flex; align-items: center; gap: var(--spacing-3);">
          <span class="text-sm font-medium" style="width: 100px;">${stage.stage}</span>
          <div style="flex: 1; height: 32px; background: var(--color-neutral-100); border-radius: var(--radius-lg); overflow: hidden; position: relative;">
            <div style="width: ${width}%; height: 100%; background: ${color}; display: flex; align-items: center; justify-content: space-between; padding: 0 var(--spacing-3); color: white; font-size: var(--font-size-sm); font-weight: 600;">
              <span>${stage.count}</span>
              <span>${rate}%</span>
            </div>
          </div>
        </div>
      `;
    });
  } else if (funnelContainer) {
    clearPlaceholder(funnelContainer);
    funnelContainer.innerHTML = '<p class="text-muted text-sm prx-text-center">Funnel-Daten fehlen</p>';
  }

  const days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
  const heatmapBody = document.getElementById("heatmapBody");
  const hasHeatmap = Array.isArray(heatmapMatrix) && heatmapMatrix.length >= 7;
  const maxVal = hasHeatmap ? Math.max(...heatmapMatrix.flat()) || 1 : 1;

  if (!hasHeatmap && heatmapBody) {
    clearPlaceholder(heatmapBody);
    const row = document.createElement("tr");
    row.innerHTML =
      '<td class="text-muted text-sm prx-text-center" colspan="14">Heatmap-Daten fehlen</td>';
    heatmapBody.appendChild(row);
  }

  if (hasHeatmap) {
    clearPlaceholder(heatmapBody);
    days.forEach((day, dayIdx) => {
      const row = document.createElement("tr");
      row.innerHTML = `<td class="font-semibold">${day}</td>`;

      for (let hour = 7; hour <= 19; hour++) {
        const count = heatmapMatrix[dayIdx][hour] || 0;
        const intensity = count / maxVal;

        let color;
        if (count === 0) {
          color = "var(--color-neutral-200)";
        } else if (intensity >= 0.9) {
          color = "var(--color-danger-500)";
        } else if (intensity >= 0.6) {
          color = "rgba(47, 111, 171, 0.9)";
        } else if (intensity >= 0.3) {
          color = "rgba(47, 111, 171, 0.6)";
        } else {
          color = "rgba(47, 111, 171, 0.3)";
        }

        row.innerHTML += `
          <td class="prx-text-center">
            <div style="
              width: 28px;
              height: 28px;
              border-radius: var(--radius-md);
              background: ${color};
              display: inline-flex;
              align-items: center;
              justify-content: center;
              font-size: var(--font-size-xs);
              font-weight: 500;
              color: ${count > 0 ? "white" : "var(--text-muted)"};
            " title="${day} ${hour}:00 - ${count} Termine">
              ${count > 0 ? count : ""}
            </div>
          </td>
        `;
      }

      heatmapBody.appendChild(row);
    });
  }
})();
