from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio
import hashlib
import random
import time

class RefundAgent(BaseAgent):
    def __init__(self, name, orchestrator):
        super().__init__(name, orchestrator)
        self.payment_providers = {
            "stripe": self.process_stripe_refund,
            "paypal": self.process_paypal_refund,
            "internal": self.process_internal_refund
        }

    async def receive(self, message: AgentMessage):
        log_event("RefundAgent", "Processing refund request")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        customer_id = payload.get("customer_id")
        order_id = payload.get("order_id")
        amount = float(payload.get("amount", 0.0))
        reason = payload.get("reason", "No reason provided")
        payment_method = payload.get("payment_method", "internal")
        auto_approve = payload.get("auto_approve", False)
        
        # 1. Validate Order
        validation = await self.simulate_order_validation(customer_id, order_id, amount)
        if not validation["valid"]:
            return {
                "status": "refund_failed",
                "error": validation["reason"],
                "risk_level": validation["risk_level"]
            }
            
        # 2. Risk Assessment
        risk_level = validation["risk_level"]
        if auto_approve:
            risk_level = "low"
            
        # 3. Process or Queue
        if risk_level == "low":
            return await self.process_automated_refund(customer_id, order_id, amount, payment_method, reason, message.session_id)
        else:
            return await self.create_refund_ticket(customer_id, order_id, amount, payment_method, reason, risk_level, message.session_id)

    async def simulate_order_validation(self, customer_id, order_id, requested_amount):
        """Simulate order validation"""
        # Simulate async DB call
        await asyncio.sleep(0.05)
        
        # Generate consistent mock data based on customer_id and order_id
        order_hash = hashlib.md5(f"{customer_id}_{order_id}".encode()).hexdigest()
        order_amount = 50 + (int(order_hash[:4], 16) % 450)  # $50-$500 range
        
        # Simulate some orders as already refunded
        refunded = int(order_hash[4:6], 16) % 10 == 0  # 10% chance of already refunded
        
        # Simulate order date (within last 90 days)
        days_ago = int(order_hash[6:8], 16) % 90
        order_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        
        if refunded:
            return {"valid": False, "reason": "Order already refunded", "risk_level": "high"}
        
        if requested_amount > order_amount:
            return {"valid": False, "reason": "Refund amount exceeds order amount", "risk_level": "high"}
            
        # Assess risk
        risk_level = "low"
        if requested_amount > 200:
            risk_level = "high"
        elif requested_amount > 100:
            risk_level = "medium"
            
        if days_ago > 30:
            risk_level = "high"
            
        return {
            "valid": True,
            "risk_level": risk_level,
            "reason": "Validation passed",
            "order_amount": order_amount,
            "order_date": order_date.isoformat()
        }

    async def process_automated_refund(self, customer_id, order_id, amount, payment_method, reason, session_id):
        log_event("RefundAgent", {"event": "processing_automated_refund", "customer_id": customer_id, "amount": amount})
        
        processor = self.payment_providers.get(payment_method, self.process_internal_refund)
        refund_result = await processor(customer_id, order_id, amount, reason)
        
        if refund_result["success"]:
            # Create success ticket
            ticket_message = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                sender="refund_agent",
                receiver="ticket_agent",
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload={
                    "intent": "refund_processed",
                    "text": f"Automated refund processed successfully. Customer: {customer_id}, Order: {order_id}, Amount: ${amount}, Method: {payment_method}, Reason: {reason}",
                    "customer_id": customer_id,
                    "priority_score": 0.3,
                    "key_phrases": ["refund processed", "automated", "successful"],
                    "status": "resolved"
                }
            )
            await self.orchestrator.send_a2a(ticket_message)
            
            # Send confirmation
            await self.send_refund_confirmation(customer_id, order_id, amount, "refund_processed", session_id)
            
            return {
                "status": "refund_processed",
                "refund_id": refund_result.get("refund_id", f"REF_{order_id}"),
                "amount": amount,
                "method": payment_method,
                "processing_time": "instant",
                "message": "Refund processed successfully"
            }
        else:
            return {
                "status": "refund_failed",
                "error": refund_result.get("error", "Payment processing failed"),
                "requires_manual_review": True
            }

    async def create_refund_ticket(self, customer_id, order_id, amount, payment_method, reason, risk_level, session_id):
        log_event("RefundAgent", {"event": "creating_refund_ticket", "customer_id": customer_id, "risk_level": risk_level})
        
        priority_score = 0.8 if risk_level == "high" else 0.6
        status = "requires_approval" if risk_level == "high" else "pending_review"
        
        ticket_message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender="refund_agent",
            receiver="ticket_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "intent": "refund_request",
                "text": f"Refund request requires manual review. Customer: {customer_id}, Order: {order_id}, Amount: ${amount}, Risk Level: {risk_level}, Reason: {reason}",
                "customer_id": customer_id,
                "priority_score": priority_score,
                "key_phrases": ["refund request", "manual review", risk_level, "requires approval"],
                "status": status
            }
        )
        
        ticket_result = await self.orchestrator.send_a2a(ticket_message)
        
        return {
            "status": "refund_queued",
            "ticket_id": ticket_result.get("ticket_id"),
            "risk_level": risk_level,
            "message": f"Refund request queued for {risk_level} risk review",
            "requires_manual_review": True
        }

    async def process_stripe_refund(self, customer_id, order_id, amount, reason):
        await asyncio.sleep(0.1)
        if random.random() < 0.95:
            return {
                "success": True,
                "refund_id": f"stripe_ref_{order_id}_{int(time.time())}",
                "transaction_fee": amount * 0.029,
                "net_amount": amount * 0.971
            }
        return {"success": False, "error": "Stripe API declined"}

    async def process_paypal_refund(self, customer_id, order_id, amount, reason):
        await asyncio.sleep(0.15)
        if random.random() < 0.92:
            return {
                "success": True,
                "refund_id": f"paypal_ref_{order_id}_{int(time.time())}",
                "transaction_fee": amount * 0.034,
                "net_amount": amount * 0.966
            }
        return {"success": False, "error": "PayPal API declined"}

    async def process_internal_refund(self, customer_id, order_id, amount, reason):
        await asyncio.sleep(0.05)
        return {
            "success": True,
            "refund_id": f"internal_ref_{order_id}_{int(time.time())}",
            "transaction_fee": 0,
            "net_amount": amount
        }

    async def send_refund_confirmation(self, customer_id, order_id, amount, status, session_id):
        confirmation_message = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender="refund_agent",
            receiver="email_sender_agent",
            type=MessageType.TASK_REQUEST,
            timestamp=str(datetime.datetime.utcnow()),
            payload={
                "recipient": customer_id,
                "subject": f"Refund Processed - Order {order_id}",
                "template": "refund_confirmation",
                "variables": {
                    "customer_id": customer_id,
                    "order_id": order_id,
                    "amount": amount,
                    "status": status,
                    "processing_time": "instant" if status == "refund_processed" else "1-2 business days"
                }
            }
        )
        try:
            await self.orchestrator.send_a2a(confirmation_message)
        except Exception:
            pass