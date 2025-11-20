from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
import random
import time

class PaymentProvider(ABC):
    @abstractmethod
    async def process_refund(self, customer_id: str, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
        pass

class MockPaymentProvider(PaymentProvider):
    async def process_refund(self, customer_id: str, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
        # Simulate network latency
        await asyncio.sleep(0.1)
        
        # Mock success logic
        return {
            "success": True,
            "refund_id": f"mock_ref_{order_id}_{int(time.time())}",
            "transaction_fee": 0,
            "net_amount": amount,
            "provider": "mock"
        }

class StripeProvider(PaymentProvider):
    async def process_refund(self, customer_id: str, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        if random.random() < 0.95:
            return {
                "success": True,
                "refund_id": f"stripe_ref_{order_id}_{int(time.time())}",
                "transaction_fee": amount * 0.029,
                "net_amount": amount * 0.971,
                "provider": "stripe"
            }
        return {"success": False, "error": "Stripe API declined"}
