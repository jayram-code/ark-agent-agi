from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio


class ConnectorAgent(BaseAgent):
    """
    Agent responsible for integrating with external systems (e.g., CRM, Ticketing).
    Mocks an OpenAPI client wrapper.
    """

    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        # Mock database for tickets
        self.tickets = {}

    async def receive(self, message: AgentMessage):
        log_event("ConnectorAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action")

        response_payload = {}

        if action == "create_ticket":
            ticket = self._create_ticket(payload)
            response_payload = {"status": "success", "ticket": ticket}
        elif action == "get_ticket":
            ticket_id = payload.get("ticket_id")
            ticket = self._get_ticket(ticket_id)
            if ticket:
                response_payload = {"status": "success", "ticket": ticket}
            else:
                response_payload = {"status": "error", "message": "Ticket not found"}
        elif action == "update_ticket":
            ticket_id = payload.get("ticket_id")
            updates = payload.get("updates", {})
            ticket = self._update_ticket(ticket_id, updates)
            if ticket:
                response_payload = {"status": "success", "ticket": ticket}
            else:
                response_payload = {"status": "error", "message": "Ticket not found"}
        else:
            response_payload = {"status": "error", "message": f"Unknown action: {action}"}

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="connector_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)

    def _create_ticket(self, payload):
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
        ticket = {
            "id": ticket_id,
            "title": payload.get("title", "Untitled Ticket"),
            "description": payload.get("description", ""),
            "priority": payload.get("priority", "medium"),
            "status": "open",
            "created_at": str(datetime.datetime.utcnow()),
        }
        self.tickets[ticket_id] = ticket
        log_event("ConnectorAgent", f"Created ticket {ticket_id}")
        return ticket

    def _get_ticket(self, ticket_id):
        return self.tickets.get(ticket_id)

    def _update_ticket(self, ticket_id, updates):
        if ticket_id in self.tickets:
            self.tickets[ticket_id].update(updates)
            self.tickets[ticket_id]["updated_at"] = str(datetime.datetime.utcnow())
            log_event("ConnectorAgent", f"Updated ticket {ticket_id}")
            return self.tickets[ticket_id]
        return None
