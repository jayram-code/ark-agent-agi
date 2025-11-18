from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

class MeetingAgent(BaseAgent):
    def receive(self, message):
        log_event("MeetingAgent", "Processing transcript")
        transcript = message.get("payload", {}).get("transcript", "")
        lines = [l.strip() for l in transcript.splitlines() if l.strip()]
        summary = " ".join(lines[:2]) if lines else ""
        actions = [l for l in lines if l.lower().startswith("action:") or "action item" in l.lower()]
        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "meeting_agent",
            "receiver": "planner_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "summary": summary,
                "action_items": actions,
                "original_transcript": transcript
            }
        }
        return self.orchestrator.send_a2a(response)
