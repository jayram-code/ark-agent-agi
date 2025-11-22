from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio


class ShippingProvider(ABC):
    @abstractmethod
    async def get_shipping_status(self, order_id: str) -> Dict[str, Any]:
        pass


class MockShippingProvider(ShippingProvider):
    async def get_shipping_status(self, order_id: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "status": "in_transit",
            "tracking_number": f"TRK_{order_id}",
            "estimated_delivery": "2023-12-25",
            "provider": "mock",
        }
