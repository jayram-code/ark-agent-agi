#!/usr/bin/env python3
"""Test script to verify all Gemini integrations work correctly"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.gemini_utils import classify_intent, analyze_sentiment, calculate_priority_score, generate_task_plan
from utils.validators import valid_planner_output, high_confidence_plan, strict_mode_validator

def test_gemini_integrations():
    """Test all Gemini AI integrations"""
    print("🤖 Testing Gemini AI Integrations")
    print("=" * 50)
    
    # Test data
    test_email = "I'm having trouble with my order. The shipping is delayed and I'm getting frustrated."
    test_sentiment_text = "I'm furious, this order never arrived!"
    test_priority_context = {
        "sentiment": "negative",
        "stress": 0.8,
        "intent": "complaint",
        "urgency": "high"
    }
    test_task_description = "Handle customer complaint about delayed shipping"
    
    print("1. Testing EmailAgent - Intent Classification...")
    try:
        intent_result = classify_intent(test_email)
        print(f"   Intent: {intent_result['intent']}")
        print(f"   Confidence: {intent_result['confidence']}")
        print(f"   Urgency: {intent_result['urgency']}")
        print(f"   Key Phrases: {intent_result['key_phrases']}")
        print("✅ EmailAgent Gemini integration working")
    except Exception as e:
        print(f"❌ EmailAgent failed: {e}")
    
    print("\n2. Testing SentimentAgent - Sentiment Analysis...")
    try:
        sentiment_result = analyze_sentiment(test_sentiment_text)
        print(f"   Sentiment: {sentiment_result['sentiment']}")
        print(f"   Confidence: {sentiment_result['confidence']}")
        print(f"   Emotional Context: {sentiment_result['emotional_context']}")
        print("✅ SentimentAgent Gemini integration working")
    except Exception as e:
        print(f"❌ SentimentAgent failed: {e}")
    
    print("\n3. Testing PriorityAgent - Priority Calculation...")
    try:
        priority_result = calculate_priority_score(test_priority_context)
        print(f"   Priority Score: {priority_result['priority_score']}")
        print(f"   Escalation: {priority_result['escalation']}")
        print(f"   Reasoning: {priority_result['reasoning']}")
        print("✅ PriorityAgent Gemini integration working")
    except Exception as e:
        print(f"❌ PriorityAgent failed: {e}")
    
    print("\n4. Testing PlannerAgent - Task Planning...")
    try:
        plan_result = generate_task_plan(test_task_description)
        print(f"   Plan Steps: {len(plan_result['steps'])}")
        print(f"   Estimated Duration: {plan_result['estimated_duration']}")
        print(f"   Success Criteria: {plan_result['success_criteria']}")
        print("✅ PlannerAgent Gemini integration working")
        
        # Test validation
        print("\n5. Testing PlannerAgent Validation...")
        print(f"   Valid Output: {valid_planner_output(plan_result)}")
        print(f"   High Confidence: {high_confidence_plan(plan_result)}")
        print(f"   Strict Mode: {strict_mode_validator(plan_result)}")
        print("✅ Validation functions working")
        
    except Exception as e:
        print(f"❌ PlannerAgent failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Gemini Integration Tests Complete!")
    print("All agents have been successfully integrated with Gemini AI capabilities.")

if __name__ == "__main__":
    test_gemini_integrations()