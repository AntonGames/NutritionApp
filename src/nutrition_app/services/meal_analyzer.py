from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from openai import OpenAI

from ..profile import ProfileConfig
from ..schemas import MealAnalysis
from ..settings import Settings


class MealAnalyzerError(RuntimeError):
    """Raised when meal analysis fails."""


def _extract_output_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text
    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        payload = model_dump()
        if isinstance(payload, dict):
            if isinstance(payload.get("output_text"), str):
                return payload["output_text"]
            for output in payload.get("output", []):
                for content in output.get("content", []):
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        return text
    raise MealAnalyzerError("OpenAI response did not contain text output.")


def _strip_code_fence(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1])
    return cleaned


@dataclass(slots=True)
class OpenAIMealAnalyzer:
    settings: Settings
    profile: ProfileConfig

    def __post_init__(self) -> None:
        if not self.settings.openai_api_key:
            raise MealAnalyzerError(
                "NUTRITION_OPENAI_API_KEY is not configured. Add it to .env before using photo analysis."
            )
        self._client = OpenAI(api_key=self.settings.openai_api_key)

    def analyze(self, *, image_bytes: bytes, mime_type: str, note: str | None) -> MealAnalysis:
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        note_text = note.strip() if note else "No user note."
        system_prompt = (
            "You are a meal estimation engine. "
            "Estimate visible food components separately, slightly rounding calories up when uncertain. "
            "Return strict JSON only with keys: meal_name, overall_confidence, analysis_notes, components. "
            "Each component must have description, category, estimated_grams, calories, protein_g, fat_g, carbs_g. "
            "Use confidence values high, medium, or low. Never include markdown."
        )
        user_prompt = (
            f"User timezone: {self.profile.timezone}.\n"
            f"Daily targets: {self.profile.targets.daily_calories} kcal, "
            f"{self.profile.targets.protein_g} g protein, {self.profile.targets.fat_g} g fat, "
            f"{self.profile.targets.carbs_g} g carbs.\n"
            f"User note: {note_text}\n"
            "Analyze the meal photo. If the food is ambiguous, say so in analysis_notes and use medium or low confidence."
        )

        last_error: Exception | None = None
        for _ in range(3):
            try:
                response = self._client.responses.create(
                    model=self.settings.openai_model,
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": user_prompt},
                                {
                                    "type": "input_image",
                                    "image_url": f"data:{mime_type};base64,{image_base64}",
                                    "detail": "high",
                                },
                            ],
                        },
                    ],
                    text={"format": {"type": "json_object"}},
                    max_output_tokens=1200,
                )
                raw_text = _strip_code_fence(_extract_output_text(response))
                payload = json.loads(raw_text)
                analysis = MealAnalysis.model_validate(payload)
                if not analysis.components:
                    raise MealAnalyzerError("Model returned no meal components.")
                return analysis
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise MealAnalyzerError(f"Photo analysis failed: {last_error}") from last_error

