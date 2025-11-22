from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
import uuid, datetime
import json
import os
import asyncio


class AnalyticsAgent(BaseAgent):
    """
    Agent responsible for collecting and aggregating system metrics.
    Writes metrics to evaluation/metrics.json.
    """

    def __init__(self, agent_id: str, orchestrator):
        super().__init__(agent_id, orchestrator)
        self.metrics_file = "evaluation/metrics.json"
        self.metrics = {
            "total_messages": 0,
            "agent_activity": {},
            "errors": 0,
            "start_time": str(datetime.datetime.utcnow()),
        }
        self._load_metrics()

    def _load_metrics(self):
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r") as f:
                    saved_metrics = json.load(f)
                    # Merge or overwrite? For now, let's just keep running totals if possible,
                    # but for simplicity in this demo, we might reset or append.
                    # Let's keep the structure but update values.
                    self.metrics.update(saved_metrics)
            except Exception:
                pass  # Start fresh if corrupt

    def _save_metrics(self):
        os.makedirs("evaluation", exist_ok=True)
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

    async def receive(self, message: AgentMessage):
        # AnalyticsAgent can receive explicit "track_metric" tasks
        # OR it could be designed to intercept all messages if the orchestrator supported it.
        # For this implementation, we'll assume it receives explicit tracking events
        # or we can manually call it from the orchestrator (if we modified orchestrator).
        # Here we implement the explicit "track" interface.

        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        if payload.get("action") == "track":
            metric_type = payload.get("type", "generic")
            value = payload.get("value", 1)
            source = payload.get("source", "unknown")

            from utils.metrics import increment

            increment("total_messages", 1)
            increment("agent_activity", 1, tags={"agent": source})

            if metric_type == "error":
                increment("errors", 1)

            # self._save_metrics() # Deprecated in favor of structured logging

            log_event("AnalyticsAgent", f"Tracked metric: {metric_type} from {source}")

            return await self.orchestrator.send_a2a(
                AgentMessage(
                    id=str(uuid.uuid4()),
                    session_id=message.session_id,
                    sender="analytics_agent",
                    receiver=message.sender,
                    type=MessageType.TASK_RESPONSE,
                    timestamp=str(datetime.datetime.utcnow()),
                    payload={"status": "tracked"},
                )
            )

        elif payload.get("action") == "get_report":
            return await self.orchestrator.send_a2a(
                AgentMessage(
                    id=str(uuid.uuid4()),
                    session_id=message.session_id,
                    sender="analytics_agent",
                    receiver=message.sender,
                    type=MessageType.TASK_RESPONSE,
                    timestamp=str(datetime.datetime.utcnow()),
                    payload={"report": self.metrics},
                )
            )

        return await self.orchestrator.send_a2a(
            AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="analytics_agent",
                receiver=message.sender,
                type=MessageType.INFO,  # Just ack
                timestamp=str(datetime.datetime.utcnow()),
                payload={"status": "ignored", "reason": "unknown_action"},
            )
        )
