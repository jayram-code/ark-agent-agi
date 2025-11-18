"""
ShippingAgent - OpenAPI tool usage (calls a shipping tracker API)
This agent demonstrates calling a shipping tracking API using the OpenAPI tool wrapper.
It expects payload: {"order_id": "12345", "next": "planner_agent"}
"""
from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.openapi_tool import track_shipping_order, get_shipping_information
import uuid, datetime

class ShippingAgent(BaseAgent):
    def receive(self, message):
        log_event("ShippingAgent", "Querying shipping API using OpenAPI tool")
        payload = message.get("payload", {})
        order_id = payload.get("order_id")
        if not order_id:
            return {"status":"error","reason":"no_order_id"}

        # Use OpenAPI tool to get shipping information
        shipping_result = get_shipping_information(order_id)
        
        if shipping_result["success"]:
            data = shipping_result["shipping_info"]
            log_event("ShippingAgent", {
                "event": "shipping_info_retrieved", 
                "order_id": order_id,
                "status": data.get("status", "unknown")
            })
        else:
            log_event("ShippingAgent", f"Shipping API error: {shipping_result['error']}")
            data = {"status":"unknown","error": shipping_result["error"]}

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

