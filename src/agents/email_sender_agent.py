import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.logging_utils import log_event


class EmailSenderAgent(BaseAgent):
    """
    Email Sender Agent - handles automated email communications with customers.
    Provides templated emails, documentation links, and follow-up scheduling.
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
        """Process email sending requests"""
        log_event("EmailSenderAgent", {"event": "email_request_received", "message_id": message.id})

        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        # Extract email parameters
        recipient = payload.get("recipient")
        template_name = payload.get("template", "general_followup")
        subject = payload.get("subject")
        custom_body = payload.get("body")
        variables = payload.get("variables", {})
        include_documentation = payload.get("include_documentation", False)
        documentation_topic = payload.get("documentation_topic", "")

        if not recipient:
            log_event("EmailSenderAgent", {"event": "email_failed", "reason": "no_recipient"})
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
                    "EmailSenderAgent",
                    {
                        "event": "email_sent",
                        "recipient": recipient,
                        "template": template_name,
                        "subject": email_content["subject"],
                    },
                )

                # Schedule follow-up if requested
                if payload.get("schedule_followup"):
                    await self.schedule_followup(recipient, template_name, variables)

                return {
                    "status": "email_sent",
                    "recipient": recipient,
                    "subject": email_content["subject"],
                    "message_id": email_result.get("message_id"),
                    "documentation_included": include_documentation,
                }
            else:
                log_event(
                    "EmailSenderAgent",
                    {
                        "event": "email_failed",
                        "recipient": recipient,
                        "reason": email_result.get("error"),
                    },
                )
                return {
                    "status": "email_failed",
                    "error": email_result.get("error"),
                    "recipient": recipient,
                }

        except Exception as e:
            log_event("EmailSenderAgent", {"event": "email_error", "error": str(e)})
            return {"status": "error", "error": str(e)}

    def generate_email_content(
        self,
        template_name,
        subject,
        custom_body,
        variables,
        include_documentation,
        documentation_topic,
    ):
        """Generate email content using templates and variables"""

        # Get template
        template = self.email_templates.get(template_name, self.email_templates["general_followup"])

        # Use custom subject if provided, otherwise use template subject
        if not subject and template.get("subject"):
            subject = template["subject"].format(**variables)
        elif not subject:
            subject = "Customer Support Update"

        # Generate body
        if custom_body:
            body = custom_body.format(**variables)
        else:
            body = template["body"].format(**variables)

        # Add documentation if requested
        if include_documentation:
            doc_content = self.get_documentation_content(
                documentation_topic or variables.get("topic", "general")
            )
            body += f"\n\n{doc_content}"

        return {"subject": subject, "body": body, "priority": template.get("priority", "medium")}

    def get_documentation_content(self, topic):
        """Get documentation content for specific topics"""

        documentation = {
            "refund": """
Documentation Links:
- Refund Policy: https://example.com/refund-policy
- Refund Status: https://example.com/my-account/refunds
            """,
            "shipping": """
Documentation Links:
- Shipping Guide: https://example.com/shipping-guide
- Track Order: https://example.com/track-order
            """,
            "technical": """
Documentation Links:
- Troubleshooting: https://example.com/troubleshooting
- System Status: https://status.example.com
            """,
            "general": """
Documentation Links:
- Help Center: https://help.example.com
- Contact Us: https://example.com/contact
            """,
        }

        return documentation.get(topic, documentation["general"]).strip()

    async def send_email(self, recipient, content):
        """Simulate sending an email via SMTP or API"""
        # Simulate network latency
        await asyncio.sleep(0.1)

        # Mock success
        return {"success": True, "message_id": f"msg_{uuid.uuid4().hex[:12]}"}

    async def schedule_followup(self, recipient, template_name, variables):
        """Schedule a follow-up email"""
        # In a real system, this would add a job to a queue
        log_event("EmailSenderAgent", {"event": "followup_scheduled", "recipient": recipient})
