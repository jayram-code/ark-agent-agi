import asyncio
import datetime
import time
import uuid
from typing import Any, Dict, Union

from src.agents.base_agent import BaseAgent
from src.config import config
from src.models.messages import AgentMessage, MessageType
from src.utils.agent_controller import agent_controller
from src.utils.observability.tracing import tracer
from src.utils.observability.metrics import metrics_collector
from src.utils.observability.session_logger import session_logger

from src.policies.routing_policy import RoutingPolicy

class Orchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.controller = agent_controller
        self.routing_policy = RoutingPolicy()

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    async def route(self, message: AgentMessage) -> Union[Dict[str, Any], AgentMessage]:
        """
        Route a message to the appropriate agent.
        
        Logic:
        1. Consult RoutingPolicy to determine target agent (if 'auto').
        2. Check if target agent is paused (via AgentController).
           - If paused, queue message and return 'queued' status.
        3. If active, deliver message via agent.receive().
        4. Track metrics (latency, success/fail) and log trace.
        
        Args:
            message: The AgentMessage to route.
            
        Returns:
            Response from the agent or queue status.
        """
        # Determine receiver using routing policy if not explicit
        target_agent = self.routing_policy.determine_receiver(message)
        
        # Update message receiver if it changed (e.g. was "auto")
        if target_agent != message.receiver:
            message.receiver = target_agent
            if config.enable_tracing:
                 tracer.log(
                    message.trace_id,
                    "routing_decision",
                    "orchestrator",
                    target_agent,
                    {"reason": "policy_match", "original_receiver": "auto"},
                )

        if target_agent in self.agents:
            # Check if agent is paused
            if self.controller.is_agent_paused(target_agent):
                # Queue the message instead of delivering
                self.controller.queue_message(target_agent, message)

                if config.enable_tracing:
                    tracer.log(
                        message.trace_id,
                        "queued",
                        message.sender,
                        target_agent,
                        {"reason": "agent_paused"},
                    )

                return {
                    "status": "queued",
                    "message": f"Agent {target_agent} is paused. Message queued.",
                    "agent": target_agent,
                    "queue_size": len(self.controller.message_queues.get(target_agent, [])),
                }

            # Log the routing event
            if config.enable_tracing:
                tracer.log(
                    message.trace_id, "route", message.sender, target_agent, message.payload
                )

            # Track metrics
            start_time = time.time()
            success = False
            error = None
            
            try:
                response = await self.agents[target_agent].receive(message)
                success = True
                return response
            except Exception as e:
                error = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                metrics_collector.record_message(
                    agent_name=target_agent,
                    latency_ms=latency_ms,
                    success=success,
                    tokens_used=0,  # TODO: Track actual token usage
                    error=error
                )
        else:
            error_msg = f"Unknown agent: {message.receiver}"
            if config.enable_tracing:
                tracer.log(message.trace_id, "error", "orchestrator", message.sender, error_msg)
            raise ValueError(error_msg)

    async def send_a2a(self, message: AgentMessage) -> Union[Dict[str, Any], AgentMessage]:
        """
        Send an Agent-to-Agent message via the orchestrator.
        Ensures trace propagation and session logging.
        """
        # Ensure trace_id exists
        if not message.trace_id:
            message.trace_id = message.id

        # Log to session
        if message.session_id:
            session_logger.log_message(message.session_id, message.dict())

        if config.enable_tracing:
            tracer.log(
                message.trace_id, "send_a2a", message.sender, message.receiver, message.payload
            )

        return await self.route(message)

    async def broadcast(self, message: AgentMessage, receivers: list[str]) -> Dict[str, Any]:
        """
        Send a message to multiple agents in parallel.
        Useful for announcements or multi-agent coordination.
        """
        tasks = []
        for receiver in receivers:
            # Create a copy of the message for each receiver
            msg_copy = message.copy(update={"receiver": receiver})
            tasks.append(self.send_a2a(msg_copy))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(receivers, results))

    def new_message(
        self,
        sender: str,
        receiver: str,
        type: MessageType,
        payload: Dict[str, Any],
        session_id: str = "global",
    ) -> AgentMessage:
        return AgentMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender=sender,
            receiver=receiver,
            type=type,
            timestamp=str(datetime.datetime.utcnow()),
            payload=payload,
        )

    def pause_agent(self, agent_name: str) -> Dict[str, Any]:
        """Pause an agent - messages will be queued"""
        return self.controller.pause_agent(agent_name)  # type: ignore[no-any-return]

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
                        tracer.log(
                            queued_msg.trace_id,
                            "error",
                            "orchestrator",
                            queued_msg.receiver,
                            f"Error delivering queued message: {str(e)}",
                        )

        return result  # type: ignore[no-any-return]

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent"""
        return self.controller.get_agent_status(agent_name)  # type: ignore[no-any-return]

    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tracked agents"""
        return self.controller.get_all_statuses()  # type: ignore[no-any-return]
