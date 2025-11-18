#!/usr/bin/env python3
"""Test script to verify Gemini integrations with multiple samples"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.gemini_utils import classify_intent, analyze_sentiment, calculate_priority_score, generate_task_plan
from utils.validators import valid_planner_output, high_confidence_plan, strict_mode_validator

def test_gemini_integrations():
    print("🤖 Testing Gemini AI Integrations")
    print("=" * 50)

    email_samples = [
        "My order didn't arrive and I want a refund.",
        "Please cancel my subscription effective immediately.",
        "The app keeps crashing when I try to login.",
        "Where is my package? The tracking hasn't updated.",
        "I'm very happy with the quick delivery, thanks!",
        "I'm frustrated with the support delays.",
        "I'd like to change my payment method.",
        "This is the worst experience; nothing works.",
        "Can you help me with my account settings?",
        "Delivery was delayed and I'm disappointed."
    ]

    sentiment_texts = [
        "I'm furious, this order never arrived!",
        "Thanks, everything looks great",
        "I'm stressed about the missing package",
        "Neutral inquiry about account options"
    ]

    print("1. Intent Classification (10 samples)")
    successes = 0
    for i, text in enumerate(email_samples, 1):
        try:
            intent_result = classify_intent(text)
            print(f"   [{i}] intent={intent_result.get('intent')} conf={float(intent_result.get('confidence',0)):.2f} urg={intent_result.get('urgency')}")
            successes += 1
        except Exception as e:
            print(f"   [{i}] ❌ classify_intent error: {e}")
    print(f"   ✅ Classified {successes}/{len(email_samples)}")

    print("\n2. Sentiment Analysis (4 samples)")
    successes = 0
    for i, text in enumerate(sentiment_texts, 1):
        try:
            s = analyze_sentiment(text)
            print(f"   [{i}] score={float(s.get('sentiment_score',0)):.2f} emotion={s.get('emotion')} intensity={float(s.get('intensity',0)):.2f}")
            successes += 1
        except Exception as e:
            print(f"   [{i}] ❌ analyze_sentiment error: {e}")
    print(f"   ✅ Analyzed {successes}/{len(sentiment_texts)}")

    print("\n3. Priority Calculation")
    context = {"sentiment_score": -0.8, "stress": 0.8, "intent": "complaint", "urgency": "high", "customer_tier": "VIP"}
    try:
        pr = calculate_priority_score(context)
        print(f"   score={float(pr.get('priority_score',0)):.2f} escalate={pr.get('escalation_recommended')} reason={pr.get('reasoning')}")
    except Exception as e:
        print(f"   ❌ calculate_priority_score error: {e}")

    print("\n4. Task Planning + Validation")
    try:
        plan = generate_task_plan("Handle customer complaint about delayed shipping", {"strict": True})
        steps = plan.get("tasks", [])
        print(f"   steps={len(steps)} est_time={plan.get('estimated_time')} success={plan.get('success_criteria')}")
        structured = {"payload": {"plan": [{"step_id": i+1, "action": s.get("action",""), "detail": s.get("expected_outcome",""), "eta": "2-4h"} for i, s in enumerate(steps)], "confidence": 0.8}}
        print(f"   valid={valid_planner_output(structured)} high_conf={high_confidence_plan(structured)} strict={strict_mode_validator(structured)}")
    except Exception as e:
        print(f"   ❌ generate_task_plan error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Gemini Integration Tests Complete!")

if __name__ == "__main__":
    test_gemini_integrations()
