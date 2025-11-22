"""
Hybrid Memory Bank
- Structured storage: SQLite for metadata and quick queries
- Semantic retrieval: sentence-transformers embeddings + FAISS index
APIs:
- init(db_path="data/memory_bank.db")
- store_interaction(customer_id, kind, text) -> record id
- recall_relevant(customer_id, query, k=3) -> list of {id, text, score}
- get_recent(customer_id, limit=5)
"""

import datetime
import json
import os
import sqlite3
import time

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DB_PATH = "data/memory_bank.db"
EMBED_INDEX = "data/memory_embeddings.index"
EMBED_STORE = "data/memory_embeddings.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_MODEL = None


def _ensure_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBED_MODEL_NAME)
    return _MODEL


def init(db_path=DB_PATH):
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        ts REAL,
        kind TEXT,
        text TEXT
    )
    """
    )
    conn.commit()
    conn.close()
    # ensure index files exist (may be empty)
    if not os.path.exists(EMBED_STORE):
        open(EMBED_STORE, "w", encoding="utf-8").close()
    if not os.path.exists(EMBED_INDEX):
        # make an empty index file by creating an empty index on the fly
        model = _ensure_model()
        dim = model.get_sentence_embedding_dimension()
        index = faiss.IndexFlatL2(dim)
        faiss.write_index(index, EMBED_INDEX)


def store_interaction(customer_id, kind, text):
    init()
    ts = time.time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO interactions (customer_id, ts, kind, text) VALUES (?,?,?,?)",
        (customer_id, ts, kind, text),
    )
    rowid = c.lastrowid
    conn.commit()
    conn.close()
    # also append to embeddings store + update faiss index (append)
    model = _ensure_model()
    emb = model.encode([text], convert_to_numpy=True).astype("float32")
    # append to jsonl store
    entry = {"id": rowid, "customer_id": customer_id, "ts": ts, "kind": kind, "text": text}
    with open(EMBED_STORE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # load existing index, add vector, write back
    index = faiss.read_index(EMBED_INDEX)
    index.add(emb)
    faiss.write_index(index, EMBED_INDEX)
    return rowid


def get_recent(customer_id, limit=5):
    init()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, ts, kind, text FROM interactions WHERE customer_id=? ORDER BY ts DESC LIMIT ?",
        (customer_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "ts": r[1], "kind": r[2], "text": r[3]} for r in rows]


def recall_relevant(customer_id, query, k=3):
    init()
    # if index or store missing -> return recent
    if not os.path.exists(EMBED_INDEX) or not os.path.exists(EMBED_STORE):
        return get_recent(customer_id, limit=k)
    model = _ensure_model()
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    index = faiss.read_index(EMBED_INDEX)
    D, I = index.search(q_emb, k)
    # load entries
    with open(EMBED_STORE, "r", encoding="utf-8") as f:
        entries = [json.loads(l) for l in f if l.strip()]
    results = []
    for dist, idx in zip(D[0], I[0]):
        if 0 <= idx < len(entries):
            e = entries[idx]
            # only return matches for same customer if customer_id provided
            if customer_id is None or e.get("customer_id") == customer_id:
                results.append(
                    {"id": e.get("id"), "text": e.get("text"), "score": float(1.0 / (1.0 + dist))}
                )
    return results


def get_customer_profile(customer_id):
    """
    Generate a comprehensive customer profile based on their interaction history.
    Returns profile with interaction summary, sentiment trends, and key metrics.
    """
    init()

    # Get all interactions for this customer
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, ts, kind, text 
        FROM interactions 
        WHERE customer_id = ? 
        ORDER BY ts DESC
    """,
        (customer_id,),
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {
            "customer_id": customer_id,
            "total_interactions": 0,
            "first_interaction": None,
            "last_interaction": None,
            "interaction_types": {},
            "sentiment_summary": {"positive": 0, "negative": 0, "neutral": 0},
            "key_issues": [],
            "profile_summary": "No interaction history found",
        }

    # Analyze interaction patterns
    interaction_types = {}
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    key_issues = []

    for row in rows:
        _, ts, kind, text = row

        # Count interaction types
        interaction_types[kind] = interaction_types.get(kind, 0) + 1

        # Simple sentiment analysis
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
            "not working",
            "broken",
            "error",
        ]
        positive_words = [
            "happy",
            "satisfied",
            "great",
            "excellent",
            "good",
            "pleased",
            "thank",
            "appreciate",
        ]

        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)

        if negative_count > positive_count:
            sentiment_counts["negative"] += 1
        elif positive_count > negative_count:
            sentiment_counts["positive"] += 1
        else:
            sentiment_counts["neutral"] += 1

        # Extract key issues (simple keyword matching)
        if "refund" in text_lower:
            key_issues.append("refund_request")
        if "shipping" in text_lower or "delivery" in text_lower:
            key_issues.append("shipping_issue")
        if "order" in text_lower:
            key_issues.append("order_issue")
        if "technical" in text_lower or "not working" in text_lower:
            key_issues.append("technical_issue")

    # Get unique key issues
    key_issues = list(set(key_issues))

    # Calculate time metrics
    timestamps = [row[1] for row in rows]
    first_interaction = (
        datetime.datetime.fromtimestamp(min(timestamps)).isoformat() if timestamps else None
    )
    last_interaction = (
        datetime.datetime.fromtimestamp(max(timestamps)).isoformat() if timestamps else None
    )

    # Generate profile summary
    total_interactions = len(rows)
    dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

    if dominant_sentiment == "negative":
        summary = f"Customer has had {total_interactions} interactions with predominantly negative sentiment. "
        if key_issues:
            summary += f"Main issues: {', '.join(key_issues)}. "
        summary += "Requires careful handling and proactive communication."
    elif dominant_sentiment == "positive":
        summary = f"Customer has had {total_interactions} interactions with positive sentiment. Generally satisfied customer."
    else:
        summary = f"Customer has had {total_interactions} interactions with neutral sentiment. Standard customer profile."

    return {
        "customer_id": customer_id,
        "total_interactions": total_interactions,
        "first_interaction": first_interaction,
        "last_interaction": last_interaction,
        "interaction_types": interaction_types,
        "sentiment_summary": sentiment_counts,
        "key_issues": key_issues,
        "profile_summary": summary,
        "recent_interactions": get_recent(customer_id, limit=5),  # Include recent interactions
    }
