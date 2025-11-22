# scripts/run_ship_test.py
import os
import sys

sys.path.append(os.getcwd())

import time

from src.agents.retryable_agent import RetryableAgent
from src.agents.shipping_agent import ShippingAgent
from src.agents.ticket_agent import TicketAgent
from src.orchestrator import Orchestrator
from src.utils.pretty import pretty

orc = Orchestrator()

# register minimal agents needed
ship = ShippingAgent("shipping_agent", orc)
ticket = TicketAgent("ticket_agent", orc)
retry = RetryableAgent("retryable_agent", orc)

orc.register_agent("shipping_agent", ship)
orc.register_agent("ticket_agent", ticket)
orc.register_agent("retryable_agent", retry)

# Build a message to call shipping_agent directly
msg = orc.new_message(sender="user", receiver="shipping_agent", payload={"order_id":"ORD123","next":"ticket_agent","customer_id":"C900"})

print("=== SENDING shipping_agent MESSAGE ===")
pretty(msg)

print("\n=== RESPONSE ===")
res = orc.send_a2a(msg)
pretty(res)

# Give a small pause then show latest tickets from DB (if exists)
time.sleep(0.3)
try:
    import sqlite3
    con = sqlite3.connect("data/tickets.db")
    cur = con.cursor()
    rows = list(cur.execute("SELECT id, intent, text FROM tickets ORDER BY id DESC LIMIT 5"))
    print("\n=== LATEST TICKETS ===")
    for r in rows:
        print(r)
    con.close()
except Exception as e:
    print("Could not read tickets DB:", e)
