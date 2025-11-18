import datetime
import uuid
from src.utils.logging_utils import log_event
from src.a2a_router import send_message

class Orchestrator:
    def __init__(self):
        self.agents = {}  # name -> agent instance

    def register_agent(self, name, agent):
        self.agents[name] = agent

    def route(self, message: dict):
        """
        Internal routing called by send_message (A2A router) or directly.
        This delivers the message to the target agent after logging.
        """
        receiver = message.get("receiver")
        log_event("orchestrator_route", {"to": receiver, "msg_id": message.get("id")})
        if receiver not in self.agents:
            raise ValueError(f"Unknown agent: {receiver}")

        # pass message to agent
        return self.agents[receiver].receive(message)

    def new_message(self, sender, receiver, payload, msg_type="task_request", session_id=None):
        return {
            "id": str(uuid.uuid4()),
            "session_id": session_id if session_id is not None else str(uuid.uuid4()),
            "sender": sender,
            "receiver": receiver,
            "type": msg_type,
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": payload,
        }

    def send_a2a(self, message: dict):
        """
        Public helper that uses the A2A router (validation + routing).
        Agents should ideally call orchestrator.send_a2a(msg) instead of orchestrator.route(msg)
        """
        # This delegates to a2a_router which validates and mutates message
        return send_message(self, message)
