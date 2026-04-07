from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


ConfidenceLevel = Literal["high", "medium", "low"]


class MealComponent(BaseModel):
    description: str = Field(min_length=1)
    category: str | None = None
    estimated_grams: float | None = Field(default=None, ge=0)
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)


class MealAnalysis(BaseModel):
    meal_name: str = Field(default="Meal from photo", min_length=1)
    overall_confidence: ConfidenceLevel = "medium"
    analysis_notes: str | None = None
    components: list[MealComponent] = Field(min_length=1)

    @property
    def total_calories(self) -> float:
        return round(sum(component.calories for component in self.components), 1)

    @property
    def total_protein_g(self) -> float:
        return round(sum(component.protein_g for component in self.components), 1)

    @property
    def total_fat_g(self) -> float:
        return round(sum(component.fat_g for component in self.components), 1)

    @property
    def total_carbs_g(self) -> float:
        return round(sum(component.carbs_g for component in self.components), 1)


class ManualMealCreate(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    meal_name: str = Field(default="Manual meal", min_length=1)
    confidence: ConfidenceLevel = "medium"
    note: str | None = None
    source: str = "manual"
    components: list[MealComponent] = Field(min_length=1)


class WeightCreate(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    weight_kg: float = Field(gt=0, le=500)
    note: str | None = None
    source: str = "manual"


class WorkoutCreate(BaseModel):
    date: dt.date | None = None
    time: dt.time | None = None
    description: str = Field(min_length=1)
    duration_min: int | None = Field(default=None, ge=1, le=600)
    calories_burned: float = Field(ge=0)
    avg_hr: int | None = Field(default=None, ge=1, le=250)
    note: str | None = None
    source: str = "manual"


class DailyMacroSnapshot(BaseModel):
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


class DailySummary(BaseModel):
    date: str
    weight_kg: float | None = None
    food: DailyMacroSnapshot
    exercise_calories: float
    net_calories: float
    targets: DailyMacroSnapshot
    remaining: DailyMacroSnapshot
    meals_count: int
    workouts_count: int
    suggestions: list[str]


class WeeklySummaryRow(BaseModel):
    week_start: str
    average_weight_kg: float | None
    weight_delta_vs_previous_week_kg: float | None
    average_food_calories: float
    average_protein_g: float
    workouts: int
    days_logged: int
    coach_note: str


class RecentEvent(BaseModel):
    kind: Literal["meal", "weight", "workout"]
    logged_at: str
    title: str
    summary: str
