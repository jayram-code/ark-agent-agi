from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from utils.gemini_utils import classify_intent
from models.messages import AgentMessage, MessageType
import uuid, datetime


class EmailAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("EmailAgent", "Processing email with Gemini AI")

        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        text = payload.get("text", "")

        # Use Gemini for intent classification
        intent_result = classify_intent(text)

        # Forward to sentiment agent for next step in pipeline
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="email_agent",
            receiver="sentiment_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "intent": intent_result["intent"],
                "intent_confidence": intent_result["confidence"],
                "text": text,
                "customer_id": payload.get("customer_id"),
                "urgency": intent_result.get("urgency", "medium"),
                "key_phrases": intent_result.get("key_phrases", []),
            },
        )

        return await self.orchestrator.send_a2a(response)
