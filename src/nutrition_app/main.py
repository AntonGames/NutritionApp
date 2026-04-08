from __future__ import annotations

import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .actions_openapi import build_actions_openapi
from .profile import ProfileConfig
from .schemas import (
    ActionResponse,
    ActionSummary,
    DailySummary,
    InitDayAction,
    LogMealAction,
    LogWeightAction,
    LogWorkoutAction,
    ManualMealCreate,
    StatsDashboard,
    WeightCreate,
    WorkoutCreate,
)
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


def _normalize_lang(lang: str | None) -> str:
    return "en" if (lang or "").lower().startswith("en") else "ru"


def _build_action_summary(summary: DailySummary) -> ActionSummary:
    return ActionSummary(
        date=summary.date,
        weight=summary.weight_kg,
        calorie_target=summary.targets.calories,
        protein_target=summary.targets.protein_g,
        fat_target=summary.targets.fat_g,
        carb_target=summary.targets.carbs_g,
        food_calories=summary.food.calories,
        protein=summary.food.protein_g,
        fat=summary.food.fat_g,
        carbs=summary.food.carbs_g,
        exercise_calories=summary.exercise_calories,
        net_calories=summary.net_calories,
        calories_left=summary.remaining.calories,
        protein_left=summary.remaining.protein_g,
        fat_left=summary.remaining.fat_g,
        carb_left=summary.remaining.carbs_g,
        meals_count=summary.meals_count,
        workouts_count=summary.workouts_count,
        suggestions=summary.suggestions,
    )


def _build_stats_payload(state: "AppState", *, end_date: date | None = None, days: int = 30, lang: str = "ru") -> StatsDashboard:
    zone = _local_zone(state.profile)
    resolved_end = end_date or datetime.now(tz=zone).date()
    safe_days = max(7, min(days, 180))
    return state.summary_service.build_stats_dashboard(days=safe_days, end_date=resolved_end, lang=_normalize_lang(lang))


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
    template_dir = root / "src/nutrition_app/templates"
    if not template_dir.exists():
        template_dir = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(template_dir))
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
        version="0.2.0",
        description="Self-hosted nutrition tracking with GPT Actions, Excel export, and Home Assistant hooks.",
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
    async def home(request: Request, lang: str | None = None, state: AppState = Depends(get_state)) -> HTMLResponse:
        today = datetime.now(tz=_local_zone(state.profile)).date()
        ui_lang = _normalize_lang(lang)
        summary = state.summary_service.build_daily_summary(today, lang=ui_lang)
        recent_events = state.database.get_recent_events()
        dashboard = _build_stats_payload(state, end_date=today, days=14, lang=ui_lang)
        return state.templates.TemplateResponse(
            request,
            "index.html",
            {
                "profile": state.profile,
                "summary": summary,
                "recent_events": recent_events,
                "dashboard_data": dashboard.model_dump(),
                "workbook_path": state.settings.workbook_path.name,
                "workbook_url": "/api/export/workbook",
                "stats_url": "/stats",
                "schema_url": "/api/actions/openapi.yaml",
                "api_key_required": bool(state.settings.api_key),
                "photo_upload_enabled": bool(state.settings.openai_api_key),
                "active_page": "home",
                "ui_lang": ui_lang,
            },
        )

    @app.get("/stats", response_class=HTMLResponse)
    async def stats_page(request: Request, lang: str | None = None, state: AppState = Depends(get_state)) -> HTMLResponse:
        today = datetime.now(tz=_local_zone(state.profile)).date()
        ui_lang = _normalize_lang(lang)
        dashboard = _build_stats_payload(state, end_date=today, days=30, lang=ui_lang)
        return state.templates.TemplateResponse(
            request,
            "stats.html",
            {
                "profile": state.profile,
                "dashboard_data": dashboard.model_dump(),
                "workbook_url": "/api/export/workbook",
                "schema_url": "/api/actions/openapi.yaml",
                "api_key_required": bool(state.settings.api_key),
                "active_page": "stats",
                "ui_lang": ui_lang,
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
    async def daily_summary(target_date: str | None = None, lang: str | None = None, state: AppState = Depends(get_state)) -> dict[str, Any]:
        zone = _local_zone(state.profile)
        resolved_date = date.fromisoformat(target_date) if target_date else datetime.now(tz=zone).date()
        summary = state.summary_service.build_daily_summary(resolved_date, lang=_normalize_lang(lang))
        return summary.model_dump()

    @app.get("/api/summary/weekly")
    async def weekly_summary(lang: str | None = None, state: AppState = Depends(get_state)) -> list[dict[str, Any]]:
        return [item.model_dump() for item in state.summary_service.build_weekly_summary(lang=_normalize_lang(lang))]

    @app.get("/api/stats/dashboard")
    async def stats_dashboard(days: int = 30, target_date: str | None = None, lang: str | None = None, state: AppState = Depends(get_state)) -> dict[str, Any]:
        zone = _local_zone(state.profile)
        resolved_date = date.fromisoformat(target_date) if target_date else datetime.now(tz=zone).date()
        dashboard = _build_stats_payload(state, end_date=resolved_date, days=days, lang=_normalize_lang(lang))
        return dashboard.model_dump()

    @app.get("/api/events/recent")
    async def recent_events(state: AppState = Depends(get_state)) -> list[dict[str, Any]]:
        return [item.model_dump() for item in state.database.get_recent_events()]

    @app.get("/api/export/workbook")
    async def download_workbook(state: AppState = Depends(get_state)) -> FileResponse:
        path = state.ensure_workbook()
        return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.get("/api/actions/openapi.yaml", response_class=PlainTextResponse)
    async def actions_openapi(request: Request) -> PlainTextResponse:
        server_url = str(request.base_url).rstrip("/")
        document = build_actions_openapi(server_url)
        return PlainTextResponse(document, media_type="application/yaml")

    @app.get("/api/actions/summary", response_model=ActionResponse, dependencies=[Depends(require_api_key)])
    async def action_summary(target_date: str | None = None, lang: str | None = None, state: AppState = Depends(get_state)) -> ActionResponse:
        zone = _local_zone(state.profile)
        resolved_date = date.fromisoformat(target_date) if target_date else datetime.now(tz=zone).date()
        summary = state.summary_service.build_daily_summary(resolved_date, lang=_normalize_lang(lang))
        return ActionResponse(action="summary", date=summary.date, summary=_build_action_summary(summary))

    @app.post("/api/actions", response_model=ActionResponse, dependencies=[Depends(require_api_key)])
    async def post_action(
        payload: Annotated[
            InitDayAction | LogMealAction | LogWeightAction | LogWorkoutAction,
            Body(discriminator="action"),
        ],
        state: AppState = Depends(get_state),
    ) -> ActionResponse:
        if isinstance(payload, InitDayAction):
            zone = _local_zone(state.profile)
            resolved_date = payload.date or datetime.now(tz=zone).date()
            summary = state.summary_service.build_daily_summary(resolved_date)
            return ActionResponse(action="init_day", date=summary.date, summary=_build_action_summary(summary))

        if isinstance(payload, LogMealAction):
            logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
            meal_id = state.database.add_manual_meal(payload.to_manual_meal(), logged_at=logged_at)
            export_if_enabled(state)
            summary = state.summary_service.build_daily_summary(logged_at.date())
            return ActionResponse(
                action="log_meal",
                date=summary.date,
                entity_id=meal_id,
                summary=_build_action_summary(summary),
            )

        if isinstance(payload, LogWeightAction):
            logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
            weight_id = state.database.add_weight(payload.to_weight_create(), logged_at=logged_at)
            export_if_enabled(state)
            summary = state.summary_service.build_daily_summary(logged_at.date())
            return ActionResponse(
                action="log_weight",
                date=summary.date,
                entity_id=weight_id,
                summary=_build_action_summary(summary),
            )

        logged_at = _resolve_timestamp(state.profile, incoming_date=payload.date, incoming_time=payload.time)
        workout_id = state.database.add_workout(payload.to_workout_create(), logged_at=logged_at)
        export_if_enabled(state)
        summary = state.summary_service.build_daily_summary(logged_at.date())
        return ActionResponse(
            action="log_workout",
            date=summary.date,
            entity_id=workout_id,
            summary=_build_action_summary(summary),
        )

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
