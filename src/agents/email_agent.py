from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.gemini_utils import classify_intent
import uuid, datetime

class EmailAgent(BaseAgent):
    def receive(self, message):
        log_event("EmailAgent", "Processing email with Gemini AI")

        email_text = message["payload"]["text"]
        
        # Use Gemini for intelligent intent classification
        intent_analysis = classify_intent(email_text)
        
        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "email_agent",
            "receiver": "sentiment_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": intent_analysis["intent"],
                "text": email_text,
                "intent_confidence": intent_analysis["confidence"],
                "urgency": intent_analysis["urgency"],
                "key_phrases": intent_analysis["key_phrases"]
            }
        }

        return self.orchestrator.send_a2a(response)
