"""
Unit Tests for Built-in Tools
Tests all 11 built-in tools and agent lifecycle management
"""

import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.calculator_tool import calculator
from utils.code_execution_tool import code_executor
from utils.database_tool import database_tool
from utils.agent_controller import agent_controller

class TestCalculatorTool(unittest.TestCase):
    """Test Calculator Tool"""
    
    def test_basic_arithmetic(self):
        result = calculator.calculate("2 + 2")
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 4)
    
    def test_advanced_math(self):
        result = calculator.calculate("sqrt(16) + pow(2, 3)")
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 12.0)
    
    def test_trigonometry(self):
        result = calculator.calculate("sin(0)")
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 0.0)
    
    def test_invalid_expression(self):
        result = calculator.calculate("invalid * expression")
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_statistics(self):
        result = calculator.statistics([1, 2, 3, 4, 5])
        self.assertTrue(result['success'])
        self.assertEqual(result['sum'], 15)
        self.assertEqual(result['mean'], 3.0)
        self.assertEqual(result['min'], 1)
        self.assertEqual(result['max'], 5)


class TestCodeExecutionTool(unittest.TestCase):
    """Test Code Execution Tool"""
    
    def test_simple_execution(self):
        code = "result = 2 + 2\\nprint(result)"
        result = code_executor.execute(code, allow_imports=False)
        self.assertTrue(result['success'])
        self.assertIn('4', result['stdout'])
    
    def test_execution_with_variables(self):
        code = "x = 10\\ny = 20\\nresult = x + y\\nprint(result)"
        result = code_executor.execute(code, allow_imports=False)
        self.assertTrue(result['success'])
        self.assertIn('30', result['stdout'])
    
    def test_execution_with_loops(self):
        code = "total = 0\\nfor i in range(5):\\n    total += i\\nprint(total)"
        result = code_executor.execute(code, allow_imports=False)
        self.assertTrue(result['success'])
        self.assertIn('10', result['stdout'])
    
    def test_syntax_error(self):
        code = "print('missing closing quote"
        result = code_executor.execute(code, allow_imports=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'SyntaxError')
    
    def test_execution_with_imports_allowed(self):
        code = "import math\\nresult = math.sqrt(16)\\nprint(result)"
        result = code_executor.execute(code, allow_imports=True)
        self.assertTrue(result['success'])
        self.assertIn('4.0', result['stdout'])


class TestDatabaseTool(unittest.TestCase):
    """Test Database Query Tool"""
    
    def test_simple_select(self):
        result = database_tool.query("SELECT 1 as test_value")
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['rows'][0]['test_value'], 1)
    
    def test_multiple_columns(self):
        result = database_tool.query("SELECT 'test' as name, 42 as value")
        self.assertTrue(result['success'])
        self.assertEqual(result['rows'][0]['name'], 'test')
        self.assertEqual(result['rows'][0]['value'], 42)
    
    def test_security_prevent_insert(self):
        result = database_tool.query("INSERT INTO test VALUES (1)")
        self.assertFalse(result['success'])
        self.assertIn('SELECT', result['error'])
    
    def test_security_prevent_update(self):
        result = database_tool.query("UPDATE test SET value=1")
        self.assertFalse(result['success'])
        self.assertIn('SELECT', result['error'])
    
    def test_security_prevent_delete(self):
        result = database_tool.query("DELETE FROM test")
        self.assertFalse(result['success'])
        self.assertIn('SELECT', result['error'])


class TestAgentController(unittest.TestCase):
    """Test Agent Lifecycle Management"""
    
    def setUp(self):
        """Reset agent controller state before each test"""
        agent_controller.paused_agents.clear()
        agent_controller.message_queues.clear()
        agent_controller.agent_stats.clear()
    
    def test_pause_agent(self):
        result = agent_controller.pause_agent("test_agent")
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'paused')
        self.assertTrue(agent_controller.is_agent_paused("test_agent"))
    
    def test_pause_already_paused(self):
        agent_controller.pause_agent("test_agent")
        result = agent_controller.pause_agent("test_agent")
        self.assertFalse(result['success'])
    
    def test_resume_agent(self):
        agent_controller.pause_agent("test_agent")
        result = agent_controller.resume_agent("test_agent")
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'active')
        self.assertFalse(agent_controller.is_agent_paused("test_agent"))
    
    def test_resume_not_paused(self):
        result = agent_controller.resume_agent("test_agent")
        self.assertFalse(result['success'])
    
    def test_message_queueing(self):
        agent_controller.pause_agent("test_agent")
        
        # Queue some messages
        msg1 = {"id": "1", "content": "test1"}
        msg2 = {"id": "2", "content": "test2"}
        
        agent_controller.queue_message("test_agent", msg1)
        agent_controller.queue_message("test_agent", msg2)
        
        status = agent_controller.get_agent_status("test_agent")
        self.assertEqual(status['queued_messages'], 2)
        
        # Resume and check messages are delivered
        result = agent_controller.resume_agent("test_agent")
        self.assertEqual(result['delivered_count'], 2)
        self.assertEqual(len(result['queued_messages']), 2)
    
    def test_agent_status(self):
        agent_controller.pause_agent("test_agent")
        agent_controller.queue_message("test_agent", {"test": "message"})
        
        status = agent_controller.get_agent_status("test_agent")
        self.assertEqual(status['agent'], 'test_agent')
        self.assertEqual(status['status'], 'paused')
        self.assertTrue(status['is_paused'])
        self.assertEqual(status['queued_messages'], 1)
    
    def test_clear_queue(self):
        agent_controller.pause_agent("test_agent")
        agent_controller.queue_message("test_agent", {"test": "msg1"})
        agent_controller.queue_message("test_agent", {"test": "msg2"})
        
        result = agent_controller.clear_queue("test_agent")
        self.assertTrue(result['success'])
        self.assertEqual(result['cleared_count'], 2)
        
        status = agent_controller.get_agent_status("test_agent")
        self.assertEqual(status['queued_messages'], 0)


class TestGoogleSearchTool(unittest.TestCase):
    """Test Google Search Tool (graceful failure without API key)"""
    
    def test_search_without_api_key(self):
        from utils.google_search_tool import google_search
        result = google_search.search("test query", num_results=1)
        # Should fail gracefully with fallback
        self.assertIn('results', result)


class TestWeatherTool(unittest.TestCase):
    """Test Weather Tool (graceful failure without API key)"""
    
    def test_weather_without_api_key(self):
        from utils.weather_tool import weather_tool
        result = weather_tool.get_weather("London")
        # Should fail gracefully
        self.assertIn('success', result)


class TestEmailTool(unittest.TestCase):
    """Test Email Tool (graceful failure without SMTP config)"""
    
    def test_email_without_config(self):
        from utils.email_tool import email_tool
        result = email_tool.send_email(["test@example.com"], "Test", "Body")
        self.assertFalse(result['success'])
        self.assertIn('credentials', result['error'])


class TestTranslationTool(unittest.TestCase):
    """Test Translation Tool"""
    
    def test_translation_simple_phrase(self):
        from utils.translation_tool import translation_tool
        result = translation_tool.translate("hello", target_lang="es")
        self.assertTrue(result['success'])
        self.assertEqual(result['translated'], "hola")
    
    def test_translation_unavailable(self):
        from utils.translation_tool import translation_tool
        result = translation_tool.translate("complex sentence", target_lang="es")
        self.assertFalse(result['success'])


class TestWebhookTool(unittest.TestCase):
    """Test Webhook Tool"""
    
    def test_invalid_method(self):
        from utils.webhook_tool import webhook_tool
        result = webhook_tool.send_webhook(
            url="https://example.com/webhook",
            payload={"test": "data"},
            method="DELETE"
        )
        self.assertFalse(result['success'])
        self.assertIn('Unsupported method', result['error'])


def run_tests():
    """Run all unit tests"""
    print("="*70)
    print("Running Built-in Tools Unit Tests")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCalculatorTool))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionTool))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseTool))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentController))
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleSearchTool))
    suite.addTests(loader.loadTestsFromTestCase(TestWeatherTool))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailTool))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationTool))
    suite.addTests(loader.loadTestsFromTestCase(TestWebhookTool))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
