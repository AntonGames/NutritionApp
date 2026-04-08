from __future__ import annotations

import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .profile import ProfileConfig
from .schemas import MealAnalysis, ManualMealCreate, RecentEvent, WeightCreate, WorkoutCreate


def _round1(value: float) -> float:
    return round(float(value), 1)


@dataclass(slots=True)
class Database:
    path: Path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS meals (
                    id TEXT PRIMARY KEY,
                    logged_at TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    local_time TEXT NOT NULL,
                    meal_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    note TEXT,
                    image_path TEXT,
                    total_calories REAL NOT NULL,
                    total_protein_g REAL NOT NULL,
                    total_fat_g REAL NOT NULL,
                    total_carbs_g REAL NOT NULL,
                    analysis_notes TEXT,
                    raw_analysis_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS meal_components (
                    id TEXT PRIMARY KEY,
                    meal_id TEXT NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT,
                    estimated_grams REAL,
                    calories REAL NOT NULL,
                    protein_g REAL NOT NULL,
                    fat_g REAL NOT NULL,
                    carbs_g REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weights (
                    id TEXT PRIMARY KEY,
                    logged_at TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    local_time TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    source TEXT NOT NULL,
                    note TEXT
                );

                CREATE TABLE IF NOT EXISTS workouts (
                    id TEXT PRIMARY KEY,
                    logged_at TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    local_time TEXT NOT NULL,
                    description TEXT NOT NULL,
                    duration_min INTEGER,
                    calories_burned REAL NOT NULL,
                    avg_hr INTEGER,
                    source TEXT NOT NULL,
                    note TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_meals_local_date ON meals(local_date);
                CREATE INDEX IF NOT EXISTS idx_weights_local_date ON weights(local_date);
                CREATE INDEX IF NOT EXISTS idx_workouts_local_date ON workouts(local_date);
                """
            )

    def add_analyzed_meal(
        self,
        analysis: MealAnalysis,
        *,
        logged_at: datetime,
        note: str | None,
        source: str,
        image_path: str | None,
    ) -> str:
        meal_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO meals (
                    id, logged_at, local_date, local_time, meal_name, source, confidence,
                    note, image_path, total_calories, total_protein_g, total_fat_g,
                    total_carbs_g, analysis_notes, raw_analysis_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    meal_id,
                    logged_at.isoformat(),
                    logged_at.date().isoformat(),
                    logged_at.strftime("%H:%M"),
                    analysis.meal_name,
                    source,
                    analysis.overall_confidence,
                    note,
                    image_path,
                    analysis.total_calories,
                    analysis.total_protein_g,
                    analysis.total_fat_g,
                    analysis.total_carbs_g,
                    analysis.analysis_notes,
                    analysis.model_dump_json(),
                ),
            )
            for index, component in enumerate(analysis.components, start=1):
                connection.execute(
                    """
                    INSERT INTO meal_components (
                        id, meal_id, position, description, category, estimated_grams,
                        calories, protein_g, fat_g, carbs_g
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        meal_id,
                        index,
                        component.description,
                        component.category,
                        component.estimated_grams,
                        component.calories,
                        component.protein_g,
                        component.fat_g,
                        component.carbs_g,
                    ),
                )
        return meal_id

    def add_manual_meal(self, payload: ManualMealCreate, *, logged_at: datetime) -> str:
        analysis = MealAnalysis(
            meal_name=payload.meal_name,
            overall_confidence=payload.confidence,
            analysis_notes=payload.note,
            components=payload.components,
        )
        return self.add_analyzed_meal(
            analysis,
            logged_at=logged_at,
            note=payload.note,
            source=payload.source,
            image_path=None,
        )

    def add_weight(self, payload: WeightCreate, *, logged_at: datetime) -> str:
        weight_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO weights (id, logged_at, local_date, local_time, weight_kg, source, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    weight_id,
                    logged_at.isoformat(),
                    logged_at.date().isoformat(),
                    logged_at.strftime("%H:%M"),
                    payload.weight_kg,
                    payload.source,
                    payload.note,
                ),
            )
        return weight_id

    def add_workout(self, payload: WorkoutCreate, *, logged_at: datetime) -> str:
        workout_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO workouts (
                    id, logged_at, local_date, local_time, description, duration_min,
                    calories_burned, avg_hr, source, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workout_id,
                    logged_at.isoformat(),
                    logged_at.date().isoformat(),
                    logged_at.strftime("%H:%M"),
                    payload.description,
                    payload.duration_min,
                    payload.calories_burned,
                    payload.avg_hr,
                    payload.source,
                    payload.note,
                ),
            )
        return workout_id

    def get_latest_weight_on_or_before(self, local_date: str) -> float | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT weight_kg
                FROM weights
                WHERE local_date <= ?
                ORDER BY local_date DESC, local_time DESC
                LIMIT 1
                """,
                (local_date,),
            ).fetchone()
        return None if row is None else _round1(row["weight_kg"])

    def get_day_meals(self, local_date: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, logged_at, local_date, local_time, meal_name, source, confidence,
                       note, image_path, total_calories, total_protein_g, total_fat_g,
                       total_carbs_g, analysis_notes
                FROM meals
                WHERE local_date = ?
                ORDER BY local_time ASC, logged_at ASC
                """,
                (local_date,),
            ).fetchall()
            components = connection.execute(
                """
                SELECT meal_id, position, description, category, estimated_grams,
                       calories, protein_g, fat_g, carbs_g
                FROM meal_components
                WHERE meal_id IN (
                    SELECT id FROM meals WHERE local_date = ?
                )
                ORDER BY meal_id, position ASC
                """,
                (local_date,),
            ).fetchall()
        grouped_components: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in components:
            grouped_components[row["meal_id"]].append(dict(row))
        result = []
        for row in rows:
            item = dict(row)
            item["components"] = grouped_components.get(row["id"], [])
            result.append(item)
        return result

    def get_day_workouts(self, local_date: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, logged_at, local_date, local_time, description, duration_min,
                       calories_burned, avg_hr, source, note
                FROM workouts
                WHERE local_date = ?
                ORDER BY local_time ASC, logged_at ASC
                """,
                (local_date,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_day_weights(self, local_date: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, logged_at, local_date, local_time, weight_kg, source, note
                FROM weights
                WHERE local_date = ?
                ORDER BY local_time ASC, logged_at ASC
                """,
                (local_date,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_events(self, limit: int = 20) -> list[RecentEvent]:
        with self.connect() as connection:
            meal_rows = connection.execute(
                """
                SELECT 'meal' AS kind, logged_at, meal_name AS title,
                       printf('%.0f kcal | Б %.0f / Ж %.0f / У %.0f',
                              total_calories, total_protein_g, total_fat_g, total_carbs_g) AS summary
                FROM meals
                ORDER BY logged_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            weight_rows = connection.execute(
                """
                SELECT 'weight' AS kind, logged_at, 'Вес' AS title,
                       printf('%.1f кг', weight_kg) AS summary
                FROM weights
                ORDER BY logged_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            workout_rows = connection.execute(
                """
                SELECT 'workout' AS kind, logged_at, description AS title,
                       printf('%.0f kcal | %s мин',
                              calories_burned,
                              COALESCE(CAST(duration_min AS TEXT), '?')) AS summary
                FROM workouts
                ORDER BY logged_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        merged = [RecentEvent.model_validate(dict(row)) for row in [*meal_rows, *weight_rows, *workout_rows]]
        merged.sort(key=lambda item: item.logged_at, reverse=True)
        return merged[:limit]

    def build_daily_rollups(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        meals_by_day: dict[str, dict[str, float]] = defaultdict(
            lambda: {"food_calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0, "meals_count": 0}
        )
        workouts_by_day: dict[str, dict[str, float]] = defaultdict(
            lambda: {"exercise_calories": 0.0, "workouts_count": 0}
        )
        weights_by_day: dict[str, float] = {}
        with self.connect() as connection:
            meal_rows = connection.execute(
                """
                SELECT local_date,
                       SUM(total_calories) AS food_calories,
                       SUM(total_protein_g) AS protein_g,
                       SUM(total_fat_g) AS fat_g,
                       SUM(total_carbs_g) AS carbs_g,
                       COUNT(*) AS meals_count
                FROM meals
                GROUP BY local_date
                ORDER BY local_date ASC
                """
            ).fetchall()
            workout_rows = connection.execute(
                """
                SELECT local_date,
                       SUM(calories_burned) AS exercise_calories,
                       COUNT(*) AS workouts_count
                FROM workouts
                GROUP BY local_date
                ORDER BY local_date ASC
                """
            ).fetchall()
            weight_rows = connection.execute(
                """
                SELECT local_date, weight_kg
                FROM weights
                ORDER BY local_date ASC, local_time ASC
                """
            ).fetchall()
        for row in meal_rows:
            meals_by_day[row["local_date"]] = {
                "food_calories": _round1(row["food_calories"] or 0),
                "protein_g": _round1(row["protein_g"] or 0),
                "fat_g": _round1(row["fat_g"] or 0),
                "carbs_g": _round1(row["carbs_g"] or 0),
                "meals_count": int(row["meals_count"] or 0),
            }
        for row in workout_rows:
            workouts_by_day[row["local_date"]] = {
                "exercise_calories": _round1(row["exercise_calories"] or 0),
                "workouts_count": int(row["workouts_count"] or 0),
            }
        for row in weight_rows:
            weights_by_day[row["local_date"]] = _round1(row["weight_kg"])

        known_dates = set(meals_by_day) | set(workouts_by_day) | set(weights_by_day)
        if start_date is not None and end_date is not None:
            first_date = start_date
            last_date = end_date
        else:
            if not known_dates:
                return []
            first_date = min(date.fromisoformat(item) for item in known_dates)
            last_date = max(date.fromisoformat(item) for item in known_dates)
            if start_date is not None:
                first_date = max(first_date, start_date)
            if end_date is not None:
                last_date = min(last_date, end_date)
        if first_date > last_date:
            return []

        results: list[dict[str, Any]] = []
        current = first_date
        latest_weight = self.get_latest_weight_on_or_before(first_date.isoformat())
        while current <= last_date:
            day_key = current.isoformat()
            if day_key in weights_by_day:
                latest_weight = weights_by_day[day_key]
            meal_values = meals_by_day.get(day_key, {})
            workout_values = workouts_by_day.get(day_key, {})
            food_calories = float(meal_values.get("food_calories", 0.0))
            exercise_calories = float(workout_values.get("exercise_calories", 0.0))
            results.append(
                {
                    "date": day_key,
                    "weight_kg": latest_weight,
                    "food_calories": _round1(food_calories),
                    "protein_g": _round1(float(meal_values.get("protein_g", 0.0))),
                    "fat_g": _round1(float(meal_values.get("fat_g", 0.0))),
                    "carbs_g": _round1(float(meal_values.get("carbs_g", 0.0))),
                    "exercise_calories": _round1(exercise_calories),
                    "net_calories": _round1(food_calories - exercise_calories),
                    "meals_count": int(meal_values.get("meals_count", 0)),
                    "workouts_count": int(workout_values.get("workouts_count", 0)),
                }
            )
            current += timedelta(days=1)
        return results

    def get_weekly_rollups(self, profile: ProfileConfig) -> list[dict[str, Any]]:
        rollups = self.build_daily_rollups()
        weeks: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in rollups:
            current = date.fromisoformat(item["date"])
            week_start = current - timedelta(days=current.weekday())
            weeks[week_start.isoformat()].append(item)

        results: list[dict[str, Any]] = []
        previous_average_weight: float | None = None
        for week_start in sorted(weeks):
            rows = weeks[week_start]
            weight_values = [row["weight_kg"] for row in rows if row["weight_kg"] is not None]
            calorie_values = [row["food_calories"] for row in rows if row["food_calories"] > 0]
            protein_values = [row["protein_g"] for row in rows if row["protein_g"] > 0]
            workouts = sum(row["workouts_count"] for row in rows)
            days_logged = sum(
                1
                for row in rows
                if row["meals_count"] > 0 or row["workouts_count"] > 0 or row["weight_kg"] is not None
            )
            average_weight = _round1(sum(weight_values) / len(weight_values)) if weight_values else None
            delta = (
                None
                if average_weight is None or previous_average_weight is None
                else _round1(average_weight - previous_average_weight)
            )
            average_food_calories = _round1(sum(calorie_values) / len(calorie_values)) if calorie_values else 0.0
            average_protein = _round1(sum(protein_values) / len(protein_values)) if protein_values else 0.0
            note_parts: list[str] = []
            if average_protein and average_protein < profile.preferences.protein_floor_g:
                note_parts.append("Белок ниже желаемого уровня")
            if workouts < profile.preferences.weekly_workout_goal:
                note_parts.append("Мало тренировок за неделю")
            if not note_parts:
                note_parts.append("Неделя выглядит стабильно")
            results.append(
                {
                    "week_start": week_start,
                    "average_weight_kg": average_weight,
                    "weight_delta_vs_previous_week_kg": delta,
                    "average_food_calories": average_food_calories,
                    "average_protein_g": average_protein,
                    "workouts": workouts,
                    "days_logged": days_logged,
                    "coach_note": "; ".join(note_parts),
                }
            )
            if average_weight is not None:
                previous_average_weight = average_weight
        return results

    def export_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        with self.connect() as connection:
            meals = [dict(row) for row in connection.execute("SELECT * FROM meals ORDER BY logged_at ASC").fetchall()]
            meal_components = [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM meal_components ORDER BY meal_id ASC, position ASC"
                ).fetchall()
            ]
            weights = [dict(row) for row in connection.execute("SELECT * FROM weights ORDER BY logged_at ASC").fetchall()]
            workouts = [dict(row) for row in connection.execute("SELECT * FROM workouts ORDER BY logged_at ASC").fetchall()]
        return {
            "meals": meals,
            "meal_components": meal_components,
            "weights": weights,
            "workouts": workouts,
        }
