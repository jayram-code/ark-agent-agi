"""
Auto-Reply Agent - Generates and sends automated responses to clients
"""
import asyncio
import datetime
import uuid
from typing import Dict, Any

from src.agents.base_agent import BaseAgent
from src.models.messages import AgentMessage, MessageType
from src.utils.observability.logging_utils import log_event


class AutoReplyAgent(BaseAgent):
    """
    Handles automatic client responses:
    - Acknowledgment emails
    - Meeting confirmations
    - Issue escalation notifications
    - Refund/shipping updates
    """
    
    def __init__(self, name: str, orchestrator):
        super().__init__(name, orchestrator)
        self.sent_replies = []
    
    async def receive(self, message: AgentMessage):
        """Generate and send automatic reply"""
        log_event("AutoReplyAgent", "Generating auto-reply")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        # Determine reply type
        reply_type = payload.get('reply_type', 'acknowledgment')
        intent = payload.get('intent', 'general_query')
        sender_email = payload.get('sender_email', 'client@example.com')
        
        # Generate appropriate response
        reply_content = self._generate_reply(reply_type, intent, payload)
        
        # Log sent reply
        reply_record = {
            'id': str(uuid.uuid4())[:8],
            'to': sender_email,
            'type': reply_type,
            'sent_at': str(datetime.datetime.utcnow()),
            'content': reply_content
        }
        self.sent_replies.append(reply_record)
        
        return AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender=self.name,
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                'reply_sent': True,
                'reply_id': reply_record['id'],
                'recipient': sender_email,
                'reply_content': reply_content,
                'reply_type': reply_type
            }
        )
    
    def _generate_reply(self, reply_type: str, intent: str, payload: Dict) -> str:
        """Generate appropriate email response"""
        
        if reply_type == 'acknowledgment':
            return self._acknowledgment_template(intent)
        
        elif reply_type == 'meeting_confirmation':
            meeting_info = payload.get('meeting_info', {})
            return self._meeting_confirmation_template(meeting_info)
        
        elif reply_type == 'escalation':
            return self._escalation_template(intent)
        
        elif reply_type == 'refund_process':
            order_id = payload.get('order_id', 'XXXXX')
            return self._refund_template(order_id)
        
        elif reply_type == 'shipping_update':
            tracking = payload.get('tracking', 'XXXXX')
            return self._shipping_template(tracking)
        
        else:
            return self._generic_template()
    
    def _acknowledgment_template(self, intent: str) -> str:
        """General acknowledgment email"""
        return f"""
Dear Valued Customer,

Thank you for reaching out to us. We have received your inquiry regarding {intent.replace('_', ' ')}.

Our team is currently reviewing your request and will get back to you within 24 hours. 

If this is urgent, please don't hesitate to call our support line at 1-800-SUPPORT.

Best regards,
ARK Customer Service Team

---
This is an automated response. Please do not reply to this email.
""".strip()
    
    def _meeting_confirmation_template(self, meeting_info: Dict) -> str:
        """Meeting confirmation email"""
        return f"""
Meeting Confirmation

Dear Participant,

Your meeting has been scheduled:

📅 Date: {meeting_info.get('proposed_date', 'TBD')}
🕐  Time: {meeting_info.get('proposed_time', 'TBD')}
📍 Location: {meeting_info.get('location', 'Google Meet')}
📝 Topic: {meeting_info.get('topic', 'Discussion')}

A calendar invite has been sent. Please accept to confirm your attendance.

Best regards,
ARK Meeting Coordinator
""".strip()
    
    def _escalation_template(self, intent: str) -> str:
        """Escalation notification"""
        return f"""
Dear Valued Customer,

Thank you for contacting us about your {intent.replace('_', ' ')}.

We understand this matter requires special attention. Your case has been escalated to our senior support team.

A dedicated agent will contact you within 4 business hours to resolve this issue.

Case ID: {str(uuid.uuid4())[:8].upper()}

We apologize for any inconvenience and appreciate your patience.

Best regards,
ARK Customer Support - Priority Team
""".strip()
    
    def _refund_template(self, order_id: str) -> str:
        """Refund processing email"""
        return f"""
Refund Request Received

Dear Customer,

We have received your refund request for order #{order_id}.

Status: Processing
Expected Timeline: 5-7 business days
Refund Method: Original payment method

You will receive a confirmation email once the refund has been processed.

If you have any questions, please reference case #{order_id}.

Best regards,
ARK Refunds Team
""".strip()
    
    def _shipping_template(self, tracking: str) -> str:
        """Shipping inquiry response"""
        return f"""
Shipping Update

Dear Customer,

Thank you for your inquiry about your shipment.

Tracking Number: {tracking}
Current Status: In Transit
Estimated Delivery: 2-3 business days

You can track your package in real-time at: track.arkexample.com/{tracking}

If your package doesn't arrive within the estimated timeframe, please contact us.

Best regards,
ARK Shipping Department
""".strip()
    
    def _generic_template(self) -> str:
        """Generic response"""
        return """
Dear Customer,

Thank you for your email. We have received your message and our team will review it shortly.

You can expect a response within 24 hours.

Best regards,
ARK Customer Service
""".strip()
    
    def get_sent_count(self) -> int:
        """Get number of replies sent"""
        return len(self.sent_replies)
