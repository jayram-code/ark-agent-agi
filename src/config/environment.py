"""
Centralized Environment Configuration
Loads and validates all environment variables with type safety
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


@dataclass
class EnvironmentConfig:
    """Type-safe environment configuration"""

    # Required
    google_api_key: str

    # Core Settings
    log_level: str = "INFO"
    log_format: str = "json"
    enable_tracing: bool = True

    # Database
    db_path: str = "data/ark_agent.db"
    memories_db_path: str = "data/memories.db"

    # Built-in Tools (Optional)
    google_search_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    openweather_api_key: Optional[str] = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    # External Integrations (Optional)
    shipping_api_url: Optional[str] = None
    shipping_api_key: Optional[str] = None
    crm_api_url: Optional[str] = None
    crm_api_key: Optional[str] = None

    # Infrastructure
    centralized_log_sink: Optional[str] = None
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    rate_limit_calls_per_second: int = 10

    @classmethod
    def from_env(cls) -> "EnvironmentConfig":
        """Load configuration from environment variables"""

        # Required validation
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required. "
                "Set it in your .env file or environment variables. "
                "See .env.example for template."
            )

        return cls(
            google_api_key=google_api_key,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            db_path=os.getenv("DB_PATH", "data/ark_agent.db"),
            memories_db_path=os.getenv("MEMORIES_DB_PATH", "data/memories.db"),
            google_search_api_key=os.getenv("GOOGLE_SEARCH_API_KEY"),
            google_cse_id=os.getenv("GOOGLE_CSE_ID"),
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            shipping_api_url=os.getenv("SHIPPING_API_URL"),
            shipping_api_key=os.getenv("SHIPPING_API_KEY"),
            crm_api_url=os.getenv("CRM_API_URL"),
            crm_api_key=os.getenv("CRM_API_KEY"),
            centralized_log_sink=os.getenv("CENTRALIZED_LOG_SINK"),
            circuit_breaker_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
            circuit_breaker_timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),
            rate_limit_calls_per_second=int(os.getenv("RATE_LIMIT_CALLS_PER_SECOND", "10")),
        )

    def validate(self) -> None:
        """Validate configuration values"""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid LOG_LEVEL: {self.log_level}")

        if self.log_format not in ["json", "text"]:
            raise ValueError(f"Invalid LOG_FORMAT: {self.log_format}")

        if self.circuit_breaker_threshold < 1:
            raise ValueError("CIRCUIT_BREAKER_THRESHOLD must be >= 1")

        if self.rate_limit_calls_per_second < 1:
            raise ValueError("RATE_LIMIT_CALLS_PER_SECOND must be >= 1")


# Global configuration instance
try:
    env_config = EnvironmentConfig.from_env()
    env_config.validate()
except ValueError as e:
    print(f"⚠️  Environment Configuration Error: {e}")
    print("⚠️  Using default configuration. Some features may not work.")
    # Create minimal config with defaults
    env_config = EnvironmentConfig(google_api_key=os.getenv("GOOGLE_API_KEY", ""))


def get_config() -> EnvironmentConfig:
    """Get the global environment configuration"""
    return env_config
