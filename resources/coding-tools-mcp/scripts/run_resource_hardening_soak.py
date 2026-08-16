#!/usr/bin/env python3
"""Run the repeatable P2/P3 resource-hardening acceptance matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resource_hygiene import disk_snapshot


RESOURCE_POLICY_VERSION = "p2-p3-operational-hardening-v1"
FINGERPRINT_PATHS = (
    "crates/webcodex-process/Cargo.toml",
    "crates/webcodex-process/src/lib.rs",
    "crates/webcodex-process/src/unix.rs",
    "crates/webcodex-process/src/windows.rs",
    "crates/webcodex-process/tests/managed_child.rs",
    "crates/webcodex-runner/src/main_tests.rs",
    "crates/webcodex-runner/src/webcodex_runner/config.rs",
    "crates/webcodex-runner/src/webcodex_runner/lsp/mod.rs",
    "crates/webcodex-runner/src/webcodex_runner/lsp/supervisor.rs",
    "crates/webcodex-runner/src/webcodex_runner/lsp/navigation.rs",
    "crates/webcodex-runner/src/webcodex_runner/lsp/tests.rs",
    "crates/webcodex-runner/src/webcodex_runner/transport.rs",
    "crates/webcodex-runner/src/webcodex_runner/transport_tests.rs",
    "crates/webcodex-core/src/lsp_bridge.rs",
    "resources/coding-tools-mcp/coding_tools_mcp/context_tools.py",
    "resources/coding-tools-mcp/coding_tools_mcp/code_mode.py",
    "resources/coding-tools-mcp/coding_tools_mcp/execution_resources.py",
    "resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py",
    "resources/coding-tools-mcp/coding_tools_mcp/semantic_localization.py",
    "resources/coding-tools-mcp/coding_tools_mcp/tool_contract.py",
    "resources/coding-tools-mcp/scripts/resource_hygiene.py",
    "resources/coding-tools-mcp/scripts/run_live_connector_resource_soak.py",
    "resources/coding-tools-mcp/scripts/run_resource_hardening_soak.py",
    "resources/coding-tools-mcp/tests/test_execution_resources.py",
    "resources/coding-tools-mcp/tests/test_live_connector_resource_soak_script.py",
    "resources/coding-tools-mcp/tests/test_resource_hygiene_script.py",
    "resources/coding-tools-mcp/tests/test_task_state_and_build.py",
    "src/auth/middleware.rs",
    "src/connector_runtime/http.rs",
    "src/connector_runtime/semantic_bridge.rs",
    "src/tool_runtime/lsp_tools.rs",
    "src/tool_runtime/registry/input_schemas/lsp.rs",
    "src/tool_runtime/semantic_navigation.rs",
    "src/tool_runtime/tool_call.rs",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def sanitize_output_tail(output: str, cwd: Path) -> str:
    sanitized = output
    for path, replacement in (
        (cwd.resolve(strict=False), "<check-cwd>"),
        (Path.home().resolve(strict=False), "<home>"),
    ):
        for rendered in {str(path), path.as_posix()}:
            if rendered:
                sanitized = sanitized.replace(rendered, replacement)
    return sanitized[-16_000:]


def run_check(name: str, command: list[str], cwd: Path) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    # Passing checks contribute only bounded timing/exit evidence. Retain a
    # bounded output tail solely on failure, where it is needed to diagnose
    # the acceptance gap without turning the report into an output archive.
    output = (
        sanitize_output_tail(completed.stdout, cwd)
        if completed.returncode != 0
        else ""
    )
    display_command = list(command)
    if display_command and Path(display_command[0]) == Path(sys.executable):
        display_command[0] = "<python>"
    return {
        "name": name,
        "passed": completed.returncode == 0,
        "exit_code": completed.returncode,
        "duration_ms": max(0, int((time.monotonic() - started) * 1000)),
        "command": display_command,
        "output_tail": output,
    }


def git_head(repository: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def source_fingerprint(repository: Path) -> dict[str, Any]:
    aggregate = hashlib.sha256()
    files: list[dict[str, str]] = []
    for relative in FINGERPRINT_PATHS:
        path = repository / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
        files.append({"path": relative, "sha256": digest})
    return {
        "algorithm": "sha256(path_nul_file_sha256_lf)",
        "sha256": aggregate.hexdigest(),
        "files": files,
    }


def coding_tools_runtime_version(repository: Path) -> str:
    source = (
        repository
        / "resources/coding-tools-mcp/coding_tools_mcp/__init__.py"
    ).read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', source, re.MULTILINE)
    return match.group(1) if match else "unknown"


def ledger_health(repository: Path) -> dict[str, Any]:
    ledger = repository / ".coding-tools/orchestration/ledger.sqlite3"
    if not ledger.exists():
        return {"observed": False}
    uri = f"file:{ledger.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            claims_exist = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='checkout_resource_claims'"
            ).fetchone()
            if claims_exist:
                active_heavy = connection.execute(
                    """SELECT COUNT(*) FROM checkout_resource_claims
                       WHERE resource_class='HEAVY' AND lifecycle_state='active'"""
                ).fetchone()[0]
            else:
                active_heavy = connection.execute(
                    """SELECT COUNT(*) FROM managed_process_jobs
                       WHERE resource_class='HEAVY'
                         AND lifecycle_state IN ('starting','running','terminating','orphaned')"""
                ).fetchone()[0]
            orphaned = connection.execute(
                """SELECT COUNT(*) FROM managed_process_jobs
                   WHERE lifecycle_state='orphaned'"""
            ).fetchone()[0]
            active_fences = connection.execute(
                """SELECT COUNT(*) FROM write_fences
                   WHERE status='active' AND expires_at>?""",
                (time.time(),),
            ).fetchone()[0]
            active_runs = connection.execute(
                "SELECT COUNT(*) FROM runs WHERE status='active'"
            ).fetchone()[0]
            now = time.time()
            cutoff = datetime.fromtimestamp(
                now - 24 * 60 * 60,
                timezone.utc,
            ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            stale_runs = 0
            candidates = connection.execute(
                """SELECT r.run_id, r.started_at,
                          MAX(e.event_time) AS event_time,
                          MAX(w.started_at) AS wave_started_at,
                          MAX(w.finished_at) AS wave_finished_at,
                          MAX(b.updated_at) AS background_updated_at,
                          MAX(l.updated_at) AS lane_updated_at,
                          MAX(h.created_at) AS handoff_created_at
                   FROM runs r
                   LEFT JOIN events e ON e.run_id=r.run_id
                   LEFT JOIN waves w ON w.run_id=r.run_id
                   LEFT JOIN background_operations b ON b.run_id=r.run_id
                   LEFT JOIN agent_lanes l ON l.run_id=r.run_id
                   LEFT JOIN handoff_capsules h ON h.run_id=r.run_id
                   WHERE r.status='active'
                   GROUP BY r.run_id, r.started_at"""
            ).fetchall()
            for candidate in candidates:
                run_id = str(candidate[0])
                latest_event = connection.execute(
                    "SELECT state_after FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                    (run_id,),
                ).fetchone()
                if latest_event and str(latest_event[0] or "").upper() == "ACCEPTING":
                    continue
                live_queries = (
                    (
                        "SELECT 1 FROM background_operations "
                        "WHERE run_id=? AND status='running' LIMIT 1",
                        (run_id,),
                    ),
                    (
                        "SELECT 1 FROM agent_lanes WHERE run_id=? "
                        "AND lifecycle IN ('active','waiting','idle') LIMIT 1",
                        (run_id,),
                    ),
                    (
                        "SELECT 1 FROM write_fences WHERE run_id=? "
                        "AND status='active' AND expires_at>? LIMIT 1",
                        (run_id, now),
                    ),
                    (
                        "SELECT 1 FROM controller_leases WHERE run_id=? "
                        "AND status='active' AND expires_at>? LIMIT 1",
                        (run_id, now),
                    ),
                )
                if any(connection.execute(query, params).fetchone() for query, params in live_queries):
                    continue
                activity = max(str(value or "") for value in candidate[1:])
                if activity and activity < cutoff:
                    stale_runs += 1
        finally:
            connection.close()
    except sqlite3.Error:
        return {"observed": False, "error": "ledger_query_failed"}
    return {
        "observed": True,
        "active_heavy_claim_count": int(active_heavy),
        "orphan_process_count": int(orphaned),
        "active_write_fence_count": int(active_fences),
        "active_run_count": int(active_runs),
        "stale_orchestration_run_count": stale_runs,
        "heavy_overlap_detected_count": 0 if int(active_heavy) <= 1 else int(active_heavy) - 1,
    }


def checks(repository: Path, *, include_root_semantic: bool) -> list[tuple[str, list[str], Path]]:
    package = repository / "resources/coding-tools-mcp"
    rows: list[tuple[str, list[str], Path]] = [
        (
            "managed_process_resource_snapshot",
            [
                "cargo",
                "test",
                "-p",
                "webcodex-process",
                "resource_snapshot_preserves_process_identity_and_unknown_semantics",
                "--",
                "--nocapture",
            ],
            repository,
        ),
        (
            "managed_process_owned_tree",
            [
                "cargo",
                "test",
                "-p",
                "webcodex-process",
                "explicit_terminate_kills_tree",
                "--",
                "--nocapture",
            ],
            repository,
        ),
        (
            "lsp_idle_teardown",
            [
                "cargo",
                "test",
                "-p",
                "webcodex-runner",
                "lsp_background_reaper_reclaims_idle_capacity_without_explicit_cleanup",
                "--",
                "--nocapture",
            ],
            repository,
        ),
        (
            "lsp_memory_pressure_matrix",
            [
                "cargo",
                "test",
                "-p",
                "webcodex-runner",
                "lsp_memory_",
                "--",
                "--nocapture",
            ],
            repository,
        ),
        (
            "semantic_heavy_conflict_and_fallback",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_execution_resources.py",
                "tests/test_task_state_and_build.py::ToolModeTests::test_prepare_coding_context_falls_back_before_native_call_during_heavy",
                "-q",
            ],
            package,
        ),
        (
            "smart_v3_tool_contract",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_code_mode_bindings.py::CodeModeHostBindingTests::test_metadata_stays_gated_and_smart_surface_is_unchanged",
                "-q",
            ],
            package,
        ),
        (
            "resource_hygiene_guards",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_resource_hygiene_script.py",
                "-q",
            ],
            package,
        ),
    ]
    if include_root_semantic:
        rows.append(
            (
                "native_semantic_cold_warm_scope",
                [
                    "cargo",
                    "test",
                    "-p",
                    "webcodex",
                    "native_semantic_bridge",
                    "--",
                    "--test-threads=1",
                ],
                repository,
            )
        )
    return rows


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repository", type=Path, default=Path.cwd())
    result.add_argument("--output", type=Path)
    result.add_argument(
        "--skip-root-semantic",
        action="store_true",
        help="Skip the root native-semantic regression when its native build toolchain is unavailable.",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repository = args.repository.resolve(strict=True)
    started_at = utc_now()
    results = [
        run_check(name, command, cwd)
        for name, command, cwd in checks(
            repository,
            include_root_semantic=not args.skip_root_semantic,
        )
    ]
    health = ledger_health(repository)
    hard_acceptance = {
        "checks_passed": all(result["passed"] for result in results),
        "orphan_process_count_zero": health.get("orphan_process_count") == 0,
        "heavy_overlap_detected_count_zero": health.get("heavy_overlap_detected_count") == 0,
        "active_heavy_claim_zero": health.get("active_heavy_claim_count") == 0,
        "active_write_fences_zero": health.get("active_write_fence_count") == 0,
        "stale_orchestration_runs_zero": health.get("stale_orchestration_run_count") == 0,
    }
    report = {
        "schema_version": 1,
        "started_at": started_at,
        "finished_at": utc_now(),
        "git_head": git_head(repository),
        "source_fingerprint": source_fingerprint(repository),
        "runtime": {
            "coding_tools_mcp_version": coding_tools_runtime_version(repository),
            "resource_policy_version": RESOURCE_POLICY_VERSION,
            "smart_profile": "smart-v3",
            "expected_public_tool_count": 8,
        },
        "mode": "real_process_and_synthetic_pressure_equivalent",
        "checks": results,
        "ledger_health": health,
        "disk": disk_snapshot(repository),
        "hard_acceptance": hard_acceptance,
        "passed": all(hard_acceptance.values()),
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
