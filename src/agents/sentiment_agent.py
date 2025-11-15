from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

class SentimentAgent(BaseAgent):
    def receive(self, message):
        log_event("SentimentAgent", "Scoring sentiment")

        text = message["payload"]["text"].lower()

        if "angry" in text or "not received" in text:
            score = -0.8
        else:
            score = 0.2

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "sentiment_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": message["payload"]["intent"],
                "text": message["payload"]["text"],
                "sentiment_score": score
            }
        }

        return self.orchestrator.route(response)
