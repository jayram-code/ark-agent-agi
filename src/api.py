import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.core.orchestrator import Orchestrator
from src.models.messages import AgentMessage, MessageType
from src.agents.email_agent import EmailAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.priority_agent import PriorityAgent
from src.agents.ticket_agent import TicketAgent
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.retryable_agent import RetryableAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.action_executor_agent import ActionExecutorAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.shipping_agent import ShippingAgent
from src.agents.integration_agent import IntegrationAgent
from src.agents.human_escalation_agent import HumanEscalationAgent

app = FastAPI(title="ARK Agent AGI", version="1.0.0")

# Initialize Orchestrator
orchestrator = Orchestrator()

# Register Agents
orchestrator.register_agent("email_agent", EmailAgent("email_agent", orchestrator))
orchestrator.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orchestrator))
orchestrator.register_agent("priority_agent", PriorityAgent("priority_agent", orchestrator))
orchestrator.register_agent("ticket_agent", TicketAgent("ticket_agent", orchestrator))
orchestrator.register_agent("supervisor_agent", SupervisorAgent("supervisor_agent", orchestrator))
orchestrator.register_agent("retryable_agent", RetryableAgent("retryable_agent", orchestrator))
orchestrator.register_agent("planner_agent", PlannerAgent("planner_agent", orchestrator))
orchestrator.register_agent("action_executor_agent", ActionExecutorAgent("action_executor_agent", orchestrator))
orchestrator.register_agent("knowledge_agent", KnowledgeAgent("knowledge_agent", orchestrator))
orchestrator.register_agent("shipping_agent", ShippingAgent("shipping_agent", orchestrator))
orchestrator.register_agent("integration_agent", IntegrationAgent("integration_agent", orchestrator))
orchestrator.register_agent("human_escalation_agent", HumanEscalationAgent("human_escalation_agent", orchestrator))

class MessageRequest(BaseModel):
    text: str
    sender: str = "user"
    session_id: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "healthy", "service": "ark-agent-agi"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: MessageRequest):
    import uuid
    import datetime
    
    session_id = request.session_id or str(uuid.uuid4())
    
    msg = AgentMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        sender=request.sender,
        receiver="email_agent",  # Entry point
        type=MessageType.TASK_REQUEST,
        timestamp=str(datetime.datetime.utcnow()),
        payload={"text": request.text}
    )
    
    try:
        response = await orchestrator.route(msg)
        return {
            "session_id": session_id,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/run")
async def run_agent(request: MessageRequest):
    """API endpoint for web UI"""
    return await chat(request)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
