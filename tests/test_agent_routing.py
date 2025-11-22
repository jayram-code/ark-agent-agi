"""
Unit Tests for Agent Routing
Tests orchestrator routing logic, broadcasts, and agent registration
"""

import unittest
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator import Orchestrator
from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType

class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, name, orchestrator):
        super().__init__(name, orchestrator)
        self.received_messages = []
    
    async def receive(self, message: AgentMessage):
        self.received_messages.append(message)
        return {
            "status": "success",
            "agent": self.name,
            "received_id": message.id
        }

class TestAgentRouting(unittest.TestCase):
    """Test orchestrator routing functionality"""
    
    def setUp(self):
        """Set up test orchestrator and agents"""
        self.orc = Orchestrator()
        self.agent1 = MockAgent("agent1", self.orc)
        self.agent2 = MockAgent("agent2", self.orc)
        self.orc.register_agent("agent1", self.agent1)
        self.orc.register_agent("agent2", self.agent2)
    
    def test_agent_registration(self):
        """Test agent registration"""
        self.assertIn("agent1", self.orc.agents)
        self.assertIn("agent2", self.orc.agents)
        self.assertEqual(self.orc.agents["agent1"], self.agent1)
    
    def test_basic_routing(self):
        """Test basic message routing"""
        message = self.orc.new_message(
            sender="test",
            receiver="agent1",
            type=MessageType.TASK_REQUEST,
            payload={"test": "data"}
        )
        
        result = asyncio.run(self.orc.route(message))
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["agent"], "agent1")
        self.assertEqual(len(self.agent1.received_messages), 1)
    
    def test_unknown_agent(self):
        """Test routing to unknown agent raises error"""
        message = self.orc.new_message(
            sender="test",
            receiver="unknown_agent",
            type=MessageType.TASK_REQUEST,
            payload={}
        )
        
        with self.assertRaises(ValueError) as context:
            asyncio.run(self.orc.route(message))
        
        self.assertIn("Unknown agent", str(context.exception))
    
    def test_broadcast(self):
        """Test broadcast to multiple agents"""
        message = self.orc.new_message(
            sender="test",
            receiver="",  # Will be set by broadcast
            type=MessageType.INFO,
            payload={"broadcast": "data"}
        )
        
        results = asyncio.run(self.orc.broadcast(message, ["agent1", "agent2"]))
        
        self.assertEqual(len(results), 2)
        self.assertIn("agent1", results)
        self.assertIn("agent2", results)
        self.assertEqual(len(self.agent1.received_messages), 1)
        self.assertEqual(len(self.agent2.received_messages), 1)
    
    def test_message_trace_id(self):
        """Test trace ID is set on messages"""
        message = self.orc.new_message(
            sender="test",
            receiver="agent1",
            type=MessageType.TASK_REQUEST,
            payload={}
        )
        
        asyncio.run(self.orc.send_a2a(message))
        
        self.assertIsNotNone(message.trace_id)
    
    def test_pause_resume_routing(self):
        """Test routing with paused agents"""
        # Pause agent1
        pause_result = self.orc.pause_agent("agent1")
        self.assertTrue(pause_result["success"])
        
        # Send message to paused agent
        message = self.orc.new_message(
            sender="test",
            receiver="agent1",
            type=MessageType.INFO,
            payload={"test": "data"}
        )
        
        result = asyncio.run(self.orc.route(message))
        
        # Should be queued, not delivered
        self.assertEqual(result["status"], "queued")
        self.assertEqual(len(self.agent1.received_messages), 0)
        
        # Resume agent
        resume_result = asyncio.run(self.orc.resume_agent("agent1"))
        self.assertTrue(resume_result["success"])
        self.assertEqual(resume_result["delivered_count"], 1)

def run_tests():
    """Run routing tests"""
    print("=" * 70)
    print("Running Agent Routing Tests")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAgentRouting)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nTests run: {result.testsRun}")
    print(f"Success: {result.wasSuccessful()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
