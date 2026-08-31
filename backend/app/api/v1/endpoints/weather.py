from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.weather_daily import WeatherDaily
from app.models.zone_status import ZoneStatus
from app.services.weather_service import sync_weather_for_jurisdictions

router = APIRouter()

import httpx
from math import radians, cos, sin, asin, sqrt
from fastapi import Query
from app.models.jurisdiction import Jurisdiction

from typing import Dict, Any, Optional

def _haversine(lon1, lat1, lon2, lat2):
    if lon1 is None or lat1 is None or lon2 is None or lat2 is None: return 999999
    try:
        lon1, lat1, lon2, lat2 = map(float, [lon1, lat1, lon2, lat2])
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 2 * 6371 * asin(sqrt(a))
    except:
        return 999999

HINDI_VILLAGES = {
    "Rampur Khurd": "रामपुर खुर्द",
    "Sonbarsa": "सोनबरसा",
    "Fatehpur Mafi": "फतेहपुर माफी",
    "Gajraula": "गजरौला",
    "Mahmoodpur": "महमूदपुर",
    "Bhadruk": "भदरुक",
    "Laharpur": "लहरपुर",
    "Naugaon": "नौगांव",
    "Deoria Khurd": "देवरिया खुर्द",
    "Pipra": "पिपरा",
    "Sikandarpur": "सिकंदरपुर",
    "Kusumkhi": "कुसुमखी",
    "Lachhimanpur": "लच्छीमनपुर",
    "Gangauli": "गंगौली",
    "Pura": "पुरा",
    "Bhilawan": "भिलावन"
}

@router.get("/local", response_model=Dict[str, Any])
async def get_local_weather_and_schemes(
    lat: float = Query(...), 
    lon: float = Query(...), 
    db: Session = Depends(get_db)
):
    """
    Returns weather for the farmer's current coordinates, along with nearby villages (in Hindi) and recommended schemes + forecasts.
    """
    villages = db.execute(select(Jurisdiction).where(Jurisdiction.jurisdiction_type == "village")).scalars().all()
    
    nearby_villages = []
    for v in villages:
        if v.name.lower() == 'bijnor':
            continue
        if v.lat and v.lon:
            dist = _haversine(lon, lat, v.lon, v.lat)
            nearby_villages.append((dist, v))
            
    nearby_villages.sort(key=lambda x: x[0])
    closest = nearby_villages[:4]
    
    village_status = [{
        "id": "live-location",
        "name": "Live Location (वर्तमान स्थान)",
        "distance_km": 0.0,
        "color": "green"
    }]
    for dist, v in closest:
        zone = db.execute(select(ZoneStatus).where(ZoneStatus.jurisdiction_id == v.id).order_by(ZoneStatus.computed_at.desc())).scalars().first()
        color = zone.color if zone else "green"
        village_status.append({
            "id": v.id,
            "name": HINDI_VILLAGES.get(v.name, v.name),
            "distance_km": round(dist, 1),
            "color": color
        })

    temp, humidity, rainfall = 28.0, 65.0, 0.0
    wind_speed, wind_direction, wind_gusts = 10.0, 180.0, 15.0
    forecast_days = []
    min_temp = 15.0
    
    try:
        async with httpx.AsyncClient() as client:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
                f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_gusts_10m_max"
                f"&timezone=auto"
            )
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                temp = current.get("temperature_2m", temp)
                humidity = current.get("relative_humidity_2m", humidity)
                rainfall = current.get("precipitation", rainfall)
                wind_speed = current.get("wind_speed_10m", wind_speed)
                wind_direction = current.get("wind_direction_10m", wind_direction)
                wind_gusts = current.get("wind_gusts_10m", wind_gusts)
                
                daily = data.get("daily", {})
                if daily and "time" in daily:
                    min_temp = min(daily.get("temperature_2m_min", [15.0]))
                    for i in range(min(3, len(daily["time"]))):
                        forecast_days.append({
                            "date": daily["time"][i],
                            "temp_max": daily["temperature_2m_max"][i],
                            "temp_min": daily["temperature_2m_min"][i],
                            "rainfall": daily["precipitation_sum"][i],
                            "wind_max": daily["wind_gusts_10m_max"][i]
                        })
    except Exception as e:
        print("Meteo API Error:", e)

    alerts = []
    schemes = []

    # Weather analysis & Schemes
    if rainfall > 50.0:
        alerts.append("Monsoon Alert: Excessive rainfall detected. Risk of waterlogging and crop damage.")
        schemes.append({
            "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
            "description": "Claim crop insurance for flood/monsoon damage. Ensure your sowing certificate is ready.",
            "url": "https://pmfby.gov.in"
        })
    elif rainfall < 2.0 and temp > 32.0 and humidity < 40.0:
        alerts.append("Drought Alert: Extreme heat and dry conditions detected. High risk of crop stress.")
        schemes.append({
            "name": "PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)",
            "description": "Avail subsidies for micro-irrigation systems (drip/sprinkler) to protect against drought.",
            "url": "https://pmksy.gov.in"
        })
    elif humidity > 85.0 and temp >= 24.0 and temp <= 30.0:
         alerts.append("Blight Risk: High humidity/temperature patterns detected. Preventive spray advised.")

    # Frost Alert
    if min_temp < 4.0:
        alerts.append("Frost Warning: Night temperatures dropping below 4°C. Irrigate fields or use smoke to protect crops.")
        
    # Storm Alert
    if wind_gusts > 60.0 or any(f.get("wind_max", 0) > 60.0 for f in forecast_days):
        alerts.append("Storm Alert: High wind gusts detected. Secure loose structures and delay spraying chemicals.")
        
    # Locust Outbreak Alert (Favorable conditions: Temp > 28, Hum 50-75%, Wind from SW/W/NW)
    if temp > 28.0 and 50.0 <= humidity <= 75.0 and 180 <= wind_direction <= 300:
        alerts.append("Locust Outbreak Risk: Warm winds and humidity are highly favorable for locust swarms. Monitor crops closely.")

    return {
        "temperature_c": float(temp),
        "humidity_pct": float(humidity),
        "rainfall_mm": float(rainfall),
        "wind_speed_kmh": float(wind_speed),
        "wind_direction_deg": float(wind_direction),
        "alerts": alerts,
        "schemes": schemes,
        "forecast": forecast_days,
        "nearby_villages": village_status,
        "location": {"lat": lat, "lon": lon}
    }

@router.get("/{jurisdiction_id}", response_model=Dict[str, Any])
async def get_weather_for_jurisdiction(jurisdiction_id: str, db: Session = Depends(get_db)):
    """
    Returns latest weather stats and any active risks for the given jurisdiction.
    Fetches real-time data from Open-Meteo.
    """
    jurisdiction = db.execute(
        select(Jurisdiction).where(Jurisdiction.id == jurisdiction_id)
    ).scalars().first()
    
    temp, humidity, rainfall = None, None, None
    if jurisdiction and jurisdiction.lat and jurisdiction.lon:
        try:
            async with httpx.AsyncClient() as client:
                url = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={jurisdiction.lat}&longitude={jurisdiction.lon}"
                    f"&current=temperature_2m,relative_humidity_2m,precipitation"
                )
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                current = data.get("current", {})
                temp = current.get("temperature_2m")
                humidity = current.get("relative_humidity_2m")
                rainfall = current.get("precipitation")
        except Exception:
            pass

    if temp is None or humidity is None or rainfall is None:
        weather = (
            db.execute(
                select(WeatherDaily)
                .where(WeatherDaily.jurisdiction_id == jurisdiction_id)
                .order_by(WeatherDaily.date.desc())
            )
            .scalars()
            .first()
        )
        temp = weather.temp_c_max if (weather and weather.temp_c_max is not None) else 28.0
        humidity = weather.humidity_pct if (weather and weather.humidity_pct is not None) else 65.0
        rainfall = weather.rainfall_mm if (weather and weather.rainfall_mm is not None) else 0.0

    zone_status = (
        db.execute(
            select(ZoneStatus)
            .where(ZoneStatus.jurisdiction_id == jurisdiction_id)
            .order_by(ZoneStatus.computed_at.desc())
        )
        .scalars()
        .first()
    )

    result = {
        "temperature_c": float(temp),
        "humidity_pct": float(humidity),
        "rainfall_mm": float(rainfall),
        "alerts": []
    }

    if zone_status:
        if zone_status.color == "red" and result["rainfall_mm"] > 100.0:
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
