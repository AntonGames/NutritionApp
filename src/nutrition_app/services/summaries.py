from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ..profile import ProfileConfig
from ..schemas import DailyMacroSnapshot, DailySummary, WeeklySummaryRow
from ..storage import Database


def _round1(value: float) -> float:
    return round(float(value), 1)


@dataclass(slots=True)
class SummaryService:
    database: Database
    profile: ProfileConfig

    def build_daily_summary(self, target_date: date) -> DailySummary:
        date_key = target_date.isoformat()
        meals = self.database.get_day_meals(date_key)
        workouts = self.database.get_day_workouts(date_key)
        weight = self.database.get_latest_weight_on_or_before(date_key)
        food_calories = _round1(sum(item["total_calories"] for item in meals))
        protein_total = _round1(sum(item["total_protein_g"] for item in meals))
        fat_total = _round1(sum(item["total_fat_g"] for item in meals))
        carbs_total = _round1(sum(item["total_carbs_g"] for item in meals))
        exercise_calories = _round1(sum(item["calories_burned"] for item in workouts))
        targets = self.profile.targets
        remaining_calories = _round1(targets.daily_calories - (food_calories - exercise_calories))
        remaining_protein = _round1(targets.protein_g - protein_total)
        remaining_fat = _round1(targets.fat_g - fat_total)
        remaining_carbs = _round1(targets.carbs_g - carbs_total)
        suggestions = self.build_suggestions(target_date)
        return DailySummary(
            date=date_key,
            weight_kg=weight,
            food=DailyMacroSnapshot(
                calories=food_calories,
                protein_g=protein_total,
                fat_g=fat_total,
                carbs_g=carbs_total,
            ),
            exercise_calories=exercise_calories,
            net_calories=_round1(food_calories - exercise_calories),
            targets=DailyMacroSnapshot(
                calories=targets.daily_calories,
                protein_g=targets.protein_g,
                fat_g=targets.fat_g,
                carbs_g=targets.carbs_g,
            ),
            remaining=DailyMacroSnapshot(
                calories=remaining_calories,
                protein_g=remaining_protein,
                fat_g=remaining_fat,
                carbs_g=remaining_carbs,
            ),
            meals_count=len(meals),
            workouts_count=len(workouts),
            suggestions=suggestions,
        )

    def build_weekly_summary(self) -> list[WeeklySummaryRow]:
        return [
            WeeklySummaryRow.model_validate(row)
            for row in self.database.get_weekly_rollups(self.profile)
        ]

    def build_suggestions(self, target_date: date) -> list[str]:
        rollups = self.database.build_daily_rollups(
            start_date=target_date - timedelta(days=13),
            end_date=target_date,
        )
        current = next((item for item in rollups if item["date"] == target_date.isoformat()), None)
        suggestions: list[str] = []
        if current is None:
            return ["Сегодня пока нет записей. Начни с фото еды, веса или тренировки."]

        targets = self.profile.targets
        preferences = self.profile.preferences

        if current["protein_g"] < preferences.protein_floor_g:
            deficit = _round1(preferences.protein_floor_g - current["protein_g"])
            suggestions.append(
                f"Добери еще примерно {deficit} г белка: творог, греческий йогурт, курица или протеин."
            )

        if current["food_calories"] > targets.daily_calories * 1.1:
            suggestions.append("Калории вышли выше плана. Завтра лучше урезать жидкие калории и соусы.")
        elif 0 < current["food_calories"] < targets.daily_calories * 0.65:
            suggestions.append("Калорий пока мало. Проверь, что приемы пищи внесены полностью, чтобы не терять данные.")

        week_slice = rollups[-7:]
        workout_total = sum(item["workouts_count"] for item in week_slice)
        if workout_total < preferences.weekly_workout_goal:
            left = preferences.weekly_workout_goal - workout_total
            suggestions.append(f"До недельной цели не хватает {left} тренировок. Даже 30-минутная прогулка уже поможет.")

        weight_values = [item["weight_kg"] for item in week_slice if item["weight_kg"] is not None]
        if len(weight_values) >= 2:
            weight_delta = _round1(weight_values[-1] - weight_values[0])
            if weight_delta > 0.4:
                suggestions.append("Вес за неделю идет вверх. Самый простой рычаг: стабилизировать выходные и белок.")
            elif weight_delta < -1.2:
                suggestions.append("Снижение веса идет быстро. Проверь самочувствие и не режь калории слишком агрессивно.")

        logged_days = sum(1 for item in week_slice if item["meals_count"] or item["workouts_count"] or item["weight_kg"])
        if logged_days < 5:
            suggestions.append("Главное улучшение сейчас — регулярность логирования. Старайся не пропускать дни.")

        if not suggestions:
            suggestions.append("Темп выглядит ровным. Продолжай держать белок и не усложняй систему без необходимости.")

        return suggestions[:4]
