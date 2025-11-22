import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.logging_utils import log_event


class ActionExecutorAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("ActionExecutorAgent", "Executing action plan")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        plan = payload.get("plan", {})
        tasks = plan.get("tasks", [])

        results = []
        for task in tasks:
            # Simulate execution
            log_event(
                "ActionExecutorAgent", {"executing": task.get("action"), "step": task.get("step")}
            )
            # In a real system, this would call external APIs
            # Simulate async work
            await asyncio.sleep(0.1)
            results.append(
                {
                    "step": task.get("step"),
                    "status": "completed",
                    "outcome": task.get("expected_outcome"),
                }
            )

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="action_executor_agent",
            receiver="ticket_agent",  # Report back to ticket agent to close/update ticket
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "status": "execution_complete",
                "results": results,
                "original_payload": payload.get("original_payload"),
            },
        )

        return await self.orchestrator.send_a2a(response)
