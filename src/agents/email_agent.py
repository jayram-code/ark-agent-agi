import asyncio
import datetime
import uuid
from typing import Any, Dict

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.gemini_utils import classify_intent
from utils.observability.logging_utils import log_event


class EmailAgent(BaseAgent):
    """
    Unified Email Agent responsible for:
    1. Processing incoming emails (Intent Classification -> Forwarding)
    2. Sending automated emails (Templates -> SMTP/API)
    """

    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)

        # Email templates for different scenarios
        self.email_templates = {
            "refund_confirmation": {
                "subject": "Refund Processed - Order {order_id}",
                "body": """
Dear Customer,

Your refund request for order {order_id} has been processed successfully.

Refund Details:
- Amount: ${amount}
- Processing Time: {processing_time}
- Status: {status}

The refund will appear in your account within 3-5 business days depending on your payment method.

If you have any questions, please don't hesitate to contact our support team.

Best regards,
Customer Support Team
                """.strip(),
                "priority": "high",
            },
            "shipping_update": {
                "subject": "Shipping Update - Order {order_id}",
                "body": """
Dear Customer,

We have an update regarding your order {order_id}.

{update_message}

Tracking Information:
{tracking_info}

Expected Delivery: {expected_delivery}

If you need any assistance, please contact our support team.

Best regards,
Shipping Team
                """.strip(),
                "priority": "medium",
            },
            "technical_support": {
                "subject": "Technical Support - {issue_summary}",
                "body": """
Dear Customer,

Thank you for contacting us about {issue_summary}.

{solution_steps}

Additional Resources:
{documentation_links}

If these steps don't resolve your issue, please reply to this email with:
- Error messages you're seeing
- Steps you've already tried
- Screenshots if applicable

Our technical team will respond within 24 hours.

Best regards,
Technical Support Team
                """.strip(),
                "priority": "high",
            },
            "general_followup": {
                "subject": "Following up on your recent inquiry",
                "body": """
Dear Customer,

I hope this email finds you well. I'm following up on your recent inquiry to ensure everything has been resolved to your satisfaction.

{followup_message}

If you need any further assistance, please don't hesitate to reach out.

Best regards,
Customer Care Team
                """.strip(),
                "priority": "low",
            },
            "documentation_followup": {
                "subject": "Helpful Resources - {topic}",
                "body": """
Dear Customer,

Following up on our conversation about {topic}, here are some helpful resources:

{documentation_content}

{additional_links}

If you have any questions about these resources or need further clarification, please let us know.

Best regards,
Support Team
                """.strip(),
                "priority": "medium",
            },
        }

    async def receive(self, message: AgentMessage):
        """
        Handle incoming messages.
        - If 'action' is 'send_email', send an email.
        - Otherwise, treat as incoming email text to classify and route.
        """
        log_event("EmailAgent", f"Received request from {message.sender}")

        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        # Check if this is a request to SEND an email
        if payload.get("action") == "send_email":
            return await self._handle_send_email(message, payload)
        
        # Default: Process incoming email text
        return await self._handle_incoming_email(message, payload)

    async def _handle_incoming_email(self, message: AgentMessage, payload: Dict[str, Any]):
        """Process incoming email text: Classify intent and forward."""
        log_event("EmailAgent", "Processing incoming email with Gemini AI")
        
        text = payload.get("text", "")
        
        # Use Gemini for intent classification
        intent_result = classify_intent(text)

        # Forward to sentiment agent for next step in pipeline
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="email_agent",
            receiver="sentiment_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "intent": intent_result["intent"],
                "intent_confidence": intent_result["confidence"],
                "text": text,
                "customer_id": payload.get("customer_id"),
                "urgency": intent_result.get("urgency", "medium"),
                "key_phrases": intent_result.get("key_phrases", []),
            },
        )

        return await self.orchestrator.send_a2a(response)

    async def _handle_send_email(self, message: AgentMessage, payload: Dict[str, Any]):
        """Process request to send an email."""
        log_event("EmailAgent", {"event": "email_send_request", "message_id": message.id})

        # Extract email parameters
        recipient = payload.get("recipient")
        template_name = payload.get("template", "general_followup")
        subject = payload.get("subject")
        custom_body = payload.get("body")
        variables = payload.get("variables", {})
        include_documentation = payload.get("include_documentation", False)
        documentation_topic = payload.get("documentation_topic", "")

        if not recipient:
            log_event("EmailAgent", {"event": "email_failed", "reason": "no_recipient"})
            return {"status": "error", "message": "No recipient specified"}

        try:
            # Generate email content
            email_content = self.generate_email_content(
                template_name,
                subject,
                custom_body,
                variables,
                include_documentation,
                documentation_topic,
            )

            # Simulate email sending (in production, integrate with email service)
            email_result = await self.send_email(recipient, email_content)

            if email_result["success"]:
                log_event(
                    "EmailAgent",
                    {
                        "event": "email_sent",
                        "recipient": recipient,
                        "template": template_name,
                        "subject": email_content["subject"],
                    },
                )
                return {
                    "status": "sent",
                    "recipient": recipient,
                    "subject": email_content["subject"],
                    "timestamp": str(datetime.datetime.utcnow()),
                }
            else:
                log_event("EmailAgent", {"event": "email_failed", "error": email_result["error"]})
                return {"status": "error", "message": email_result["error"]}

        except Exception as e:
            log_event("EmailAgent", {"event": "email_exception", "error": str(e)})
            return {"status": "error", "message": str(e)}

    def generate_email_content(
        self,
        template_name,
        subject,
        custom_body,
        variables,
        include_documentation,
        documentation_topic,
    ):
        """Generate email subject and body based on template or custom content."""
        template = self.email_templates.get(template_name, self.email_templates["general_followup"])

        # Determine Subject
        final_subject = subject if subject else template["subject"]
        final_subject = final_subject.format(**variables)

        # Determine Body
        if custom_body:
            final_body = custom_body
        else:
            final_body = template["body"]

        # Format body with variables
        # Use safe formatting to avoid errors if variables are missing
        for key, value in variables.items():
            final_body = final_body.replace(f"{{{key}}}", str(value))

        # Append documentation if requested
        if include_documentation and documentation_topic:
            doc_section = f"\n\nRegarding {documentation_topic}, please check our help center for more details."
            final_body += doc_section

        return {"subject": final_subject, "body": final_body}

    async def send_email(self, recipient, content):
        """Simulate sending an email via SMTP/API."""
        # In a real implementation, this would use a library like smtplib or SendGrid API
        await asyncio.sleep(0.5)  # Simulate network delay

        # Mock success
        return {"success": True, "message_id": str(uuid.uuid4())}
