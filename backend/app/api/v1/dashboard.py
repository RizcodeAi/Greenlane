from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.deps import require_role

router = APIRouter()

# ============================================================
# Pydantic response models
# ============================================================

class FleetSummaryResponse(BaseModel):
    total_ships: int = 0
    active_ships: int = 0
    green_count: int = 0
    yellow_count: int = 0
    red_count: int = 0
    total_co2_ytd: float = 0.0
    total_fuel_ytd: float = 0.0
    avg_cii_rating: str = "N/A"


class MapVesselResponse(BaseModel):
    name: str
    imo: str
    vessel_type: str
    lat: float
    lng: float
    speed_knots: float
    heading_deg: int
    destination: str
    eta: str
    fuel_type: str
    compliance_status: str


# ============================================================
# Endpoints
# ============================================================

@router.get("/dashboard/summary", response_model=FleetSummaryResponse)
async def get_dashboard_summary(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Operator", "Fleet Manager", "Org Admin", "Compliance Officer")),
):
    """Returns fleet summary metrics for the current organization."""
    org_id = current_user["org_id"]

    # Fetch all ships for the org
    cursor = db["ships"].find({"org_id": org_id})
    ships = await cursor.to_list(length=1000)

    total_ships = len(ships)
    active_ships = sum(1 for s in ships if s.get("status") == "active")

    # Compliance counts
    green_count = 0
    yellow_count = 0
    red_count = 0

    for ship in ships:
        cs = ship.get("compliance_status", "Compliant")
        if cs == "Compliant":
            green_count += 1
        elif cs == "Warning":
            yellow_count += 1
        else:
            red_count += 1

    # YTD CO2 and fuel calculations
    now_utc = datetime.now(timezone.utc)
    start_of_year = now_utc.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {"$match": {"org_id": org_id, "calculated_at": {"$gte": start_of_year}}},
        {"$group": {
            "_id": None,
            "total_co2_kg": {"$sum": "$co2_kg"},
            "total_fuel_l": {"$sum": "$fuel_consumed_l"},
            "count": {"$sum": 1},
        }},
    ]
    emission_result = await db["emissions_computed"].aggregate(pipeline).to_list(length=1)

    total_co2_ytd = 0.0
    total_fuel_ytd = 0.0
    if emission_result and emission_result[0].get("count", 0) > 0:
        total_co2_ytd = round(emission_result[0].get("total_co2_kg", 0) / 1000, 2)
        total_fuel_ytd = round(emission_result[0].get("total_fuel_l", 0) / 1000, 2)

    # Average CII rating
    cii_ratings = [s.get("cii_rating") for s in ships if s.get("cii_rating")]

    avg_cii = "N/A"
    if cii_ratings:
        priority = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
        avg_val = sum(priority.get(r, 3) for r in cii_ratings) / len(cii_ratings)
        rounded = round(avg_val)
        avg_cii = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}.get(min(max(rounded, 1), 5), "C")

    return FleetSummaryResponse(
        total_ships=total_ships,
        active_ships=active_ships,
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
        total_co2_ytd=total_co2_ytd,
        total_fuel_ytd=total_fuel_ytd,
        avg_cii_rating=avg_cii,
    )


@router.get("/dashboard/map-vessels", response_model=List[MapVesselResponse])
async def get_map_vessels(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Operator", "Fleet Manager", "Org Admin", "Compliance Officer")),
):
    """Returns list of vessels with live AIS position mock data."""
    org_id = current_user["org_id"]

    cursor = db["ships"].find({"org_id": org_id})
    org_ships = await cursor.to_list(length=1000)

    now = datetime.now(timezone.utc)
    vessels: List[MapVesselResponse] = []

    for ship in org_ships:
        compliance = ship.get("compliance_status", "Compliant")
        vessels.append(MapVesselResponse(
            name=ship.get("name", "Unknown"),
            imo=str(ship.get("imo_number", "")),
            vessel_type=ship.get("vessel_type", "Container"),
            lat=float(ship.get("lat", 0.0)),
            lng=float(ship.get("lng", 0.0)),
            speed_knots=float(ship.get("speed_knots", 0.0)),
            heading_deg=int(ship.get("heading_deg", 0)),
            destination=ship.get("destination", ""),
            eta=ship.get("eta", now.isoformat()),
            fuel_type=ship.get("fuel_type", "HFO"),
            compliance_status=compliance,
        ))

    return vessels
