"""
Seed villages, officials, farmers, crop entries, disease reports,
weather records, and zone status from seed-data/villages.json.

Builds the jurisdiction tree: District -> Tehsil -> Block -> Village
Then populates all related tables.

Usage: python -m app.db.seed_villages
"""

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Jurisdiction,
    Official,
    Farmer,
    CropEntry,
    DiseaseReport,
    WeatherDaily,
    ZoneStatus,
)

_candidates = [
    Path(__file__).resolve().parents[3] / "seed-data" / "villages.json",
    Path(__file__).resolve().parents[2] / "seed-data" / "villages.json",
    Path("/app/seed-data/villages.json"),
    Path("./seed-data/villages.json"),
]
VILLAGES_JSON = next((p for p in _candidates if p.exists()), _candidates[0])


def _new_id() -> str:
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


def seed_villages(db_url: str) -> dict:
    """Seed all village-related data. Returns summary counts."""
    with open(VILLAGES_JSON, encoding="utf-8") as f:
        data = json.load(f)

    sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    engine = create_engine(sync_url)

    counts = {
        "jurisdictions": 0,
        "officials": 0,
        "farmers": 0,
        "crop_entries": 0,
        "disease_reports": 0,
        "weather_daily": 0,
        "zone_status": 0,
    }

    with Session(engine) as session:
        if session.query(Jurisdiction).count() > 0:
            print("  [INFO] Jurisdictions table already populated, skipping village re-seed.")
            return {
                "jurisdictions": session.query(Jurisdiction).count(),
                "officials": session.query(Official).count(),
                "farmers": session.query(Farmer).count(),
                "crop_entries": session.query(CropEntry).count(),
                "disease_reports": session.query(DiseaseReport).count(),
                "weather_daily": session.query(WeatherDaily).count(),
                "zone_status": session.query(ZoneStatus).count(),
            }

        # -- 1. Jurisdiction tree --
        district_data = data["district"]
        district_id = _new_id()
        district = Jurisdiction(
            id=district_id,
            name=district_data["name"],
            jurisdiction_type="district",
            parent_id=None,
            state=district_data["state"],
            district_name=district_data["name"],
        )
        session.add(district)
        counts["jurisdictions"] += 1
        session.flush()

        jur_map = {"district": district_id}

        for tehsil_data in data["tehsils"]:
            tehsil_id = _new_id()
            tehsil = Jurisdiction(
                id=tehsil_id,
                name=tehsil_data["name"],
                jurisdiction_type="tehsil",
                parent_id=district_id,
                state=district_data["state"],
                district_name=district_data["name"],
            )
            session.add(tehsil)
            counts["jurisdictions"] += 1
            jur_map["tehsil"] = tehsil_id
            session.flush()

            for block_data in tehsil_data["blocks"]:
                block_id = _new_id()
                block = Jurisdiction(
                    id=block_id,
                    name=block_data["name"],
                    jurisdiction_type="block",
                    parent_id=tehsil_id,
                    state=district_data["state"],
                    district_name=district_data["name"],
                )
                session.add(block)
                counts["jurisdictions"] += 1
                session.flush()

                if block_data["name"] == "Bakshi Ka Talab":
                    jur_map["block_bkt"] = block_id
                else:
                    jur_map["block_moh"] = block_id

                for v in block_data["villages"]:
                    village_id = _new_id()
                    village = Jurisdiction(
                        id=village_id,
                        name=v["name"],
                        jurisdiction_type="village",
                        parent_id=block_id,
                        state=district_data["state"],
                        district_name=district_data["name"],
                        lat=v.get("lat"),
                        lon=v.get("lon"),
                    )
                    session.add(village)
                    counts["jurisdictions"] += 1
                    jur_map[v["ref"]] = village_id
                    session.flush()

                    # -- 2. Farmers (2 per village) --
                    farmer_ids = []
                    for i in range(1, 3):
                        fid = _new_id()
                        farmer = Farmer(
                            id=fid,
                            name=f"Farmer {v['ref']}-{i}",
                            phone=f"+9190{v['ref'].replace('V','')}{i:04d}",
                            jurisdiction_id=village_id,
                        )
                        session.add(farmer)
                        farmer_ids.append(fid)
                        counts["farmers"] += 1
                    session.flush()

                    # -- 3. Crop entry --
                    crop_entry = CropEntry(
                        id=_new_id(),
                        farmer_id=farmer_ids[0],
                        crop_name=v["crop"],
                        acreage_ha=v["acreage_ha"],
                        growth_stage=v.get("growth_stage"),
                        season=v["season"],
                        sowing_date=date(2026, 6 if v["season"] == "kharif" else 11, 1),
                    )
                    session.add(crop_entry)
                    counts["crop_entries"] += 1

                    # -- 4. Disease reports --
                    report_count = v.get("report_count", 0)
                    disease_id = v.get("disease_id")
                    if report_count > 0 and disease_id:
                        base_date = _now() - timedelta(days=7)
                        for r in range(report_count):
                            reporter_id = farmer_ids[r % len(farmer_ids)]
                            report = DiseaseReport(
                                id=_new_id(),
                                farmer_id=reporter_id,
                                jurisdiction_id=village_id,
                                disease_id=disease_id,
                                image_url=f"https://storage.example.com/mock/{v['ref']}_report_{r+1}.jpg",
                                confidence_score=v.get("confidence_avg", 0.8),
                                gps_lat=float(v.get("lat", 0)),
                                gps_lon=float(v.get("lon", 0)),
                                status=(
                                    "confirmed"
                                    if v.get("confidence_avg", 0.8) >= 0.70
                                    else "pending"
                                ),
                                reported_at=base_date + timedelta(hours=r * 12),
                                confirmed_at=(
                                    (base_date + timedelta(hours=r * 12 + 2))
                                    if v.get("confidence_avg", 0.8) >= 0.70
                                    else None
                                ),
                            )
                            session.add(report)
                            counts["disease_reports"] += 1

                    # -- 5. Secondary disease reports (compound risk V8) --
                    secondary_id = v.get("secondary_disease_id")
                    if secondary_id:
                        for r in range(2):
                            report = DiseaseReport(
                                id=_new_id(),
                                farmer_id=farmer_ids[r % len(farmer_ids)],
                                jurisdiction_id=village_id,
                                disease_id=secondary_id,
                                image_url=f"https://storage.example.com/mock/{v['ref']}_secondary_{r+1}.jpg",
                                confidence_score=0.78,
                                status="confirmed",
                                gps_lat=float(v.get("lat", 0)),
                                gps_lon=float(v.get("lon", 0)),
                                reported_at=_now() - timedelta(days=5, hours=r * 6),
                                confirmed_at=_now()
                                - timedelta(days=5, hours=r * 6 - 1),
                            )
                            session.add(report)
                            counts["disease_reports"] += 1

                    # -- 6. Weather daily (last 7 days) --
                    w = v.get("weather", {})
                    for d in range(7):
                        weather = WeatherDaily(
                            id=_new_id(),
                            jurisdiction_id=village_id,
                            date=date.today() - timedelta(days=d),
                            temp_c_min=w.get("temp_c_min"),
                            temp_c_max=w.get("temp_c_max"),
                            humidity_pct=w.get("humidity_pct"),
                            rainfall_mm=w.get("rainfall_mm"),
                            wind_direction=w.get("wind_direction"),
                            source="mock",
                        )
                        session.add(weather)
                        counts["weather_daily"] += 1

                    # -- 7. Zone status (expected) --
                    expected_zone = v.get("expected_zone", "green")
                    zone = ZoneStatus(
                        id=_new_id(),
                        jurisdiction_id=village_id,
                        color=expected_zone,
                        score=_zone_score(expected_zone),
                        report_count=report_count,
                        affected_area_pct=v.get("affected_area_pct", 0),
                        weather_trigger_fired=v.get("weather_trigger_match", False),
                        alert_fired=(expected_zone in ("red", "incoming_risk")),
                        computed_at=_now(),
                    )
                    session.add(zone)
                    counts["zone_status"] += 1

        # -- 8. Officials --
        for off_data in data.get("officials", []):
            jur_key = off_data.get("jurisdiction", "district")
            jur_id = jur_map.get(jur_key, district_id)
            jur_type = jur_key if jur_key in ("district", "tehsil") else "block"
            # Handle village-level officials
            if jur_key.startswith("V"):
                jur_type = "village"
            official = Official(
                id=_new_id(),
                name=off_data["name"],
                phone=off_data["phone"],
                role=off_data["role"],
                wing=off_data["wing"],
                jurisdiction_type=jur_type,
                jurisdiction_id=jur_id,
            )
            session.add(official)
            counts["officials"] += 1

        session.commit()

    # -- Print verification table --
    print("")
    print("=" * 90)
    print("PHASE 1 SEED VERIFICATION TABLE")
    print("=" * 90)
    _print_verification(data)
    print("=" * 90)
    print("")

    for k, v in counts.items():
        print(f"  [OK] {k}: {v} rows")

    return counts


def _zone_score(color: str) -> float:
    """Mock score for expected zones."""
    return {"green": 15.0, "orange": 55.0, "red": 85.0, "incoming_risk": 70.0}.get(
        color, 0
    )


def _print_verification(data: dict):
    """Print the human-verification table matching AI_AGENT_BUILD_PROMPT.md gate."""
    header = (
        f"{'Ref':<4} {'Village':<16} {'Crop':<10} "
        f"{'Disease':<28} {'Rpts':>4} {'Wx?':>3} {'Zone':<14}"
    )
    print(header)
    print("-" * 90)

    for tehsil in data["tehsils"]:
        for block in tehsil["blocks"]:
            for v in block["villages"]:
                disease = v.get("disease_id") or "(none - spread risk)"
                wx = "Y" if v.get("weather_trigger_match") else "N"
                zone = v.get("expected_zone", "green").upper()
                if disease == "rice_tungro":
                    zone += " VIRAL-NO-CURE"
                print(
                    f"{v['ref']:<4} {v['name']:<16} {v['crop']:<10} "
                    f"{disease:<28} {v.get('report_count', 0):>4} {wx:>3} {zone:<14}"
                )


if __name__ == "__main__":
    from app.core.config import settings

    seed_villages(settings.DB_URL)
