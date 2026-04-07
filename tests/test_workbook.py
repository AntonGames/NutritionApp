from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from nutrition_app.main import create_state
from nutrition_app.schemas import ManualMealCreate, MealComponent, WeightCreate, WorkoutCreate


def test_workbook_export_contains_russian_sheets(tmp_path, monkeypatch):
    profile_src = Path(__file__).resolve().parents[1] / "config/profile.example.yaml"
    profile_path = tmp_path / "config/profile.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(profile_src.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("NUTRITION_PROFILE_PATH", str(profile_path.relative_to(tmp_path)).replace("\\", "/"))
    monkeypatch.setenv("NUTRITION_DB_PATH", "data/test.db")
    monkeypatch.setenv("NUTRITION_WORKBOOK_PATH", "data/exports/test.xlsx")
    monkeypatch.setenv("NUTRITION_UPLOAD_DIR", "data/uploads")
    monkeypatch.setenv("NUTRITION_EXPORT_ON_WRITE", "false")

    state = create_state(tmp_path)
    now = datetime.now()
    state.database.add_manual_meal(
        ManualMealCreate(
            meal_name="Breakfast",
            components=[
                MealComponent(
                    description="Yogurt",
                    category="protein",
                    estimated_grams=200,
                    calories=160,
                    protein_g=18,
                    fat_g=4,
                    carbs_g=18,
                )
            ],
        ),
        logged_at=now,
    )
    state.database.add_weight(WeightCreate(weight_kg=108.0), logged_at=now)
    state.database.add_workout(
        WorkoutCreate(description="Run", calories_burned=250, duration_min=30),
        logged_at=now,
    )
    workbook_path = state.workbook_exporter.export(state.settings.workbook_path)

    assert workbook_path.exists()
    with ZipFile(workbook_path) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
    assert "Главная" in workbook_xml
    assert "Приемы пищи" in workbook_xml
