import asyncio
import datetime
import json
import os
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.logging_utils import log_event


class FeedbackAgent(BaseAgent):
    """
    Agent responsible for collecting and storing customer feedback (CSAT).
    """

    def __init__(self, agent_id, orchestrator, storage_path="evaluation/feedback.json"):
        super().__init__(agent_id, orchestrator)
        self.storage_path = storage_path
        self.feedback_data = self._load_feedback()

    def _load_feedback(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                log_event("FeedbackAgent", f"Error loading feedback: {e}")
        return []

    def _save_feedback(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.feedback_data, f, indent=2)

    async def receive(self, message: AgentMessage):
        log_event("FeedbackAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action")

        response_payload = {}

        if action == "send_survey":
            survey_id = self._send_survey(payload.get("customer_id"), payload.get("ticket_id"))
            response_payload = {"status": "sent", "survey_id": survey_id}
        elif action == "record_feedback":
            self._record_feedback(payload)
            response_payload = {"status": "recorded"}
        elif action == "get_summary":
            summary = self._get_summary()
            response_payload = {"status": "success", "summary": summary}
        else:
            response_payload = {"status": "error", "message": f"Unknown action: {action}"}

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="feedback_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)

    def _send_survey(self, customer_id, ticket_id):
        survey_id = f"SURVEY-{uuid.uuid4().hex[:6]}"
        log_event(
            "FeedbackAgent", f"Sent CSAT survey {survey_id} to {customer_id} for ticket {ticket_id}"
        )
        # In a real system, this would trigger an email/SMS via NotificationAgent
        return survey_id

    def _record_feedback(self, payload):
        entry = {
            "id": str(uuid.uuid4()),
            "ticket_id": payload.get("ticket_id"),
            "score": payload.get("score"),  # 1-5
            "comment": payload.get("comment", ""),
            "timestamp": str(datetime.datetime.utcnow()),
        }
        self.feedback_data.append(entry)
        self._save_feedback()
        log_event(
            "FeedbackAgent",
            f"Recorded feedback score {entry['score']} for ticket {entry['ticket_id']}",
        )

    def _get_summary(self):
        if not self.feedback_data:
            return {"average_score": 0, "count": 0}

        total_score = sum(
            item["score"] for item in self.feedback_data if isinstance(item["score"], (int, float))
        )
        count = len(self.feedback_data)
        return {"average_score": round(total_score / count, 2) if count > 0 else 0, "count": count}
