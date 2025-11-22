import asyncio

from models.messages import AgentMessage


class BaseAgent:
    def __init__(self, name, orchestrator):
        self.name = name
        self.orchestrator = orchestrator

    async def receive(self, message: AgentMessage):
        raise NotImplementedError("Subclasses must implement this method.")
