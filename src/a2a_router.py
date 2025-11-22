import asyncio
import time
import uuid

from models.messages import AgentMessage
from services.session_service import SESSION
from utils.a2a_schema import validate_message
from utils.logging_utils import log_event
from utils.metrics import accumulate_trace_time, ensure_trace, record_latency


async def send_message(orchestrator, message):
    """
    Validate message, optionally mutate, then route via orchestrator.
    Central place for A2A concerns (logging, retries, transforms).
    """
    # Convert to AgentMessage if dict
    if isinstance(message, dict):
        # We need to handle trace_id injection before validation if it was a dict
        if "trace_id" not in message or not message.get("trace_id"):
            message["trace_id"] = str(uuid.uuid4())

        # Validate legacy dicts
        validate_message(message)
        message = AgentMessage(**message)

    # If it's already a model, ensure trace_id
    if not message.trace_id:
        message.trace_id = str(uuid.uuid4())

    ensure_trace(message.trace_id)  # initialize trace accumulator

    # optional place to compact context / add metadata
    # e.g., attach routing hints, attempt counts, etc.
    # For Pydantic, we access payload as object or dict depending on definition
    # In our definition, payload is Union[MessagePayload, Dict]

    # Helper to access payload dict safely
    payload_dict = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
    if not isinstance(payload_dict, dict):
        # Should not happen given the model, but safety check
        payload_dict = {}

    metadata = payload_dict.get("metadata", {})
    if "hops" not in metadata:
        metadata["hops"] = 0
    metadata["hops"] += 1

    # Update metadata in the message object
    if hasattr(message.payload, "metadata"):
        message.payload.metadata = metadata
    elif isinstance(message.payload, dict):
        message.payload["metadata"] = metadata

    # route the message with latency measurement
    start = time.time()
    output = await orchestrator.route(message)
    latency_ms = (time.time() - start) * 1000.0

    # log standardized observability entry
    try:
        log_event(
            "A2A",
            {
                "timestamp": time.time(),
                "trace_id": message.trace_id,
                "sender": message.sender,
                "receiver": message.receiver,
                "payload": payload_dict,
                "output": output,
                "latency_ms": round(latency_ms, 2),
            },
        )
    except Exception:
        pass

    # record metrics
    try:
        record_latency(
            "a2a_message_latency_ms",
            latency_ms,
            tags={"sender": message.sender, "receiver": message.receiver},
        )
        accumulate_trace_time(message.trace_id, latency_ms)
        # SESSION update might need dict, let's convert back for legacy service
        msg_dict = message.dict()
        SESSION.update_from_message(msg_dict, output=output, latency_ms=latency_ms)
    except Exception:
        pass

    return output
