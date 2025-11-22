from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from storage.memory_bank import store_interaction, recall_relevant, get_recent
from models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio

class MemoryAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("MemoryAgent", "Memory action")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        action = payload.get("action", "add")  # add | query | recent
        customer_id = payload.get("customer_id", "unknown")
        
        # Simulate async DB operations
        await asyncio.sleep(0.05)
        
        if action == "add":
            kind = payload.get("kind", "note")
            content = payload.get("content", "")
            # Use store_interaction from memory_bank
            rowid = store_interaction(customer_id, kind, content)
            result_payload = {"status": "memory_added", "id": rowid}
            
        elif action == "recent":
            rows = get_recent(customer_id, limit=payload.get("limit", 5))
            result_payload = {"status": "memory_recent", "rows": rows}
            
        else: # query
            q = payload.get("query", "")
            # Use recall_relevant from memory_bank
            rows = recall_relevant(customer_id if customer_id != "" else None, q, k=payload.get("k", 3))
            result_payload = {"status": "memory_recall", "rows": rows}
            
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="memory_agent",
            receiver=message.sender, # Reply to sender
            type=MessageType.INFO,
            timestamp=str(datetime.datetime.utcnow()),
            payload=result_payload
        )
        
        return await self.orchestrator.send_a2a(response)
