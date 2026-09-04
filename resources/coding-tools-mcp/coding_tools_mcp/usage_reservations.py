from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


RESERVATION_EVENT_TYPES = frozenset({
    "usage_reservation_reserved",
    "usage_reservation_indeterminate",
    "usage_reservation_reconciled",
    "usage_reservation_aborted",
})


class UsageReservationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = str(code)


class UsageReservationStore:
    """Durable token reservation authority backed by the canonical event ledger.

    Reservations are estimates only. Exact usage enters this lifecycle only through
    reconcile(), and absent exact usage is represented as indeterminate rather than
    zero. ProviderTrafficGovernor remains a separate runtime-local quota mechanism.
    """

    def __init__(self, ledger: Any, *, clock_ms: Callable[[], int] | None = None) -> None:
        self._ledger = ledger
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))

    @staticmethod
    def _units(value: Any, *, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise UsageReservationError("USAGE_RESERVATION_INVALID", f"{field} must be a non-negative integer")
        return value

    @staticmethod
    def _text(value: Any, *, field: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise UsageReservationError("USAGE_RESERVATION_INVALID", f"{field} is required")
        return text

    @staticmethod
    def _event_measurement(payload: dict[str, Any], key: str, expected: str, *, allow_none: bool = False) -> int | None:
        measured = payload.get(key)
        if not isinstance(measured, dict) or measured.get("unit") != "tokens" or measured.get("measurement") != expected:
            raise UsageReservationError("USAGE_RESERVATION_CORRUPT", f"invalid {key} measurement")
        units = measured.get("units")
        if units is None and allow_none:
            return None
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise UsageReservationError("USAGE_RESERVATION_CORRUPT", f"invalid {key} units")
        return units

    def get(self, run_id: str, reservation_id: str) -> dict[str, Any] | None:
        run = self._text(run_id, field="run_id")
        expected_id = self._text(reservation_id, field="reservation_id")
        state: dict[str, Any] | None = None
        for event in self._ledger.list_events(run):
            event_type = str(event.get("event_type") or "")
            if event_type not in RESERVATION_EVENT_TYPES:
                continue
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            if str(payload.get("reservation_id") or "") != expected_id:
                continue
            wave_id = str(event.get("wave_id") or "").strip()
            if event_type == "usage_reservation_reserved":
                reserved_units = self._event_measurement(payload, "reservation", "estimated")
                candidate = {
                    "schema_version": 1,
                    "reservation_id": expected_id,
                    "run_id": run,
                    "wave_id": self._text(wave_id, field="wave_id"),
                    "request_id": self._text(payload.get("request_id"), field="request_id"),
                    "provider_model": self._text(payload.get("provider_model"), field="provider_model"),
                    "status": "reserved",
                    "reservation": {"unit": "tokens", "units": reserved_units, "measurement": "estimated"},
                    "actual": None,
                    "usage_id": "",
                    "reason": "",
                    "expires_at_unix_ms": payload.get("expires_at_unix_ms"),
                }
                expiry = candidate["expires_at_unix_ms"]
                if expiry is not None and (isinstance(expiry, bool) or not isinstance(expiry, int) or expiry <= 0):
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "invalid reservation expiry")
                if state is None:
                    state = candidate
                    continue
                comparable = ("wave_id", "request_id", "provider_model", "reservation")
                if any(state.get(key) != candidate.get(key) for key in comparable):
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "conflicting reservation evidence")
                if state.get("status") != "reserved":
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "reservation reopened after terminal transition")
                continue
            if state is None or wave_id != state.get("wave_id"):
                raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "reservation transition has no matching base authority")
            if event_type == "usage_reservation_indeterminate":
                self._event_measurement(payload, "actual", "unobserved", allow_none=True)
                if state["status"] == "reconciled":
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "reconciled reservation regressed to indeterminate")
                if state["status"] == "aborted":
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "aborted reservation became indeterminate")
                state["status"] = "indeterminate"
                state["actual"] = {"unit": "tokens", "units": None, "measurement": "unobserved"}
                state["reason"] = str(payload.get("reason") or "exact_usage_unavailable")
                continue
            if event_type == "usage_reservation_reconciled":
                actual_units = self._event_measurement(payload, "actual", "measured")
                usage_id = self._text(payload.get("usage_id"), field="usage_id")
                if state["status"] == "aborted":
                    raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "aborted reservation was reconciled")
                if state["status"] == "reconciled":
                    if state["actual"] != {"unit": "tokens", "units": actual_units, "measurement": "measured"} or state["usage_id"] != usage_id:
                        raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "conflicting reconciliation evidence")
                    continue
                state["status"] = "reconciled"
                state["actual"] = {"unit": "tokens", "units": actual_units, "measurement": "measured"}
                state["usage_id"] = usage_id
                state["reason"] = ""
                continue
            if state["status"] not in {"reserved", "aborted"}:
                raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "terminal reservation was aborted after usage observation")
            state["status"] = "aborted"
            state["reason"] = str(payload.get("reason") or "dispatch_aborted")
        return state

    @staticmethod
    def _same_authority(state: dict[str, Any], *, wave_id: str, request_id: str, provider_model: str, reserved_units: int) -> bool:
        return (
            state.get("wave_id") == wave_id
            and state.get("request_id") == request_id
            and state.get("provider_model") == provider_model
            and (state.get("reservation") or {}).get("units") == reserved_units
        )

    def reserve(self, *, run_id: str, wave_id: str, reservation_id: str, request_id: str, provider_model: str, reserved_units: int, expires_at_unix_ms: int | None) -> dict[str, Any]:
        run = self._text(run_id, field="run_id")
        wave = self._text(wave_id, field="wave_id")
        reservation = self._text(reservation_id, field="reservation_id")
        request = self._text(request_id, field="request_id")
        model = self._text(provider_model, field="provider_model")
        units = self._units(reserved_units, field="reserved_units")
        if expires_at_unix_ms is not None:
            if isinstance(expires_at_unix_ms, bool) or not isinstance(expires_at_unix_ms, int) or expires_at_unix_ms <= self._clock_ms():
                raise UsageReservationError("USAGE_RESERVATION_STALE", "reservation expiry must be in the future")
        existing = self.get(run, reservation)
        if existing is not None:
            if not self._same_authority(existing, wave_id=wave, request_id=request, provider_model=model, reserved_units=units):
                raise UsageReservationError("USAGE_RESERVATION_CONFLICT", "reservation identity already exists with different authority")
            if existing["status"] != "reserved":
                raise UsageReservationError("USAGE_RESERVATION_STALE", f"reservation is already {existing['status']}")
            expiry = existing.get("expires_at_unix_ms")
            if expiry is not None and self._clock_ms() >= int(expiry):
                raise UsageReservationError("USAGE_RESERVATION_STALE", "reservation authority has expired")
            return {**existing, "changed": False}
        payload = {
            "schema_version": 1,
            "reservation_id": reservation,
            "request_id": request,
            "provider_model": model,
            "status": "reserved",
            "reservation": {"unit": "tokens", "units": units, "measurement": "estimated"},
            "expires_at_unix_ms": expires_at_unix_ms,
        }
        self._ledger.append_event(run, wave_id=wave, event_type="usage_reservation_reserved", payload=payload)
        created = self.get(run, reservation)
        if created is None:
            raise UsageReservationError("USAGE_RESERVATION_CORRUPT", "reservation event was not durably observable")
        return {**created, "changed": True}

    def require(self, *, run_id: str, wave_id: str, reservation_id: str, provider_model: str, allowed_statuses: tuple[str, ...] = ("reserved",), allow_expired: bool = False) -> dict[str, Any]:
        state = self.get(run_id, reservation_id)
        if state is None:
            raise UsageReservationError("USAGE_RESERVATION_MISSING", "durable usage reservation authority is missing")
        if state.get("wave_id") != self._text(wave_id, field="wave_id") or state.get("provider_model") != self._text(provider_model, field="provider_model"):
            raise UsageReservationError("USAGE_RESERVATION_STALE", "reservation authority does not match the current wave/model")
        if state.get("status") not in allowed_statuses:
            raise UsageReservationError("USAGE_RESERVATION_STALE", f"reservation status {state.get('status')} is not authorized")
        expiry = state.get("expires_at_unix_ms")
        if not allow_expired and expiry is not None and self._clock_ms() >= int(expiry):
            raise UsageReservationError("USAGE_RESERVATION_STALE", "reservation authority has expired")
        return state

    def mark_indeterminate(self, *, run_id: str, wave_id: str, reservation_id: str, provider_model: str, reason: str = "exact_usage_unavailable") -> dict[str, Any]:
        state = self.require(run_id=run_id, wave_id=wave_id, reservation_id=reservation_id, provider_model=provider_model, allowed_statuses=("reserved", "indeterminate", "reconciled"), allow_expired=True)
        if state["status"] in {"indeterminate", "reconciled"}:
            return {**state, "changed": False}
        self._ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type="usage_reservation_indeterminate",
            payload={"schema_version": 1, "reservation_id": reservation_id, "status": "indeterminate", "actual": {"unit": "tokens", "units": None, "measurement": "unobserved"}, "reason": str(reason or "exact_usage_unavailable")[:160]},
        )
        updated = self.get(run_id, reservation_id)
        return {**(updated or state), "changed": True}

    def reconcile(self, *, run_id: str, wave_id: str, reservation_id: str, provider_model: str, actual_units: int, usage_id: str) -> dict[str, Any]:
        units = self._units(actual_units, field="actual_units")
        exact_usage_id = self._text(usage_id, field="usage_id")
        state = self.require(run_id=run_id, wave_id=wave_id, reservation_id=reservation_id, provider_model=provider_model, allowed_statuses=("reserved", "indeterminate", "reconciled"), allow_expired=True)
        exact = {"unit": "tokens", "units": units, "measurement": "measured"}
        if state["status"] == "reconciled":
            if state.get("actual") != exact or state.get("usage_id") != exact_usage_id:
                raise UsageReservationError("USAGE_RESERVATION_CONFLICT", "reservation already reconciled with different exact usage")
            return {**state, "changed": False}
        self._ledger.append_event(run_id, wave_id=wave_id, event_type="usage_reservation_reconciled", payload={"schema_version": 1, "reservation_id": reservation_id, "status": "reconciled", "actual": exact, "usage_id": exact_usage_id})
        updated = self.get(run_id, reservation_id)
        return {**(updated or state), "changed": True}

    def abort(self, *, run_id: str, wave_id: str, reservation_id: str, provider_model: str, reason: str = "dispatch_aborted") -> dict[str, Any]:
        state = self.require(run_id=run_id, wave_id=wave_id, reservation_id=reservation_id, provider_model=provider_model, allowed_statuses=("reserved", "indeterminate", "reconciled", "aborted"), allow_expired=True)
        if state["status"] != "reserved":
            return {**state, "changed": False}
        self._ledger.append_event(run_id, wave_id=wave_id, event_type="usage_reservation_aborted", payload={"schema_version": 1, "reservation_id": reservation_id, "status": "aborted", "reason": str(reason or "dispatch_aborted")[:160]})
        updated = self.get(run_id, reservation_id)
        return {**(updated or state), "changed": True}
