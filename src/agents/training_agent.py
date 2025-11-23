import asyncio
import datetime
import random
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.observability.logging_utils import log_event


class TrainingAgent(BaseAgent):
    """
    Agent responsible for automating the evaluation and retraining loop.
    Mocks the process of running test sets and triggering model updates.
    """

    async def receive(self, message: AgentMessage):
        log_event("TrainingAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action")

        response_payload = {}

        if action == "run_evaluation":
            results = self._run_evaluation(payload.get("dataset", "default"))
            response_payload = {"status": "completed", "results": results}

            # Auto-trigger retrain if score is low
            if results["accuracy"] < payload.get("threshold", 0.8):
                retrain_job = self._trigger_retrain(results)
                response_payload["retrain_job"] = retrain_job

        elif action == "trigger_retrain":
            job_id = self._trigger_retrain(payload.get("reason"))
            response_payload = {"status": "started", "job_id": job_id}
        else:
            response_payload = {"status": "error", "message": f"Unknown action: {action}"}

        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="training_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )

        return await self.orchestrator.send_a2a(response)

    def _run_evaluation(self, dataset):
        log_event("TrainingAgent", f"Running evaluation on dataset: {dataset}")
        # Mock evaluation logic
        accuracy = random.uniform(0.7, 0.95)
        return {
            "dataset": dataset,
            "accuracy": round(accuracy, 2),
            "latency_ms": random.randint(100, 500),
            "timestamp": str(datetime.datetime.utcnow()),
        }

    def _trigger_retrain(self, context):
        job_id = f"TRAIN-{uuid.uuid4().hex[:6].upper()}"
        log_event("TrainingAgent", f"Triggered retraining job {job_id}. Context: {context}")
        return job_id
