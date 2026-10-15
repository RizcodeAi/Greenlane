import httpx
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
import asyncio
from app.api.v1.deps import get_current_tenant_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class StormData(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    scale_x: float
    scale_y: float
    scale_height: float
    wind_speed: float

# Key ocean regions to monitor for storms
OCEAN_REGIONS = [
    {"id": "north_atlantic", "name": "North Atlantic Ocean", "lat": 45.0, "lng": -40.0},
    {"id": "pacific", "name": "Pacific Ocean", "lat": 15.0, "lng": -130.0},
    {"id": "indian_ocean", "name": "Indian Ocean", "lat": -10.0, "lng": 80.0},
    {"id": "gulf_of_mexico", "name": "Gulf of Mexico", "lat": 25.0, "lng": -90.0},
    {"id": "south_china_sea", "name": "South China Sea", "lat": 15.0, "lng": 115.0},
    {"id": "mediterranean", "name": "Mediterranean Sea", "lat": 35.0, "lng": 18.0}
]

async def fetch_weather_for_region(client: httpx.AsyncClient, region: dict) -> dict:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={region['lat']}&longitude={region['lng']}&current=temperature_2m,wind_speed_10m,precipitation&wind_speed_unit=kn&forecast_days=1"
    try:
        response = await client.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        wind_speed = current.get("wind_speed_10m", 0)
        precipitation = current.get("precipitation", 0)

        # Calculate cloud size based on wind and rain (simulating storms)
        # Base size for clear day
        scale_x = 50000.0
        scale_y = 50000.0
        scale_height = 5000.0

        if wind_speed > 25 or precipitation > 5:
            # Significant weather system
            scale_x = 200000.0 + (wind_speed * 5000)
            scale_y = 200000.0 + (wind_speed * 5000)
            scale_height = 10000.0 + (precipitation * 1000)

            # Cap maximum sizes to prevent render glitches
            scale_x = min(scale_x, 600000.0)
            scale_y = min(scale_y, 600000.0)
            scale_height = min(scale_height, 30000.0)

        return {
            "id": region["id"],
            "name": region["name"],
            "lat": region["lat"],
            "lng": region["lng"],
            "scale_x": scale_x,
            "scale_y": scale_y,
            "scale_height": scale_height,
            "wind_speed": wind_speed
        }
    except Exception as e:
        logger.error(f"Failed to fetch weather for {region['name']}: {str(e)}")
        # Return fallback clear weather
        return {
            "id": region["id"],
            "name": region["name"],
            "lat": region["lat"],
            "lng": region["lng"],
            "scale_x": 50000.0,
            "scale_y": 50000.0,
            "scale_height": 5000.0,
            "wind_speed": 0.0
        }


@router.get("/storms", response_model=List[StormData])
async def get_storms(current_user: dict = Depends(get_current_tenant_user)):
    """
    Get current weather storms and volumetric cloud coordinates using Open-Meteo.
    Translates wind speed and precipitation into 3D cloud scales for Cesium.
    """
    async with httpx.AsyncClient() as client:
        tasks = [fetch_weather_for_region(client, region) for region in OCEAN_REGIONS]
        results = await asyncio.gather(*tasks)

    return results
