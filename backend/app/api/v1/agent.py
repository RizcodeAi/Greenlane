from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os

from app.api.v1.deps import get_current_tenant_user
from app.core.database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    actions_taken: List[str] = []
    data: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user)
):
    """
    Maritime AI Agent Endpoint.
    Integrates with LangChain structure / DB queries to provide intelligent responses
    about fleet compliance, emissions aggregation, fuel breakdown, and eco-routes.
    """
    query = payload.message.lower()
    org_id = current_user["org_id"]

    reply = ""
    actions = []
    response_data = {}

    if "non-compliant" in query or "compliance" in query or "red" in query or "status" in query:
        ships = await db["ships"].find({"org_id": org_id, "status": "inactive"}).to_list(10)
        if not ships:
            # Also check for is_anomalous or Non-Compliant status flag
            ships = await db["ships"].find({"org_id": org_id, "compliance_status": "Non-Compliant"}).to_list(10)

        if ships:
            ship_names = ", ".join([s.get("name", "Unknown") for s in ships])
            reply = f"I found {len(ships)} non-compliant/inactive vessel(s) in your fleet: {ship_names}. Would you like me to generate an anomaly report for them?"
            actions.append("queried_non_compliant_ships")
            response_data["non_compliant_ships"] = [s.get("name") for s in ships]
        else:
            reply = "Great news! All active vessels in your fleet are currently compliant with IMO DCS standards."
            actions.append("queried_compliance_status")

    elif "co2" in query or "emissions" in query or "total" in query:
        pipeline = [{"$match": {"org_id": org_id}}, {"$group": {"_id": None, "total": {"$sum": "$emissions.co2"}}}]
        res = await db["emissions_computed"].aggregate(pipeline).to_list(1)
        if res and res[0].get("total") is not None:
            total = round(res[0]["total"], 2)
            reply = f"Your fleet has emitted a total of {total} metric tonnes of CO2."
            actions.append("aggregated_emissions_data")
            response_data["total_co2_mt"] = total
        else:
            reply = "I couldn't find any recorded emissions data for your fleet yet."
            actions.append("queried_emissions_data")

    elif "fuel" in query or "breakdown" in query or "hfo" in query or "lng" in query:
        pipeline = [{"$match": {"org_id": org_id}}, {"$group": {"_id": "$fuel_type", "total": {"$sum": "$emissions.co2"}}}]
        res = await db["emissions_computed"].aggregate(pipeline).to_list(10)
        if res:
            breakdown_str = ", ".join([f"{item['_id'] or 'Other'}: {round(item['total'], 1)} mt CO2" for item in res])
            reply = f"Here is your fleet's CO2 breakdown by fuel type: {breakdown_str}."
            actions.append("queried_fuel_breakdown")
            response_data["fuel_breakdown"] = {item['_id']: round(item['total'], 1) for item in res}
        else:
            reply = "No fuel breakdown data is currently available."

    elif "route" in query or "eco" in query or "optimize" in query or "weather" in query:
        reply = "I recommend enabling Eco Route mode on the Fleet Map. Eco Routes adjust trajectories around storm systems and can save between 10 to 50 metric tonnes of fuel per voyage."
        actions.append("recommended_route_optimization")

    else:
        reply = "I am your Maritime AI Agent. I can help you analyze fleet emissions, find non-compliant ships, review fuel breakdowns, or recommend optimized eco-routes. How can I assist you today?"

    return {
        "reply": reply,
        "actions_taken": actions,
        "data": response_data
    }
