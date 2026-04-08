const ui = window.NUTRITION_UI || {};
const initialDashboard = window.NUTRITION_DASHBOARD || null;

const resultNode = document.getElementById("result");
const apiKeyNode = document.getElementById("api-key");

const storedKey = window.localStorage.getItem("nutrition-api-key");
if (storedKey && apiKeyNode) {
  apiKeyNode.value = storedKey;
}

apiKeyNode?.addEventListener("change", () => {
  window.localStorage.setItem("nutrition-api-key", apiKeyNode.value.trim());
});

function headers() {
  const apiKey = apiKeyNode?.value?.trim();
  const base = {};
  if (apiKey) {
    base["X-API-Key"] = apiKey;
  }
  return base;
}

function setResult(value) {
  if (!resultNode) return;
  resultNode.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return Number(value).toLocaleString("ru-RU", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, value));
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}

function setMeter(id, ratio) {
  const node = document.getElementById(id);
  if (node) {
    node.style.width = `${clampPercent(ratio * 100)}%`;
  }
}

function renderList(id, items) {
  const node = document.getElementById(id);
  if (!node) return;
  if (!items || items.length === 0) {
    node.innerHTML = "<li>Пока нет данных.</li>";
    return;
  }
  node.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderRecentEvents(events) {
  const node = document.getElementById("recent-events");
  if (!node) return;
  if (!events || events.length === 0) {
    node.innerHTML = "<li><strong>Пока нет записей</strong><span>Как только вы добавите данные, журнал появится здесь.</span></li>";
    return;
  }
  node.innerHTML = events
    .map(
      (event) => `
        <li>
          <strong>${escapeHtml(event.title)}</strong>
          <span>${escapeHtml(event.summary)}</span>
          <time>${escapeHtml(event.logged_at)}</time>
        </li>
      `,
    )
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function chartEmpty(container, message) {
  container.innerHTML = `<div class="chart-empty">${escapeHtml(message)}</div>`;
}

function svgShell(width, height, inner) {
  return `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img">
      ${inner}
    </svg>
  `;
}

function renderLineChart(container, values, labels, color, target = null) {
  if (!container) return;
  const width = 640;
  const height = 260;
  const left = 36;
  const right = 16;
  const top = 14;
  const bottom = 32;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const numeric = values.filter((value) => value !== null && value !== undefined);
  if (numeric.length === 0) {
    chartEmpty(container, "Недостаточно данных для графика.");
    return;
  }

  const minValue = Math.min(...numeric, target ?? numeric[0]);
  const maxValue = Math.max(...numeric, target ?? numeric[0]);
  const padding = Math.max(1, (maxValue - minValue) * 0.15);
  const yMin = minValue - padding;
  const yMax = maxValue + padding;

  const xForIndex = (index) => left + (chartWidth * index) / Math.max(1, values.length - 1);
  const yForValue = (value) => top + ((yMax - value) / Math.max(1, yMax - yMin)) * chartHeight;

  let grids = "";
  for (let step = 0; step < 4; step += 1) {
    const y = top + (chartHeight * step) / 3;
    grids += `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />`;
  }

  if (target !== null && target !== undefined) {
    const y = yForValue(target);
    grids += `<line class="chart-target" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />`;
  }

  const pointList = values
    .map((value, index) => (value === null || value === undefined ? null : `${xForIndex(index)},${yForValue(value)}`))
    .filter(Boolean);
  const polyline = `<polyline class="chart-series" stroke="${color}" points="${pointList.join(" ")}" />`;
  const points = values
    .map((value, index) => {
      if (value === null || value === undefined) {
        return "";
      }
      return `<circle class="chart-point" cx="${xForIndex(index)}" cy="${yForValue(value)}" r="4" fill="${color}" />`;
    })
    .join("");

  const labelIndexes = Array.from(new Set([0, Math.floor(labels.length / 2), labels.length - 1])).filter((index) => index >= 0);
  const labelNodes = labelIndexes
    .map((index) => `<text class="chart-label" x="${xForIndex(index)}" y="${height - 10}" text-anchor="middle">${labels[index]}</text>`)
    .join("");

  container.innerHTML = svgShell(width, height, `${grids}${polyline}${points}${labelNodes}`);
}

function renderBarChart(container, values, labels, colorClass, target = null) {
  if (!container) return;
  const width = 640;
  const height = 260;
  const left = 36;
  const right = 16;
  const top = 14;
  const bottom = 32;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const maxValue = Math.max(...values, target ?? 0, 1);

  if (values.length === 0) {
    chartEmpty(container, "Пока нет данных для графика.");
    return;
  }

  const barWidth = Math.max(10, chartWidth / Math.max(values.length * 1.5, 8));
  const gap = values.length > 1 ? (chartWidth - values.length * barWidth) / (values.length - 1) : 0;

  let inner = "";
  for (let step = 0; step < 4; step += 1) {
    const y = top + (chartHeight * step) / 3;
    inner += `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />`;
  }

  if (target !== null && target !== undefined) {
    const y = top + ((maxValue - target) / maxValue) * chartHeight;
    inner += `<line class="chart-target" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />`;
  }

  values.forEach((value, index) => {
    const x = left + index * (barWidth + gap);
    const barHeight = (Math.max(0, value) / maxValue) * chartHeight;
    const y = top + chartHeight - barHeight;
    inner += `<rect class="bar ${colorClass}" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" />`;
  });

  const labelIndexes = Array.from(new Set([0, Math.floor(labels.length / 2), labels.length - 1])).filter((index) => index >= 0);
  labelIndexes.forEach((index) => {
    const x = left + index * (barWidth + gap) + barWidth / 2;
    inner += `<text class="chart-label" x="${x}" y="${height - 10}" text-anchor="middle">${labels[index]}</text>`;
  });

  container.innerHTML = svgShell(width, height, inner);
}

function renderDualBarChart(container, primaryValues, secondaryValues, labels) {
  if (!container) return;
  const width = 640;
  const height = 260;
  const left = 36;
  const right = 16;
  const top = 14;
  const bottom = 32;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const maxValue = Math.max(...primaryValues, ...secondaryValues, 1);
  const groupWidth = chartWidth / Math.max(primaryValues.length, 1);
  const barWidth = Math.max(8, groupWidth * 0.28);

  let inner = "";
  for (let step = 0; step < 4; step += 1) {
    const y = top + (chartHeight * step) / 3;
    inner += `<line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" />`;
  }

  primaryValues.forEach((value, index) => {
    const baseX = left + index * groupWidth + groupWidth / 2 - barWidth - 3;
    const primaryHeight = (Math.max(0, value) / maxValue) * chartHeight;
    const secondaryHeight = (Math.max(0, secondaryValues[index]) / maxValue) * chartHeight;
    inner += `<rect class="bar bar--activity" x="${baseX}" y="${top + chartHeight - primaryHeight}" width="${barWidth}" height="${primaryHeight}" />`;
    inner += `<rect class="bar bar--protein" x="${baseX + barWidth + 6}" y="${top + chartHeight - secondaryHeight}" width="${barWidth}" height="${secondaryHeight}" />`;
  });

  const labelIndexes = Array.from(new Set([0, Math.floor(labels.length / 2), labels.length - 1])).filter((index) => index >= 0);
  labelIndexes.forEach((index) => {
    const x = left + index * groupWidth + groupWidth / 2;
    inner += `<text class="chart-label" x="${x}" y="${height - 10}" text-anchor="middle">${labels[index]}</text>`;
  });

  container.innerHTML = svgShell(width, height, inner);
}

function renderWeeklyList(items) {
  const node = document.getElementById("weekly-list");
  if (!node) return;
  if (!items || items.length === 0) {
    node.innerHTML = `<article class="weekly-item"><strong>Пока нет недельных данных</strong><small>Сводка появится после нескольких дней записей.</small></article>`;
    return;
  }
  node.innerHTML = items
    .map(
      (item) => `
        <article class="weekly-item">
          <strong>${escapeHtml(item.week_start)}</strong>
          <span>${formatNumber(item.average_food_calories)} ккал в среднем, белок ${formatNumber(item.average_protein_g, 1)} г</span>
          <small>${escapeHtml(item.coach_note)}</small>
        </article>
      `,
    )
    .join("");
}

function renderStatsTable(history) {
  const body = document.getElementById("stats-table-body");
  if (!body) return;
  body.innerHTML = history
    .map(
      (row) => `
        <tr>
          <td>${escapeHtml(row.date)}</td>
          <td>${row.weight_kg === null ? "—" : formatNumber(row.weight_kg, 1)}</td>
          <td>${formatNumber(row.net_calories)}</td>
          <td>${formatNumber(row.protein_g, 1)}</td>
          <td>${formatNumber(row.fat_g, 1)}</td>
          <td>${formatNumber(row.carbs_g, 1)}</td>
          <td>${formatNumber(row.workouts_count)}</td>
          <td>${formatNumber(row.meals_count)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderTodaySummary(summary) {
  if (!summary) return;
  setText("kpi-food-calories", formatNumber(summary.food.calories));
  setText("kpi-calories-left", formatNumber(summary.remaining.calories));
  setText("kpi-protein", `${formatNumber(summary.food.protein_g, 1)} г`);
  setText("kpi-weight", summary.weight_kg === null ? "—" : formatNumber(summary.weight_kg, 1));

  setText("macro-calories-caption", `${formatNumber(summary.net_calories)} / ${formatNumber(summary.targets.calories)}`);
  setText("macro-protein-caption", `${formatNumber(summary.food.protein_g, 1)} / ${formatNumber(summary.targets.protein_g, 1)} г`);
  setText("macro-fat-caption", `${formatNumber(summary.food.fat_g, 1)} / ${formatNumber(summary.targets.fat_g, 1)} г`);
  setText("macro-carbs-caption", `${formatNumber(summary.food.carbs_g, 1)} / ${formatNumber(summary.targets.carbs_g, 1)} г`);

  setMeter("meter-calories", summary.targets.calories ? summary.net_calories / summary.targets.calories : 0);
  setMeter("meter-protein", summary.targets.protein_g ? summary.food.protein_g / summary.targets.protein_g : 0);
  setMeter("meter-fat", summary.targets.fat_g ? summary.food.fat_g / summary.targets.fat_g : 0);
  setMeter("meter-carbs", summary.targets.carbs_g ? summary.food.carbs_g / summary.targets.carbs_g : 0);
}

function renderHomeDashboard(data) {
  if (!data) return;
  renderTodaySummary(data.today);
  renderList("today-focus-list", data.today?.suggestions || []);
  setText("home-average-calories", formatNumber(data.highlights?.average_net_calories || 0));
  setText("home-average-protein", `${formatNumber(data.highlights?.average_protein_g || 0, 1)} г`);
  setText("home-workouts", formatNumber(data.highlights?.workout_sessions || 0));

  const history = data.history || [];
  const labels = history.map((item) => item.label);
  renderBarChart(
    document.getElementById("home-calorie-chart"),
    history.map((item) => item.net_calories),
    labels,
    "bar--food",
    data.today?.targets?.calories,
  );
}

function renderStatsDashboard(data) {
  if (!data) return;
  const history = data.history || [];
  const labels = history.map((item) => item.label);
  setText("stats-average-calories", formatNumber(data.highlights?.average_net_calories || 0));
  setText("stats-average-protein", formatNumber(data.highlights?.average_protein_g || 0, 1));
  setText(
    "stats-weight-change",
    data.highlights?.weight_change_kg === null || data.highlights?.weight_change_kg === undefined
      ? "—"
      : formatNumber(data.highlights.weight_change_kg, 1),
  );
  setText("stats-workouts", formatNumber(data.highlights?.workout_sessions || 0));

  renderList("stats-focus-list", data.focus || []);
  renderWeeklyList(data.weekly || []);
  renderStatsTable(history);

  renderBarChart(
    document.getElementById("stats-calories-chart"),
    history.map((item) => item.net_calories),
    labels,
    "bar--food",
    data.today?.targets?.calories,
  );
  renderBarChart(
    document.getElementById("stats-protein-chart"),
    history.map((item) => item.protein_g),
    labels,
    "bar--protein",
    data.today?.targets?.protein_g,
  );
  renderLineChart(
    document.getElementById("stats-weight-chart"),
    history.map((item) => item.weight_kg),
    labels,
    "#3e6f8c",
  );
  renderDualBarChart(
    document.getElementById("stats-activity-chart"),
    history.map((item) => item.meals_count),
    history.map((item) => item.workouts_count),
    labels,
  );
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.detail || `HTTP ${response.status}`);
  }
  return payload;
}

async function refreshHomePage() {
  const [dashboard, recentEvents] = await Promise.all([
    fetchJson(`${ui.statsUrl}?days=14`),
    fetchJson(ui.recentEventsUrl),
  ]);
  renderHomeDashboard(dashboard);
  renderRecentEvents(recentEvents);
}

async function refreshStatsPage(days) {
  const dashboard = await fetchJson(`${ui.statsUrl}?days=${days}`);
  renderStatsDashboard(dashboard);
}

async function submitJson(formId, url, bodyBuilder) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = bodyBuilder(new FormData(form));
    setResult("Сохраняю...");
    try {
      const payload = await fetchJson(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers(),
        },
        body: JSON.stringify(body),
      });
      setResult(payload);
      form.reset();
      if (ui.activePage === "home") {
        await refreshHomePage();
      }
    } catch (error) {
      setResult(String(error));
    }
  });
}

const mealForm = document.getElementById("meal-form");
mealForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  setResult("Анализирую фото...");
  try {
    const response = await fetch("/api/meals/photo", {
      method: "POST",
      headers: headers(),
      body: new FormData(mealForm),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload?.detail || `HTTP ${response.status}`);
    }
    setResult(payload);
    mealForm.reset();
    if (ui.activePage === "home") {
      await refreshHomePage();
    }
  } catch (error) {
    setResult(String(error));
  }
});

submitJson("weight-form", "/api/weights", (formData) => ({
  weight_kg: Number(formData.get("weight_kg")),
  note: formData.get("note") || null,
}));

submitJson("workout-form", "/api/workouts", (formData) => ({
  description: formData.get("description"),
  duration_min: formData.get("duration_min") ? Number(formData.get("duration_min")) : null,
  calories_burned: Number(formData.get("calories_burned")),
  avg_hr: formData.get("avg_hr") ? Number(formData.get("avg_hr")) : null,
  note: formData.get("note") || null,
}));

document.querySelectorAll("[data-range]").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll("[data-range]").forEach((node) => node.classList.remove("is-active"));
    button.classList.add("is-active");
    try {
      await refreshStatsPage(Number(button.dataset.range));
    } catch (error) {
      setResult(String(error));
    }
  });
});

if (ui.activePage === "home" && initialDashboard) {
  renderHomeDashboard(initialDashboard);
}

if (ui.activePage === "stats" && initialDashboard) {
  renderStatsDashboard(initialDashboard);
}
