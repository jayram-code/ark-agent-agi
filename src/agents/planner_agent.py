"""
PlannerAgent
- Generates ordered resolution steps from input (email, meeting summary, KB)
- Uses Gemini AI for intelligent task planning and breakdown
- Supports strict mode: produce explicit, verifiable actions (useful for supervisor re-runs)
- Returns a payload with 'plan' (list of step dicts) and an overall 'confidence' float
"""

from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.gemini_utils import generate_task_plan
import uuid, datetime

def simple_step_generator(text, kb_passages=None, strict=False):
    """
    Very-lightweight planner:
    - If strict=True produce more granular actionable steps
    - Uses keyword heuristics + KB hints
    """
    kb_passages = kb_passages or []
    text_l = text.lower()
    steps = []

    # If refund/return words are present -> refund workflow
    if any(w in text_l for w in ["refund", "return", "money back"]):
        if strict:
            steps = [
                {"step": 1, "action": "verify_order", "expected_outcome": "Order details confirmed", "detail": "Verify order ID and customer details"},
                {"step": 2, "action": "initiate_refund", "expected_outcome": "Refund processed", "detail": "Process automated refund for eligible orders"},
                {"step": 3, "action": "send_refund_confirmation", "expected_outcome": "Customer notified", "detail": "Send confirmation email with refund details"},
                {"step": 4, "action": "schedule_followup", "expected_outcome": "Follow-up scheduled", "detail": "Schedule 3-day follow-up to confirm satisfaction"}
            ]
        else:
            steps = [
                {"step": 1, "action": "verify_order", "expected_outcome": "Order verified", "detail": "Confirm order details"},
                {"step": 2, "action": "initiate_refund", "expected_outcome": "Refund initiated", "detail": "Process refund request"}
            ]
    elif any(w in text_l for w in ["not delivered","not arrived","delayed","tracking"]):
        if strict:
            steps = [
                {"step": 1, "action": "contact_shipping", "expected_outcome": "Shipping status obtained", "detail": "Contact shipping carrier for status update"},
                {"step": 2, "action": "update_customer", "expected_outcome": "Customer informed", "detail": "Send shipping update with tracking information"},
                {"step": 3, "action": "escalate_if_needed", "expected_outcome": "Issue escalated if required", "detail": "Escalate to shipping operations if package is lost"},
                {"step": 4, "action": "schedule_followup", "expected_outcome": "Follow-up scheduled", "detail": "Schedule 24-hour follow-up"}
            ]
        else:
            steps = [
                {"step": 1, "action": "contact_shipping", "expected_outcome": "Status checked", "detail": "Check shipping status"},
                {"step": 2, "action": "update_customer", "expected_outcome": "Customer updated", "detail": "Inform customer of status"}
            ]
    elif any(w in text_l for w in ["broken", "defective", "not working", "issue"]):
        if strict:
            steps = [
                {"step": 1, "action": "send_documentation", "expected_outcome": "Troubleshooting sent", "detail": "Send relevant troubleshooting documentation"},
                {"step": 2, "action": "verify_issue", "expected_outcome": "Issue confirmed", "detail": "Confirm the technical issue details"},
                {"step": 3, "action": "escalate_to_human", "expected_outcome": "Human support assigned", "detail": "Escalate complex technical issues to specialist"},
                {"step": 4, "action": "schedule_followup", "expected_outcome": "Follow-up scheduled", "detail": "Schedule 48-hour follow-up"}
            ]
        else:
            steps = [
                {"step": 1, "action": "send_documentation", "expected_outcome": "Help provided", "detail": "Provide troubleshooting help"},
                {"step": 2, "action": "escalate_if_needed", "expected_outcome": "Escalation if required", "detail": "Escalate if issue persists"}
            ]
    else:
        # fallback: generic troubleshooting steps possibly using KB
        if strict:
            steps = [
                {"step": 1, "action": "send_documentation", "expected_outcome": "Resources provided", "detail": "Send relevant help documentation"},
                {"step": 2, "action": "clarify_if_needed", "expected_outcome": "Clarity obtained", "detail": "Ask for clarification if needed"},
                {"step": 3, "action": "schedule_followup", "expected_outcome": "Follow-up scheduled", "detail": "Schedule follow-up to ensure resolution"}
            ]
        else:
            steps = [{"step": 1, "action": "send_documentation", "expected_outcome": "Help provided", "detail": "Provide helpful information"}]

    # use KB to increase confidence if matching keywords
    confidence = 0.5
    if kb_passages:
        confidence = min(0.95, 0.6 + 0.1 * len(kb_passages))
    else:
        confidence = 0.45 if strict else 0.6

    return steps, float(confidence)


class PlannerAgent(BaseAgent):
    def receive(self, message):
        log_event("PlannerAgent", "Generating intelligent plan with Gemini AI")
        payload = message.get("payload", {})
        text = payload.get("text", "") or payload.get("summary", "") or payload.get("original", {}).get("text", "")
        strict = payload.get("strict", False)
        kb = payload.get("kb", [])

        kb_texts = []
        if isinstance(kb, list):
            for p in kb:
                if isinstance(p, dict):
                    kb_texts.append(p.get("text", ""))
                elif isinstance(p, str):
                    kb_texts.append(p)
                else:
                    kb_texts.append(str(p))
        
        # Build comprehensive context for Gemini task planning
        context = {
            "customer_id": payload.get("customer_id"),
            "intent": payload.get("intent", "unknown"),
            "sentiment_score": payload.get("sentiment_score", 0.0),
            "emotion": payload.get("emotion", "neutral"),
            "stress": payload.get("stress", 0.0),
            "urgency": payload.get("urgency", "medium"),
            "priority_score": payload.get("priority_score", 0.5),
            "kb_passages": kb_texts[:3],  # Limit to top 3 KB passages
            "strict_mode": strict
        }
        
        # Use Gemini for intelligent task planning
        try:
            task_plan = generate_task_plan(text, context)
            if not isinstance(task_plan, dict):
                task_plan = {
                    "tasks": task_plan if isinstance(task_plan, list) else [],
                    "estimated_time": 2,
                    "resources_needed": [],
                    "success_criteria": [],
                    "potential_challenges": []
                }
            
            plan = []
            tasks_raw = task_plan.get("tasks", []) if isinstance(task_plan, dict) else []
            for idx, task in enumerate(tasks_raw):
                if isinstance(task, dict):
                    action = task.get("action", "unknown")
                    detail = task.get("expected_outcome", "")
                elif isinstance(task, str):
                    action = task
                    detail = ""
                elif isinstance(task, list):
                    action = " ".join(str(x) for x in task)
                    detail = ""
                else:
                    action = "unknown"
                    detail = ""
                plan.append({
                    "step_id": idx + 1,
                    "action": action,
                    "detail": detail,
                    "eta": task_plan.get("estimated_time", "2-4h") if isinstance(task_plan, dict) else "2-4h"
                })
            
            confidence = min(0.95, 0.7 + (0.05 * len(kb_texts))) if kb_texts else 0.7
            
            log_event("PlannerAgent", {
                "plan_steps": len(plan),
                "confidence": confidence,
                "estimated_time": task_plan.get("estimated_time", 2),
                "ai_generated": True
            })
            
        except Exception as e:
            log_event("PlannerAgent", f"Gemini planning failed, falling back: {e}")
            # Fallback to simple step generator
            steps, confidence = simple_step_generator(text, kb_texts, strict=strict)
            plan = [{"step_id": idx+1, "action": s["action"], "detail": s["detail"], "eta": s.get("eta","")} for idx,s in enumerate(steps)]
            task_plan = {
                "resources_needed": ["customer_service"],
                "success_criteria": ["customer_satisfied"],
                "potential_challenges": ["complex_issue"]
            }

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "planner_agent",
            "receiver": "action_executor_agent",  # Route to executor for automation
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "plan": plan,
                "confidence": confidence,
                "estimated_time": task_plan.get("estimated_time", 2),
                "resources_needed": task_plan.get("resources_needed", []),
                "success_criteria": task_plan.get("success_criteria", []),
                "potential_challenges": task_plan.get("potential_challenges", []),
                "original_payload": payload  # Pass original payload for context
            }
        }

        return self.orchestrator.send_a2a(response)
