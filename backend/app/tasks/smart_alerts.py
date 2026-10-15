import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.tasks.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)

async def _check_and_send_alerts():
    """
    Async logic to check for compliance breaches or severe weather risks
    and generate smart alerts using a fresh Motor client instance bound to the current event loop.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL, journal=True)
    db = client[settings.MONGODB_DB_NAME]
    try:
        # 1. Check for newly flagged anomalies
        anomalous_voyages = await db["voyages"].find({"is_anomalous": True, "alert_sent": {"$ne": True}}).to_list(length=100)

        for voyage in anomalous_voyages:
            ship = await db["ships"].find_one({"_id": voyage["ship_id"]})
            ship_name = ship.get("name", "Unknown Ship") if ship else "Unknown Ship"
            reasons = ", ".join(voyage.get("anomaly_reasons", []))

            logger.warning(f"🚨 SMART ALERT: Voyage anomaly detected on {ship_name}. Reasons: {reasons}")

            # Mark as sent
            await db["voyages"].update_one(
                {"_id": voyage["_id"]},
                {"$set": {"alert_sent": True}}
            )

        # 2. Check for Non-Compliant vessels
        non_compliant_ships = await db["ships"].find({"compliance_status": "Non-Compliant"}).to_list(length=100)
        for ship in non_compliant_ships:
            logger.warning(f"🚨 COMPLIANCE ALERT: Vessel {ship.get('name')} is currently NON-COMPLIANT with emissions targets.")

    except Exception as e:
        logger.error(f"Error in smart alert engine: {str(e)}")
    finally:
        client.close()

@celery_app.task(name="run_smart_alerts")
def run_smart_alerts():
    """
    Celery beat task to run the smart alert engine.
    """
    logger.info("Running Smart Alerts engine...")
    asyncio.run(_check_and_send_alerts())
    return "Alerts processed"
