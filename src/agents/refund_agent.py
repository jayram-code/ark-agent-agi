from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

class RefundAgent(BaseAgent):
    """
    Refund Agent - handles automated refund processing with payment system integration.
    Provides one-click refund automation with proper validation and audit trails.
    """
    
    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        # Placeholder for payment system integration
        # In production, this would integrate with Stripe, PayPal, or internal payment systems
        self.payment_providers = {
            "stripe": self.process_stripe_refund,
            "paypal": self.process_paypal_refund,
            "internal": self.process_internal_refund
        }
    
    def receive(self, message):
        """Process refund requests with validation and automation"""
        log_event("RefundAgent", {"event": "refund_request_received", "message_id": message.get("id")})
        
        payload = message.get("payload", {})
        
        # Extract refund parameters
        customer_id = payload.get("customer_id")
        order_id = payload.get("order_id")
        amount = payload.get("amount")
        reason = payload.get("reason", "Customer request")
        payment_method = payload.get("payment_method", "internal")  # Default to internal
        auto_approve = payload.get("auto_approve", False)  # For low-risk refunds
        
        # Validate refund request
        validation_result = self.validate_refund_request(customer_id, order_id, amount, payment_method)
        
        if not validation_result["valid"]:
            log_event("RefundAgent", {"event": "refund_validation_failed", "reason": validation_result["reason"]})
            return {
                "status": "refund_validation_failed",
                "reason": validation_result["reason"],
                "requires_manual_review": True
            }
        
        # Process refund based on validation and auto-approval settings
        if auto_approve and validation_result["risk_level"] == "low":
            refund_result = self.process_automated_refund(customer_id, order_id, amount, payment_method, reason)
        else:
            refund_result = self.create_refund_ticket(customer_id, order_id, amount, payment_method, reason, validation_result["risk_level"])
        
        # Send confirmation notification
        if refund_result["status"] in ["refund_processed", "refund_approved"]:
            self.send_refund_confirmation(customer_id, order_id, amount, refund_result["status"])
        
        log_event("RefundAgent", {
            "event": "refund_request_complete",
            "status": refund_result["status"],
            "customer_id": customer_id,
            "order_id": order_id,
            "amount": amount
        })
        
        return refund_result
    
    def validate_refund_request(self, customer_id, order_id, amount, payment_method):
        """Validate refund request for fraud prevention and compliance"""
        log_event("RefundAgent", {"event": "validating_refund", "customer_id": customer_id, "order_id": order_id})
        
        # Basic validation
        if not customer_id or not order_id:
            return {"valid": False, "reason": "Missing customer_id or order_id", "risk_level": "high"}
        
        if not amount or amount <= 0:
            return {"valid": False, "reason": "Invalid refund amount", "risk_level": "high"}
        
        # Simulate order validation (in production, this would check actual order data)
        order_validation = self.simulate_order_validation(customer_id, order_id, amount)
        
        if not order_validation["exists"]:
            return {"valid": False, "reason": "Order not found", "risk_level": "high"}
        
        if order_validation["refunded"]:
            return {"valid": False, "reason": "Order already refunded", "risk_level": "high"}
        
        if amount > order_validation["order_amount"]:
            return {"valid": False, "reason": "Refund amount exceeds order amount", "risk_level": "high"}
        
        # Risk assessment based on amount and timing
        risk_level = self.assess_refund_risk(amount, order_validation["order_date"])
        
        return {
            "valid": True,
            "risk_level": risk_level,
            "reason": "Validation passed",
            "order_amount": order_validation["order_amount"],
            "order_date": order_validation["order_date"]
        }
    
    def simulate_order_validation(self, customer_id, order_id, requested_amount):
        """Simulate order validation (replace with real order system integration)"""
        # This is a simulation - in production, this would query your order management system
        import hashlib
        
        # Generate consistent mock data based on customer_id and order_id
        order_hash = hashlib.md5(f"{customer_id}_{order_id}".encode()).hexdigest()
        order_amount = 50 + (int(order_hash[:4], 16) % 450)  # $50-$500 range
        
        # Simulate some orders as already refunded
        refunded = int(order_hash[4:6], 16) % 10 == 0  # 10% chance of already refunded
        
        # Simulate order date (within last 90 days)
        import datetime
        days_ago = int(order_hash[6:8], 16) % 90
        order_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        
        return {
            "exists": True,
            "order_amount": float(order_amount),
            "refunded": refunded,
            "order_date": order_date.isoformat()
        }
    
    def assess_refund_risk(self, amount, order_date):
        """Assess refund risk level for auto-approval decisions"""
        import datetime
        
        # High amount = high risk
        if amount > 200:
            return "high"
        elif amount > 100:
            return "medium"
        
        # Recent orders = lower risk for refund
        try:
            order_datetime = datetime.datetime.fromisoformat(order_date)
            days_since_order = (datetime.datetime.now() - order_datetime).days
            
            if days_since_order < 7:  # Within 7 days
                return "low"
            elif days_since_order < 30:  # Within 30 days
                return "medium"
            else:
                return "high"  # Older orders require review
        except:
            return "medium"  # Default to medium if date parsing fails
    
    def process_automated_refund(self, customer_id, order_id, amount, payment_method, reason):
        """Process automated refund for low-risk cases"""
        log_event("RefundAgent", {"event": "processing_automated_refund", "customer_id": customer_id, "amount": amount})
        
        try:
            # Simulate payment system integration
            processor = self.payment_providers.get(payment_method, self.process_internal_refund)
            refund_result = processor(customer_id, order_id, amount, reason)
            
            if refund_result["success"]:
                # Create success ticket
                ticket_message = {
                    "id": str(uuid.uuid4()),
                    "session_id": str(uuid.uuid4()),
                    "sender": "refund_agent",
                    "receiver": "ticket_agent",
                    "type": "task_request",
                    "timestamp": str(datetime.datetime.utcnow()),
                    "payload": {
                        "intent": "refund_processed",
                        "text": f"Automated refund processed successfully. Customer: {customer_id}, Order: {order_id}, Amount: ${amount}, Method: {payment_method}, Reason: {reason}",
                        "customer_id": customer_id,
                        "priority_score": 0.3,  # Low priority for completed refunds
                        "key_phrases": ["refund processed", "automated", "successful"],
                        "status": "resolved"
                    }
                }
                
                self.orchestrator.send_a2a(ticket_message)
                
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
                
        except Exception as e:
            log_event("RefundAgent", {"event": "automated_refund_failed", "error": str(e)})
            return {
                "status": "refund_failed",
                "error": str(e),
                "requires_manual_review": True
            }
    
    def create_refund_ticket(self, customer_id, order_id, amount, payment_method, reason, risk_level):
        """Create ticket for manual refund review"""
        log_event("RefundAgent", {"event": "creating_refund_ticket", "customer_id": customer_id, "risk_level": risk_level})
        
        priority_score = 0.8 if risk_level == "high" else 0.6
        status = "requires_approval" if risk_level == "high" else "pending_review"
        
        ticket_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "refund_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": "refund_request",
                "text": f"Refund request requires manual review. Customer: {customer_id}, Order: {order_id}, Amount: ${amount}, Risk Level: {risk_level}, Reason: {reason}",
                "customer_id": customer_id,
                "priority_score": priority_score,
                "key_phrases": ["refund request", "manual review", risk_level, "requires approval"],
                "status": status
            }
        }
        
        ticket_result = self.orchestrator.send_a2a(ticket_message)
        
        return {
            "status": "refund_queued",
            "ticket_id": ticket_result.get("ticket_id"),
            "risk_level": risk_level,
            "message": f"Refund request queued for {risk_level} risk review",
            "requires_manual_review": True
        }
    
    def process_stripe_refund(self, customer_id, order_id, amount, reason):
        """Simulate Stripe refund processing"""
        log_event("RefundAgent", {"event": "processing_stripe_refund", "customer_id": customer_id, "amount": amount})
        
        # Simulate API call
        import time
        time.sleep(0.1)  # Simulate API latency
        
        # Simulate 95% success rate
        import random
        if random.random() < 0.95:
            return {
                "success": True,
                "refund_id": f"stripe_ref_{order_id}_{int(time.time())}",
                "transaction_fee": amount * 0.029,  # 2.9% Stripe fee
                "net_amount": amount * 0.971
            }
        else:
            return {
                "success": False,
                "error": "Stripe API declined the refund"
            }
    
    def process_paypal_refund(self, customer_id, order_id, amount, reason):
        """Simulate PayPal refund processing"""
        log_event("RefundAgent", {"event": "processing_paypal_refund", "customer_id": customer_id, "amount": amount})
        
        # Simulate API call
        import time
        time.sleep(0.15)  # Simulate API latency
        
        # Simulate 92% success rate
        import random
        if random.random() < 0.92:
            return {
                "success": True,
                "refund_id": f"paypal_ref_{order_id}_{int(time.time())}",
                "transaction_fee": amount * 0.034,  # 3.4% PayPal fee
                "net_amount": amount * 0.966
            }
        else:
            return {
                "success": False,
                "error": "PayPal API declined the refund"
            }
    
    def process_internal_refund(self, customer_id, order_id, amount, reason):
        """Simulate internal refund processing"""
        log_event("RefundAgent", {"event": "processing_internal_refund", "customer_id": customer_id, "amount": amount})
        
        # Internal refunds are typically faster and have lower fees
        import time
        time.sleep(0.05)  # Simulate processing
        
        return {
            "success": True,
            "refund_id": f"internal_ref_{order_id}_{int(time.time())}",
            "transaction_fee": 0,  # No fees for internal refunds
            "net_amount": amount
        }
    
    def send_refund_confirmation(self, customer_id, order_id, amount, status):
        """Send refund confirmation to customer"""
        log_event("RefundAgent", {"event": "sending_refund_confirmation", "customer_id": customer_id, "status": status})
        
        # Route to EmailSenderAgent (to be created)
        confirmation_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "refund_agent",
            "receiver": "email_sender_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "recipient": customer_id,  # This would be customer's email
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
        }
        
        try:
            self.orchestrator.send_a2a(confirmation_message)
            log_event("RefundAgent", {"event": "refund_confirmation_sent", "customer_id": customer_id})
        except Exception as e:
            log_event("RefundAgent", {"event": "refund_confirmation_failed", "error": str(e)})