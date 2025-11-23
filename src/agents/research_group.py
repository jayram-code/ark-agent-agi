import asyncio
import datetime
import uuid

from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from core.orchestrator import Orchestrator
from utils.observability.logging_utils import log_event


class ResearchGroupAgent(BaseAgent):
    """
    A composite agent that manages a group of sub-agents (simulated)
    to perform parallel research tasks.
    """

    def __init__(self, name: str, orchestrator: Orchestrator):
        super().__init__(name, orchestrator)

    async def receive(self, message: AgentMessage):
        query = message.payload.get("query", "")

        # Simulate parallel sub-tasks
        tasks = [
            self.perform_web_search(query),
            self.perform_doc_search(query),
            self.perform_expert_consult(query),
        ]

        # Fan-out / Fan-in
        results = await asyncio.gather(*tasks)

        combined_result = {
            "web": results[0],
            "docs": results[1],
            "expert": results[2],
            "synthesis": "Combined insights from all sources.",
        }

        return combined_result

    async def perform_web_search(self, query):
        await asyncio.sleep(0.2)
        return f"Web results for {query}"

    async def perform_doc_search(self, query):
        await asyncio.sleep(0.15)
        return f"Doc results for {query}"

    async def perform_expert_consult(self, query):
        await asyncio.sleep(0.3)
        return f"Expert opinion on {query}"
