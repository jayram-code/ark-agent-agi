# src/agents/emotion_agent.py
from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
import joblib, os, uuid, datetime
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
STRESS_MODEL_PATH = os.path.join(MODEL_DIR, "stress_model.joblib")
CALL_MODEL_PATH = os.path.join(MODEL_DIR, "call_model.joblib")

def _load_model(path):
    try:
        return joblib.load(path)
    except Exception:
        return None

class EmotionAgent(BaseAgent):
    """
    Predicts stress and call_label when 'audio_features' present in payload.
    If audio_features missing or models not found, returns None and lets SentimentAgent/Gemini handle.
    """

    def __init__(self, name, orchestrator):
        super().__init__(name, orchestrator)
        self.stress_model = _load_model(STRESS_MODEL_PATH)
        self.call_model = _load_model(CALL_MODEL_PATH)

    def receive(self, message):
        log_event("EmotionAgent", "Receive payload for emotion inference")
        payload = message.get("payload", {}) or {}
        features = payload.get("audio_features")
        customer_id = payload.get("customer_id")
        # if no numeric features, return neutral fallback
        if not features or not isinstance(features, dict):
            log_event("EmotionAgent", "No audio_features provided — skipping model inference")
            return {
                "id": str(uuid.uuid4()),
                "session_id": message.get("session_id"),
                "sender": "emotion_agent",
                "receiver": payload.get("next", "sentiment_agent"),
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {
                    "stress": None,
                    "call_label": None,
                    "note": "no_audio_features"
                }
            }

        # prepare vector: ensure ordering consistent with training (simple: sort keys)
        try:
            keys = sorted(features.keys())
            x = np.array([features[k] for k in keys], dtype=float).reshape(1, -1)
        except Exception as e:
            log_event("EmotionAgent", f"Feature parse error: {e}")
            return {
                "id": str(uuid.uuid4()),
                "session_id": message.get("session_id"),
                "sender": "emotion_agent",
                "receiver": payload.get("next", "sentiment_agent"),
                "type": "task_request",
                "timestamp": str(datetime.datetime.utcnow()),
                "payload": {"stress": None, "call_label": None, "note":"feature_parse_error"}
            }

        stress = None
        call_label = None
        if self.stress_model:
            try:
                stress = float(self.stress_model.predict(x)[0])
            except Exception as e:
                log_event("EmotionAgent", f"Stress predict error: {e}")
        if self.call_model:
            try:
                call_label = int(self.call_model.predict(x)[0])
            except Exception as e:
                log_event("EmotionAgent", f"Call_label predict error: {e}")

        log_event("EmotionAgentDebug", {
            "predicted_stress": stress,
            "predicted_call_label": call_label
        })

        out = {
            "id": str(uuid.uuid4()),
            "session_id": message.get("session_id"),
            "sender": "emotion_agent",
            "receiver": payload.get("next", "sentiment_agent"),
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": {
                "stress": stress,
                "call_label": call_label,
                "customer_id": customer_id
            }
        }
        return self.orchestrator.send_a2a(out)

