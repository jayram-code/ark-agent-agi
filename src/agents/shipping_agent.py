"""
ShippingAgent - example OpenAPI tool usage (calls a shipping tracker API)
This agent demonstrates calling a shipping tracking API (mocked by the developer).
It expects payload: {"order_id": "12345", "next": "planner_agent"}
"""
from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import requests, uuid, datetime, os, json

MOCK_URL = os.getenv("SHIPPING_API_URL", "http://localhost:8082/track")

class ShippingAgent(BaseAgent):
    def receive(self, message):
        log_event("ShippingAgent", "Querying shipping API")
        payload = message.get("payload", {})
        order_id = payload.get("order_id")
        if not order_id:
            return {"status":"error","reason":"no_order_id"}

        try:
            r = requests.get(MOCK_URL, params={"order_id": order_id}, timeout=5)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log_event("ShippingAgent", f"API error: {e}")
            data = {"status":"unknown","error": str(e)}

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message.get("session_id"),
            "sender": "shipping_agent",
            "receiver": payload.get("next", "planner_agent"),
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "order_id": order_id,
                "tracking": data
            }
        }
        return self.orchestrator.send_a2a(response)

