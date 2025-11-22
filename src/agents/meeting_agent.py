from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio


class MeetingAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("MeetingAgent", "Scheduling meeting")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        participants = payload.get("participants", [])
        time_slot = payload.get("time_slot")
        topic = payload.get("topic")

        # Simulate scheduling
        await asyncio.sleep(0.2)

        meeting_id = f"mtg_{uuid.uuid4().hex[:8]}"

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="meeting_agent",
            receiver="email_sender_agent",  # Send invites
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "recipient": participants[0] if participants else "organizer@example.com",
                "subject": f"Meeting Invitation: {topic}",
                "template": "general_followup",  # Using generic for now
                "variables": {
                    "followup_message": f"Meeting scheduled for {time_slot}. ID: {meeting_id}"
                },
                "meeting_details": {
                    "id": meeting_id,
                    "time": time_slot,
                    "participants": participants,
                },
            },
        )

        return await self.orchestrator.send_a2a(response)
