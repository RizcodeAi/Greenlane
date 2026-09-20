from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase


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
    await db["audit_logs"].insert_one(entry)
    return entry
