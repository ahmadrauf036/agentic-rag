"""
Resilience wrappers for external service calls (Groq, Chroma). Retries
transient failures with exponential backoff; a simple in-process circuit
breaker stops hammering a service that's clearly down, failing fast
instead of making every request wait through a doomed retry cycle.
"""

import logging
import time

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at > self.cooldown_seconds:
            self._opened_at = None
            self._consecutive_failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._opened_at = time.monotonic()
            logger.warning("Circuit breaker opened after %d consecutive failures", self._consecutive_failures)


chroma_breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=30)


def with_chroma_resilience(func):
    """Decorator: retry transient Chroma failures with backoff, respecting a circuit breaker."""
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        if chroma_breaker.is_open():
            raise RuntimeError("Chroma service temporarily unavailable (circuit breaker open) — please try again shortly.")
        try:
            result = func(*args, **kwargs)
            chroma_breaker.record_success()
            return result
        except Exception:
            chroma_breaker.record_failure()
            raise
    return wrapper