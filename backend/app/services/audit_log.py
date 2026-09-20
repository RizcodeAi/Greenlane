from datetime import datetime, timezone
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

async def _log_audit_task(db, entry):
    try:
        await db["audit_logs"].insert_one(entry)
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")

async def log_audit(
    db: AsyncIOMotorDatabase,
    org_id: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict = None,
):
    entry = {
        "org_id": org_id,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": datetime.now(timezone.utc),
        "details": details or {},
    }

    # Run in background to make it non-blocking
    asyncio.create_task(_log_audit_task(db, entry))
    return entry
