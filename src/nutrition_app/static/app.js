const ui = window.NUTRITION_UI || {};
const initialDashboard = window.NUTRITION_DASHBOARD || null;

const resultNode = document.getElementById("result");
const apiKeyNode = document.getElementById("api-key");

const translations = {
  ru: {
    "nav.home": "Главная",
    "nav.stats": "Статистика",
    "actions.downloadExcel": "Скачать Excel",
    "actions.openStats": "Открыть статистику",
    "actions.openSchema": "Открыть schema для GPT Actions",
    "actions.saveWeight": "Сохранить вес",
    "actions.saveWorkout": "Сохранить тренировку",
    "home.eyebrow": "Еда, вес, тренировки и сводка в одном месте",
    "home.title": "Дневной контроль выглядит как дашборд, а не как технический лог",
    "home.lede":
      "Фото еды можно отправлять через Custom GPT, а здесь сразу видеть, сколько уже съедено, сколько осталось до лимита, где проседает белок и как идет неделя.",
    "home.focusTitle": "Что улучшить сегодня",
    "home.focusCaption": "Фокус на питание",
    "home.trendTitle": "Динамика за 14 дней",
    "home.trendCaption": "Быстрый взгляд",
    "home.quickActions": "Быстрые действия",
    "home.quickActionsCaption": "Обновляет дашборд сразу после сохранения",
    "home.photoViaGptTitle": "Фото еды идут через Custom GPT.",
    "home.photoViaGptBody":
      "Загружайте фото в свой GPT, а этот сайт используйте как центр статистики, веса, тренировок и Excel-экспорта.",
    "home.recentTitle": "Последние записи",
    "home.recentCaption": "живой журнал",
    "home.apiResponse": "Ответ API",
    "home.apiKeyRequired": "нужен API key",
    "home.openAccess": "доступ без ключа",
    "kpi.foodCalories": "Калории сегодня",
    "kpi.foodLeft": "До лимита по еде",
    "kpi.protein": "Белок",
    "kpi.weight": "Вес",
    "kpi.weightNote": "последняя запись",
    "macro.calories": "Калории",
    "macro.protein": "Белок",
    "macro.fat": "Жиры",
    "macro.carbs": "Углеводы",
    "stats.eyebrow": "Статистика по дням",
    "stats.title": "Здесь видно не только сегодня, но и темп всей системы",
    "stats.lede":
      "Вес, калории, белок, тренировки и недельные заметки собраны в одном месте. Меняйте период и смотрите, что происходит по дням, а не по ощущениям.",
    "stats.avgCalories": "Средние калории",
    "stats.avgCaloriesNote": "чистыми в день",
    "stats.avgProtein": "Средний белок",
    "stats.gramsPerDay": "г в день",
    "stats.weightChange": "Изменение веса",
    "stats.forPeriod": "за период",
    "stats.workouts": "Тренировки",
    "stats.focusTitle": "Фокус по питанию",
    "stats.focusCaption": "что реально влияет на результат",
    "stats.weeklyTitle": "Недельные итоги",
    "stats.weeklyCaption": "по неделям",
    "stats.caloriesChartTitle": "Калории по дням",
    "stats.caloriesChartCaption": "чистые калории vs цель",
    "stats.proteinChartTitle": "Белок по дням",
    "stats.proteinChartCaption": "факт vs цель",
    "stats.weightChartTitle": "Вес",
    "stats.weightChartCaption": "линия тренда",
    "stats.activityChartTitle": "Активность",
    "stats.activityChartCaption": "тренировки и приемы пищи",
    "stats.tableTitle": "Все по дням",
    "stats.tableCaption": "таблица для быстрой проверки",
    "table.date": "Дата",
    "table.weight": "Вес",
    "table.kcal": "Ккал",
    "table.protein": "Белок",
    "table.fat": "Жиры",
    "table.carbs": "Углеводы",
    "table.workouts": "Тренировки",
    "table.meals": "Приемы пищи",
    "forms.weightTitle": "Вес",
    "forms.quickEntry": "быстрый ввод",
    "forms.weightLabel": "Вес, кг",
    "forms.comment": "Комментарий",
    "forms.workoutTitle": "Тренировка",
    "forms.workoutCaption": "кардио или зал",
    "forms.description": "Описание",
    "forms.minutes": "Минуты",
    "forms.kcal": "Ккал",
    "forms.heartRate": "Пульс",
    "placeholders.weightNote": "Например: утром после сна",
    "placeholders.workoutDescription": "Прогулка, силовая, велотренажер",
    "placeholders.workoutNote": "Например: вечерняя сессия",
    "placeholders.apiKey": "Только если включен NUTRITION_API_KEY",
    "result.ready": "Готово к работе.",
    "result.saving": "Сохраняю...",
    "result.analyzing": "Анализирую фото...",
    "empty.data": "Пока нет данных.",
    "empty.eventsTitle": "Пока нет записей",
    "empty.eventsBody": "Как только вы добавите данные, журнал появится здесь.",
    "empty.chart": "Недостаточно данных для графика.",
    "empty.weeklyTitle": "Пока нет недельных данных",
    "empty.weeklyBody": "Сводка появится после нескольких дней записей.",
    "macro.caloriesFootnote": "Чистые калории с учетом тренировок.",
    "macro.proteinFootnote": "Главный маркер сытости и сохранения мышц.",
    "macro.fatFootnote": "Смотри, чтобы план не уезжал за счет калорийно плотной еды.",
    "macro.carbsFootnote": "Проверяй, чтобы они не обгоняли белок слишком рано.",
    "kpi.ofTarget": "из {target}",
    "kpi.foodLeftNote": "ккал без учета тренировок",
    "kpi.netLeftNote": "С учетом тренировок: {value} ккал",
    "kpi.netLeftNoWorkout": "Тренировочного бонуса сегодня пока нет",
    "kpi.proteinTarget": "цель {target} г",
    "stats.weeklyRow": "{calories} ккал в среднем, белок {protein} г",
  },
  en: {
    "nav.home": "Home",
    "nav.stats": "Statistics",
    "actions.downloadExcel": "Download Excel",
    "actions.openStats": "Open statistics",
    "actions.openSchema": "Open GPT Actions schema",
    "actions.saveWeight": "Save weight",
    "actions.saveWorkout": "Save workout",
    "home.eyebrow": "Food, weight, workouts, and summary in one place",
    "home.title": "Daily control should feel like a dashboard, not a raw technical log",
    "home.lede":
      "Send meal photos through Custom GPT, then use this dashboard to see calories eaten, food budget left, protein gaps, and weekly momentum.",
    "home.focusTitle": "Today's focus",
    "home.focusCaption": "Diet-focused guidance",
    "home.trendTitle": "14-day trend",
    "home.trendCaption": "Quick view",
    "home.quickActions": "Quick actions",
    "home.quickActionsCaption": "Refreshes the dashboard right after saving",
    "home.photoViaGptTitle": "Meal photos go through Custom GPT.",
    "home.photoViaGptBody":
      "Upload photos in your GPT, and use this site as the hub for statistics, weight, workouts, and Excel export.",
    "home.recentTitle": "Recent entries",
    "home.recentCaption": "live journal",
    "home.apiResponse": "API response",
    "home.apiKeyRequired": "API key required",
    "home.openAccess": "open access",
    "kpi.foodCalories": "Calories eaten",
    "kpi.foodLeft": "Food budget left",
    "kpi.protein": "Protein",
    "kpi.weight": "Weight",
    "kpi.weightNote": "latest entry",
    "macro.calories": "Calories",
    "macro.protein": "Protein",
    "macro.fat": "Fat",
    "macro.carbs": "Carbs",
    "stats.eyebrow": "Daily statistics",
    "stats.title": "This page shows more than today: it shows the pace of the whole system",
    "stats.lede":
      "Weight, calories, protein, workouts, and weekly notes are all in one place. Switch the period and read the trend day by day instead of guessing.",
    "stats.avgCalories": "Average calories",
    "stats.avgCaloriesNote": "net per day",
    "stats.avgProtein": "Average protein",
    "stats.gramsPerDay": "g per day",
    "stats.weightChange": "Weight change",
    "stats.forPeriod": "for the period",
    "stats.workouts": "Workouts",
    "stats.focusTitle": "Nutrition focus",
    "stats.focusCaption": "what really affects the result",
    "stats.weeklyTitle": "Weekly recap",
    "stats.weeklyCaption": "by week",
    "stats.caloriesChartTitle": "Calories by day",
    "stats.caloriesChartCaption": "net calories vs target",
    "stats.proteinChartTitle": "Protein by day",
    "stats.proteinChartCaption": "actual vs target",
    "stats.weightChartTitle": "Weight",
    "stats.weightChartCaption": "trend line",
    "stats.activityChartTitle": "Activity",
    "stats.activityChartCaption": "workouts and meals",
    "stats.tableTitle": "All days",
    "stats.tableCaption": "table for quick review",
    "table.date": "Date",
    "table.weight": "Weight",
    "table.kcal": "Kcal",
    "table.protein": "Protein",
    "table.fat": "Fat",
    "table.carbs": "Carbs",
    "table.workouts": "Workouts",
    "table.meals": "Meals",
    "forms.weightTitle": "Weight",
    "forms.quickEntry": "quick entry",
    "forms.weightLabel": "Weight, kg",
    "forms.comment": "Comment",
    "forms.workoutTitle": "Workout",
    "forms.workoutCaption": "cardio or gym",
    "forms.description": "Description",
    "forms.minutes": "Minutes",
    "forms.kcal": "Kcal",
    "forms.heartRate": "Heart rate",
    "placeholders.weightNote": "For example: morning after sleep",
    "placeholders.workoutDescription": "Walk, lifting, bike trainer",
    "placeholders.workoutNote": "For example: evening session",
    "placeholders.apiKey": "Only if NUTRITION_API_KEY is enabled",
    "result.ready": "Ready.",
    "result.saving": "Saving...",
    "result.analyzing": "Analyzing photo...",
    "empty.data": "No data yet.",
    "empty.eventsTitle": "No entries yet",
    "empty.eventsBody": "As soon as you add data, the journal will appear here.",
    "empty.chart": "Not enough data for a chart yet.",
    "empty.weeklyTitle": "No weekly data yet",
    "empty.weeklyBody": "The weekly summary will appear after a few logged days.",
    "macro.caloriesFootnote": "Net calories after subtracting workout burn.",
    "macro.proteinFootnote": "The main marker for satiety and muscle retention.",
    "macro.fatFootnote": "Watch that the plan does not drift because of calorie-dense foods.",
    "macro.carbsFootnote": "Make sure carbs do not outrun protein too early.",
    "kpi.ofTarget": "of {target}",
    "kpi.foodLeftNote": "kcal before workout credit",
    "kpi.netLeftNote": "With workouts: {value} kcal left",
    "kpi.netLeftNoWorkout": "No workout credit yet today",
    "kpi.proteinTarget": "target {target} g",
    "stats.weeklyRow": "{calories} kcal average, protein {protein} g",
  },
};

function detectInitialLang() {
  const saved = window.localStorage.getItem("nutrition-ui-lang");
  if (saved === "ru" || saved === "en") return saved;
  return ui.initialLang === "en" ? "en" : "ru";
}

let currentLang = detectInitialLang();

const storedKey = window.localStorage.getItem("nutrition-api-key");
if (storedKey && apiKeyNode) {
  apiKeyNode.value = storedKey;
}

apiKeyNode?.addEventListener("change", () => {
  window.localStorage.setItem("nutrition-api-key", apiKeyNode.value.trim());
});

function t(key, vars = {}) {
  const table = translations[currentLang] || translations.ru;
  let value = table[key] || translations.ru[key] || key;
  Object.entries(vars).forEach(([name, item]) => {
    value = value.replaceAll(`{${name}}`, item);
  });
  return value;
}

function localeCode() {
  return currentLang === "en" ? "en-US" : "ru-RU";
}

function withLang(url) {
  const target = new URL(url, window.location.origin);
  target.searchParams.set("lang", currentLang);
  return `${target.pathname}${target.search}${target.hash}`;
}

function updateInternalLinks() {
  document.querySelectorAll("a[href='/' ], a[href='/stats']").forEach((link) => {
    const path = link.getAttribute("href");
    link.setAttribute("href", withLang(path));
  });
}

function setActiveLangChip() {
  document.querySelectorAll("[data-set-lang]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.setLang === currentLang);
  });
}

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
  return Number(value).toLocaleString(localeCode(), {
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function applyTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder));
  });
  if (resultNode && (resultNode.textContent.trim() === "" || resultNode.textContent.trim() === translations.ru["result.ready"] || resultNode.textContent.trim() === translations.en["result.ready"])) {
    setResult(t("result.ready"));
  }
  setActiveLangChip();
  updateInternalLinks();
  document.title = ui.activePage === "stats" ? `Nutrition App | ${t("nav.stats")}` : `Nutrition App | ${t("nav.home")}`;
}

function renderList(id, items) {
  const node = document.getElementById(id);
  if (!node) return;
  if (!items || items.length === 0) {
    node.innerHTML = `<li>${escapeHtml(t("empty.data"))}</li>`;
    return;
  }
  node.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderRecentEvents(events) {
  const node = document.getElementById("recent-events");
  if (!node) return;
  if (!events || events.length === 0) {
    node.innerHTML = `<li><strong>${escapeHtml(t("empty.eventsTitle"))}</strong><span>${escapeHtml(t("empty.eventsBody"))}</span></li>`;
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

function chartEmpty(container, message) {
  container.innerHTML = `<div class="chart-empty">${escapeHtml(message)}</div>`;
}

function svgShell(width, height, inner) {
  return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img">${inner}</svg>`;
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
    chartEmpty(container, t("empty.chart"));
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
      if (value === null || value === undefined) return "";
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
    chartEmpty(container, t("empty.chart"));
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
    node.innerHTML = `<article class="weekly-item"><strong>${escapeHtml(t("empty.weeklyTitle"))}</strong><small>${escapeHtml(t("empty.weeklyBody"))}</small></article>`;
    return;
  }
  node.innerHTML = items
    .map(
      (item) => `
        <article class="weekly-item">
          <strong>${escapeHtml(item.week_start)}</strong>
          <span>${escapeHtml(t("stats.weeklyRow", { calories: formatNumber(item.average_food_calories), protein: formatNumber(item.average_protein_g, 1) }))}</span>
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
  setText("kpi-food-calories-note", t("kpi.ofTarget", { target: formatNumber(summary.targets.calories) }));
  setText("kpi-food-left", formatNumber(summary.food_budget_left));
  setText("kpi-food-left-note", t("kpi.foodLeftNote"));
  setText(
    "kpi-net-left-note",
    summary.exercise_calories > 0
      ? t("kpi.netLeftNote", { value: formatNumber(summary.net_budget_left) })
      : t("kpi.netLeftNoWorkout"),
  );
  setText("kpi-protein", `${formatNumber(summary.food.protein_g, 1)} g`);
  setText("kpi-protein-note", t("kpi.proteinTarget", { target: formatNumber(summary.targets.protein_g, 1) }));
  setText("kpi-weight", summary.weight_kg === null ? "—" : formatNumber(summary.weight_kg, 1));

  setText("macro-calories-caption", `${formatNumber(summary.net_calories)} / ${formatNumber(summary.targets.calories)}`);
  setText("macro-protein-caption", `${formatNumber(summary.food.protein_g, 1)} / ${formatNumber(summary.targets.protein_g, 1)} g`);
  setText("macro-fat-caption", `${formatNumber(summary.food.fat_g, 1)} / ${formatNumber(summary.targets.fat_g, 1)} g`);
  setText("macro-carbs-caption", `${formatNumber(summary.food.carbs_g, 1)} / ${formatNumber(summary.targets.carbs_g, 1)} g`);
  setText("macro-calories-footnote", t("macro.caloriesFootnote"));
  setText("macro-protein-footnote", t("macro.proteinFootnote"));
  setText("macro-fat-footnote", t("macro.fatFootnote"));
  setText("macro-carbs-footnote", t("macro.carbsFootnote"));

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
  setText("home-average-protein", `${formatNumber(data.highlights?.average_protein_g || 0, 1)} g`);
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

  renderBarChart(document.getElementById("stats-calories-chart"), history.map((item) => item.net_calories), labels, "bar--food", data.today?.targets?.calories);
  renderBarChart(document.getElementById("stats-protein-chart"), history.map((item) => item.protein_g), labels, "bar--protein", data.today?.targets?.protein_g);
  renderLineChart(document.getElementById("stats-weight-chart"), history.map((item) => item.weight_kg), labels, "#3e6f8c");
  renderDualBarChart(document.getElementById("stats-activity-chart"), history.map((item) => item.meals_count), history.map((item) => item.workouts_count), labels);
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
    fetchJson(withLang(`${ui.statsUrl}?days=14`)),
    fetchJson(ui.recentEventsUrl),
  ]);
  renderHomeDashboard(dashboard);
  renderRecentEvents(recentEvents);
}

async function refreshStatsPage(days) {
  const dashboard = await fetchJson(withLang(`${ui.statsUrl}?days=${days}`));
  renderStatsDashboard(dashboard);
}

async function refreshCurrentPage() {
  if (ui.activePage === "stats") {
    const activeRange = document.querySelector("[data-range].is-active");
    await refreshStatsPage(Number(activeRange?.dataset.range || 30));
    return;
  }
  await refreshHomePage();
}

async function submitJson(formId, url, bodyBuilder) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = bodyBuilder(new FormData(form));
    setResult(t("result.saving"));
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
  setResult(t("result.analyzing"));
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

document.querySelectorAll("[data-set-lang]").forEach((button) => {
  button.addEventListener("click", async () => {
    const nextLang = button.dataset.setLang;
    if (!nextLang || nextLang === currentLang) return;
    currentLang = nextLang;
    window.localStorage.setItem("nutrition-ui-lang", currentLang);
    applyTranslations();
    try {
      await refreshCurrentPage();
      window.history.replaceState({}, "", withLang(window.location.pathname + window.location.search));
    } catch (error) {
      setResult(String(error));
    }
  });
});

applyTranslations();

if (ui.activePage === "home" && initialDashboard) {
  renderHomeDashboard(initialDashboard);
  refreshHomePage().catch((error) => setResult(String(error)));
}

if (ui.activePage === "stats" && initialDashboard) {
  renderStatsDashboard(initialDashboard);
  refreshStatsPage(Number(document.querySelector("[data-range].is-active")?.dataset.range || 30)).catch((error) => setResult(String(error)));
}
