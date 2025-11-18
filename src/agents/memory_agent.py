from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.storage.memory_bank import store_interaction, recall_relevant, get_recent
import uuid, datetime

class MemoryAgent(BaseAgent):
    def receive(self, message):
        log_event("MemoryAgent", "Memory action")
        payload = message.get("payload", {})
        action = payload.get("action", "add")  # add | query | recent
        customer_id = payload.get("customer_id", "unknown")
        if action == "add":
            kind = payload.get("kind", "note")
            content = payload.get("content", "")
            rowid = store_interaction(customer_id, kind, content)
            return {"status": "memory_added", "id": rowid}
        elif action == "recent":
            rows = get_recent(customer_id, limit=payload.get("limit", 5))
            return {"status": "memory_recent", "rows": rows}
        else:
            q = payload.get("query", "")
            rows = recall_relevant(customer_id if customer_id != "" else None, q, k=payload.get("k", 3))
            return {"status": "memory_recall", "rows": rows}
from src.storage.memory_bank import init, store_interaction, get_recent, recall_relevant
print("init")
init()
print("store")
id1 = store_interaction("C100","ticket","Customer reported missing order #999")
id2 = store_interaction("C100","note","Called customer; awaiting reply")
print("recent:", get_recent("C100"))
print("recall:", recall_relevant("C100","missing order", k=3))
