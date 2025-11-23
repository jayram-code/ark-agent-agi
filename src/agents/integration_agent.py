import asyncio
import datetime
import uuid
from typing import Dict, Any

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.observability.logging_utils import log_event
from tools.database_tool import database_tool
from tools.email_tool import email_tool
from tools.google_search_tool import google_search


class IntegrationAgent(BaseAgent):
    """
    Agent responsible for integrating with external systems (e.g., CRM, Ticketing, DB).
    Wraps external APIs and database connections.
    """

    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.tools = {
            "database": database_tool,
            "email": email_tool,
            "search": google_search
        }
        # Ensure tickets table exists
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        database_tool.query("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                priority TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

    async def receive(self, message: AgentMessage):
        log_event("IntegrationAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action")
        response_payload = {}

        try:
            if action == "create_ticket":
                ticket = await self._create_ticket(payload)
                response_payload = {"status": "success", "ticket": ticket}
            elif action == "get_ticket":
                ticket_id = payload.get("ticket_id")
                ticket = await self._get_ticket(ticket_id)
                if ticket:
                    response_payload = {"status": "success", "ticket": ticket}
                else:
                    response_payload = {"status": "error", "message": "Ticket not found"}
            elif action == "update_ticket":
                ticket_id = payload.get("ticket_id")
                updates = payload.get("updates", {})
                ticket = await self._update_ticket(ticket_id, updates)
                if ticket:
                    response_payload = {"status": "success", "ticket": ticket}
                else:
                    response_payload = {"status": "error", "message": "Ticket not found"}
            elif action == "send_email":
                result = await self._send_email(payload)
                response_payload = result
            elif action == "search_web":
                result = await self._search_web(payload)
                response_payload = result
            else:
                response_payload = {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            log_event("IntegrationAgent", {"event": "error", "error": str(e)})
            response_payload = {"status": "error", "message": str(e)}

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="integration_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)

    async def _create_ticket(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
        created_at = str(datetime.datetime.utcnow())
        
        ticket = {
            "id": ticket_id,
            "title": payload.get("title", "Untitled Ticket"),
            "description": payload.get("description", ""),
            "priority": payload.get("priority", "medium"),
            "status": "open",
            "created_at": created_at,
            "updated_at": created_at
        }
        
        database_tool.query(
            "INSERT INTO tickets (id, title, description, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket["id"], ticket["title"], ticket["description"], ticket["priority"], ticket["status"], ticket["created_at"], ticket["updated_at"])
        )
        
        log_event("IntegrationAgent", f"Created ticket {ticket_id}")
        return ticket

    async def _get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        result = database_tool.query("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if result["success"] and result["rows"]:
            return result["rows"][0]
        return None

    async def _update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        current_ticket = await self._get_ticket(ticket_id)
        if not current_ticket:
            return None
            
        # Build update query dynamically
        fields = []
        values = []
        for k, v in updates.items():
            if k in ["title", "description", "priority", "status"]:
                fields.append(f"{k} = ?")
                values.append(v)
        
        if not fields:
            return current_ticket
            
        fields.append("updated_at = ?")
        values.append(str(datetime.datetime.utcnow()))
        
        values.append(ticket_id) # For WHERE clause
        
        query = f"UPDATE tickets SET {', '.join(fields)} WHERE id = ?"
        database_tool.query(query, tuple(values))
        
        return await self._get_ticket(ticket_id)

    async def _send_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await email_tool.execute(
            to=payload.get("to", []),
            subject=payload.get("subject", ""),
            body=payload.get("body", ""),
            html=payload.get("html", False)
        )

    async def _search_web(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await google_search.execute(
            query=payload.get("query", ""),
            num_results=payload.get("num_results", 5)
        )
