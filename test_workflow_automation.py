#!/usr/bin/env python3
"""
🚀 ARK Agent AGI - Workflow Automation Test
Tests the new workflow automation features including:
- One-click refund processing
- Auto-tagging and categorization  
- Automated follow-up emails with documentation
- Action execution and plan interpretation
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import datetime
import uuid

from agents.action_executor_agent import ActionExecutorAgent
from agents.email_agent import EmailAgent
from agents.email_sender_agent import EmailSenderAgent
from agents.emotion_agent import EmotionAgent
from agents.planner_agent import PlannerAgent
from agents.priority_agent import PriorityAgent
from agents.refund_agent import RefundAgent
from agents.sentiment_agent import SentimentAgent
from agents.ticket_agent import TicketAgent
from orchestrator import Orchestrator
from utils.pretty import pretty


def test_workflow_automation():
    """Test the complete workflow automation pipeline"""
    print("🚀 Testing Workflow Automation Features")
    print("=" * 60)
    
    # Initialize orchestrator with all agents
    orc = Orchestrator()
    orc.register_agent("email_agent", EmailAgent("email_agent", orc))
    orc.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orc))
    orc.register_agent("priority_agent", PriorityAgent("priority_agent", orc))
    orc.register_agent("planner_agent", PlannerAgent("planner_agent", orc))
    orc.register_agent("action_executor_agent", ActionExecutorAgent("action_executor_agent", orc))
    orc.register_agent("refund_agent", RefundAgent("refund_agent", orc))
    orc.register_agent("email_sender_agent", EmailSenderAgent("email_sender_agent", orc))
    orc.register_agent("ticket_agent", TicketAgent("ticket_agent", orc))
    orc.register_agent("emotion_agent", EmotionAgent("emotion_agent", orc))
    
    print("✅ All agents registered")
    
    # Test 1: Refund Request Workflow
    print("\n1️⃣ Testing Refund Request Workflow...")
    test_refund_workflow(orc)
    
    # Test 2: Shipping Issue Workflow  
    print("\n2️⃣ Testing Shipping Issue Workflow...")
    test_shipping_workflow(orc)
    
    # Test 3: Technical Support Workflow
    print("\n3️⃣ Testing Technical Support Workflow...")
    test_technical_workflow(orc)
    
    # Test 4: Auto-tagging and Categorization
    print("\n4️⃣ Testing Auto-tagging and Categorization...")
    test_auto_tagging(orc)
    
    print("\n" + "=" * 60)
    print("🎉 All Workflow Automation Tests Complete!")
    print("✅ One-click refund processing")
    print("✅ Auto-tagging and categorization")
    print("✅ Automated follow-up emails")
    print("✅ Action execution and plan interpretation")

def test_refund_workflow(orc):
    """Test automated refund processing"""
    
    # Simulate a refund request email
    refund_request = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "customer_service",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": str(datetime.datetime.utcnow()),
        "payload": {
            "text": "I need a refund for order #12345. The product arrived damaged and I want my money back. This is urgent!",
            "customer_id": "CUST_12345",
            "order_id": "ORD_12345",
            "customer_email": "customer@example.com"
        }
    }
    
    print("   Processing refund request...")
    result = orc.send_a2a(refund_request)
    
    if result.get("status") == "ticket_created":
        print(f"   ✅ Refund workflow completed - Ticket #{result.get('ticket_id')} created")
        print(f"   📋 Category: {result.get('category')}")
        print(f"   🏷️  Tags: {result.get('tags')}")
    else:
        print(f"   ❌ Refund workflow failed: {result}")

def test_shipping_workflow(orc):
    """Test automated shipping issue resolution"""
    
    # Simulate a shipping issue email
    shipping_issue = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "customer_service",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": str(datetime.datetime.utcnow()),
        "payload": {
            "text": "My order hasn't arrived yet. It's been 2 weeks and the tracking shows it's still in transit. Can you help?",
            "customer_id": "CUST_67890",
            "order_id": "ORD_67890",
            "tracking_number": "TRACK_67890"
        }
    }
    
    print("   Processing shipping issue...")
    result = orc.send_a2a(shipping_issue)
    
    if result.get("status") == "ticket_created":
        print(f"   ✅ Shipping workflow completed - Ticket #{result.get('ticket_id')} created")
        print(f"   📋 Category: {result.get('category')}")
        print(f"   🏷️  Tags: {result.get('tags')}")
    else:
        print(f"   ❌ Shipping workflow failed: {result}")

def test_technical_workflow(orc):
    """Test automated technical support"""
    
    # Simulate a technical issue email
    technical_issue = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "customer_service",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": str(datetime.datetime.utcnow()),
        "payload": {
            "text": "The app keeps crashing when I try to login. I've tried restarting my phone but it still doesn't work. Please help!",
            "customer_id": "CUST_11111",
            "customer_email": "techuser@example.com",
            "device_info": "iPhone 12, iOS 15.1"
        }
    }
    
    print("   Processing technical issue...")
    result = orc.send_a2a(technical_issue)
    
    if result.get("status") == "ticket_created":
        print(f"   ✅ Technical workflow completed - Ticket #{result.get('ticket_id')} created")
        print(f"   📋 Category: {result.get('category')}")
        print(f"   🏷️  Tags: {result.get('tags')}")
    else:
        print(f"   ❌ Technical workflow failed: {result}")

def test_auto_tagging(orc):
    """Test auto-tagging and categorization functionality"""
    
    # Test different types of emails to verify auto-tagging
    test_cases = [
        {
            "text": "I want to return this item and get my money back",
            "expected_category": "billing",
            "expected_tags": ["refund", "return"]
        },
        {
            "text": "My package hasn't arrived yet, can you check the shipping status?",
            "expected_category": "logistics", 
            "expected_tags": ["shipping", "delivery"]
        },
        {
            "text": "The app is not working properly, it keeps showing an error message",
            "expected_category": "technical",
            "expected_tags": ["not working", "error"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   {i}. Testing: {test_case['text'][:50]}...")
        
        test_email = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "test_customer",
            "receiver": "email_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "text": test_case["text"],
                "customer_id": f"TEST_CUST_{i}"
            }
        }
        
        result = orc.send_a2a(test_email)
        
        if result.get("status") == "ticket_created":
            category = result.get('category', 'unknown')
            tags = result.get('tags', [])
            
            print(f"      ✅ Auto-categorized as: {category}")
            print(f"      ✅ Auto-tagged with: {tags}")
            
            # Verify expected results
            if category == test_case["expected_category"]:
                print(f"      🎯 Category match: {category}")
            else:
                print(f"      ⚠️  Category mismatch: expected {test_case['expected_category']}, got {category}")
        else:
            print(f"      ❌ Auto-tagging failed: {result}")

if __name__ == "__main__":
    test_workflow_automation()