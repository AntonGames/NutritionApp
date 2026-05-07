# Nutrition App

Self-hosted nutrition logging for your Raspberry Pi / Home Assistant stack.

This project now supports two modes:

1. Recommended: `ChatGPT Plus + Custom GPT + Actions -> your Pi -> SQLite -> Excel/HA`
2. Optional: direct server-side photo analysis through the OpenAI API

The first mode is the cheaper one. In that setup, ChatGPT analyzes the meal photo inside the chat, then calls your Pi through Actions. Your server only stores structured data, builds summaries, updates the workbook, and feeds Home Assistant.

## Recommended architecture

`Photo in ChatGPT -> Custom GPT with Actions -> Nutrition App API on Pi -> SQLite -> Excel export + Home Assistant`

Why this is the best default:

- no Google Apps Script redirects
- no Google Sheets used as a fragile backend
- no OpenAI API key required on the server
- durable local storage
- clean workbook export
- easy HA sensors and automations

The older failed Apps Script approach is documented in [docs/legacy_analysis.md](./docs/legacy_analysis.md).

## What this app does

- stores meals, weight, and workouts in SQLite
- builds daily and weekly summaries
- generates a Russian-friendly Excel workbook
- exposes write endpoints for Home Assistant
- exposes GPT Actions endpoints for a Custom GPT
- optionally supports direct photo upload if you decide to add a server-side OpenAI API key later

## Main files

- `src/nutrition_app/main.py`
  FastAPI app, UI, GPT Actions endpoints, and workbook download
- `src/nutrition_app/storage.py`
  SQLite schema and persistence
- `src/nutrition_app/services/summaries.py`
  Deterministic suggestions and progress logic
- `src/nutrition_app/services/workbook.py`
  Excel export
- `deploy/home_assistant/package_example.yaml`
  Home Assistant package template
- `deploy/gpt_actions/custom_gpt_instructions.md`
  Ready-to-paste instructions for your Custom GPT

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

Copy [`.env.example`](./.env.example) to `.env`:

```env
NUTRITION_PROFILE_PATH=config/profile.yaml
NUTRITION_DB_PATH=data/nutrition.db
NUTRITION_WORKBOOK_PATH=data/exports/nutrition_tracker.xlsx
NUTRITION_UPLOAD_DIR=data/uploads
NUTRITION_API_KEY=change-me
NUTRITION_OPENAI_API_KEY=
NUTRITION_OPENAI_MODEL=gpt-4.1-mini
NUTRITION_MAX_UPLOAD_MB=8
NUTRITION_EXPORT_ON_WRITE=true
```

Notes:

- `NUTRITION_API_KEY` is the shared secret for GPT Actions and protected write endpoints.
- `NUTRITION_OPENAI_API_KEY` is optional.
- leave `NUTRITION_OPENAI_API_KEY` empty if you only want the cheaper GPT Actions flow
- set `NUTRITION_OPENAI_API_KEY` only if you want the local web UI to analyze uploaded photos directly

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
- FastAPI docs: `http://localhost:8000/docs`
- GPT Actions schema: `http://localhost:8000/api/actions/openapi.yaml`
- Workbook download: `http://localhost:8000/api/export/workbook`

## Run on Raspberry Pi

```bash
git clone https://github.com/AntonGames/NutritionApp.git
cd NutritionApp
cp .env.example .env
nano .env
docker compose up -d --build
```

If you are using the Home Assistant SSH add-on fallback instead of Docker, the same `.env` values still apply.

## Stable free public HTTPS with DuckDNS on Home Assistant OS

If you want the most stable free URL for GPT Actions without relying on temporary tunnels, use:

- DuckDNS for the public hostname
- Let's Encrypt for a real certificate
- direct HTTPS serving from Nutrition App on port `443`

This repository includes a deployment script for Home Assistant OS / Advanced SSH:

```sh
cd /config/NutritionApp
DUCKDNS_DOMAIN=your-subdomain.duckdns.org \
DUCKDNS_TOKEN=your-duckdns-token \
sh deploy/home_assistant/install_duckdns_https.sh
```

You can also avoid putting the token on the command line by creating:

```sh
/config/NutritionApp/.duckdns.env
```

with:

```sh
DOMAIN=your-subdomain.duckdns.org
TOKEN=your-duckdns-token
```

What the script does:

- updates the DuckDNS A record to your current public IP
- installs `acme.sh` locally into the app folder
- issues a Let's Encrypt certificate through the DuckDNS DNS challenge
- stores the certificate in `certs/fullchain.pem` and `certs/privkey.pem`
- keeps the local HTTP app on `:8000`
- starts a second HTTPS instance on `:443` for GPT Actions

To keep the public IP current, schedule:

```sh
sh deploy/home_assistant/update_duckdns_ip.sh
```

every few minutes on the Home Assistant host.

After that, do one router step:

- forward external TCP `443` to your Home Assistant host on TCP `443`

### Self-healing watchdog on Home Assistant OS

If you keep this app on Home Assistant OS instead of moving it to a normal Docker host, add the watchdog too:

```sh
cd /config/NutritionApp
printf '%s\n' 'YOUR_SUDO_PASSWORD' | sudo -S sh deploy/home_assistant/install_watchdog.sh
sh deploy/home_assistant/watchdog.sh
```

What it does:

- installs a symlink into `/etc/periodic/15min`
- checks local HTTP and HTTPS health every 15 minutes
- restarts the app listeners if either one is down

This does not make the HA OS approach perfect, but it gives you automatic recovery instead of waiting for a manual SSH restart.

Then your stable schema URL becomes:

- `https://your-subdomain.duckdns.org/api/actions/openapi.yaml`

Important notes:

- this path assumes your DuckDNS hostname already points to your public IP
- if your ISP uses CG-NAT, normal port forwarding will not work
- the script does not configure your router for you
- `certs/` is runtime state and should not be committed

## GPT Actions setup

### Important networking note

Your local URL such as `http://YOUR_PI_IP:8000` is fine for the web UI and Home Assistant on your LAN, but ChatGPT Actions will need a URL that ChatGPT can reach.

Inference from the architecture:

- a private `192.168.x.x` address is not enough for Actions
- you will need a public HTTPS URL in front of this app

Typical ways to do that:

- DuckDNS + Let's Encrypt + router port forwarding
- Cloudflare Tunnel
- your own reverse proxy + domain + TLS
- another secure HTTPS tunnel you trust

### Step-by-step

1. Run the app and make it reachable through a public HTTPS URL.
2. Open your running schema:
   - `https://YOUR_PUBLIC_DOMAIN/api/actions/openapi.yaml`
3. Create a Custom GPT.
4. Add an Action using that schema URL or paste the schema manually.
5. Configure authentication as API key:
   - header name: `X-API-Key`
   - value: your `NUTRITION_API_KEY`
6. Paste the instructions from [deploy/gpt_actions/custom_gpt_instructions.md](./deploy/gpt_actions/custom_gpt_instructions.md).
7. Save and test with:
   - a meal photo
   - a weight message
   - a workout message

## GPT Actions API

### `GET /api/actions/openapi.yaml`

Returns a minimal OpenAPI document for Custom GPT Actions.

### `POST /api/actions`

Single GPT-friendly endpoint with four actions:

- `init_day`
- `log_meal`
- `log_weight`
- `log_workout`

The response is flat and GPT-friendly. It always includes the updated daily summary:

```json
{
  "ok": true,
  "action": "log_meal",
  "date": "2026-04-07",
  "entityId": "uuid",
  "summary": {
    "date": "2026-04-07",
    "weight": 108.4,
    "calorieTarget": 2400,
    "proteinTarget": 180,
    "fatTarget": 75,
    "carbTarget": 250,
    "foodCalories": 830,
    "protein": 40,
    "fat": 56,
    "carbs": 35,
    "exerciseCalories": 0,
    "netCalories": 830,
    "caloriesLeft": 1570,
    "proteinLeft": 140,
    "fatLeft": 19,
    "carbLeft": 215,
    "mealsCount": 1,
    "workoutsCount": 0,
    "suggestions": [
      "Добери еще примерно 130.0 г белка..."
    ]
  }
}
```

### `GET /api/actions/summary`

Query:

- `target_date=YYYY-MM-DD` optional

Returns the same flat summary object without writing data.

## Local API and UI endpoints

These still exist and are useful for Home Assistant and local testing:

- `GET /api/health`
- `GET /api/summary/daily`
- `GET /api/summary/weekly`
- `GET /api/events/recent`
- `GET /api/export/workbook`
- `POST /api/meals/manual`
- `POST /api/weights`
- `POST /api/workouts`

## Optional server-side photo analysis

If you later decide you want the Pi itself to accept image uploads and call OpenAI directly, set:

```env
NUTRITION_OPENAI_API_KEY=sk-...
```

Then the local UI form and this endpoint become usable:

- `POST /api/meals/photo`

That mode is optional and not required for the subscription-only GPT Actions setup.

## Excel workbook output

The workbook is saved by default to:

`data/exports/nutrition_tracker.xlsx`

Sheets include:

- `Главная`
- `Настройки`
- `Приемы пищи`
- `Вес`
- `Тренировки`
- `Дни`
- `Недели`

SQLite is still the source of truth. Excel is the reporting layer.

## Home Assistant integration

See [`deploy/home_assistant/package_example.yaml`](./deploy/home_assistant/package_example.yaml).

It includes:

- `rest_command` examples for weight and workout logging
- `rest` sensors for daily summary values
- helper entities for quick weight entry

Recommended split:

- meals through Custom GPT
- weight/workouts through HA or the local UI
- workbook review through the export endpoint

## Suggestions logic

Daily suggestions are deterministic and local.

That is intentional:

- meal estimation can come from GPT
- daily coaching should still work without extra API calls
- deterministic rules are easier to trust and debug

The logic currently looks at:

- protein vs target floor
- calories vs target
- weekly workouts
- short-term weight direction
- logging consistency

## Tests

```powershell
.venv\Scripts\Activate.ps1
py -3.13 -m pip install -e .[dev]
pytest
```

Covered flows:

- protected write endpoints
- manual meal logging updates daily summary
- GPT Actions logging updates the flat summary
- workbook export contains the expected Russian sheets

## Known limitations

- ChatGPT Actions require a reachable HTTPS URL, not just a LAN IP
- food estimation quality still depends on the model and the photo
- the Pi UI is intentionally simple and not a full native mobile app
- HEIC handling is still not implemented

## Best next improvements

1. Add Google Sheets sync as a secondary mirror on top of SQLite.
2. Add a correction screen for editing GPT-estimated meals after logging.
3. Add Telegram ingestion.
4. Import workouts from Apple Health, Garmin, or Strava.
5. Add automatic weekly reports in Home Assistant.
