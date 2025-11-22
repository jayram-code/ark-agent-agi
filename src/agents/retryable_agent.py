from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
from utils import validators
import uuid, datetime
import asyncio
import random

VALIDATOR_MAP = {
    "non_empty_plan": validators.non_empty_plan,
    "contains_action_items": validators.contains_action_items,
    "valid_planner_output": validators.valid_planner_output,
    "high_confidence_plan": validators.high_confidence_plan,
    "strict_mode_validator": validators.strict_mode_validator,
    "non_empty_malformed_safe": validators.non_empty_malformed_safe,
}


class RetryableAgent(BaseAgent):
    def _get_validator(self, name, args):
        if name is None:
            return lambda r: True
        if name.startswith("supervisor_score_above:"):
            try:
                thr = float(name.split(":")[1])
                return validators.supervisor_score_above(thr)
            except Exception:
                return validators.non_empty_plan
        return VALIDATOR_MAP.get(name, validators.non_empty_plan)

    def _calculate_backoff(self, attempt, base_delay=0.5, exponential=True):
        jitter = random.uniform(0, 0.1 * base_delay)
        if exponential:
            return (base_delay * (2 ** (attempt - 1))) + jitter
        return (base_delay * attempt) + jitter

    async def receive(self, message: AgentMessage):
        log_event("RetryableAgent", "Starting enhanced retryable execution")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        agent_name = payload.get("agent")
        max_retries = int(payload.get("max_retries", 3))
        validator_name = payload.get("validator", "valid_planner_output")
        validator_args = payload.get("validator_args", {})
        original_payload = payload.get("original_payload", {})
        base_delay = float(payload.get("retry_delay", 0.5))
        exponential_backoff = bool(payload.get("exponential_backoff", True))

        if not agent_name:
            return {"status": "error", "reason": "no_target_agent_specified"}

        validator = self._get_validator(validator_name, validator_args)
        validation_errors = []
        last_result = None

        for attempt in range(1, max_retries + 1):
            log_event(
                "RetryableAgent",
                {"attempt": attempt, "target": agent_name, "validator": validator_name},
            )

            m = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="retryable_agent",
                receiver=agent_name,
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload=original_payload,
            )

            try:
                last_result = await self.orchestrator.send_a2a(m)
                log_event("RetryableAgent", {"attempt_success": attempt})
            except Exception as e:
                log_event("RetryableAgent", {"attempt_error": str(e), "attempt": attempt})
                last_result = {"status": "error", "error": str(e)}

            try:
                # Note: Validators might need to be updated to handle AgentMessage objects or dicts
                # For now assuming last_result is the return value from send_a2a which might be a dict or AgentMessage
                # We should probably convert to dict for validation if validators expect dicts
                val_input = last_result
                if hasattr(last_result, "dict"):
                    val_input = last_result.dict()
                elif hasattr(
                    last_result, "payload"
                ):  # If it's an AgentMessage but not pydantic model yet (unlikely)
                    val_input = last_result.payload

                if validator(val_input):
                    return {
                        "status": "accepted",
                        "attempt": attempt,
                        "result": last_result,
                        "validation_passed": True,
                    }
                else:
                    validation_errors.append({"attempt": attempt, "error": "validation_failed"})
            except Exception as e:
                validation_errors.append(
                    {"attempt": attempt, "error": f"validator_exception: {str(e)}"}
                )

            if attempt < max_retries:
                backoff_delay = self._calculate_backoff(attempt, base_delay, exponential_backoff)
                await asyncio.sleep(backoff_delay)

        return {
            "status": "retries_exhausted",
            "attempts": max_retries,
            "last_result": last_result,
            "validation_errors": validation_errors,
        }
