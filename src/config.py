import os
from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    """Centralized system configuration."""

    # API Keys & Models
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    gemini_model_name: str = "gemini-1.5-flash"

    # Risk Thresholds
    refund_risk_threshold_high: float = 0.8
    refund_risk_threshold_medium: float = 0.5

    # Priority Thresholds
    priority_threshold_high: float = 0.8
    priority_threshold_medium: float = 0.5

    # Tracing
    enable_tracing: bool = True
    trace_file: str = "traces.jsonl"

    # Retry Settings
    max_retries: int = 3
    base_delay: float = 1.0


# Global config instance
config = SystemConfig()
