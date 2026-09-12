"""Emissions API router for voyage logging and analytics."""

from datetime import datetime, timezone
from typing import Optional
import re
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.core.database import get_db
from app.core.security import verify_access_token
from app.services.audit_log import log_audit
from app.services.emissions_calculator import calculate_voyage_emissions
from app.models.schemas import VoyageCreate
from app.api.v1.deps import get_current_tenant_user, require_role

router = APIRouter()

VALID_FUEL_TYPES = {"HFO", "MGO", "LNG", "Methanol"}


def validate_voyage_data(data: dict):
    fuel_type = data.get("fuel_type")
    if fuel_type and fuel_type not in VALID_FUEL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid fuel_type. Must be one of: {', '.join(sorted(VALID_FUEL_TYPES))}",
        )


@router.post("/voyages", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_voyage(
    voyage_data: VoyageCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Operator", "Fleet Manager", "Org Admin", "Compliance Officer")),
):
    """Create a voyage log and automatically compute emissions."""
    org_id = current_user["org_id"]
    validate_voyage_data(voyage_data.model_dump())

    fuel_type = voyage_data.fuel_type
    fuel_consumed_mt = float(voyage_data.fuel_consumed_mt)
    distance_nm = float(voyage_data.distance_nm)
    cargo_mt = float(voyage_data.cargo_mt or 0)
    asset_id = voyage_data.asset_id

    now = datetime.now(timezone.utc)
    voyage_id = str(ObjectId())

    # Build voyage document
    voyage = {
        "id": voyage_id,
        "asset_id": asset_id,
        "departure_port": voyage_data.departure_port,
        "arrival_port": voyage_data.arrival_port,
        "departure_date": voyage_data.departure_date,
        "arrival_date": voyage_data.arrival_date,
        "fuel_type": fuel_type,
        "fuel_consumed_mt": fuel_consumed_mt,
        "distance_nm": distance_nm,
        "cargo_mt": cargo_mt,
        "org_id": org_id,
        "created_at": now,
        "updated_at": now,
    }
    await db["voyages"].insert_one(voyage)

    # Compute and store emissions (version 1, is_current=True)
    emissions_record = build_emissions_record(
        voyage_id=voyage_id,
        org_id=org_id,
        asset_id=asset_id,
        fuel_type=fuel_type,
        fuel_consumed_mt=fuel_consumed_mt,
        distance_nm=distance_nm,
        cargo_mt=cargo_mt,
        calculation_version=1,
        is_current=True,
    )
    await db["emissions_computed"].insert_one(emissions_record)

    # Audit log
    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "create", "voyage", voyage_id,
        {
            "asset_id": asset_id,
            "departure_port": voyage_data.departure_port,
            "arrival_port": voyage_data.arrival_port,
            "fuel_type": fuel_type,
            "fuel_consumed_mt": fuel_consumed_mt,
            "distance_nm": distance_nm,
            "cargo_mt": cargo_mt,
        },
    )

    return {
        "voyage": voyage,
        "emissions": emissions_record,
        "message": "Voyage created and emissions computed",
    }


@router.get("/voyages", response_model=dict)
async def list_voyages(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    period: Optional[str] = Query(None, description="Filter by period (year or YYYY-MM)"),
    search: Optional[str] = Query(None, description="Search by port names"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """List voyage logs for the org with optional filters."""
    org_id = current_user["org_id"]
    query = {"org_id": org_id}

    if asset_id:
        query["asset_id"] = asset_id

    if period:
        if len(period) == 4:
            query["departure_date"] = {"$gte": datetime(int(period), 1, 1, tzinfo=timezone.utc)}
            query["departure_date"] = {**query["departure_date"], "$lt": datetime(int(period) + 1, 1, 1, tzinfo=timezone.utc)}
        elif len(period) == 7:
            year, month = int(period[:4]), int(period[5:7])
            start = datetime(year, month, 1, tzinfo=timezone.utc)
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            query["departure_date"] = {"$gte": start, "$lt": end}

    if search:
        escaped_search = re.escape(search)
        query["$or"] = [
            {"departure_port": {"$regex": escaped_search, "$options": "i"}},
            {"arrival_port": {"$regex": escaped_search, "$options": "i"}},
        ]

    skip = (page - 1) * page_size
    cursor = db["voyages"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    voyages = await cursor.to_list(length=page_size)
    total = await db["voyages"].count_documents(query)

    voyage_ids = [v["id"] for v in voyages]

    # Fetch current emissions for each voyage
    emissions_map = {}
    if voyage_ids:
        emissions_cursor = db["emissions_computed"].find({
            "voyage_id": {"$in": voyage_ids},
            "is_current": True,
            "org_id": org_id,
        })
        emissions_list = await emissions_cursor.to_list(length=1000)
        for e in emissions_list:
            emissions_map[e["voyage_id"]] = e

    # Fetch latest emissions (any version) for history count
    for v in voyages:
        v["_id"] = str(v["_id"])
        v["id"] = v.pop("_id") if isinstance(v.get("id"), str) else str(v.get("id"))
        v["emissions"] = emissions_map.get(v["id"])

    return {"voyages": voyages, "total": total, "page": page, "page_size": page_size}


@router.get("/voyages/{voyage_id}", response_model=dict)
async def get_voyage(
    voyage_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """Get single voyage detail + emissions calculation history."""
    org_id = current_user["org_id"]

    voyage = await db["voyages"].find_one({"_id": ObjectId(voyage_id), "org_id": org_id})
    if not voyage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")

    voyage["_id"] = str(voyage["_id"])
    voyage["id"] = voyage.pop("_id") if isinstance(voyage.get("id"), str) else str(voyage.get("id"))

    # Fetch all emissions versions for this voyage
    history_cursor = db["emissions_computed"].find({"voyage_id": voyage_id}).sort("calculation_version", -1)
    history = await history_cursor.to_list(length=100)
    for h in history:
        h["_id"] = str(h["_id"])
        h["id"] = h.pop("_id") if isinstance(h.get("id"), str) else str(h.get("id"))
        h["calculated_at"] = h["calculated_at"].isoformat() if isinstance(h.get("calculated_at"), datetime) else h.get("calculated_at")

    voyage["emissions_history"] = history
    return {"voyage": voyage, "emissions_history": history}


@router.put("/voyages/{voyage_id}", response_model=dict)
async def update_voyage(
    voyage_id: str,
    update_data: VoyageCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Fleet Manager", "Org Admin", "Compliance Officer")),
):
    """Edit voyage log. Re-computes emissions, marks previous as is_current=False."""
    org_id = current_user["org_id"]
    validate_voyage_data(update_data.model_dump())

    voyage = await db["voyages"].find_one({"_id": ObjectId(voyage_id), "org_id": org_id})
    if not voyage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")

    # Mark previous emissions as not current
    await db["emissions_computed"].update_many(
        {"voyage_id": voyage_id, "org_id": org_id},
        {"$set": {"is_current": False}},
    )

    # Get current version
    current_emissions = await db["emissions_computed"].find_one({
        "voyage_id": voyage_id, "is_current": True,
    })
    prev_version = current_emissions["calculation_version"] if current_emissions else 0
    new_version = prev_version + 1

    # Build updated voyage fields
    update_dict = update_data.model_dump()
    allowed_fields = [
        "departure_port", "arrival_port", "departure_date", "arrival_date",
        "fuel_type", "fuel_consumed_mt", "distance_nm", "cargo_mt", "updated_at",
    ]
    update_fields = {k: v for k, v in update_dict.items() if k in allowed_fields}
    update_fields["updated_at"] = datetime.now(timezone.utc)

    await db["voyages"].update_one({"_id": ObjectId(voyage_id)}, {"$set": update_fields})

    # Fetch updated voyage
    updated_voyage = await db["voyages"].find_one({"_id": ObjectId(voyage_id), "org_id": org_id})
    updated_voyage["_id"] = str(updated_voyage["_id"])
    updated_voyage["id"] = updated_voyage.pop("_id") if isinstance(updated_voyage.get("id"), str) else str(updated_voyage.get("id"))

    # Re-compute emissions
    fuel_type = update_dict.get("fuel_type", voyage["fuel_type"])
    fuel_consumed_mt = float(update_dict.get("fuel_consumed_mt", voyage["fuel_consumed_mt"]))
    distance_nm = float(update_dict.get("distance_nm", voyage["distance_nm"]))
    cargo_mt = float(update_dict.get("cargo_mt", voyage.get("cargo_mt", 0)))

    new_emissions_record = build_emissions_record(
        voyage_id=voyage_id,
        org_id=org_id,
        asset_id=updated_voyage["asset_id"],
        fuel_type=fuel_type,
        fuel_consumed_mt=fuel_consumed_mt,
        distance_nm=distance_nm,
        cargo_mt=cargo_mt,
        calculation_version=new_version,
        is_current=True,
    )
    await db["emissions_computed"].insert_one(new_emissions_record)

    # Audit log
    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "update", "voyage", voyage_id,
        {"updated_fields": list(update_fields.keys()), "new_version": new_version},
    )

    return {
        "voyage": updated_voyage,
        "emissions": new_emissions_record,
        "message": f"Voyage updated (emissions version {new_version})",
    }


@router.delete("/voyages/{voyage_id}", response_model=dict)
async def delete_voyage(
    voyage_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Fleet Manager", "Org Admin")),
):
    """Delete voyage log. Audit logged."""
    org_id = current_user["org_id"]

    voyage = await db["voyages"].find_one({"_id": ObjectId(voyage_id), "org_id": org_id})
    if not voyage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")

    await db["voyages"].delete_one({"_id": ObjectId(voyage_id)})
    await db["emissions_computed"].delete_many({"voyage_id": voyage_id, "org_id": org_id})

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "delete", "voyage", voyage_id,
        {"departure_port": voyage.get("departure_port"), "arrival_port": voyage.get("arrival_port")},
    )

    return {"message": "Voyage deleted successfully"}


@router.get("/summary", response_model=dict)
async def get_emissions_summary(
    period: str = Query("month", description="Time period: month, quarter, year"),
    group_by: str = Query("vessel", description="Group by vessel or fuel_type"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """Aggregated emissions analytics for the organization."""
    org_id = current_user["org_id"]
    now = datetime.now(timezone.utc)

    # Determine date range
    if period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "quarter":
        quarter_start = ((now.month - 1) // 3) * 3 + 1
        start_date = now.replace(month=quarter_start, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get voyages for the org in this period
    voyage_query = {
        "org_id": org_id,
        "created_at": {"$gte": start_date},
    }

    voyages_cursor = db["voyages"].find(voyage_query)
    voyages = []
    async for v in voyages_cursor:
        voyages.append(v)
    if len(voyages) > 500:
        voyages = voyages[:500]
    voyage_ids = [v["id"] for v in voyages]

    if not voyage_ids:
        return {
            "total_co2": 0, "total_co2e": 0, "total_fuel_mt": 0, "avg_eefi": None,
            "by_fuel_type": {}, "by_pollutant": {}, "period": period, "group_by": group_by,
            "voyage_count": 0,
        }

    # Get current emissions records
    emissions_cursor = db["emissions_computed"].find({
        "voyage_id": {"$in": voyage_ids},
        "is_current": True,
        "org_id": org_id,
    })
    emissions_records = []
    async for e in emissions_cursor:
        emissions_records.append(e)
    if len(emissions_records) > 500:
        emissions_records = emissions_records[:500]

    voyages_by_id = {v["id"]: v for v in voyages}

    total_co2 = 0.0
    total_co2e = 0.0
    total_fuel_mt = 0.0
    total_transport_work = 0.0
    eeoi_sum = 0.0
    eefi_count = 0

    by_fuel_type: dict = {}
    by_pollutant = {"co2": 0, "ch4": 0, "n2o": 0, "sox": 0, "nox": 0}

    for rec in emissions_records:
        fuel = rec["fuel_type"]
        if fuel not in by_fuel_type:
            by_fuel_type[fuel] = {"co2": 0, "co2e": 0, "fuel_mt": 0, "voyage_count": 0}

        by_fuel_type[fuel]["co2"] += rec["emissions"]["co2"]
        by_fuel_type[fuel]["co2e"] += rec["co2_equivalent"]
        by_fuel_type[fuel]["fuel_mt"] += rec["fuel_consumed_mt"]
        by_fuel_type[fuel]["voyage_count"] += 1

        total_co2 += rec["emissions"]["co2"]
        total_co2e += rec["co2_equivalent"]
        total_fuel_mt += rec["fuel_consumed_mt"]

        for pol in by_pollutant:
            by_pollutant[pol] += rec["emissions"][pol]

        # EEOI average — using dict lookup instead of N+1 scan
        voyage = voyages_by_id.get(rec["voyage_id"])
        if voyage and voyage.get("cargo_mt") and voyage.get("distance_nm"):
            cargo = voyage["cargo_mt"]
            dist = voyage["distance_nm"]
            if cargo > 0 and dist > 0:
                # Recompute EEOI from the record
                eeoi = (rec["emissions"]["co2"] * 1e6) / (cargo * dist)
                eeoi_sum += eeoi
                eefi_count += 1

    # Group breakdowns
    if group_by == "vessel":
        vessel_breakdown: dict = {}
        for rec in emissions_records:
            aid = rec["asset_id"]
            if aid not in vessel_breakdown:
                vessel_breakdown[aid] = {"co2": 0, "co2e": 0, "fuel_mt": 0}
            vessel_breakdown[aid]["co2"] += rec["emissions"]["co2"]
            vessel_breakdown[aid]["co2e"] += rec["co2_equivalent"]
            vessel_breakdown[aid]["fuel_mt"] += rec["fuel_consumed_mt"]
    else:
        vessel_breakdown = {}

    avg_eefi = round(eeoi_sum / eefi_count, 4) if eefi_count > 0 else None

    return {
        "total_co2": round(total_co2, 4),
        "total_co2e": round(total_co2e, 4),
        "total_fuel_mt": round(total_fuel_mt, 4),
        "avg_eefi": avg_eefi,
        "by_fuel_type": by_fuel_type,
        "by_pollutant": by_pollutant,
        "by_vessel": vessel_breakdown,
        "period": period,
        "group_by": group_by,
        "voyage_count": len(voyages),
    }


def build_emissions_record(
    voyage_id: str,
    org_id: str,
    asset_id: str,
    fuel_type: str,
    fuel_consumed_mt: float,
    distance_nm: float,
    cargo_mt: float,
    calculation_version: int,
    is_current: bool,
) -> dict:
    """Build a full emissions record from voyage data."""
    calc = calculate_voyage_emissions(fuel_type, fuel_consumed_mt, distance_nm, cargo_mt)
    now = datetime.now(timezone.utc)
    return {
        "id": str(ObjectId()),
        "asset_id": asset_id,
        "org_id": org_id,
        "voyage_id": voyage_id,
        "calculation_version": calculation_version,
        "methodology": "IMO",
        "period": {"year": now.year, "month": now.month},
        "fuel_type": fuel_type,
        "fuel_consumed_mt": fuel_consumed_mt,
        "emissions": {
            "co2": calc["co2_tonnes"],
            "ch4": calc["ch4_tonnes"],
            "n2o": calc["n2o_tonnes"],
            "sox": calc["sox_tonnes"],
            "nox": calc["nox_tonnes"],
        },
        "co2_equivalent": calc["co2_equivalent_tonnes"],
        "calculated_at": now,
        "is_current": is_current,
    }


