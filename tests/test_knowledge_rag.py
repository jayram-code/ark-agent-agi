import unittest
import asyncio
import os
import sys
import shutil
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from tools.vector_db_tool import VectorDBTool
from agents.knowledge_agent import KnowledgeAgent
from models.messages import AgentMessage, MessageType

TEST_INDEX_PATH = "data/test_vector_store.index"
TEST_METADATA_PATH = "data/test_vector_metadata.pkl"

class TestVectorDBTool(unittest.TestCase):
    def setUp(self):
        # Use a very small model or mock embedding to speed up tests
        # For now we use the real one but with small data
        self.tool = VectorDBTool(index_path=TEST_INDEX_PATH, metadata_path=TEST_METADATA_PATH)
        
    def tearDown(self):
        if os.path.exists(TEST_INDEX_PATH):
            os.remove(TEST_INDEX_PATH)
        if os.path.exists(TEST_METADATA_PATH):
            os.remove(TEST_METADATA_PATH)

    def test_add_and_search(self):
        texts = ["The sky is blue", "The grass is green", "The sun is yellow"]
        metadatas = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        # Add
        result = self.tool.add_texts(texts, metadatas)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 3)
        
        # Search
        result = self.tool.search("what color is the sky?", k=1)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["text"], "The sky is blue")
        self.assertGreater(result["results"][0]["score"], 0)

    def test_persistence(self):
        texts = ["Persistent memory"]
        self.tool.add_texts(texts)
        
        # Create new instance
        new_tool = VectorDBTool(index_path=TEST_INDEX_PATH, metadata_path=TEST_METADATA_PATH)
        result = new_tool.search("memory", k=1)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["results"][0]["text"], "Persistent memory")


class TestKnowledgeAgent(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MagicMock()
        self.orchestrator.send_a2a = AsyncMock()
        self.agent = KnowledgeAgent("knowledge_agent", self.orchestrator)
        
        # Mock vector_db tool used by agent
        # We need to patch the global 'vector_db' instance in knowledge_agent module
        self.patcher = patch("agents.knowledge_agent.vector_db")
        self.mock_vector_db = self.patcher.start()
        self.mock_vector_db.execute = AsyncMock()

    def tearDown(self):
        self.patcher.stop()

    def test_ingest_flow(self):
        async def run_test():
            msg = AgentMessage(
                sender="user",
                receiver="knowledge_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "ingest",
                    "text": "Important knowledge",
                    "source": "doc1"
                }
            )
            self.mock_vector_db.execute.return_value = {"success": True, "count": 1}
            
            await self.agent.receive(msg)
            
            # Verify tool call
            self.mock_vector_db.execute.assert_called_with(
                action="add",
                texts=["Important knowledge"],
                metadatas=[{"source": "doc1"}]
            )
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
            self.assertEqual(payload["status"], "success")

        asyncio.run(run_test())

    def test_query_flow(self):
        async def run_test():
            msg = AgentMessage(
                sender="user",
                receiver="knowledge_agent",
                type=MessageType.TASK_REQUEST,
                payload={
                    "action": "query",
                    "query": "test query"
                }
            )
            self.mock_vector_db.execute.return_value = {
                "success": True, 
                "results": [{"text": "match", "score": 0.9}]
            }
            
            await self.agent.receive(msg)
            
            # Verify tool call
            self.mock_vector_db.execute.assert_called_with(
                action="search",
                query="test query",
                k=3
            )
            
            # Verify response
            call_args = self.orchestrator.send_a2a.call_args[0][0]
            payload = call_args.payload
            if hasattr(payload, "dict"):
                payload = payload.dict()
            self.assertEqual(payload["results"][0]["text"], "match")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
