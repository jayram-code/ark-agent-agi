import os, json, time

LOG_PATH = "logs/events.log"


def log_event(agent, message, extra=None):
    os.makedirs("logs", exist_ok=True)
    entry = {"time": time.time(), "agent": agent, "message": message, "extra": extra}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
