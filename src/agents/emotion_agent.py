from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio

class EmotionAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("EmotionAgent", "Analyzing emotion")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        audio_url = payload.get("audio_url")
        text = payload.get("text")
        
        # Simulate emotion analysis
        await asyncio.sleep(0.1)
        
        stress_level = 0.2
        if text and "angry" in text.lower():
            stress_level = 0.8
            
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="emotion_agent",
            receiver="sentiment_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "stress": stress_level,
                "call_label": "neutral" if stress_level < 0.5 else "escalated",
                "text": text,
                "customer_id": payload.get("customer_id")
            }
        )
        
        return await self.orchestrator.send_a2a(response)
