import json
import os
import sqlite3
from datetime import datetime

DB_PATH = "data/tickets.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT,
        category TEXT,
        text TEXT,
        sentiment REAL,
        tags TEXT,
        key_phrases TEXT,
        customer_id TEXT,
        priority_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'open'
    )
    """
    )
    conn.commit()
    conn.close()


def create_ticket(
    intent,
    text,
    sentiment,
    category=None,
    tags=None,
    key_phrases=None,
    customer_id=None,
    priority_score=None,
    status="open",
):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Auto-categorize if not provided
    if category is None:
        category = derive_category(intent)

    # Convert lists to JSON strings for storage
    tags_json = json.dumps(tags) if tags else "[]"
    key_phrases_json = json.dumps(key_phrases) if key_phrases else "[]"

    cursor.execute(
        """INSERT INTO tickets (intent, category, text, sentiment, tags, key_phrases, customer_id, priority_score, status) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            intent,
            category,
            text,
            sentiment,
            tags_json,
            key_phrases_json,
            customer_id,
            priority_score,
            status,
        ),
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def derive_category(intent):
    """Derive category from intent for better organization"""
    intent_to_category = {
        "refund_request": "billing",
        "shipping_inquiry": "logistics",
        "complaint": "customer_service",
        "technical_support": "technical",
        "cancellation": "account",
        "general_query": "general",
    }

    # Also check for keywords in the intent text
    if isinstance(intent, str):
        intent_lower = intent.lower()
        if any(word in intent_lower for word in ["refund", "money", "billing", "payment"]):
            return "billing"
        elif any(word in intent_lower for word in ["shipping", "delivery", "tracking", "package"]):
            return "logistics"
        elif any(
            word in intent_lower
            for word in ["technical", "broken", "error", "not working", "issue"]
        ):
            return "technical"
        elif any(word in intent_lower for word in ["complaint", "angry", "frustrated", "terrible"]):
            return "customer_service"
        elif any(word in intent_lower for word in ["cancel", "unsubscribe", "stop"]):
            return "account"

    return intent_to_category.get(intent, "general")


def get_ticket(ticket_id):
    """Retrieve a ticket by ID"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "intent": row[1],
            "category": row[2],
            "text": row[3],
            "sentiment": row[4],
            "tags": json.loads(row[5]),
            "key_phrases": json.loads(row[6]),
            "customer_id": row[7],
            "priority_score": row[8],
            "created_at": row[9],
            "status": row[10],
        }
    return None


def update_ticket_status(ticket_id, status):
    """Update ticket status (open, in_progress, resolved, closed)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()


def get_tickets_by_category(category, limit=50):
    """Get tickets by category for workflow automation"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE category = ? ORDER BY created_at DESC LIMIT ?",
        (category, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    tickets = []
    for row in rows:
        tickets.append(
            {
                "id": row[0],
                "intent": row[1],
                "category": row[2],
                "text": row[3],
                "sentiment": row[4],
                "tags": json.loads(row[5]),
                "key_phrases": json.loads(row[6]),
                "customer_id": row[7],
                "priority_score": row[8],
                "created_at": row[9],
                "status": row[10],
            }
        )
    return tickets
