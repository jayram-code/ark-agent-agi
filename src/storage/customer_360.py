from storage.memory_bank import get_customer_profile


def generate_customer_360(customer_id: str):
    profile = get_customer_profile(customer_id)
    sentiment = profile.get("sentiment_summary", {})
    total = profile.get("total_interactions", 0)
    issues = profile.get("key_issues", [])
    dominant = None
    if sentiment:
        dominant = max(sentiment, key=sentiment.get)
    risk_flag = (sentiment.get("negative", 0) > sentiment.get("positive", 0)) and total >= 3
    vip_status = False
    avg_sentiment = 0.0
    if total:
        pos = float(sentiment.get("positive", 0))
        neg = float(sentiment.get("negative", 0))
        neu = float(sentiment.get("neutral", 0))
        avg_sentiment = (pos - neg) / max(1.0, (pos + neg + neu))
    return {
        "customer_id": customer_id,
        "total_interactions": total,
        "dominant_sentiment": dominant,
        "avg_sentiment_index": avg_sentiment,
        "common_issues": issues,
        "vip_status": vip_status,
        "risk_flag": risk_flag,
        "summary": profile.get("profile_summary"),
        "recent_interactions": profile.get("recent_interactions", []),
    }
