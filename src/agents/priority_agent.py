# src/agents/priority_agent.py
from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.gemini_utils import calculate_priority_score
import uuid, datetime

class PriorityAgent(BaseAgent):
    """
    Intelligent priority agent using Gemini AI for escalation decisions.
    Analyzes multiple factors: sentiment, stress, intent, customer history, and urgency.
    """

    def receive(self, message):
        log_event("PriorityAgent", "Deciding priority with Gemini AI")
        payload = message.get("payload", {}) or {}
        
        # Build comprehensive context for Gemini analysis
        context = {
            "sentiment_score": payload.get("sentiment_score", 0.0),
            "stress": payload.get("stress", 0.0),
            "emotion": payload.get("emotion", "neutral"),
            "intensity": payload.get("intensity", 0.0),
            "intent": payload.get("intent", "unknown"),
            "customer_id": payload.get("customer_id"),
            "urgency": payload.get("urgency", "medium"),
            "intent_confidence": payload.get("intent_confidence", 0.0),
            "key_phrases": payload.get("key_phrases", []),
            "factors": payload.get("factors", [])
        }
        
        # Use Gemini for intelligent priority calculation
        priority_result = calculate_priority_score(context)
        
        escalate = priority_result["escalation_recommended"]
        reasons = [priority_result["reasoning"]]

        if escalate:
            # route to action_executor_agent for automated workflow execution
            out = {
                "id": str(uuid.uuid4()),
                "session_id": message.get("session_id"),
                "sender": "priority_agent",
                "receiver": "action_executor_agent",  # Use action executor for automation
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "plan": {
                        "tasks": [
                            {"step": 1, "action": "escalate_to_human", "expected_outcome": "Human support assigned", "detail": "Escalate complex issue to human agent"},
                            {"step": 2, "action": "schedule_followup", "expected_outcome": "Follow-up scheduled", "detail": "Schedule high-priority follow-up"}
                        ],
                        "estimated_time": 1,
                        "resources_needed": ["human_agent"],
                        "success_criteria": ["human_assigned", "customer_contacted"],
                        "potential_challenges": ["agent_availability"]
                    },
                    "priority_score": priority_result["priority_score"],
                    "time_estimate": priority_result["time_estimate"],
                    "original_payload": {
                        "text": payload.get("text") or payload.get("summary"),
                        "kb": payload.get("kb"),
                        "strict": True,
                        "intent": payload.get("intent"),
                        "customer_id": context["customer_id"],
                        "reason": reasons,
                        "emotion": context["emotion"],
                        "intensity": context["intensity"],
                        "key_phrases": context["key_phrases"],
                        "escalation_reason": priority_result["reasoning"]
                    }
                }
            }
            log_event("PriorityAgent", {
                "escalate": True, 
                "priority_score": priority_result["priority_score"],
                "reasoning": priority_result["reasoning"],
                "time_estimate": priority_result["time_estimate"]
            })
            return self.orchestrator.send_a2a(out)
        else:
            # route to ticket_agent normally
            out = {
                "id": str(uuid.uuid4()),
                "session_id": message.get("session_id"),
                "sender": "priority_agent",
                "receiver": "ticket_agent",
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "intent": payload.get("intent"),
                    "text": payload.get("text") or payload.get("summary"),
                    "sentiment_score": context["sentiment_score"],
                    "stress": context["stress"],
                    "customer_id": context["customer_id"],
                    "priority_score": priority_result["priority_score"],
                    "emotion": context["emotion"],
                    "time_estimate": priority_result["time_estimate"],
                    "key_phrases": context["key_phrases"],  # Preserve key_phrases for tagging
                    "factors": context["factors"]  # Preserve factors for context
                }
            }
            log_event("PriorityAgent", {
                "escalate": False,
                "priority_score": priority_result["priority_score"],
                "route": "ticket_agent"
            })
            return self.orchestrator.send_a2a(out)

