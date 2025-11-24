import json
import os
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import typing_extensions as typing
from dotenv import load_dotenv

from src.utils.observability.logging_utils import log_event
from src.utils.observability.metrics import record_latency

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model with smart fallback
# Priority: gemini-2.0-flash (fast, paid) -> gemini-1.5-pro (slower, free tier friendly)
model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
try:
    model = genai.GenerativeModel(model_name)
    print(f"✅ Using model: {model_name}")
except Exception as e:
    print(f"⚠️  {model_name} unavailable, falling back to gemini-1.5-pro")
    model_name = "gemini-1.5-pro"
    model = genai.GenerativeModel(model_name)


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


import random

# ... (imports)

def generate_with_retry(prompt: str, schema: Any = None, retries: int = 3, base_delay: float = 1.0) -> Any:
    """
    Helper to call Gemini with retry logic for rate limits.
    Retries: 3 (1s, 2s, 4s) for free tier compatibility.
    """
    for i in range(retries):
        try:
            config = genai.GenerationConfig(
                response_mime_type="application/json", response_schema=schema
            ) if schema else None
            
            return model.generate_content(prompt, generation_config=config)
        except Exception as e:
            error_str = str(e).lower()
            # Handle both rate limits and model not found errors
            if "429" in error_str or "quota" in error_str or "404" in error_str:
                if i < retries - 1:  # Don't sleep on last retry
                    sleep_time = base_delay * (2 ** i) + random.uniform(0, 0.5)
                    print(f"⏳ Rate limit/quota hit. Retrying in {sleep_time:.1f}s... (attempt {i+1}/{retries})")
                    time.sleep(sleep_time)
                    continue
            raise e
    raise Exception("Max retries exceeded for Gemini API")

def classify_intent(text: str) -> Dict[str, Any]:
    """Use Gemini to classify email intent with native structured output."""
    try:
        prompt = f"""
        Analyze this customer email and classify the intent.
        
        Examples:
        - "Where is my order? I placed it 2 weeks ago and tracking hasn't updated." -> intent: shipping_inquiry, urgency: high
        - "I want a full refund immediately. This product is defective." -> intent: refund_request, urgency: high
        - "The app crashes every time I click login. Error code 500." -> intent: technical_support, urgency: high
        - "Please cancel my subscription. I no longer need this service." -> intent: cancellation_request, urgency: high
        - "This is the THIRD time I've contacted you with no response! Unacceptable!" -> intent: complaint, urgency: critical
        - "Does this work with iPhone 15? What are the dimensions?" -> intent: product_question, urgency: low
        - "I can't log into my account. It says invalid credentials but I'm sure they're right." -> intent: account_issue, urgency: high
        - "Thank you so much! Your team resolved my issue in 10 minutes. Excellent service!" -> intent: feedback, urgency: low
        - "What are your return policy timeframes? How many days do I have?" -> intent: general_inquiry, urgency: low
        - "Tracking number TRACK123456 shows delivered but I never received anything!" -> intent: shipping_inquiry, urgency: critical
        - "This doesn't match what you advertised. I want my money back and I'm posting a review." -> intent: refund_request, urgency: high
        - "The product stopped working after 2 days. Can you send a replacement?" -> intent: technical_support, urgency: medium
        - "Cancel order #12345 immediately before it ships!" -> intent: cancellation_request, urgency: critical
        - "I've been waiting 3 weeks for a response. This is terrible customer service." -> intent: complaint, urgency: high
        - "Can I use this outdoors? Is it waterproof?" -> intent: product_question, urgency: low

        Email: "{text}"
        """

        t0 = time.time()
        response = generate_with_retry(prompt, schema=IntentSchema)
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
        
        Examples:
        - "Thank you so much! Your team is absolutely amazing!" -> emotion: grateful, score: 0.95
        - "This is terrible. Worst experience ever." -> emotion: angry, score: -0.90
        - "I expected more based on the reviews. Kinda disappointed." -> emotion: disappointed, score: -0.45
        - "Can you provide tracking information for order #12345?" -> emotion: neutral, score: 0.0
        - "I've contacted you THREE times and STILL no response!" -> emotion: frustrated, score: -0.75
        - "I'm not sure I understand how this works. It's a bit confusing." -> emotion: confused, score: -0.20
        - "I'm worried this won't arrive in time for the wedding. It's really important." -> emotion: anxious, score: -0.40
        - "Happy with the product! Works exactly as described." -> emotion: satisfied, score: 0.80
        - "This is UNACCEPTABLE! I'm filing a complaint with the BBB!" -> emotion: angry, score: -0.98
        - "The app is pretty good but crashes occasionally. Not a huge deal." -> emotion: satisfied, score: 0.30
        - "I've tried everything you suggested and it STILL doesn't work. What now?" -> emotion: frustrated, score: -0.65
        - "Could you explain the return process? I'm a bit lost." -> emotion: confused, score: -0.15
        - "I hope my package arrives soon. Getting nervous about the deadline." -> emotion: anxious, score: -0.35
        - "Absolutely love it! Best purchase I've made all year!" -> emotion: satisfied, score: 0.95
        - "This is the last straw. Canceling everything and never coming back." -> emotion: angry, score: -0.92

        Text: "{text}"
        """

        t0 = time.time()
        response = generate_with_retry(prompt, schema=SentimentSchema)
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
    """Calculate priority score using Gemini."""
    try:
        prompt = f"""
        Calculate the priority score (1-10) for this customer case.
        
        Context:
        {json.dumps(context, indent=2)}
        """
        
        # Simple schema for priority
        class PrioritySchema(typing.TypedDict):
            priority_score: int
            reasoning: str
            time_estimate: int
            escalation_recommended: bool

        t0 = time.time()
        response = generate_with_retry(prompt, schema=PrioritySchema)
        result = json.loads(response.text)
        
        return result

    except Exception as e:
        log_event("GeminiPriorityScorer", f"Error: {e}")
        return {
            "priority_score": 5,
            "reasoning": "Fallback due to error",
            "time_estimate": 24,
            "escalation_recommended": False
        }


def generate_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to generate structured task plans with native structured output."""
    try:
        prompt = f"""
        Create a detailed task plan for this customer service request.
        Request: "{request}"
        Context: {context}
        """

        t0 = time.time()
        response = generate_with_retry(prompt, schema=TaskPlanSchema)
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
