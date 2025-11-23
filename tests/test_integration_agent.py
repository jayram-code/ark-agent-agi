import unittest
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.integration_agent import IntegrationAgent
from models.messages import AgentMessage, MessageType
from tools.database_tool import database_tool

class TestIntegrationAgent(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MagicMock()
        self.orchestrator.send_a2a = AsyncMock()
        self.agent = IntegrationAgent("integration_agent", self.orchestrator)
        
        # Reset DB
        database_tool.query("DELETE FROM tickets")

    def test_ticket_lifecycle(self):
        async def run_test():
            # 1. Create Ticket
            create_msg = AgentMessage(
                sender="user_agent",
                receiver="integration_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "create_ticket",
                    "title": "Test Ticket",
                    "description": "This is a test",
                    "priority": "high"
                }
            )
            await self.agent.receive(create_msg)
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
            
            self.assertEqual(payload["status"], "success")
            ticket_id = payload["ticket"]["id"]
            self.assertEqual(payload["ticket"]["title"], "Test Ticket")
            
            # 2. Get Ticket
            get_msg = AgentMessage(
                sender="user_agent",
                receiver="integration_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "get_ticket",
                    "ticket_id": ticket_id
                }
            )
            await self.agent.receive(get_msg)
            
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
                
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["ticket"]["id"], ticket_id)
            
            # 3. Update Ticket
            update_msg = AgentMessage(
                sender="user_agent",
                receiver="integration_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "update_ticket",
                    "ticket_id": ticket_id,
                    "updates": {"status": "closed"}
                }
            )
            await self.agent.receive(update_msg)
            
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
                
            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["ticket"]["status"], "closed")
            
            # Verify in DB directly
            result = database_tool.query("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
            self.assertEqual(result["rows"][0]["status"], "closed")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
