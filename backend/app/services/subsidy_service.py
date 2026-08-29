"""
Phase 11 — Subsidy/PMFBY + Drone Booking Service.
Business logic for:
  - PMFBY subsidy flag lifecycle (raise, approve, audit)
  - Drone spray booking (routed to nearest CHC/SHG by Haversine)
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.subsidy_flag import SubsidyFlag
from app.models.disease_report import DiseaseReport
from app.models.drone_booking import DroneBooking
from app.models.jurisdiction import Jurisdiction

# ─── Configuration ────────────────────────────────────────────────────────────

PMFBY_MIN_REPORTS = 5          # Minimum confirmed reports to allow flagging
PMFBY_MIN_UNIQUE_FARMERS = 3   # Must come from at least this many distinct farmers
PMFBY_WINDOW_HOURS = 72        # PMFBY claim window in hours

# ─── Mock CHC / Custom Hiring Centre Data ────────────────────────────────────
# In production this table would be populated from AgriStack / CHC registry.
# Keyed by district-level jurisdiction_id prefix for routing.

MOCK_CHC_CENTRES = [
    {"id": "CHC-001", "name": "Gorakhpur CHC (Block: Sadar)", "lat": 26.755, "lon": 83.373, "district": "Gorakhpur"},
    {"id": "CHC-002", "name": "Deoria CHC (Block: Bhatpar Rani)", "lat": 26.504, "lon": 83.784, "district": "Deoria"},
    {"id": "CHC-003", "name": "Azamgarh CHC (Block: Mirzapur)", "lat": 26.064, "lon": 83.185, "district": "Azamgarh"},
    {"id": "CHC-004", "name": "Maharajganj CHC (Block: Naugarh)", "lat": 27.145, "lon": 83.564, "district": "Maharajganj"},
    {"id": "CHC-005", "name": "Basti CHC (Block: Haraiya)", "lat": 26.795, "lon": 82.734, "district": "Basti"},
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _find_nearest_chc(lat: float, lon: float) -> Optional[dict]:
    """Return the CHC closest to the given coordinates."""
    if not lat or not lon:
        return MOCK_CHC_CENTRES[0]
    best = min(
        MOCK_CHC_CENTRES,
        key=lambda c: _haversine_km(lat, lon, c["lat"], c["lon"])
    )
    best["distance_km"] = round(_haversine_km(lat, lon, best["lat"], best["lon"]), 2)
    return best


# ─── Subsidy Flag Service ──────────────────────────────────────────────────────

def can_flag_subsidy(session: Session, jurisdiction_id: str, disease_id: str) -> tuple[bool, str]:
    """
    Check if a jurisdiction has enough confirmed reports to raise a PMFBY subsidy flag.
    Returns (allowed: bool, reason: str).
    """
    reports = (
        session.query(DiseaseReport)
        .filter(
            DiseaseReport.jurisdiction_id == jurisdiction_id,
            DiseaseReport.disease_id == disease_id,
            DiseaseReport.status == "confirmed",
        )
        .all()
    )

    if len(reports) < PMFBY_MIN_REPORTS:
        return False, (
            f"Only {len(reports)} confirmed report(s) found for this disease in this village. "
            f"Minimum required: {PMFBY_MIN_REPORTS}."
        )

    unique_farmer_ids = {r.farmer_id for r in reports}
    if len(unique_farmer_ids) < PMFBY_MIN_UNIQUE_FARMERS:
        return False, (
            f"Reports are from only {len(unique_farmer_ids)} distinct farmer(s). "
            f"Minimum {PMFBY_MIN_UNIQUE_FARMERS} independent farmers required."
        )

    return True, "Eligible for PMFBY subsidy flag."


def create_subsidy_flag(
    session: Session,
    officer_id: str,
    jurisdiction_id: str,
    disease_id: str,
    acreage_ha: Optional[float] = None,
) -> tuple[Optional[SubsidyFlag], str]:
    """
    Raise a PMFBY subsidy flag if eligible. Assembles the full claim packet.
    Returns (flag, message).
    """
    allowed, reason = can_flag_subsidy(session, jurisdiction_id, disease_id)
    if not allowed:
        return None, reason

    # Assemble claim packet
    reports = (
        session.query(DiseaseReport)
        .filter(
            DiseaseReport.jurisdiction_id == jurisdiction_id,
            DiseaseReport.disease_id == disease_id,
            DiseaseReport.status == "confirmed",
        )
        .all()
    )

    report_ids = [r.id for r in reports]
    farmer_ids = list({r.farmer_id for r in reports})
    geotagged_image_urls = [r.image_url for r in reports if r.image_url]
    now = datetime.now(timezone.utc)

    flag = SubsidyFlag(
        jurisdiction_id=jurisdiction_id,
        disease_id=disease_id,
        flagged_by=officer_id,
        report_ids=report_ids,
        farmer_ids=farmer_ids,
        geotagged_image_urls=geotagged_image_urls,
        acreage_ha=acreage_ha,
        status="pending",
        pmfby_window_expires_at=now + timedelta(hours=PMFBY_WINDOW_HOURS),
        audit_trail=[
            {
                "action": "flagged",
                "by": officer_id,
                "at": now.isoformat(),
                "report_count": len(report_ids),
                "farmer_count": len(farmer_ids),
            }
        ],
    )
    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag, "PMFBY subsidy flag raised successfully."


def approve_subsidy_flag(
    session: Session,
    flag_id: str,
    approver_id: str,
) -> tuple[Optional[SubsidyFlag], str]:
    """
    BDO/DM approves a pending subsidy flag. Once approved, status is locked
    (immutable — any second approve call returns None with an error message).
    """
    flag = session.get(SubsidyFlag, flag_id)
    if flag is None:
        return None, "Subsidy flag not found."

    if flag.status != "pending":
        return None, f"Subsidy flag is already '{flag.status}'. Approval is immutable once set."

    now = datetime.now(timezone.utc)
    flag.status = "approved"
    flag.approved_by = approver_id
    flag.approved_at = now

    # Append to immutable audit trail (never overwrite existing entries)
    trail = list(flag.audit_trail or [])
    trail.append({
        "action": "approved",
        "by": approver_id,
        "at": now.isoformat(),
    })
    flag.audit_trail = trail

    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag, "Subsidy flag approved and audit trail locked."


# ─── Drone Booking Service ────────────────────────────────────────────────────

def create_drone_booking(
    session: Session,
    farmer_id: str,
    jurisdiction_id: str,
    disease_report_id: Optional[str] = None,
    acreage_ha: Optional[float] = None,
    crop_name: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> DroneBooking:
    """
    Create a drone spray booking for a farmer.
    Resolves nearest CHC/SHG by jurisdiction GPS coordinates.
    """
    # Look up jurisdiction GPS to find nearest CHC
    lat, lon = None, None
    jurisdiction = session.get(Jurisdiction, jurisdiction_id)
    if jurisdiction:
        # Cast to float — SQLite may return strings via ORM
        try:
            lat = float(jurisdiction.lat) if jurisdiction.lat is not None else None
            lon = float(jurisdiction.lon) if jurisdiction.lon is not None else None
        except (TypeError, ValueError):
            lat, lon = None, None

    chc = _find_nearest_chc(lat, lon)

    booking = DroneBooking(
        farmer_id=farmer_id,
        jurisdiction_id=jurisdiction_id,
        disease_report_id=disease_report_id,
        chc_id=chc["id"] if chc else None,
        chc_name=chc["name"] if chc else None,
        chc_lat=chc["lat"] if chc else None,
        chc_lon=chc["lon"] if chc else None,
        chc_distance_km=chc.get("distance_km") if chc else None,
        acreage_ha=acreage_ha,
        crop_name=crop_name,
        scheduled_for=scheduled_for,
        notes=notes,
        status="pending",
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
