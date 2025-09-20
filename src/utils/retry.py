"""Reusable retry utilities with exponential backoff and circuit breaker support."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Tuple, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a circuit breaker is open and retries are short-circuited."""

    def __init__(self, key: str, retry_after: float, last_exception: Optional[BaseException] = None):
        message = (
            f"Circuit breaker open for '{key}'. Retry after {retry_after:.2f}s"
            if retry_after > 0
            else f"Circuit breaker open for '{key}'. Retry later"
        )
        super().__init__(message)
        self.key = key
        self.retry_after = retry_after
        self.last_exception = last_exception


@dataclass
class _BreakerState:
    failures: int = 0
    opened_at: float = 0.0


class CircuitBreaker:
    """Simple in-process circuit breaker with fixed recovery window."""

    def __init__(self, *, failure_threshold: int = 3, recovery_time: float = 30.0):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_time <= 0:
            raise ValueError("recovery_time must be > 0")
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self._states: dict[str, _BreakerState] = {}

    def _state(self, key: str) -> _BreakerState:
        state = self._states.get(key)
        if state is None:
            state = _BreakerState()
            self._states[key] = state
        return state

    def allow(self, key: str) -> bool:
        state = self._states.get(key)
        if state is None or state.failures < self.failure_threshold:
            return True

        elapsed = time.monotonic() - state.opened_at
        if elapsed >= self.recovery_time:
            self.reset(key)
            return True

        return False

    def record_failure(self, key: str) -> bool:
        state = self._state(key)
        state.failures += 1
        if state.failures >= self.failure_threshold and state.opened_at == 0.0:
            state.opened_at = time.monotonic()
            return True
        return state.opened_at != 0.0

    def record_success(self, key: str) -> None:
        self.reset(key)

    def reset(self, key: str) -> None:
        self._states[key] = _BreakerState()

    def cooldown_remaining(self, key: str) -> float:
        state = self._states.get(key)
        if state is None or state.opened_at == 0.0:
            return 0.0
        elapsed = time.monotonic() - state.opened_at
        remaining = max(0.0, self.recovery_time - elapsed)
        if remaining == 0.0:
            self.reset(key)
        return remaining


RetryableExceptions = Tuple[type[BaseException], ...]


async def async_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    operation_name: str,
    logger: logging.Logger,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    multiplier: float = 2.0,
    jitter: float = 0.25,
    retryable_exceptions: RetryableExceptions = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
    breaker_key: Optional[str] = None,
) -> T:
    """Retry an async operation with exponential backoff and optional circuit breaker."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if multiplier < 1:
        raise ValueError("multiplier must be >= 1")
    if circuit_breaker and not breaker_key:
        raise ValueError("breaker_key must be provided when circuit_breaker is set")

    attempt = 0
    last_exception: Optional[BaseException] = None

    while attempt < max_attempts:
        attempt += 1

        if circuit_breaker and breaker_key and not circuit_breaker.allow(breaker_key):
            retry_after = circuit_breaker.cooldown_remaining(breaker_key)
            raise CircuitBreakerOpenError(breaker_key, retry_after, last_exception)

        try:
            result = await operation()
        except retryable_exceptions as exc:  # type: ignore[arg-type]
            last_exception = exc
            breaker_opened = False
            if circuit_breaker and breaker_key:
                breaker_opened = circuit_breaker.record_failure(breaker_key)

            retry_context = {
                "operation": operation_name,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "breaker_opened": breaker_opened,
            }
            logger.warning(
                "Retryable error during %s (attempt %d/%d)",
                operation_name,
                attempt,
                max_attempts,
                extra={"event": f"retry.{operation_name}", **retry_context},
                exc_info=True,
            )

            if breaker_opened:
                retry_after = circuit_breaker.cooldown_remaining(breaker_key)
                raise CircuitBreakerOpenError(breaker_key, retry_after, exc) from exc

            if attempt >= max_attempts:
                raise

            delay = min(max_delay, base_delay * (multiplier ** (attempt - 1)))
            if jitter > 0:
                delay += random.uniform(0, jitter)
            await asyncio.sleep(delay)
            continue
        except BaseException:  # pragma: no cover - propagate cancellation/system exits
            raise
        else:
            if circuit_breaker and breaker_key:
                circuit_breaker.record_success(breaker_key)
            return result

    assert last_exception is not None  # for mypy/static expectations
    raise last_exception


LLM_CIRCUIT_BREAKER = CircuitBreaker(failure_threshold=3, recovery_time=45.0)
