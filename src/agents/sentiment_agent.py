from src.agents.base_agent import BaseAgent
from src.utils.logging_utils import log_event
from src.utils.gemini_utils import analyze_sentiment
from src.utils.metrics import increment
import uuid, datetime

class SentimentAgent(BaseAgent):
    def receive(self, message):
        log_event("SentimentAgent", "Scoring sentiment with Gemini AI")

        payload = message.get("payload", {})
        
        # Handle different payload types from different agents
        if "text" in payload:
            text = payload["text"]
            
            # Use Gemini for advanced sentiment analysis
            sentiment_result = analyze_sentiment(text)
            
            response_payload = {
                "intent": payload.get("intent", "unknown"),
                "text": text,
                "sentiment_score": sentiment_result["sentiment_score"],
                "emotion": sentiment_result["emotion"],
                "intensity": sentiment_result["intensity"],
                "factors": sentiment_result["factors"],
                "original_confidence": payload.get("intent_confidence", 0.0),
                "original_urgency": payload.get("urgency", "unknown")
            }
            try:
                emo = response_payload["emotion"].lower()
                score = response_payload["sentiment_score"]
                negative_emotions = {"frustrated","angry","stressed","furious","sad"}
                is_negative_emotion = any(e in emo for e in negative_emotions)
                accurate = (is_negative_emotion and score < 0) or ((not is_negative_emotion) and score >= 0)
                increment("sentiment_accuracy", 1 if accurate else 0, tags={"session_id": message.get("session_id")})
            except Exception:
                pass
            
        elif "stress" in payload or "call_label" in payload:
            # Handle emotion agent output - combine with text sentiment if available
            stress = payload.get("stress", 0.0)
            
            # If we have text from emotion agent, analyze it too
            if "text" in payload:
                sentiment_result = analyze_sentiment(payload["text"])
                sentiment_score = sentiment_result["sentiment_score"]
                emotion = sentiment_result["emotion"]
            else:
                # Use stress as sentiment indicator
                if stress is not None and stress > 0.5:
                    sentiment_score = -0.8  # High stress = negative sentiment
                    emotion = "stressed"
                else:
                    sentiment_score = 0.2   # Low stress = neutral/positive sentiment
                    emotion = "calm"
            
            response_payload = {
                "intent": "emotion_analysis",
                "stress": stress,
                "call_label": payload.get("call_label"),
                "customer_id": payload.get("customer_id"),
                "sentiment_score": sentiment_score,
                "emotion": emotion,
                "intensity": abs(sentiment_score)
            }
            try:
                emo = response_payload["emotion"].lower()
                score = response_payload["sentiment_score"]
                negative_emotions = {"frustrated","angry","stressed","furious","sad"}
                is_negative_emotion = any(e in emo for e in negative_emotions)
                accurate = (is_negative_emotion and score < 0) or ((not is_negative_emotion) and score >= 0)
                increment("sentiment_accuracy", 1 if accurate else 0, tags={"session_id": message.get("session_id")})
            except Exception:
                pass
        else:
            # Fallback for unknown payload types
            response_payload = {
                "intent": "unknown",
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "intensity": 0.0,
                "factors": ["no_text_available"]
            }

        response = {
            "id": str(uuid.uuid4()),
            "session_id": message["session_id"],
            "sender": "sentiment_agent",
            "receiver": "priority_agent",  # Route to priority agent next
            "type": "task_request",
            "timestamp": str(datetime.datetime.utcnow()),
            "payload": response_payload
        }

        return self.orchestrator.send_a2a(response)
