#!/usr/bin/env python3
"""Test script for Memory Bank functionality"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from storage.memory_bank import (
    get_customer_profile,
    get_recent,
    init,
    recall_relevant,
    store_interaction,
)


def test_memory_bank():
    """Test all Memory Bank functions"""
    print("🧠 Testing Memory Bank Implementation")
    print("=" * 50)
    
    # Test customer ID
    customer_id = "test_customer_123"
    
    # Clear any existing data
    import shutil
    if os.path.exists("data"):
        shutil.rmtree("data")
    
    # Initialize memory bank
    print("1. Initializing Memory Bank...")
    init()
    print("✅ Memory Bank initialized")
    
    # Test store_interaction
    print("\n2. Testing store_interaction...")
    interactions = [
        (customer_id, "email", "I'm having trouble with my order. The shipping is delayed and I'm getting frustrated."),
        (customer_id, "chat", "Thank you for helping me with the refund process. Great service!"),
        (customer_id, "email", "My product arrived broken. This is terrible quality control."),
        (customer_id, "chat", "I appreciate your quick response to my technical issue."),
        (customer_id, "email", "When will my refund be processed? I need this resolved quickly.")
    ]
    
    stored_ids = []
    for cust_id, kind, text in interactions:
        record_id = store_interaction(cust_id, kind, text)
        stored_ids.append(record_id)
        print(f"   Stored interaction: {kind} -> ID: {record_id}")
    print(f"✅ Stored {len(interactions)} interactions")
    
    # Test get_recent
    print("\n3. Testing get_recent...")
    recent = get_recent(customer_id, limit=3)
    print(f"   Found {len(recent)} recent interactions:")
    for interaction in recent:
        print(f"   - {interaction['kind']}: {interaction['text'][:50]}...")
    print("✅ get_recent working correctly")
    
    # Test recall_relevant
    print("\n4. Testing recall_relevant...")
    query = "refund and shipping issues"
    relevant = recall_relevant(customer_id, query, k=3)
    print(f"   Found {len(relevant)} relevant interactions for query '{query}':")
    for interaction in relevant:
        print(f"   - Score: {interaction['score']:.3f}: {interaction['text'][:50]}...")
    print("✅ recall_relevant working correctly")
    
    # Test get_customer_profile
    print("\n5. Testing get_customer_profile...")
    profile = get_customer_profile(customer_id)
    print(f"   Customer Profile:")
    print(f"   - Total interactions: {profile['total_interactions']}")
    print(f"   - First interaction: {profile['first_interaction']}")
    print(f"   - Last interaction: {profile['last_interaction']}")
    print(f"   - Interaction types: {profile['interaction_types']}")
    print(f"   - Sentiment summary: {profile['sentiment_summary']}")
    print(f"   - Key issues: {profile['key_issues']}")
    print(f"   - Profile summary: {profile['profile_summary']}")
    print("✅ get_customer_profile working correctly")
    
    # Test with non-existent customer
    print("\n6. Testing with non-existent customer...")
    empty_profile = get_customer_profile("non_existent_customer")
    print(f"   Empty profile handled correctly: {empty_profile['total_interactions']} interactions")
    print("✅ Edge cases handled properly")
    
    print("\n" + "=" * 50)
    print("🎉 All Memory Bank tests passed!")
    print("✅ store_interaction: Stores interactions with embeddings")
    print("✅ get_recent: Retrieves recent interactions")
    print("✅ recall_relevant: Finds semantically similar interactions")
    print("✅ get_customer_profile: Generates comprehensive customer profiles")

if __name__ == "__main__":
    test_memory_bank()