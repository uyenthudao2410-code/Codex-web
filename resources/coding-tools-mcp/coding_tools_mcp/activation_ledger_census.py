#!/usr/bin/env python3
"""Emit one immutable, read-only Gate 0 census for a stopped MCP runtime."""

from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import nullcontext
from pathlib import Path

from .ledger_file_gate import LedgerGateTimeout, ledger_access_gate
from .lifecycle_census import lifecycle_census, open_lifecycle_census_snapshot, read_task_projection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--source-checkpoint-json", default="")
    parser.add_argument("--hold-exclusive", action="store_true")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve(strict=True)
    ledger_path = workspace / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    gate = ledger_access_gate(ledger_path, exclusive=True, timeout_seconds=5.0) if args.hold_exclusive else nullcontext()
    with gate:
        with open_lifecycle_census_snapshot(workspace) as snapshot:
            result = lifecycle_census(
                snapshot,
                workspace=workspace,
                observed_at=time.time(),
                grace_seconds=15 * 60,
                stale_after_seconds=24 * 60 * 60,
                projection=read_task_projection(workspace),
            )
            checkpoint = None
            if args.source_checkpoint_json:
                try:
                    candidate = json.loads(args.source_checkpoint_json)
                    checkpoint = candidate if isinstance(candidate, dict) else None
                except json.JSONDecodeError:
                    checkpoint = None
                rows = getattr(snapshot.facts, "_checkpoints_by_run", {})
                checkpoint_verified = False
                if checkpoint:
                    requested_id = str(checkpoint.get("checkpoint_id") or "")
                    requested_run = str(checkpoint.get("run_id") or "")
                    requested_wave = str(checkpoint.get("wave_id") or "")
                    requested_proof = str(checkpoint.get("proof_fingerprint") or "")
                    requested_head = str(checkpoint.get("git_head") or "")
                    for rowset in rows.values():
                        for row in rowset:
                            if (
                                str(row.get("checkpoint_id") or "") == requested_id
                                and str(row.get("run_id") or "") == requested_run
                                and str(row.get("wave_id") or "") == requested_wave
                                and str(row.get("proof_fingerprint") or "") == requested_proof
                                and str(row.get("git_head") or "") == requested_head
                                and str(row.get("status") or "") == "accepted"
                            ):
                                checkpoint_verified = True
                                break
                        if checkpoint_verified:
                            break
                result["source_checkpoint_verified"] = checkpoint_verified
            else:
                result["source_checkpoint_verified"] = True
        result["workspace"] = str(workspace)
        result["ledger_path"] = str(ledger_path)
        result["exclusive_gate_held"] = bool(args.hold_exclusive)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")), flush=True)
        if args.hold_exclusive:
            # Keep the application-level ledger gate across Recovery Host's
            # epoch-store create. EOF or process termination also releases it.
            sys.stdin.readline()
    return 0


def _run_cli() -> int:
    try:
        return main()
    except LedgerGateTimeout:
        # Machine-readable typed cause only. Do not put the ledger path or the
        # raw lock exception into the cross-process failure channel.
        print("ACTIVATION_LEDGER_CENSUS_LOCK_TIMEOUT", file=sys.stderr)
        return 75


if __name__ == "__main__":
    try:
        raise SystemExit(_run_cli())
    except Exception as exc:  # stdout must remain machine-readable only on success.
        print(f"activation ledger census failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
