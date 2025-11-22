import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from storage.knowledge_base import initialize_kb, search_kb
from utils.logging_utils import log_event


class KnowledgeAgent(BaseAgent):
    def __init__(self, agent_id: str, orchestrator):
        super().__init__(agent_id, orchestrator)
        # Ensure KB is ready on startup
        initialize_kb()

    async def receive(self, message: AgentMessage):
        log_event("KnowledgeAgent", "Searching knowledge base")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        query = payload.get("query") or payload.get("text")

        if not query:
            results = []
            log_event("KnowledgeAgent", "No query provided")
        else:
            try:
                # Run search (synchronous FAISS op)
                results = search_kb(query, k=3)
                log_event("KnowledgeAgent", f"Found {len(results)} results")
            except Exception as e:
                log_event("KnowledgeAgent", f"Error searching KB: {e}")
                results = []

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="knowledge_agent",
            receiver=message.sender,  # Reply to sender
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "results": results,
                "query": query,
                "status": "success" if results else "no_results",
            },
        )

        return await self.orchestrator.send_a2a(response)
