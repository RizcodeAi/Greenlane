from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
import time
import math

from app.api.v1.deps import get_current_tenant_user

router = APIRouter()

class LiveVessel(BaseModel):
    imo: str
    name: str
    lat: float
    lng: float
    heading: float
    speed: float
    compliance_status: str

# Define static routes (start_lat, start_lng, end_lat, end_lng)
ROUTES = [
    {"imo": "IMO9340835", "name": "MSC Daniela", "route": [(30.0, -40.0), (45.0, -10.0)], "speed_knots": 18.0, "status": "Warning"},
    {"imo": "IMO9820855", "name": "CMA CGM Jacques Saade", "route": [(20.0, 110.0), (5.0, 80.0)], "speed_knots": 22.0, "status": "Compliant"},
    {"imo": "IMO9459591", "name": "Maersk Mc-Kinney Moller", "route": [(-20.0, 40.0), (-35.0, 15.0)], "speed_knots": 15.0, "status": "Non-Compliant"},
    {"imo": "IMO9773210", "name": "Ever Golden", "route": [(35.0, -120.0), (20.0, -150.0)], "speed_knots": 20.0, "status": "Compliant"},
    {"imo": "IMO9305570", "name": "Hapag-Lloyd Colombo Express", "route": [(10.0, -60.0), (35.0, -5.0)], "speed_knots": 17.5, "status": "Warning"}
]

# A reference time to calculate movement (Unix epoch seconds)
START_TIME = 1700000000

def calculate_current_position(route_data: dict, current_time: float) -> dict:
    start_lat, start_lng = route_data["route"][0]
    end_lat, end_lng = route_data["route"][1]

    # Simple linear interpolation based on time
    # 1 knot = ~1.852 km/h. Let's do a fast simulation speed: 1 hour of real time = 1 second of sim
    elapsed_hours = (current_time - START_TIME) * 10

    # Distance in roughly degrees (very simplified for mock)
    dist_lat = end_lat - start_lat
    dist_lng = end_lng - start_lng
    total_dist = math.sqrt(dist_lat**2 + dist_lng**2)

    # Degrees per hour (rough approximation)
    deg_per_hour = route_data["speed_knots"] / 60.0

    progress = (elapsed_hours * deg_per_hour) / total_dist if total_dist > 0 else 0

    # Loop back if reached the end
    progress = progress % 2.0
    if progress > 1.0:
        # Returning
        p = 2.0 - progress
        heading = math.degrees(math.atan2(start_lng - end_lng, start_lat - end_lat))
    else:
        # Going
        p = progress
        heading = math.degrees(math.atan2(end_lng - start_lng, end_lat - start_lat))

    current_lat = start_lat + (dist_lat * p)
    current_lng = start_lng + (dist_lng * p)

    # Normalize heading
    heading = (heading + 360) % 360

    return {
        "imo": route_data["imo"],
        "name": route_data["name"],
        "lat": current_lat,
        "lng": current_lng,
        "heading": heading,
        "speed": route_data["speed_knots"],
        "compliance_status": route_data["status"]
    }

@router.get("/live", response_model=List[LiveVessel])
async def get_live_fleet(current_user: dict = Depends(get_current_tenant_user)):
    """
    Returns simulated real-time positions for the fleet.
    The positions update continuously based on server time to simulate live AIS.
    """
    current_time = time.time()

    live_vessels = []
    for r in ROUTES:
        pos = calculate_current_position(r, current_time)
        live_vessels.append(pos)

    return live_vessels
