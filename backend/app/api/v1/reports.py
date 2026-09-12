"""Report API router for IMO DCS compliance reports."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.services.audit_log import log_audit
from app.services.report_generator import generate_imo_dcs_report, get_all_report_files
from app.models.schemas import ReportCreate, ReportStatusUpdate
from app.api.v1.deps import get_current_tenant_user, require_role

router = APIRouter()

VALID_STATUSES = {"Draft", "Generated", "Submitted"}


@router.post("/reports/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: ReportCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Compliance Officer", "Org Admin")),
):
    """Generate an IMO DCS Annual Compliance Report for the specified year."""
    org_id = current_user["org_id"]
    year = request.year

    if not isinstance(year, int) or year < 2000 or year > 2100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="year must be an integer between 2000 and 2100",
        )

    # Fetch all ships for the org using cursor
    ships = []
    ships_cursor = db["ships"].find({"org_id": org_id}).limit(1000)
    async for doc in ships_cursor:
        ships.append(doc)

    # Fetch voyages for the year using cursor
    voyages = []
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    voyages_cursor = db["voyages"].find({
        "org_id": org_id,
        "created_at": {"$gte": start, "$lt": end},
    }).limit(1000)
    async for doc in voyages_cursor:
        voyages.append(doc)

    voyage_ids = [v["id"] for v in voyages]

    # Fetch emissions computed for voyages in this year using cursor
    emissions_records = []
    if voyage_ids:
        emissions_cursor = db["emissions_computed"].find({
            "voyage_id": {"$in": voyage_ids},
        }).limit(1000)
        async for doc in emissions_cursor:
            emissions_records.append(doc)

    # Generate the PDF
    org_name = current_user["user"].get("full_name", org_id)
    org_doc = await db["organizations"].find_one({"_id": org_id})
    if org_doc and org_doc.get("name"):
        org_name = org_doc["name"]

    pdf_path = generate_imo_dcs_report(
        org_id=org_id,
        org_name=org_name,
        year=year,
        ships=ships,
        emissions_records=emissions_records,
        voyages=voyages,
    )

    # Create report document
    report_id = pdf_path.split("/")[-1].replace(".pdf", "")
    report_doc = {
        "id": report_id,
        "org_id": org_id,
        "year": year,
        "status": "Generated",
        "report_type": "IMO DCS Annual",
        "generated_at": datetime.now(timezone.utc),
        "pdf_url": f"/api/v1/reports/{report_id}/download",
        "fleet_summary": {
            "total_ships": len(ships),
            "total_fuel_consumed_mt": sum(
                rec.get("fuel_consumed_mt", 0) for rec in emissions_records
            ),
            "total_co2_emissions_tonnes": sum(
                rec.get("emissions", {}).get("co2", 0) for rec in emissions_records
            ),
            "total_transport_work_tonne_miles": sum(
                v.get("distance_nm", 0) * v.get("cargo_mt", 0)
                for v in voyages if v.get("cargo_mt") and v.get("distance_nm")
            ),
        },
    }
    await db["reports"].insert_one(report_doc)

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "generate", "report", report_id,
        {"year": year, "total_ships": len(ships), "total_co2": report_doc["fleet_summary"]["total_co2_emissions_tonnes"]},
    )

    return {
        "report": {
            "id": report_id, "org_id": org_id, "year": year,
            "status": "Generated", "generated_at": report_doc["generated_at"],
            "report_type": "IMO DCS Annual", "pdf_url": f"/api/v1/reports/{report_id}/download",
            "fleet_summary": report_doc["fleet_summary"],
        },
        "message": "IMO DCS report generated successfully",
    }


@router.get("/reports", response_model=dict)
async def list_reports(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """List all generated compliance reports for the current org."""
    org_id = current_user["org_id"]
    cursor = db["reports"].find({"org_id": org_id}).sort("generated_at", -1)
    reports = await cursor.to_list(length=1000)

    for r in reports:
        r["_id"] = str(r["_id"])
        r["id"] = r.pop("_id") if isinstance(r.get("id"), str) else str(r.get("id"))
        r["generated_at"] = r["generated_at"].isoformat() if isinstance(r.get("generated_at"), datetime) else r.get("generated_at")

    return {"reports": reports, "total": len(reports)}


@router.get("/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """Get report details."""
    org_id = current_user["org_id"]
    report = await db["reports"].find_one({"_id": ObjectId(report_id), "org_id": org_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report["_id"] = str(report["_id"])
    report["id"] = report.pop("_id") if isinstance(report.get("id"), str) else str(report.get("id"))
    report["generated_at"] = report["generated_at"].isoformat() if isinstance(report.get("generated_at"), datetime) else report.get("generated_at")

    return {"report": report}


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user),
):
    """Download the generated PDF file."""
    org_id = current_user["org_id"]
    report = await db["reports"].find_one({"_id": ObjectId(report_id), "org_id": org_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    import os
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports_storage")
    fname = f"{report_id}.pdf"
    full_path = os.path.join(pdf_path, fname)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found on disk")

    return FileResponse(
        path=full_path,
        filename=f"IMO_DCS_Report_{report.get('year', 'unknown')}_{report_id}.pdf",
        media_type="application/pdf",
    )


@router.patch("/reports/{report_id}/status")
async def update_report_status(
    report_id: str,
    status_data: ReportStatusUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(require_role("Compliance Officer", "Org Admin")),
):
    """Update report status (Draft -> Generated -> Submitted)."""
    org_id = current_user["org_id"]
    new_status = status_data.status

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"status must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    report = await db["reports"].find_one({"_id": ObjectId(report_id), "org_id": org_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    old_status = report.get("status", "Draft")
    await db["reports"].update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {"status": new_status}},
    )

    await log_audit(
        db, org_id, current_user["user"]["_id"],
        "update", "report", report_id,
        {"status_change": f"{old_status} -> {new_status}"},
    )

    return {"report_id": report_id, "status": new_status, "message": f"Report status updated from {old_status} to {new_status}"}