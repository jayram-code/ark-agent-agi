import sqlite3, os

DB_PATH = "data/tickets.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT,
        text TEXT,
        sentiment REAL
    )
    """)
    conn.commit()
    conn.close()

def create_ticket(intent, text, sentiment):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tickets (intent, text, sentiment) VALUES (?, ?, ?)",
        (intent, text, sentiment)
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id
