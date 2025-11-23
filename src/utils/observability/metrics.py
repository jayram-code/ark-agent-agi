"""
Metrics Collector for ARK Agent AGI
Tracks system performance metrics (latency, success rate, token usage)
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict


class MetricsCollector:
    """
    Collect and aggregate system metrics
    """

    def __init__(self, metrics_file: str = "data/metrics.json"):
        self.metrics_file = metrics_file
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        
        # In-memory metrics
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_metrics()

    def record_message(
        self,
        agent_name: str,
        latency_ms: float,
        success: bool,
        tokens_used: int = 0,
        error: Optional[str] = None
    ):
        """Record metrics for a single message processed by an agent"""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
            "success": success,
            "tokens": tokens_used,
            "error": error
        }
        
        self.metrics[agent_name].append(metric)
        
        # Save periodically (every 10 records)
        if len(self.metrics[agent_name]) % 10 == 0:
            self._save_metrics()

    def get_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated statistics"""
        if agent_name:
            return self._compute_stats(agent_name, self.metrics.get(agent_name, []))
        
        # Global stats
        all_stats = {}
        total_metrics = []
        
        for name, metrics in self.metrics.items():
            all_stats[name] = self._compute_stats(name, metrics)
            total_metrics.extend(metrics)
        
        all_stats["_global"] = self._compute_stats("global", total_metrics)
        return all_stats

    def _compute_stats(self, name: str, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistics for a set of metrics"""
        if not metrics:
            return {
                "agent": name,
                "count": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "total_tokens": 0
            }
        
        successful = sum(1 for m in metrics if m["success"])
        total_latency = sum(m["latency_ms"] for m in metrics)
        total_tokens = sum(m.get("tokens", 0) for m in metrics)
        
        return {
            "agent": name,
            "count": len(metrics),
            "success_rate": successful / len(metrics) * 100,
            "avg_latency_ms": total_latency / len(metrics),
            "total_tokens": total_tokens,
            "last_updated": metrics[-1]["timestamp"] if metrics else None
        }

    def _load_metrics(self):
        """Load metrics from file"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r") as f:
                    data = json.load(f)
                    self.metrics = defaultdict(list, data)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(dict(self.metrics), f, indent=2)
        except IOError:
            pass

    def reset(self):
        """Clear all metrics"""
        self.metrics.clear()
        self._save_metrics()


# Global instance
metrics_collector = MetricsCollector()


# Helper functions for backward compatibility and ease of use
def record_latency(agent_name: str, latency_ms: float, success: bool = True, tokens: int = 0, error: Optional[str] = None, tags: Optional[Dict[str, Any]] = None):
    metrics_collector.record_message(agent_name, latency_ms, success, tokens, error)


def increment(metric_name: str, value: int = 1, tags: Optional[Dict[str, Any]] = None):
    # For now, we just record it as a generic metric or log it
    # In a real system, this would go to Prometheus/StatsD
    pass


def ensure_trace(trace_id: str):
    # No-op for now, or could initialize trace storage
    pass


def accumulate_trace_time(trace_id: str, latency_ms: float):
    # No-op for now, or could aggregate total trace time
    pass


def gauge(metric_name: str, value: float, tags: Optional[Dict[str, Any]] = None):
    # For now, we just record it as a generic metric or log it
    pass
