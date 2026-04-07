from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str = "User"
    height_cm: int | None = None
    age: int | None = None
    sex: str | None = None
    start_weight_kg: float | None = None
    goal_weight_kg: float | None = None


class NutritionTargets(BaseModel):
    daily_calories: float = 2400
    protein_g: float = 180
    fat_g: float = 75
    carbs_g: float = 250


class Preferences(BaseModel):
    protein_floor_g: float = 170
    weekly_workout_goal: int = 3
    weekly_weight_change_goal_kg: float = -0.5


class ProfileConfig(BaseModel):
    timezone: str = "Europe/Vilnius"
    user: UserProfile = Field(default_factory=UserProfile)
    targets: NutritionTargets = Field(default_factory=NutritionTargets)
    preferences: Preferences = Field(default_factory=Preferences)

    @classmethod
    def load(cls, path: Path) -> "ProfileConfig":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)

