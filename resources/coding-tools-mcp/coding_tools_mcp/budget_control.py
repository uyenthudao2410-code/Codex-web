from __future__ import annotations

import random
import time
from typing import Any

from .errors import ToolFailure


class RetryPolicy:
    """Capped exponential backoff with jitter for side-effect-free retries.

    Mutating tools never auto-retry: retrying a write can duplicate side
    effects. This policy is applied only to read-only handlers and to
    idempotent-safe transient failures.
    """

    def __init__(
        self,
        *,
        max_attempts: int = 1,
        base_delay_seconds: float = 0.25,
        max_delay_seconds: float = 2.0,
        jitter: float = 0.25,
    ) -> None:
        self.max_attempts = max(1, max_attempts)
        self.base_delay_seconds = max(0.0, base_delay_seconds)
        self.max_delay_seconds = max(self.base_delay_seconds, max_delay_seconds)
        self.jitter = max(0.0, min(0.9, jitter))

    def delay_for(self, failure_count: int) -> float:
        exponent = min(max(failure_count - 1, 0), 8)
        delay = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** exponent))
        if self.jitter > 0:
            delay *= 1.0 + random.uniform(-self.jitter, self.jitter)
        return max(0.0, delay)

    def should_retry(self, failure_count: int) -> bool:
        return failure_count < self.max_attempts

    def describe(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "jitter": self.jitter,
        }


class BudgetDeadline:
    """Unified wall-clock + inactivity budget for durable operations.

    ``touch()`` records progress activity. ``check()`` raises a terminal
    ToolFailure once a budget is exhausted so the durable operation can be
    marked failed instead of running forever.
    """

    def __init__(
        self,
        *,
        max_runtime_seconds: float,
        inactivity_timeout_seconds: float = 0.0,
    ) -> None:
        self.max_runtime_seconds = max(0.001, max_runtime_seconds)
        self.inactivity_timeout_seconds = max(0.0, inactivity_timeout_seconds)
        self.started_monotonic = time.monotonic()
        self.last_activity_monotonic = self.started_monotonic
        self.exceeded: str | None = None

    def touch(self) -> None:
        self.last_activity_monotonic = time.monotonic()

    def check(self) -> None:
        now = time.monotonic()
        if now - self.started_monotonic > self.max_runtime_seconds:
            self.exceeded = "runtime"
            raise ToolFailure(
                "WORKFLOW_RUNTIME_EXCEEDED",
                "The durable operation exceeded its wall-clock runtime budget.",
                category="policy",
                retryable=False,
                details={
                    "max_runtime_seconds": self.max_runtime_seconds,
                    "elapsed_seconds": round(now - self.started_monotonic, 3),
                },
            )
        if self.inactivity_timeout_seconds > 0 and (
            now - self.last_activity_monotonic > self.inactivity_timeout_seconds
        ):
            self.exceeded = "inactivity"
            raise ToolFailure(
                "WORKFLOW_INACTIVITY_EXCEEDED",
                "The durable operation made no progress within the inactivity budget.",
                category="policy",
                retryable=False,
                details={
                    "inactivity_timeout_seconds": self.inactivity_timeout_seconds,
                    "idle_seconds": round(now - self.last_activity_monotonic, 3),
                },
            )

    def remaining_seconds(self) -> float:
        return max(0.0, self.max_runtime_seconds - (time.monotonic() - self.started_monotonic))
