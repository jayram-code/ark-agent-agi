import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.logging_utils import log_event


class HumanEscalationAgent(BaseAgent):
    """
    Agent responsible for handling requests that require human intervention.
    Creates a 'ticket' for human review and returns a pending status.
    """

    async def receive(self, message: AgentMessage):
        log_event("HumanEscalationAgent", f"Received escalation request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        reason = payload.get("reason", "Unknown reason")
        context = payload.get("context", {})
        customer_id = payload.get("customer_id", "Unknown")
        severity = payload.get("severity", "medium")

        # Create a unique ticket ID for this escalation
        ticket_id = f"HIL-{uuid.uuid4().hex[:8].upper()}"

        # Log the escalation (mocking the creation of a task in a dashboard)
        self._create_human_task(ticket_id, customer_id, reason, severity, context)

        response_payload = {
            "status": "escalated_to_human",
            "ticket_id": ticket_id,
            "estimated_wait_time": "24h",
            "message": "Your request has been forwarded to a human specialist.",
        }

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="human_escalation_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)

    def _create_human_task(self, ticket_id, customer_id, reason, severity, context):
        """
        Mock function to create a task in an external system (Jira, Zendesk, internal dashboard)
        """
        print(f"\\n[HumanEscalationAgent] HUMAN INTERVENTION REQUIRED")
        print(f"Ticket ID: {ticket_id}")
        print(f"Customer: {customer_id}")
        print(f"Severity: {severity.upper()}")
        print(f"Reason: {reason}")
        print(f"Context: {str(context)[:200]}...")
        log_event("HumanEscalationAgent", f"Created human task {ticket_id} for {customer_id}")
