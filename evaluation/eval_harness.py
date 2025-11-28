import asyncio
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

# Add src to path
import sys
# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Add src directory (for imports like 'from agents...')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.agents.email_agent import EmailAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.priority_agent import PriorityAgent
from src.agents.ticket_agent import TicketAgent
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.retryable_agent import RetryableAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.action_executor_agent import ActionExecutorAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.shipping_agent import ShippingAgent
from src.agents.base_agent import BaseAgent
from src.core.orchestrator import Orchestrator
from src.models.messages import AgentMessage, MessageType

# Helper: Normalize agent names for comparison
def normalize_agent_name(name: str) -> str:
    """Convert agent names to consistent format (snake_case)."""
    if not name:
        return ""
    # Convert PascalCase to snake_case: TicketAgent -> ticket_agent
    import re
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', str(name)).lower()
    return name

# Helper: Improved sentiment matching with synonyms
SENTIMENT_SYNONYMS = {
    "angry": ["angry", "furious", "mad", "enraged"],
    "frustrated": ["frustrated", "annoyed", "irritated"],
    "happy": ["happy", "satisfied", "pleased", "delighted"],
    "neutral": ["neutral", "calm"],
    "stressed": ["stressed", "anxious", "worried"],
    "confused": ["confused", "uncertain"],
    "sad": ["sad", "disappointed", "unhappy"]
}

def normalize_sentiment(sentiment: str) -> str:
    """Map sentiment to canonical form."""
    sentiment = sentiment.lower().strip()
    for canonical, synonyms in SENTIMENT_SYNONYMS.items():
        if sentiment in synonyms:
            return canonical
    return sentiment

# ------------------------------------------------------------------------------
# Instrumented Orchestrator
# ------------------------------------------------------------------------------
class InstrumentedOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__()
        self.history: List[AgentMessage] = []
        self.routing_decisions: List[Dict[str, Any]] = []

    async def route(self, message: AgentMessage) -> Any:
        # Capture the message being routed
        self.history.append(message)
        
        # Capture routing decision
        target = self.routing_policy.determine_receiver(message)
        self.routing_decisions.append({
            "trace_id": message.trace_id,
            "sender": message.sender,
            "original_receiver": message.receiver,
            "final_receiver": target,
            "payload": message.payload
        })
        
        # Call parent route (which executes the agent)
        return await super().route(message)

    async def send_a2a(self, message: AgentMessage) -> Any:
        # Capture A2A messages too
        self.history.append(message)
        return await super().send_a2a(message)

# ------------------------------------------------------------------------------
# Evaluation Logic
# ------------------------------------------------------------------------------
def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    if not os.path.exists(path):
        print(f"Warning: Dataset not found at {path}")
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def _write_results(results: List[Dict], summary: Dict):
    os.makedirs("evaluation", exist_ok=True)
    
    # Write JSON Summary
    with open("evaluation/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    # Write CSV Results
    if results:
        keys = results[0].keys()
        with open("evaluation/results.csv", "w", encoding="utf-8") as f:
            f.write(",".join(keys) + "\n")
            for r in results:
                vals = [str(r.get(k, "")).replace(",", ";") for k in keys]
                f.write(",".join(vals) + "\n")

async def evaluate_case(orchestrator: InstrumentedOrchestrator, case: Dict[str, Any]) -> Dict[str, Any]:
    # Reset history for this case
    orchestrator.history = []
    orchestrator.routing_decisions = []
    
    email_text = case["email_text"]
    session_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # 1. Inject message into EmailAgent
    msg = AgentMessage(
        id=str(uuid.uuid4()),
        trace_id=trace_id,
        session_id=session_id,
        sender="user",
        receiver="email_agent",
        type=MessageType.TASK_REQUEST,
        timestamp=str(time.time()),
        payload={"text": email_text}
    )
    
    start_time = time.time()
    try:
        # We await the first call, but subsequent A2A calls happen within the chain
        await orchestrator.route(msg)
    except Exception as e:
        print(f"Error processing case: {e}")
    
    duration = (time.time() - start_time) * 1000
    
    # 2. Inspect History to find predictions
    pred_intent = "unknown"
    pred_sentiment = "neutral"
    pred_urgency = "low"
    final_agent = "unknown"
    
    # Find what EmailAgent sent to SentimentAgent (contains Intent)
    for m in orchestrator.history:
        if m.sender == "email_agent" and m.receiver == "sentiment_agent":
            payload = m.payload if isinstance(m.payload, dict) else m.payload.model_dump()
            pred_intent = payload.get("intent", "unknown")
            pred_urgency = payload.get("urgency", "unknown")
            
    # Find what SentimentAgent sent to PriorityAgent (contains Sentiment)
    for m in orchestrator.history:
        if m.sender == "sentiment_agent" and m.receiver == "priority_agent":
            payload = m.payload if isinstance(m.payload, dict) else m.payload.model_dump()
            pred_sentiment = payload.get("emotion", "neutral")
            
    # Find final routing decision (The last decision in the chain usually points to the handler)
    # Typically: Email -> Sentiment -> Priority -> Ticket/Refund/etc.
    # We look for the decision made by PriorityAgent or RoutingPolicy
    if orchestrator.routing_decisions:
        # The last routing decision that isn't to an intermediate agent
        intermediates = {"email_agent", "sentiment_agent", "priority_agent"}
        for d in reversed(orchestrator.routing_decisions):
            if d["final_receiver"] not in intermediates:
                final_agent = d["final_receiver"]
                break
    
    # Normalize for comparison
    true_intent = case.get("true_intent", "").lower()
    pred_intent = pred_intent.lower()
    
    true_sentiment = case.get("true_sentiment", "").lower()
    pred_sentiment = pred_sentiment.lower()
    
    # Improved sentiment matching using synonym mapping
    true_sentiment_norm = normalize_sentiment(true_sentiment)
    pred_sentiment_norm = normalize_sentiment(pred_sentiment)
    sentiment_match = true_sentiment_norm == pred_sentiment_norm
    
    # Normalize agent names for routing comparison
    expected_agent = normalize_agent_name(case.get("expected_routing", ""))
    actual_agent = normalize_agent_name(final_agent)
    routing_match = expected_agent == actual_agent
        
    return {
        "email_text": email_text[:50] + "...",
        "true_intent": true_intent,
        "pred_intent": pred_intent,
        "intent_correct": pred_intent == true_intent,
        "true_sentiment": true_sentiment,
        "pred_sentiment": pred_sentiment,
        "sentiment_correct": sentiment_match,
        "expected_routing": case.get("expected_routing"),
        "actual_routing": final_agent,
        "routing_correct": routing_match,
        "latency_ms": round(duration, 2)
    }

async def run_evaluation():
    print("Starting Evaluation...")
    
    # Setup Orchestrator
    orchestrator = InstrumentedOrchestrator()
    
    # Register Agents
    orchestrator.register_agent("email_agent", EmailAgent("email_agent", orchestrator))
    orchestrator.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orchestrator))
    orchestrator.register_agent("priority_agent", PriorityAgent("priority_agent", orchestrator))
    orchestrator.register_agent("ticket_agent", TicketAgent("ticket_agent", orchestrator))
    orchestrator.register_agent("supervisor_agent", SupervisorAgent("supervisor_agent", orchestrator))
    orchestrator.register_agent("retryable_agent", RetryableAgent("retryable_agent", orchestrator))
    orchestrator.register_agent("planner_agent", PlannerAgent("planner_agent", orchestrator))
    orchestrator.register_agent("action_executor_agent", ActionExecutorAgent("action_executor_agent", orchestrator))
    orchestrator.register_agent("knowledge_agent", KnowledgeAgent("knowledge_agent", orchestrator))
    orchestrator.register_agent("shipping_agent", ShippingAgent("shipping_agent", orchestrator))
    
    # Load Data
    dataset_path = os.path.join(os.getcwd(), "failure_cases.jsonl")
    cases = _read_jsonl(dataset_path)
    print(f"Loaded {len(cases)} test cases.")
    
    results = []
    for i, case in enumerate(cases):
        print(f"Running case {i+1}/{len(cases)}...", end="\r")
        res = await evaluate_case(orchestrator, case)
        results.append(res)
        
    print("\nEvaluation Complete.")
    
    # Compute Metrics
    total = len(results)
    if total == 0:
        print("No results to summarize.")
        return

    intent_acc = sum(1 for r in results if r["intent_correct"]) / total
    sentiment_acc = sum(1 for r in results if r["sentiment_correct"]) / total
    routing_acc = sum(1 for r in results if r["routing_correct"]) / total
    avg_latency = sum(r["latency_ms"] for r in results) / total
    
    summary = {
        "total_cases": total,
        "intent_accuracy": round(intent_acc, 2),
        "sentiment_accuracy": round(sentiment_acc, 2),
        "routing_accuracy": round(routing_acc, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "timestamp": str(datetime.datetime.now())
    }
    
    print("\n--- Summary ---")
    print(json.dumps(summary, indent=2))
    
    _write_results(results, summary)
    print(f"Results saved to evaluation/summary.json and evaluation/results.csv")

if __name__ == "__main__":
    import datetime
    asyncio.run(run_evaluation())
