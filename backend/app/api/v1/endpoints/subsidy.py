"""
Phase 11 — Subsidy/PMFBY + Drone Booking API endpoints.
Routes:
  POST   /subsidy/flag              — officer raises a PMFBY subsidy flag
  GET    /subsidy/flags             — list flags (filtered by jurisdiction)
  POST   /subsidy/flags/{id}/approve — BDO approves a flag (immutable)
  POST   /drone/book                — farmer books drone spray
  GET    /drone/bookings            — list drone bookings (officer view)
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.subsidy_flag import SubsidyFlag
from app.models.drone_booking import DroneBooking
from app.services.subsidy_service import (
    can_flag_subsidy,
    create_subsidy_flag,
    approve_subsidy_flag,
    create_drone_booking,
)

router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class SubsidyFlagRequest(BaseModel):
    officer_id: str
    jurisdiction_id: str
    disease_id: str
    acreage_ha: Optional[float] = None


class SubsidyApproveRequest(BaseModel):
    approver_id: str


class DroneBookingRequest(BaseModel):
    farmer_id: str
    jurisdiction_id: str
    disease_report_id: Optional[str] = None
    acreage_ha: Optional[float] = None
    crop_name: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    notes: Optional[str] = None


# ─── Subsidy Flag Endpoints ───────────────────────────────────────────────────

@router.post("/flag", tags=["subsidy"])
def raise_subsidy_flag(body: SubsidyFlagRequest, db: Session = Depends(get_db)):
    """
    Officer raises a PMFBY subsidy flag for a disease outbreak in a jurisdiction.
    Rejected with 403 if the minimum independent-report threshold is not met.
    """
    flag, message = create_subsidy_flag(
        db,
        officer_id=body.officer_id,
        jurisdiction_id=body.jurisdiction_id,
        disease_id=body.disease_id,
        acreage_ha=body.acreage_ha,
    )
    if flag is None:
        raise HTTPException(status_code=403, detail=message)

    return {
        "id": flag.id,
        "status": flag.status,
        "jurisdiction_id": flag.jurisdiction_id,
        "disease_id": flag.disease_id,
        "acreage_ha": flag.acreage_ha,
        "farmer_ids": flag.farmer_ids,
        "report_ids": flag.report_ids,
        "geotagged_image_urls": flag.geotagged_image_urls,
        "pmfby_window_expires_at": flag.pmfby_window_expires_at,
        "audit_trail": flag.audit_trail,
        "message": message,
    }


@router.get("/flags", tags=["subsidy"])
def list_subsidy_flags(
    jurisdiction_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List PMFBY subsidy flags, optionally filtered by jurisdiction and status."""
    q = db.query(SubsidyFlag)
    if jurisdiction_id:
        q = q.filter(SubsidyFlag.jurisdiction_id == jurisdiction_id)
    if status:
        q = q.filter(SubsidyFlag.status == status)
    flags = q.order_by(SubsidyFlag.created_at.desc()).all()

    return [
        {
            "id": f.id,
            "jurisdiction_id": f.jurisdiction_id,
            "disease_id": f.disease_id,
            "flagged_by": f.flagged_by,
            "status": f.status,
            "acreage_ha": f.acreage_ha,
            "farmer_count": len(f.farmer_ids or []),
            "report_count": len(f.report_ids or []),
            "pmfby_window_expires_at": f.pmfby_window_expires_at,
            "created_at": f.created_at,
        }
        for f in flags
    ]


@router.post("/flags/{flag_id}/approve", tags=["subsidy"])
def approve_flag(flag_id: str, body: SubsidyApproveRequest, db: Session = Depends(get_db)):
    """
    BDO/DM approves a pending PMFBY flag. Once approved the flag is locked:
    any subsequent approval attempt returns 409 Conflict.
    Audit trail entry is appended and immutable.
    """
    flag, message = approve_subsidy_flag(db, flag_id, body.approver_id)
    if flag is None:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=409, detail=message)

    return {
        "id": flag.id,
        "status": flag.status,
        "approved_by": flag.approved_by,
        "approved_at": flag.approved_at,
        "audit_trail": flag.audit_trail,
        "message": message,
    }


# ─── Drone Booking Endpoints ──────────────────────────────────────────────────

@router.post("/book", tags=["drone"])
def book_drone(body: DroneBookingRequest, db: Session = Depends(get_db)):
    """
    Farmer books a drone spray session. The system automatically routes the
    booking to the nearest CHC/SHG by GPS proximity.
    """
    booking = create_drone_booking(
        db,
        farmer_id=body.farmer_id,
        jurisdiction_id=body.jurisdiction_id,
        disease_report_id=body.disease_report_id,
        acreage_ha=body.acreage_ha,
        crop_name=body.crop_name,
        scheduled_for=body.scheduled_for,
        notes=body.notes,
    )
    return {
        "id": booking.id,
        "farmer_id": booking.farmer_id,
        "status": booking.status,
        "chc_id": booking.chc_id,
        "chc_name": booking.chc_name,
        "chc_distance_km": booking.chc_distance_km,
        "acreage_ha": booking.acreage_ha,
        "crop_name": booking.crop_name,
        "scheduled_for": booking.scheduled_for,
        "booked_at": booking.booked_at,
        "message": f"Drone spray booked successfully. Nearest CHC: {booking.chc_name} ({booking.chc_distance_km} km away).",
    }


@router.get("/bookings", tags=["drone"])
def list_drone_bookings(
    jurisdiction_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Officer view — list all drone bookings, optionally filtered."""
    q = db.query(DroneBooking)
    if jurisdiction_id:
        q = q.filter(DroneBooking.jurisdiction_id == jurisdiction_id)
    if status:
        q = q.filter(DroneBooking.status == status)
    bookings = q.order_by(DroneBooking.booked_at.desc()).all()

    return [
        {
            "id": b.id,
            "farmer_id": b.farmer_id,
            "jurisdiction_id": b.jurisdiction_id,
            "chc_name": b.chc_name,
            "chc_distance_km": b.chc_distance_km,
            "crop_name": b.crop_name,
            "acreage_ha": b.acreage_ha,
            "status": b.status,
            "scheduled_for": b.scheduled_for,
            "booked_at": b.booked_at,
        }
        for b in bookings
    ]
