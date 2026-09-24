from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(
    settings.mongodb_url,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    connectTimeoutMS=10000,
    socketTimeoutMS=30000,
    serverSelectionTimeoutMS=10000,
    replicaSet=settings.MONGODB_REPLICA_SET,
    w="majority",
    journal=True,
    readPreference="secondaryPreferred",
    retryWrites=True,
)
db = client[settings.database_name]


async def get_db():
    yield db


async def close_db():
    client.close()


async def init_db_indexes(db):
    """Create essential indexes for collections at app startup."""
    # users: unique email
    await db["users"].create_index("email", unique=True)

    # ships: unique (org_id, imo_number), and (org_id, created_at)
    await db["ships"].create_index([("org_id", 1), ("imo_number", 1)], unique=True)
    await db["ships"].create_index([("org_id", 1), ("created_at", 1)])

    # voyages: (org_id, asset_id) and (org_id, departure_date)
    await db["voyages"].create_index([("org_id", 1), ("asset_id", 1)])
    await db["voyages"].create_index([("org_id", 1), ("departure_date", 1)])

    # emissions_computed: (voyage_id, is_current) and (org_id, calculated_at)
    await db["emissions_computed"].create_index([("voyage_id", 1), ("is_current", 1)])
    await db["emissions_computed"].create_index([("org_id", 1), ("calculated_at", 1)])

    # reports: (org_id, year)
    await db["reports"].create_index([("org_id", 1), ("year", 1)])

    # audit_logs: (org_id, timestamp) with TTL for auto-expiry after 1 year
    await db["audit_logs"].create_index([("org_id", 1), ("timestamp", 1)])
    await db["audit_logs"].create_index("timestamp", expireAfterSeconds=31536000)

    # ships: single-field indexes for regex search
    await db["ships"].create_index("name")
    await db["ships"].create_index("imo_number")

    # ships: additional indexes
    await db["ships"].create_index([("org_id", 1), ("status", 1)])
    await db["ships"].create_index([("org_id", 1), ("compliance_status", 1)])
    await db["ships"].create_index([("org_id", 1), ("name", 1)])

    # voyages: index for org_id + voyage_id on emissions
    await db["emissions_computed"].create_index([("org_id", 1), ("voyage_id", 1)])
    await db["emissions_computed"].create_index([("org_id", 1), ("generated_at", -1)])
    await db["emissions_computed"].create_index([("voyage_id", 1), ("is_current", 1)], unique=True, partialFilterExpression={"is_current": True}, name="voyage_id_1_is_current_1_partial")

    # voyages: indexes for created_at (sort) and asset_id (query)
    await db["voyages"].create_index("created_at")
    await db["voyages"].create_index("asset_id")

    # emissions_computed: index for calculation_version (sort)
    await db["emissions_computed"].create_index("calculation_version")

    # users: index for org_id
    await db["users"].create_index([("org_id", 1)])

    # organizations: index for name
    await db["organizations"].create_index([("name", 1)])

    # reports: index for org_id + generated_at
    await db["reports"].create_index([("org_id", 1), ("generated_at", -1)])
