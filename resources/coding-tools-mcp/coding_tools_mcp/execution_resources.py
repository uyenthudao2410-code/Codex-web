from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # Optional desktop signal; durable admission still works without it.
    psutil = None  # type: ignore[assignment]

from .command_parse import command_executables, shlex_split
from .orchestration_ledger import utc_now
from .processes import attach_managed_process, terminate_process_group


RESOURCE_CLASSES = frozenset({"LIGHT", "MEDIUM", "HEAVY"})
ACTIVE_LIFECYCLES = frozenset({"starting", "running", "terminating", "orphaned"})
HEAVY_EXECUTABLES = frozenset({
    "rustc",
    "rustc.exe",
    "rust-analyzer",
    "rust-analyzer.exe",
    "electron-builder",
    "electron-builder.exe",
})
_CARGO_EXECUTABLES = frozenset({"cargo", "cargo.exe"})
_CARGO_LIGHT_SUBCOMMANDS = frozenset({
    "--help",
    "--version",
    "help",
    "locate-project",
    "metadata",
    "search",
    "tree",
    "version",
})
_STARTING_RECONCILIATION_GRACE_SECONDS = 30.0
_RUST_ANALYZER_FOREIGN_RSS_BYTES = 1024 * 1024 * 1024
_PROCESS_MANAGED_LOCK = threading.RLock()
_PROCESS_MANAGED_PROCESSES: dict[
    tuple[str, str], dict[str, subprocess.Popen[Any]]
] = {}


class ExecutionResourceError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}


@dataclass(frozen=True)
class ManagedProcessAdmission:
    job_id: str
    command_id: str
    run_id: str
    wave_id: str
    owner: str
    checkout_id: str
    resource_class: str


def classify_resource_class(command: str, requested: object = "") -> str:
    explicit = str(requested or "").strip().upper()
    if explicit:
        if explicit not in RESOURCE_CLASSES:
            raise ExecutionResourceError(
                "INVALID_RESOURCE_CLASS",
                f"Unknown execution resource class: {explicit}",
                details={"supported": sorted(RESOURCE_CLASSES)},
            )
        return explicit

    lowered = str(command or "").strip().lower()
    tokens = shlex_split(str(command or ""))
    executable_names = {
        Path(token).name.lower()
        for token in command_executables(tokens)
    }
    cargo_resource = ""
    if executable_names & _CARGO_EXECUTABLES:
        cargo_subcommands = re.findall(
            r"(?:^|[\\/\s\"'])cargo(?:\.exe)?[\"']?\s+(?:\+\S+\s+)?([^\s;&|]+)",
            lowered,
        )
        if not cargo_subcommands or any(
            subcommand not in _CARGO_LIGHT_SUBCOMMANDS | {"fmt"}
            for subcommand in cargo_subcommands
        ):
            cargo_resource = "HEAVY"
        elif any(subcommand == "fmt" for subcommand in cargo_subcommands):
            cargo_resource = "MEDIUM"
        else:
            cargo_resource = "LIGHT"
    if executable_names & HEAVY_EXECUTABLES:
        return "HEAVY"
    if cargo_resource == "HEAVY":
        return "HEAVY"
    if re.search(r"(?:^|\s)(?:npm|pnpm|yarn)(?:\.cmd|\.exe)?\s+(?:run\s+)?(?:build|package|dist)\b", lowered):
        return "HEAVY"
    pytest_segments = [
        segment
        for segment in re.split(r"(?:&&|\|\||[;\r\n])", lowered)
        if re.search(
            r"(?:^|\s)(?:python(?:\.exe)?\s+-m\s+)?pytest(?:\.exe)?(?:\s|$)",
            segment,
        )
    ]
    pytest_resource = ""
    if pytest_segments:
        executable_pytest_segments = [
            segment
            for segment in pytest_segments
            if not re.search(
                r"pytest(?:\.exe)?\s+(?:--version|--help|-h)\s*$",
                segment.strip(),
            )
        ]
        if not executable_pytest_segments:
            pytest_resource = "LIGHT"
        elif any(
            not re.search(r"(?:\.py(?:::\S+)?|\s-k\s+\S+)", segment)
            for segment in executable_pytest_segments
        ):
            return "HEAVY"
        else:
            pytest_resource = "MEDIUM"
    if (
        cargo_resource == "MEDIUM"
        or pytest_resource == "MEDIUM"
        or executable_names & {"rustfmt", "rustfmt.exe"}
    ):
        return "MEDIUM"
    if cargo_resource or pytest_resource:
        return "LIGHT"
    return "LIGHT"


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_process_is_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _windows_process_is_alive(pid: int) -> bool:
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process = kernel32.OpenProcess(0x1000, False, int(pid))
        if not process:
            return False
        exit_code = wintypes.DWORD()
        try:
            return bool(kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code))) and exit_code.value == 259
        finally:
            kernel32.CloseHandle(process)
    except Exception:
        return False


def process_identity_token(pid: int) -> str:
    if pid <= 0:
        return ""
    if os.name == "nt":
        return _windows_process_identity_token(pid)
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
        return fields[21] if len(fields) > 21 else ""
    except (OSError, IndexError):
        return ""


def _windows_process_identity_token(pid: int) -> str:
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        process = kernel32.OpenProcess(0x1000, False, int(pid))
        if not process:
            return ""
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        try:
            if not kernel32.GetProcessTimes(
                process,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return ""
            return str((int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime))
        finally:
            kernel32.CloseHandle(process)
    except Exception:
        return ""


class ExecutionResourceGovernor:
    """Durable command ownership and checkout-wide HEAVY admission.

    The SQLite partial unique index is the global semaphore. In-memory Popen
    references are only used to terminate process trees that this runtime
    actually owns; restart orphans fail closed instead of being killed by PID.
    """

    def __init__(
        self,
        workspace: Path,
        ledger: Any,
        *,
        process_instance_id: str,
        runtime_instance_id: str,
    ) -> None:
        self.workspace = workspace.resolve(strict=False)
        self.checkout_id = hashlib.sha256(
            os.path.normcase(str(self.workspace)).encode("utf-8", errors="replace")
        ).hexdigest()
        self.ledger = ledger
        self.process_instance_id = str(process_instance_id)
        self.runtime_instance_id = str(runtime_instance_id)
        self._lock = _PROCESS_MANAGED_LOCK
        with self._lock:
            self._owned_processes = _PROCESS_MANAGED_PROCESSES.setdefault(
                (self.process_instance_id, self.checkout_id),
                {},
            )
        self._last_pressure: dict[str, Any] = {"pressured": False, "observed": False}
        self.recovery = self.reconcile_restart()

    def _rows(self, *, run_id: str = "", wave_id: str = "", active_only: bool = False) -> list[dict[str, Any]]:
        clauses = ["checkout_id=?"]
        params: list[Any] = [self.checkout_id]
        if run_id:
            clauses.append("run_id=?")
            params.append(run_id)
        if wave_id:
            clauses.append("wave_id=?")
            params.append(wave_id)
        if active_only:
            placeholders = ",".join("?" for _ in ACTIVE_LIFECYCLES)
            clauses.append(f"lifecycle_state IN ({placeholders})")
            params.extend(sorted(ACTIVE_LIFECYCLES))
        with self.ledger._lock, self.ledger._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM managed_process_jobs WHERE {' AND '.join(clauses)} ORDER BY started_at",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: Any) -> dict[str, Any]:
        return {
            "job_id": str(row["job_id"]),
            "run_id": str(row["run_id"]),
            "wave_id": str(row["wave_id"]),
            "command_id": str(row["command_id"]),
            "owner": str(row["owner"]),
            "checkout_id": str(row["checkout_id"]),
            "resource_class": str(row["resource_class"]),
            "root_pid": int(row["root_pid"] or 0),
            "root_process_token": str(row["root_process_token"] or ""),
            "process_instance_id": str(row["process_instance_id"] or ""),
            "runtime_instance_id": str(row["runtime_instance_id"] or ""),
            "lifecycle_state": str(row["lifecycle_state"]),
            "started_at": str(row["started_at"]),
            "updated_at": str(row["updated_at"]),
            "finished_at": row["finished_at"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def _emit(self, row: dict[str, Any], event_type: str, **payload: Any) -> None:
        run_id = str(row.get("run_id") or "")
        wave_id = str(row.get("wave_id") or "")
        if not run_id or not wave_id:
            return
        self.ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type=event_type,
            payload={
                "job_id": row.get("job_id"),
                "command_id": row.get("command_id"),
                "owner": row.get("owner"),
                "checkout_id": row.get("checkout_id"),
                "resource_class": row.get("resource_class"),
                "root_pid": row.get("root_pid", 0),
                **payload,
            },
        )

    def _validate_owner(self, run_id: str, wave_id: str) -> None:
        if not run_id or not wave_id:
            raise ExecutionResourceError(
                "EXECUTION_OWNERSHIP_REQUIRED",
                "HEAVY execution on the authoritative checkout requires a current RUN/WAVE owner.",
                retryable=True,
            )
        with self.ledger._lock, self.ledger._connect() as connection:
            row = connection.execute(
                """SELECT r.status AS run_status, w.status AS wave_status,
                          (SELECT state_after FROM events e
                           WHERE e.run_id=w.run_id AND e.wave_id=w.wave_id
                             AND COALESCE(e.state_after,'')<>''
                           ORDER BY e.seq DESC LIMIT 1) AS orchestration_state
                   FROM waves w JOIN runs r ON r.run_id=w.run_id
                   WHERE w.wave_id=? AND w.run_id=?""",
                (wave_id, run_id),
            ).fetchone()
        if row is None or str(row["run_status"]) != "active" or str(row["wave_status"]) != "active":
            raise ExecutionResourceError(
                "EXECUTION_OWNER_INVALID",
                "The supplied RUN/WAVE is not the current active execution owner.",
                retryable=True,
                details={"run_id": run_id, "wave_id": wave_id},
            )
        orchestration_state = str(row["orchestration_state"] or "").upper()
        if orchestration_state in {"REPLAN", "BLOCKED", "ABORTED", "CHECKPOINTED"}:
            raise ExecutionResourceError(
                "EXECUTION_OWNER_INVALID",
                "The supplied RUN/WAVE is quiescing or terminal and cannot admit new execution.",
                retryable=True,
                details={
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "orchestration_state": orchestration_state,
                },
            )

    @staticmethod
    def _row_age_seconds(row: dict[str, Any]) -> float:
        try:
            timestamp = datetime.fromisoformat(
                str(row.get("started_at") or "").replace("Z", "+00:00")
            )
            return max(0.0, time.time() - timestamp.astimezone(timezone.utc).timestamp())
        except (TypeError, ValueError):
            return _STARTING_RECONCILIATION_GRACE_SECONDS + 1.0

    def _host_pressure(self) -> dict[str, Any]:
        if psutil is None:
            snapshot = {"observed": False, "pressured": False}
            self._last_pressure = snapshot
            return snapshot
        try:
            memory = psutil.virtual_memory()
            available_percent = (
                (float(memory.available) / float(memory.total)) * 100.0
                if memory.total
                else 0.0
            )
            try:
                threshold = float(
                    os.environ.get("CODING_TOOLS_MCP_HEAVY_MIN_AVAILABLE_MEMORY_PERCENT", "5")
                )
            except (TypeError, ValueError):
                threshold = 5.0
            threshold = max(0.0, min(threshold, 50.0))
            snapshot = {
                "observed": True,
                "pressured": available_percent < threshold,
                "available_bytes": int(memory.available),
                "available_percent": round(available_percent, 2),
                "minimum_available_percent": threshold,
            }
        except (OSError, RuntimeError):
            snapshot = {"observed": False, "pressured": False}
        self._last_pressure = snapshot
        return snapshot

    def _path_in_checkout(self, value: object) -> bool:
        text = str(value or "").strip().strip('"')
        if not text:
            return False
        try:
            candidate = Path(text).resolve(strict=False)
            common = os.path.commonpath((str(self.workspace), str(candidate)))
            return os.path.normcase(common) == os.path.normcase(str(self.workspace))
        except (OSError, ValueError):
            return False

    def _foreign_heavy_processes(self) -> list[dict[str, Any]]:
        if psutil is None:
            return []
        excluded_pids = {os.getpid()}
        try:
            excluded_pids.update(parent.pid for parent in psutil.Process().parents())
        except (psutil.Error, OSError):
            pass

        active_rows = self._rows(active_only=True)
        managed_roots = {
            int(row["root_pid"])
            for row in active_rows
            if int(row["root_pid"]) > 0
        }
        managed_pids = set(managed_roots)
        for pid in managed_roots:
            try:
                managed_pids.update(child.pid for child in psutil.Process(pid).children(recursive=True))
            except (psutil.Error, OSError):
                continue

        foreign: list[dict[str, Any]] = []
        for process in psutil.process_iter(["pid", "name", "cmdline", "cwd", "memory_info"]):
            try:
                pid = int(process.info.get("pid") or 0)
                if pid <= 0 or pid in excluded_pids or pid in managed_pids:
                    continue
                name = str(process.info.get("name") or "").lower()
                argv = [str(token) for token in (process.info.get("cmdline") or [])]
                command = " ".join([name, *argv])
                if classify_resource_class(command) != "HEAVY":
                    continue
                in_checkout = self._path_in_checkout(process.info.get("cwd")) or any(
                    Path(token.strip('"')).is_absolute() and self._path_in_checkout(token)
                    for token in argv
                )
                if not in_checkout:
                    continue
                rss = int(getattr(process.info.get("memory_info"), "rss", 0) or 0)
                if name in {"rust-analyzer", "rust-analyzer.exe"} and rss < _RUST_ANALYZER_FOREIGN_RSS_BYTES:
                    continue
                foreign.append({"pid": pid, "name": name[:128], "working_set_bytes": rss})
                if len(foreign) >= 8:
                    break
            except (psutil.Error, OSError, ValueError):
                continue
        return foreign

    def foreign_heavy_processes(self) -> list[dict[str, Any]]:
        """Return bounded, redacted HEAVY processes confirmed on this checkout."""

        return self._foreign_heavy_processes()

    def _active_write_fence_count(self, run_id: str, wave_id: str) -> int:
        with self.ledger._lock, self.ledger._connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS count FROM write_fences
                   WHERE run_id=? AND wave_id=? AND status='active' AND expires_at>?""",
                (str(run_id), str(wave_id), time.time()),
            ).fetchone()
        return int(row["count"] or 0) if row else 0

    def admit(
        self,
        *,
        command: str,
        command_id: str,
        run_id: str = "",
        wave_id: str = "",
        owner: str = "default",
        resource_class: object = "",
    ) -> ManagedProcessAdmission:
        resource = classify_resource_class(command, resource_class)
        run_id = str(run_id or "").strip()
        wave_id = str(wave_id or "").strip()
        if resource == "HEAVY":
            self._validate_owner(run_id, wave_id)
        elif bool(run_id) != bool(wave_id):
            raise ExecutionResourceError(
                "EXECUTION_OWNER_INVALID",
                "run_id and wave_id must be supplied together.",
                details={"run_id": run_id, "wave_id": wave_id},
            )
        elif run_id:
            self._validate_owner(run_id, wave_id)

        self.reconcile()
        if resource == "HEAVY":
            active = self._rows(active_only=True)
            heavy = next((row for row in active if row["resource_class"] == "HEAVY"), None)
            if heavy is not None:
                code = (
                    "UNOWNED_EXECUTION_PROCESS"
                    if heavy["lifecycle_state"] == "orphaned"
                    else "HEAVY_SLOT_BUSY"
                )
                raise ExecutionResourceError(
                    code,
                    "Another HEAVY execution owns this checkout's global resource slot.",
                    retryable=True,
                    details={"active_job": self._public_row(heavy)},
                )
            pressure = self._host_pressure()
            if pressure.get("pressured"):
                raise ExecutionResourceError(
                    "HOST_RESOURCE_PRESSURE",
                    "Available host memory is below the HEAVY execution admission threshold.",
                    retryable=True,
                    details=pressure,
                )
            foreign = self._foreign_heavy_processes()
            if foreign:
                raise ExecutionResourceError(
                    "UNOWNED_EXECUTION_PROCESS",
                    "An unowned HEAVY process is already active on this checkout.",
                    retryable=True,
                    details={"foreign_processes": foreign},
                )
        job_id = uuid.uuid4().hex
        now = utc_now()
        command_hash = hashlib.sha256(str(command).encode("utf-8", errors="replace")).hexdigest()
        metadata = json.dumps(
            {"command_sha256": command_hash, "classification": "explicit" if resource_class else "automatic"},
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            with self.ledger._lock, self.ledger._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO managed_process_jobs(
                        job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,
                        process_instance_id,runtime_instance_id,lifecycle_state,started_at,updated_at,metadata_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        job_id,
                        run_id,
                        wave_id,
                        str(command_id),
                        str(owner or "default")[:128],
                        self.checkout_id,
                        resource,
                        self.process_instance_id,
                        self.runtime_instance_id,
                        "starting",
                        now,
                        now,
                        metadata,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            active = self._rows(active_only=True)
            heavy = next((row for row in active if row["resource_class"] == "HEAVY"), None)
            code = "UNOWNED_EXECUTION_PROCESS" if heavy and heavy["lifecycle_state"] == "orphaned" else "HEAVY_SLOT_BUSY"
            raise ExecutionResourceError(
                code,
                "Another HEAVY execution owns this checkout's global resource slot.",
                retryable=True,
                details={"active_job": self._public_row(heavy) if heavy else None},
            ) from exc

        admission = ManagedProcessAdmission(
            job_id=job_id,
            command_id=str(command_id),
            run_id=run_id,
            wave_id=wave_id,
            owner=str(owner or "default")[:128],
            checkout_id=self.checkout_id,
            resource_class=resource,
        )
        self._emit(admission.__dict__, "managed_process_admitted", lifecycle_state="starting")
        return admission

    def bind_process(self, admission: ManagedProcessAdmission, process: subprocess.Popen[Any]) -> None:
        attach_managed_process(process)
        token = process_identity_token(int(process.pid))
        now = utc_now()
        with self._lock:
            self._owned_processes[admission.job_id] = process
        try:
            with self.ledger._lock, self.ledger._connect() as connection:
                cursor = connection.execute(
                    """UPDATE managed_process_jobs
                       SET root_pid=?,root_process_token=?,lifecycle_state='running',updated_at=?
                       WHERE job_id=? AND process_instance_id=? AND lifecycle_state='starting'""",
                    (int(process.pid), token, now, admission.job_id, self.process_instance_id),
                )
                if cursor.rowcount != 1:
                    raise ExecutionResourceError(
                        "EXECUTION_ADMISSION_LOST",
                        "The managed command admission was revoked before process binding completed.",
                        retryable=True,
                        details={"job_id": admission.job_id},
                    )
        except Exception:
            with self._lock:
                self._owned_processes.pop(admission.job_id, None)
            raise
        self._emit(
            {**admission.__dict__, "root_pid": int(process.pid)},
            "managed_process_started",
            lifecycle_state="running",
        )

    def complete(self, job_id: str, *, lifecycle_state: str, exit_code: int | None = None) -> None:
        terminal = str(lifecycle_state or "exited")[:64]
        now = utc_now()
        with self._lock:
            owned_process = self._owned_processes.pop(str(job_id), None)
        if owned_process is not None:
            terminate_process_group(owned_process, signal.SIGTERM)
            if exit_code is None:
                exit_code = owned_process.poll()
        with self.ledger._lock, self.ledger._connect() as connection:
            row = connection.execute("SELECT * FROM managed_process_jobs WHERE job_id=?", (str(job_id),)).fetchone()
            if row is None:
                return
            if str(row["lifecycle_state"]) not in ACTIVE_LIFECYCLES:
                return
            connection.execute(
                """UPDATE managed_process_jobs
                   SET lifecycle_state=?,updated_at=?,finished_at=?,metadata_json=json_set(metadata_json,'$.exit_code',?)
                   WHERE job_id=?""",
                (terminal, now, now, exit_code, str(job_id)),
            )
        item = self._row(row)
        self._emit(item, "managed_process_terminal", lifecycle_state=terminal, exit_code=exit_code)

    def spawn_failed(self, admission: ManagedProcessAdmission) -> None:
        self.complete(admission.job_id, lifecycle_state="spawn_failed")

    def reconcile_restart(self) -> dict[str, int]:
        return self.reconcile(restart=True)

    def reconcile(self, *, restart: bool = False) -> dict[str, int]:
        counts = {"quiesced": 0, "orphaned": 0}
        rows = self._rows(active_only=True)
        for row in rows:
            pid = int(row["root_pid"])
            token = str(row["root_process_token"])
            with self._lock:
                owned_process = self._owned_processes.get(row["job_id"])
            alive = process_is_alive(pid)
            if alive and token:
                observed = process_identity_token(pid)
                alive = not observed or observed == token
            if not alive and pid > 0:
                if owned_process is not None:
                    self.complete(
                        row["job_id"],
                        lifecycle_state="quiesced",
                        exit_code=owned_process.poll(),
                    )
                else:
                    self._set_reconciled_state(row, "quiesced", reason="root_process_gone")
                counts["quiesced"] += 1
                continue
            owner_process_missing = row["process_instance_id"] != self.process_instance_id
            stale_start = (
                pid == 0
                and owned_process is None
                and self._row_age_seconds(row) > _STARTING_RECONCILIATION_GRACE_SECONDS
            )
            handle_missing = alive and owned_process is None
            if owner_process_missing or stale_start or handle_missing:
                state = "orphaned" if alive or pid == 0 else "quiesced"
                self._set_reconciled_state(
                    row,
                    state,
                    reason=(
                        "process_restarted"
                        if restart and owner_process_missing
                        else "owner_process_missing"
                        if owner_process_missing
                        else "owned_handle_missing"
                    ),
                )
                counts[state] += 1
        return counts

    def _set_reconciled_state(self, row: dict[str, Any], state: str, *, reason: str) -> None:
        if row["lifecycle_state"] == state:
            return
        now = utc_now()
        finished_at = now if state == "quiesced" else None
        with self.ledger._lock, self.ledger._connect() as connection:
            connection.execute(
                """UPDATE managed_process_jobs
                   SET lifecycle_state=?,updated_at=?,finished_at=COALESCE(?,finished_at),
                       metadata_json=json_set(metadata_json,'$.recovery_reason',?)
                   WHERE job_id=?""",
                (state, now, finished_at, reason, row["job_id"]),
            )
        self._emit(row, "managed_process_reconciled", lifecycle_state=state, reason=reason)

    def teardown_wave(self, run_id: str, wave_id: str, *, reason: str, grace_seconds: float = 1.0) -> dict[str, Any]:
        rows = self._rows(run_id=str(run_id), wave_id=str(wave_id), active_only=True)
        terminated = 0
        for row in rows:
            if row["process_instance_id"] != self.process_instance_id:
                continue
            with self._lock:
                process = self._owned_processes.get(row["job_id"])
            if process is None:
                if not process_is_alive(int(row["root_pid"])) and int(row["root_pid"]) > 0:
                    self._set_reconciled_state(row, "quiesced", reason="teardown_process_gone")
                else:
                    self._set_reconciled_state(row, "orphaned", reason="owned_handle_missing")
                continue
            if process.poll() is None:
                terminate_process_group(process, signal.SIGTERM)
                try:
                    process.wait(timeout=max(0.0, float(grace_seconds)))
                except subprocess.TimeoutExpired:
                    terminate_process_group(process, signal.SIGTERM, force=True)
            self.complete(row["job_id"], lifecycle_state="quiesced", exit_code=process.poll())
            terminated += 1
        self.reconcile()
        active = self._rows(run_id=str(run_id), wave_id=str(wave_id), active_only=True)
        payload = {
            "run_id": str(run_id),
            "wave_id": str(wave_id),
            "reason": str(reason),
            "terminated": terminated,
            "active_command_count": len(active),
            "quiescent": not active,
        }
        if run_id and wave_id:
            self.ledger.append_event(
                str(run_id),
                wave_id=str(wave_id),
                event_type="wave_processes_quiesced" if not active else "wave_processes_quiescence_failed",
                payload=payload,
            )
        return payload

    def assert_wave_quiescent(self, run_id: str, wave_id: str) -> None:
        self.reconcile()
        active = self._rows(run_id=str(run_id), wave_id=str(wave_id), active_only=True)
        foreign = self._foreign_heavy_processes()
        active_write_fences = self._active_write_fence_count(run_id, wave_id)
        if active or foreign or active_write_fences:
            raise ExecutionResourceError(
                "WAVE_NOT_QUIESCENT",
                "The prior orchestration wave or checkout still has active execution ownership.",
                retryable=True,
                details={
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "active_jobs": [self._public_row(row) for row in active],
                    "foreign_heavy_processes": foreign,
                    "active_write_fence_count": active_write_fences,
                },
            )

    @staticmethod
    def _public_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            key: row.get(key)
            for key in (
                "job_id",
                "run_id",
                "wave_id",
                "command_id",
                "owner",
                "resource_class",
                "root_pid",
                "lifecycle_state",
                "started_at",
                "updated_at",
            )
        }

    def snapshot(self, *, limit: int = 20) -> dict[str, Any]:
        self.reconcile()
        rows = self._rows()
        active = [row for row in rows if row["lifecycle_state"] in ACTIVE_LIFECYCLES]
        visible = rows[-max(1, min(int(limit), 100)) :]
        return {
            "schema_version": 1,
            "checkout_id": self.checkout_id,
            "heavy_concurrency_limit": 1,
            "active_command_count": len(active),
            "active_heavy_count": sum(1 for row in active if row["resource_class"] == "HEAVY"),
            "orphaned_count": sum(1 for row in active if row["lifecycle_state"] == "orphaned"),
            "quiescent": not active,
            "quiescence_scope": "managed_processes",
            "host_pressure": dict(self._last_pressure),
            "recovery": dict(self.recovery),
            "jobs": [self._public_row(row) for row in visible],
        }
