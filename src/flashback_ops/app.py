from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import load_settings
from .memory.hindsight_store import HindsightMemoryStore
from .memory.local_store import LocalMemoryStore
from .models import (
    AssistRequest,
    AssistResponse,
    FeedbackRequest,
    FeedbackResponse,
    IncidentCreateRequest,
    IncidentCreateResponse,
    SeedResponse,
    StatusResponse,
)
from .service import IncidentService


settings = load_settings()
local_store = LocalMemoryStore(settings.data_file)
if settings.memory_backend.lower() == "hindsight":
    store = HindsightMemoryStore(
        base_url=settings.hindsight_base_url,
        api_key=settings.hindsight_api_key,
        bank_id=settings.hindsight_bank_id,
        local_fallback=local_store,
    )
else:
    store = local_store
service = IncidentService(store=store)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/status", response_model=StatusResponse)
def status() -> StatusResponse:
    base = service.status()
    return StatusResponse(app=settings.app_name, **base)


@app.post("/api/incidents", response_model=IncidentCreateResponse)
def retain_incident(payload: IncidentCreateRequest) -> IncidentCreateResponse:
    return service.retain_incident(payload)


@app.post("/api/assist", response_model=AssistResponse)
def assist(payload: AssistRequest) -> AssistResponse:
    return service.assist(payload)


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest) -> FeedbackResponse:
    try:
        return service.feedback(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/seed", response_model=SeedResponse)
def seed() -> SeedResponse:
    return service.seed()


@app.get("/api/memory/stats")
def memory_stats() -> dict:
    return store.stats()


@app.get("/api/demo/scenarios")
def demo_scenarios() -> list[dict]:
    return service.demo_scenarios()
