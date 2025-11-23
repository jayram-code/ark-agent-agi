from typing import Dict, Optional, List
from models.messages import AgentMessage

class RoutingPolicy:
    """
    Defines rules for routing messages to the appropriate agent.
    """

    def __init__(self):
        # Keyword-based routing rules
        self.keyword_rules = {
            "refund": "refund_agent",
            "return": "refund_agent",
            "shipping": "shipping_agent",
            "delivery": "shipping_agent",
            "track": "shipping_agent",
            "technical": "integration_agent",
            "error": "integration_agent",
            "bug": "integration_agent",
            "broken": "integration_agent",
            "sentiment": "sentiment_agent",
            "emotion": "sentiment_agent",
            "email": "email_agent",
            "schedule": "scheduler_agent",
            "meeting": "meeting_agent",
            "research": "research_group",
            "knowledge": "knowledge_agent",
        }

        # Intent-based routing (if intent is present in payload)
        self.intent_rules = {
            "request_refund": "refund_agent",
            "check_order_status": "shipping_agent",
            "report_issue": "integration_agent",
            "create_ticket": "integration_agent",
            "get_ticket": "integration_agent",
            "update_ticket": "integration_agent",
            "schedule_meeting": "meeting_agent",
            "send_email": "email_agent",
            "escalate": "human_escalation_agent",
            "review": "human_escalation_agent",
            "approval": "human_escalation_agent",
        }

    def determine_receiver(self, message: AgentMessage) -> str:
        """
        Determines the receiver based on the message content.
        """
        # 1. Check if receiver is already set and valid (not 'router')
        if message.receiver and message.receiver != "router":
            return message.receiver

        payload = message.payload or {}
        text = payload.get("text", "").lower()
        intent = payload.get("intent", "").lower()

        # 2. Check Intent Rules
        if intent in self.intent_rules:
            return self.intent_rules[intent]

        # 3. Check Keyword Rules
        for keyword, agent in self.keyword_rules.items():
            if keyword in text:
                return agent

        # 4. Default to Supervisor
        return "supervisor_agent"

