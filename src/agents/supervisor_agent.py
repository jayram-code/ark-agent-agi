from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from sentence_transformers import SentenceTransformer
import numpy as np, uuid, datetime

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
        # cosine between reply and top passage
        reply_emb = embs[0]
        kb_embs = embs[1:]
        if len(kb_embs)==0:
            return 0.0
        # compute cosine similarities
        kb_norm = np.linalg.norm(kb_embs, axis=1)
        reply_norm = np.linalg.norm(reply_emb)
        sims = (kb_embs @ reply_emb) / (kb_norm * reply_norm + 1e-12)
        return float(np.max(sims))

    def receive(self, message):
        log_event("SupervisorAgent", "Auto-eval incoming payload")
        payload = message.get("payload", {})
        candidate_reply = payload.get("candidate_reply", "")
        kb = payload.get("kb", [])  # list of passages
        # compute score
        score = self.score_reply_against_kb(candidate_reply, kb)
        log_event("SupervisorAgent", {"supervisor_score": score})
        # threshold logic
        if score < 0.45:
            # ask planner to re-run with strict flag
            route = {
                "id": str(uuid.uuid4()),
                "session_id": message["session_id"],
                "sender": "supervisor_agent",
                "receiver": "planner_agent",
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "original": payload,
                    "strict": True,
                    "reason": "low_supervisor_score"
                }
            }
            return self.orchestrator.send_a2a(route)
        else:
            # ok, forward to ticket agent or human-in-loop
            route = {
                "id": str(uuid.uuid4()),
                "session_id": message["session_id"],
                "sender": "supervisor_agent",
                "receiver": "ticket_agent",
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "intent": payload.get("original", {}).get("intent", "general"),
                    "text": candidate_reply,
                    "sentiment_score": payload.get("original", {}).get("sentiment_score", 0.0)
                }
            }
            return self.orchestrator.send_a2a(route)
