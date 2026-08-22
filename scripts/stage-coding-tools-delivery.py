#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

CANONICAL_LEDGER = ".coding-tools/orchestration/ledger.sqlite3"
DELIVERY_RECEIPT = ".coding-tools/delivery-snapshot.json"


def run_git(root: Path, args: list[str], *, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=text,
    )


def git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()).resolve()


def index_entry(root: Path) -> tuple[str, str]:
    result = run_git(root, ["ls-files", "--stage", "--", CANONICAL_LEDGER])
    line = result.stdout.strip()
    if not line:
        raise RuntimeError(f"canonical ledger is not staged: {CANONICAL_LEDGER}")
    metadata, path = line.split("\t", 1)
    if path.replace("\\", "/") != CANONICAL_LEDGER:
        raise RuntimeError("unexpected canonical ledger index path")
    mode, blob, stage = metadata.split()
    if stage != "0":
        raise RuntimeError("canonical ledger has an unresolved index stage")
    return mode, blob


def staged_receipt(root: Path) -> dict:
    result = run_git(root, ["show", f":{DELIVERY_RECEIPT}"])
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("staged delivery snapshot receipt is not valid JSON") from exc
    if receipt.get("schema_version") != 1:
        raise RuntimeError("staged delivery snapshot receipt schema is unsupported")
    if receipt.get("canonical_ledger") != CANONICAL_LEDGER:
        raise RuntimeError("staged delivery snapshot receipt targets the wrong ledger")
    return receipt


def sqlite_integrity(path: Path) -> tuple[int, int]:
    connection = sqlite3.connect(path, timeout=10.0)
    try:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity.lower() != "ok":
            raise RuntimeError(f"SQLite integrity_check failed: {integrity}")
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()
    return path.stat().st_size, user_version


def materialize_index_blob(root: Path, blob: str, target: Path) -> None:
    with target.open("wb") as handle:
        result = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", blob],
            check=False,
            stdout=handle,
            stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"unable to materialize staged ledger blob: {message}")


def verify_index(root: Path) -> tuple[str, int, int]:
    _mode, blob = index_entry(root)
    receipt = staged_receipt(root)
    if receipt.get("ledger_blob") != blob:
        raise RuntimeError("staged delivery snapshot receipt does not match the staged ledger blob")
    with tempfile.TemporaryDirectory(prefix="coding-tools-ledger-index-") as temp_dir:
        snapshot = Path(temp_dir) / "ledger.sqlite3"
        materialize_index_blob(root, blob, snapshot)
        size_bytes, user_version = sqlite_integrity(snapshot)
    if int(receipt.get("size_bytes", -1)) != size_bytes:
        raise RuntimeError("staged delivery snapshot receipt size does not match the staged ledger")
    if int(receipt.get("user_version", -1)) != user_version:
        raise RuntimeError("staged delivery snapshot receipt user_version does not match the staged ledger")
    return blob, size_bytes, user_version


def write_receipt(root: Path, blob: str, size_bytes: int, user_version: int) -> None:
    receipt_path = root / DELIVERY_RECEIPT
    receipt = {
        "schema_version": 1,
        "snapshot_id": str(time.time_ns()),
        "captured_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "canonical_ledger": CANONICAL_LEDGER,
        "ledger_blob": blob,
        "size_bytes": size_bytes,
        "user_version": user_version,
    }
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    run_git(root, ["add", "--", DELIVERY_RECEIPT])


def snapshot_live_ledger(source: Path, target: Path) -> None:
    uri = f"file:{source.as_posix()}?mode=ro"
    source_connection = sqlite3.connect(uri, uri=True, timeout=10.0)
    destination_connection = sqlite3.connect(target, timeout=10.0)
    try:
        source_connection.execute("PRAGMA busy_timeout=10000")
        source_connection.backup(destination_connection, pages=256, sleep=0.01)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()
    sqlite_integrity(target)


def stage_delivery(root: Path) -> tuple[str, int, int]:
    evidence_root = root / ".coding-tools"
    ledger = root / CANONICAL_LEDGER
    if not evidence_root.exists():
        run_git(root, ["add", "-A", "--", ".coding-tools"])
        print("coding-tools delivery stage: .coding-tools is absent")
        return "", 0, 0
    if not ledger.is_file():
        raise RuntimeError(f"canonical ledger is missing: {CANONICAL_LEDGER}")

    run_git(
        root,
        ["add", "-A", "--", ".coding-tools", f":(exclude){CANONICAL_LEDGER}"],
    )

    current_entry = run_git(root, ["ls-files", "--stage", "--", CANONICAL_LEDGER]).stdout.strip()
    mode = current_entry.split(None, 1)[0] if current_entry else "100644"

    with tempfile.TemporaryDirectory(prefix="coding-tools-ledger-stage-") as temp_dir:
        snapshot = Path(temp_dir) / "ledger.sqlite3"
        snapshot_live_ledger(ledger, snapshot)
        size_bytes, user_version = sqlite_integrity(snapshot)
        blob = run_git(root, ["hash-object", "-w", "--", str(snapshot)]).stdout.strip()
        if len(blob) != 40:
            raise RuntimeError("git hash-object did not return a SHA-1 object id")
        run_git(
            root,
            ["update-index", "--add", "--cacheinfo", f"{mode},{blob},{CANONICAL_LEDGER}"],
        )

    write_receipt(root, blob, size_bytes, user_version)

    verified_blob, size_bytes, user_version = verify_index(root)
    if verified_blob != blob:
        raise RuntimeError("staged ledger blob changed during verification")
    return verified_blob, size_bytes, user_version


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage .coding-tools with a WAL-safe canonical SQLite ledger snapshot."
    )
    parser.add_argument(
        "--verify-index",
        action="store_true",
        help="Verify that the canonical ledger currently staged in the Git index is a valid SQLite database.",
    )
    args = parser.parse_args()
    root = git_root()
    if args.verify_index:
        blob, size_bytes, user_version = verify_index(root)
        print(
            f"coding-tools staged ledger check: PASS blob={blob} size_bytes={size_bytes} user_version={user_version}"
        )
        return 0

    blob, size_bytes, user_version = stage_delivery(root)
    if blob:
        print(
            f"coding-tools delivery stage: PASS ledger_blob={blob} size_bytes={size_bytes} user_version={user_version}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
