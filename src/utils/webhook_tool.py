"""
Webhook Tool for ARK Agent AGI
Send HTTP webhooks to external services
"""

import requests
from typing import Dict, Any, Optional
from utils.logging_utils import log_event


class WebhookTool:
    """
    Send HTTP webhooks to external endpoints
    """

    def __init__(self):
        log_event("WebhookTool", {"event": "initialized"})

    def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        method: str = "POST",
        headers: Dict[str, str] = None,
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
                response = requests.put(url, json=payload, headers=default_headers, timeout=timeout)
            elif method == "PATCH":
                response = requests.patch(
                    url, json=payload, headers=default_headers, timeout=timeout
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported method: {method}. Use POST, PUT, or PATCH.",
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
                "success": response.ok,
                "status_code": response.status_code,
                "url": url,
                "method": method,
                "response_body": response.text[:500],  # Limit response size
                "headers": dict(response.headers),
            }

        except requests.exceptions.Timeout:
            log_event("WebhookTool", {"event": "webhook_timeout", "url": url})
            return {
                "success": False,
                "error": f"Webhook timeout after {timeout} seconds",
                "url": url,
            }

        except Exception as e:
            log_event("WebhookTool", {"event": "webhook_error", "url": url, "error": str(e)})
            return {"success": False, "error": str(e), "error_type": type(e).__name__, "url": url}


webhook_tool = WebhookTool()
