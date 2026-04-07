# Nutrition Tracker System

This bundle gives you a near-ready setup for:
- Google Sheets workbook
- Google Apps Script backend
- OpenAPI schema for a custom GPT Action
- Behavior spec for the GPT

## What is already done
- `nutrition_tracker_template.xlsx` — tracker workbook template
- `Code.gs` — Apps Script backend
- `openapi.yaml` — action schema for the custom GPT
- `custom_gpt_instructions.md` — system behavior spec

## What still requires your account
I cannot deploy into your Google account from here. You must do the account-bound steps:
1. Upload or import the workbook to Google Sheets.
2. Open Extensions -> Apps Script.
3. Paste `Code.gs`.
4. Deploy as Web App.
5. Put the web app URL into `openapi.yaml`.
6. Create a Custom GPT and add the Action using `openapi.yaml`.
7. Paste the instructions from `custom_gpt_instructions.md`.

## Recommended starting targets
- Calories: 2400
- Protein: 180 g
- Fat: 75 g
- Carbs: 250 g

## Google Sheets structure
- Dashboard
- Settings
- Weekly Summary
- Day Template
- Daily sheets created automatically like `2026-04-07`

## How the Apps Script works
### POST actions
- `init_day`
- `log_weight`
- `log_meal`
- `log_workout`

### GET summary
- `action=summary&date=YYYY-MM-DD`

## Example payloads

### Log weight
```json
{
  "token": "CHANGE_ME",
  "action": "log_weight",
  "date": "2026-04-07",
  "weight": 108.7
}
```

### Log meal
```json
{
  "token": "CHANGE_ME",
  "action": "log_meal",
  "date": "2026-04-07",
  "time": "12:35",
  "source": "photo",
  "confidence": "medium",
  "comment": "Estimated from image",
  "components": [
    {
      "description": "Olivier salad",
      "componentType": "food",
      "category": "salad",
      "calories": 550,
      "protein": 12,
      "fat": 38,
      "carbs": 35
    },
    {
      "description": "Baked chicken thigh",
      "componentType": "food",
      "category": "meat",
      "calories": 280,
      "protein": 28,
      "fat": 18,
      "carbs": 0
    }
  ]
}
```

### Log workout
```json
{
  "token": "CHANGE_ME",
  "action": "log_workout",
  "date": "2026-04-07",
  "time": "20:10",
  "durationMin": 58,
  "exerciseCalories": 420,
  "avgHr": 134,
  "description": "Strength training"
}
```

## Best practice notes
- Meal photos are estimates, not lab measurements.
- For mixed dishes, desserts, sauces, and restaurant food, keep confidence as `low` or `medium`.
- Do not subtract watch calories too aggressively in real life. Use them as a secondary metric.

## Suggested next step
Start with 7 test days before trusting the automation fully.
