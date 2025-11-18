"""
Small collection of reusable validators for the RetryableAgent.
Each validator accepts (result_payload: dict) and returns True (accept) or False (reject).
Add more validators here as needed.
"""

def non_empty_plan(result_payload):
    """Accept if payload contains 'plan' with at least one step."""
    p = result_payload.get("payload", {}) if isinstance(result_payload, dict) else {}
    plan = p.get("plan") or p.get("payload", {}).get("plan")
    if plan and isinstance(plan, list) and len(plan) > 0:
        return True
    return False

def supervisor_score_above(threshold):
    """Return a validator function that checks supervisor_score >= threshold."""
    def validator(result_payload):
        p = result_payload.get("payload", {}) if isinstance(result_payload, dict) else {}
        score = p.get("supervisor_score")
        try:
            return float(score) >= float(threshold)
        except Exception:
            return False
    return validator

def contains_action_items(result_payload):
    """Accept if payload contains 'action_items' with at least one item."""
    p = result_payload.get("payload", {}) if isinstance(result_payload, dict) else {}
    actions = p.get("action_items") or p.get("payload", {}).get("action_items")
    return bool(actions)
