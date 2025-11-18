import google.generativeai as genai
import os
from typing import Dict, Any, Optional
from src.utils.logging_utils import log_event
from src.utils.metrics import record_latency
import time

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

def classify_intent(text: str) -> Dict[str, Any]:
    """Use Gemini to classify email intent with confidence scoring."""
    try:
        prompt = f"""
        Analyze this customer email and classify the intent. Return ONLY a JSON object with:
        - "intent": One of: complaint, refund_request, shipping_inquiry, general_query, cancellation, technical_support
        - "confidence": Float 0.0-1.0 indicating classification confidence
        - "urgency": One of: low, medium, high
        - "key_phrases": List of 3-5 key phrases that support this classification
        
        Email: "{text}"
        
        Response format: {{"intent": "complaint", "confidence": 0.85, "urgency": "high", "key_phrases": ["not working", "very disappointed", "need immediate help"]}}
        """
        
        t0 = time.time()
        response = model.generate_content(prompt)
        result = eval(response.text.strip())  # Safe for controlled JSON output
        record_latency("model_inference_latency_ms", (time.time()-t0)*1000.0, tags={"model":"gemini","fn":"classify_intent"})
        
        log_event("GeminiIntentClassifier", {
            "intent": result.get("intent"),
            "confidence": result.get("confidence"),
            "urgency": result.get("urgency")
        })
        
        return result
        
    except Exception as e:
        log_event("GeminiIntentClassifier", f"Error: {e}")
        # Fallback to rule-based classification
        return fallback_intent_classification(text)

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Use Gemini for advanced sentiment analysis with emotional context."""
    try:
        prompt = f"""
        Analyze the sentiment of this customer text. Return ONLY a JSON object with:
        - "sentiment_score": Float -1.0 to 1.0 (-1 very negative, 1 very positive)
        - "emotion": Primary emotion (angry, frustrated, neutral, satisfied, happy)
        - "intensity": Float 0.0-1.0 indicating emotional intensity
        - "factors": List of factors contributing to this sentiment
        
        Text: "{text}"
        
        Response format: {{"sentiment_score": -0.7, "emotion": "frustrated", "intensity": 0.8, "factors": ["delivery delay", "poor communication"]}}
        """
        
        t0 = time.time()
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response text
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = eval(response_text.strip())
        
        # Ensure all required fields are present
        result = {
            "sentiment_score": result.get("sentiment_score", 0.0),
            "emotion": result.get("emotion", "neutral"),
            "intensity": result.get("intensity", 0.5),
            "factors": result.get("factors", [])
        }
        
        log_event("GeminiSentimentAnalyzer", {
            "sentiment_score": result["sentiment_score"],
            "emotion": result["emotion"],
            "intensity": result["intensity"]
        })
        
        return result
        
    except Exception as e:
        log_event("GeminiSentimentAnalyzer", f"Error: {e}")
        # Fallback to rule-based sentiment analysis
        return fallback_sentiment_analysis(text)

def calculate_priority_score(context: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to calculate escalation priority based on multiple factors."""
    try:
        prompt = f"""
        Calculate escalation priority for this customer service case. Return ONLY a JSON object with:
        - "priority_score": Float 0.0-1.0 (higher = more urgent)
        - "escalation_recommended": Boolean
        - "reasoning": Brief explanation of the score
        - "time_estimate": Estimated resolution time ("<1h", "1-4h", "4-24h", ">24h")
        
        Context: {context}
        
        Response format: {{"priority_score": 0.85, "escalation_recommended": true, "reasoning": "High stress + complaint + VIP customer", "time_estimate": "1-4h"}}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response text
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = eval(response_text.strip())
        
        # Ensure all required fields are present
        result = {
            "priority_score": result.get("priority_score", 0.5),
            "escalation_recommended": result.get("escalation_recommended", False),
            "reasoning": result.get("reasoning", "Rule-based calculation"),
            "time_estimate": result.get("time_estimate", "4-24h")
        }
        
        log_event("GeminiPriorityCalculator", {
            "priority_score": result["priority_score"],
            "escalation_recommended": result["escalation_recommended"]
        })
        
        return result
        
    except Exception as e:
        log_event("GeminiPriorityCalculator", f"Error: {e}")
        # Fallback to rule-based priority calculation
        return fallback_priority_calculation(context)

def generate_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini to generate structured task plans for customer service requests."""
    try:
        prompt = f"""
        Create a detailed task plan for this customer service request. Return ONLY a JSON object with:
        - "tasks": List of task objects with "step", "action", "expected_outcome"
        - "estimated_time": Total estimated time in hours
        - "resources_needed": List of required resources/departments
        - "success_criteria": List of success criteria
        - "potential_challenges": List of potential challenges
        
        Request: "{request}"
        Context: {context}
        
        Response format: {{
            "tasks": [
                {{"step": 1, "action": "Verify order status", "expected_outcome": "Order location confirmed"}},
                {{"step": 2, "action": "Contact shipping department", "expected_outcome": "Shipping issue identified"}}
            ],
            "estimated_time": 2,
            "resources_needed": ["shipping_team", "order_database"],
            "success_criteria": ["customer_informed", "issue_resolved"],
            "potential_challenges": ["delayed_response_from_shipping"]
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response text
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        parsed = eval(response_text.strip())
        record_latency("model_inference_latency_ms", (time.time()-t0)*1000.0, tags={"model":"gemini","fn":"generate_task_plan"})
        if isinstance(parsed, list):
            parsed = {"tasks": parsed}
        result = {
            "tasks": parsed.get("tasks", []),
            "estimated_time": parsed.get("estimated_time", 2),
            "resources_needed": parsed.get("resources_needed", ["customer_service"]),
            "success_criteria": parsed.get("success_criteria", ["issue_resolved"]),
            "potential_challenges": parsed.get("potential_challenges", ["complex_issue"])
        }
        
        log_event("GeminiTaskPlanner", {
            "task_count": len(result["tasks"]),
            "estimated_time": result["estimated_time"]
        })
        
        return result
        
    except Exception as e:
        log_event("GeminiTaskPlanner", f"Error: {e}")
        # Fallback to basic task generation
        return fallback_task_plan(request, context)

# Fallback functions for when Gemini is unavailable
def fallback_intent_classification(text: str) -> Dict[str, Any]:
    """Rule-based intent classification fallback."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["not received", "missing", "lost"]):
        return {"intent": "shipping_inquiry", "confidence": 0.8, "urgency": "high", "key_phrases": ["not received"]}
    elif any(word in text_lower for word in ["refund", "money back", "return"]):
        return {"intent": "refund_request", "confidence": 0.9, "urgency": "medium", "key_phrases": ["refund"]}
    elif any(word in text_lower for word in ["angry", "frustrated", "terrible", "worst"]):
        return {"intent": "complaint", "confidence": 0.85, "urgency": "high", "key_phrases": ["angry"]}
    elif any(word in text_lower for word in ["cancel", "stop", "unsubscribe"]):
        return {"intent": "cancellation", "confidence": 0.9, "urgency": "medium", "key_phrases": ["cancel"]}
    elif any(word in text_lower for word in ["not working", "broken", "error", "issue"]):
        return {"intent": "technical_support", "confidence": 0.8, "urgency": "medium", "key_phrases": ["not working"]}
    else:
        return {"intent": "general_query", "confidence": 0.7, "urgency": "low", "key_phrases": []}

def fallback_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis fallback."""
    text_lower = text.lower()
    
    negative_words = ["angry", "frustrated", "terrible", "worst", "awful", "horrible", "disappointed", "furious"]
    positive_words = ["happy", "satisfied", "great", "excellent", "good", "pleased"]
    
    negative_count = sum(1 for word in negative_words if word in text_lower)
    positive_count = sum(1 for word in positive_words if word in text_lower)
    
    if negative_count > positive_count:
        return {"sentiment_score": -0.6, "emotion": "frustrated", "intensity": 0.7, "factors": ["negative language"]}
    elif positive_count > negative_count:
        return {"sentiment_score": 0.6, "emotion": "satisfied", "intensity": 0.5, "factors": ["positive language"]}
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
        "time_estimate": "2-4h" if score > 0.7 else "4-24h"
    }

def fallback_task_plan(request: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Basic task plan generation fallback."""
    return {
        "tasks": [
            {"step": 1, "action": "Acknowledge customer request", "expected_outcome": "Customer notified"},
            {"step": 2, "action": "Investigate issue", "expected_outcome": "Root cause identified"},
            {"step": 3, "action": "Provide resolution", "expected_outcome": "Issue resolved"}
        ],
        "estimated_time": 2,
        "resources_needed": ["customer_service"],
        "success_criteria": ["customer_satisfied"],
        "potential_challenges": ["complex_issue"]
    }
