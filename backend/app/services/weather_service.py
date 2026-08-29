import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

from app.models.jurisdiction import Jurisdiction
from app.models.weather_daily import WeatherDaily
from app.services.zone_scoring_service import calculate_zone_scores

logger = logging.getLogger(__name__)

async def sync_weather_for_jurisdictions(session: Session, jurisdiction_id: str = None):
    """
    Fetches real-time weather from Open-Meteo for villages and updates WeatherDaily.
    Also acts as a proxy for CWC Flood Advisory by checking extreme rainfall.
    """
    query = select(Jurisdiction).where(Jurisdiction.jurisdiction_type == "village")
    if jurisdiction_id:
        query = query.where(Jurisdiction.id == jurisdiction_id)

    villages = session.execute(query).scalars().all()
    today = datetime.now(timezone.utc).date()

    async with httpx.AsyncClient() as client:
        for village in villages:
            if village.lat is None or village.lon is None:
                continue

            try:
                # Open-Meteo current weather API
                v_lat = float(village.lat)
                v_lon = float(village.lon)
                url = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={v_lat}&longitude={v_lon}"
                    f"&current=temperature_2m,relative_humidity_2m,precipitation"
                )
                
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current", {})
                temp = current.get("temperature_2m", 25.0)
                humidity = current.get("relative_humidity_2m", 50.0)
                rainfall = current.get("precipitation", 0.0)
                
                existing = session.execute(
                    select(WeatherDaily)
                    .where(WeatherDaily.jurisdiction_id == village.id)
                    .where(WeatherDaily.date == today)
                ).scalars().first()

                if existing:
                    existing.temp_c_max = temp
                    existing.temp_c_min = temp
                    existing.humidity_pct = humidity
                    existing.rainfall_mm = rainfall
                else:
                    new_weather = WeatherDaily(
                        jurisdiction_id=village.id,
                        date=today,
                        temp_c_max=temp,
                        temp_c_min=temp,
                        humidity_pct=humidity,
                        rainfall_mm=rainfall,
                    )
                    session.add(new_weather)

            except Exception as e:
                logger.error(f"Failed to fetch weather for village {village.id}: {e}")

    session.commit()
    
    # Trigger recalculation of zone scores so weather triggers apply immediately
    calculate_zone_scores(session)
