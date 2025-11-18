from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import uuid, datetime

class ActionExecutorAgent(BaseAgent):
    """
    Action Executor Agent - interprets and executes workflow plans.
    This agent reads plan steps and automatically executes them by routing to appropriate domain agents.
    """
    
    def __init__(self, agent_id, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.action_handlers = {
            "initiate_refund": self.handle_refund,
            "contact_shipping": self.handle_shipping,
            "notify_customer": self.handle_notification,
            "verify_order": self.handle_order_verification,
            "escalate_to_human": self.handle_escalation,
            "send_documentation": self.handle_documentation,
            "update_ticket_status": self.handle_ticket_update,
            "schedule_followup": self.handle_followup_scheduling
        }
    
    def receive(self, message):
        """Receive and execute workflow plans"""
        log_event("ActionExecutorAgent", {"event": "received_plan", "message_id": message.get("id")})
        
        payload = message.get("payload", {})
        plan = payload.get("plan", {})
        tasks = plan if isinstance(plan, list) else plan.get("tasks", [])
        original_payload = payload.get("original_payload", {})
        
        if not tasks:
            log_event("ActionExecutorAgent", {"event": "no_tasks_in_plan"})
            return {"status": "error", "message": "No tasks found in plan"}
        
        execution_results = []
        
        # Execute each task in sequence
        for task in tasks:
            try:
                result = self.execute_task(task, original_payload)
                execution_results.append({
                    "step": task.get("step") or task.get("step_id"),
                    "action": task.get("action"),
                    "result": result,
                    "status": "success"
                })
                log_event("ActionExecutorAgent", {
                    "event": "task_executed",
                    "step": task.get("step"),
                    "action": task.get("action"),
                    "result": result
                })
            except Exception as e:
                execution_results.append({
                    "step": task.get("step") or task.get("step_id"),
                    "action": task.get("action"),
                    "error": str(e),
                    "status": "failed"
                })
                log_event("ActionExecutorAgent", {
                    "event": "task_failed",
                    "step": task.get("step"),
                    "action": task.get("action"),
                    "error": str(e)
                })
                break  # Stop execution on first failure
        
        # Return comprehensive execution results
        final_result = {
            "status": "plan_executed",
            "execution_results": execution_results,
            "total_steps": len(tasks),
            "completed_steps": len([r for r in execution_results if r["status"] == "success"]),
            "original_plan": plan
        }
        
        log_event("ActionExecutorAgent", {
            "event": "plan_execution_complete",
            "total_steps": len(tasks),
            "completed_steps": len([r for r in execution_results if r["status"] == "success"])
        })
        
        return final_result
    
    def execute_task(self, task, original_payload):
        """Execute a single task from the plan"""
        action = task.get("action", "").lower()
        expected_outcome = task.get("expected_outcome", "")
        
        # Find appropriate handler for the action
        handler = None
        for handler_action, handler_func in self.action_handlers.items():
            if handler_action in action:
                handler = handler_func
                break
        
        if handler:
            return handler(task, original_payload, expected_outcome)
        else:
            # Default handler - route to appropriate agent
            return self.route_to_agent(action, task, original_payload)
    
    def handle_refund(self, task, original_payload, expected_outcome):
        """Handle refund initiation"""
        log_event("ActionExecutorAgent", {"event": "initiating_refund", "task": task})
        
        # Route to RefundAgent if available, otherwise create ticket for manual processing
        refund_data = {
            "customer_id": original_payload.get("customer_id"),
            "order_id": original_payload.get("order_id"),
            "amount": original_payload.get("refund_amount"),
            "reason": original_payload.get("reason", "Customer request"),
            "priority": "high" if "urgent" in task.get("action", "").lower() else "normal"
        }
        
        # For now, create a high-priority ticket for refund processing
        ticket_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": "refund_request",
                "text": f"Automated refund request for customer {refund_data['customer_id']}, order {refund_data['order_id']}, amount {refund_data['amount']}, reason: {refund_data['reason']}",
                "sentiment_score": -0.5,  # Slightly negative for refund requests
                "customer_id": refund_data["customer_id"],
                "priority_score": 0.8,  # High priority
                "key_phrases": ["refund", "automated", "customer request"],
                "status": "requires_approval"  # Flag for manual review
            }
        }
        
        result = self.orchestrator.send_a2a(ticket_message)
        return {
            "action": "refund_initiated",
            "ticket_id": result.get("ticket_id"),
            "status": "pending_approval",
            "message": "Refund request ticket created for manual processing"
        }
    
    def handle_shipping(self, task, original_payload, expected_outcome):
        """Handle shipping-related actions"""
        log_event("ActionExecutorAgent", {"event": "contacting_shipping", "task": task})
        
        # Route to ShippingAgent
        shipping_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "shipping_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "action": "track_order",
                "order_id": original_payload.get("order_id"),
                "customer_id": original_payload.get("customer_id"),
                "tracking_number": original_payload.get("tracking_number")
            }
        }
        
        return self.orchestrator.send_a2a(shipping_message)
    
    def handle_notification(self, task, original_payload, expected_outcome):
        """Handle customer notifications"""
        log_event("ActionExecutorAgent", {"event": "sending_notification", "task": task})
        
        # Route to EmailSenderAgent (to be created)
        notification_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "email_sender_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "recipient": original_payload.get("customer_email") or original_payload.get("customer_id"),
                "subject": task.get("subject", "Update on your request"),
                "message": task.get("message", expected_outcome),
                "template": task.get("template", "generic_update"),
                "include_documentation": "documentation" in task.get("action", "").lower()
            }
        }
        
        return self.orchestrator.send_a2a(notification_message)
    
    def handle_order_verification(self, task, original_payload, expected_outcome):
        """Handle order verification"""
        log_event("ActionExecutorAgent", {"event": "verifying_order", "task": task})
        
        # Create verification ticket
        verification_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": "order_verification",
                "text": f"Automated order verification for customer {original_payload.get('customer_id')}, order {original_payload.get('order_id')}",
                "customer_id": original_payload.get("customer_id"),
                "priority_score": 0.6,
                "key_phrases": ["order verification", "automated"]
            }
        }
        
        return self.orchestrator.send_a2a(verification_message)
    
    def handle_escalation(self, task, original_payload, expected_outcome):
        """Handle escalation to human agents"""
        log_event("ActionExecutorAgent", {"event": "escalating_to_human", "task": task})
        
        # Create high-priority escalation ticket
        escalation_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": "human_escalation",
                "text": f"ESCALATION REQUIRED: {task.get('reason', 'Complex issue requiring human intervention')}. Customer: {original_payload.get('customer_id')}",
                "customer_id": original_payload.get("customer_id"),
                "priority_score": 0.9,  # Highest priority
                "key_phrases": ["escalation", "human required", "complex issue"],
                "status": "requires_human_review"
            }
        }
        
        return self.orchestrator.send_a2a(escalation_message)
    
    def handle_documentation(self, task, original_payload, expected_outcome):
        """Handle documentation sending"""
        log_event("ActionExecutorAgent", {"event": "sending_documentation", "task": task})
        
        # Route to KnowledgeAgent for documentation retrieval
        documentation_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "knowledge_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "query": task.get("topic", original_payload.get("intent")),
                "customer_id": original_payload.get("customer_id"),
                "include_links": True,
                "format": "email_friendly"
            }
        }
        
        return self.orchestrator.send_a2a(documentation_message)
    
    def handle_ticket_update(self, task, original_payload, expected_outcome):
        """Handle ticket status updates"""
        log_event("ActionExecutorAgent", {"event": "updating_ticket_status", "task": task})
        
        # This would integrate with ticket management system
        ticket_id = task.get("ticket_id") or original_payload.get("ticket_id")
        new_status = task.get("new_status", "in_progress")
        
        return {
            "action": "ticket_updated",
            "ticket_id": ticket_id,
            "new_status": new_status,
            "message": f"Ticket {ticket_id} status updated to {new_status}"
        }
    
    def handle_followup_scheduling(self, task, original_payload, expected_outcome):
        """Handle follow-up scheduling"""
        log_event("ActionExecutorAgent", {"event": "scheduling_followup", "task": task})
        
        # For now, create a follow-up ticket
        followup_delay = task.get("delay_hours", 24)
        followup_message = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": "action_executor_agent",
            "receiver": "ticket_agent",
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "intent": "followup_scheduled",
                "text": f"Scheduled follow-up for customer {original_payload.get('customer_id')} in {followup_delay} hours. Reason: {task.get('reason', 'Check resolution status')}",
                "customer_id": original_payload.get("customer_id"),
                "priority_score": 0.5,
                "key_phrases": ["followup", "scheduled", f"{followup_delay}h"],
                "status": "scheduled",
                "scheduled_for": followup_delay
            }
        }
        
        return self.orchestrator.send_a2a(followup_message)
    
    def route_to_agent(self, action, task, original_payload):
        """Route unknown actions to appropriate agents based on keywords"""
        log_event("ActionExecutorAgent", {"event": "routing_unknown_action", "action": action})
        
        # Simple keyword-based routing
        if "refund" in action:
            return self.handle_refund(task, original_payload, "")
        elif "shipping" in action or "delivery" in action:
            return self.handle_shipping(task, original_payload, "")
        elif "email" in action or "notify" in action or "contact" in action:
            return self.handle_notification(task, original_payload, "")
        elif "verify" in action or "check" in action:
            return self.handle_order_verification(task, original_payload, "")
        elif "escalate" in action or "human" in action:
            return self.handle_escalation(task, original_payload, "")
        else:
            # Default: create ticket for manual processing
            default_message = {
                "id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "sender": "action_executor_agent",
                "receiver": "ticket_agent",
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "intent": "manual_processing",
                    "text": f"Action requires manual processing: {action}. Task: {task.get('action', 'unknown')}",
                    "customer_id": original_payload.get("customer_id"),
                    "priority_score": 0.4,
                    "key_phrases": ["manual processing", action]
                }
            }
            
            return self.orchestrator.send_a2a(default_message)