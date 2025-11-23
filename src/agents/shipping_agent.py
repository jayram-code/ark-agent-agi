import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.observability.logging_utils import log_event
from utils.openapi_tool import get_shipping_information


class ShippingAgent(BaseAgent):
    async def receive(self, message: AgentMessage):
        log_event("ShippingAgent", "Checking shipping status")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        order_id = payload.get("order_id")

        # Simulate shipping check or use tool
        # In reality, get_shipping_information might be synchronous
        try:
            # shipping_result = get_shipping_information(order_id)
            # For now, simulate async
            await asyncio.sleep(0.1)
            status = "shipped"
            tracking_number = f"TRK-{uuid.uuid4().hex[:8].upper()}"
            estimated_delivery = "2023-12-25"
        except Exception:
            status = "unknown"
            tracking_number = None
            estimated_delivery = None

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="shipping_agent",
            receiver=message.sender,  # Reply to sender
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "order_id": order_id,
                "status": status,
                "tracking_number": tracking_number,
                "estimated_delivery": estimated_delivery,
            },
        )

        return await self.orchestrator.send_a2a(response)
