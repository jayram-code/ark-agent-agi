from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

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
                "priority": "high"
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
                "priority": "medium"
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
                "priority": "high"
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
                "priority": "low"
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
                "priority": "medium"
            }
        }
    
    def receive(self, message):
        """Process email sending requests"""
        log_event("EmailSenderAgent", {"event": "email_request_received", "message_id": message.get("id")})
        
        payload = message.get("payload", {})
        
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
                template_name, subject, custom_body, variables, 
                include_documentation, documentation_topic
            )
            
            # Simulate email sending (in production, integrate with email service)
            email_result = self.send_email(recipient, email_content)
            
            if email_result["success"]:
                log_event("EmailSenderAgent", {
                    "event": "email_sent",
                    "recipient": recipient,
                    "template": template_name,
                    "subject": email_content["subject"]
                })
                
                # Schedule follow-up if requested
                if payload.get("schedule_followup"):
                    self.schedule_followup(recipient, template_name, variables)
                
                return {
                    "status": "email_sent",
                    "recipient": recipient,
                    "subject": email_content["subject"],
                    "message_id": email_result.get("message_id"),
                    "documentation_included": include_documentation
                }
            else:
                log_event("EmailSenderAgent", {
                    "event": "email_failed",
                    "recipient": recipient,
                    "reason": email_result.get("error")
                })
                return {
                    "status": "email_failed",
                    "error": email_result.get("error"),
                    "recipient": recipient
                }
                
        except Exception as e:
            log_event("EmailSenderAgent", {"event": "email_error", "error": str(e)})
            return {"status": "error", "error": str(e)}
    
    def generate_email_content(self, template_name, subject, custom_body, variables, include_documentation, documentation_topic):
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
            doc_content = self.get_documentation_content(documentation_topic or variables.get("topic", "general"))
            body += f"\n\n{doc_content}"
        
        return {
            "subject": subject,
            "body": body,
            "priority": template.get("priority", "medium")
        }
    
    def get_documentation_content(self, topic):
        """Get documentation content for specific topics"""
        
        documentation = {
            "refund": """
Documentation Links:
• Refund Policy: https://support.example.com/refund-policy
• How to Request a Refund: https://support.example.com/request-refund
• Refund Timeline: https://support.example.com/refund-timeline

Common Questions:
• Q: How long does a refund take?
  A: Refunds typically process within 3-5 business days
• Q: Will I get a full refund?
  A: Yes, you'll receive a full refund minus any processing fees
            """.strip(),
            
            "shipping": """
Documentation Links:
• Shipping Policy: https://support.example.com/shipping
• Track Your Order: https://support.example.com/track-order
• Delivery Issues: https://support.example.com/delivery-issues

Helpful Tips:
• Check your email for tracking information
• Allow 24-48 hours for tracking to update
• Contact us if tracking shows no movement after 3 days
            """.strip(),
            
            "technical": """
Documentation Links:
• Troubleshooting Guide: https://support.example.com/troubleshooting
• System Requirements: https://support.example.com/requirements
• Video Tutorials: https://support.example.com/tutorials

Quick Fixes:
• Clear your browser cache and cookies
• Try a different browser or device
• Disable browser extensions temporarily
            """.strip(),
            
            "account": """
Documentation Links:
• Account Management: https://support.example.com/account
• Password Reset: https://support.example.com/reset-password
• Security Settings: https://support.example.com/security

Account Security:
• Use strong, unique passwords
• Enable two-factor authentication
• Review account activity regularly
            """.strip()
        }
        
        return documentation.get(topic, documentation["general"]) if topic in documentation else ""
    
    def send_email(self, recipient, email_content):
        """Simulate email sending (integrate with real email service in production)"""
        
        # Simulate email service integration
        import time
        import hashlib
        
        # Simulate API latency
        time.sleep(0.1)
        
        # Generate mock message ID
        message_id = hashlib.md5(f"{recipient}_{email_content['subject']}_{time.time()}".encode()).hexdigest()
        
        # Simulate 98% success rate
        import random
        if random.random() < 0.98:
            log_event("EmailSenderAgent", {
                "event": "email_sent_simulation",
                "recipient": recipient,
                "subject": email_content["subject"],
                "priority": email_content["priority"]
            })
            
            return {
                "success": True,
                "message_id": f"msg_{message_id}",
                "sent_at": datetime.datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Email service temporarily unavailable"
            }
    
    def schedule_followup(self, recipient, template_name, variables):
        """Schedule follow-up email (placeholder for scheduling system)"""
        
        # For now, just log the follow-up request
        # In production, integrate with a scheduling service like Celery or cron
        log_event("EmailSenderAgent", {
            "event": "followup_scheduled",
            "recipient": recipient,
            "template": template_name,
            "delay_hours": 48  # Default 48-hour follow-up
        })
        
        return {
            "status": "followup_scheduled",
            "recipient": recipient,
            "template": template_name,
            "scheduled_for": "48 hours"
        }
    
    def create_email_template(self, template_name, subject, body, priority="medium"):
        """Create new email template (for admin use)"""
        self.email_templates[template_name] = {
            "subject": subject,
            "body": body,
            "priority": priority
        }
        
        log_event("EmailSenderAgent", {
            "event": "template_created",
            "template_name": template_name,
            "priority": priority
        })
        
        return {"status": "template_created", "template_name": template_name}
    
    def get_template_list(self):
        """Get list of available templates"""
        return {
            "templates": list(self.email_templates.keys()),
            "count": len(self.email_templates)
        }