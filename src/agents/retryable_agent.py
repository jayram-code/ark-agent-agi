"""
Enhanced RetryableAgent with advanced validation and retry logic.
Usage:
- Send an A2A message to 'retryable_agent' with payload:
{
  "agent": "planner_agent",          # target agent name to call
  "max_retries": 3,
  "validator": "valid_planner_output",    # name of validator (string) supported below
  "validator_args": {},             # optional args for validator
  "original_payload": { ... },       # payload forwarded to target agent
  "retry_delay": 0.5,               # optional: base delay between retries (seconds)
  "exponential_backoff": true         # optional: use exponential backoff
}
The agent will call orchestrator.send_a2a() to the target agent, examine the returned result,
run the validator, and if rejected, re-run up to max_retries with intelligent backoff.
"""

from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils import validators
import time, uuid, datetime

VALIDATOR_MAP = {
    "non_empty_plan": validators.non_empty_plan,
    "contains_action_items": validators.contains_action_items,
    "valid_planner_output": validators.valid_planner_output,
    "high_confidence_plan": validators.high_confidence_plan,
    "strict_mode_validator": validators.strict_mode_validator,
    "non_empty_malformed_safe": validators.non_empty_malformed_safe,
    # threshold validators are created dynamically (handled below)
}

class RetryableAgent(BaseAgent):
    def _get_validator(self, name, args):
        if name is None:
            return lambda r: True
        if name.startswith("supervisor_score_above:"):
            # allow "supervisor_score_above:0.6" style
            try:
                thr = float(name.split(":")[1])
                return validators.supervisor_score_above(thr)
            except Exception:
                return validators.non_empty_plan
        return VALIDATOR_MAP.get(name, validators.non_empty_plan)

    def _calculate_backoff(self, attempt, base_delay=0.5, exponential=True):
        """Calculate backoff delay with optional exponential increase."""
        if exponential:
            return base_delay * (2 ** (attempt - 1))
        return base_delay * attempt

    def receive(self, message):
        log_event("RetryableAgent", "Starting enhanced retryable execution")
        payload = message.get("payload", {}) or {}
        agent_name = payload.get("agent")
        max_retries = int(payload.get("max_retries", 3))
        validator_name = payload.get("validator", "valid_planner_output")  # Default to comprehensive validator
        validator_args = payload.get("validator_args", {})
        original_payload = payload.get("original_payload", {})
        base_delay = float(payload.get("retry_delay", 0.5))
        exponential_backoff = bool(payload.get("exponential_backoff", True))

        if not agent_name:
            return {"status":"error","reason":"no_target_agent_specified"}

        validator = self._get_validator(validator_name, validator_args)
        validation_errors = []

        last_result = None
        for attempt in range(1, max_retries+1):
            log_event("RetryableAgent", {
                "attempt": attempt, 
                "target": agent_name,
                "validator": validator_name,
                "max_retries": max_retries
            })
            
            # build message to target
            m = {
                "id": str(uuid.uuid4()),
                "session_id": message.get("session_id"),
                "sender": "retryable_agent",
                "receiver": agent_name,
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": original_payload
            }
            
            try:
                # route via orchestrator (A2A)
                last_result = self.orchestrator.send_a2a(m)
                log_event("RetryableAgent", {"attempt_success": attempt, "target_response": "received"})
            except Exception as e:
                log_event("RetryableAgent", {"attempt_error": str(e), "attempt": attempt})
                last_result = {"status":"error","error": str(e)}

            # if validator accepts, return success
            try:
                if validator(last_result):
                    log_event("RetryableAgent", {
                        "accepted_on_attempt": attempt,
                        "validation": "passed",
                        "final_status": "success"
                    })
                    return {
                        "status":"accepted",
                        "attempt":attempt,
                        "result": last_result,
                        "validation_passed": True
                    }
                else:
                    # Record validation failure for debugging
                    validation_errors.append({
                        "attempt": attempt,
                        "error": "validation_failed",
                        "validator": validator_name
                    })
                    log_event("RetryableAgent", {
                        "validation_failed": attempt,
                        "validator": validator_name
                    })
            except Exception as e:
                # validator error -> treat as reject and continue
                validation_errors.append({
                    "attempt": attempt,
                    "error": f"validator_exception: {str(e)}",
                    "validator": validator_name
                })
                log_event("RetryableAgent", {"validator_error": str(e), "attempt": attempt})
            
            # Calculate backoff delay
            if attempt < max_retries:  # Don't delay after the last attempt
                backoff_delay = self._calculate_backoff(attempt, base_delay, exponential_backoff)
                log_event("RetryableAgent", {
                    "retry_delay": backoff_delay,
                    "attempt": attempt,
                    "next_attempt": attempt + 1
                })
                time.sleep(backoff_delay)

        # final fallback return last_result with detailed error information
        log_event("RetryableAgent", {
            "status": "retries_exhausted",
            "total_attempts": max_retries,
            "final_validator": validator_name
        })
        
        return {
            "status":"retries_exhausted",
            "attempts": max_retries, 
            "last_result": last_result,
            "validation_errors": validation_errors,
            "final_validator": validator_name
        }
