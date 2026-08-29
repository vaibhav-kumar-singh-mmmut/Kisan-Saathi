"""
Kisan Saathi — FastAPI entry-point (Phase 0 scaffold)
Run with: uvicorn main:app --reload

MVP Module Map (high-level architecture reference):
  M1 — AI Crop Doctor        : image capture, ML inference, geotag   (Phase 3-5)
  M2 — Crop Risk Radar       : zone scoring, weather/flood risk       (Phase 8-10)
  M3 — Smart Advisory        : pathogen-branched advisory             (Phase 5-6)
  M4 — Geo Disease Hotspot Maps : officer map, PostGIS hotspots       (Phase 8-9)
  M5 — Expert Validation Loop: expert queue, retraining pipeline      (Phase 7)

See PRODUCTION_WORKFLOW.md § MVP Module Map and AI_AGENT_BUILD_PROMPT.md for
the full phase checklist.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router


from app.core.database import Base, engine
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(f"[Kisan Saathi] Starting in '{settings.APP_ENV}' mode …")
    Base.metadata.create_all(bind=engine)
    yield
    print("[Kisan Saathi] Shutting down …")


app = FastAPI(
    title="Kisan Saathi API",
    description=(
        "Fasal Rakshak — AI-powered crop-disease surveillance, "
        "advisory, and subsidy management for UP districts."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Phase 2+  : auth, jurisdiction-aware filtering
# M1 routes : /crop-scan, /disease-reports      (Phase 3-5)
# M2 routes : /zone-status, /weather            (Phase 8-10)
# M3 routes : /advisory                         (Phase 5-6)
# M4 routes : /hotspot-map                      (Phase 8-9)
# M5 routes : /expert-queue                     (Phase 7)
app.include_router(api_router, prefix="/api/v1")


# ── Health (open, no auth) ────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "version": app.version, "env": settings.APP_ENV}


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["meta"])
async def root():
    return {"message": "Kisan Saathi API is running. See /docs for endpoints."}
