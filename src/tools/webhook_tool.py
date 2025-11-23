"""
Webhook Tool for ARK Agent AGI
Send HTTP webhooks to external services
"""

from typing import Any, Dict, Optional
import requests
from tools.base import BaseTool
from utils.observability.logging_utils import log_event


class WebhookTool(BaseTool):
    """
    Send HTTP webhooks to external endpoints
    """

    def __init__(self):
        super().__init__(name="webhook_tool", description="Send HTTP webhooks to external endpoints")
        log_event("WebhookTool", {"event": "initialized"})

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the webhook tool.
        
        Args:
            url (str): Webhook URL
            payload (Dict[str, Any]): Data to send
            method (str): HTTP method (default: POST)
            headers (Optional[Dict[str, str]]): Optional HTTP headers
            timeout (int): Request timeout in seconds (default: 10)
        """
        return self.send_webhook(
            url=kwargs.get("url", ""),
            payload=kwargs.get("payload", {}),
            method=kwargs.get("method", "POST"),
            headers=kwargs.get("headers"),
            timeout=kwargs.get("timeout", 10)
        )

    def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Send a webhook to an external endpoint

        Args:
            url: Webhook URL
            payload: Data to send
            method: HTTP method (POST, PUT, PATCH)
            headers: Optional HTTP headers
            timeout: Request timeout in seconds

        Returns:
            Webhook result
        """
        try:
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)

            method = method.upper()

            if method == "POST":
                response = requests.post(
                    url, json=payload, headers=default_headers, timeout=timeout
                )
            elif method == "PUT":
                response = requests.put(
                    url, json=payload, headers=default_headers, timeout=timeout
                )
            elif method == "PATCH":
                response = requests.patch(
                    url, json=payload, headers=default_headers, timeout=timeout
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported method: {method}",
                }

            log_event(
                "WebhookTool",
                {
                    "event": "webhook_sent",
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                },
            )

            return {
                "success": response.status_code >= 200 and response.status_code < 300,
                "status_code": response.status_code,
                "response": response.text,
            }

        except Exception as e:
            log_event("WebhookTool", {"event": "webhook_error", "error": str(e)})
            return {
                "success": False,
                "error": str(e),
            }

# Global instance
webhook_tool = WebhookTool()
