import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[2])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.drone_booking import DroneBooking
from app.models.subsidy_flag import SubsidyFlag
from app.models.crop_entry import CropEntry
from app.models.farmer import Farmer
from app.models.jurisdiction import Jurisdiction

db = SessionLocal()

farmers = db.query(Farmer).limit(5).all()
if not farmers:
    print("No farmers found. Cannot seed dashboard data.")
    sys.exit(1)

# Seed DroneBookings
for i, f in enumerate(farmers):
    booking = DroneBooking(
        farmer_id=f.id,
        jurisdiction_id=f.jurisdiction_id,
        chc_name=f"Gorakhpur Drone CHC {i+1}",
        chc_distance_km=2.5 + i,
        acreage_ha=1.5 + i,
        crop_name="Wheat",
        status="approved" if i % 2 == 0 else "pending"
    )
    db.add(booking)

# Seed SubsidyFlags
for i, f in enumerate(farmers):
    flag = SubsidyFlag(
        jurisdiction_id=f.jurisdiction_id,
        disease_id="wheat_yellow_rust",
        farmer_ids=[f.id],
        acreage_ha=2.0 + i,
        status="approved" if i % 2 == 1 else "pending"
    )
    db.add(flag)

# Update CropEntries to be synced from AgriStack so they show up
crops = db.query(CropEntry).all()
for crop in crops:
    crop.synced_from_agristack = True

db.commit()
print("Dashboard dummy data seeded successfully!")
