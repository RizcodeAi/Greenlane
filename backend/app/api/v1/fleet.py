from datetime import datetime, timezone
from typing import Optional
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import ShipCreate, ShipUpdate
from app.services.audit_log import log_audit
from app.api.v1.deps import get_current_tenant_user, require_role

router = APIRouter()

# Allowed values validation
VALID_VESSEL_TYPES = {"Bulk Carrier", "Tanker", "Container", "Ro-Ro", "General Cargo", "Gas Carrier"}
VALID_FUEL_TYPES = {"HFO", "MGO", "LNG", "Methanol"}
VALID_STATUSES = {"active", "inactive"}


def validate_ship_data(data: dict):
    """Validate vessel_type, fuel_type, and status against allowed values."""
    if data.get("vessel_type") and data["vessel_type"] not in VALID_VESSEL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid vessel_type. Must be one of: {', '.join(sorted(VALID_VESSEL_TYPES))}",
        )
    if data.get("fuel_type") and data["fuel_type"] not in VALID_FUEL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid fuel_type. Must be one of: {', '.join(sorted(VALID_FUEL_TYPES))}",
        )
    if data.get("status") and data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )


@router.post("/ships", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_ship(
    ship_data: ShipCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Fleet Manager", "Org Admin")),
):
    """Add a new ship to the fleet."""
    org_id = current_user["org_id"]
    validate_ship_data(ship_data.model_dump())

    now = datetime.now(timezone.utc)
    ship = {
        "id": str(ObjectId()),
        "imo_number": ship_data.imo_number,
        "name": ship_data.name,
        "flag_state": ship_data.flag_state,
        "vessel_type": ship_data.vessel_type,
        "gross_tonnage": float(ship_data.gross_tonnage),
        "dwt": float(ship_data.dwt),
        "fuel_type": ship_data.fuel_type,
        "status": ship_data.status,
        "org_id": org_id,
        "created_at": now,
        "updated_at": now,
    }

    # Enforce unique IMO per org via unique index, handle DuplicateKeyError
    try:
        await db["ships"].insert_one(ship)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ship with IMO {ship_data.imo_number} already exists in your organization",
        )

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "create", "ship", ship["id"],
        {"imo_number": ship["imo_number"], "name": ship["name"], "vessel_type": ship["vessel_type"]},
    )

    return {"ship": ship, "message": "Ship created successfully"}


@router.get("/ships", response_model=dict)
async def list_ships(
    search: Optional[str] = Query(None, description="Search by ship name or IMO number"),
    vessel_type: Optional[str] = Query(None, description="Filter by vessel type"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """List ships for the current organization with search and filter."""
    org_id = current_user["org_id"]

    query = {"org_id": org_id, "is_deleted": False}

    if search:
        escaped_search = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": escaped_search, "$options": "i"}},
            {"imo_number": {"$regex": escaped_search, "$options": "i"}},
        ]
    if vessel_type:
        query["vessel_type"] = vessel_type
    if fuel_type:
        query["fuel_type"] = fuel_type
    if status:
        query["status"] = status

    # Validate filter values
    if vessel_type and vessel_type not in VALID_VESSEL_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid vessel_type. Must be one of: {', '.join(sorted(VALID_VESSEL_TYPES))}")
    if fuel_type and fuel_type not in VALID_FUEL_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid fuel_type. Must be one of: {', '.join(sorted(VALID_FUEL_TYPES))}")
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}")

    skip = (page - 1) * page_size
    cursor = db["ships"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    ships = await cursor.to_list(length=page_size)
    total = await db["ships"].count_documents(query)

    for ship in ships:
        ship["_id"] = str(ship["_id"])
        ship["id"] = ship.pop("_id") if isinstance(ship.get("_id"), str) else str(ship.get("_id"))

    return {"ships": ships, "total": total, "page": page, "page_size": page_size}


@router.get("/ships/{ship_id}", response_model=dict)
async def get_ship(
    ship_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """Get detailed info of a single ship owned by the org."""
    org_id = current_user["org_id"]
    ship = await db["ships"].find_one({"_id": ObjectId(ship_id), "org_id": org_id, "is_deleted": False})
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

    ship["_id"] = str(ship["_id"])
    ship["id"] = ship.pop("_id") if isinstance(ship.get("_id"), str) else str(ship.get("_id"))
    return {"ship": ship}


@router.put("/ships/{ship_id}", response_model=dict)
async def update_ship(
    ship_id: str,
    update_data: ShipUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Fleet Manager", "Org Admin")),
):
    """Update ship details (requires Fleet Manager or Org Admin role)."""
    org_id = current_user["org_id"]

    # Validate fields
    if "vessel_type" in update_data and update_data["vessel_type"] not in VALID_VESSEL_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid vessel_type. Must be one of: {', '.join(sorted(VALID_VESSEL_TYPES))}")
    if "fuel_type" in update_data and update_data["fuel_type"] not in VALID_FUEL_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid fuel_type. Must be one of: {', '.join(sorted(VALID_FUEL_TYPES))}")
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                          detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}")

    ship = await db["ships"].find_one({"_id": ObjectId(ship_id), "org_id": org_id, "is_deleted": False})
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

    # Prevent changing IMO number to one that conflicts
    if "imo_number" in update_data:
        existing = await db["ships"].find_one({
            "imo_number": update_data["imo_number"],
            "org_id": org_id,
            "_id": {"$ne": ObjectId(ship_id)},
        })
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                              detail=f"Ship with IMO {update_data['imo_number']} already exists")

    update_fields = {k: v for k, v in update_data.items() if k in
                     ["name", "flag_state", "vessel_type", "gross_tonnage", "dwt", "fuel_type", "status", "imo_number"]}
    update_fields["updated_at"] = datetime.now(timezone.utc)

    await db["ships"].update_one({"_id": ObjectId(ship_id), "org_id": org_id}, {"$set": update_fields})

    updated_ship = await db["ships"].find_one({"_id": ObjectId(ship_id), "org_id": org_id})
    updated_ship["_id"] = str(updated_ship["_id"])
    updated_ship["id"] = updated_ship.pop("_id") if isinstance(updated_ship.get("_id"), str) else str(updated_ship.get("_id"))

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "update", "ship", ship_id,
        {"updated_fields": list(update_fields.keys())},
    )

    return {"ship": updated_ship, "message": "Ship updated successfully"}


@router.delete("/ships/{ship_id}", response_model=dict)
async def delete_ship(
    ship_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Org Admin")),
):
    """Soft delete ship (requires Org Admin role). Cascades to voyages."""
    org_id = current_user["org_id"]
    ship = await db["ships"].find_one({"_id": ObjectId(ship_id), "org_id": org_id})
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

    deleted_at = datetime.now(timezone.utc)
    await db["ships"].update_one(
        {"_id": ObjectId(ship_id), "org_id": org_id},
        {"$set": {"is_deleted": True, "deleted_at": deleted_at}},
    )

    # Cascade: soft delete associated voyages
    await db["voyages"].update_many(
        {"asset_id": ship.get("id"), "org_id": org_id},
        {"$set": {"is_deleted": True, "deleted_at": deleted_at}},
    )

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "delete", "ship", ship_id,
        {"imo_number": ship.get("imo_number"), "name": ship.get("name")},
    )

    return {"message": "Ship soft deleted successfully"}