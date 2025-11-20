# src/agents/priority_agent.py
from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.gemini_utils import calculate_priority_score
from src.utils.metrics import gauge
from src.services.session_service import SESSION
from src.models.messages import AgentMessage, MessageType
import uuid, datetime

class PriorityAgent(BaseAgent):
    """
    Intelligent priority agent using Gemini AI for escalation decisions.
    Analyzes multiple factors: sentiment, stress, intent, customer history, and urgency.
    """

    async def receive(self, message: AgentMessage):
        log_event("PriorityAgent", "Deciding priority with Gemini AI")
        
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        
        result = await self._analyze(payload, message.session_id)
        
        if message.type == MessageType.QUERY:
            return result
            
        # Legacy routing logic
        escalate = result.get("escalation_recommended", False)
        
        if escalate:
            # route to action_executor_agent for automated workflow execution
            out = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="priority_agent",
                receiver="action_executor_agent",  # Use action executor for automation
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload={
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
                    "priority_score": result["priority_score"],
                    "time_estimate": result["time_estimate"],
                    "original_payload": {
                        "text": payload.get("text") or payload.get("summary"),
                        "kb": payload.get("kb"),
                        "strict": True,
                        "intent": payload.get("intent"),
                        "customer_id": payload.get("customer_id"),
                        "reason": [result["reasoning"]],
                        "emotion": payload.get("emotion"),
                        "intensity": payload.get("intensity"),
                        "key_phrases": payload.get("key_phrases"),
                        "escalation_reason": result["reasoning"]
                    }
                }
            )
            log_event("PriorityAgent", {
                "escalate": True, 
                "priority_score": result["priority_score"],
                "reasoning": result["reasoning"],
                "time_estimate": result["time_estimate"]
            })
            return await self.orchestrator.send_a2a(out)
        else:
            # route to ticket_agent normally
            out = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="priority_agent",
                receiver="ticket_agent",
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload={
                    "intent": payload.get("intent"),
                    "text": payload.get("text") or payload.get("summary"),
                    "sentiment_score": payload.get("sentiment_score", 0.0),
                    "stress": payload.get("stress", 0.0),
                    "customer_id": payload.get("customer_id"),
                    "priority_score": result["priority_score"],
                    "emotion": payload.get("emotion"),
                    "time_estimate": result["time_estimate"],
                    "key_phrases": payload.get("key_phrases"),  # Preserve key_phrases for tagging
                    "factors": payload.get("factors")  # Preserve factors for context
                }
            )
            log_event("PriorityAgent", {
                "escalate": False,
                "priority_score": result["priority_score"],
                "route": "ticket_agent"
            })
            return await self.orchestrator.send_a2a(out)

    async def _analyze(self, payload, session_id):
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
        
        # priority consistency metric (rolling std dev over customer history)
        try:
            cid = context.get("customer_id")
            if cid:
                hist = SESSION.get_customer(cid)["priorities"]
                if hist:
                    mean = sum(hist)/len(hist)
                    var = sum((p-mean)**2 for p in hist)/len(hist)
                    std = var ** 0.5
                    gauge("priority_scoring_consistency_std", std, tags={"customer_id": cid})
        except Exception:
            pass
            
        return priority_result

