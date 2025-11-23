import asyncio
import datetime
import uuid
import os
from typing import Dict, Any

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.observability.logging_utils import log_event
from tools.email_tool import email_tool
from tools.webhook_tool import webhook_tool


class NotificationAgent(BaseAgent):
    """
    Agent responsible for sending external notifications (Email, SMS, Slack).
    Uses EmailTool and WebhookTool for actual delivery.
    """

    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        # Load webhook URLs from env or config
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    async def receive(self, message: AgentMessage):
        log_event("NotificationAgent", f"Received notification request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        channel = payload.get("channel", "email").lower()
        recipient = payload.get("recipient")
        content = payload.get("content") or payload.get("text")
        subject = payload.get("subject", "Notification")

        if not content:
            error_msg = "Missing content"
            log_event("NotificationAgent", f"Error: {error_msg}")
            return await self._send_response(message, {"status": "failed", "error": error_msg})

        success = False
        delivery_details = {}
        error_msg = None

        try:
            if channel == "email":
                if not recipient:
                    raise ValueError("Recipient required for email")
                result = await self._send_email(recipient, subject, content)
                success = result["success"]
                delivery_details = result
            elif channel == "slack":
                # Recipient can be override webhook url, otherwise use default
                webhook_url = recipient if recipient and recipient.startswith("http") else self.slack_webhook_url
                if not webhook_url:
                    raise ValueError("No Slack webhook URL configured")
                result = await self._send_slack(webhook_url, content)
                success = result["success"]
                delivery_details = result
            elif channel == "discord":
                webhook_url = recipient if recipient and recipient.startswith("http") else self.discord_webhook_url
                if not webhook_url:
                    raise ValueError("No Discord webhook URL configured")
                result = await self._send_discord(webhook_url, content)
                success = result["success"]
                delivery_details = result
            else:
                error_msg = f"Unknown channel: {channel}"
                log_event("NotificationAgent", error_msg)
                success = False
                delivery_details = {"error": error_msg}
        except Exception as e:
            log_event("NotificationAgent", f"Delivery failed: {e}")
            success = False
            error_msg = str(e)
            delivery_details = {"error": str(e)}

        status = "sent" if success else "failed"
        log_event("NotificationAgent", f"Notification {status} via {channel}")

        return await self._send_response(
            message,
            {
                "status": status,
                "error": error_msg,
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

    async def _send_email(self, to, subject, body):
        return await email_tool.execute(
            to=[to],
            subject=subject,
            body=body
        )

    async def _send_slack(self, webhook_url, message):
        return await webhook_tool.execute(
            url=webhook_url,
            payload={"text": message}
        )

    async def _send_discord(self, webhook_url, message):
        return await webhook_tool.execute(
            url=webhook_url,
            payload={"content": message}
        )
