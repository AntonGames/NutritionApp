from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    profile_path: Path
    db_path: Path
    workbook_path: Path
    upload_dir: Path
    api_key: str | None
    openai_api_key: str | None
    openai_model: str
    max_upload_mb: int
    export_on_write: bool

    @classmethod
    def from_env(cls, root: Path) -> "Settings":
        profile_path = root / os.getenv("NUTRITION_PROFILE_PATH", "config/profile.yaml")
        db_path = root / os.getenv("NUTRITION_DB_PATH", "data/nutrition.db")
        workbook_path = root / os.getenv(
            "NUTRITION_WORKBOOK_PATH",
            "data/exports/nutrition_tracker.xlsx",
        )
        upload_dir = root / os.getenv("NUTRITION_UPLOAD_DIR", "data/uploads")
        return cls(
            profile_path=profile_path,
            db_path=db_path,
            workbook_path=workbook_path,
            upload_dir=upload_dir,
            api_key=os.getenv("NUTRITION_API_KEY") or None,
            openai_api_key=os.getenv("NUTRITION_OPENAI_API_KEY") or None,
            openai_model=os.getenv("NUTRITION_OPENAI_MODEL", "gpt-4.1-mini"),
            max_upload_mb=int(os.getenv("NUTRITION_MAX_UPLOAD_MB", "8")),
            export_on_write=_env_bool("NUTRITION_EXPORT_ON_WRITE", True),
        )

    def ensure_directories(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.workbook_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

