"""
PlannerAgent
- Generates ordered resolution steps from input (email, meeting summary, KB)
- Supports strict mode: produce explicit, verifiable actions (useful for supervisor re-runs)
- Returns a payload with 'plan' (list of step dicts) and an overall 'confidence' float
"""

from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
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
                {"action": "verify_order_id", "detail": "Ask customer for order id and proof", "eta":"within 1 business day"},
                {"action": "check_order_status", "detail": "Verify warehouse and tracking", "eta":"within 2 business days"},
                {"action": "initiate_refund", "detail": "Process refund if order not delivered or damaged", "eta":"within 3 business days"},
                {"action": "confirm_with_customer", "detail": "Send final confirmation email with refund ID", "eta":"within 1 business day"}
            ]
        else:
            steps = [
                {"action":"verify_order","detail":"Confirm order id and status"},
                {"action":"process_refund_or_replace","detail":"Issue refund or replacement"}
            ]
    elif any(w in text_l for w in ["not delivered","not arrived","delayed","tracking"]):
        if strict:
            steps = [
                {"action":"check_tracking","detail":"Verify carrier tracking and timestamps"},
                {"action":"contact_warehouse","detail":"Ask operations to validate pickup and shipment"},
                {"action":"escalate_shipping","detail":"Escalate to shipping ops if missing; request proof"},
                {"action":"notify_customer","detail":"Inform customer with next steps & ETA"}
            ]
        else:
            steps = [
                {"action":"check_tracking","detail":"Review tracking status"},
                {"action":"reply_customer","detail":"Explain next steps or escalate"}
            ]
    else:
        # fallback: generic troubleshooting steps possibly using KB
        if strict:
            steps = [
                {"action":"clarify_issue","detail":"Ask clarifying question to customer"},
                {"action":"search_kb","detail":"Retrieve relevant KB passages and propose steps"},
                {"action":"propose_resolution","detail":"Provide suggested resolution or next step"}
            ]
        else:
            steps = [{"action":"clarify","detail":"Ask clarifying question"}]

    # use KB to increase confidence if matching keywords
    confidence = 0.5
    if kb_passages:
        confidence = min(0.95, 0.6 + 0.1 * len(kb_passages))
    else:
        confidence = 0.45 if strict else 0.6

    return steps, float(confidence)


class PlannerAgent(BaseAgent):
    def receive(self, message):
        log_event("PlannerAgent", "Generating plan")
        payload = message.get("payload", {})
        text = payload.get("text", "") or payload.get("summary", "") or payload.get("original", {}).get("text", "")
        strict = payload.get("strict", False)
        kb = payload.get("kb", [])  # list of kb chunks

        # extract kb texts if provided as list of dicts
        kb_texts = [p.get("text","") for p in kb] if isinstance(kb, list) else []

        steps, confidence = simple_step_generator(text, kb_texts, strict=strict)

        plan = [{"step_id": idx+1, "action": s["action"], "detail": s["detail"], "eta": s.get("eta","")} for idx,s in enumerate(steps)]

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "planner_agent",
            "receiver": payload.get("next","ticket_agent"),
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "plan": plan,
                "confidence": confidence,
                "original": payload
            }
        }

        return self.orchestrator.send_a2a(response)
