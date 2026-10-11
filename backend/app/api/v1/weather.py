from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel

from app.api.v1.deps import get_current_tenant_user

router = APIRouter()

class StormData(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    scale_x: float
    scale_y: float
    scale_height: float

@router.get("/storms", response_model=List[StormData])
async def get_storms(current_user: dict = Depends(get_current_tenant_user)):
    """
    Get current weather storms and volumetric cloud coordinates.
    Currently returns mock data representing major storm systems.
    Ready to be hooked up to NOAA or StormGlass APIs.
    """
    return [
        {
            "id": "storm-1",
            "name": "North Atlantic Storm",
            "lat": 45.0,
            "lng": -40.0,
            "scale_x": 250000.0,
            "scale_y": 200000.0,
            "scale_height": 15000.0
        },
        {
            "id": "storm-2",
            "name": "Pacific Cyclone",
            "lat": 15.0,
            "lng": 130.0,
            "scale_x": 300000.0,
            "scale_y": 300000.0,
            "scale_height": 20000.0
        },
        {
            "id": "storm-3",
            "name": "Indian Ocean Depression",
            "lat": -10.0,
            "lng": 80.0,
            "scale_x": 150000.0,
            "scale_y": 150000.0,
            "scale_height": 12000.0
        }
    ]
