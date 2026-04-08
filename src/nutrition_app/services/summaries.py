from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ..profile import ProfileConfig
from ..schemas import (
    DailyHistoryPoint,
    DailyMacroSnapshot,
    DailySummary,
    StatsDashboard,
    StatsHighlights,
    WeeklySummaryRow,
)
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

    def build_history(self, *, days: int, end_date: date) -> list[DailyHistoryPoint]:
        span = max(1, min(days, 180))
        start_date = end_date - timedelta(days=span - 1)
        targets = self.profile.targets
        rollups = self.database.build_daily_rollups(start_date=start_date, end_date=end_date)
        history: list[DailyHistoryPoint] = []
        for row in rollups:
            current = date.fromisoformat(row["date"])
            history.append(
                DailyHistoryPoint(
                    date=row["date"],
                    label=current.strftime("%d.%m"),
                    weight_kg=row["weight_kg"],
                    food_calories=row["food_calories"],
                    exercise_calories=row["exercise_calories"],
                    net_calories=row["net_calories"],
                    protein_g=row["protein_g"],
                    fat_g=row["fat_g"],
                    carbs_g=row["carbs_g"],
                    meals_count=row["meals_count"],
                    workouts_count=row["workouts_count"],
                    calorie_target=targets.daily_calories,
                    protein_target=targets.protein_g,
                    fat_target=targets.fat_g,
                    carb_target=targets.carbs_g,
                    calorie_delta=_round1(row["net_calories"] - targets.daily_calories),
                    protein_delta=_round1(row["protein_g"] - targets.protein_g),
                    logged=bool(row["meals_count"] or row["workouts_count"] or row["weight_kg"] is not None),
                )
            )
        return history

    def build_stats_dashboard(self, *, days: int, end_date: date) -> StatsDashboard:
        history = self.build_history(days=days, end_date=end_date)
        weekly = self.build_weekly_summary()[-8:]
        today_summary = self.build_daily_summary(end_date)
        logged_history = [item for item in history if item.logged]
        weight_history = [item.weight_kg for item in history if item.weight_kg is not None]
        highlights = StatsHighlights(
            period_days=max(1, min(days, 180)),
            logged_days=len(logged_history),
            average_food_calories=_round1(
                sum(item.food_calories for item in logged_history) / len(logged_history)
            )
            if logged_history
            else 0.0,
            average_net_calories=_round1(
                sum(item.net_calories for item in logged_history) / len(logged_history)
            )
            if logged_history
            else 0.0,
            average_protein_g=_round1(
                sum(item.protein_g for item in logged_history) / len(logged_history)
            )
            if logged_history
            else 0.0,
            workout_sessions=sum(item.workouts_count for item in history),
            average_weight_kg=_round1(sum(weight_history) / len(weight_history)) if weight_history else None,
            weight_change_kg=_round1(weight_history[-1] - weight_history[0]) if len(weight_history) >= 2 else None,
        )
        focus = self.build_period_focus(history)
        return StatsDashboard(
            today=today_summary,
            history=history,
            weekly=weekly,
            focus=focus,
            highlights=highlights,
        )

    def build_suggestions(self, target_date: date) -> list[str]:
        rollups = self.database.build_daily_rollups(
            start_date=target_date - timedelta(days=13),
            end_date=target_date,
        )
        current = next((item for item in rollups if item["date"] == target_date.isoformat()), None)
        if current is None:
            return ["Сегодня еще нет записей. Начни с приема пищи, веса или тренировки, чтобы появился план на день."]

        suggestions: list[str] = []
        targets = self.profile.targets
        preferences = self.profile.preferences
        net_calories = _round1(current["food_calories"] - current["exercise_calories"])
        calorie_gap = _round1(targets.daily_calories - net_calories)
        protein_gap = _round1(preferences.protein_floor_g - current["protein_g"])

        if protein_gap > 0:
            suggestions.append(
                f"Белка не хватает примерно на {protein_gap} г. Самый быстрый добор сегодня: творог, йогурт, курица, тунец или протеин."
            )

        if calorie_gap < -120:
            suggestions.append(
                f"Сегодня уже перебор примерно на {abs(calorie_gap)} ккал. Следующий прием лучше сделать вокруг постного белка и овощей без десерта и жидких калорий."
            )
        elif current["food_calories"] > 0 and calorie_gap > max(250.0, targets.daily_calories * 0.2):
            suggestions.append(
                f"До лимита остается около {calorie_gap} ккал. Лучше оставить их на один нормальный прием пищи, а не расходовать на случайные перекусы."
            )

        if current["fat_g"] > targets.fat_g * 1.12:
            suggestions.append(
                "Жиры уже вышли выше плана. До конца дня смести акцент на более постные продукты: птицу, рыбу, йогурт, творог, овощи."
            )

        if current["carbs_g"] > targets.carbs_g * 1.12 and current["protein_g"] < targets.protein_g:
            suggestions.append(
                "Углеводы уже обгоняют белок. Следующий прием лучше собрать без сладкого и выпечки, с упором на белок и объемные овощи."
            )

        week_slice = rollups[-7:]
        logged_week = [
            item for item in week_slice if item["meals_count"] > 0 or item["workouts_count"] > 0 or item["weight_kg"] is not None
        ]
        if logged_week:
            average_net = _round1(sum(item["net_calories"] for item in logged_week) / len(logged_week))
            average_protein = _round1(sum(item["protein_g"] for item in logged_week) / len(logged_week))
            if average_net > targets.daily_calories + 120:
                suggestions.append(
                    f"Средняя неделя идет около {average_net} ккал чистыми, это выше цели {targets.daily_calories}. Для снижения веса попробуй убрать 150-250 ккал из самых незаметных калорий."
                )
            elif average_net < max(targets.daily_calories - 550, targets.daily_calories * 0.72):
                suggestions.append(
                    "Средняя неделя слишком низкая по калориям. Так сложнее держать режим и белок; лучше дефицит делать мягче и стабильнее."
                )
            if average_protein < preferences.protein_floor_g - 15:
                suggestions.append(
                    f"Средний белок за неделю около {average_protein} г. Для удержания мышц стоит стабильно держаться ближе к {preferences.protein_floor_g} г."
                )

        weight_values = [item["weight_kg"] for item in week_slice if item["weight_kg"] is not None]
        if len(weight_values) >= 2:
            weight_delta = _round1(weight_values[-1] - weight_values[0])
            if weight_delta > 0.3:
                suggestions.append(
                    "Вес за неделю подрос. Сначала проверь калорийно плотные продукты: выпечку, сыр, орехи, соусы и сладкие напитки."
                )
            elif weight_delta < -1.2:
                suggestions.append(
                    "Вес снижается быстро. Следи, чтобы дефицит не был слишком жестким, и не отпускай белок."
                )

        workout_total = sum(item["workouts_count"] for item in week_slice)
        if workout_total < preferences.weekly_workout_goal and len(suggestions) < 4:
            left = preferences.weekly_workout_goal - workout_total
            suggestions.append(
                f"Для недельной цели не хватает еще {left} тренировок. Даже короткая ходьба добавит расход и поможет держать аппетит под контролем."
            )

        if not suggestions:
            suggestions.append(
                "По цифрам день выглядит ровно: лимит под контролем, белок близко к цели. Держи тот же шаблон приемов пищи."
            )

        return suggestions[:4]

    def build_period_focus(self, history: list[DailyHistoryPoint]) -> list[str]:
        if not history:
            return ["Пока нет данных за выбранный период. Как только появятся записи, здесь будет видна динамика по весу, калориям и белку."]

        logged_history = [item for item in history if item.logged]
        if not logged_history:
            return ["За выбранный период нет полноценных записей. Начни логировать еду и вес, чтобы появились графики и тренды."]

        targets = self.profile.targets
        preferences = self.profile.preferences
        focus: list[str] = []
        average_net = _round1(sum(item.net_calories for item in logged_history) / len(logged_history))
        average_protein = _round1(sum(item.protein_g for item in logged_history) / len(logged_history))
        average_fat = _round1(sum(item.fat_g for item in logged_history) / len(logged_history))
        workouts = sum(item.workouts_count for item in history)
        weight_values = [item.weight_kg for item in history if item.weight_kg is not None]

        if average_net > targets.daily_calories + 120:
            focus.append(
                f"Средняя чистая калорийность за период около {average_net} ккал, это выше вашей цели {targets.daily_calories}. Самый прямой рычаг сейчас — убрать 150-250 ккал в день из самых незаметных источников."
            )
        elif average_net < max(targets.daily_calories - 550, targets.daily_calories * 0.72):
            focus.append(
                "Средняя калорийность получилась очень низкой. Для более устойчивого темпа лучше держать дефицит мягче и не проваливаться слишком низко."
            )
        else:
            focus.append(
                f"Средняя чистая калорийность держится около {average_net} ккал. Это достаточно близко к цели и дает хорошую базу для ровного темпа."
            )

        if average_protein < preferences.protein_floor_g:
            deficit = _round1(preferences.protein_floor_g - average_protein)
            focus.append(
                f"Средний белок ниже желаемого примерно на {deficit} г в день. Проще всего исправить это одним стабильным белковым приемом пищи каждый день."
            )
        else:
            focus.append(
                f"Средний белок около {average_protein} г. Это уже поддерживает нормальную сытость и помогает не терять мышечную массу."
            )

        if average_fat > targets.fat_g * 1.12:
            focus.append(
                "Жиры регулярно выходят выше плана. Обычно это скрытые калории из сыра, масла, орехов, выпечки и жирных соусов — там проще всего найти запас."
            )

        if len(weight_values) >= 2:
            change = _round1(weight_values[-1] - weight_values[0])
            if change > 0.3:
                focus.append(
                    f"Вес за период вырос на {change} кг. Стоит сначала проверить среднюю калорийность недели и калорийно плотные перекусы."
                )
            elif change < -1.2:
                focus.append(
                    f"Вес снизился на {abs(change)} кг. Темп быстрый; если есть усталость или сильный голод, лучше немного смягчить дефицит."
                )
            else:
                focus.append(
                    f"Вес за период изменился на {change} кг. Это выглядит как достаточно ровная динамика без резких скачков."
                )

        scaled_goal = max(1, round(preferences.weekly_workout_goal * max(1, len(history)) / 7))
        if workouts < scaled_goal:
            focus.append(
                f"Тренировок за период {workouts}, а ориентир около {scaled_goal}. Дополнительная ходьба или 1-2 короткие сессии заметно улучшат расход."
            )
        else:
            focus.append(
                f"С активностью все неплохо: {workouts} тренировок за период. Это помогает удерживать дефицит без лишнего урезания еды."
            )

        return focus[:4]
