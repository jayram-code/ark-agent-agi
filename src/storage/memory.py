import os
import sqlite3
import time

DB = "data/memory.db"


def init():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS memory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        ts REAL,
        kind TEXT,
        content TEXT
    )
    """
    )
    conn.commit()
    conn.close()


def add_memory(customer_id, kind, content):
    init()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO memory(customer_id,ts,kind,content) VALUES (?,?,?,?)",
        (customer_id, time.time(), kind, content),
    )
    conn.commit()
    conn.close()


def get_recent(customer_id, limit=5):
    init()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT ts, kind, content FROM memory WHERE customer_id=? ORDER BY ts DESC LIMIT ?",
        (customer_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows
