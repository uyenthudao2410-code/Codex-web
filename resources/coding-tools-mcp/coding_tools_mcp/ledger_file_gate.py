"""Cross-process shared/exclusive gate for canonical ledger file access.

SQLite protects database/WAL transactions, but application-level physical
replacement is unsafe while another process owns a handle to the old database.
Normal canonical connections hold a shared byte-range lock for their lifetime;
physical maintenance holds the same lock exclusively across replacement.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class LedgerGateTimeout(TimeoutError):
    """Canonical ledger coordination gate could not be acquired in time."""


_HELD = threading.local()


def _canonical_key(ledger_path: Path) -> str:
    value = str(Path(ledger_path).resolve(strict=False))
    return value.casefold() if os.name == "nt" else value


def _lock_path(ledger_path: Path) -> Path:
    digest = hashlib.sha256(_canonical_key(ledger_path).encode("utf-8", errors="replace")).hexdigest()
    root = Path(tempfile.gettempdir()) / "coding-tools-ledger-gates"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{digest}.lock"


def _thread_state() -> dict[str, dict[str, Any]]:
    state = getattr(_HELD, "ledger_gates", None)
    if state is None:
        state = {}
        _HELD.ledger_gates = state
    return state


if os.name == "nt":
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _LOCKFILE_FAIL_IMMEDIATELY = 0x00000001
    _LOCKFILE_EXCLUSIVE_LOCK = 0x00000002
    _ERROR_LOCK_VIOLATION = 33
    _ERROR_SHARING_VIOLATION = 32

    class _OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ("Internal", ctypes.c_size_t),
            ("InternalHigh", ctypes.c_size_t),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        ]

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _LOCK_FILE_EX = _KERNEL32.LockFileEx
    _LOCK_FILE_EX.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_OVERLAPPED),
    ]
    _LOCK_FILE_EX.restype = wintypes.BOOL
    _UNLOCK_FILE_EX = _KERNEL32.UnlockFileEx
    _UNLOCK_FILE_EX.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_OVERLAPPED),
    ]
    _UNLOCK_FILE_EX.restype = wintypes.BOOL


def _try_os_lock(fd: int, *, exclusive: bool) -> Any | None:
    if os.name == "nt":
        overlapped = _OVERLAPPED()
        flags = _LOCKFILE_FAIL_IMMEDIATELY | (_LOCKFILE_EXCLUSIVE_LOCK if exclusive else 0)
        handle = wintypes.HANDLE(msvcrt.get_osfhandle(fd))
        ctypes.set_last_error(0)
        if _LOCK_FILE_EX(handle, flags, 0, 1, 0, ctypes.byref(overlapped)):
            return overlapped
        error = ctypes.get_last_error()
        if error in {_ERROR_LOCK_VIOLATION, _ERROR_SHARING_VIOLATION}:
            return None
        raise ctypes.WinError(error)

    import errno
    import fcntl

    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    try:
        fcntl.flock(fd, operation | fcntl.LOCK_NB)
    except OSError as exc:
        if exc.errno in {errno.EACCES, errno.EAGAIN}:
            return None
        raise
    return True


def _unlock_os(fd: int, token: Any) -> None:
    if os.name == "nt":
        handle = wintypes.HANDLE(msvcrt.get_osfhandle(fd))
        if not _UNLOCK_FILE_EX(handle, 0, 1, 0, ctypes.byref(token)):
            raise ctypes.WinError(ctypes.get_last_error())
        return

    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def ledger_access_gate(
    ledger_path: Path,
    *,
    exclusive: bool = False,
    timeout_seconds: float = 5.0,
) -> Iterator[None]:
    """Hold shared normal access or exclusive physical-maintenance authority."""

    key = _canonical_key(ledger_path)
    state = _thread_state()
    existing = state.get(key)
    if existing is not None:
        if existing["exclusive"] or not exclusive:
            existing["depth"] += 1
            try:
                yield
            finally:
                existing["depth"] -= 1
            return
        raise RuntimeError("cannot upgrade a held shared ledger gate to exclusive authority")

    fd = os.open(str(_lock_path(ledger_path)), os.O_RDWR | os.O_CREAT, 0o600)
    token: Any | None = None
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    try:
        while token is None:
            token = _try_os_lock(fd, exclusive=exclusive)
            if token is not None:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                mode = "exclusive" if exclusive else "shared"
                raise LedgerGateTimeout(f"timed out acquiring {mode} ledger access gate")
            time.sleep(min(0.01, remaining))
        state[key] = {"exclusive": bool(exclusive), "depth": 1, "fd": fd, "token": token}
        try:
            yield
        finally:
            state.pop(key, None)
            _unlock_os(fd, token)
            token = None
    finally:
        os.close(fd)


def ledger_exclusive_gate_held(ledger_path: Path) -> bool:
    """Whether this thread currently owns exclusive maintenance authority."""
    held = _thread_state().get(_canonical_key(ledger_path))
    return bool(held and held.get("exclusive"))
