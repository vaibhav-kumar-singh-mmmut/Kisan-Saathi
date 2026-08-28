"""
Seed disease_lookup table from disease_lookup.json (38 entries).
Pathogen type classification: user-approved mapping (see implementation_plan.md).

Usage: python -m app.db.seed_disease_lookup
"""
import json

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/../..
DISEASE_JSON = PROJECT_ROOT / "disease_lookup.json"

# ── Approved pathogen_type map (verified by user before seeding) ──────────────
# fungal=26, insect=7, viral=1, bacterial=3, nematode=1
PATHOGEN_TYPE_MAP = {
    # Wheat
    "wheat_yellow_rust": "fungal",
    "wheat_brown_leaf_rust": "fungal",
    "wheat_stem_black_rust": "fungal",
    "wheat_pests": "insect",
    # Rice
    "rice_bakanae": "fungal",
    "rice_false_smut": "fungal",
    "rice_blast": "fungal",
    "rice_tungro": "viral",  # ⚠️ CRITICAL: must NEVER get cure advisory
    # Sugarcane
    "sugarcane_red_rot": "fungal",  # irreversible but fungal
    # Cotton
    "cotton_whitefly": "insect",
    "cotton_pink_bollworm": "insect",
    # Mustard (mixed — Option A: primary=insect, secondary in JSONB)
    "mustard_pests_diseases": "insect",
    # Onion
    "onion_purple_blotch": "fungal",
    "onion_stemphylium_blight": "fungal",
    "onion_thrips": "insect",
    "onion_fusarium_basal_rot": "fungal",
    # Solanaceous
    "solanaceous_early_blight": "fungal",
    "solanaceous_late_blight": "fungal",  # oomycete, treated as fungal
    "solanaceous_bacterial_wilt": "bacterial",
    # Potato
    "potato_pink_rot": "fungal",
    "potato_powdery_scab": "fungal",
    # Brinjal
    "brinjal_fruit_shoot_borer": "insect",
    # Nursery
    "nursery_damping_off": "fungal",
    # Fruit
    "anthracnose_multi": "fungal",
    "mango_powdery_mildew": "fungal",
    "mango_bacterial_canker": "bacterial",
    "litchi_blight": "fungal",
    "litchi_sudden_death": "fungal",
    "litchi_fruit_shoot_borer": "insect",
    # Pomegranate
    "pomegranate_bacterial_blight": "bacterial",
    "pomegranate_nematode_wilt": "nematode",
    # Pulses
    "chickpea_wilt": "fungal",
    "chickpea_ascochyta_blight": "fungal",
    "pulses_rust": "fungal",
    "pulses_powdery_mildew": "fungal",
    "lentil_collar_rot": "fungal",
    "pigeonpea_wilt": "fungal",
    # Strawberry
    "strawberry_powdery_mildew": "fungal",
}

# Secondary pathogen notes for mixed entries (Option A)
SECONDARY_NOTES = {
    "mustard_pests_diseases": {
        "note": "Mixed entry: Aphid (insect) + Alternaria Blight (fungal) + White Rust (fungal). "
                "Primary pathogen_type = insect. All ipm_steps cover all three sub-pathogens.",
        "sub_pathogens": [
            {"name": "Aphid", "type": "insect"},
            {"name": "Alternaria Blight", "type": "fungal"},
            {"name": "White Rust", "type": "fungal"},
        ],
    },
}


def load_disease_json() -> dict:
    """Load and return the disease_lookup.json data."""
    with open(DISEASE_JSON, encoding="utf-8") as f:
        return json.load(f)


def seed_disease_lookup(db_url: str) -> int:
    """Seed disease_lookup table. Returns count of rows inserted."""
    from app.models.disease_lookup import DiseaseLookup

    data = load_disease_json()
    diseases = data["diseases"]

    sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    engine = create_engine(sync_url)

    count = 0
    with Session(engine) as session:
        for d in diseases:
            disease_id = d["id"]
            pathogen_type = PATHOGEN_TYPE_MAP.get(disease_id)
            if not pathogen_type:
                print(f"  [WARN] Unmapped disease ID: {disease_id} -- skipping")
                continue

            row = DiseaseLookup(
                id=disease_id,
                name=d["name"],
                crops=d["crops"],
                severity=d["severity"],
                pathogen_type=pathogen_type,
                spread_medium=d.get("spread_medium"),
                spread_radius_km=d.get("spread_radius_km"),
                seasonal_window=d.get("seasonal_window"),
                weather_triggers=d.get("weather_triggers"),
                risk_factors=d.get("risk_factors"),
                irreversible=d.get("irreversible", False),
                ipm_steps=d.get("ipm_steps"),
                growth_stage=d.get("growth_stage"),
                compound_risk_with=d.get("compound_risk_with"),
                regional_note=d.get("regional_note"),
                regional_source=d.get("regional_source"),
                secondary_pathogen_notes=SECONDARY_NOTES.get(disease_id),
            )
            session.merge(row)  # upsert
            count += 1

        session.commit()

    print(f"  [OK] disease_lookup: {count} entries seeded")
    return count


if __name__ == "__main__":
    from app.core.config import settings
    seed_disease_lookup(settings.DB_URL)
