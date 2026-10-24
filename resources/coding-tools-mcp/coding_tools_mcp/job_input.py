"""Interactive Job input contract (WebCodex §8 port, W5).

WebCodex's ``job_input`` contract gives every input sent to a running job a
caller-supplied ``input_id`` and a typed receipt, so that losing the
acknowledgement of a send can never silently turn into a duplicate send:

- first submission with an ``input_id`` performs the write exactly once and
  records the outcome;
- a retry with the same ``input_id`` returns the stored receipt and does
  NOT write again (``duplicate: true``);
- if the write itself fails part-way, the outcome is ``unknown`` — the
  bytes may or may not have landed — and a later retry still returns that
  ``unknown`` receipt instead of re-sending. Reconciliation is the caller's
  explicit decision, never an automatic replay;
- an input that was provably never written (for example the command had
  already exited) is recorded as ``rejected``, which is a definite outcome,
  not ``unknown``.

Receipts are kept in memory, bounded, per server instance. W5 introduced
this as an internal contract layer for Python-internal callers of
``SessionControlMixin.write_stdin`` / ``Server.command_control``. The
follow-up cluster opened it on the wire: ``input_id`` is now an optional
property (string, maxLength 128) of the ``command_control`` facade schema
and of the internal ``write_stdin`` tool schema, so MCP callers can use it
too. Adding the property changes the runtime-computed smart-v3 contract
SHA, so connector clients must rediscover and acknowledge the new
contract after release — that rediscovery is expected, not an error.
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Callable

OUTCOME_DELIVERED = "delivered"
OUTCOME_UNKNOWN = "unknown"
OUTCOME_REJECTED = "rejected"

MAX_INPUT_ID_CHARS = 128
DEFAULT_MAX_RECORDS = 512


def _receipt(
    *,
    session_id: str,
    input_id: str,
    outcome: str,
    data: bytes,
    duplicate: bool,
    reason: str = "",
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "input_id": input_id,
        "session_id": session_id,
        "outcome": outcome,
        "duplicate": duplicate,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "recorded_at": time.time(),
    }
    if reason:
        receipt["reason"] = reason
    return receipt


class JobInputLedger:
    """Exactly-once record of interactive inputs for running jobs."""

    def __init__(self, max_records: int = DEFAULT_MAX_RECORDS) -> None:
        self._max_records = max(1, int(max_records))
        self._records: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _store(self, receipt: dict[str, Any]) -> dict[str, Any]:
        key = (receipt["session_id"], receipt["input_id"])
        self._records[key] = receipt
        while len(self._records) > self._max_records:
            self._records.pop(next(iter(self._records)))
        return dict(receipt)

    def submit(
        self,
        session_id: str,
        input_id: str,
        data: bytes,
        write_fn: Callable[[bytes], None],
    ) -> dict[str, Any]:
        """Write ``data`` exactly once for (session_id, input_id).

        Returns the typed receipt. A repeated submission returns the stored
        receipt with ``duplicate: true`` and never calls ``write_fn`` again,
        whatever the original outcome was.
        """
        session_id = str(session_id or "")
        input_id = str(input_id or "").strip()
        if not session_id:
            raise ValueError("session_id is required for a job input receipt")
        if not input_id or len(input_id) > MAX_INPUT_ID_CHARS:
            raise ValueError(f"input_id must be 1..{MAX_INPUT_ID_CHARS} characters")
        with self._lock:
            existing = self._records.get((session_id, input_id))
            if existing is not None:
                return {**existing, "duplicate": True}
            try:
                write_fn(data)
            except Exception as exc:  # bytes may have partially landed
                return self._store(
                    _receipt(
                        session_id=session_id,
                        input_id=input_id,
                        outcome=OUTCOME_UNKNOWN,
                        data=data,
                        duplicate=False,
                        reason=f"{type(exc).__name__}: {exc}"[:300],
                    )
                )
            return self._store(
                _receipt(
                    session_id=session_id,
                    input_id=input_id,
                    outcome=OUTCOME_DELIVERED,
                    data=data,
                    duplicate=False,
                )
            )

    def record_rejected(
        self,
        session_id: str,
        input_id: str,
        data: bytes,
        reason: str,
    ) -> dict[str, Any]:
        """Record an input that was provably never written."""
        session_id = str(session_id or "")
        input_id = str(input_id or "").strip()
        if not session_id or not input_id or len(input_id) > MAX_INPUT_ID_CHARS:
            raise ValueError("session_id and a valid input_id are required")
        with self._lock:
            existing = self._records.get((session_id, input_id))
            if existing is not None:
                return {**existing, "duplicate": True}
            return self._store(
                _receipt(
                    session_id=session_id,
                    input_id=input_id,
                    outcome=OUTCOME_REJECTED,
                    data=data,
                    duplicate=False,
                    reason=str(reason)[:300],
                )
            )

    def receipt_for(self, session_id: str, input_id: str) -> dict[str, Any] | None:
        """Look up the stored receipt — the reconciliation path after a
        lost acknowledgement. Never triggers a write."""
        with self._lock:
            existing = self._records.get((str(session_id or ""), str(input_id or "").strip()))
            return dict(existing) if existing is not None else None
