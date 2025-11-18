#!/usr/bin/env python3
"""
🚀 ARK Agent AGI - Workflow Automation Showcase
Demonstrates the complete workflow automation system with:
- One-click refund processing with risk assessment
- Auto-tagging and intelligent categorization
- Automated follow-up emails with documentation
- Action execution and plan interpretation
- Comprehensive audit trails and logging
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator import Orchestrator
from agents.email_agent import EmailAgent
from agents.sentiment_agent import SentimentAgent
from agents.priority_agent import PriorityAgent
from agents.planner_agent import PlannerAgent
from agents.ticket_agent import TicketAgent
from agents.action_executor_agent import ActionExecutorAgent
from agents.refund_agent import RefundAgent
from agents.email_sender_agent import EmailSenderAgent
from agents.emotion_agent import EmotionAgent
from storage.ticket_db import get_tickets_by_category, get_ticket
from utils.pretty import pretty
import uuid, datetime

def showcase_workflow_automation():
    """Comprehensive showcase of all workflow automation features"""
    print("🚀 ARK Agent AGI - Workflow Automation Showcase")
    print("=" * 70)
    
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
    
    print("✅ All workflow automation agents registered")
    print("\n" + "=" * 70)
    
    # Showcase different workflow scenarios
    showcase_refund_automation(orc)
    showcase_shipping_automation(orc)
    showcase_technical_support_automation(orc)
    showcase_auto_categorization(orc)
    showcase_ticket_analytics(orc)
    
    print("\n" + "=" * 70)
    print("🎉 WORKFLOW AUTOMATION SHOWCASE COMPLETE!")
    print("✅ One-click refund processing with risk assessment")
    print("✅ Intelligent auto-tagging and categorization")
    print("✅ Automated follow-up emails with documentation")
    print("✅ Action execution and plan interpretation")
    print("✅ Comprehensive audit trails and analytics")

def showcase_refund_automation(orc):
    """Demonstrate automated refund processing"""
    print("\n💰 REFUND AUTOMATION SHOWCASE")
    print("-" * 40)
    
    # Test different refund scenarios
    refund_scenarios = [
        {
            "name": "Low-Risk Instant Refund",
            "text": "I need a refund for order #12345. The product arrived damaged. Order amount was $25.",
            "customer_id": "CUST_LOW_RISK",
            "order_id": "ORD_LOW_RISK",
            "amount": 25.00,
            "expected": "Automated processing"
        },
        {
            "name": "High-Risk Manual Review", 
            "text": "I want a refund for my $300 order #67890. The product is not what I expected.",
            "customer_id": "CUST_HIGH_RISK",
            "order_id": "ORD_HIGH_RISK", 
            "amount": 300.00,
            "expected": "Manual review required"
        },
        {
            "name": "Recent Order Refund",
            "text": "Please refund my order #11111 placed 2 days ago. I changed my mind.",
            "customer_id": "CUST_RECENT",
            "order_id": "ORD_RECENT",
            "amount": 75.00,
            "expected": "Automated processing"
        }
    ]
    
    for scenario in refund_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   Customer: {scenario['customer_id']}")
        print(f"   Amount: ${scenario['amount']}")
        print(f"   Expected: {scenario['expected']}")
        
        # Create refund request message
        refund_request = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "customer_service",
            "receiver": "refund_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "customer_id": scenario['customer_id'],
                "order_id": scenario['order_id'],
                "amount": scenario['amount'],
                "reason": scenario['text'][:100],
                "auto_approve": True,  # Enable auto-approval for testing
                "payment_method": "stripe"
            }
        }
        
        # Process refund
        result = orc.send_a2a(refund_request)
        
        if result.get("status") in ["refund_processed", "refund_queued"]:
            print(f"   ✅ Result: {result.get('status')}")
            if result.get("refund_id"):
                print(f"   🏷️  Refund ID: {result.get('refund_id')}")
            if result.get("requires_manual_review"):
                print(f"   👥 Manual review required: {result.get('requires_manual_review')}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

def showcase_shipping_automation(orc):
    """Demonstrate automated shipping issue resolution"""
    print("\n📦 SHIPPING AUTOMATION SHOWCASE")
    print("-" * 40)
    
    # Test shipping issue workflow
    shipping_issue = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "customer_service",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": str(datetime.datetime.utcnow()),
        "payload": {
            "text": "My package hasn't arrived yet. It's been 2 weeks and the tracking shows it's still in transit. Order #SHIP123.",
            "customer_id": "CUST_SHIP_001",
            "order_id": "ORD_SHIP_123",
            "tracking_number": "TRACK_123456789"
        }
    }
    
    print("🧪 Testing shipping issue workflow...")
    result = orc.send_a2a(shipping_issue)
    
    if result.get("status") == "ticket_created":
        print(f"   ✅ Shipping workflow completed")
        print(f"   📋 Ticket #{result.get('ticket_id')} created")
        print(f"   🏷️  Category: {result.get('category')}")
        print(f"   🏷️  Tags: {result.get('tags')}")
        
        # Show what the automated workflow would do:
        print(f"   🤖 Automated actions that would be taken:")
        print(f"      1. Contact shipping carrier for status update")
        print(f"      2. Send customer shipping update email")
        print(f"      3. Escalate to shipping ops if package is lost")
        print(f"      4. Schedule 24-hour follow-up")
    else:
        print(f"   ❌ Shipping workflow failed: {result}")

def showcase_technical_support_automation(orc):
    """Demonstrate automated technical support"""
    print("\n🔧 TECHNICAL SUPPORT AUTOMATION SHOWCASE")
    print("-" * 40)
    
    # Test technical issue workflow
    technical_issue = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "sender": "customer_service",
        "receiver": "email_agent",
        "type": "task_request",
        "timestamp": str(datetime.datetime.utcnow()),
        "payload": {
            "text": "The app keeps crashing when I try to login. I've tried restarting my phone but it still doesn't work. Error code: LOGIN_FAIL_001",
            "customer_id": "CUST_TECH_001",
            "customer_email": "techuser@example.com",
            "device_info": "iPhone 12, iOS 15.1"
        }
    }
    
    print("🧪 Testing technical support workflow...")
    result = orc.send_a2a(technical_issue)
    
    if result.get("status") == "ticket_created":
        print(f"   ✅ Technical workflow completed")
        print(f"   📋 Ticket #{result.get('ticket_id')} created")
        print(f"   🏷️  Category: {result.get('category')}")
        print(f"   🏷️  Tags: {result.get('tags')}")
        
        # Show automated email that would be sent:
        print(f"   📧 Automated email that would be sent:")
        print(f"      Subject: Technical Support - App Login Issues")
        print(f"      Content: Troubleshooting steps, documentation links,")
        print(f"              system requirements, error code reference")
        print(f"      Follow-up: 48-hour check-in scheduled")
    else:
        print(f"   ❌ Technical workflow failed: {result}")

def showcase_auto_categorization(orc):
    """Demonstrate intelligent auto-categorization and tagging"""
    print("\n🏷️ AUTO-CATEGORIZATION SHOWCASE")
    print("-" * 40)
    
    # Test various email types for categorization
    test_emails = [
        {
            "text": "I need a refund for my order. The product arrived damaged.",
            "expected_category": "billing",
            "expected_keywords": ["refund", "damaged"]
        },
        {
            "text": "My package hasn't arrived yet. Can you check the shipping status?",
            "expected_category": "logistics",
            "expected_keywords": ["package", "shipping", "arrived"]
        },
        {
            "text": "The app keeps crashing when I try to login. Please help!",
            "expected_category": "technical",
            "expected_keywords": ["app", "crashing", "login"]
        },
        {
            "text": "I'm very frustrated with your service. This is terrible!",
            "expected_category": "customer_service",
            "expected_keywords": ["frustrated", "terrible", "service"]
        },
        {
            "text": "I want to cancel my subscription. How do I do that?",
            "expected_category": "account",
            "expected_keywords": ["cancel", "subscription"]
        }
    ]
    
    print("🧪 Testing intelligent categorization...")
    
    for i, test_email in enumerate(test_emails, 1):
        print(f"\n   {i}. Testing: {test_email['text'][:50]}...")
        
        email_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": f"test_customer_{i}",
            "receiver": "email_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "text": test_email["text"],
                "customer_id": f"TEST_CUST_{i}"
            }
        }
        
        result = orc.send_a2a(email_message)
        
        if result.get("status") == "ticket_created":
            category = result.get('category', 'unknown')
            tags = result.get('tags', [])
            
            print(f"      ✅ Auto-categorized as: {category}")
            print(f"      ✅ Auto-tagged with: {tags}")
            
            # Verify expected categorization
            if category == test_email["expected_category"]:
                print(f"      🎯 Category match!")
            else:
                print(f"      ⚠️  Category mismatch: expected {test_email['expected_category']}, got {category}")
        else:
            print(f"      ❌ Categorization failed: {result}")

def showcase_ticket_analytics(orc):
    """Demonstrate ticket analytics and insights"""
    print("\n📊 TICKET ANALYTICS SHOWCASE")
    print("-" * 40)
    
    # Get tickets by category for analytics
    categories = ["billing", "logistics", "technical", "customer_service", "account", "general"]
    
    print("📈 Ticket Distribution by Category:")
    
    total_tickets = 0
    category_stats = {}
    
    for category in categories:
        tickets = get_tickets_by_category(category, limit=100)
        count = len(tickets)
        total_tickets += count
        category_stats[category] = count
        
        if count > 0:
            print(f"   📋 {category.upper()}: {count} tickets")
            
            # Show sample tickets with details
            for ticket in tickets[:2]:  # Show first 2 tickets per category
                print(f"      Ticket #{ticket['id']}: {ticket['intent']}")
                print(f"      Priority: {ticket['priority_score']:.2f} | Status: {ticket['status']}")
                if ticket['tags']:
                    print(f"      Tags: {ticket['tags']}")
                print()
    
    print(f"\n📊 Summary Statistics:")
    print(f"   Total Tickets: {total_tickets}")
    print(f"   Categories: {len([c for c, count in category_stats.items() if count > 0])}")
    
    # Show most common intents
    print(f"\n🔍 Most Common Issues:")
    all_tickets = []
    for category in categories:
        tickets = get_tickets_by_category(category, limit=10)
        all_tickets.extend(tickets)
    
    intent_counts = {}
    for ticket in all_tickets:
        intent = ticket['intent']
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
    for intent, count in sorted_intents[:5]:
        print(f"   {intent}: {count} tickets")

if __name__ == "__main__":
    showcase_workflow_automation()