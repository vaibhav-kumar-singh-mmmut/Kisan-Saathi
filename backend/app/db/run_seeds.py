"""
Phase 1 seed orchestrator — creates all tables then seeds data.

Usage:
  cd backend
  python -m app.db.run_seeds
"""
import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[2])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine

from app.core.config import settings
from app.core.database import Base
# Import all models so Base.metadata knows about every table
from app.models import (  # noqa: F401
    Jurisdiction, Official, Farmer, CropEntry, DiseaseLookup,
    DiseaseReport, WeatherDaily, ZoneStatus, SubsidyFlag, RetrainingData,
)
from app.db.seed_disease_lookup import seed_disease_lookup
from app.db.seed_villages import seed_villages


def run():
    db_url = settings.DB_URL
    sync_url = db_url.replace("+asyncpg", "").replace("+aiosqlite", "")

    print("")
    print("=" * 60)
    print("Kisan Saathi -- Phase 1 Seed Runner")
    print("=" * 60)
    print(f"  DB:  {sync_url[:60]}")
    print(f"  ENV: {settings.APP_ENV}")
    print("")

    # -- Create tables --
    engine = create_engine(sync_url)
    print("[1/3] Creating tables (if not exist)...")
    Base.metadata.create_all(engine)

    # Verify table count
    table_names = sorted(Base.metadata.tables.keys())
    print(f"  [OK] {len(table_names)} tables ready: {', '.join(table_names)}")
    print("")

    # -- Seed disease_lookup --
    print("[2/3] Seeding disease_lookup (38 entries)...")
    seed_disease_lookup(db_url)
    print("")

    # -- Seed villages + related data --
    print("[3/3] Seeding villages + officials + farmers + reports + weather + zones...")
    counts = seed_villages(db_url)

    # -- Summary --
    print("")
    print("=" * 60)
    print("PHASE 1 SEED COMPLETE")
    print("=" * 60)
    total = sum(counts.values()) + 38  # +38 for disease_lookup
    print(f"  Total rows inserted: {total}")
    print("  Next: human-review the verification table above,")
    print("  then proceed to Phase 2 (Auth + Jurisdiction-Aware Access).")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    run()
