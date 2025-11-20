from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.storage.memory_bank import recall_relevant
from src.models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio

class KnowledgeAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("KnowledgeAgent", "Searching knowledge base")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        query = payload.get("query") or payload.get("text")
        
        # Simulate async search
        # In reality, recall_relevant might be synchronous, so we might want to wrap it
        # or just run it if it's fast.
        try:
            # Use recall_relevant from memory_bank (acting as KB search)
            results = recall_relevant(None, query, k=3)
        except Exception:
            results = []
        
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="knowledge_agent",
            receiver=message.sender, # Reply to sender
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "results": results,
                "query": query
            }
        )
        
        return await self.orchestrator.send_a2a(response)
