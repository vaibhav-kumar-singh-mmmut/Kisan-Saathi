from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.weather_daily import WeatherDaily
from app.models.zone_status import ZoneStatus
from app.services.weather_service import sync_weather_for_jurisdictions

router = APIRouter()


@router.get("/{jurisdiction_id}", response_model=Dict[str, Any])
def get_weather_for_jurisdiction(jurisdiction_id: str, db: Session = Depends(get_db)):
    """
    Returns latest weather stats and any active risks for the given jurisdiction.
    """
    weather = (
        db.execute(
            select(WeatherDaily)
            .where(WeatherDaily.jurisdiction_id == jurisdiction_id)
            .order_by(WeatherDaily.date.desc())
        )
        .scalars()
        .first()
    )

    zone_status = (
        db.execute(
            select(ZoneStatus)
            .where(ZoneStatus.jurisdiction_id == jurisdiction_id)
            .order_by(ZoneStatus.computed_at.desc())
        )
        .scalars()
        .first()
    )

    temp = weather.temp_c_max if (weather and weather.temp_c_max is not None) else 28.0
    humidity = weather.humidity_pct if (weather and weather.humidity_pct is not None) else 65.0
    rainfall = weather.rainfall_mm if (weather and weather.rainfall_mm is not None) else 0.0

    result = {
        "temperature_c": float(temp),
        "humidity_pct": float(humidity),
        "rainfall_mm": float(rainfall),
        "alerts": []
    }

    if zone_status:
        # Generate dynamic banners based on current zone and weather_triggered status
        if zone_status.color == "red" and weather and weather.rainfall_mm and weather.rainfall_mm > 100.0:
            result["alerts"].append("Flood Warning: Extreme rainfall detected!")
        elif zone_status.color in ["orange", "red"] and zone_status.weather_trigger_fired:
            result["alerts"].append("Blight Risk: High humidity/temperature patterns detected. Preventive spray advised.")
        elif zone_status.color == "incoming_risk":
            result["alerts"].append("Incoming Risk: Disease outbreak reported in a neighboring village.")

    return result


@router.post("/sync")
async def trigger_weather_sync(background_tasks: BackgroundTasks, jurisdiction_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Manually triggers Open-Meteo fetch for demo purposes.
    Runs asynchronously.
    """
    # Note: normally db session should not be passed to background task without handling its lifecycle,
    # but for simplicity in demo we await the sync synchronously here, or pass it correctly.
    # Actually, we can just run it synchronously since it's a demo
    await sync_weather_for_jurisdictions(db, jurisdiction_id)
    return {"status": "Weather sync completed"}
