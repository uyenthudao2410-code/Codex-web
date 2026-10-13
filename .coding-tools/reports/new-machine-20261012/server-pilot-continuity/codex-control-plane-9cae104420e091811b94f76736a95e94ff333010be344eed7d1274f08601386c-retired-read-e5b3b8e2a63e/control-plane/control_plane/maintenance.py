"""Explicit, local-only maintenance operations for the control-plane database.

This module has no HTTP client and never starts the service. It can create a
new, recovery-locked restore candidate, but never replaces a live database or
changes a running service's admission: those operations require the separate
operator-approved recovery/reconciliation runbook.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from typing import Sequence

from .http_api import _package_source_sha256
from .store import (
    ControlPlaneError,
    create_recovery_restore_candidate,
    create_verified_backup,
    inspect_verified_snapshot,
)


def _snapshot(args: argparse.Namespace) -> int:
    result = create_verified_backup(args.source, args.destination)
    # Paths can reveal host layout, so the success receipt contains only
    # content-free snapshot metadata. The operator already supplied both paths.
    print(json.dumps({"operation": "verified_sqlite_snapshot", **result}, separators=(",", ":")))
    return 0


def _inspect_snapshot(args: argparse.Namespace) -> int:
    result = inspect_verified_snapshot(args.source, expected_sha256=args.expected_sha256)
    # This is a read-only restore preflight, not an admission or restore action.
    print(json.dumps({"operation": "verified_snapshot_inspection", **result}, separators=(",", ":")))
    return 0


def _package_fingerprint(_args: argparse.Namespace) -> int:
    # This is a source-only deployment-preparation operation. It does not
    # instantiate a store, open SQLite, start an HTTP listener, or read config.
    print(
        json.dumps(
            {
                "operation": "control_plane_package_source_fingerprint",
                "package_source_sha256": _package_source_sha256(),
            },
            separators=(",", ":"),
        )
    )
    return 0


def _prepare_recovery_restore(args: argparse.Namespace) -> int:
    result = create_recovery_restore_candidate(
        args.source,
        args.destination,
        expected_sha256=args.expected_sha256,
    )
    # This is a new, non-overwriting candidate with durable recovery admission,
    # not a service/database switch or a completed restore.
    print(json.dumps({"operation": "recovery_restore_candidate", **result}, separators=(",", ":")))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="create a verified, non-overwriting SQLite snapshot")
    snapshot.add_argument("--source", required=True, help="existing control-plane SQLite file")
    snapshot.add_argument("--destination", required=True, help="new snapshot file path")
    inspect_snapshot = commands.add_parser("inspect-snapshot", help="read a completed snapshot before restore planning")
    inspect_snapshot.add_argument("--source", required=True, help="existing snapshot SQLite file without WAL sidecars")
    inspect_snapshot.add_argument("--expected-sha256", default=None, help="optional exact SHA-256 from the snapshot receipt")
    commands.add_parser("package-fingerprint", help="print the source fingerprint for a selected deployment package")
    recovery_candidate = commands.add_parser(
        "prepare-recovery-restore",
        help="make a new recovery-locked candidate from an inspected snapshot",
    )
    recovery_candidate.add_argument("--source", required=True, help="existing verified snapshot without WAL sidecars")
    recovery_candidate.add_argument("--destination", required=True, help="new recovery-candidate SQLite path")
    recovery_candidate.add_argument("--expected-sha256", default=None, help="optional exact SHA-256 from the source snapshot receipt")
    args = parser.parse_args(argv)
    try:
        return {
            "snapshot": _snapshot,
            "inspect-snapshot": _inspect_snapshot,
            "package-fingerprint": _package_fingerprint,
            "prepare-recovery-restore": _prepare_recovery_restore,
        }[args.command](args)
    except ControlPlaneError as error:
        print(json.dumps({"error": {"code": error.code}}, separators=(",", ":")), file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error, RuntimeError):
        print(json.dumps({"error": {"code": "CONTROL_PLANE_SNAPSHOT_FAILED"}}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
