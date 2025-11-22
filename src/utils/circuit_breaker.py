"""
Circuit Breaker Pattern Implementation
Provides fault tolerance and prevents cascading failures in distributed systems
"""

import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

from utils.logging_utils import log_event


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for network calls with configurable thresholds
    """

    def __init__(
        self, failure_threshold: int = 5, timeout: int = 60, expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

        log_event(
            "CircuitBreaker",
            {"event": "initialized", "threshold": failure_threshold, "timeout": timeout},
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                log_event(
                    "CircuitBreaker", {"event": "state_change", "from": "open", "to": "half_open"}
                )
            else:
                raise RuntimeError("Circuit breaker is OPEN - calls are blocked")

        try:
            result = func(*args, **kwargs)

            # Success - reset if in half-open state
            if self.state == CircuitState.HALF_OPEN:
                self._reset()

            return result

        except self.expected_exception as e:  # type: ignore[misc]
            self._record_failure()
            raise e

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call()"""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN - calls are blocked")

        try:
            result = await func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self._reset()

            return result

        except self.expected_exception as e:  # type: ignore[misc]
            self._record_failure()
            raise e

    def _record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            log_event(
                "CircuitBreaker",
                {
                    "event": "circuit_opened",
                    "failure_count": self.failure_count,
                    "threshold": self.failure_threshold,
                },
            )

    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

        log_event(
            "CircuitBreaker",
            {"event": "circuit_closed", "message": "Circuit breaker reset to normal operation"},
        )


def circuit_breaker(failure_threshold: int = 5, timeout: int = 60):
    """
    Decorator for circuit breaker protection

    Usage:
        @circuit_breaker(failure_threshold=3, timeout=30)
        def my_network_call():
            # ... network operation ...
            pass
    """
    cb = CircuitBreaker(failure_threshold=failure_threshold, timeout=timeout)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await cb.call_async(func, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
