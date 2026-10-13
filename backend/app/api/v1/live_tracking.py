from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
import time
import math
import searoute as sr

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
    {"imo": "IMO9340835", "name": "MSC Daniela", "route": [(51.95, 4.05), (40.71, -74.00)], "speed_knots": 18.0, "status": "Warning"}, # Rotterdam to NY
    {"imo": "IMO9820855", "name": "CMA CGM Jacques Saade", "route": [(1.26, 103.83), (31.23, 121.47)], "speed_knots": 22.0, "status": "Compliant"}, # Singapore to Shanghai
    {"imo": "IMO9459591", "name": "Maersk Mc-Kinney Moller", "route": [(33.83, -118.28), (-34.60, -58.38)], "speed_knots": 15.0, "status": "Non-Compliant"}, # LA to Buenos Aires
    {"imo": "IMO9773210", "name": "Ever Golden", "route": [(25.20, 55.27), (3.13, 101.68)], "speed_knots": 20.0, "status": "Compliant"}, # Dubai to Port Klang
    {"imo": "IMO9305570", "name": "Hapag-Lloyd Colombo Express", "route": [(-33.92, 18.42), (51.95, 4.05)], "speed_knots": 17.5, "status": "Warning"} # Cape Town to Rotterdam
]

# A reference time to calculate movement (Unix epoch seconds)
START_TIME = 1700000000

# Cache the sea routes so we don't recalculate them every 3 seconds
ROUTE_GEOMETRIES = {}

def get_route_geometry(start, end):
    key = f"{start}_{end}"
    if key not in ROUTE_GEOMETRIES:
        # searoute expects [lng, lat]
        route = sr.searoute([start[1], start[0]], [end[1], end[0]])
        # Extract coordinates list
        coords = route['geometry']['coordinates']
        # Convert back to (lat, lng) tuples
        ROUTE_GEOMETRIES[key] = [(c[1], c[0]) for c in coords]
    return ROUTE_GEOMETRIES[key]

def calculate_current_position(route_data: dict, current_time: float) -> dict:
    start = route_data["route"][0]
    end = route_data["route"][1]

    path = get_route_geometry(start, end)

    if not path or len(path) < 2:
        return {
            "imo": route_data["imo"], "name": route_data["name"],
            "lat": start[0], "lng": start[1], "heading": 0.0,
            "speed": route_data["speed_knots"], "compliance_status": route_data["status"]
        }

    # Time-based interpolation
    # 1 knot = 1.852 km/h. To make the simulation visible on the map, we multiply time by 1000
    elapsed_hours = (current_time - START_TIME) * 1000
    total_segments = len(path) - 1

    # We pretend each segment is roughly equal in time for simplicity
    time_per_segment = 24.0 / route_data["speed_knots"]  # arbitrary math for visualization

    total_time = total_segments * time_per_segment
    progress_time = elapsed_hours % total_time

    current_segment_idx = int(progress_time / time_per_segment)
    if current_segment_idx >= total_segments:
        current_segment_idx = total_segments - 1

    p1 = path[current_segment_idx]
    p2 = path[current_segment_idx + 1]

    segment_progress = (progress_time % time_per_segment) / time_per_segment

    current_lat = p1[0] + (p2[0] - p1[0]) * segment_progress
    current_lng = p1[1] + (p2[1] - p1[1]) * segment_progress

    # Calculate true heading
    heading = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
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
