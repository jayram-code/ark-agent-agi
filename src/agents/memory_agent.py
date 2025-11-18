from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.storage.memory import add_memory, get_recent
import uuid, datetime

class MemoryAgent(BaseAgent):
    def receive(self, message):
        log_event("MemoryAgent", "Memory action")
        payload = message.get("payload", {})
        action = payload.get("action","add")  # add | query
        customer_id = payload.get("customer_id","unknown")
        if action == "add":
            kind = payload.get("kind","note")
            content = payload.get("content","")
            add_memory(customer_id, kind, content)
            return {"status":"memory_added"}
        else:
            rows = get_recent(customer_id, limit=payload.get("limit",5))
            return {"status":"memory_query", "rows": rows}
