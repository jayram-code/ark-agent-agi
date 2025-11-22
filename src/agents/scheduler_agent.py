from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from models.messages import AgentMessage, MessageType
import uuid, datetime
import asyncio
import json
import os

class SchedulerAgent(BaseAgent):
    """
    Agent responsible for scheduling and managing long-running tasks.
    """
    def __init__(self, agent_id, orchestrator, storage_path="data/scheduler_tasks.json"):
        super().__init__(agent_id, orchestrator)
        self.storage_path = storage_path
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                log_event("SchedulerAgent", f"Error loading tasks: {e}")
        return []

    def _save_tasks(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.tasks, f, indent=2)

    async def receive(self, message: AgentMessage):
        log_event("SchedulerAgent", f"Received request from {message.sender}")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        action = payload.get("action")
        
        response_payload = {}
        
        if action == "schedule_task":
            task_id = self._schedule_task(payload)
            response_payload = {"status": "scheduled", "task_id": task_id}
        elif action == "check_due_tasks":
            due_tasks = self._check_due_tasks()
            response_payload = {"status": "checked", "due_tasks": due_tasks}
        else:
            response_payload = {"status": "error", "message": f"Unknown action: {action}"}
            
        response = AgentMessage(
            id=str(uuid.uuid4()),
            session_id=message.session_id,
            sender="scheduler_agent",
            receiver=message.sender,
            type=MessageType.TASK_RESPONSE,
            timestamp=str(datetime.datetime.utcnow()),
            payload=response_payload
        )
        
        return await self.orchestrator.send_a2a(response)

    def _schedule_task(self, payload):
        task_id = f"TASK-{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "type": payload.get("task_type", "generic"),
            "payload": payload.get("task_payload", {}),
            "due_time": payload.get("due_time"), # ISO format string
            "status": "pending",
            "created_at": str(datetime.datetime.utcnow())
        }
        self.tasks.append(task)
        self._save_tasks()
        log_event("SchedulerAgent", f"Scheduled task {task_id} due at {task['due_time']}")
        return task_id

    def _check_due_tasks(self):
        now = datetime.datetime.utcnow()
        due = []
        for task in self.tasks:
            if task["status"] == "pending":
                try:
                    due_time = datetime.datetime.fromisoformat(task["due_time"])
                    if now >= due_time:
                        task["status"] = "executed" # Mark as executed for now
                        task["executed_at"] = str(now)
                        due.append(task)
                except ValueError:
                    log_event("SchedulerAgent", f"Invalid date format for task {task['id']}")
        
        if due:
            self._save_tasks()
            log_event("SchedulerAgent", f"Found {len(due)} due tasks")
            
        return due
