#!/usr/bin/env python3
"""Run the repeatable P2/P3 resource-hardening acceptance matrix."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resource_hygiene import disk_snapshot


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


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
    output = completed.stdout[-16_000:]
    return {
        "name": name,
        "passed": completed.returncode == 0,
        "exit_code": completed.returncode,
        "duration_ms": max(0, int((time.monotonic() - started) * 1000)),
        "command": command,
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


def ledger_health(repository: Path) -> dict[str, Any]:
    ledger = repository / ".coding-tools/orchestration/ledger.sqlite3"
    if not ledger.exists():
        return {"observed": False}
    uri = f"file:{ledger.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
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
        finally:
            connection.close()
    except sqlite3.Error:
        return {"observed": False, "error": "ledger_query_failed"}
    return {
        "observed": True,
        "active_managed_heavy_count": int(active_heavy),
        "orphan_process_count": int(orphaned),
        "active_write_fence_count": int(active_fences),
        "active_run_count": int(active_runs),
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
        "active_managed_heavy_zero": health.get("active_managed_heavy_count") == 0,
        "active_write_fences_zero": health.get("active_write_fence_count") == 0,
    }
    report = {
        "schema_version": 1,
        "started_at": started_at,
        "finished_at": utc_now(),
        "git_head": git_head(repository),
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
