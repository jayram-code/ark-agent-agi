import os
import json
import time
import uuid
from typing import List, Dict, Any
from src.a2a_router import send_message
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
from src.agents.email_sender_agent import EmailSenderAgent

def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def _write_csv(path: str, rows: List[Dict[str, Any]], header: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            vals = [str(r.get(h, "")) for h in header]
            f.write(",".join(vals) + "\n")

def _append_json(path: str, obj: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2))

def _clear_logs():
    os.makedirs("logs", exist_ok=True)
    open("logs/events.log", "w").close()
    open("logs/metrics.jsonl", "w").close()

def _parse_events_for_trace(trace_id: str) -> List[Dict[str, Any]]:
    events = []
    if not os.path.exists("logs/events.log"):
        return events
    with open("logs/events.log", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            msg = e.get("message")
            if e.get("agent") == "A2A" and isinstance(msg, dict):
                if msg.get("trace_id") == trace_id:
                    events.append(e)
    return events

def _parse_recent_supervisor_score(prev_len: int) -> float:
    if not os.path.exists("logs/events.log"):
        return 0.0
    size = os.path.getsize("logs/events.log")
    with open("logs/events.log", "r", encoding="utf-8") as f:
        f.seek(prev_len)
        for line in f:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("agent") == "SupervisorAgent":
                m = e.get("message")
                if isinstance(m, dict) and "supervisor_score" in m:
                    try:
                        return float(m.get("supervisor_score", 0.0))
                    except Exception:
                        return 0.0
    return 0.0

def _count_retry_attempts(trace_id: str) -> int:
    attempts = 0
    if not os.path.exists("logs/events.log"):
        return attempts
    with open("logs/events.log", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            msg = e.get("message")
            if e.get("agent") == "A2A" and isinstance(msg, dict):
                if msg.get("trace_id") == trace_id:
                    if msg.get("sender") == "retryable_agent" and msg.get("receiver") == "planner_agent":
                        attempts += 1
    return attempts

class SimpleOrchestrator:
    def __init__(self):
        self.agents = {}
    def register_agent(self, name, agent):
        self.agents[name] = agent
    def route(self, message: dict):
        receiver = message.get("receiver")
        return self.agents[receiver].receive(message)
    def send_a2a(self, message: dict):
        return send_message(self, message)

def build_orchestrator() -> SimpleOrchestrator:
    o = SimpleOrchestrator()
    o.register_agent("email_agent", EmailAgent("email_agent", o))
    o.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", o))
    o.register_agent("priority_agent", PriorityAgent("priority_agent", o))
    o.register_agent("ticket_agent", TicketAgent("ticket_agent", o))
    o.register_agent("supervisor_agent", SupervisorAgent("supervisor_agent", o))
    o.register_agent("retryable_agent", RetryableAgent("retryable_agent", o))
    o.register_agent("planner_agent", PlannerAgent("planner_agent", o))
    o.register_agent("action_executor_agent", ActionExecutorAgent("action_executor_agent", o))
    o.register_agent("knowledge_agent", KnowledgeAgent("knowledge_agent", o))
    o.register_agent("shipping_agent", ShippingAgent("shipping_agent", o))
    o.register_agent("email_sender_agent", EmailSenderAgent("email_sender_agent", o))
    return o

def run_dataset(dataset_path: str) -> Dict[str, Any]:
    _clear_logs()
    cases = _read_jsonl(dataset_path)
    o = build_orchestrator()
    results = []
    latencies = []
    escalations = 0
    routing_errors = 0
    intent_correct = 0
    sentiment_correct = 0
    urgency_correct = 0
    total_retry_invocations = 0
    supervisor_scores = []
    for i, row in enumerate(cases):
        start_pos = os.path.getsize("logs/events.log") if os.path.exists("logs/events.log") else 0
        email = row["email_text"]
        true_intent = row.get("true_intent")
        true_sentiment = row.get("true_sentiment")
        true_urgency = row.get("true_urgency")
        expected_routing = row.get("expected_routing")
        session_id = f"S_{i+1}"
        trace_id = str(uuid.uuid4())
        msg = {
            "id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "session_id": session_id,
            "sender": "email_agent",
            "receiver": "sentiment_agent",
            "type": "task_request",
            "timestamp": str(time.time()),
            "payload": {
                "text": email,
                "customer_id": f"C_{i+1}"
            }
        }
        t0 = time.time()
        _ = o.send_a2a(msg)
        t1 = time.time()
        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)
        events = _parse_events_for_trace(trace_id)
        pred_intent = ""
        pred_sentiment = ""
        pred_urgency = ""
        pred_routing = "TicketAgent"
        for e in events:
            m = e.get("message")
            recv = m.get("receiver")
            payload = m.get("payload", {})
            if recv == "sentiment_agent":
                pred_intent = payload.get("intent", "")
                pred_urgency = payload.get("urgency", "")
            if recv == "priority_agent":
                pred_sentiment = payload.get("emotion", "")
            if recv == "supervisor_agent":
                pred_routing = "SupervisorAgent"
        if pred_routing != expected_routing:
            routing_errors += 1
        if pred_intent == true_intent:
            intent_correct += 1
        if str(pred_sentiment).lower() == str(true_sentiment).lower():
            sentiment_correct += 1
        if str(pred_urgency).lower() == str(true_urgency).lower():
            urgency_correct += 1
        if pred_routing == "SupervisorAgent":
            escalations += 1
        retry_attempts = _count_retry_attempts(trace_id)
        total_retry_invocations += (1 if retry_attempts > 0 else 0)
        supervisor_score = _parse_recent_supervisor_score(start_pos)
        if supervisor_score > 0:
            supervisor_scores.append(supervisor_score)
        results.append({
            "email_id": i + 1,
            "true_intent": true_intent,
            "pred_intent": pred_intent,
            "correct": int(pred_intent == true_intent),
            "true_sentiment": true_sentiment,
            "pred_sentiment": pred_sentiment,
            "sentiment_correct": int(str(pred_sentiment).lower() == str(true_sentiment).lower()),
            "processing_time_ms": round(latency_ms, 2),
            "retry_count": retry_attempts,
            "supervisor_score": round(supervisor_score, 4)
        })
    intent_acc = intent_correct / max(1, len(cases))
    sentiment_acc = sentiment_correct / max(1, len(cases))
    urgency_acc = urgency_correct / max(1, len(cases))
    avg_latency = sum(latencies) / max(1, len(latencies))
    sorted_lat = sorted(latencies)
    def _pctl(vals: List[float], p: float) -> float:
        if not vals:
            return 0.0
        k = int(round(p * (len(vals) - 1)))
        return vals[k]
    p95 = _pctl(sorted_lat, 0.95)
    p99 = _pctl(sorted_lat, 0.99)
    retry_rate = total_retry_invocations / max(1, len(cases))
    escalation_rate = escalations / max(1, len(cases))
    false_positive_rate = routing_errors / max(1, len(cases))
    manual_min = 7.0
    auto_min = avg_latency / 60000.0
    tickets_per_hour = 3600.0 / (avg_latency / 1000.0) if avg_latency > 0 else 0.0
    hours_saved_per_week = max(0.0, (manual_min - auto_min)) * 100.0 / 60.0
    cost_per_ticket = 0.15
    summary = {
        "overall_accuracy": round((intent_acc + sentiment_acc + urgency_acc) / 3.0, 4),
        "intent_accuracy": round(intent_acc, 4),
        "sentiment_accuracy": round(sentiment_acc, 4),
        "urgency_accuracy": round(urgency_acc, 4),
        "avg_processing_time_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "retry_rate": round(retry_rate, 4),
        "escalation_rate": round(escalation_rate, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "business_impact": {
            "hours_saved_per_week": round(hours_saved_per_week, 2),
            "cost_per_ticket": cost_per_ticket,
            "tickets_per_hour": round(tickets_per_hour, 2)
        }
    }
    _write_csv("evaluation/results.csv", results, [
        "email_id","true_intent","pred_intent","correct","true_sentiment","pred_sentiment","sentiment_correct","processing_time_ms","retry_count","supervisor_score"
    ])
    _append_json("evaluation/summary.json", summary)
    return {"results": results, "summary": summary}

def main():
    ds = os.path.join(os.getcwd(), "failure_cases.jsonl")
    run_dataset(ds)

if __name__ == "__main__":
    main()
