import unittest
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.notification_agent import NotificationAgent
from models.messages import AgentMessage, MessageType

class TestNotificationAgent(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MagicMock()
        self.orchestrator.send_a2a = AsyncMock()
        self.agent = NotificationAgent("notification_agent", self.orchestrator)
        
        # Mock tools
        self.email_patcher = patch("agents.notification_agent.email_tool")
        self.webhook_patcher = patch("agents.notification_agent.webhook_tool")
        
        self.mock_email_tool = self.email_patcher.start()
        self.mock_webhook_tool = self.webhook_patcher.start()
        
        self.mock_email_tool.execute = AsyncMock(return_value={"success": True})
        self.mock_webhook_tool.execute = AsyncMock(return_value={"success": True})

    def tearDown(self):
        self.email_patcher.stop()
        self.webhook_patcher.stop()

    def test_email_notification(self):
        async def run_test():
            msg = AgentMessage(
                sender="user_agent",
                receiver="notification_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "channel": "email",
                    "recipient": "test@example.com",
                    "subject": "Test Subject",
                    "content": "Test Body"
                }
            )
            await self.agent.receive(msg)
            
            # Verify email tool called
            self.mock_email_tool.execute.assert_called_with(
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body"
            )
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
            self.assertEqual(payload["status"], "sent")

        asyncio.run(run_test())

    def test_slack_notification(self):
        async def run_test():
            # Mock env var
            self.agent.slack_webhook_url = "http://slack.com/webhook"
            
            msg = AgentMessage(
                sender="user_agent",
                receiver="notification_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "channel": "slack",
                    "content": "Slack Message"
                }
            )
            await self.agent.receive(msg)
            
            # Verify webhook tool called
            self.mock_webhook_tool.execute.assert_called_with(
                url="http://slack.com/webhook",
                payload={"text": "Slack Message"}
            )
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
            self.assertEqual(payload["status"], "sent")

        asyncio.run(run_test())

    def test_discord_notification(self):
        async def run_test():
            msg = AgentMessage(
                sender="user_agent",
                receiver="notification_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "channel": "discord",
                    "recipient": "http://discord.com/webhook",
                    "content": "Discord Message"
                }
            )
            await self.agent.receive(msg)
            
            # Verify webhook tool called
            self.mock_webhook_tool.execute.assert_called_with(
                url="http://discord.com/webhook",
                payload={"content": "Discord Message"}
            )

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
