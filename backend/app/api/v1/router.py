"""Top-level API v1 router — mounts all feature routers.

Module routing reference (PRODUCTION_WORKFLOW.md § MVP Module Map):
  M1 — AI Crop Doctor     : /crop-scan, /disease-reports
  M2 — Crop Risk Radar    : /zone-status, /weather, /flood
  M3 — Smart Advisory     : /advisory
  M4 — Geo Hotspot Maps   : /hotspot-map
  M5 — Expert Validation  : /expert-queue
"""
from fastapi import APIRouter

from app.api.v1.endpoints import ping
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import dashboard

api_router = APIRouter()

# ── Phase 0 ───────────────────────────────────────────────────────────────────
api_router.include_router(ping.router, prefix="/ping", tags=["meta"])

# ── Phase 2 — Auth + Jurisdiction-Aware Access ────────────────────────────────
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Phase 3-5 : M1 AI Crop Doctor — /crop-scan, /disease-reports
# Phase 5-6 : M3 Smart Advisory — /advisory
# Phase 7   : M5 Expert Validation Loop — /expert-queue
# Phase 8-10: M2 Crop Risk Radar — /zone-status, /weather
# Phase 8-9 : M4 Geo Disease Hotspot Maps — /hotspot-map
# Phase 11  : /subsidy, /drone-booking
# Phase 12  : /agristack-sync
