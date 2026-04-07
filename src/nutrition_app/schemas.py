from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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


class ActionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ActionMealComponent(ActionModel):
    description: str = Field(min_length=1)
    component_type: str | None = Field(
        default="food",
        validation_alias=AliasChoices("componentType", "component_type"),
        serialization_alias="componentType",
    )
    category: str | None = None
    estimated_grams: float | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("estimatedGrams", "estimated_grams"),
        serialization_alias="estimatedGrams",
    )
    calories: float = Field(ge=0)
    protein_g: float = Field(
        ge=0,
        validation_alias=AliasChoices("protein", "protein_g"),
        serialization_alias="protein",
    )
    fat_g: float = Field(
        ge=0,
        validation_alias=AliasChoices("fat", "fat_g"),
        serialization_alias="fat",
    )
    carbs_g: float = Field(
        ge=0,
        validation_alias=AliasChoices("carbs", "carbs_g"),
        serialization_alias="carbs",
    )

    def to_meal_component(self) -> MealComponent:
        return MealComponent(
            description=self.description,
            category=self.category,
            estimated_grams=self.estimated_grams,
            calories=self.calories,
            protein_g=self.protein_g,
            fat_g=self.fat_g,
            carbs_g=self.carbs_g,
        )


class InitDayAction(ActionModel):
    action: Literal["init_day"]
    date: dt.date | None = None


class LogMealAction(ActionModel):
    action: Literal["log_meal"]
    date: dt.date | None = None
    time: dt.time | None = None
    meal_name: str = Field(
        default="Meal from ChatGPT",
        min_length=1,
        validation_alias=AliasChoices("mealName", "meal_name"),
        serialization_alias="mealName",
    )
    confidence: ConfidenceLevel = "medium"
    comment: str | None = None
    source: str = "gpt_action"
    components: list[ActionMealComponent] = Field(min_length=1)

    def to_manual_meal(self) -> ManualMealCreate:
        return ManualMealCreate(
            date=self.date,
            time=self.time,
            meal_name=self.meal_name,
            confidence=self.confidence,
            note=self.comment,
            source=self.source,
            components=[component.to_meal_component() for component in self.components],
        )


class LogWeightAction(ActionModel):
    action: Literal["log_weight"]
    date: dt.date | None = None
    time: dt.time | None = None
    weight_kg: float = Field(
        gt=0,
        le=500,
        validation_alias=AliasChoices("weight", "weightKg", "weight_kg"),
        serialization_alias="weight",
    )
    note: str | None = None
    source: str = "gpt_action"

    def to_weight_create(self) -> WeightCreate:
        return WeightCreate(
            date=self.date,
            time=self.time,
            weight_kg=self.weight_kg,
            note=self.note,
            source=self.source,
        )


class LogWorkoutAction(ActionModel):
    action: Literal["log_workout"]
    date: dt.date | None = None
    time: dt.time | None = None
    description: str = Field(min_length=1)
    duration_min: int | None = Field(
        default=None,
        ge=1,
        le=600,
        validation_alias=AliasChoices("durationMin", "duration_min"),
        serialization_alias="durationMin",
    )
    calories_burned: float = Field(
        ge=0,
        validation_alias=AliasChoices("exerciseCalories", "calories_burned", "caloriesBurned"),
        serialization_alias="exerciseCalories",
    )
    avg_hr: int | None = Field(
        default=None,
        ge=1,
        le=250,
        validation_alias=AliasChoices("avgHr", "avg_hr"),
        serialization_alias="avgHr",
    )
    note: str | None = None
    source: str = "gpt_action"

    def to_workout_create(self) -> WorkoutCreate:
        return WorkoutCreate(
            date=self.date,
            time=self.time,
            description=self.description,
            duration_min=self.duration_min,
            calories_burned=self.calories_burned,
            avg_hr=self.avg_hr,
            note=self.note,
            source=self.source,
        )


class ActionSummary(ActionModel):
    date: str
    weight: float | None = None
    calorie_target: float = Field(serialization_alias="calorieTarget")
    protein_target: float = Field(serialization_alias="proteinTarget")
    fat_target: float = Field(serialization_alias="fatTarget")
    carb_target: float = Field(serialization_alias="carbTarget")
    food_calories: float = Field(serialization_alias="foodCalories")
    protein: float
    fat: float
    carbs: float
    exercise_calories: float = Field(serialization_alias="exerciseCalories")
    net_calories: float = Field(serialization_alias="netCalories")
    calories_left: float = Field(serialization_alias="caloriesLeft")
    protein_left: float = Field(serialization_alias="proteinLeft")
    fat_left: float = Field(serialization_alias="fatLeft")
    carb_left: float = Field(serialization_alias="carbLeft")
    meals_count: int = Field(serialization_alias="mealsCount")
    workouts_count: int = Field(serialization_alias="workoutsCount")
    suggestions: list[str]


class ActionResponse(ActionModel):
    ok: bool = True
    action: Literal["init_day", "log_meal", "log_weight", "log_workout", "summary"]
    date: str
    entity_id: str | None = Field(default=None, serialization_alias="entityId")
    summary: ActionSummary
