#!/usr/bin/env python3
"""Preflight or apply evidence-only canonical ledger recovery.

The default command is read-only and prints a JSON preflight receipt.  Apply
requires that receipt, a separately captured stopped-runtime receipt, a new
rollback backup destination, and explicit operator authority.  It never
replays unknown effects or imports controller authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from coding_tools_mcp.ledger_evidence_recovery import (  # noqa: E402
    LedgerEvidenceRecoveryError,
    apply_evidence_recovery,
    capture_quiesce_receipt,
    preflight_evidence_recovery,
)


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_RECEIPT_INVALID") from exc
    if not isinstance(value, dict):
        raise LedgerEvidenceRecoveryError("RECOVERY_PREFLIGHT_RECEIPT_INVALID")
    return value


def _write_json(path: Path | None, value: object) -> None:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path is None:
        print(encoded, end="")
        return
    target = path.resolve()
    if target.exists():
        raise LedgerEvidenceRecoveryError("RECOVERY_OUTPUT_MUST_BE_NEW")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(encoded, encoding="utf-8", newline="\n")
    target.chmod(0o400)
    print(encoded, end="")


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--allow-run-id", action="append", required=True)
    parser.add_argument("--allow-existing-run-id", action="append", default=[])
    parser.add_argument("--allow-problem-id", action="append", required=True)
    parser.add_argument("--allow-evidence-id", action="append", default=[])
    parser.add_argument("--allow-existing-evidence-id", action="append", default=[])
    parser.add_argument("--expected-current-sha256", default="")
    parser.add_argument("--expected-current-logical-sha256", default="")
    parser.add_argument("--expected-candidate-sha256", default="")
    parser.add_argument("--expected-candidate-logical-sha256", default="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight", help="read-only candidate and clone proof")
    _common(preflight)
    preflight.add_argument("--receipt-out", type=Path)

    quiesce = sub.add_parser("capture-quiesce", help="capture a stopped-runtime receipt; never stops anything")
    quiesce.add_argument("--workspace", type=Path, required=True)
    quiesce.add_argument("--output", type=Path, required=True)
    quiesce.add_argument("--runtime-stopped", action="store_true")
    quiesce.add_argument("--authority", required=True)

    apply = sub.add_parser("apply", help="apply the exact evidence-only preflight atomically")
    _common(apply)
    apply.add_argument("--preflight-receipt", type=Path, required=True)
    apply.add_argument("--quiesce-receipt", type=Path, required=True)
    apply.add_argument("--rollback-backup", type=Path, required=True)
    apply.add_argument("--runtime-stopped", action="store_true")
    apply.add_argument("--authority", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "capture-quiesce":
            result = capture_quiesce_receipt(
                args.workspace,
                output=args.output,
                runtime_stopped=bool(args.runtime_stopped),
                operator_authority=args.authority,
            )
            _write_json(None, result)
            return 0
        if args.command == "preflight":
            result = preflight_evidence_recovery(
                args.workspace,
                candidate=args.candidate,
                expected_current_sha256=args.expected_current_sha256,
                expected_current_logical_sha256=args.expected_current_logical_sha256,
                expected_candidate_sha256=args.expected_candidate_sha256,
                expected_candidate_logical_sha256=args.expected_candidate_logical_sha256,
                allowed_run_ids=set(args.allow_run_id),
                allowed_existing_run_ids=set(args.allow_existing_run_id),
                allowed_problem_ids=set(args.allow_problem_id),
                allowed_evidence_ids=set(args.allow_evidence_id),
                allowed_existing_evidence_ids=set(args.allow_existing_evidence_id),
            )
            _write_json(args.receipt_out, result)
            return 0
        preflight_receipt = _load_json(args.preflight_receipt)
        result = apply_evidence_recovery(
            args.workspace,
            candidate=args.candidate,
            preflight=preflight_receipt,
            quiesce_receipt=args.quiesce_receipt,
            rollback_backup=args.rollback_backup,
            runtime_stopped=bool(args.runtime_stopped),
            authority=args.authority,
        )
        _write_json(None, result)
        return 0
    except (LedgerEvidenceRecoveryError, OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:1000]}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
