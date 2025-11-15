import datetime
import uuid
from src.utils.logging_utils import log_event

class Orchestrator:
    def __init__(self):
        self.agents = {}  # agents are registered here

    def register_agent(self, name, agent):
        self.agents[name] = agent

    def route(self, message: dict):
        receiver = message.get("receiver")

        if receiver not in self.agents:
            raise ValueError(f"Unknown agent: {receiver}")

        log_event("orchestrator", f"Routing -> {receiver}")
        return self.agents[receiver].receive(message)

    def new_message(self, sender, receiver, payload, msg_type="task_request"):
        return {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "sender": sender,
            "receiver": receiver,
            "type": msg_type,
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": payload,
        }

