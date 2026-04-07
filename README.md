# Nutrition App

Self-hosted nutrition logging for your Raspberry Pi / Home Assistant stack.

This project replaces the older Google Apps Script prototype in this folder with a more reliable setup:

- upload a meal photo through a normal web page or HTTP API
- analyze the meal with OpenAI vision
- store meals, workouts, and weight in SQLite
- regenerate a Russian-friendly Excel workbook automatically
- expose clean JSON endpoints for Home Assistant, dashboards, or future mobile clients

## Why this design is more reliable

The failed approach in [`nutrition_tracker_system_bundle`](./nutrition_tracker_system_bundle) treated Google Sheets as both UI and database. That works for a demo, but it becomes fragile once you want image uploads, corrections, auditing, or stable automations.

The new flow is:

`Photo/UI/HA -> FastAPI -> SQLite -> Excel export`

That gives you:

- a normal HTTP service on your Pi
- durable local storage
- easier debugging and tests
- a clean Excel file for reporting instead of using Excel as a backend database

More detail: [`docs/legacy_analysis.md`](./docs/legacy_analysis.md)

## What’s included

- `src/nutrition_app/main.py`
  The FastAPI app and mobile-friendly upload UI.
- `src/nutrition_app/storage.py`
  SQLite schema and CRUD logic.
- `src/nutrition_app/services/meal_analyzer.py`
  OpenAI-based photo analysis.
- `src/nutrition_app/services/summaries.py`
  Deterministic daily/weekly summaries and suggestions.
- `src/nutrition_app/services/workbook.py`
  Automatic `.xlsx` export with Russian sheet names.
- `deploy/home_assistant/package_example.yaml`
  Example Home Assistant package for logging and sensors.

## Main assumptions

- Meal photos are the primary AI input.
- Weight and workouts are logged manually or via Home Assistant.
- SQLite is the source of truth.
- Excel is the human-readable report/export layer.
- Your Pi runs Docker or plain Python.

If you later want smartwatch import, Telegram bot input, or GPT Action support, this design can be extended without changing the storage model.

## Project structure

```text
config/
  profile.yaml
  profile.example.yaml
data/
  exports/
src/nutrition_app/
  main.py
  storage.py
  services/
deploy/home_assistant/
tests/
```

## Configuration

### 1. Profile

Edit [`config/profile.yaml`](./config/profile.yaml):

```yaml
timezone: Europe/Vilnius
user:
  name: Your Name
  height_cm: 180
  age: 30
  sex: unspecified
  start_weight_kg: 100
  goal_weight_kg: 85
targets:
  daily_calories: 2400
  protein_g: 180
  fat_g: 75
  carbs_g: 250
preferences:
  protein_floor_g: 170
  weekly_workout_goal: 3
  weekly_weight_change_goal_kg: -0.5
```

### 2. Environment

Copy [`.env.example`](./.env.example) to `.env` and fill in secrets:

```env
NUTRITION_PROFILE_PATH=config/profile.yaml
NUTRITION_DB_PATH=data/nutrition.db
NUTRITION_WORKBOOK_PATH=data/exports/nutrition_tracker.xlsx
NUTRITION_UPLOAD_DIR=data/uploads
NUTRITION_API_KEY=change-me
NUTRITION_OPENAI_API_KEY=sk-...
NUTRITION_OPENAI_MODEL=gpt-4.1-mini
NUTRITION_MAX_UPLOAD_MB=8
NUTRITION_EXPORT_ON_WRITE=true
```

Important notes:

- `NUTRITION_API_KEY` protects write endpoints.
- `NUTRITION_OPENAI_API_KEY` is required for meal photo analysis.
- The workbook export is regenerated after each write when `NUTRITION_EXPORT_ON_WRITE=true`.

## Run locally with Python

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
py -3.13 -m pip install -e .[dev]
copy .env.example .env
python -m uvicorn nutrition_app.main:app --reload
```

Open:

- UI: `http://localhost:8000/`
- OpenAPI docs: `http://localhost:8000/docs`
- Workbook download: `http://localhost:8000/api/export/workbook`

## Run on Raspberry Pi with Docker

```bash
git clone <your-repo-url>
cd NutritionApp
cp .env.example .env
nano .env
docker compose up -d --build
```

The included [`Dockerfile`](./Dockerfile) and [`docker-compose.yml`](./docker-compose.yml) are Pi-friendly. The official Python base image is multi-arch, so this should work on a Pi 5 without changing the image name.

Recommended next step on the Pi:

- keep the service private on your LAN
- put it behind your Home Assistant reverse proxy or Nginx Proxy Manager
- do not expose it publicly without auth

## API overview

### `GET /api/health`

Health check.

### `GET /api/summary/daily`

Optional query:

- `target_date=YYYY-MM-DD`

Returns the current day totals, targets, remaining macros, weight, and suggestions.

### `GET /api/summary/weekly`

Returns weekly rollups for trend tracking.

### `GET /api/events/recent`

Returns the latest saved meals, workouts, and weight entries.

### `GET /api/export/workbook`

Generates and downloads the current Excel workbook.

### `POST /api/meals/photo`

Multipart form fields:

- `photo` required image file
- `note` optional
- `logged_date` optional `YYYY-MM-DD`
- `logged_time` optional `HH:MM`

This endpoint:

1. uploads the image
2. calls OpenAI vision
3. stores structured components
4. refreshes the workbook export
5. returns the meal analysis and the updated daily summary

### `POST /api/meals/manual`

Fallback/manual correction endpoint for meals.

Example:

```json
{
  "meal_name": "Lunch",
  "components": [
    {
      "description": "Chicken breast",
      "category": "protein",
      "estimated_grams": 180,
      "calories": 300,
      "protein_g": 42,
      "fat_g": 8,
      "carbs_g": 0
    }
  ]
}
```

### `POST /api/weights`

Example:

```json
{
  "weight_kg": 108.4,
  "note": "after waking up"
}
```

### `POST /api/workouts`

Example:

```json
{
  "description": "Strength training",
  "duration_min": 55,
  "calories_burned": 420,
  "avg_hr": 132
}
```

## Excel workbook output

The exported workbook is saved to `data/exports/nutrition_tracker.xlsx` by default.

Sheets:

- `Главная`
- `Настройки`
- `Приемы пищи`
- `Вес`
- `Тренировки`
- `Дни`
- `Недели`

This workbook is intended to be pleasant to read, filter, and review in Excel or LibreOffice, while the database remains the actual backend.

## Home Assistant integration

See [`deploy/home_assistant/package_example.yaml`](./deploy/home_assistant/package_example.yaml).

It includes:

- `rest_command` examples for weight/workout logging
- `rest` sensors for the daily summary
- simple helper entities for a weight-entry flow

Practical setup:

1. Put the service on the same Docker network as Home Assistant, or expose it on your LAN.
2. Add a secret in `secrets.yaml`:

```yaml
nutrition_tracker_api_key: change-me
```

3. Copy the package example into your HA packages folder and adapt hostnames.

The cleanest first version is:

- use the Nutrition App UI for meal photo uploads
- use HA for reminders, dashboards, and weight/workout quick actions

## Suggestions logic

The app’s coaching suggestions are deterministic and local.

That was deliberate:

- photo estimation already depends on AI
- daily coaching should still work if you don’t want extra model calls
- deterministic rules are easier to trust and debug

Current suggestions look at:

- protein intake vs your minimum
- calories vs target
- weekly workout volume
- recent weight direction
- logging consistency

## Tests

```powershell
.venv\Scripts\Activate.ps1
py -3.13 -m pip install -e .[dev]
pytest
```

Covered flows:

- protected write endpoints
- meal logging updates daily summary
- workout logging updates exercise calories
- workbook export contains the expected Russian sheets

## Known limitations

- The first version assumes food photos, not workout screenshots.
- Meal estimation is only as good as the photo quality and model output.
- HEIC support is not implemented yet; JPEG/PNG/WebP are the safe formats.
- The UI is intentionally lightweight, not a full mobile app.

## Best next improvements

If you want to keep iterating after this base is running, the best upgrades would be:

1. add a meal correction screen for editing AI-estimated components
2. support Telegram or WhatsApp ingestion
3. import workouts from Apple Health / Garmin / Strava
4. add weekly PDF or email reports from Home Assistant
5. add GPT Action or chat bot access on top of the same API
