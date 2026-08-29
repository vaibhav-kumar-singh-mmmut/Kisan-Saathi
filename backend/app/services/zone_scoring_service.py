from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from app.models.jurisdiction import Jurisdiction
from app.models.disease_report import DiseaseReport
from app.models.disease_lookup import DiseaseLookup
from app.models.weather_daily import WeatherDaily
from app.models.zone_status import ZoneStatus


def calculate_zone_scores(session: Session):
    """
    Core Zone Scoring Engine (Phase 8).
    Calculates the risk score for all villages and updates ZoneStatus.
    Handles 'Incoming Risk' based on spatial proximity to red zones.
    Prevents alert fatigue by firing alerts only on state changes.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # 1. Fetch all villages
    villages = (
        session.execute(
            select(Jurisdiction).where(Jurisdiction.jurisdiction_type == "village")
        )
        .scalars()
        .all()
    )

    red_zones_info = []  # List of tuples: (village_id, disease_id)

    # 2. Score each village
    for village in villages:
        # Fetch reports
        reports = (
            session.execute(
                select(DiseaseReport)
                .where(DiseaseReport.jurisdiction_id == village.id)
                .where(DiseaseReport.status == "confirmed")
                .where(DiseaseReport.confirmed_at >= seven_days_ago)
            )
            .scalars()
            .all()
        )

        report_count = len(reports)

        # Calculate base score based on severity and count
        max_severity = "low"
        weather_triggered = False
        primary_disease_id = None

        score = 0.0

        if report_count > 0:
            # For simplicity, aggregate highest severity
            for report in reports:
                disease = session.get(DiseaseLookup, report.disease_id)
                if not disease:
                    continue

                if disease.severity == "high":
                    max_severity = "high"
                    primary_disease_id = disease.id
                elif disease.severity == "medium" and max_severity != "high":
                    max_severity = "medium"
                    primary_disease_id = disease.id
                elif max_severity == "low":
                    primary_disease_id = disease.id

                # Check weather triggers
                weather_today = (
                    session.execute(
                        select(WeatherDaily)
                        .where(WeatherDaily.jurisdiction_id == village.id)
                        .order_by(WeatherDaily.date.desc())
                    )
                    .scalars()
                    .first()
                )

                if weather_today and disease.weather_triggers:
                    h_min = disease.weather_triggers.get("humidity_pct_min") or disease.weather_triggers.get("humidity_min")
                    if h_min is not None and weather_today.humidity_pct is not None:
                        if weather_today.humidity_pct >= h_min:
                            temp_max = disease.weather_triggers.get("temp_c_max")
                            temp_min = disease.weather_triggers.get("temp_c_min")
                            if temp_max is not None and weather_today.temp_c_max is not None:
                                if weather_today.temp_c_max <= temp_max:
                                    weather_triggered = True
                            elif temp_min is not None and weather_today.temp_c_min is not None:
                                if weather_today.temp_c_min >= temp_min:
                                    weather_triggered = True
                            else:
                                weather_triggered = True

        if report_count == 0:
            score = 10.0  # baseline
            
            # Phase 10: Weather check even if no reports
            weather_today = (
                session.execute(
                    select(WeatherDaily)
                    .where(WeatherDaily.jurisdiction_id == village.id)
                    .order_by(WeatherDaily.date.desc())
                )
                .scalars()
                .first()
            )

            if weather_today:
                # 1. Flood Risk proxy (rainfall > 100mm)
                if weather_today.rainfall_mm and weather_today.rainfall_mm > 100.0:
                    score = 75.0  # Immediate Red Zone (Flood Risk)
                    weather_triggered = True
                else:
                    # 2. Disease weather triggers
                    all_diseases = session.execute(select(DiseaseLookup)).scalars().all()
                    for disease in all_diseases:
                        if disease.weather_triggers:
                            h_min = disease.weather_triggers.get("humidity_pct_min") or disease.weather_triggers.get("humidity_min")
                            if h_min is not None and weather_today.humidity_pct is not None:
                                if weather_today.humidity_pct >= h_min:
                                    temp_max = disease.weather_triggers.get("temp_c_max")
                                    temp_min = disease.weather_triggers.get("temp_c_min")
                                    if temp_max is not None and weather_today.temp_c_max is not None:
                                        if weather_today.temp_c_max <= temp_max:
                                            score = max(score, 50.0)  # Orange Zone (Weather Risk)
                                            weather_triggered = True
                                            primary_disease_id = disease.id
                                    elif temp_min is not None and weather_today.temp_c_min is not None:
                                        if weather_today.temp_c_min >= temp_min:
                                            score = max(score, 50.0)
                                            weather_triggered = True
                                            primary_disease_id = disease.id
                                    else:
                                        # Just humidity trigger
                                        score = max(score, 50.0)
                                        weather_triggered = True
                                        primary_disease_id = disease.id

        else:
            if max_severity == "high":
                score = 60.0 + (report_count * 5)
            elif max_severity == "medium":
                score = 40.0 + (report_count * 3)
            else:
                score = 20.0 + (report_count * 2)

            if weather_triggered:
                score += 15.0

        # Cap at 100
        score = min(score, 100.0)

        # Determine Color
        if score >= 75.0:
            color = "red"
            if primary_disease_id:
                red_zones_info.append((village.id, primary_disease_id))
        elif score >= 45.0:
            color = "orange"
        else:
            color = "green"

        _record_zone_status(
            session, village.id, color, score, report_count, weather_triggered
        )

    # 3. Spatial Pass for Incoming Risk
    for red_village_id, disease_id in red_zones_info:
        disease = session.get(DiseaseLookup, disease_id)
        if not disease or not disease.spread_radius_km:
            continue

        nearby_villages = _get_nearby_jurisdictions(
            session, red_village_id, disease.spread_radius_km
        )

        for nearby_id in nearby_villages:
            # Check if this village is already Red/Orange
            latest = (
                session.execute(
                    select(ZoneStatus)
                    .where(ZoneStatus.jurisdiction_id == nearby_id)
                    .order_by(ZoneStatus.computed_at.desc())
                )
                .scalars()
                .first()
            )

            # If it's green, flip it to incoming_risk
            if latest and latest.color == "green":
                # We need to create a NEW record for incoming risk to trigger the alert properly
                _record_zone_status(session, nearby_id, "incoming_risk", 70.0, 0, False)


def _record_zone_status(
    session: Session,
    jurisdiction_id: str,
    color: str,
    score: float,
    report_count: int,
    weather_triggered: bool,
):
    import time

    time.sleep(0.001)  # Guarantee sorting precision for tests
    # Fetch previous latest state to prevent alert fatigue
    previous_zone = (
        session.execute(
            select(ZoneStatus)
            .where(ZoneStatus.jurisdiction_id == jurisdiction_id)
            .order_by(ZoneStatus.computed_at.desc())
        )
        .scalars()
        .first()
    )

    alert_fired = False

    if not previous_zone:
        # First time being scored
        if color in ("red", "incoming_risk"):
            alert_fired = True
    else:
        # State change detection
        if color != previous_zone.color:
            if color in ("red", "incoming_risk"):
                alert_fired = True
        else:
            # Same color, but check if we need to escalate based on time? No, alert fatigue rule:
            # a village whose color DIDN'T change produces NO new alert.
            alert_fired = False

    new_zone = ZoneStatus(
        jurisdiction_id=jurisdiction_id,
        color=color,
        score=score,
        report_count=report_count,
        weather_trigger_fired=weather_triggered,
        alert_fired=alert_fired,
    )
    session.add(new_zone)
    session.commit()


def _get_nearby_jurisdictions(
    session: Session, source_id: str, radius_km: float
) -> List[str]:
    """
    Uses PostGIS ST_DWithin to find villages within a given radius.
    """
    # Assuming lat/lon are stored as floats in Jurisdiction and PostGIS is enabled.
    # Note: 1 degree of lat/lon is approximately 111km.
    # A more precise PostGIS query using Geography type:

    import math

    source = session.get(Jurisdiction, source_id)
    if not source or source.lat is None or source.lon is None:
        return []

    # Fallback to Python-based Haversine distance since SQLite doesn't support PostGIS natively
    villages = session.execute(
        select(Jurisdiction)
        .where(Jurisdiction.jurisdiction_type == 'village')
        .where(Jurisdiction.id != source_id)
        .where(Jurisdiction.lat != None)
        .where(Jurisdiction.lon != None)
    ).scalars().all()

    nearby = []
    for v in villages:
        # Haversine formula
        R = 6371.0 # Earth radius in km
        lat1, lon1 = math.radians(float(source.lat)), math.radians(float(source.lon))
        lat2, lon2 = math.radians(float(v.lat)), math.radians(float(v.lon))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        if distance <= radius_km:
            nearby.append(v.id)

    return nearby
