"""
Agent Controller - Centralized agent lifecycle management
Handles pause/resume operations and message queueing
"""

from typing import Dict, List, Optional, Any
from collections import deque
from utils.logging_utils import log_event


class AgentController:
    """
    Manages agent lifecycle states and message queueing
    """

    def __init__(self):
        """Initialize the agent controller"""
        self.paused_agents = set()  # Set of paused agent names
        self.message_queues = {}  # agent_name -> deque of messages
        self.agent_stats = {}  # agent_name -> stats dict

        log_event("AgentController", {"event": "initialized"})

    def pause_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Pause an agent - it will stop processing messages

        Args:
            agent_name: Name of the agent to pause

        Returns:
            Operation result
        """
        if agent_name in self.paused_agents:
            log_event(
                "AgentController", {"event": "pause_agent_already_paused", "agent": agent_name}
            )
            return {
                "success": False,
                "message": f"Agent {agent_name} is already paused",
                "agent": agent_name,
                "status": "paused",
            }

        self.paused_agents.add(agent_name)

        # Initialize message queue if not exists
        if agent_name not in self.message_queues:
            self.message_queues[agent_name] = deque()

        # Initialize stats
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {
                "paused_count": 0,
                "resumed_count": 0,
                "messages_queued": 0,
                "messages_delivered": 0,
            }

        self.agent_stats[agent_name]["paused_count"] += 1

        log_event(
            "AgentController",
            {
                "event": "agent_paused",
                "agent": agent_name,
                "queue_size": len(self.message_queues[agent_name]),
            },
        )

        return {
            "success": True,
            "message": f"Agent {agent_name} has been paused",
            "agent": agent_name,
            "status": "paused",
            "queued_messages": len(self.message_queues[agent_name]),
        }

    def resume_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Resume a paused agent and return queued messages

        Args:
            agent_name: Name of the agent to resume

        Returns:
            Operation result with queued messages
        """
        if agent_name not in self.paused_agents:
            log_event("AgentController", {"event": "resume_agent_not_paused", "agent": agent_name})
            return {
                "success": False,
                "message": f"Agent {agent_name} is not paused",
                "agent": agent_name,
                "status": "active",
                "queued_messages": [],
            }

        self.paused_agents.remove(agent_name)

        # Get queued messages
        queued_messages = []
        if agent_name in self.message_queues:
            queued_messages = list(self.message_queues[agent_name])
            self.message_queues[agent_name].clear()

        # Update stats
        if agent_name in self.agent_stats:
            self.agent_stats[agent_name]["resumed_count"] += 1
            self.agent_stats[agent_name]["messages_delivered"] += len(queued_messages)

        log_event(
            "AgentController",
            {
                "event": "agent_resumed",
                "agent": agent_name,
                "messages_to_deliver": len(queued_messages),
            },
        )

        return {
            "success": True,
            "message": f"Agent {agent_name} has been resumed",
            "agent": agent_name,
            "status": "active",
            "queued_messages": queued_messages,
            "delivered_count": len(queued_messages),
        }

    def is_agent_paused(self, agent_name: str) -> bool:
        """
        Check if an agent is paused

        Args:
            agent_name: Name of the agent

        Returns:
            True if paused, False otherwise
        """
        return agent_name in self.paused_agents

    def queue_message(self, agent_name: str, message: Any) -> Dict[str, Any]:
        """
        Queue a message for a paused agent

        Args:
            agent_name: Name of the agent
            message: Message to queue

        Returns:
            Operation result
        """
        if agent_name not in self.message_queues:
            self.message_queues[agent_name] = deque()

        self.message_queues[agent_name].append(message)

        # Update stats
        if agent_name in self.agent_stats:
            self.agent_stats[agent_name]["messages_queued"] += 1

        log_event(
            "AgentController",
            {
                "event": "message_queued",
                "agent": agent_name,
                "queue_size": len(self.message_queues[agent_name]),
            },
        )

        return {
            "success": True,
            "message": f"Message queued for {agent_name}",
            "agent": agent_name,
            "queue_size": len(self.message_queues[agent_name]),
        }

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get the status of an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Agent status information
        """
        is_paused = agent_name in self.paused_agents
        queue_size = len(self.message_queues.get(agent_name, []))
        stats = self.agent_stats.get(agent_name, {})

        return {
            "agent": agent_name,
            "status": "paused" if is_paused else "active",
            "is_paused": is_paused,
            "queued_messages": queue_size,
            "stats": stats,
        }

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all agents being tracked

        Returns:
            Dictionary of agent statuses
        """
        all_agents = (
            set(self.paused_agents) | set(self.message_queues.keys()) | set(self.agent_stats.keys())
        )

        return {agent: self.get_agent_status(agent) for agent in all_agents}

    def clear_queue(self, agent_name: str) -> Dict[str, Any]:
        """
        Clear the message queue for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Operation result
        """
        cleared_count = 0
        if agent_name in self.message_queues:
            cleared_count = len(self.message_queues[agent_name])
            self.message_queues[agent_name].clear()

        log_event(
            "AgentController",
            {"event": "queue_cleared", "agent": agent_name, "cleared_count": cleared_count},
        )

        return {
            "success": True,
            "message": f"Cleared {cleared_count} messages from {agent_name} queue",
            "agent": agent_name,
            "cleared_count": cleared_count,
        }


# Global instance
agent_controller = AgentController()
