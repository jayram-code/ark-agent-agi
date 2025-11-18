# scripts/run_emotion_pipeline.py
import sys, os, json
sys.path.append(os.getcwd())

# ensure working dir is repo root
os.chdir(os.getcwd())

import pandas as pd
from src.orchestrator import Orchestrator
from src.agents.emotion_agent import EmotionAgent
from src.agents.priority_agent import PriorityAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.ticket_agent import TicketAgent
from src.agents.retryable_agent import RetryableAgent
from src.agents.sentiment_agent import SentimentAgent
from src.utils.pretty import pretty
import uuid, datetime

SAMPLE_CSV = "data/Hide_and_Seek_SAMPLE.csv"

def get_first_numeric_row(path):
    df = pd.read_csv(path, nrows=1)
    row = df.iloc[0].to_dict()
    # keep only numeric scalars (int/float/np.number)
    numeric = {}
    for k, v in row.items():
        try:
            if v is None:
                continue
            # convert booleans -> int, numpy types -> python float/int
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric[k] = float(v) if not isinstance(v, int) else float(v)
            else:
                # try to coerce
                val = float(v)
                numeric[k] = val
        except Exception:
            # skip non-numeric
            continue
    return numeric

# build audio_features safely
audio_features = get_first_numeric_row(SAMPLE_CSV)
if not audio_features:
    raise RuntimeError(f"No numeric features found in {SAMPLE_CSV}. Check the CSV or create a sample row manually.")

print("Using audio_features keys:", list(audio_features.keys())[:10], " (showing up to 10 keys)")

# prepare orchestrator + agents
orc = Orchestrator()
orc.register_agent("planner_agent", PlannerAgent("planner_agent", orc))
orc.register_agent("retryable_agent", RetryableAgent("retryable_agent", orc))
orc.register_agent("ticket_agent", TicketAgent("ticket_agent", orc))
orc.register_agent("sentiment_agent", SentimentAgent("sentiment_agent", orc))
orc.register_agent("emotion_agent", EmotionAgent("emotion_agent", orc))
orc.register_agent("priority_agent", PriorityAgent("priority_agent", orc))

# Construct message routed to emotion_agent
msg = {
    "id": str(uuid.uuid4()),
    "session_id": str(uuid.uuid4()),
    "sender": "test_user",
    "receiver": "emotion_agent",
    "type": "task_request",
    "timestamp": str(datetime.datetime.utcnow()),
    "payload": {
        "audio_features": audio_features,
        "customer_id": "C_SAMPLE",
        "text": "I'm furious, this order never arrived!"
    }
}

print("\n=== OUTGOING MESSAGE ===")
pretty(msg)

print("\n=== SENDING THROUGH ORCHESTRATOR ===")
res = orc.send_a2a(msg)

print("\n=== FINAL RESPONSE ===")
pretty(res)
