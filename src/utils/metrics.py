import os, json, time

METRICS_LOG = "logs/metrics.jsonl"
_TRACE_ACCUM = {}

def _write(entry):
    os.makedirs("logs", exist_ok=True)
    with open(METRICS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def record_latency(name, value_ms, tags=None):
    entry = {
        "ts": time.time(),
        "metric": name,
        "type": "latency_ms",
        "value": float(value_ms),
        "tags": tags or {}
    }
    _write(entry)

def increment(name, value=1, tags=None):
    entry = {
        "ts": time.time(),
        "metric": name,
        "type": "counter",
        "value": int(value),
        "tags": tags or {}
    }
    _write(entry)

def gauge(name, value, tags=None):
    entry = {
        "ts": time.time(),
        "metric": name,
        "type": "gauge",
        "value": float(value),
        "tags": tags or {}
    }
    _write(entry)

def ensure_trace(trace_id):
    if trace_id and trace_id not in _TRACE_ACCUM:
        _TRACE_ACCUM[trace_id] = 0.0

def accumulate_trace_time(trace_id, latency_ms):
    if trace_id:
        ensure_trace(trace_id)
        _TRACE_ACCUM[trace_id] += float(latency_ms)
        gauge("trace_pipeline_time_ms", _TRACE_ACCUM[trace_id], tags={"trace_id": trace_id})
