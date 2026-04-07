from __future__ import annotations

import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .profile import ProfileConfig
from .schemas import ManualMealCreate, WeightCreate, WorkoutCreate
from .services.meal_analyzer import MealAnalyzerError, OpenAIMealAnalyzer
from .services.summaries import SummaryService
from .services.workbook import WorkbookExporter
from .settings import Settings
from .storage import Database


def _root_dir() -> Path:
    configured_root = os.getenv("NUTRITION_APP_ROOT")
    if configured_root:
        return Path(configured_root).resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "config").exists() or (cwd / "src").exists():
        return cwd
    return Path(__file__).resolve().parents[2]


def _local_zone(profile: ProfileConfig) -> ZoneInfo:
    try:
        return ZoneInfo(profile.timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _resolve_timestamp(profile: ProfileConfig, *, incoming_date: date | None, incoming_time: time | None) -> datetime:
    zone = _local_zone(profile)
    now = datetime.now(tz=zone)
    return datetime.combine(incoming_date or now.date(), incoming_time or now.timetz().replace(tzinfo=None), tzinfo=zone)


@dataclass(slots=True)
class AppState:
    settings: Settings
    profile: ProfileConfig
    database: Database
    summary_service: SummaryService
    workbook_exporter: WorkbookExporter
    templates: Jinja2Templates

    def ensure_workbook(self) -> Path:
        return self.workbook_exporter.export(self.settings.workbook_path)


def create_state(root: Path | None = None) -> AppState:
    root = root or _root_dir()
    settings = Settings.from_env(root)
    settings.ensure_directories()
    example_path = root / "config/profile.example.yaml"
    profile_path = settings.profile_path if settings.profile_path.exists() else example_path
    if not profile_path.exists():
        raise RuntimeError(
            f"Profile config not found at {settings.profile_path}. Copy {example_path} to {settings.profile_path} first."
        )
    profile = ProfileConfig.load(profile_path)
    database = Database(settings.db_path)
    database.initialize()
    summary_service = SummaryService(database=database, profile=profile)
    workbook_exporter = WorkbookExporter(database=database, profile=profile, summary_service=summary_service)
    templates = Jinja2Templates(directory=str(root / "src/nutrition_app/templates"))
    return AppState(
        settings=settings,
        profile=profile,
        database=database,
        summary_service=summary_service,
        workbook_exporter=workbook_exporter,
        templates=templates,
    )


def create_app(state: AppState | None = None) -> FastAPI:
    app = FastAPI(
        title="Nutrition Tracker API",
        version="0.1.0",
        description="Self-hosted meal photo logging with Excel export and Home Assistant hooks.",
    )
    state = state or create_state()
    app.state.nutrition = state

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_path = _root_dir() / "src/nutrition_app/static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    def get_state() -> AppState:
        return app.state.nutrition

    def require_api_key(
        x_api_key: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
        state: AppState = Depends(get_state),
    ) -> None:
        expected = state.settings.api_key
        if not expected:
            return
        bearer = None
        if authorization and authorization.lower().startswith("bearer "):
            bearer = authorization.split(" ", 1)[1].strip()
        provided = x_api_key or bearer
        if provided != expected:
            raise HTTPException(status_code=401, detail="Invalid API key.")

    def export_if_enabled(state: AppState) -> None:
        if state.settings.export_on_write:
            state.ensure_workbook()

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request, state: AppState = Depends(get_state)) -> HTMLResponse:
        today = datetime.now(tz=_local_zone(state.profile)).date()
        summary = state.summary_service.build_daily_summary(today)
        recent_events = state.database.get_recent_events()
        return state.templates.TemplateResponse(
            request,
            "index.html",
            {
                "profile": state.profile,
                "summary": summary,
                "recent_events": recent_events,
                "workbook_path": state.settings.workbook_path.name,
                "api_key_required": bool(state.settings.api_key),
            },
        )

    @app.get("/api/health")
    async def health(state: AppState = Depends(get_state)) -> dict[str, Any]:
        return {
            "ok": True,
            "timezone": state.profile.timezone,
            "db_path": str(state.settings.db_path),
            "workbook_path": str(state.settings.workbook_path),
        }

    @app.get("/api/summary/daily")
    async def daily_summary(target_date: str | None = None, state: AppState = Depends(get_state)) -> dict[str, Any]:
        zone = _local_zone(state.profile)
        resolved_date = date.fromisoformat(target_date) if target_date else datetime.now(tz=zone).date()
        summary = state.summary_service.build_daily_summary(resolved_date)
        return summary.model_dump()

    @app.get("/api/summary/weekly")
    async def weekly_summary(state: AppState = Depends(get_state)) -> list[dict[str, Any]]:
        return [item.model_dump() for item in state.summary_service.build_weekly_summary()]

    @app.get("/api/events/recent")
    async def recent_events(state: AppState = Depends(get_state)) -> list[dict[str, Any]]:
        return [item.model_dump() for item in state.database.get_recent_events()]

    @app.get("/api/export/workbook")
    async def download_workbook(state: AppState = Depends(get_state)) -> FileResponse:
        path = state.ensure_workbook()
        return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.post("/api/meals/photo", dependencies=[Depends(require_api_key)])
    async def upload_meal_photo(
        photo: UploadFile = File(...),
        note: str | None = Form(default=None),
        logged_date: str | None = Form(default=None),
        logged_time: str | None = Form(default=None),
        state: AppState = Depends(get_state),
    ) -> dict[str, Any]:
        mime_type = photo.content_type or mimetypes.guess_type(photo.filename or "photo.jpg")[0] or "image/jpeg"
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are supported.")
        file_bytes = await photo.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(file_bytes) > state.settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Uploaded image is too large.")

        try:
            analyzer = OpenAIMealAnalyzer(settings=state.settings, profile=state.profile)
            analysis = analyzer.analyze(image_bytes=file_bytes, mime_type=mime_type, note=note)
        except MealAnalyzerError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        resolved_date = date.fromisoformat(logged_date) if logged_date else None
        resolved_time = time.fromisoformat(logged_time) if logged_time else None
        logged_at = _resolve_timestamp(state.profile, incoming_date=resolved_date, incoming_time=resolved_time)
        extension = Path(photo.filename or "upload.jpg").suffix or ".jpg"
        relative_path = Path(logged_at.strftime("%Y/%m/%d")) / f"{uuid.uuid4()}{extension.lower()}"
        full_path = state.settings.upload_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_bytes)
        meal_id = state.database.add_analyzed_meal(
            analysis,
            logged_at=logged_at,
            note=note,
            source="photo",
            image_path=str(relative_path).replace("\\", "/"),
        )
        export_if_enabled(state)
        summary = state.summary_service.build_daily_summary(logged_at.date())
        return {
            "ok": True,
            "meal_id": meal_id,
            "analysis": analysis.model_dump(),
            "daily_summary": summary.model_dump(),
        }

    @app.post("/api/meals/manual", dependencies=[Depends(require_api_key)])
    async def create_manual_meal(payload: ManualMealCreate, state: AppState = Depends(get_state)) -> dict[str, Any]:
        logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
        meal_id = state.database.add_manual_meal(payload, logged_at=logged_at)
        export_if_enabled(state)
        summary = state.summary_service.build_daily_summary(logged_at.date())
        return {"ok": True, "meal_id": meal_id, "daily_summary": summary.model_dump()}

    @app.post("/api/weights", dependencies=[Depends(require_api_key)])
    async def create_weight(payload: WeightCreate, state: AppState = Depends(get_state)) -> dict[str, Any]:
        logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
        weight_id = state.database.add_weight(payload, logged_at=logged_at)
        export_if_enabled(state)
        summary = state.summary_service.build_daily_summary(logged_at.date())
        return {"ok": True, "weight_id": weight_id, "daily_summary": summary.model_dump()}

    @app.post("/api/workouts", dependencies=[Depends(require_api_key)])
    async def create_workout(payload: WorkoutCreate, state: AppState = Depends(get_state)) -> dict[str, Any]:
        logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
        workout_id = state.database.add_workout(payload, logged_at=logged_at)
        export_if_enabled(state)
        summary = state.summary_service.build_daily_summary(logged_at.date())
        return {"ok": True, "workout_id": workout_id, "daily_summary": summary.model_dump()}

    return app


app = create_app()
