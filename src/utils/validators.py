"""
Comprehensive validators for the RetryableAgent.
Each validator accepts (result_payload: dict) and returns True (accept) or False (reject).
Includes specific validators for PlannerAgent output validation.
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

def valid_planner_output(result_payload):
    """
    Comprehensive validator for PlannerAgent output.
    Checks for required keys, proper structure, and valid content.
    """
    if not isinstance(result_payload, dict):
        return False
    
    payload = result_payload.get("payload", {})
    if not isinstance(payload, dict):
        return False
    
    # Check for required top-level keys
    required_keys = ["plan", "confidence"]
    for key in required_keys:
        if key not in payload:
            return False
    
    # Validate plan structure
    plan = payload.get("plan")
    if not isinstance(plan, list) or len(plan) == 0:
        return False
    
    # Validate each plan step
    for step in plan:
        if not isinstance(step, dict):
            return False
        
        # Required step fields
        step_required = ["step_id", "action", "detail"]
        for field in step_required:
            if field not in step:
                return False
        
        # Validate step field types and content
        if not isinstance(step["step_id"], int) or step["step_id"] <= 0:
            return False
        
        if not isinstance(step["action"], str) or len(step["action"].strip()) == 0:
            return False
        
        if not isinstance(step["detail"], str) or len(step["detail"].strip()) == 0:
            return False
    
    # Validate confidence score
    confidence = payload.get("confidence")
    try:
        conf_float = float(confidence)
        if not (0.0 <= conf_float <= 1.0):
            return False
    except (ValueError, TypeError):
        return False
    
    return True

def high_confidence_plan(result_payload):
    """
    Validator that accepts only high-confidence plans (confidence >= 0.7).
    """
    if not valid_planner_output(result_payload):
        return False
    
    payload = result_payload.get("payload", {})
    confidence = float(payload.get("confidence", 0))
    return confidence >= 0.7

def strict_mode_validator(result_payload):
    """
    Validator for strict mode - requires detailed steps with ETA and higher confidence.
    """
    if not valid_planner_output(result_payload):
        return False
    
    payload = result_payload.get("payload", {})
    plan = payload.get("plan", [])
    confidence = float(payload.get("confidence", 0))
    
    # Require higher confidence in strict mode
    if confidence < 0.8:
        return False
    
    # Require ETA in each step for strict mode
    for step in plan:
        if "eta" not in step or not isinstance(step["eta"], str) or len(step["eta"].strip()) == 0:
            return False
    
    # Require minimum number of steps for comprehensive planning
    if len(plan) < 3:
        return False
    
    return True

def non_empty_malformed_safe(result_payload):
    """
    Safety validator that rejects obviously malformed or empty outputs.
    Checks for basic structure and non-empty content.
    """
    if not isinstance(result_payload, dict):
        return False
    
    # Check if result is empty or contains obvious error indicators
    if result_payload.get("status") == "error":
        return False
    
    payload = result_payload.get("payload", {})
    if not payload:
        return False
    
    # Check for empty strings, None values, or malformed data
    def check_malformed(obj):
        if isinstance(obj, dict):
            return any(check_malformed(v) for v in obj.values())
        elif isinstance(obj, list):
            return len(obj) > 0 and any(check_malformed(item) for item in obj)
        elif isinstance(obj, str):
            return len(obj.strip()) > 0
        elif obj is None:
            return False
        else:
            return True
    
    return check_malformed(payload)
