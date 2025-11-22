from agents.base_agent import BaseAgent
from utils.logging_utils import log_event
from sentence_transformers import SentenceTransformer
from models.messages import AgentMessage, MessageType
import numpy as np, uuid, datetime
import json

MODEL = None
def _ensure_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return MODEL

class SupervisorAgent(BaseAgent):
    def score_reply_against_kb(self, reply_text, kb_passages):
        model = _ensure_model()
        texts = [reply_text] + [p.get("text","") for p in kb_passages]
        embs = model.encode(texts, convert_to_numpy=True)
        reply_emb = embs[0]
        kb_embs = embs[1:]
        if len(kb_embs)==0:
            return 0.0
        kb_norm = np.linalg.norm(kb_embs, axis=1)
        reply_norm = np.linalg.norm(reply_emb)
        sims = (kb_embs @ reply_emb) / (kb_norm * reply_norm + 1e-12)
        return float(np.max(sims))

    async def receive(self, message: AgentMessage):
        log_event("SupervisorAgent", "Auto-eval incoming payload")
        payload = message.payload.dict() if hasattr(message.payload, "dict") else message.payload
        candidate_reply = payload.get("candidate_reply", "") or payload.get("text","")
        kb = payload.get("kb", [])  # list of passages

        # compute score
        score = self.score_reply_against_kb(candidate_reply, kb)
        log_event("SupervisorAgent", {"supervisor_score": score})

        # if low, instead of directly calling planner, call retryable_agent
        threshold = float(payload.get("threshold", 0.45))
        if score < threshold:
            # build a message that asks retryable_agent to call planner_agent with strict mode
            retry_msg = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="supervisor_agent",
                receiver="retryable_agent",
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload={
                    "agent": "planner_agent",
                    "max_retries": int(payload.get("max_retries", 3)),
                    "validator": payload.get("validator", "non_empty_plan"),
                    "original_payload": {
                        "text": candidate_reply,
                        "kb": kb,
                        "strict": True,
                        "intent": payload.get("intent"),
                        "customer_id": payload.get("customer_id")
                    }
                }
            )
            log_event("SupervisorAgent", {"action":"invoke_retryable","payload_preview": str(retry_msg.payload)[:300]})
            return await self.orchestrator.send_a2a(retry_msg)
        else:
            # OK — forward to ticket agent (keep same behavior)
            route = AgentMessage(
                id=str(uuid.uuid4()),
                session_id=message.session_id,
                sender="supervisor_agent",
                receiver="ticket_agent",
                type=MessageType.TASK_REQUEST,
                timestamp=str(datetime.datetime.utcnow()),
                payload={
                    "intent": payload.get("intent", "general"),
                    "text": candidate_reply,
                    "sentiment_score": payload.get("sentiment_score", 0.0),
                    "kb": kb,
                    "customer_id": payload.get("customer_id")
                }
            )
            return await self.orchestrator.send_a2a(route)

