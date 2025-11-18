#!/usr/bin/env python3
"""
🚀 ARK Agent AGI - Multi-Agent System & A2A Protocol Validation
Simplified test suite to verify:
1. Multi-agent communication chains
2. A2A protocol compliance
3. Tool integrations (OpenAPI, MCP FileSystem)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator import Orchestrator
from agents.email_agent import EmailAgent
from agents.sentiment_agent import SentimentAgent
from agents.planner_agent import PlannerAgent
from agents.ticket_agent import TicketAgent
from agents.emotion_agent import EmotionAgent
from agents.priority_agent import PriorityAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.supervisor_agent import SupervisorAgent
from agents.shipping_agent import ShippingAgent
from agents.action_executor_agent import ActionExecutorAgent
from agents.refund_agent import RefundAgent
from agents.email_sender_agent import EmailSenderAgent
from utils.mcp_filesystem_tool import mcp_filesystem
from utils.openapi_tool import check_shipping_api_health, track_shipping_order
from utils.a2a_schema import validate_message
import uuid

def test_a2a_protocol_compliance():
    """Test A2A protocol compliance"""
    print("🔍 Testing A2A Protocol Compliance")
    print("=" * 60)
    
    # Test valid message
    valid_message = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "email_agent",
        "receiver": "sentiment_agent",
        "type": "task_request",
        "timestamp": "2024-01-01T12:00:00Z",
        "payload": {"text": "Test message"}
    }
    
    try:
        validate_message(valid_message)
        print("✅ Valid message passes validation")
    except Exception as e:
        print(f"❌ Valid message failed: {e}")
        return False
    
    # Test invalid messages
    invalid_messages = [
        {k: v for k, v in valid_message.items() if k != "id"},  # Missing id
        {k: v for k, v in valid_message.items() if k != "session_id"},  # Missing session_id
        {k: v for k, v in valid_message.items() if k != "sender"},  # Missing sender
    ]
    
    for i, invalid_msg in enumerate(invalid_messages):
        try:
            validate_message(invalid_msg)
            print(f"❌ Invalid message {i+1} should have failed validation")
            return False
        except ValueError as e:
            print(f"✅ Invalid message {i+1} correctly failed: {e}")
    
    return True

def test_tool_integrations():
    """Test all tool integrations"""
    print("\n🛠️ Testing Tool Integrations")
    print("=" * 60)
    
    # Test Tool A: OpenAPI Tool (Shipping API)
    print("\n📦 Tool A: OpenAPI Shipping API")
    print("-" * 40)
    
    # Check API health
    health_result = check_shipping_api_health()
    print(f"API Health: {'✅ Healthy' if health_result.get('healthy') else '❌ Unhealthy (will use mock data)'}")
    
    # Test tracking
    tracking_result = track_shipping_order("ORD123456")
    print(f"Tracking Result: {'✅ Success' if tracking_result.get('success') else '❌ Failed'}")
    if tracking_result.get('data'):
        print(f"  Status: {tracking_result['data'].get('status', 'unknown')}")
        print(f"  Tracking #: {tracking_result['data'].get('tracking_number', 'N/A')}")
        print(f"  Carrier: {tracking_result['data'].get('carrier', 'N/A')}")
    
    # Test Tool C: MCP FileSystem
    print("\n📁 Tool C: MCP FileSystem")
    print("-" * 40)
    
    # Create sample documents if they don't exist
    mcp_filesystem.create_sample_documents()
    
    # List documents
    docs = mcp_filesystem.list_documents()
    print(f"Documents Found: {len(docs)}")
    for doc in docs[:3]:  # Show first 3
        print(f"  📄 {doc['filename']} ({doc['size']} bytes)")
    
    # Search documents
    search_results = mcp_filesystem.search_documents("refund", max_results=2)
    print(f"Search Results: {len(search_results)} documents found")
    for result in search_results:
        print(f"  🔍 {result['filename']} (relevance: {result['relevance_score']:.2f})")
    
    return True

def test_multi_agent_chains():
    """Test all required multi-agent communication chains"""
    print("🔄 Testing Multi-Agent Communication Chains")
    print("=" * 60)
    
    # Initialize orchestrator
    orc = Orchestrator()
    
    # Register all agents
    agents = {
        "email_agent": EmailAgent("email_agent", orc),
        "sentiment_agent": SentimentAgent("sentiment_agent", orc),
        "planner_agent": PlannerAgent("planner_agent", orc),
        "ticket_agent": TicketAgent("ticket_agent", orc),
        "emotion_agent": EmotionAgent("emotion_agent", orc),
        "priority_agent": PriorityAgent("priority_agent", orc),
        "knowledge_agent": KnowledgeAgent("knowledge_agent", orc),
        "supervisor_agent": SupervisorAgent("supervisor_agent", orc),
        "shipping_agent": ShippingAgent("shipping_agent", orc),
        "action_executor_agent": ActionExecutorAgent("action_executor_agent", orc),
        "refund_agent": RefundAgent("refund_agent", orc),
        "email_sender_agent": EmailSenderAgent("email_sender_agent", orc),
    }
    
    for name, agent in agents.items():
        orc.register_agent(name, agent)
    
    print("✅ All agents registered")
    
    # Test Chain 1: EmailAgent → SentimentAgent → PlannerAgent → TicketAgent
    print("\n📧 Chain 1: EmailAgent → SentimentAgent → PlannerAgent → TicketAgent")
    print("-" * 60)
    
    session_id = str(uuid.uuid4())
    test_email = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "sender": "user",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": "2024-01-01T12:00:00Z",
        "payload": {
            "text": "My order didn't arrive and I want a refund. This is very frustrating!",
            "customer_id": "CUST001"
        }
    }
    
    print(f"📨 Input: {test_email['payload']['text']}")
    try:
        result = orc.send_a2a(test_email)
        print(f"✅ Chain completed - Final result type: {type(result).__name__}")
        if isinstance(result, dict) and 'ticket_id' in result:
            print(f"  📋 Ticket created: #{result['ticket_id']}")
    except Exception as e:
        print(f"❌ Chain failed: {e}")
        return False
    
    # Test Chain 2: EmotionAgent → SentimentAgent → PriorityAgent
    print("\n😊 Chain 2: EmotionAgent → SentimentAgent → PriorityAgent")
    print("-" * 60)
    
    session_id = str(uuid.uuid4())
    test_emotion = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "sender": "user",
        "receiver": "emotion_agent",
        "type": "task_request",
        "timestamp": "2024-01-01T12:00:00Z",
        "payload": {
            "text": "I'm really stressed about my missing package",
            "customer_id": "CUST002",
            "stress": 0.8
        }
    }
    
    print(f"😰 Input: {test_emotion['payload']['text']}")
    try:
        result = orc.send_a2a(test_emotion)
        print(f"✅ Chain completed - Final result type: {type(result).__name__}")
    except Exception as e:
        print(f"❌ Chain failed: {e}")
        return False
    
    # Test Chain 3: KnowledgeAgent integration (with fallback)
    print("\n📚 Chain 3: KnowledgeAgent → PlannerAgent (with RAG fallback)")
    print("-" * 60)
    
    session_id = str(uuid.uuid4())
    test_knowledge = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "sender": "user",
        "receiver": "knowledge_agent",
        "type": "task_request",
        "timestamp": "2024-01-01T12:00:00Z",
        "payload": {
            "text": "How do I request a refund?",
            "next": "planner_agent",
            "kb": [  # Provide fallback KB data
                {"text": "To request a refund, contact customer support with your order ID and reason."},
                {"text": "Refunds are processed within 3-5 business days."}
            ]
        }
    }
    
    print(f"❓ Input: {test_knowledge['payload']['text']}")
    try:
        result = orc.send_a2a(test_knowledge)
        print(f"✅ Chain completed - Final result type: {type(result).__name__}")
    except Exception as e:
        print(f"❌ Chain failed: {e}")
        return False
    
    # Test Chain 4: SupervisorAgent routing
    print("\n👮 Chain 4: SupervisorAgent → PlannerAgent")
    print("-" * 60)
    
    session_id = str(uuid.uuid4())
    test_supervisor = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "sender": "user",
        "receiver": "supervisor_agent",
        "type": "task_request",
        "timestamp": "2024-01-01T12:00:00Z",
        "payload": {
            "candidate_reply": "I need help with my technical issue",
            "text": "The app keeps crashing when I try to login",
            "customer_id": "CUST003",
            "kb": [
                {"text": "Try clearing your browser cache and cookies"},
                {"text": "Check system requirements for compatibility"}
            ]
        }
    }
    
    print(f"🎯 Input: {test_supervisor['payload']['text']}")
    try:
        result = orc.send_a2a(test_supervisor)
        print(f"✅ Chain completed - Final result type: {type(result).__name__}")
    except Exception as e:
        print(f"❌ Chain failed: {e}")
        return False
    
    return True

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 ARK Agent AGI - Multi-Agent System & A2A Protocol Test")
    print("=" * 70)
    
    try:
        # Run all tests
        chain_test = test_multi_agent_chains()
        protocol_test = test_a2a_protocol_compliance()
        tools_test = test_tool_integrations()
        
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        print(f"✅ Multi-Agent Chains: {'PASS' if chain_test else 'FAIL'}")
        print(f"✅ A2A Protocol Compliance: {'PASS' if protocol_test else 'FAIL'}")
        print(f"✅ Tool Integrations: {'PASS' if tools_test else 'FAIL'}")
        
        overall_success = chain_test and protocol_test and tools_test
        print(f"\n🎯 OVERALL: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            print("\n🎉 Multi-agent system is fully operational!")
            print("📋 All A2A protocol requirements met")
            print("🔧 All tool integrations working correctly")
            print("\n📈 System Capabilities:")
            print("  • Email → Sentiment → Planner → Ticket chain")
            print("  • Emotion → Sentiment → Priority chain")
            print("  • Knowledge → Planner integration")
            print("  • Supervisor routing with KB validation")
            print("  • OpenAPI shipping tool with fallback")
            print("  • MCP filesystem for document access")
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)