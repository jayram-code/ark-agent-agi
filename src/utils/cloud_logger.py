"""
Enhanced Centralized Logging
Cloud-ready structured logging with multiple sinks
"""

import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class CloudLogger:
    """
    Centralized logging with cloud sink support
    Supports: JSON formatting, multiple sinks, structured metadata
    """

    def __init__(
        self,
        log_level: str = "INFO",
        log_format: str = "json",
        sink: str = "file",
        log_dir: str = "logs",
    ):
        """
        Initialize cloud logger

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Format (json or text)
            sink: Destination (file, stackdriver, cloudwatch, splunk, stdout)
            log_dir: Directory for file logs
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_format = log_format
        self.sink = sink
        self.log_dir = Path(log_dir)

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logger
        self.logger = logging.getLogger("ark_agent_agi")
        self.logger.setLevel(self.log_level)

        # Remove existing handlers
        self.logger.handlers = []

        # Add appropriate handler based on sink
        self._setup_handler()

    def _setup_handler(self):
        """Set up logging handler based on sink configuration"""
        if self.sink == "stdout":
            handler = logging.StreamHandler(sys.stdout)
        elif self.sink in ["stackdriver", "cloudwatch", "splunk"]:
            # In production, integrate with actual cloud logging SDKs
            # For now, write to file with cloud-ready format
            log_file = self.log_dir / f"cloud_{self.sink}.jsonl"
            handler = logging.FileHandler(log_file)
        else:  # default to file
            log_file = self.log_dir / "app.log"
            handler = logging.FileHandler(log_file)

        # Set formatter based on format
        if self.log_format == "json":
            handler.setFormatter(JSONFormatter())
        else:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def log(self, level: str, message: str, **metadata):
        """
        Log a message with structured metadata

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **metadata: Additional structured data
        """
        log_method = getattr(self.logger, level.lower())

        if self.log_format == "json":
            # Include metadata in extra for JSON formatter
            log_method(message, extra={"metadata": metadata})
        else:
            # Append metadata to message for text format
            if metadata:
                message = f"{message} | {json.dumps(metadata)}"
            log_method(message)

    def debug(self, message: str, **metadata):
        """Log debug message"""
        self.log("debug", message, **metadata)

    def info(self, message: str, **metadata):
        """Log info message"""
        self.log("info", message, **metadata)

    def warning(self, message: str, **metadata):
        """Log warning message"""
        self.log("warning", message, **metadata)

    def error(self, message: str, **metadata):
        """Log error message"""
        self.log("error", message, **metadata)

    def critical(self, message: str, **metadata):
        """Log critical message"""
        self.log("critical", message, **metadata)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add metadata if present
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Global logger instance
try:
    from config.environment import get_config

    env_config = get_config()
    cloud_logger = CloudLogger(
        log_level=env_config.log_level,
        log_format=env_config.log_format,
        sink=env_config.centralized_log_sink or "file",
    )
except Exception:
    # Fallback to default config if environment not available
    cloud_logger = CloudLogger()


def get_logger() -> CloudLogger:
    """Get the global cloud logger instance"""
    return cloud_logger
