import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.messages import AgentMessage, MessageType
from policies.routing_policy import RoutingPolicy

class TestRoutingPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RoutingPolicy()

    def test_explicit_receiver(self):
        """Test that explicit receiver is respected"""
        msg = AgentMessage(
            sender="user",
            receiver="specific_agent",
            type=MessageType.TASK_REQUEST,
            payload={"text": "hello"}
        )
        receiver = self.policy.determine_receiver(msg)
        self.assertEqual(receiver, "specific_agent")

    def test_auto_receiver_keyword(self):
        """Test routing based on keywords"""
        msg = AgentMessage(
            sender="user",
            receiver="auto",
            type=MessageType.TASK_REQUEST,
            payload={"text": "I want a refund please"}
        )
        receiver = self.policy.determine_receiver(msg)
        self.assertEqual(receiver, "refund_agent")

        msg_ship = AgentMessage(
            sender="user",
            receiver="auto",
            type=MessageType.TASK_REQUEST,
            payload={"text": "Where is my delivery?"}
        )
        receiver = self.policy.determine_receiver(msg_ship)
        self.assertEqual(receiver, "shipping_agent")

    def test_auto_receiver_intent(self):
        """Test routing based on intent"""
        msg = AgentMessage(
            sender="user",
            receiver="auto",
            type=MessageType.TASK_REQUEST,
            payload={"text": "some text", "intent": "report_issue"}
        )
        receiver = self.policy.determine_receiver(msg)
        self.assertEqual(receiver, "integration_agent")

    def test_fallback(self):
        """Test fallback to supervisor"""
        msg = AgentMessage(
            sender="user",
            receiver="auto",
            type=MessageType.TASK_REQUEST,
            payload={"text": "just saying hello"}
        )
        receiver = self.policy.determine_receiver(msg)
        self.assertEqual(receiver, "supervisor_agent")

if __name__ == "__main__":
    unittest.main()
