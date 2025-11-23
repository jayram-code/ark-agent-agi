import unittest
import asyncio
import os
import sys
import json
import shutil
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.human_escalation_agent import HumanEscalationAgent
from models.messages import AgentMessage, MessageType

TEST_QUEUE_PATH = "data/test_human_queue.json"

class TestHumanEscalationAgent(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MagicMock()
        self.orchestrator.send_a2a = AsyncMock()
        self.agent = HumanEscalationAgent("human_escalation_agent", self.orchestrator, queue_path=TEST_QUEUE_PATH)
        
        # Clean queue
        with open(TEST_QUEUE_PATH, "w") as f:
            json.dump([], f)

    def tearDown(self):
        if os.path.exists(TEST_QUEUE_PATH):
            os.remove(TEST_QUEUE_PATH)

    def test_escalation_flow(self):
        async def run_test():
            # 1. Escalate Task
            escalate_msg = AgentMessage(
                sender="user_agent",
                receiver="human_escalation_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "escalate",
                    "description": "Review this critical action",
                    "context": {"risk": "high"}
                }
            )
            await self.agent.receive(escalate_msg)
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
                
            self.assertEqual(payload["status"], "escalated")
            task_id = payload["task_id"]
            
            # Verify queue
            with open(TEST_QUEUE_PATH, "r") as f:
                queue = json.load(f)
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["id"], task_id)
            self.assertEqual(queue[0]["status"], "pending")
            
            # 2. Simulate Human Review (via CLI logic)
            # We'll manually update the queue as the CLI would
            queue[0]["status"] = "approved"
            queue[0]["feedback"] = "Looks good"
            with open(TEST_QUEUE_PATH, "w") as f:
                json.dump(queue, f)
                
            # 3. Process Review Response (Triggered by system or CLI sending a message)
            # In our design, the CLI updates the file. The Agent needs to be told to check it or receive a message.
            # The agent has a `review_response` action.
            
            review_msg = AgentMessage(
                sender="cli_tool",
                receiver="human_escalation_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "review_response",
                    "task_id": task_id,
                    "decision": "approved",
                    "feedback": "Looks good"
                }
            )
            await self.agent.receive(review_msg)
            
            # Verify notification to original sender
            # The second call to send_a2a
            self.assertEqual(self.orchestrator.send_a2a.call_count, 2)
            call_args = self.orchestrator.send_a2a.call_args_list[1][0][0]
            
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
                
            self.assertEqual(payload["status"], "reviewed")
            self.assertEqual(payload["decision"], "approved")
            self.assertEqual(call_args.receiver, "user_agent")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
