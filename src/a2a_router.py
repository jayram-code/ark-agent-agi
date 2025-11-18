from src.utils.a2a_schema import validate_message

def send_message(orchestrator, message: dict):
    """
    Validate message, optionally mutate, then route via orchestrator.
    Central place for A2A concerns (logging, retries, transforms).
    """
    # validate (will raise if invalid)
    validate_message(message)

    # optional place to compact context / add metadata
    # e.g., attach routing hints, attempt counts, etc.
    metadata = message.get("payload", {}).get("metadata", {})
    if "hops" not in metadata:
        metadata["hops"] = 0
    metadata["hops"] += 1
    message["payload"].setdefault("metadata", metadata)

    # route the message
    return orchestrator.route(message)
