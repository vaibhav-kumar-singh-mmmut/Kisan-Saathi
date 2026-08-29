"""
ORM model barrel — import all models here so Alembic's autogenerate
and Base.metadata.create_all() discover every table.
"""

from app.models.jurisdiction import Jurisdiction
from app.models.official import Official
from app.models.farmer import Farmer
from app.models.crop_entry import CropEntry
from app.models.disease_lookup import DiseaseLookup
from app.models.disease_report import DiseaseReport
from app.models.weather_daily import WeatherDaily
from app.models.zone_status import ZoneStatus
from app.models.subsidy_flag import SubsidyFlag
from app.models.drone_booking import DroneBooking
from app.models.retraining_data import RetrainingData
from app.models.crop_discrepancy import CropDiscrepancy

__all__ = [
    "Jurisdiction",
    "Official",
    "Farmer",
    "CropEntry",
    "DiseaseLookup",
    "DiseaseReport",
    "WeatherDaily",
    "ZoneStatus",
    "SubsidyFlag",
    "DroneBooking",
    "RetrainingData",
    "CropDiscrepancy",
]
