from models.messages import AgentMessage
import asyncio

class BaseAgent:
    def __init__(self, name, orchestrator):
        self.name = name
        self.orchestrator = orchestrator

    async def receive(self, message: AgentMessage):
        raise NotImplementedError("Subclasses must implement this method.")

