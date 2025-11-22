import google.generativeai as genai
import os, json
import typing_extensions as typing
from typing import Dict, Any, Optional, List
from utils.logging_utils import log_event
from utils.metrics import record_latency
import time

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash")


# Define Schemas for Structured Output
class IntentSchema(typing.TypedDict):
    intent: str
    confidence: float
    urgency: str
    key_phrases: List[str]


class SentimentSchema(typing.TypedDict):
    sentiment_score: float
    emotion: str
    intensity: float
    factors: List[str]


class PrioritySchema(typing.TypedDict):
    priority_score: float
    escalation_recommended: bool
    reasoning: str
    time_estimate: str


class TaskStep(typing.TypedDict):
    step: int
    action: str
    expected_outcome: str


class TaskPlanSchema(typing.TypedDict):
    tasks: List[TaskStep]
    estimated_time: float
    resources_needed: List[str]
    success_criteria: List[str]
    potential_challenges: List[str]


def classify_intent(text: str) -> Dict[str, Any]:
    """Use Gemini to classify email intent with native structured output."""
    try:
        prompt = f"""
        Analyze this customer email and classify the intent.
        Email: "{text}"
        """

        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=IntentSchema
            ),
        )
        result = json.loads(response.text)
        record_latency(
            "model_inference_latency_ms",
            (time.time() - t0) * 1000.0,
            tags={"model": "gemini", "fn": "classify_intent"},
        )

        log_event(
            "GeminiIntentClassifier",
            {
                "intent": result.get("intent"),
                "confidence": result.get("confidence"),
                "urgency": result.get("urgency"),
            },
        )

        return result

    except Exception as e:
        log_event("GeminiIntentClassifier", f"Error: {e}")
        return fallback_intent_classification(text)


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Use Gemini for advanced sentiment analysis with native structured output."""
    try:
        prompt = f"""
        Analyze the sentiment of this customer text.
        Text: "{text}"
        """

        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=SentimentSchema
            ),
        )
        result = json.loads(response.text)

        log_event(
            "GeminiSentimentAnalyzer",
            {
                "sentiment_score": result.get("sentiment_score"),
                "emotion": result.get("emotion"),
                "intensity": result.get("intensity"),
            },
        )

        return result

    except Exception as e:
        log_event("GeminiSentimentAnalyzer", f"Error: {e}")
        return fallback_sentiment_analysis(text)


def calculate_priority_score(context: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to calculate escalation priority with native structured output."""
    try:
        prompt = f"""
        Calculate escalation priority for this customer service case.
        Context: {context}
        """

        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=PrioritySchema
            ),
        )
        result = json.loads(response.text)

        log_event(
            "GeminiPriorityCalculator",
            {
                "priority_score": result.get("priority_score"),
                "escalation_recommended": result.get("escalation_recommended"),
            },
        )

        return result

    except Exception as e:
        log_event("GeminiPriorityCalculator", f"Error: {e}")
        return fallback_priority_calculation(context)


def generate_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to generate structured task plans with native structured output."""
    try:
        prompt = f"""
        Create a detailed task plan for this customer service request.
        Request: "{request}"
        Context: {context}
        """

        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=TaskPlanSchema
            ),
        )
        result = json.loads(response.text)
        record_latency(
            "model_inference_latency_ms",
            (time.time() - t0) * 1000.0,
            tags={"model": "gemini", "fn": "generate_task_plan"},
        )

        log_event(
            "GeminiTaskPlanner",
            {
                "task_count": len(result.get("tasks", [])),
                "estimated_time": result.get("estimated_time"),
            },
        )

        return result

    except Exception as e:
        log_event("GeminiTaskPlanner", f"Error: {e}")
        return fallback_task_plan(request, context)


# Fallback functions for when Gemini is unavailable
def fallback_intent_classification(text: str) -> Dict[str, Any]:
    """Rule-based intent classification fallback."""
    text_lower = text.lower()

    if any(word in text_lower for word in ["not received", "missing", "lost"]):
        return {
            "intent": "shipping_inquiry",
            "confidence": 0.8,
            "urgency": "high",
            "key_phrases": ["not received"],
        }
    elif any(word in text_lower for word in ["refund", "money back", "return"]):
        return {
            "intent": "refund_request",
            "confidence": 0.9,
            "urgency": "medium",
            "key_phrases": ["refund"],
        }
    elif any(word in text_lower for word in ["angry", "frustrated", "terrible", "worst"]):
        return {
            "intent": "complaint",
            "confidence": 0.85,
            "urgency": "high",
            "key_phrases": ["angry"],
        }
    elif any(word in text_lower for word in ["cancel", "stop", "unsubscribe"]):
        return {
            "intent": "cancellation",
            "confidence": 0.9,
            "urgency": "medium",
            "key_phrases": ["cancel"],
        }
    elif any(word in text_lower for word in ["not working", "broken", "error", "issue"]):
        return {
            "intent": "technical_support",
            "confidence": 0.8,
            "urgency": "medium",
            "key_phrases": ["not working"],
        }
    else:
        return {"intent": "general_query", "confidence": 0.7, "urgency": "low", "key_phrases": []}


def fallback_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis fallback."""
    text_lower = text.lower()

    negative_words = [
        "angry",
        "frustrated",
        "terrible",
        "worst",
        "awful",
        "horrible",
        "disappointed",
        "furious",
    ]
    positive_words = ["happy", "satisfied", "great", "excellent", "good", "pleased"]

    negative_count = sum(1 for word in negative_words if word in text_lower)
    positive_count = sum(1 for word in positive_words if word in text_lower)

    if negative_count > positive_count:
        return {
            "sentiment_score": -0.6,
            "emotion": "frustrated",
            "intensity": 0.7,
            "factors": ["negative language"],
        }
    elif positive_count > negative_count:
        return {
            "sentiment_score": 0.6,
            "emotion": "satisfied",
            "intensity": 0.5,
            "factors": ["positive language"],
        }
    else:
        return {"sentiment_score": 0.0, "emotion": "neutral", "intensity": 0.3, "factors": []}


def fallback_priority_calculation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based priority calculation fallback."""
    score = 0.5  # Base score

    if context.get("sentiment_score", 0) < -0.5:
        score += 0.3
    if context.get("intent") == "complaint":
        score += 0.2
    if context.get("stress", 0) > 0.7:
        score += 0.2
    if context.get("customer_tier") == "VIP":
        score += 0.1

    return {
        "priority_score": min(score, 1.0),
        "escalation_recommended": score > 0.7,
        "reasoning": "Rule-based calculation",
        "time_estimate": "2-4h" if score > 0.7 else "4-24h",
    }


def fallback_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Basic task plan generation fallback."""
    return {
        "tasks": [
            {
                "step": 1,
                "action": "Acknowledge customer request",
                "expected_outcome": "Customer notified",
            },
            {"step": 2, "action": "Investigate issue", "expected_outcome": "Root cause identified"},
            {"step": 3, "action": "Provide resolution", "expected_outcome": "Issue resolved"},
        ],
        "estimated_time": 2,
        "resources_needed": ["customer_service"],
        "success_criteria": ["customer_satisfied"],
        "potential_challenges": ["complex_issue"],
    }
