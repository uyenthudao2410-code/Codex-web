from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from .fs_utils import is_relative_to


MAX_ACCEPTED_FILE_RECEIPTS = 256
MAX_ACCEPTED_RECEIPT_FILE_BYTES = 16 * 1024 * 1024
MAX_ACCEPTED_RECEIPT_TOTAL_BYTES = 64 * 1024 * 1024


def _accepted_file_receipts(
    workspace: Path,
    modified_files: Any,
    *,
    acceptance_files: Any = None,
    run_id: str = "",
    wave_id: str = "",
) -> dict[str, Any]:
    """Build content-free, bounded file receipts for one final acceptance."""
    root = workspace.resolve()
    explicit_attestation = acceptance_files is not None
    if explicit_attestation:
        if not isinstance(acceptance_files, list) or not acceptance_files:
            raise ToolFailure(
                "ACCEPTANCE_FILES_INVALID",
                "acceptance_files must be a non-empty array when supplied.",
                category="validation",
            )
        if not str(run_id or "").strip() or not str(wave_id or "").strip():
            raise ToolFailure(
                "ACCEPTANCE_CONTEXT_REQUIRED",
                "Explicit acceptance file attestations require a current run_id and wave_id.",
                category="runtime",
            )
        raw_items = list(acceptance_files)
    else:
        raw_items = list(modified_files or []) if isinstance(modified_files, list) else []
    normalized: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    incomplete_reasons: set[str] = set()
    for item in raw_items:
        raw = item.get("path") if isinstance(item, dict) else item
        expected_sha256 = str(item.get("sha256") or "").strip().lower() if explicit_attestation and isinstance(item, dict) else ""
        value = str(raw or "").strip().replace("\\", "/")
        while value.startswith("./"):
            value = value[2:]
        if explicit_attestation and (not isinstance(item, dict) or not value):
            raise ToolFailure(
                "ACCEPTANCE_FILE_INVALID",
                "Each acceptance file attestation must contain a non-empty workspace-relative path.",
                category="validation",
            )
        if not value:
            continue
        if value == ".coding-tools" or value.startswith(".coding-tools/"):
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_INVALID",
                    "Runtime evidence under .coding-tools cannot be used as an explicit source-file attestation.",
                    category="validation",
                    details={"path": value},
                )
            continue
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_INVALID",
                    "Acceptance file paths must stay within the governed workspace.",
                    category="validation",
                    details={"path": value},
                )
            incomplete_reasons.add("unsafe_path")
            continue
        target = (root / relative).resolve(strict=False)
        if not is_relative_to(target, root):
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_INVALID",
                    "Acceptance file paths must stay within the governed workspace.",
                    category="validation",
                    details={"path": value},
                )
            incomplete_reasons.add("outside_workspace")
            continue
        portable = relative.as_posix()
        if explicit_attestation:
            if len(expected_sha256) != 64 or any(char not in "0123456789abcdef" for char in expected_sha256):
                raise ToolFailure(
                    "ACCEPTANCE_FILE_SHA_INVALID",
                    "Each acceptance file attestation must provide a 64-character SHA-256 digest.",
                    category="validation",
                    details={"path": portable},
                )
            if portable in seen_paths:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_DUPLICATE",
                    "Each explicitly attested acceptance path may appear only once.",
                    category="validation",
                    details={"path": portable},
                )
        if portable not in seen_paths:
            seen_paths.add(portable)
            normalized.append({"path": portable, "expected_sha256": expected_sha256})
    if len(normalized) > MAX_ACCEPTED_FILE_RECEIPTS:
        if explicit_attestation:
            raise ToolFailure(
                "ACCEPTANCE_FILES_LIMIT_EXCEEDED",
                "Too many files were supplied for explicit final-acceptance attestation.",
                category="validation",
                details={"limit": MAX_ACCEPTED_FILE_RECEIPTS},
            )
        incomplete_reasons.add("too_many_files")
        normalized = normalized[:MAX_ACCEPTED_FILE_RECEIPTS]

    receipts: list[dict[str, Any]] = []
    total_bytes = 0
    for normalized_item in normalized:
        portable = normalized_item["path"]
        expected_sha256 = normalized_item["expected_sha256"]
        target = (root / Path(portable)).resolve(strict=False)
        if not target.exists():
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_NOT_FOUND",
                    "An explicitly attested acceptance file does not exist.",
                    category="validation",
                    details={"path": portable},
                )
            receipts.append({"path": portable, "state": "missing", "sha256": None, "size_bytes": 0})
            continue
        if not target.is_file():
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_NOT_REGULAR",
                    "An explicitly attested acceptance path is not a regular file.",
                    category="validation",
                    details={"path": portable},
                )
            incomplete_reasons.add("non_file")
            continue
        try:
            size = int(target.stat().st_size)
        except OSError as exc:
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_STAT_FAILED",
                    "Could not stat an explicitly attested acceptance file.",
                    category="runtime",
                    details={"path": portable, "error_type": type(exc).__name__},
                ) from exc
            incomplete_reasons.add("stat_failed")
            continue
        if size < 0 or size > MAX_ACCEPTED_RECEIPT_FILE_BYTES or total_bytes + size > MAX_ACCEPTED_RECEIPT_TOTAL_BYTES:
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_TOO_LARGE",
                    "An explicitly attested acceptance file exceeds the bounded receipt budget.",
                    category="validation",
                    details={"path": portable, "size_bytes": size},
                )
            incomplete_reasons.add("byte_limit")
            continue
        digest = hashlib.sha256()
        try:
            with target.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        except OSError as exc:
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_READ_FAILED",
                    "Could not read an explicitly attested acceptance file.",
                    category="runtime",
                    details={"path": portable, "error_type": type(exc).__name__},
                ) from exc
            incomplete_reasons.add("read_failed")
            continue
        total_bytes += size
        observed_sha256 = digest.hexdigest()
        if explicit_attestation and observed_sha256 != expected_sha256:
            raise ToolFailure(
                "ACCEPTANCE_FILE_SHA_MISMATCH",
                "An explicitly attested acceptance file does not match the expected SHA-256 digest.",
                category="validation",
                details={
                    "path": portable,
                    "expected_sha256": expected_sha256,
                    "observed_sha256": observed_sha256,
                },
            )
        receipt = {"path": portable, "state": "file", "sha256": observed_sha256, "size_bytes": size}
        if explicit_attestation:
            receipt.update({
                "receipt_kind": "existing_file_attestation",
                "expected_sha256": expected_sha256,
                "run_id": str(run_id),
                "wave_id": str(wave_id),
                "restart_safe": True,
                "content_addressed": True,
            })
        receipts.append(receipt)
    return {
        "schema_version": 1,
        "source": "explicit_acceptance_attestations" if explicit_attestation else "task_modified_files",
        "complete": not incomplete_reasons and len(receipts) == len(normalized),
        "count": len(receipts),
        "total_bytes": total_bytes,
        "files": receipts,
        "incomplete_reasons": sorted(incomplete_reasons),
    }
