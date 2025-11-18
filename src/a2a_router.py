from src.utils.a2a_schema import validate_message
from src.utils.logging_utils import log_event
from src.utils.metrics import record_latency, accumulate_trace_time, ensure_trace
from src.services.session_service import SESSION
import time, uuid

def send_message(orchestrator, message: dict):
    """
    Validate message, optionally mutate, then route via orchestrator.
    Central place for A2A concerns (logging, retries, transforms).
    """
    # inject trace_id if missing
    if "trace_id" not in message or not message.get("trace_id"):
        message["trace_id"] = str(uuid.uuid4())
    ensure_trace(message["trace_id"])  # initialize trace accumulator

    # validate (will raise if invalid)
    validate_message(message)

    # optional place to compact context / add metadata
    # e.g., attach routing hints, attempt counts, etc.
    metadata = message.get("payload", {}).get("metadata", {})
    if "hops" not in metadata:
        metadata["hops"] = 0
    metadata["hops"] += 1
    message["payload"].setdefault("metadata", metadata)

    # route the message with latency measurement
    start = time.time()
    output = orchestrator.route(message)
    latency_ms = (time.time() - start) * 1000.0

    # log standardized observability entry
    try:
        log_event("A2A", {
            "timestamp": time.time(),
            "trace_id": message.get("trace_id"),
            "sender": message.get("sender"),
            "receiver": message.get("receiver"),
            "payload": message.get("payload"),
            "output": output,
            "latency_ms": round(latency_ms, 2)
        })
    except Exception:
        pass

    # record metrics
    try:
        record_latency("a2a_message_latency_ms", latency_ms, tags={
            "sender": message.get("sender"),
            "receiver": message.get("receiver")
        })
        accumulate_trace_time(message.get("trace_id"), latency_ms)
        SESSION.update_from_message(message, output=output, latency_ms=latency_ms)
    except Exception:
        pass

    return output
