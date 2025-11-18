from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.rag import retrieve
import uuid, datetime

class KnowledgeAgent(BaseAgent):
    def receive(self, message):
        log_event("KnowledgeAgent", "Retrieving KB passages")
        query = message.get("payload", {}).get("text", "") or message.get("payload", {}).get("query", "")
        try:
            results = retrieve(query, k=3)
        except Exception as e:
            results = []
            log_event("KnowledgeAgent", f"RAG error: {e}")
        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "knowledge_agent",
            "receiver": message.get("payload", {}).get("next", "planner_agent"),
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "kb": results,
                "original": message.get("payload", {})
            }
        }
        return self.orchestrator.send_a2a(response)
