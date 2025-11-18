from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

class EmailAgent(BaseAgent):
    def receive(self, message):
        log_event("EmailAgent", "Processing email")

        email_text = message["payload"]["text"].lower()

        if "not received" in email_text or "angry" in email_text:
            intent = "complaint"
        else:
            intent = "general_query"

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "email_agent",
            "receiver": "sentiment_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": intent,
                "text": message["payload"]["text"]
            }
        }

        return self.orchestrator.send_a2a(response)
