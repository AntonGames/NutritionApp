from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nutrition_app.main import create_app, create_state


@pytest.fixture()
def app_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    profile_src = Path(__file__).resolve().parents[1] / "config/profile.example.yaml"
    profile_path = tmp_path / "config/profile.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(profile_src.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("NUTRITION_PROFILE_PATH", str(profile_path.relative_to(tmp_path)).replace("\\", "/"))
    monkeypatch.setenv("NUTRITION_DB_PATH", "data/test.db")
    monkeypatch.setenv("NUTRITION_WORKBOOK_PATH", "data/exports/test.xlsx")
    monkeypatch.setenv("NUTRITION_UPLOAD_DIR", "data/uploads")
    monkeypatch.setenv("NUTRITION_API_KEY", "secret")
    monkeypatch.setenv("NUTRITION_EXPORT_ON_WRITE", "false")
    return create_state(tmp_path)


def test_weight_and_workout_flow(app_state):
    app = create_app(app_state)
    client = TestClient(app)
    headers = {"X-API-Key": "secret"}

    weight_response = client.post("/api/weights", json={"weight_kg": 108.4}, headers=headers)
    assert weight_response.status_code == 200
    assert weight_response.json()["ok"] is True

    workout_response = client.post(
        "/api/workouts",
        json={"description": "Walk", "duration_min": 45, "calories_burned": 300},
        headers=headers,
    )
    assert workout_response.status_code == 200
    payload = workout_response.json()
    assert payload["daily_summary"]["exercise_calories"] == 300.0


def test_manual_meal_updates_daily_summary(app_state):
    app = create_app(app_state)
    client = TestClient(app)
    headers = {"X-API-Key": "secret"}

    response = client.post(
        "/api/meals/manual",
        json={
            "meal_name": "Lunch",
            "components": [
                {
                    "description": "Chicken",
                    "category": "protein",
                    "estimated_grams": 150,
                    "calories": 280,
                    "protein_g": 32,
                    "fat_g": 14,
                    "carbs_g": 0,
                },
                {
                    "description": "Rice",
                    "category": "carb",
                    "estimated_grams": 180,
                    "calories": 240,
                    "protein_g": 5,
                    "fat_g": 1,
                    "carbs_g": 52,
                },
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    summary = response.json()["daily_summary"]
    assert summary["food"]["calories"] == 520.0
    assert summary["food"]["protein_g"] == 37.0
    assert summary["meals_count"] == 1


def test_action_meal_updates_flat_summary(app_state):
    app = create_app(app_state)
    client = TestClient(app)
    headers = {"X-API-Key": "secret"}

    response = client.post(
        "/api/actions",
        json={
            "action": "log_meal",
            "mealName": "Lunch",
            "confidence": "medium",
            "components": [
                {
                    "description": "Chicken",
                    "componentType": "food",
                    "category": "protein",
                    "estimatedGrams": 150,
                    "calories": 280,
                    "protein": 32,
                    "fat": 14,
                    "carbs": 0,
                },
                {
                    "description": "Rice",
                    "componentType": "food",
                    "category": "carb",
                    "estimatedGrams": 180,
                    "calories": 240,
                    "protein": 5,
                    "fat": 1,
                    "carbs": 52,
                },
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "log_meal"
    assert payload["summary"]["foodCalories"] == 520.0
    assert payload["summary"]["protein"] == 37.0
    assert payload["summary"]["mealsCount"] == 1


def test_actions_openapi_route_exists(app_state):
    app = create_app(app_state)
    client = TestClient(app)

    response = client.get("/api/actions/openapi.yaml")
    assert response.status_code == 200
    assert "postNutritionEvent" in response.text
    assert "/api/actions/summary" in response.text
    assert "NutritionActionRequest" in response.text
    assert "oneOf" not in response.text


def test_api_key_required_for_write(app_state):
    app = create_app(app_state)
    client = TestClient(app)
    response = client.post("/api/weights", json={"weight_kg": 108.4})
    assert response.status_code == 401
