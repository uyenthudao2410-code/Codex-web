#!/usr/bin/env python3
"""Run the real-binding-only Connector/Runner/rust-analyzer lifecycle soak."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
for import_root in (SCRIPT_DIR, PACKAGE_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from coding_tools_mcp.execution_resources import (  # noqa: E402
    ExecutionResourceError,
    ExecutionResourceGovernor,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger  # noqa: E402
from coding_tools_mcp.semantic_localization import (  # noqa: E402
    NativeRustSemanticLocalizationProvider,
    semantic_localizer_from_env,
    semantic_provider_resource_status,
    semantic_provider_status,
    semantic_resource_cost,
)
from run_resource_hardening_soak import (  # noqa: E402
    git_head,
    ledger_health,
    source_fingerprint,
    utc_now,
)


LIVE_SOAK_SCHEMA_VERSION = 1
MINIMUM_LIFECYCLE_CYCLES = 10


class LiveSoakBlocked(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LiveBinding:
    provider: NativeRustSemanticLocalizationProvider
    initial_status: dict[str, Any]
    rust_analyzer_version: str


def distribution(values: list[int]) -> dict[str, int]:
    ordered = sorted(int(value) for value in values)
    if not ordered:
        return {"count": 0}
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) // 2
    )
    p95 = ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": median,
        "p95": p95,
        "max": ordered[-1],
    }


def _bounded_label(value: object, *, name: str) -> str:
    label = str(value or "").strip()
    if (
        not label
        or len(label.encode("utf-8")) > 256
        or re.fullmatch(r"[A-Za-z0-9._:@+\-]+", label) is None
        or re.fullmatch(r"webcodex_[a-f0-9]{64}", label) is not None
    ):
        raise LiveSoakBlocked(
            "LIVE_ARTIFACT_ID_REQUIRED",
            f"{name} must be a bounded path-free live artifact identifier",
        )
    return label


def _relative_rust_file(repository: Path, value: object) -> str:
    rendered = str(value or "").strip().replace("\\", "/")
    candidate = Path(rendered)
    if (
        not rendered
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.suffix.lower() != ".rs"
        or not (repository / candidate).is_file()
    ):
        raise LiveSoakBlocked(
            "LIVE_RUST_FILE_REQUIRED",
            "--file must be an existing project-relative Rust source file",
        )
    return rendered


def _query(value: object) -> str:
    query = str(value or "").strip()
    if not query or len(query.encode("utf-8")) > 200:
        raise LiveSoakBlocked(
            "LIVE_QUERY_REQUIRED",
            "--query must name a stable symbol in 1..=200 UTF-8 bytes",
        )
    return query


def _rust_analyzer_version() -> str:
    executable = shutil.which("rust-analyzer")
    if not executable:
        raise LiveSoakBlocked(
            "RUST_ANALYZER_UNAVAILABLE",
            "rust-analyzer is not available on the live acceptance host",
        )
    completed = subprocess.run(
        [executable, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    version = " ".join(completed.stdout.strip().split())[:200]
    if completed.returncode != 0 or not version:
        raise LiveSoakBlocked(
            "RUST_ANALYZER_VERSION_UNAVAILABLE",
            "rust-analyzer did not return a usable version",
        )
    return version


def resolve_live_binding(repository: Path, rust_file: str) -> LiveBinding:
    provider = semantic_localizer_from_env(repository)
    if not isinstance(provider, NativeRustSemanticLocalizationProvider):
        binding = semantic_provider_status(provider).get("binding") or {}
        state = str(binding.get("state") or "unconfigured")
        raise LiveSoakBlocked(
            "REAL_CONNECTOR_BINDING_REQUIRED",
            f"a configured real native-LSP binding is required (state={state})",
        )
    status = semantic_provider_resource_status(
        provider,
        workspace=repository,
        path=rust_file,
    )
    if status.get("observed") is not True or status.get("lifecycle_state") == "UNKNOWN":
        raise LiveSoakBlocked(
            "LIVE_CONNECTOR_RUNNER_UNAVAILABLE",
            "the configured Connector did not return an observed Runner LSP status",
        )
    return LiveBinding(
        provider=provider,
        initial_status=status,
        rust_analyzer_version=_rust_analyzer_version(),
    )


def wait_for_status(
    provider: NativeRustSemanticLocalizationProvider,
    repository: Path,
    rust_file: str,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout_seconds: float,
    poll_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] = {}
    while True:
        last = semantic_provider_resource_status(
            provider,
            workspace=repository,
            path=rust_file,
        )
        if predicate(last):
            return last
        if time.monotonic() >= deadline:
            raise LiveSoakBlocked(
                "LIVE_LIFECYCLE_TIMEOUT",
                "the live LSP lifecycle did not reach the required bounded state",
            )
        time.sleep(poll_seconds)


def _native_call(
    provider: NativeRustSemanticLocalizationProvider,
    *,
    repository: Path,
    path: str,
    query: str,
    resource_class: str,
) -> tuple[int, list[dict[str, Any]]]:
    started = time.monotonic()
    try:
        rows = provider.localize(
            workspace=repository,
            path=path,
            queries=[query],
            max_results=20,
            resource_class=resource_class,
        )
    except Exception as exc:
        raise LiveSoakBlocked(
            "LIVE_NATIVE_CALL_FAILED",
            f"the real native semantic {resource_class.lower()} request failed",
        ) from exc
    latency_ms = max(0, int((time.monotonic() - started) * 1000))
    if not any(isinstance(row, dict) and row.get("handled") is True for row in rows):
        raise LiveSoakBlocked(
            "LIVE_QUERY_NOT_HANDLED",
            "the configured live query was not handled by native rust-analyzer",
        )
    for row in rows:
        for match in row.get("matches", []) if isinstance(row, dict) else []:
            path = str(match.get("path") or "") if isinstance(match, dict) else ""
            candidate = Path(path)
            if not path or candidate.is_absolute() or ".." in candidate.parts:
                raise LiveSoakBlocked(
                    "LIVE_RESULT_PATH_INVALID",
                    "native semantic returned a non-project-relative match path",
                )
    return latency_ms, rows


def _native_call_until_handled(
    provider: NativeRustSemanticLocalizationProvider,
    *,
    repository: Path,
    path: str,
    query: str,
    resource_class: str,
    timeout_seconds: float,
    poll_seconds: float,
) -> tuple[int, list[dict[str, Any]]]:
    started = time.monotonic()
    deadline = started + max(0.1, timeout_seconds)
    while True:
        try:
            _, rows = _native_call(
                provider,
                repository=repository,
                path=path,
                query=query,
                resource_class=resource_class,
            )
            return max(0, int((time.monotonic() - started) * 1000)), rows
        except LiveSoakBlocked as exc:
            if exc.code != "LIVE_QUERY_NOT_HANDLED" or time.monotonic() >= deadline:
                raise
            time.sleep(max(0.01, poll_seconds))


def _new_governor(repository: Path, ledger: OrchestrationLedger, prefix: str) -> ExecutionResourceGovernor:
    return ExecutionResourceGovernor(
        repository,
        ledger,
        process_instance_id=f"live-soak-process-{prefix}-{uuid.uuid4().hex}",
        runtime_instance_id=f"live-soak-runtime-{prefix}-{uuid.uuid4().hex}",
    )


def atomic_live_conflict(
    *,
    repository: Path,
    provider: NativeRustSemanticLocalizationProvider,
    rust_file: str,
    query: str,
    ledger: OrchestrationLedger,
) -> dict[str, Any]:
    semantic_governor = _new_governor(repository, ledger, "semantic")
    managed_governor = _new_governor(repository, ledger, "managed")
    run_id = ledger.create_run(
        objective="P2/P3 live atomic semantic/managed HEAVY conflict",
        task_id=f"live-soak-{uuid.uuid4().hex}",
    )
    wave_id = ledger.create_wave(
        run_id,
        execution_mode="mcp_only",
        base_head=git_head(repository),
        worktree_fp=source_fingerprint(repository)["sha256"],
    )
    barrier = threading.Barrier(3)
    release = threading.Event()
    semantic_done = threading.Event()
    managed_done = threading.Event()
    outcomes: dict[str, Any] = {}

    def semantic_lane() -> None:
        try:
            barrier.wait()
            status = semantic_provider_resource_status(
                provider,
                workspace=repository,
                path=rust_file,
            )
            with semantic_governor.semantic_native_claim(
                mode="single_file",
                cost="HEAVY",
                resource_status=status,
            ) as lease:
                outcomes["semantic"] = lease.public_decision()
                if lease["allowed"]:
                    latency, _ = _native_call(
                        provider,
                        repository=repository,
                        path=rust_file,
                        query=query,
                        resource_class="HEAVY",
                    )
                    outcomes["semantic_latency_ms"] = latency
                semantic_done.set()
                release.wait(timeout=60)
        except Exception as exc:
            outcomes["semantic_error"] = type(exc).__name__
            semantic_done.set()

    def managed_lane() -> None:
        admission = None
        try:
            barrier.wait()
            try:
                admission = managed_governor.admit(
                    command="cargo check",
                    command_id=f"live-soak-conflict-{uuid.uuid4().hex}",
                    run_id=run_id,
                    wave_id=wave_id,
                    resource_class="HEAVY",
                )
                outcomes["managed"] = "ALLOWED"
            except ExecutionResourceError as exc:
                outcomes["managed"] = exc.code
            managed_done.set()
            release.wait(timeout=60)
        except Exception as exc:
            outcomes["managed_error"] = type(exc).__name__
            managed_done.set()
        finally:
            if admission is not None:
                managed_governor.complete(
                    admission.job_id,
                    lifecycle_state="exited",
                    exit_code=0,
                )

    semantic_thread = threading.Thread(target=semantic_lane, daemon=True)
    managed_thread = threading.Thread(target=managed_lane, daemon=True)
    semantic_thread.start()
    managed_thread.start()
    barrier.wait()
    semantic_done.wait(timeout=60)
    managed_done.wait(timeout=60)
    semantic_allowed = bool(
        isinstance(outcomes.get("semantic"), dict)
        and outcomes["semantic"].get("allowed") is True
    )
    managed_allowed = outcomes.get("managed") == "ALLOWED"
    release.set()
    semantic_thread.join(timeout=60)
    managed_thread.join(timeout=60)
    try:
        if semantic_thread.is_alive() or managed_thread.is_alive():
            raise LiveSoakBlocked("LIVE_CONFLICT_TIMEOUT", "the live conflict barrier did not quiesce")
        if outcomes.get("semantic_error") or outcomes.get("managed_error"):
            raise LiveSoakBlocked(
                "LIVE_CONFLICT_LANE_FAILED",
                "a live conflict lane failed before producing an admission decision",
            )
        if int(semantic_allowed) + int(managed_allowed) != 1:
            raise LiveSoakBlocked(
                "LIVE_HEAVY_OVERLAP",
                "the live semantic/managed barrier did not produce exactly one HEAVY winner",
            )
        loser = outcomes.get("managed") if semantic_allowed else outcomes.get("semantic", {}).get("reason_code")
        if loser != "HEAVY_SLOT_BUSY":
            raise LiveSoakBlocked(
                "LIVE_CONFLICT_REASON_INVALID",
                "the losing HEAVY claimant did not receive HEAVY_SLOT_BUSY",
            )
        if semantic_governor._claim_rows(active_only=True):
            raise LiveSoakBlocked("LIVE_CLAIM_LEAK", "the live conflict left an active claim")
        return {
            "semantic_allowed": semantic_allowed,
            "managed_allowed": managed_allowed,
            "loser_reason_code": loser,
            "semantic_latency_ms": outcomes.get("semantic_latency_ms"),
        }
    finally:
        ledger.finish_wave(wave_id, status="completed")
        ledger.finish_run(run_id, status="completed")


def run_cycles(
    *,
    repository: Path,
    provider: NativeRustSemanticLocalizationProvider,
    rust_file: str,
    query: str,
    cycles: int,
    idle_timeout_seconds: float,
    poll_seconds: float,
    ledger: OrchestrationLedger,
) -> dict[str, Any]:
    governor = _new_governor(repository, ledger, "cycles")
    cold_latency: list[int] = []
    warm_latency: list[int] = []
    workspace_latency: list[int] = []
    working_sets: list[int] = []
    peak_working_sets: list[int] = []
    claim_wait: list[int] = []
    process_ids: list[str] = []
    cycle_rows: list[dict[str, Any]] = []

    for index in range(cycles):
        cold = wait_for_status(
            provider,
            repository,
            rust_file,
            lambda status: status.get("lifecycle_state") == "STOPPED",
            timeout_seconds=idle_timeout_seconds,
            poll_seconds=poll_seconds,
        )
        claim_started = time.monotonic()
        with governor.semantic_native_claim(
            mode="single_file",
            cost="HEAVY",
            resource_status=cold,
        ) as lease:
            claim_wait.append(max(0, int((time.monotonic() - claim_started) * 1000)))
            if not lease["allowed"] or not lease["claim_acquired"]:
                raise LiveSoakBlocked(
                    "LIVE_COLD_CLAIM_DENIED",
                    f"cold cycle {index + 1} did not acquire the HEAVY claim",
                )
            latency, _ = _native_call(
                provider,
                repository=repository,
                path=rust_file,
                query=query,
                resource_class="HEAVY",
            )
            cold_latency.append(latency)

        warm = wait_for_status(
            provider,
            repository,
            rust_file,
            lambda status: status.get("lifecycle_state") == "RUNNING" and status.get("warm") is True,
            timeout_seconds=35,
            poll_seconds=poll_seconds,
        )
        process_id = str(warm.get("process_instance_id") or "")
        if not process_id or (process_ids and process_id == process_ids[-1]):
            raise LiveSoakBlocked(
                "LIVE_RESTART_IDENTITY_UNPROVEN",
                "each cold restart must expose a new opaque process instance id",
            )
        process_ids.append(process_id)
        if isinstance(warm.get("working_set_bytes"), int):
            working_sets.append(warm["working_set_bytes"])
        if isinstance(warm.get("peak_working_set_bytes"), int):
            peak_working_sets.append(warm["peak_working_set_bytes"])

        warm_cost = semantic_resource_cost("single_file", warm)
        if warm_cost != "MEDIUM":
            raise LiveSoakBlocked(
                "LIVE_WARM_CLASSIFICATION_INVALID",
                "RUNNING + warm + NORMAL focused status did not classify as MEDIUM",
            )
        with governor.semantic_native_claim(
            mode="single_file",
            cost=warm_cost,
            resource_status=warm,
        ) as lease:
            if not lease["allowed"] or lease["claim_acquired"]:
                raise LiveSoakBlocked(
                    "LIVE_WARM_ADMISSION_INVALID",
                    "warm focused semantic did not use the claim-free MEDIUM path",
                )
            latency, _ = _native_call(
                provider,
                repository=repository,
                path=rust_file,
                query=query,
                resource_class="MEDIUM",
            )
            warm_latency.append(latency)

        workspace_status = semantic_provider_resource_status(
            provider,
            workspace=repository,
            path=".",
        )
        with governor.semantic_native_claim(
            mode="workspace",
            cost="HEAVY",
            resource_status=workspace_status,
        ) as lease:
            if not lease["allowed"] or not lease["claim_acquired"]:
                raise LiveSoakBlocked(
                    "LIVE_WORKSPACE_CLAIM_DENIED",
                    "warm workspace semantic did not acquire the HEAVY claim",
                )
            latency, _ = _native_call_until_handled(
                provider,
                repository=repository,
                path=".",
                query=query,
                resource_class="HEAVY",
                timeout_seconds=min(35.0, idle_timeout_seconds),
                poll_seconds=poll_seconds,
            )
            workspace_latency.append(latency)

        stopped = wait_for_status(
            provider,
            repository,
            rust_file,
            lambda status: status.get("lifecycle_state") == "STOPPED",
            timeout_seconds=idle_timeout_seconds,
            poll_seconds=poll_seconds,
        )
        cycle_rows.append(
            {
                "cycle": index + 1,
                "cold_latency_ms": cold_latency[-1],
                "warm_latency_ms": warm_latency[-1],
                "workspace_latency_ms": workspace_latency[-1],
                "process_instance_id": process_id,
                "working_set_bytes": warm.get("working_set_bytes"),
                "peak_working_set_bytes": warm.get("peak_working_set_bytes"),
                "restart_count": warm.get("restart_count"),
                "drain_count": stopped.get("drain_count"),
            }
        )

    # Fault injection is deliberately inside the real governor/status path;
    # it validates owner-safe release without fabricating a Connector binding.
    final_stopped = semantic_provider_resource_status(
        provider,
        workspace=repository,
        path=rust_file,
    )
    try:
        with governor.semantic_native_claim(
            mode="single_file",
            cost="HEAVY",
            resource_status=final_stopped,
        ) as lease:
            if not lease["allowed"]:
                raise LiveSoakBlocked("LIVE_EXCEPTION_CLAIM_DENIED", "fault-injection claim was denied")
            raise RuntimeError("live soak provider fault injection")
    except RuntimeError as exc:
        if str(exc) != "live soak provider fault injection":
            raise
    if governor._claim_rows(active_only=True):
        raise LiveSoakBlocked("LIVE_EXCEPTION_CLAIM_LEAK", "fault injection left an active claim")

    return {
        "cycles": cycle_rows,
        "metrics": {
            "cold_semantic_latency_ms": distribution(cold_latency),
            "warm_semantic_latency_ms": distribution(warm_latency),
            "workspace_semantic_latency_ms": distribution(workspace_latency),
            "lsp_working_set_bytes": distribution(working_sets),
            "lsp_peak_working_set_bytes": distribution(peak_working_sets),
            "claim_wait_ms": distribution(claim_wait),
            "working_set_unknown_count": cycles - len(working_sets),
            "peak_working_set_unknown_count": cycles - len(peak_working_sets),
        },
        "final_active_claim_count": len(governor._claim_rows(active_only=True)),
        "final_lsp_resource": final_stopped,
        "idle_teardown_count": len(cycle_rows),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repository", type=Path, default=Path.cwd())
    result.add_argument("--output", type=Path)
    result.add_argument("--cycles", type=int, default=MINIMUM_LIFECYCLE_CYCLES)
    result.add_argument("--file", default=os.environ.get("WEBCODEX_LIVE_SOAK_FILE", ""))
    result.add_argument("--query", default=os.environ.get("WEBCODEX_LIVE_SOAK_QUERY", ""))
    result.add_argument(
        "--connector-artifact-id",
        default=os.environ.get("WEBCODEX_LIVE_CONNECTOR_ARTIFACT_ID", ""),
    )
    result.add_argument(
        "--runner-artifact-id",
        default=os.environ.get("WEBCODEX_LIVE_RUNNER_ARTIFACT_ID", ""),
    )
    result.add_argument("--idle-timeout-seconds", type=float, default=120.0)
    result.add_argument("--poll-seconds", type=float, default=1.0)
    return result


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    started_at = utc_now()
    repository = args.repository.resolve(strict=True)
    try:
        if args.cycles < MINIMUM_LIFECYCLE_CYCLES:
            raise LiveSoakBlocked(
                "LIVE_CYCLE_COUNT_TOO_SMALL",
                f"live acceptance requires at least {MINIMUM_LIFECYCLE_CYCLES} cycles",
            )
        rust_file = _relative_rust_file(repository, args.file)
        query = _query(args.query)
        connector_artifact = _bounded_label(
            args.connector_artifact_id,
            name="--connector-artifact-id",
        )
        runner_artifact = _bounded_label(
            args.runner_artifact_id,
            name="--runner-artifact-id",
        )
        binding = resolve_live_binding(repository, rust_file)
        ledger = OrchestrationLedger(repository)
        initial = wait_for_status(
            binding.provider,
            repository,
            rust_file,
            lambda status: status.get("lifecycle_state") == "STOPPED",
            timeout_seconds=max(1.0, args.idle_timeout_seconds),
            poll_seconds=max(0.1, args.poll_seconds),
        )
        conflict = atomic_live_conflict(
            repository=repository,
            provider=binding.provider,
            rust_file=rust_file,
            query=query,
            ledger=ledger,
        )
        wait_for_status(
            binding.provider,
            repository,
            rust_file,
            lambda status: status.get("lifecycle_state") == "STOPPED",
            timeout_seconds=max(1.0, args.idle_timeout_seconds),
            poll_seconds=max(0.1, args.poll_seconds),
        )
        cycle_evidence = run_cycles(
            repository=repository,
            provider=binding.provider,
            rust_file=rust_file,
            query=query,
            cycles=args.cycles,
            idle_timeout_seconds=max(1.0, args.idle_timeout_seconds),
            poll_seconds=max(0.1, args.poll_seconds),
            ledger=ledger,
        )
        health = ledger_health(repository)
        hard_acceptance = {
            "minimum_lifecycle_cycles_passed": len(cycle_evidence["cycles"]) >= MINIMUM_LIFECYCLE_CYCLES,
            "atomic_conflict_exactly_one_winner": bool(conflict["semantic_allowed"]) ^ bool(conflict["managed_allowed"]),
            "heavy_overlap_detected_count_zero": health.get("heavy_overlap_detected_count") == 0,
            "orphan_process_count_zero": health.get("orphan_process_count") == 0,
            "active_heavy_claim_zero": health.get("active_heavy_claim_count") == 0,
            "active_write_fences_zero": health.get("active_write_fence_count") == 0,
            "stale_orchestration_runs_zero": health.get("stale_orchestration_run_count") == 0,
            "fault_injection_claim_released": cycle_evidence["final_active_claim_count"] == 0,
            "final_lsp_stopped": cycle_evidence["final_lsp_resource"].get("lifecycle_state") == "STOPPED",
        }
        report = {
            "schema_version": LIVE_SOAK_SCHEMA_VERSION,
            "mode": "real_connector_runner_rust_analyzer",
            "started_at": started_at,
            "finished_at": utc_now(),
            "git_head": git_head(repository),
            "source_fingerprint": source_fingerprint(repository),
            "artifacts": {
                "connector": connector_artifact,
                "runner": runner_artifact,
                "rust_analyzer_version": binding.rust_analyzer_version,
            },
            "scope": {"file": rust_file, "query": query, "cycles": args.cycles},
            "initial_lsp_resource": initial,
            "atomic_conflict": conflict,
            **cycle_evidence,
            "ledger_health": health,
            "hard_acceptance": hard_acceptance,
            "passed": all(hard_acceptance.values()),
        }
        _write_report(report, args.output)
        return 0 if report["passed"] else 1
    except LiveSoakBlocked as exc:
        report = {
            "schema_version": LIVE_SOAK_SCHEMA_VERSION,
            "mode": "real_connector_runner_rust_analyzer",
            "started_at": started_at,
            "finished_at": utc_now(),
            "git_head": git_head(repository),
            "status": "blocked",
            "blocker": {"code": exc.code, "message": str(exc)},
            "passed": False,
        }
        _write_report(report, args.output)
        return 2


if __name__ == "__main__":
    sys.exit(main())
