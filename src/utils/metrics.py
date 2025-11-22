import os, json, time
import uuid
import threading

METRICS_LOG = "logs/metrics.jsonl"
_TRACE_ACCUM = {}
_LOCK = threading.Lock()


class StructuredLogger:
    """
    Production-grade structured logger for metrics.
    Writes NDJSON (Newline Delimited JSON) to a log file.
    Thread-safe.
    """

    def __init__(self, log_path=METRICS_LOG):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, metric_name, metric_type, value, tags=None):
        entry = {
            "ts": time.time(),
            "iso_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metric": metric_name,
            "type": metric_type,
            "value": value,
            "tags": tags or {},
            "event_id": str(uuid.uuid4()),
        }

        with _LOCK:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")


_LOGGER = StructuredLogger()


def record_latency(name, value_ms, tags=None):
    _LOGGER.log(name, "latency_ms", float(value_ms), tags)


def increment(name, value=1, tags=None):
    _LOGGER.log(name, "counter", int(value), tags)


def gauge(name, value, tags=None):
    _LOGGER.log(name, "gauge", float(value), tags)


def ensure_trace(trace_id):
    if trace_id and trace_id not in _TRACE_ACCUM:
        _TRACE_ACCUM[trace_id] = 0.0


def accumulate_trace_time(trace_id, latency_ms):
    if trace_id:
        ensure_trace(trace_id)
        _TRACE_ACCUM[trace_id] += float(latency_ms)
        gauge("trace_pipeline_time_ms", _TRACE_ACCUM[trace_id], tags={"trace_id": trace_id})
