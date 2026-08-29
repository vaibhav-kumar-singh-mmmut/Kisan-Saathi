"""Top-level API v1 router — mounts all feature routers.
Module routing reference (PRODUCTION_WORKFLOW.md § MVP Module Map):
  M1 — AI Crop Doctor     : /crop-scan, /disease-reports
  M2 — Crop Risk Radar    : /zone-status, /weather, /flood
  M3 — Smart Advisory     : /advisory
  M4 — Geo Hotspot Maps   : /hotspot-map
  M5 — Expert Validation  : /expert-queue
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    ping,
    auth,
    dashboard,
    expert_queue,
    advisory,
    map,
    zones,
    weather,
    subsidy,
    agristack,
    post_harvest,
    notifications,
)

api_router = APIRouter()
api_router.include_router(ping.router, prefix="/ping", tags=["meta"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(advisory.router, prefix="/advisory", tags=["advisory"])
api_router.include_router(zones.router, prefix="/zones", tags=["zones"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
api_router.include_router(expert_queue.router, prefix="/expert-queue", tags=["expert"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(subsidy.router, prefix="/subsidy", tags=["subsidy"])
api_router.include_router(subsidy.router, prefix="/drone", tags=["drone"])
api_router.include_router(agristack.router, prefix="/agristack", tags=["agristack"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(post_harvest.router, prefix="/post-harvest", tags=["post-harvest"])
import sys
import os

ml_model_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ml-model")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ml-model")),
    "/app/ml-model",
    "/ml-model",
]
for p in ml_model_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

try:
    from ml_service import predict

    api_router.add_api_route("/predict", predict, methods=["POST"], tags=["ml"])
except Exception as e:
    import traceback

    print(f"=== ML_SERVICE IMPORT FAILED: {e} ===")
    traceback.print_exc()

