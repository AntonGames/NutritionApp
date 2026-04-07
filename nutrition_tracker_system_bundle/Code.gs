/**
 * Nutrition Tracker for Google Sheets + ChatGPT Actions
 * Deploy as Web App:
 *   Execute as: Me
 *   Who has access: Anyone with link
 *
 * Request JSON examples:
 * POST {"token":"CHANGE_ME","action":"init_day","date":"2026-04-07"}
 * POST {"token":"CHANGE_ME","action":"log_weight","date":"2026-04-07","weight":108.7}
 * POST {
 *   "token":"CHANGE_ME",
 *   "action":"log_meal",
 *   "date":"2026-04-07",
 *   "time":"12:35",
 *   "source":"photo",
 *   "confidence":"medium",
 *   "comment":"Estimated from image",
 *   "components":[
 *     {"description":"Olivier salad","componentType":"food","category":"salad","calories":550,"protein":12,"fat":38,"carbs":35},
 *     {"description":"Baked chicken thigh","componentType":"food","category":"meat","calories":280,"protein":28,"fat":18,"carbs":0}
 *   ]
 * }
 * POST {
 *   "token":"CHANGE_ME",
 *   "action":"log_workout",
 *   "date":"2026-04-07",
 *   "time":"20:10",
 *   "durationMin":58,
 *   "exerciseCalories":420,
 *   "avgHr":134,
 *   "description":"Strength training"
 * }
 */

const SHEET_SETTINGS = 'Settings';
const SHEET_DASHBOARD = 'Dashboard';
const SHEET_WEEKLY = 'Weekly Summary';
const SHEET_TEMPLATE = 'Day Template';
const FIRST_LOG_ROW = 23;
const DAY_HEADER_DATE_CELL = 'B4';
const DAY_WEIGHT_CELL = 'B5';
const TOKEN_CELL = 'B18'; // optional storage on Settings

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || '{}');
    validateToken_(payload.token);
    const action = payload.action;
    if (!action) return json_({ok:false, error:'Missing action'}, 400);

    if (action === 'init_day') {
      const date = ensureIsoDate_(payload.date);
      initDaySheet_(date);
      return json_({ok:true, action, date});
    }
    if (action === 'log_weight') {
      const date = ensureIsoDate_(payload.date);
      const sh = initDaySheet_(date);
      sh.getRange(DAY_WEIGHT_CELL).setValue(Number(payload.weight));
      refreshAggregates_();
      return json_({ok:true, action, date, weight:Number(payload.weight)});
    }
    if (action === 'log_meal') {
      const date = ensureIsoDate_(payload.date);
      const sh = initDaySheet_(date);
      const time = payload.time || currentVilniusTime_();
      const source = payload.source || 'chatgpt';
      const confidence = payload.confidence || 'medium';
      const comment = payload.comment || '';
      const components = payload.components || [];
      if (!components.length) return json_({ok:false, error:'No meal components provided'}, 400);

      const startRow = nextFreeRow_(sh);
      const rows = components.map(c => [
        time,
        c.description || '',
        c.componentType || 'food',
        c.category || '',
        num_(c.calories),
        num_(c.protein),
        num_(c.fat),
        num_(c.carbs),
        confidence,
        source,
        comment
      ]);
      sh.getRange(startRow, 1, rows.length, rows[0].length).setValues(rows);
      sh.getRange(startRow, 1, rows.length, 1).setNumberFormat('hh:mm');
      refreshAggregates_();
      return json_({ok:true, action, date, rowsAdded:rows.length});
    }
    if (action === 'log_workout') {
      const date = ensureIsoDate_(payload.date);
      const sh = initDaySheet_(date);
      const time = payload.time || currentVilniusTime_();
      const calories = num_(payload.exerciseCalories);
      const duration = payload.durationMin ? `Duration ${payload.durationMin} min` : '';
      const hr = payload.avgHr ? `Avg HR ${payload.avgHr}` : '';
      const comment = [payload.description || 'Workout', duration, hr].filter(Boolean).join(' | ');
      const row = nextFreeRow_(sh);
      sh.getRange(row, 1, 1, 11).setValues([[
        time,
        payload.description || 'Workout',
        'exercise',
        'training',
        calories,
        0, 0, 0,
        'high',
        'manual',
        comment
      ]]);
      sh.getRange(row, 1).setNumberFormat('hh:mm');
      refreshAggregates_();
      return json_({ok:true, action, date, calories});
    }

    return json_({ok:false, error:'Unknown action'}, 400);
  } catch (err) {
    return json_({ok:false, error:String(err && err.message ? err.message : err)}, 500);
  }
}

function doGet(e) {
  try {
    const token = e.parameter.token || '';
    validateToken_(token);
    const action = e.parameter.action || 'summary';
    if (action !== 'summary') return json_({ok:false, error:'Unknown action'}, 400);
    const date = ensureIsoDate_(e.parameter.date || todayVilnius_());
    const sh = initDaySheet_(date);
    refreshAggregates_();
    const summary = {
      ok: true,
      date,
      weight: sh.getRange('B5').getValue(),
      calorieTarget: sh.getRange('B6').getValue(),
      proteinTarget: sh.getRange('B7').getValue(),
      fatTarget: sh.getRange('B8').getValue(),
      carbTarget: sh.getRange('B9').getValue(),
      foodCalories: sh.getRange('B10').getValue(),
      protein: sh.getRange('B11').getValue(),
      fat: sh.getRange('B12').getValue(),
      carbs: sh.getRange('B13').getValue(),
      exerciseCalories: sh.getRange('B14').getValue(),
      netCalories: sh.getRange('B15').getValue(),
      caloriesLeft: sh.getRange('B16').getValue(),
      proteinLeft: sh.getRange('B17').getValue(),
      fatLeft: sh.getRange('B18').getValue(),
      carbLeft: sh.getRange('B19').getValue()
    };
    return json_(summary, 200);
  } catch (err) {
    return json_({ok:false, error:String(err && err.message ? err.message : err)}, 500);
  }
}

function initDaySheet_(dateStr) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(dateStr);
  if (sh) return sh;
  const template = ss.getSheetByName(SHEET_TEMPLATE);
  if (!template) throw new Error('Missing Day Template sheet');
  sh = template.copyTo(ss).setName(dateStr);
  ss.setActiveSheet(sh);
  ss.moveActiveSheet(ss.getSheets().length);
  sh.getRange(DAY_HEADER_DATE_CELL).setValue(new Date(dateStr + 'T00:00:00'));
  sh.getRange(DAY_HEADER_DATE_CELL).setNumberFormat('yyyy-mm-dd');
  return sh;
}

function nextFreeRow_(sh) {
  const values = sh.getRange(FIRST_LOG_ROW, 1, Math.max(1, sh.getMaxRows() - FIRST_LOG_ROW + 1), 1).getValues();
  for (let i = 0; i < values.length; i++) {
    if (!values[i][0]) return FIRST_LOG_ROW + i;
  }
  sh.insertRowsAfter(sh.getMaxRows(), 20);
  return sh.getMaxRows() - 19;
}

function refreshAggregates_() {
  const ss = SpreadsheetApp.getActive();
  const sheets = ss.getSheets()
    .map(s => s.getName())
    .filter(name => /^\d{4}-\d{2}-\d{2}$/.test(name))
    .sort();

  // Dashboard current weight + recent trend
  const dashboard = ss.getSheetByName(SHEET_DASHBOARD);
  const trendRows = [];
  let latestWeight = '';
  sheets.forEach(name => {
    const sh = ss.getSheetByName(name);
    const weight = sh.getRange('B5').getValue();
    const foodCalories = sh.getRange('B10').getValue();
    const protein = sh.getRange('B11').getValue();
    const netCalories = sh.getRange('B15').getValue();
    if (weight !== '' || foodCalories !== '' || protein !== '') {
      trendRows.push([new Date(name + 'T00:00:00'), weight, foodCalories, protein, netCalories]);
    }
    if (weight !== '') latestWeight = weight;
  });
  dashboard.getRange('B5').setValue(latestWeight);
  dashboard.getRange('A12:E41').clearContent();
  if (trendRows.length) {
    const last30 = trendRows.slice(-30);
    dashboard.getRange(12,1,last30.length,last30[0].length).setValues(last30);
    dashboard.getRange(12,1,last30.length,1).setNumberFormat('yyyy-mm-dd');
  }

  // Weekly summary
  const weekly = ss.getSheetByName(SHEET_WEEKLY);
  weekly.getRange('A4:H100').clearContent();
  const bucket = {};
  sheets.forEach(name => {
    const sh = ss.getSheetByName(name);
    const date = new Date(name + 'T00:00:00');
    const monday = weekStart_(date);
    const key = Utilities.formatDate(monday, 'Europe/Vilnius', 'yyyy-MM-dd');
    if (!bucket[key]) bucket[key] = {weights:[], calories:[], protein:[], workouts:0, days:0};
    const weight = numOrBlank_(sh.getRange('B5').getValue());
    const foodCalories = numOrBlank_(sh.getRange('B10').getValue());
    const protein = numOrBlank_(sh.getRange('B11').getValue());
    const workoutCals = numOrBlank_(sh.getRange('B14').getValue());
    if (weight !== '') bucket[key].weights.push(weight);
    if (foodCalories !== '') bucket[key].calories.push(foodCalories);
    if (protein !== '') bucket[key].protein.push(protein);
    if (workoutCals !== '' && workoutCals > 0) bucket[key].workouts += 1;
    bucket[key].days += 1;
  });
  const weeks = Object.keys(bucket).sort();
  const out = [];
  let prevAvgWeight = '';
  weeks.forEach(key => {
    const b = bucket[key];
    const avgWeight = avg_(b.weights);
    const avgCalories = avg_(b.calories);
    const avgProtein = avg_(b.protein);
    const delta = (prevAvgWeight === '' || avgWeight === '') ? '' : round1_(avgWeight - prevAvgWeight);
    const note = avgProtein !== '' && avgProtein < 170 ? 'Protein below target' : '';
    out.push([new Date(key + 'T00:00:00'), avgWeight, delta, avgCalories, avgProtein, b.workouts, b.days, note]);
    if (avgWeight !== '') prevAvgWeight = avgWeight;
  });
  if (out.length) {
    weekly.getRange(4,1,out.length,out[0].length).setValues(out);
    weekly.getRange(4,1,out.length,1).setNumberFormat('yyyy-mm-dd');
  }
}

function weekStart_(dateObj) {
  const d = new Date(dateObj);
  const day = d.getDay(); // Sun 0 ... Sat 6
  const diff = (day === 0 ? -6 : 1 - day);
  d.setDate(d.getDate() + diff);
  d.setHours(0,0,0,0);
  return d;
}

function validateToken_(incoming) {
  const ss = SpreadsheetApp.getActive();
  const settings = ss.getSheetByName(SHEET_SETTINGS);
  const expected = String(settings.getRange(TOKEN_CELL).getValue() || '').trim();
  if (!expected) return; // allow during initial setup
  if (String(incoming || '').trim() !== expected) throw new Error('Invalid token');
}

function ensureIsoDate_(dateStr) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(dateStr || ''))) throw new Error('Date must be YYYY-MM-DD');
  return dateStr;
}
function num_(v) { return Number(v || 0); }
function numOrBlank_(v) { return v === '' ? '' : Number(v); }
function avg_(arr) { return arr.length ? round1_(arr.reduce((a,b)=>a+b,0)/arr.length) : ''; }
function round1_(n) { return Math.round(n * 10) / 10; }
function todayVilnius_() { return Utilities.formatDate(new Date(), 'Europe/Vilnius', 'yyyy-MM-dd'); }
function currentVilniusTime_() { return Utilities.formatDate(new Date(), 'Europe/Vilnius', 'HH:mm'); }

function json_(obj, code) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
