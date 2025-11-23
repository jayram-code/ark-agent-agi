import unittest
import asyncio
import os
import sys
import shutil
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.observability.metrics import MetricsCollector
from utils.observability.session_logger import SessionLogger

TEST_METRICS_FILE = "data/test_metrics.json"
TEST_SESSIONS_DIR = "data/test_sessions"

class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        self.collector = MetricsCollector(metrics_file=TEST_METRICS_FILE)
        
    def tearDown(self):
        if os.path.exists(TEST_METRICS_FILE):
            os.remove(TEST_METRICS_FILE)

    def test_record_and_stats(self):
        # Record some metrics
        self.collector.record_message("test_agent", 100.0, True, tokens_used=50)
        self.collector.record_message("test_agent", 200.0, True, tokens_used=100)
        self.collector.record_message("test_agent", 150.0, False, tokens_used=0)
        
        # Get stats
        stats = self.collector.get_stats("test_agent")
        
        self.assertEqual(stats["count"], 3)
        self.assertAlmostEqual(stats["success_rate"], 66.67, places=1)
        self.assertAlmostEqual(stats["avg_latency_ms"], 150.0, places=1)
        self.assertEqual(stats["total_tokens"], 150)

    def test_global_stats(self):
        self.collector.record_message("agent1", 100.0, True)
        self.collector.record_message("agent2", 200.0, True)
        
        stats = self.collector.get_stats()
        
        self.assertIn("agent1", stats)
        self.assertIn("agent2", stats)
        self.assertIn("_global", stats)
        self.assertEqual(stats["_global"]["count"], 2)


class TestSessionLogger(unittest.TestCase):
    def setUp(self):
        self.logger = SessionLogger(sessions_dir=TEST_SESSIONS_DIR)
        
    def tearDown(self):
        if os.path.exists(TEST_SESSIONS_DIR):
            shutil.rmtree(TEST_SESSIONS_DIR)

    def test_log_and_retrieve(self):
        session_id = "test-session-001"
        
        # Log messages
        self.logger.log_message(session_id, {"sender": "user", "text": "hello"})
        self.logger.log_message(session_id, {"sender": "agent", "text": "hi there"})
        
        # Retrieve
        messages = self.logger.get_session(session_id)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["sender"], "user")
        self.assertEqual(messages[1]["sender"], "agent")

    def test_list_sessions(self):
        self.logger.log_message("session1", {"text": "msg1"})
        self.logger.log_message("session2", {"text": "msg2"})
        
        sessions = self.logger.list_sessions()
        
        self.assertEqual(len(sessions), 2)
        self.assertIn("session1", sessions)
        self.assertIn("session2", sessions)


if __name__ == "__main__":
    unittest.main()
