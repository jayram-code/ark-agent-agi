from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from utils.gemini_utils import generate_task_plan
from models.messages import AgentMessage, MessageType
import uuid, datetime


class PlannerAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("PlannerAgent", "Generating plan with Gemini AI")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        # Extract context
        text = payload.get("text") or payload.get("original_payload", {}).get("text", "")
        intent = payload.get("intent")

        # Generate plan using Gemini
        # Note: generate_task_plan is synchronous, but we can run it directly if it's fast enough,
        # or wrap it if it's blocking. For now assuming it's acceptable or will be made async later.
        plan = generate_task_plan(text, {"intent": intent})

        # Forward to Supervisor for validation/execution
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="planner_agent",
            receiver="supervisor_agent",  # Supervisor checks plan before execution
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={"plan": plan, "original_payload": payload, "status": "plan_generated"},
        )

        return await self.orchestrator.send_a2a(response)
