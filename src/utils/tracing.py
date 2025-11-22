import json
import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio


class TraceLogger:
    """Logs agent interactions to a JSONL file for observability."""

    def __init__(self, filepath: str = "traces.jsonl"):
        self.filepath = Path(filepath)

    def log(
        self, trace_id: Optional[str], event_type: str, sender: str, receiver: str, payload: Any
    ):
        """Log an event to the trace file."""
        if not trace_id:
            return

        # Handle Pydantic models in payload
        if hasattr(payload, "dict"):
            payload_data = payload.dict()
        elif hasattr(payload, "model_dump"):
            payload_data = payload.model_dump()
        else:
            payload_data = str(payload)

        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "event_type": event_type,
            "sender": sender,
            "receiver": receiver,
            "payload": payload_data,
        }

        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write trace: {e}")


# Global tracer instance
tracer = TraceLogger()
