# scripts/run_retry_test.py
import sys, os
sys.path.append(os.getcwd())

from src.orchestrator import Orchestrator
from src.agents.planner_agent import PlannerAgent
from src.agents.retryable_agent import RetryableAgent
from src.utils.pretty import pretty
import time

orc = Orchestrator()
planner = PlannerAgent("planner_agent", orc)
retry = RetryableAgent("retryable_agent", orc)

orc.register_agent("planner_agent", planner)
orc.register_agent("retryable_agent", retry)

# Craft a retry message that asks planner to create a plan and validator to check it
m = orc.new_message(sender="user", receiver="retryable_agent", payload={
    "agent":"planner_agent",
    "max_retries":3,
    "validator":"non_empty_plan",
    "original_payload":{"text":"My order didn't arrive. I want a refund."}
})

print("=== SENDING retryable_agent MESSAGE ===")
pretty(m)

print("\n=== RESPONSE ===")
res = orc.send_a2a(m)
pretty(res)
