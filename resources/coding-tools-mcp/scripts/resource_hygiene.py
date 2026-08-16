#!/usr/bin/env python3
"""Content-free build-cache telemetry and guarded soft cleanup.

This script never runs ``cargo clean``. Soft cleanup is limited to explicitly
named, old, non-primary ``target`` directories and is blocked unless managed
HEAVY ownership and local build/Connector process references can be observed
and confirmed inactive for those roots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    import psutil
except ImportError:  # pragma: no cover - optional runtime guard
    psutil = None  # type: ignore[assignment]


ACTIVE_LIFECYCLES = ("starting", "running", "terminating", "orphaned")
BUILD_PROCESS_NAMES = {
    "cargo",
    "cargo.exe",
    "rustc",
    "rustc.exe",
    "pytest",
    "pytest.exe",
    "python",
    "python.exe",
}
CONNECTOR_PROCESS_NAMES = {
    "webcodex",
    "webcodex.exe",
    "webcodex-runner",
    "webcodex-runner.exe",
}


class HygieneError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def directory_size(path: Path) -> int:
    if not path.exists() or path.is_symlink():
        return 0
    total = 0
    for root, _directories, files in os.walk(path, followlinks=False):
        for name in files:
            candidate = Path(root) / name
            try:
                if not candidate.is_symlink():
                    total += candidate.stat().st_size
            except OSError:
                continue
    return total


def newest_mtime(path: Path) -> float:
    newest = path.stat().st_mtime
    for root, directories, files in os.walk(path, followlinks=False):
        for name in [*directories, *files]:
            candidate = Path(root) / name
            try:
                if not candidate.is_symlink():
                    newest = max(newest, candidate.stat().st_mtime)
            except OSError:
                continue
    return newest


def target_identity(path: Path) -> str:
    normalized = os.path.normcase(str(path.resolve(strict=False)))
    return hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()[:16]


def load_state(state_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_state(state_path: Path, payload: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_name(f".{state_path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, state_path)


def validate_temporary_target(repository: Path, target: Path) -> Path:
    repository = repository.resolve(strict=True)
    target = target.resolve(strict=False)
    primary_target = (repository / "target").resolve(strict=False)
    if target == primary_target or primary_target in target.parents:
        raise HygieneError("primary repository target requires manual cargo clean policy")
    if target.name.lower() != "target":
        raise HygieneError("soft cleanup targets must be explicitly named target directories")
    if target.is_symlink():
        raise HygieneError("soft cleanup refuses symlink targets")
    if repository == target or (
        repository in target.parents and ".git" in target.parts
    ):
        raise HygieneError("soft cleanup target is inside protected repository metadata")
    return target


def active_heavy_claim_count(ledger_path: Path) -> int:
    if not ledger_path.exists():
        return 0
    uri = f"file:{ledger_path.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            claims_exist = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='checkout_resource_claims'"
            ).fetchone()
            if claims_exist:
                row = connection.execute(
                    """SELECT COUNT(*) FROM checkout_resource_claims
                       WHERE resource_class='HEAVY' AND lifecycle_state='active'"""
                ).fetchone()
            else:
                row = connection.execute(
                    """SELECT COUNT(*) FROM managed_process_jobs
                       WHERE resource_class='HEAVY'
                         AND lifecycle_state IN (?,?,?,?)""",
                    ACTIVE_LIFECYCLES,
                ).fetchone()
        finally:
            connection.close()
        return int(row[0] or 0) if row else 0
    except sqlite3.Error as exc:
        raise HygieneError("unable to verify managed HEAVY ownership") from exc


def _path_within(value: object, root: Path) -> bool:
    text = str(value or "").strip().strip('"')
    if not text:
        return False
    try:
        candidate = Path(text).resolve(strict=False)
        candidate.relative_to(root)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def process_guards(targets: Iterable[Path]) -> dict[str, int | bool]:
    roots = [target.resolve(strict=False) for target in targets]
    if psutil is None:
        return {
            "observed": False,
            "active_build_process_count": 0,
            "active_connector_reference_count": 0,
        }
    build_count = 0
    connector_count = 0
    for process in psutil.process_iter(["name", "cwd", "cmdline", "exe"]):
        try:
            name = str(process.info.get("name") or "").lower()
            values = [process.info.get("cwd"), process.info.get("exe")]
            values.extend(process.info.get("cmdline") or [])
            referenced = any(
                _path_within(value, root) or _path_within(value, root.parent)
                for root in roots
                for value in values
            )
            if not referenced:
                continue
            if name in CONNECTOR_PROCESS_NAMES:
                connector_count += 1
            elif name in BUILD_PROCESS_NAMES:
                build_count += 1
        except (psutil.Error, OSError, ValueError):
            continue
    return {
        "observed": True,
        "active_build_process_count": build_count,
        "active_connector_reference_count": connector_count,
    }


def disk_snapshot(
    repository: Path,
    temporary_targets: Iterable[Path] = (),
    *,
    state_path: Path | None = None,
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    primary = repository / "target"
    validated = [
        validate_temporary_target(repository, target) for target in temporary_targets
    ]
    state = load_state(state_path or repository / ".coding-tools/resource-hygiene.json")
    temporary_rows = [
        {
            "target_id": target_identity(target),
            "bytes": directory_size(target),
            "exists": target.exists(),
        }
        for target in validated
    ]
    return {
        "schema_version": 1,
        "observed_at": utc_now(),
        "target_total_bytes": directory_size(primary),
        "debug_incremental_bytes": directory_size(primary / "debug/incremental"),
        "release_artifact_bytes": directory_size(primary / "release"),
        "temporary_worktree_target_bytes": sum(
            int(row["bytes"]) for row in temporary_rows
        ),
        "temporary_target_count": len(temporary_rows),
        "temporary_targets": temporary_rows,
        "last_soft_cleanup_at": state.get("last_soft_cleanup_at"),
        "last_hard_cleanup_at": state.get("last_hard_cleanup_at"),
        "hard_cleanup_policy": "manual_cargo_clean_only",
    }


def soft_cleanup(
    repository: Path,
    temporary_targets: Iterable[Path],
    *,
    older_than_hours: float,
    state_path: Path | None = None,
    process_observer: Callable[[Iterable[Path]], dict[str, int | bool]] = process_guards,
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    targets = [
        validate_temporary_target(repository, target) for target in temporary_targets
    ]
    if not targets:
        raise HygieneError("soft cleanup requires at least one explicit temporary target")
    active_heavy = active_heavy_claim_count(
        repository / ".coding-tools/orchestration/ledger.sqlite3"
    )
    guards = process_observer(targets)
    if active_heavy:
        raise HygieneError("soft cleanup blocked by an active HEAVY scheduling claim")
    if guards.get("observed") is not True:
        raise HygieneError("soft cleanup blocked because process ownership is unavailable")
    if int(guards.get("active_build_process_count", 0) or 0):
        raise HygieneError("soft cleanup blocked by an active build process")
    if int(guards.get("active_connector_reference_count", 0) or 0):
        raise HygieneError("soft cleanup blocked by an active Connector reference")

    cutoff = time.time() - max(0.0, float(older_than_hours)) * 3600.0
    removed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for target in targets:
        identity = target_identity(target)
        if not target.exists():
            skipped.append({"target_id": identity, "reason": "missing"})
            continue
        if newest_mtime(target) > cutoff:
            skipped.append({"target_id": identity, "reason": "too_recent"})
            continue
        bytes_before = directory_size(target)
        shutil.rmtree(target)
        removed.append({"target_id": identity, "bytes_removed": bytes_before})

    state_file = state_path or repository / ".coding-tools/resource-hygiene.json"
    state = load_state(state_file)
    if removed:
        state["schema_version"] = 1
        state["last_soft_cleanup_at"] = utc_now()
        write_state(state_file, state)
    return {
        "schema_version": 1,
        "removed": removed,
        "skipped": skipped,
        "bytes_removed": sum(int(row["bytes_removed"]) for row in removed),
        "active_heavy_claim_count": active_heavy,
        "process_guards": guards,
        "hard_cleanup_performed": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=("snapshot", "soft-clean"))
    result.add_argument("--repository", type=Path, default=Path.cwd())
    result.add_argument("--temporary-target", type=Path, action="append", default=[])
    result.add_argument("--state-file", type=Path)
    result.add_argument("--older-than-hours", type=float, default=168.0)
    result.add_argument("--confirm-soft-clean", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.action == "snapshot":
            payload = disk_snapshot(
                args.repository,
                args.temporary_target,
                state_path=args.state_file,
            )
        else:
            if not args.confirm_soft_clean:
                raise HygieneError("soft cleanup requires --confirm-soft-clean")
            payload = soft_cleanup(
                args.repository,
                args.temporary_target,
                older_than_hours=args.older_than_hours,
                state_path=args.state_file,
            )
    except (HygieneError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "data": payload}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
