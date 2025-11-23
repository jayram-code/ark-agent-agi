import asyncio
import datetime
import uuid
from typing import Dict, Any

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from tools.vector_db_tool import vector_db
from utils.observability.logging_utils import log_event


class KnowledgeAgent(BaseAgent):
    """
    Agent responsible for managing and retrieving knowledge from the Vector DB.
    """

    def __init__(self, agent_id: str, orchestrator):
        super().__init__(agent_id, orchestrator)
        # Vector DB is initialized in the tool itself

    async def receive(self, message: AgentMessage):
        log_event("KnowledgeAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action", "query")
        response_payload = {}

        try:
            if action == "query":
                query = payload.get("query") or payload.get("text")
                if not query:
                    response_payload = {"status": "error", "message": "No query provided"}
                else:
                    result = await vector_db.execute(action="search", query=query, k=3)
                    response_payload = result
            
            elif action == "ingest":
                text = payload.get("text")
                if not text:
                    response_payload = {"status": "error", "message": "No text provided"}
                else:
                    # Simple ingestion: treat whole text as one chunk for now
                    # In a real system, we'd split this
                    result = await vector_db.execute(
                        action="add", 
                        texts=[text], 
                        metadatas=[{"source": payload.get("source", "user_input")}]
                    )
                    response_payload = result
                    response_payload["status"] = "success" if result.get("success") else "error"
            
            else:
                response_payload = {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            log_event("KnowledgeAgent", f"Error: {e}")
            response_payload = {"status": "error", "message": str(e)}

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="knowledge_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)
