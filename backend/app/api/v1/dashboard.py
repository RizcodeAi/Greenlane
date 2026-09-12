from datetime import datetime, timezone
import random
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_access_token
from app.services.audit_log import log_audit

router = APIRouter()
security = HTTPBearer(auto_error=False)

# -- Mock vessels for map view when org has fewer than 10 ships --
MOCK_VESSELS = [
    {"name": "MV Atlantic Star", "imo": "9234567", "vessel_type": "Container",
     "lat": 51.9244, "lng": 4.4777, "speed_knots": 14.2, "heading_deg": 85,
     "destination": "Rotterdam", "eta": "2025-07-15T14:00:00Z",
     "fuel_type": "HFO", "compliance_status": "Compliant"},
    {"name": "Ever Given", "imo": "9811234", "vessel_type": "Container",
     "lat": 30.5850, "lng": 32.2650, "speed_knots": 8.5, "heading_deg": 120,
     "destination": "Suez Canal", "eta": "2025-07-12T08:30:00Z",
     "fuel_type": "MGO", "compliance_status": "Warning"},
    {"name": "Maersk Mc-Kinney", "imo": "9608123", "vessel_type": "Container",
     "lat": 1.2833, "lng": 103.8667, "speed_knots": 16.0, "heading_deg": 45,
     "destination": "Singapore Strait", "eta": "2025-07-18T22:00:00Z",
     "fuel_type": "LNG", "compliance_status": "Compliant"},
    {"name": "MSC Oscar", "imo": "9704567", "vessel_type": "Container",
     "lat": 33.8110, "lng": 131.4280, "speed_knots": 12.8, "heading_deg": 270,
     "destination": "Tokyo Bay", "eta": "2025-07-20T06:00:00Z",
     "fuel_type": "HFO", "compliance_status": "Non-Compliant"},
    {"name": "CMA CGM Antoine", "imo": "9823456", "vessel_type": "Container",
     "lat": 32.4000, "lng": 35.1500, "speed_knots": 10.5, "heading_deg": 180,
     "destination": "Suez Canal", "eta": "2025-07-14T12:00:00Z",
     "fuel_type": "MGO", "compliance_status": "Compliant"},
    {"name": "MV Pacific Voyager", "imo": "9712345", "vessel_type": "Bulk Carrier",
     "lat": 8.9833, "lng": 100.6167, "speed_knots": 11.3, "heading_deg": 90,
     "destination": "Malacca Strait", "eta": "2025-07-16T10:00:00Z",
     "fuel_type": "HFO", "compliance_status": "Warning"},
    {"name": "MV North End", "imo": "9623456", "vessel_type": "Tanker",
     "lat": 50.9097, "lng": -1.4047, "speed_knots": 13.7, "heading_deg": 60,
     "destination": "English Channel", "eta": "2025-07-13T16:00:00Z",
     "fuel_type": "MGO", "compliance_status": "Compliant"},
    {"name": "Hanjin Seoul", "imo": "9734567", "vessel_type": "Container",
     "lat": 37.5665, "lng": 126.9780, "speed_knots": 9.8, "heading_deg": 315,
     "destination": "Tokyo Bay", "eta": "2025-07-21T04:00:00Z",
     "fuel_type": "LNG", "compliance_status": "Compliant"},
    {"name": "MV Hamburg Express", "imo": "9834567", "vessel_type": "General Cargo",
     "lat": 53.5511, "lng": 9.9937, "speed_knots": 15.1, "heading_deg": 135,
     "destination": "Hamburg", "eta": "2025-07-11T20:00:00Z",
     "fuel_type": "MGO", "compliance_status": "Non-Compliant"},
    {"name": "MV Long Beach Star", "imo": "9745678", "vessel_type": "Container",
     "lat": 33.7542, "lng": -118.2164, "speed_knots": 7.4, "heading_deg": 225,
     "destination": "Los Angeles", "eta": "2025-07-17T09:00:00Z",
     "fuel_type": "HFO", "compliance_status": "Warning"},
]

MAP_LOCATIONS = [
    ("Rotterdam", 51.9244, 4.4777),
    ("Singapore Strait", 1.2833, 103.8667),
    ("Suez Canal", 30.5850, 32.2650),
    ("Panama Canal", 9.1000, -79.5000),
    ("Malacca Strait", 8.9833, 100.6167),
    ("English Channel", 50.9097, -1.4047),
    ("Tokyo Bay", 35.6762, 139.6503),
    ("Hamburg", 53.5511, 9.9937),
    ("Busan", 35.1796, 129.0756),
    ("Los Angeles", 33.7542, -118.2164),
]

VESSEL_PREFIXES = ["MV", "MS", "MT", "SS"]
VESSEL_NAMES = [
    "Star", "Voyager", "Pioneer", "Navigator", "Explorer", "Heritage",
    "Aurora", "Endeavour", "Horizon", "Legacy", "Quantum", "Trident",
    "Summit", "Titan", "Phoenix", "Catalyst", "Valor", "Atlas",
]
VESSEL_TYPES = ["Bulk Carrier", "Tanker", "Container", "Ro-Ro", "General Cargo"]
FUEL_TYPES = ["HFO", "MGO", "LNG", "Methanol"]
COMPLIANCE_STATUSES = ["Compliant", "Warning", "Non-Compliant"]
STATUSES = ["active", "inactive"]


def _generate_mock_ships(count: int, org_id: str, now: datetime) -> List[dict]:
    ships = []
    for i in range(count):
        prefix = VESSEL_PREFIXES[i % len(VESSEL_PREFIXES)]
        name_base = VESSEL_NAMES[i % len(VESSEL_NAMES)]
        idx = i // len(VESSEL_NAMES)
        loc = MAP_LOCATIONS[i % len(MAP_LOCATIONS)]
        loc_name, lat, lng = loc
        ships.append({
            "id": str(ObjectId()),
            "imo_number": f"9{8000000 + i:07d}",
            "name": f"{prefix} {name_base} {idx + 1}",
            "flag_state": ["Panama", "Liberia", "Marshall Islands", "Singapore", "Hong Kong"][i % 5],
            "vessel_type": VESSEL_TYPES[i % len(VESSEL_TYPES)],
            "gross_tonnage": float(10000 + (i * 7351) % 50000),
            "dwt": float(15000 + (i * 12345) % 80000),
            "fuel_type": FUEL_TYPES[i % len(FUEL_TYPES)],
            "status": STATUSES[i % len(STATUSES)],
            "org_id": org_id,
            "created_at": now,
            "updated_at": now,
            "mock": True,
            "lat": lat,
            "lng": lng,
            "speed_knots": round(5.0 + (i * 2.1) % 15.0, 1),
            "heading_deg": (i * 37) % 360,
            "destination": loc_name,
            "eta": now.isoformat(),
            "compliance_status": COMPLIANCE_STATUSES[i % len(COMPLIANCE_STATUSES)],
        })
    return ships


async def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role", "Operator")
    user = await db["users"].find_one({"_id": user_id, "org_id": org_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user": user, "org_id": org_id, "role": role}


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
    current_user: dict = Depends(_get_current_user),
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

    # If fewer than 10 ships, generate mock data in-memory only (never stored in DB)
    mock_ships_in_memory = []
    if total_ships < 10:
        mock_count = 10 - total_ships
        now = datetime.now(timezone.utc)
        mock_ships_in_memory = _generate_mock_ships(mock_count, org_id, now)
        # Combine real ships with mock ships for counting only
        all_ships_for_counting = ships + mock_ships_in_memory
        total_ships = len(all_ships_for_counting)
        green_count = yellow_count = red_count = 0
        for s in all_ships_for_counting:
            cs = s.get("compliance_status", "Compliant")
            if cs == "Compliant": green_count += 1
            elif cs == "Warning": yellow_count += 1
            else: red_count += 1

    # YTD CO2 and fuel calculations
    now_utc = datetime.now(timezone.utc)
    start_of_year = now_utc.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {"$match": {"org_id": org_id, "timestamp": {"$gte": start_of_year}}},
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
    if not cii_ratings:
        random.seed(42)
        for ship in ships:
            if not ship.get("cii_rating"):
                ship["cii_rating"] = random.choice(["A", "B", "C", "D", "E"])
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
    current_user: dict = Depends(_get_current_user),
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

    # If fewer than 10 vessels, add mock vessels in-memory only (never stored in DB)
    if len(vessels) < 10:
        mock_count = 10 - len(vessels)
        mock_ships = _generate_mock_ships(mock_count, org_id, now)
        for ms in mock_ships:
            vessels.append(MapVesselResponse(
                name=ms["name"],
                imo=ms["imo_number"],
                vessel_type=ms["vessel_type"],
                lat=ms["lat"],
                lng=ms["lng"],
                speed_knots=ms["speed_knots"],
                heading_deg=ms["heading_deg"],
                destination=ms["destination"],
                eta=ms["eta"],
                fuel_type=ms["fuel_type"],
                compliance_status=ms["compliance_status"],
            ))

    return vessels
