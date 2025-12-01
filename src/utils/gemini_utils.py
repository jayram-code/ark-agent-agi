import json
import os
import time
import random
from typing import Any, Dict, List, Optional
import typing_extensions as typing

import google.generativeai as genai
from dotenv import load_dotenv
from src.utils.resilience.circuit_breaker import CircuitBreaker

from src.utils.observability.logging_utils import log_event
from src.utils.observability.metrics import record_latency

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model with smart fallback
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
try:
    model = genai.GenerativeModel(model_name)
    print(f"Using model: {model_name}")
except Exception as e:
    print(f"{model_name} unavailable, falling back to gemini-1.5-pro")
    model_name = "gemini-1.5-pro"
    model = genai.GenerativeModel(model_name)

# Circuit breaker to avoid repeated quota hammering
CB = CircuitBreaker(
    failure_threshold=int(os.getenv("GEMINI_CB_THRESHOLD", "5")),
    timeout=int(os.getenv("GEMINI_CB_TIMEOUT", "60")),
    expected_exception=Exception,
)

# Define Schema for Structured Output
class CombinedAnalysisSchema(typing.TypedDict):
    intent: str
    confidence: float
    urgency: str
    sentiment_score: float
    emotion: str
    rationale: str
    key_phrases: List[str]

class PriorityScoreSchema(typing.TypedDict):
    priority_score: int
    reasoning: str
    time_estimate: int
    escalation_recommended: bool

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
            
            return CB.call(model.generate_content, prompt, generation_config=config)
        except Exception as e:
            error_str = str(e).lower()
            # Handle both rate limits and model not found errors
            if "429" in error_str or "quota" in error_str or "404" in error_str:
                if i < retries - 1:  # Don't sleep on last retry
                    sleep_time = base_delay * (2 ** i) + random.uniform(0, 0.5)
                    print(f"⏳ Rate limit/quota hit. Retrying in {sleep_time:.1f}s... (attempt {i+1}/{retries})")
                    time.sleep(sleep_time)
                    continue
                else:
                    # On last retry, fall back immediately
                    raise RuntimeError("Rate limited - fallback engaged")
            raise e
    raise Exception("Max retries exceeded for Gemini API")

def analyze_email_combined(text: str) -> Dict[str, Any]:
    """Combined intent + sentiment analysis in ONE API call for speed."""
    try:
        prompt = f"""
        Analyze this email and provide a JSON response with:
        - intent (string): The primary goal (e.g., shipping_inquiry, refund_request, complaint)
        - confidence (float): 0.0 to 1.0
        - urgency (string): low, medium, high, critical
        - sentiment_score (float): -1.0 (negative) to 1.0 (positive)
        - emotion (string): e.g., happy, angry, frustrated
        - rationale (string): Brief explanation
        - key_phrases (list[str]): Important keywords
        
        Email: "{text}"
        """

        t0 = time.time()
        response = generate_with_retry(prompt, schema=CombinedAnalysisSchema)
        result = json.loads(response.text)
        
        record_latency(
            "model_inference_latency_ms",
            (time.time() - t0) * 1000.0,
            tags={"model": "gemini", "fn": "analyze_email_combined"},
        )

        log_event(
            "GeminiCombinedAnalyzer",
            {
                "intent": result.get("intent"),
                "confidence": result.get("confidence"),
                "urgency": result.get("urgency"),
                "sentiment_score": result.get("sentiment_score"),
            },
        )

        return result

    except Exception as e:
        log_event("GeminiCombinedAnalyzer", f"Error with {model_name}: {e}")
        # Fallback to rule-based
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "urgency": "medium",
            "sentiment_score": 0.0,
            "emotion": "neutral",
            "rationale": "Fallback due to error",
            "key_phrases": []
        }

def classify_intent(text: str) -> Dict[str, Any]:
    """Wrapper for backward compatibility with EmailAgent."""
    result = analyze_email_combined(text)
    return {
        "intent": result.get("intent", "unknown"),
        "confidence": result.get("confidence", 0.0),
        "urgency": result.get("urgency", "medium"),
        "key_phrases": result.get("key_phrases", [])
    }

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Return sentiment in legacy shape used by SentimentAgent."""
    result = analyze_email_combined(text)
    score = result.get("sentiment_score", 0.0)
    return {
        "sentiment_score": score,
        "emotion": result.get("emotion", "neutral"),
        "intensity": abs(score),
        "factors": result.get("key_phrases", []),
    }

def calculate_priority_score(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        prompt = (
            "Calculate priority score (1-10) with reasoning, time_estimate (hours), "
            "and whether escalation is recommended based on this context:\n"
            + json.dumps(context, indent=2)
        )
        response = generate_with_retry(prompt, schema=PriorityScoreSchema)
        result = json.loads(response.text)
        return result
    except Exception:
        return fallback_priority_calculation(context)

def fallback_priority_calculation(context: Dict[str, Any]) -> Dict[str, Any]:
    score = 5
    urgency = str(context.get("urgency", "medium")).lower()
    sentiment = float(context.get("sentiment_score", 0.0))
    intent = str(context.get("intent", "")).lower()
    if urgency in ("critical", "high"):
        score += 2 if urgency == "high" else 3
    if sentiment < -0.5:
        score += 2
    if intent in ("complaint", "refund_request"):
        score += 2
    score = max(1, min(int(round(score)), 10))
    escalation = score >= 8
    time_estimate = 12 if escalation else 24
    return {
        "priority_score": score,
        "reasoning": "Rule-based calculation",
        "time_estimate": time_estimate,
        "escalation_recommended": escalation,
    }

def generate_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        prompt = (
            "Create a detailed task plan for this customer service request. "
            "Return JSON with tasks, estimated_time, resources_needed, success_criteria, potential_challenges.\n"
            f"Request: \"{request}\"\nContext: {json.dumps(context)}"
        )
        response = generate_with_retry(prompt, schema=TaskPlanSchema)
        result = json.loads(response.text)
        record_latency(
            "model_inference_latency_ms",
            0.0,
            tags={"model": "gemini", "fn": "generate_task_plan"},
        )
        log_event("GeminiTaskPlanner", {"task_count": len(result.get("tasks", []))})
        return result
    except Exception:
        return {
            "tasks": [
                {"step": 1, "action": "acknowledge_request", "expected_outcome": "customer_notified"},
                {"step": 2, "action": "investigate_issue", "expected_outcome": "root_cause_identified"},
                {"step": 3, "action": "provide_resolution", "expected_outcome": "issue_resolved"},
            ],
            "estimated_time": 2,
            "resources_needed": ["customer_service"],
            "success_criteria": ["customer_satisfied"],
            "potential_challenges": ["complex_issue"],
        }
