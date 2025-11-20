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
import asyncio
import uuid
import datetime

# Add src to path
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
from agents.shipping_agent import ShippingAgent
from agents.supervisor_agent import SupervisorAgent
from agents.retryable_agent import RetryableAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.meeting_agent import MeetingAgent
from agents.memory_agent import MemoryAgent
from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType

class UserProxyAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        # print(f"   [UserProxy] Received from {message.sender}: {message.payload.get('status', 'info')}")
        return {"status": "received", "message": "User received response"}

async def showcase_workflow_automation():
    """Comprehensive showcase of all workflow automation features"""
    print("🚀 ARK Agent AGI - Workflow Automation Showcase")
    print("=" * 70)
    
    # Initialize orchestrator with all agents
    orc = Orchestrator()
    
    # Register User Proxies
    orc.register_agent("customer_service", UserProxyAgent("customer_service", orc))
    orc.register_agent("user", UserProxyAgent("user", orc))
    orc.register_agent("test_customer", UserProxyAgent("test_customer", orc))
    
    orc.register_agent("email_agent", EmailAgent("email_agent", orc))
    orc.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orc))
    orc.register_agent("priority_agent", PriorityAgent("priority_agent", orc))
    orc.register_agent("planner_agent", PlannerAgent("planner_agent", orc))
    orc.register_agent("action_executor_agent", ActionExecutorAgent("action_executor_agent", orc))
    orc.register_agent("refund_agent", RefundAgent("refund_agent", orc))
    orc.register_agent("email_sender_agent", EmailSenderAgent("email_sender_agent", orc))
    orc.register_agent("ticket_agent", TicketAgent("ticket_agent", orc))
    orc.register_agent("emotion_agent", EmotionAgent("emotion_agent", orc))
    orc.register_agent("shipping_agent", ShippingAgent("shipping_agent", orc))
    orc.register_agent("supervisor_agent", SupervisorAgent("supervisor_agent", orc))
    # Fixed RetryableAgent instantiation (removed 3rd arg)
    orc.register_agent("retryable_agent", RetryableAgent("retryable_agent", orc))
    orc.register_agent("knowledge_agent", KnowledgeAgent("knowledge_agent", orc))
    orc.register_agent("meeting_agent", MeetingAgent("meeting_agent", orc))
    orc.register_agent("memory_agent", MemoryAgent("memory_agent", orc))
    
    print("✅ All workflow automation agents registered")
    print("\n" + "=" * 70)
    
    # Showcase different workflow scenarios
    await showcase_refund_automation(orc)
    await showcase_shipping_automation(orc)
    await showcase_technical_support_automation(orc)
    await showcase_auto_categorization(orc)
    
    print("\n" + "=" * 70)
    print("🎉 WORKFLOW AUTOMATION SHOWCASE COMPLETE!")

async def showcase_refund_automation(orc):
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
        }
    ]
    
    for scenario in refund_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   Customer: {scenario['customer_id']}")
        print(f"   Amount: ${scenario['amount']}")
        
        # Create refund request message
        refund_request = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            sender="customer_service",
            receiver="refund_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "customer_id": scenario['customer_id'],
                "order_id": scenario['order_id'],
                "amount": scenario['amount'],
                "reason": scenario['text'][:100],
                "auto_approve": True,
                "payment_method": "stripe"
            }
        )
        
        # Process refund
        result = await orc.send_a2a(refund_request)
        
        # Handle both dict and AgentMessage responses
        payload = result.payload if isinstance(result, AgentMessage) else result
        if hasattr(payload, 'dict'): payload = payload.dict()
            
        status = payload.get("status")
        print(f"   ✅ Result: {status}")

async def showcase_shipping_automation(orc):
    """Demonstrate automated shipping issue resolution"""
    print("\n📦 SHIPPING AUTOMATION SHOWCASE")
    print("-" * 40)
    
    # Test shipping issue workflow
    shipping_issue = AgentMessage(
        id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        sender="customer_service",
        receiver="shipping_agent",
        type=MessageType.TASK_REQUEST,
        timestamp=str(datetime.datetime.utcnow()),
        payload={
            "text": "My package hasn't arrived yet. Order #SHIP123.",
            "customer_id": "CUST_SHIP_001",
            "order_id": "ORD_SHIP_123"
        }
    )
    
    print("🧪 Testing shipping issue workflow...")
    result = await orc.send_a2a(shipping_issue)
    
    payload = result.payload if isinstance(result, AgentMessage) else result
    if hasattr(payload, 'dict'): payload = payload.dict()
    
    print(f"   ✅ Status: {payload.get('status')}")
    print(f"   ✅ Tracking: {payload.get('tracking_number')}")

async def showcase_technical_support_automation(orc):
    """Demonstrate automated technical support"""
    print("\n🔧 TECHNICAL SUPPORT AUTOMATION SHOWCASE")
    print("-" * 40)
    
    # Test technical issue workflow
    technical_issue = AgentMessage(
        id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        sender="customer_service",
        receiver="supervisor_agent", # Start with supervisor for complex issues
        type=MessageType.TASK_REQUEST,
        timestamp=str(datetime.datetime.utcnow()),
        payload={
            "text": "The app keeps crashing when I try to login. Error code: LOGIN_FAIL_001",
            "customer_id": "CUST_TECH_001",
            "customer_email": "techuser@example.com"
        }
    )
    
    print("🧪 Testing technical support workflow...")
    # This might trigger a chain of agents
    await orc.send_a2a(technical_issue)
    print("   ✅ Technical workflow initiated")

async def showcase_auto_categorization(orc):
    """Demonstrate intelligent auto-categorization"""
    print("\n🏷️ AUTO-CATEGORIZATION SHOWCASE")
    print("-" * 40)
    
    test_email = {
        "text": "I need a refund for my order. The product arrived damaged.",
        "expected_category": "billing"
    }
    
    print(f"🧪 Testing: {test_email['text'][:50]}...")
    
    email_message = AgentMessage(
        id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        sender="test_customer",
        receiver="ticket_agent", # Direct to ticket agent for categorization
        type=MessageType.TASK_REQUEST,
        timestamp=str(datetime.datetime.utcnow()),
        payload={
            "text": test_email["text"],
            "customer_id": "TEST_CUST",
            "intent": "refund_request"
        }
    )
    
    result = await orc.send_a2a(email_message)
    
    payload = result.payload if isinstance(result, AgentMessage) else result
    if hasattr(payload, 'dict'): payload = payload.dict()
    
    print(f"      ✅ Category: {payload.get('category')}")
    print(f"      ✅ Tags: {payload.get('tags')}")

if __name__ == "__main__":
    asyncio.run(showcase_workflow_automation())