"""
RetryableAgent (Retry / Validate wrapper)
Usage:
- Send an A2A message to 'retryable_agent' with payload:
{
  "agent": "planner_agent",          # target agent name to call
  "max_retries": 3,
  "validator": "non_empty_plan",    # name of validator (string) supported below
  "validator_args": {},             # optional args for validator
  "original_payload": { ... }       # payload forwarded to target agent
}
The agent will call orchestrator.send_a2a() to the target agent, examine the returned result,
run the validator, and if rejected, re-run up to max_retries. Final result is returned to caller.
"""

from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils import validators
import time, uuid, datetime

VALIDATOR_MAP = {
    "non_empty_plan": validators.non_empty_plan,
    "contains_action_items": validators.contains_action_items,
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

    def receive(self, message):
        log_event("RetryableAgent", "Starting retryable execution")
        payload = message.get("payload", {}) or {}
        agent_name = payload.get("agent")
        max_retries = int(payload.get("max_retries", 3))
        validator_name = payload.get("validator")
        validator_args = payload.get("validator_args", {})
        original_payload = payload.get("original_payload", {})

        if not agent_name:
            return {"status":"error","reason":"no_target_agent_specified"}

        validator = self._get_validator(validator_name, validator_args)

        last_result = None
        for attempt in range(1, max_retries+1):
            log_event("RetryableAgent", {"attempt": attempt, "target": agent_name})
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
            except Exception as e:
                log_event("RetryableAgent", {"error": str(e)})
                last_result = {"status":"error","error": str(e)}

            # if validator accepts, return success
            try:
                if validator(last_result):
                    log_event("RetryableAgent", {"accepted_on_attempt": attempt})
                    return {"status":"accepted","attempt":attempt,"result": last_result}
            except Exception as e:
                # validator error -> treat as reject and continue
                log_event("RetryableAgent", {"validator_error": str(e)})
            # wait small backoff before retrying
            time.sleep(0.5 * attempt)

        # final fallback return last_result with a flag
        return {"status":"retries_exhausted","attempts": max_retries, "last_result": last_result}
