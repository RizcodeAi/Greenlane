from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
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

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_tenant_user)
):
    """
    Maritime AI Agent Endpoint.
    Integrates with LangChain to provide intelligent responses about fleet compliance and data.
    """

    # We will build a mock logic structure here because calling an actual OpenAI endpoint
    # requires an API key in the environment, which we don't assume exists right now.
    # In a full deployment, this is where you'd initialize ChatOpenAI and a LangChain AgentExecutor.

    query = payload.message.lower()
    org_id = current_user["org_id"]

    reply = ""
    actions = []

    if "non-compliant" in query or "red" in query or "bad" in query:
        ships = await db["ships"].find({"org_id": org_id, "compliance_status": "Non-Compliant"}).to_list(10)
        if ships:
            ship_names = ", ".join([s["name"] for s in ships])
            reply = f"I found {len(ships)} non-compliant vessels in your fleet: {ship_names}. Would you like me to generate an anomaly report for them?"
            actions.append("queried_non_compliant_ships")
        else:
            reply = "Great news! You currently have no non-compliant vessels in your fleet."

    elif "co2" in query or "emissions" in query or "total" in query:
        # Aggregate total CO2
        pipeline = [{"$match": {"org_id": org_id}}, {"$group": {"_id": None, "total": {"$sum": "$emissions.co2"}}}]
        res = await db["emissions_computed"].aggregate(pipeline).to_list(1)
        if res:
            total = round(res[0]["total"], 2)
            reply = f"Your fleet has emitted a total of {total} metric tonnes of CO2 this year."
            actions.append("aggregated_emissions_data")
        else:
            reply = "I couldn't find any recorded emissions data for your fleet yet."

    else:
        reply = "I am your Maritime AI Agent. I can help you analyze fleet emissions, find non-compliant ships, or explain weather patterns affecting your routes. How can I assist you today?"

    return {
        "reply": reply,
        "actions_taken": actions
    }
