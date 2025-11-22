"""
Baseline Implementations for Comparison
Rule-based approaches for intent, sentiment, and priority classification
"""

import re
from typing import Dict, Any, List

class RuleBasedIntentClassifier:
    """Rule-based intent classification using keyword matching"""
    
    INTENT_KEYWORDS = {
        "refund_request": ["refund", "money back", "return", "cancel order"],
        "shipping_inquiry": ["shipping", "delivery", "track", "package", "where is my"],
        "password_reset": ["password", "reset", "forgot", "can't login", "locked out"],
        "billing_issue": ["charge", "billing", "invoice", "payment", "charged twice"],
        "product_question": ["how to", "what is", "does it", "can it", "features"],
        "complaint": ["terrible", "worst", "never again", "disappointed", "horrible"],
        "general_inquiry": []  # default
    }
    
    def classify(self, text: str) -> str:
        """Classify intent based on keyword matching"""
        text_lower = text.lower()
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent
        
        return "general_inquiry"

class RuleBasedSentimentAnalyzer:
    """Rule-based sentiment analysis using keyword matching"""
    
    POSITIVE_WORDS = ["great", "excellent", "love", "amazing", "wonderful", "perfect", "fantastic"]
    NEGATIVE_WORDS = ["terrible", "horrible", "worst", "hate", "awful", "disappointed", "angry"]
    
    def analyze(self, text: str) -> str:
        """Analyze sentiment based on keyword presence"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"

class RuleBasedPriorityCalculator:
    """Rule-based priority calculation using simple rules"""
    
    HIGH_PRIORITY_KEYWORDS = ["urgent", "emergency", "asap", "immediately", "critical"]
    LOW_PRIORITY_KEYWORDS = ["whenever", "no rush", "when you can"]
    
    def calculate(self, text: str, sentiment: str = "neutral") -> str:
        """Calculate priority based on keywords and sentiment"""
        text_lower = text.lower()
        
        # Check for explicit priority keywords
        for keyword in self.HIGH_PRIORITY_KEYWORDS:
            if keyword in text_lower:
                return "high"
        
        for keyword in self.LOW_PRIORITY_KEYWORDS:
            if keyword in text_lower:
                return "low"
        
        # Use sentiment as fallback
        if sentiment == "negative":
            return "medium"
        
        return "low"

class BaselineComparison:
    """
    Compare LLM-based and rule-based approaches
    """
    
    def __init__(self):
        self.intent_classifier = RuleBasedIntentClassifier()
        self.sentiment_analyzer = RuleBasedSentimentAnalyzer()
        self.priority_calculator = RuleBasedPriorityCalculator()
    
    def process(self, text: str) -> Dict[str, str]:
        """Process text with rule-based models"""
        intent = self.intent_classifier.classify(text)
        sentiment = self.sentiment_analyzer.analyze(text)
        priority = self.priority_calculator.calculate(text, sentiment)
        
        return {
            "intent": intent,
            "sentiment": sentiment,
            "priority": priority
        }
    
    @staticmethod
    def estimate_manual_time(num_emails: int) -> float:
        """
        Estimate manual processing time in seconds
        
        Assumptions:
        - Reading email: 30 seconds
        - Classification: 15 seconds
        - Response drafting: 60 seconds
        - Total: ~105 seconds per email
        """
        SECONDS_PER_EMAIL = 105
        return num_emails * SECONDS_PER_EMAIL
    
    @staticmethod
    def compare_approaches(
        llm_results: List[Dict[str, Any]],
        rule_results: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare LLM vs Rule-based vs Manual approaches
        
        Args:
            llm_results: Results from LLM-based system
            rule_results: Results from rule-based system
            ground_truth: Actual correct labels
            
        Returns:
            Comparison metrics
        """
        def calculate_accuracy(predictions, truth):
            correct = sum(1 for p, t in zip(predictions, truth) if p == t)
            return correct / len(predictions) if predictions else 0
        
        return {
            "llm": {
                "accuracy": calculate_accuracy(
                    [r.get("intent") for r in llm_results],
                    [t.get("intent") for t in ground_truth]
                ),
                "avg_latency_ms": sum(r.get("latency_ms", 0) for r in llm_results) / len(llm_results)
            },
            "rule_based": {
                "accuracy": calculate_accuracy(
                    [r.get("intent") for r in rule_results],
                    [t.get("intent") for t in ground_truth]
                ),
                "avg_latency_ms": 5.0  # Rule-based is very fast
            },
            "manual": {
                "accuracy": 0.95,  # Assume humans are 95% accurate
                "time_per_email_seconds": 105,
                "total_time_seconds": BaselineComparison.estimate_manual_time(len(ground_truth))
            }
        }

# Global baseline instance
baseline = BaselineComparison()

def get_baseline() -> BaselineComparison:
    """Get the global baseline comparison instance"""
    return baseline
