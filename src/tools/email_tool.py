"""
Email/SMTP Tool for ARK Agent AGI
Send emails programmatically
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from tools.base import BaseTool
from utils.observability.logging_utils import log_event


class EmailTool(BaseTool):
    """
    Send emails via SMTP
    """

    def __init__(self):
        super().__init__(name="email", description="Send emails via SMTP")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        log_event(
            "EmailTool",
            {
                "event": "initialized",
                "has_credentials": bool(self.smtp_user and self.smtp_password),
            },
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute email send.
        Args:
            to (list): List of recipient email addresses
            subject (str): Email subject
            body (str): Email body
            html (bool): Whether body is HTML (default: False)
            from_addr (str): From address (optional)
        """
        return self.send_email(
            kwargs.get("to", []),
            kwargs.get("subject", ""),
            kwargs.get("body", ""),
            kwargs.get("html", False),
            kwargs.get("from_addr"),
        )

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = False,
        from_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            from_addr: From address (defaults to SMTP_USER)

        Returns:
            Send result
        """
        if not self.smtp_user or not self.smtp_password:
            return {
                "success": False,
                "error": "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD.",
            }

        try:
            from_addr = from_addr or self.smtp_user

            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html" if html else "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            log_event("EmailTool", {"event": "email_sent", "to": to, "subject": subject})

            return {
                "success": True,
                "message": f"Email sent to {len(to)} recipient(s)",
                "recipients": to,
            }

        except Exception as e:
            log_event("EmailTool", {"event": "email_error", "error": str(e)})
            return {"success": False, "error": str(e), "error_type": type(e).__name__}


email_tool = EmailTool()
