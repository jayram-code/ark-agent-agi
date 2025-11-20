import asyncio
from typing import Dict, Any, Union
from agents.base_agent import BaseAgent
from models.messages import AgentMessage, MessageType
from utils.tracing import tracer
from config import config
import uuid
import datetime

class Orchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    async def route(self, message: AgentMessage) -> Union[Dict[str, Any], AgentMessage]:
        if message.receiver in self.agents:
            # Log the routing event
            if config.enable_tracing:
                tracer.log(message.trace_id, "route", message.sender, message.receiver, message.payload)
            
            response = await self.agents[message.receiver].receive(message)
            return response
        else:
            error_msg = f"Unknown agent: {message.receiver}"
            if config.enable_tracing:
                tracer.log(message.trace_id, "error", "orchestrator", message.sender, error_msg)
            raise ValueError(error_msg)

    async def send_a2a(self, message: AgentMessage) -> Union[Dict[str, Any], AgentMessage]:
        """Send an Agent-to-Agent message via the orchestrator."""
        # Ensure trace_id exists
        if not message.trace_id:
            message.trace_id = message.id
            
        if config.enable_tracing:
            tracer.log(message.trace_id, "send_a2a", message.sender, message.receiver, message.payload)
            
        return await self.route(message)
        
    async def broadcast(self, message: AgentMessage, receivers: list[str]) -> Dict[str, Any]:
        """Send a message to multiple agents in parallel."""
        tasks = []
        for receiver in receivers:
            # Create a copy of the message for each receiver
            msg_copy = message.copy(update={"receiver": receiver})
            tasks.append(self.send_a2a(msg_copy))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(receivers, results))

    def new_message(self, sender: str, receiver: str, type: MessageType, payload: Dict[str, Any], session_id: str = "global") -> AgentMessage:
        return AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender=sender,
            receiver=receiver,
            type=type,
            timestamp=str(datetime.datetime.utcnow()),
            payload=payload
        )
