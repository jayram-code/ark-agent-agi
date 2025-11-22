import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.logging_utils import log_event


class NotificationAgent(BaseAgent):
    """
    Agent responsible for sending external notifications (Email, SMS, Slack).
    Currently mocks the actual delivery but logs the intent.
    """

    async def receive(self, message: AgentMessage):
        log_event("NotificationAgent", f"Received notification request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        channel = payload.get("channel", "email").lower()
        recipient = payload.get("recipient")
        content = payload.get("content") or payload.get("text")
        subject = payload.get("subject", "Notification")

        if not recipient or not content:
            error_msg = "Missing recipient or content"
            log_event("NotificationAgent", f"Error: {error_msg}")
            return await self._send_response(message, {"status": "failed", "error": error_msg})

        # Mock delivery logic
        success = True
        delivery_details = {}

        try:
            if channel == "email":
                self._send_email(recipient, subject, content)
                delivery_details = {"channel": "email", "sent_to": recipient}
            elif channel == "sms":
                self._send_sms(recipient, content)
                delivery_details = {"channel": "sms", "sent_to": recipient}
            elif channel == "slack":
                self._send_slack(recipient, content)
                delivery_details = {"channel": "slack", "sent_to": recipient}
            else:
                log_event("NotificationAgent", f"Unknown channel: {channel}")
                success = False
                delivery_details = {"error": f"Unknown channel {channel}"}
        except Exception as e:
            log_event("NotificationAgent", f"Delivery failed: {e}")
            success = False
            delivery_details = {"error": str(e)}

        status = "sent" if success else "failed"
        log_event("NotificationAgent", f"Notification {status} to {recipient} via {channel}")

        return await self._send_response(
            message,
            {
                "status": status,
                "details": delivery_details,
                "timestamp": str(datetime.datetime.utcnow()),
            },
        )

    async def _send_response(self, original_message, payload):
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=original_message.session_id,
            sender="notification_agent",
            receiver=original_message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=payload,
        )
        return await self.orchestrator.send_a2a(response)

    def _send_email(self, to, subject, body):
        print(f"\\n[NotificationAgent] SENDING EMAIL to {to}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body}")
        return True

    def _send_sms(self, to, body):
        print(f"\\n[NotificationAgent] SENDING SMS to {to}")
        print(f"   Body: {body}")
        return True

    def _send_slack(self, channel, message):
        print(f"\\n[NotificationAgent] SENDING SLACK to {channel}")
        print(f"   Message: {message}")
        return True
