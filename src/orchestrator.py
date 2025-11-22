import asyncio
from typing import Dict, Any, Union
from src.agents.base_agent import BaseAgent
from src.models.messages import AgentMessage, MessageType
from src.utils.tracing import tracer
from src.utils.agent_controller import agent_controller
from src.config import config
import uuid
import datetime

class Orchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.controller = agent_controller

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    async def route(self, message: AgentMessage) -> Union[Dict[str, Any], AgentMessage]:
        if message.receiver in self.agents:
            # Check if agent is paused
            if self.controller.is_agent_paused(message.receiver):
                # Queue the message instead of delivering
                self.controller.queue_message(message.receiver, message)
                
                if config.enable_tracing:
                    tracer.log(message.trace_id, "queued", message.sender, message.receiver, 
                              {"reason": "agent_paused"})
                
                return {
                    "status": "queued",
                    "message": f"Agent {message.receiver} is paused. Message queued.",
                    "agent": message.receiver,
                    "queue_size": len(self.controller.message_queues.get(message.receiver, []))
                }
            
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
    
    def pause_agent(self, agent_name: str) -> Dict[str, Any]:
        """Pause an agent - messages will be queued"""
        return self.controller.pause_agent(agent_name)
    
    async def resume_agent(self, agent_name: str) -> Dict[str, Any]:
        """Resume a paused agent and deliver queued messages"""
        result = self.controller.resume_agent(agent_name)
        
        # Deliver queued messages
        if result["success"] and result["queued_messages"]:
            for queued_msg in result["queued_messages"]:
                try:
                    await self.route(queued_msg)
                except Exception as e:
                    if config.enable_tracing:
                        tracer.log(queued_msg.trace_id, "error", "orchestrator", queued_msg.receiver, 
                                 f"Error delivering queued message: {str(e)}")
        
        return result
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent"""
        return self.controller.get_agent_status(agent_name)
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tracked agents"""
        return self.controller.get_all_statuses()
