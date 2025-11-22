"""
Enhanced Evaluation Harness
Direct capture of agent predictions and routing decisions for reliable metrics
"""

import asyncio
import uuid
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class PredictionCapture:
    """Structured prediction capture"""
    timestamp: str
    agent: str
    prediction_type: str  # intent, sentiment, priority, routing
    prediction: Any
    ground_truth: Any
    correct: bool
    latency_ms: float
    metadata: Dict[str, Any]

class EvaluationHarness:
    """
    Enhanced evaluation harness with direct prediction capture
    """
    
    def __init__(self):
        self.predictions: List[PredictionCapture] = []
        self.start_time = None
        self.end_time = None
    
    def capture(
        self,
        agent: str,
        prediction_type: str,
        prediction: Any,
        ground_truth: Any,
        latency_ms: float,
        **metadata
    ):
        """
        Capture a prediction directly from an agent
        
        Args:
            agent: Agent name
            prediction_type: Type of prediction
            prediction: Predicted value
            ground_truth: Actual/expected value
            latency_ms: Prediction latency in milliseconds
            **metadata: Additional context
        """
        capture = PredictionCapture(
            timestamp=str(datetime.datetime.utcnow()),
            agent=agent,
            prediction_type=prediction_type,
            prediction=prediction,
            ground_truth=ground_truth,
            correct=(prediction == ground_truth),
            latency_ms=latency_ms,
            metadata=metadata
        )
        
        self.predictions.append(capture)
    
    def get_accuracy(self, prediction_type: str = None, agent: str = None) -> float:
        """
        Calculate accuracy for predictions
        
        Args:
            prediction_type: Filter by type (optional)
            agent: Filter by agent (optional)
            
        Returns:
            Accuracy as float between 0 and 1
        """
        filtered = self.predictions
        
        if prediction_type:
            filtered = [p for p in filtered if p.prediction_type == prediction_type]
        
        if agent:
            filtered = [p for p in filtered if p.agent == agent]
        
        if not filtered:
            return 0.0
        
        correct = sum(1 for p in filtered if p.correct)
        return correct / len(filtered)
    
    def get_avg_latency(self, prediction_type: str = None) -> float:
        """Get average latency in milliseconds"""
        filtered = self.predictions
        
        if prediction_type:
            filtered = [p for p in filtered if p.prediction_type == prediction_type]
        
        if not filtered:
            return 0.0
        
        return sum(p.latency_ms for p in filtered) / len(filtered)
    
    def get_metrics_by_type(self) -> Dict[str, Dict[str, float]]:
        """Get accuracy and latency metrics grouped by prediction type"""
        types = set(p.prediction_type for p in self.predictions)
        
        metrics = {}
        for pred_type in types:
            metrics[pred_type] = {
                "accuracy": self.get_accuracy(prediction_type=pred_type),
                "avg_latency_ms": self.get_avg_latency(prediction_type=pred_type),
                "count": sum(1 for p in self.predictions if p.prediction_type == pred_type)
            }
        
        return metrics
    
    def save_results(self, filepath: str):
        """Save evaluation results to JSON file"""
        results = {
            "summary": {
                "total_predictions": len(self.predictions),
                "overall_accuracy": self.get_accuracy(),
                "avg_latency_ms": self.get_avg_latency(),
                "start_time": self.start_time,
                "end_time": self.end_time
            },
            "by_type": self.get_metrics_by_type(),
            "predictions": [asdict(p) for p in self.predictions]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
    
    def print_summary(self):
        """Print evaluation summary to console"""
        print("=" * 70)
        print("Evaluation Results")
        print("=" * 70)
        print(f"Total Predictions: {len(self.predictions)}")
        print(f"Overall Accuracy: {self.get_accuracy():.2%}")
        print(f"Average Latency: {self.get_avg_latency():.2f}ms")
        print()
        
        print("By Prediction Type:")
        print("-" * 70)
        metrics = self.get_metrics_by_type()
        for pred_type, vals in metrics.items():
            print(f"  {pred_type}:")
            print(f"    Accuracy: {vals['accuracy']:.2%}")
            print(f"    Avg Latency: {vals['avg_latency_ms']:.2f}ms")
            print(f"    Count: {vals['count']}")
            print()

# Global harness instance
harness = EvaluationHarness()

def get_harness() -> EvaluationHarness:
    """Get the global evaluation harness"""
    return harness
