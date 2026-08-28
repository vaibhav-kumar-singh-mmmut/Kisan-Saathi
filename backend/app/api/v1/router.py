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

# Phase 3-5 : M1 AI Crop Doctor — /predict (formerly /crop-scan, /disease-reports)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../ml-model"))
try:
    from ml_service import predict  # type: ignore
    api_router.add_api_route("/predict", predict, methods=["POST"], tags=["ml"])
except ImportError:
    pass

from app.api.v1.endpoints import advisory
# Phase 5-6 : M3 Smart Advisory — /advisory
api_router.include_router(advisory.router, prefix="/advisory", tags=["advisory"])

# Phase 8-10: M2 Crop Risk Radar — /zone-status, /weather
from app.api.v1.endpoints import zones
api_router.include_router(zones.router, prefix="/zones", tags=["zones"])

# Phase 8-9 : M4 Geo Disease Hotspot Maps — /hotspot-map
from app.api.v1.endpoints import map as map_endpoint
api_router.include_router(map_endpoint.router, prefix="/map", tags=["map"])

from app.api.v1.endpoints import expert_queue
# M5 routes : /expert-queue (Phase 7)
api_router.include_router(expert_queue.router, prefix="/expert-queue", tags=["expert"])

# Phase 11  : /subsidy, /drone-booking
# Phase 12  : /agristack-sync
