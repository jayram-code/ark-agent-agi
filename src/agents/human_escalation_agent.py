import asyncio
import datetime
import json
import os
import uuid
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.observability.logging_utils import log_event


class HumanEscalationAgent(BaseAgent):
    """
    Agent responsible for escalating tasks to a human for review.
    Stores tasks in a persistent queue (JSON file) and waits for human input.
    """

    def __init__(self, agent_id, orchestrator, queue_path: str = "data/human_queue.json"):
        super().__init__(agent_id, orchestrator)
        self.queue_path = queue_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.queue_path), exist_ok=True)
        if not os.path.exists(self.queue_path):
            with open(self.queue_path, "w") as f:
                json.dump([], f)

    async def receive(self, message: AgentMessage):
        log_event("HumanEscalationAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload

        action = payload.get("action")
        
        if action == "escalate":
            return await self._handle_escalation(message, payload)
        elif action == "review_response":
            return await self._handle_review_response(message, payload)
        else:
            # Default to escalation if no specific action
            return await self._handle_escalation(message, payload)

    async def _handle_escalation(self, message: AgentMessage, payload: Dict[str, Any]):
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "original_sender": message.sender,
            "session_id": message.session_id,
            "description": payload.get("description", "No description provided"),
            "context": payload.get("context", {}),
            "status": "pending",
            "created_at": str(datetime.datetime.utcnow()),
        }
        
        self._add_to_queue(task)
        
        log_event("HumanEscalationAgent", f"Escalated task {task_id} to human queue")
        
        response_payload = {
            "status": "escalated",
            "task_id": task_id,
            "message": "Task has been escalated to a human. Please wait for review."
        }
        
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender=self.name,
            receiver=message.sender,
            type=MessageType.INFO,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )
        
        return await self.orchestrator.send_a2a(response)

    async def _handle_review_response(self, message: AgentMessage, payload: Dict[str, Any]):
        """
        Handle response from human (via CLI or other interface)
        """
        task_id = payload.get("task_id")
        decision = payload.get("decision") # "approve" or "reject"
        feedback = payload.get("feedback", "")
        
        # Update queue status
        task = self._update_task_status(task_id, decision, feedback)
        
        if not task:
            return None
            
        # Notify original sender
        response_payload = {
            "status": "reviewed",
            "decision": decision,
            "feedback": feedback,
            "task_id": task_id,
            "original_context": task.get("context", {})
        }
        
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=task["session_id"],
            sender=self.name,
            receiver=task["original_sender"], # Reply to whoever asked for escalation
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload,
        )
        
        log_event("HumanEscalationAgent", f"Processed review for task {task_id}: {decision}")
        
        return await self.orchestrator.send_a2a(response)

    def _add_to_queue(self, task: Dict[str, Any]):
        queue = self._read_queue()
        queue.append(task)
        self._write_queue(queue)

    def _update_task_status(self, task_id: str, status: str, feedback: str) -> Dict[str, Any]:
        queue = self._read_queue()
        updated_task = None
        for task in queue:
            if task["id"] == task_id:
                task["status"] = status
                task["feedback"] = feedback
                task["reviewed_at"] = str(datetime.datetime.utcnow())
                updated_task = task
                break
        
        if updated_task:
            self._write_queue(queue)
            
        return updated_task

    def _read_queue(self) -> List[Dict[str, Any]]:
        try:
            with open(self.queue_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_queue(self, queue: List[Dict[str, Any]]):
        with open(self.queue_path, "w") as f:
            json.dump(queue, f, indent=2)
