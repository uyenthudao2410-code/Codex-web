from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable

from .envutils import ENV_PREFIX


PROVIDER_LIMITS_ENV = f"{ENV_PREFIX}_PROVIDER_LIMITS_JSON"
WINDOW_SECONDS = 60.0
_ALLOWED_LIMIT_KEYS = frozenset({"rpm", "tpm", "concurrency"})


def _positive_limit(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


class ProviderTrafficGovernor:
    """Runtime-scoped admission guard for explicitly configured provider limits.

    Unknown provider quotas stay unknown. When no limit is configured for a model,
    manual provider dispatch remains observe-only and is not blocked. Automatic
    routing is controlled elsewhere and is deliberately not enabled by this class.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        configuration_error: str = "",
    ) -> None:
        self._clock = clock
        self._lock = threading.RLock()
        self._limits: dict[str, dict[str, int | None]] = {}
        self._errors: dict[str, str] = {}
        self._configuration_error = str(configuration_error or "")[:300]
        self._reservations: dict[str, dict[str, Any]] = {}
        for raw_model, raw_limits in (config or {}).items():
            model = str(raw_model or "").strip()
            if not model:
                continue
            if not isinstance(raw_limits, dict):
                self._errors[model] = "provider limits must be an object"
                continue
            unexpected = sorted(set(raw_limits) - _ALLOWED_LIMIT_KEYS)
            if unexpected:
                self._errors[model] = "unsupported provider limit fields: " + ", ".join(unexpected[:5])
                continue
            try:
                limits = {
                    "rpm": _positive_limit(raw_limits.get("rpm"), "rpm"),
                    "tpm": _positive_limit(raw_limits.get("tpm"), "tpm"),
                    "concurrency": _positive_limit(raw_limits.get("concurrency"), "concurrency"),
                }
            except ValueError as exc:
                self._errors[model] = str(exc)
                continue
            if any(value is not None for value in limits.values()):
                self._limits[model] = limits

    @classmethod
    def from_env(cls) -> "ProviderTrafficGovernor":
        raw = str(os.environ.get(PROVIDER_LIMITS_ENV) or "").strip()
        if not raw:
            return cls({})
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return cls({}, configuration_error=f"{PROVIDER_LIMITS_ENV} must be a JSON object")
        if not isinstance(parsed, dict):
            return cls({}, configuration_error=f"{PROVIDER_LIMITS_ENV} must be a JSON object")
        return cls(parsed)

    def _cleanup_locked(self, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        expired = [
            key for key, item in self._reservations.items()
            if not item.get("active") and float(item.get("created_at", 0.0)) < cutoff
        ]
        for key in expired:
            self._reservations.pop(key, None)

    def _usage_locked(self, model: str, now: float) -> tuple[list[dict[str, Any]], int, int, int]:
        cutoff = now - WINDOW_SECONDS
        model_rows = [item for item in self._reservations.values() if item.get("model") == model]
        window_rows = [item for item in model_rows if float(item.get("created_at", 0.0)) >= cutoff]
        requests = len(window_rows)
        tokens = sum(max(0, int(item.get("token_budget") or 0)) for item in window_rows)
        active = sum(1 for item in model_rows if item.get("active"))
        return window_rows, requests, tokens, active

    @staticmethod
    def _remaining(limits: dict[str, int | None], requests: int, tokens: int, active: int) -> dict[str, int | None]:
        return {
            "rpm": None if limits.get("rpm") is None else max(0, int(limits["rpm"] or 0) - requests),
            "tpm": None if limits.get("tpm") is None else max(0, int(limits["tpm"] or 0) - tokens),
            "concurrency": None if limits.get("concurrency") is None else max(0, int(limits["concurrency"] or 0) - active),
        }

    @staticmethod
    def _window_retry_after_ms(rows: list[dict[str, Any]], now: float) -> int | None:
        if not rows:
            return None
        oldest = min(float(item.get("created_at", now)) for item in rows)
        return max(1, int(max(0.0, oldest + WINDOW_SECONDS - now) * 1000))

    @staticmethod
    def _tpm_retry_after_ms(rows: list[dict[str, Any]], now: float, current_tokens: int, requested: int, limit: int) -> int | None:
        remaining = current_tokens
        for item in sorted(rows, key=lambda row: float(row.get("created_at", 0.0))):
            remaining -= max(0, int(item.get("token_budget") or 0))
            if remaining + requested <= limit:
                return max(1, int(max(0.0, float(item.get("created_at", now)) + WINDOW_SECONDS - now) * 1000))
        return None

    def _decision(
        self,
        *,
        model: str,
        allowed: bool,
        mode: str,
        reason: str,
        limits: dict[str, int | None] | None = None,
        requests: int = 0,
        tokens: int = 0,
        active: int = 0,
        retry_after_ms: int | None = None,
        deduplicated: bool = False,
    ) -> dict[str, Any]:
        limits = limits or {"rpm": None, "tpm": None, "concurrency": None}
        return {
            "schema_version": 1,
            "provider_model": model,
            "allowed": allowed,
            "mode": mode,
            "reason": reason,
            "deduplicated": deduplicated,
            "limits": dict(limits),
            "usage": {
                "requests_last_minute": requests,
                "reserved_tokens_last_minute": tokens,
                "active_requests": active,
            },
            "remaining": self._remaining(limits, requests, tokens, active),
            "retry_after_ms": retry_after_ms,
            "token_basis": "configured_request_budget" if limits.get("tpm") is not None else "unobserved",
        }

    def admit(self, model: str, request_key: str, *, token_budget: int | None = None) -> dict[str, Any]:
        model = str(model or "").strip()
        key = str(request_key or "").strip()
        if token_budget is not None and (isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget < 0):
            return self._decision(model=model, allowed=False, mode="enforced", reason="invalid_token_budget")
        with self._lock:
            now = float(self._clock())
            self._cleanup_locked(now)
            if self._configuration_error:
                return self._decision(model=model, allowed=False, mode="invalid", reason="invalid_configuration")
            if model in self._errors:
                return self._decision(model=model, allowed=False, mode="invalid", reason="invalid_configuration")
            limits = self._limits.get(model)
            if limits is None:
                return self._decision(model=model, allowed=True, mode="observe_only", reason="limits_unconfigured")
            if not key:
                return self._decision(model=model, allowed=False, mode="enforced", reason="request_identity_required", limits=limits)
            existing = self._reservations.get(key)
            if existing is not None:
                if existing.get("model") != model:
                    return self._decision(model=model, allowed=False, mode="enforced", reason="request_identity_conflict", limits=limits)
                rows, requests, tokens, active = self._usage_locked(model, now)
                return self._decision(
                    model=model,
                    allowed=True,
                    mode="enforced",
                    reason="deduplicated",
                    limits=limits,
                    requests=requests,
                    tokens=tokens,
                    active=active,
                    deduplicated=True,
                )
            if limits.get("tpm") is not None and token_budget is None:
                rows, requests, tokens, active = self._usage_locked(model, now)
                return self._decision(
                    model=model, allowed=False, mode="enforced", reason="token_budget_required",
                    limits=limits, requests=requests, tokens=tokens, active=active,
                )
            requested_tokens = max(0, int(token_budget or 0))
            if limits.get("tpm") is not None and requested_tokens > int(limits["tpm"] or 0):
                rows, requests, tokens, active = self._usage_locked(model, now)
                return self._decision(
                    model=model, allowed=False, mode="enforced", reason="token_budget_exceeds_limit",
                    limits=limits, requests=requests, tokens=tokens, active=active,
                )
            rows, requests, tokens, active = self._usage_locked(model, now)
            concurrency = limits.get("concurrency")
            if concurrency is not None and active >= concurrency:
                return self._decision(
                    model=model, allowed=False, mode="enforced", reason="concurrency_exhausted",
                    limits=limits, requests=requests, tokens=tokens, active=active,
                )
            rpm = limits.get("rpm")
            if rpm is not None and requests >= rpm:
                return self._decision(
                    model=model, allowed=False, mode="enforced", reason="rpm_exhausted",
                    limits=limits, requests=requests, tokens=tokens, active=active,
                    retry_after_ms=self._window_retry_after_ms(rows, now),
                )
            tpm = limits.get("tpm")
            if tpm is not None and tokens + requested_tokens > tpm:
                return self._decision(
                    model=model, allowed=False, mode="enforced", reason="tpm_exhausted",
                    limits=limits, requests=requests, tokens=tokens, active=active,
                    retry_after_ms=self._tpm_retry_after_ms(rows, now, tokens, requested_tokens, tpm),
                )
            self._reservations[key] = {
                "model": model,
                "created_at": now,
                "token_budget": requested_tokens,
                "active": True,
            }
            _rows, requests, tokens, active = self._usage_locked(model, now)
            return self._decision(
                model=model, allowed=True, mode="enforced", reason="admitted",
                limits=limits, requests=requests, tokens=tokens, active=active,
            )

    def complete(self, request_key: str) -> bool:
        key = str(request_key or "").strip()
        if not key:
            return False
        with self._lock:
            item = self._reservations.get(key)
            if item is None:
                return False
            item["active"] = False
            item["completed_at"] = float(self._clock())
            return True

    def abort(self, request_key: str) -> bool:
        key = str(request_key or "").strip()
        if not key:
            return False
        with self._lock:
            return self._reservations.pop(key, None) is not None

    def snapshot(self, *, models: list[str] | tuple[str, ...] | set[str] | None = None) -> dict[str, Any]:
        with self._lock:
            now = float(self._clock())
            self._cleanup_locked(now)
            requested_models = {str(item) for item in (models or []) if str(item).strip()}
            requested_models.update(self._limits)
            requested_models.update(self._errors)
            providers: list[dict[str, Any]] = []
            for model in sorted(requested_models):
                limits = self._limits.get(model)
                _rows, requests, tokens, active = self._usage_locked(model, now)
                if self._configuration_error or model in self._errors:
                    mode = "invalid"
                    reason = "invalid_configuration"
                elif limits is None:
                    mode = "observe_only"
                    reason = "limits_unconfigured"
                    limits = {"rpm": None, "tpm": None, "concurrency": None}
                else:
                    mode = "enforced"
                    reason = "configured_limits"
                providers.append({
                    **self._decision(
                        model=model, allowed=mode != "invalid", mode=mode, reason=reason,
                        limits=limits, requests=requests, tokens=tokens, active=active,
                    ),
                    "configuration_error": self._configuration_error or self._errors.get(model),
                })
            status = "invalid" if self._configuration_error or self._errors else "configured" if self._limits else "unconfigured"
            return {
                "schema_version": 1,
                "window_seconds": int(WINDOW_SECONDS),
                "configuration": {
                    "source": PROVIDER_LIMITS_ENV,
                    "status": status,
                    "error": self._configuration_error or None,
                    "invalid_models": sorted(self._errors),
                },
                "providers": providers,
            }
