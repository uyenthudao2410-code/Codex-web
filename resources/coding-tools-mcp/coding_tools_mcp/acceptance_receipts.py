from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import stat
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from .fs_utils import is_relative_to


MAX_ACCEPTED_FILE_RECEIPTS = 256
MAX_ACCEPTED_RECEIPT_FILE_BYTES = 16 * 1024 * 1024
MAX_ACCEPTED_RECEIPT_TOTAL_BYTES = 64 * 1024 * 1024
ACCEPTED_FILE_RECEIPT_SCHEMA_VERSION = 2
ACCEPTED_FILE_RECEIPT_KINDS = frozenset({
    "explicit_existing_file",
    "task_modified_file",
    "durable_wave_patch_surface",
})
_HEX_DIGITS = frozenset("0123456789abcdef")
_PROTECTED_ACCEPTANCE_ROOTS = frozenset({".coding-tools", ".git"})
_SOURCE_CHECKPOINT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$")


def _portable_path_key(value: Any) -> str:
    """Return the comparison key used by Windows source-path guards.

    Receipts retain the portable spelling supplied by the caller.  Only
    protected/dirty/lease comparisons use this key so a case-only spelling
    change cannot bypass a workspace safety boundary on Windows.
    """
    portable = _portable_path(value)
    return portable.casefold() if os.name == "nt" else portable


def _is_protected_acceptance_path(value: Any) -> bool:
    key = _portable_path_key(value)
    return any(key == root or key.startswith(f"{root}/") for root in _PROTECTED_ACCEPTANCE_ROOTS)


def _reparse_component(path: Path) -> Path | None:
    """Return the first existing symlink/reparse component, if any.

    ``Path.resolve`` must not be used as the first check: it follows a link
    and can make an unsafe path appear to be inside the workspace.  Missing
    final components are allowed for deletion receipts, while every existing
    parent is checked without following it.
    """
    try:
        absolute = Path(os.path.abspath(str(path)))
    except (OSError, ValueError):
        return path
    parts = absolute.parts
    if not parts:
        return None
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            # A missing component means all later components are absent too;
            # this is the safe deletion/tombstone case.
            break
        except OSError:
            return current
        if current.is_symlink() or stat.S_ISLNK(info.st_mode):
            return current
        reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        if int(getattr(info, "st_file_attributes", 0) or 0) & reparse_flag:
            return current
    return None


def _assert_safe_path(root: Path, relative: Path, *, explicit: bool, portable: str) -> bool:
    """Check all existing components before resolving, hashing, or opening."""
    root_absolute = Path(os.path.abspath(str(root)))
    candidate = root_absolute.joinpath(*relative.parts)
    unsafe = _reparse_component(root_absolute) or _reparse_component(candidate)
    if unsafe is None:
        return True
    if explicit:
        raise ToolFailure(
            "ACCEPTANCE_FILE_NOT_REGULAR",
            "An acceptance path contains a symlink, junction, or reparse point.",
            category="validation",
            details={"path": portable, "unsafe_component": _portable_path(str(unsafe))},
        )
    return False


def _passed_proof_keys(proofs: Any) -> list[tuple[str, str]]:
    passed: set[tuple[str, str]] = set()
    for item in proofs if isinstance(proofs, list) else []:
        if not isinstance(item, dict) or str(item.get("status") or "").strip().lower() != "passed":
            continue
        proof_id = str(item.get("proof_id") or "").strip()
        input_fingerprint = str(item.get("input_fingerprint") or "").strip()
        if proof_id and input_fingerprint:
            passed.add((proof_id, input_fingerprint))
    return sorted(passed)


def has_passed_proof(proofs: Any) -> bool:
    """Return whether the exact proof set contains one usable passed proof."""
    return bool(_passed_proof_keys(proofs))


def passed_proof_fingerprint(proofs: Any) -> str:
    """Compute the shared deterministic fingerprint of exact passed proofs.

    Failed, skipped, and other non-passed observations are deliberately
    excluded.  The canonical no-mutation proof identity is the empty string;
    callers that require a real passed proof must use :func:`has_passed_proof`.
    """
    material = "|".join(
        f"{proof_id}:{input_fingerprint}"
        for proof_id, input_fingerprint in _passed_proof_keys(proofs)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest() if material else ""


def _portable_path(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return Path(path).as_posix() if path else ""


def _is_hex_digest(value: Any, length: int = 64) -> bool:
    text = str(value or "").strip().lower()
    return len(text) == length and all(char in _HEX_DIGITS for char in text)


def _is_canonical_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(char in _HEX_DIGITS for char in value)


def _accepted_file_receipts(
    workspace: Path,
    modified_files: Any,
    *,
    acceptance_files: Any = None,
    run_id: str = "",
    wave_id: str = "",
    receipt_kinds: dict[str, str] | None = None,
    receipt_source: str = "",
) -> dict[str, Any]:
    """Build content-free, bounded file receipts for one final acceptance."""
    # Keep the non-resolved spelling for the reparse check.  Resolving first
    # would follow a junction/symlink and defeat the containment guard.
    root = Path(os.path.abspath(str(workspace)))
    root_real = root.resolve(strict=False)
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
        value = _portable_path(raw)
        if explicit_attestation and (not isinstance(item, dict) or not value):
            raise ToolFailure(
                "ACCEPTANCE_FILE_INVALID",
                "Each acceptance file attestation must contain a non-empty workspace-relative path.",
                category="validation",
            )
        if not value:
            continue
        if _is_protected_acceptance_path(value):
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_INVALID",
                    "Protected repository control paths cannot be used as explicit source-file attestations.",
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
        if not _assert_safe_path(root, relative, explicit=explicit_attestation, portable=value):
            incomplete_reasons.add("unsafe_path")
            continue
        unresolved_target = root / relative
        if unresolved_target.is_symlink():
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_NOT_REGULAR",
                    "An explicitly attested acceptance path is not a regular file.",
                    category="validation",
                    details={"path": value},
                )
            incomplete_reasons.add("symlink")
            continue
        target = unresolved_target.resolve(strict=False)
        if not is_relative_to(target, root_real):
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
            receipt_kind = (
                "explicit_existing_file"
                if explicit_attestation
                else str((receipt_kinds or {}).get(portable) or "task_modified_file")
            )
            if receipt_kind not in ACCEPTED_FILE_RECEIPT_KINDS:
                incomplete_reasons.add("receipt_kind_invalid")
                continue
            normalized.append({
                "path": portable,
                "expected_sha256": expected_sha256,
                "receipt_kind": receipt_kind,
            })
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
        receipt_kind = normalized_item["receipt_kind"]
        unresolved_target = root / Path(portable)
        if not _assert_safe_path(root, Path(portable), explicit=explicit_attestation, portable=portable):
            incomplete_reasons.add("unsafe_path")
            continue
        if unresolved_target.is_symlink():
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_NOT_REGULAR",
                    "An explicitly attested acceptance path is not a regular file.",
                    category="validation",
                    details={"path": portable},
                )
            incomplete_reasons.add("symlink")
            continue
        target = unresolved_target.resolve(strict=False)
        if not is_relative_to(target, root_real):
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_INVALID",
                    "Acceptance file paths must stay within the governed workspace.",
                    category="validation",
                    details={"path": portable},
                )
            incomplete_reasons.add("outside_workspace")
            continue
        if not target.exists():
            if explicit_attestation:
                raise ToolFailure(
                    "ACCEPTANCE_FILE_NOT_FOUND",
                    "An explicitly attested acceptance file does not exist.",
                    category="validation",
                    details={"path": portable},
                )
            receipts.append({
                "path": portable,
                "state": "missing",
                "sha256": None,
                "size_bytes": 0,
                "receipt_kind": receipt_kind,
                "run_id": str(run_id),
                "wave_id": str(wave_id),
                "restart_safe": True,
                "content_addressed": False,
            })
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
        # Recheck immediately before stat/open to reduce the TOCTOU window
        # between path validation and content addressing.
        if not _assert_safe_path(root, Path(portable), explicit=explicit_attestation, portable=portable):
            incomplete_reasons.add("unsafe_path")
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
        receipt = {
            "path": portable,
            "state": "file",
            "sha256": observed_sha256,
            "size_bytes": size,
            "receipt_kind": receipt_kind,
            "run_id": str(run_id),
            "wave_id": str(wave_id),
            "restart_safe": True,
            "content_addressed": True,
        }
        if explicit_attestation:
            receipt["expected_sha256"] = expected_sha256
        receipts.append(receipt)
    return {
        "schema_version": ACCEPTED_FILE_RECEIPT_SCHEMA_VERSION,
        "source": receipt_source or ("explicit_acceptance_attestations" if explicit_attestation else "task_modified_files"),
        "complete": not incomplete_reasons and len(receipts) == len(normalized),
        "count": len(receipts),
        "total_bytes": total_bytes,
        "run_id": str(run_id),
        "wave_id": str(wave_id),
        "files": receipts,
        "incomplete_reasons": sorted(incomplete_reasons),
    }


def _durable_wave_acceptance_paths(
    ledger: Any,
    run_id: str,
    wave_id: str,
    *,
    workspace: Path | None = None,
) -> tuple[bool, list[str]]:
    """Recover exact touched paths from the canonical run/wave event stream."""
    events = [
        item for item in ledger.list_events(run_id)
        if str(item.get("wave_id") or "") == str(wave_id or "")
    ]
    observed_file_ids: set[str] = set()
    mutation_observed = False
    for event in events:
        if str(event.get("event_type") or "") != "patch_surface_observed":
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        file_count = payload.get("file_count")
        file_ids_value = payload.get("file_ids")
        file_ids = [
            str(item).strip().lower()
            for item in file_ids_value
            if isinstance(item, str) and str(item).strip()
        ] if isinstance(file_ids_value, list) else []
        if (
            isinstance(file_count, bool)
            or not isinstance(file_count, int)
            or file_count < 0
            or payload.get("complete") is not True
            or len(file_ids) != file_count
            or len(set(file_ids)) != file_count
            or any(not _is_hex_digest(item) for item in file_ids)
        ):
            raise ToolFailure(
                "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
                "Durable mutation evidence is incomplete; exact accepted files cannot be reconstructed.",
                category="runtime",
                retryable=False,
                details={"run_id": run_id, "wave_id": wave_id, "observed_file_count": file_count},
            )
        if file_count > 0:
            mutation_observed = True
            observed_file_ids.update(file_ids)
    if not mutation_observed:
        return False, []
    if not observed_file_ids:
        raise ToolFailure(
            "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
            "Durable mutation evidence did not contain reconstructable file identities.",
            category="runtime",
            retryable=False,
            details={"run_id": run_id, "wave_id": wave_id},
        )

    lease_payloads = [
        event.get("payload") if isinstance(event.get("payload"), dict) else {}
        for event in events
        if str(event.get("event_type") or "") == "write_lease_acquired"
    ]
    if not lease_payloads:
        raise ToolFailure(
            "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
            "Durable mutation evidence has no matching write-lease scope.",
            category="runtime",
            retryable=False,
            details={"run_id": run_id, "wave_id": wave_id},
        )

    allowed_paths: set[str] = set()
    existing_dirty_paths: set[str] = set()
    protected_paths: set[str] = {".coding-tools", ".git"}
    for payload in lease_payloads:
        allowed_paths.update(
            _portable_path(item) for item in payload.get("allowed_paths", [])
            if _portable_path(item)
        )
        existing_dirty_paths.update(
            _portable_path_key(item) for item in payload.get("existing_dirty_source_paths", [])
            if _portable_path(item)
        )
        protected_paths.update(
            _portable_path_key(item).rstrip("/") for item in payload.get("protected_paths", [])
            if _portable_path(item)
        )

    matched: dict[str, str] = {}
    for portable in sorted(allowed_paths):
        relative = Path(portable)
        portable_key = _portable_path_key(portable)
        if relative.is_absolute() or ".." in relative.parts or portable_key in existing_dirty_paths:
            continue
        if any(portable_key == protected or portable_key.startswith(f"{protected}/") for protected in protected_paths):
            continue
        scope_root = workspace or getattr(ledger, "workspace", None)
        if scope_root is not None and not _assert_safe_path(
            Path(scope_root),
            relative,
            explicit=False,
            portable=portable,
        ):
            raise ToolFailure(
                "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
                "Durable mutation evidence references an unsafe symlink, junction, or reparse path.",
                category="runtime",
                retryable=False,
                details={"run_id": run_id, "wave_id": wave_id, "path": portable},
            )
        if scope_root is None:
            raise ToolFailure(
                "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
                "Durable mutation evidence requires a workspace root before path identity matching.",
                category="runtime",
                retryable=False,
                details={"run_id": run_id, "wave_id": wave_id},
            )
        file_id = hashlib.sha256(portable.encode("utf-8")).hexdigest()
        if file_id in observed_file_ids:
            matched[file_id] = portable
    if observed_file_ids.difference(matched):
        raise ToolFailure(
            "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
            "Durable mutation evidence exceeds the safe write-lease paths available for final acceptance.",
            category="runtime",
            retryable=False,
            details={
                "run_id": run_id,
                "wave_id": wave_id,
                "observed_file_count": len(observed_file_ids),
                "matched_file_count": len(matched),
            },
        )
    return True, sorted(matched.values())


def _accepted_checkpoint_file_receipts(
    workspace: Path,
    ledger: Any,
    modified_files: Any,
    *,
    acceptance_files: Any = None,
    run_id: str,
    wave_id: str,
) -> dict[str, Any]:
    """Build the one checkpointable receipt contract for final acceptance."""
    if not str(run_id or "").strip() or not str(wave_id or "").strip():
        raise ToolFailure(
            "ACCEPTANCE_CONTEXT_REQUIRED",
            "Final acceptance receipts require an exact run_id and wave_id.",
            category="runtime",
        )
    durable_mutation, durable_paths = _durable_wave_acceptance_paths(
        ledger,
        run_id,
        wave_id,
        workspace=workspace,
    )
    explicit = acceptance_files is not None
    task_items = list(modified_files) if isinstance(modified_files, list) else []
    source_items: list[Any]
    receipt_kinds: dict[str, str] = {}
    if explicit:
        source_items = []
    else:
        source_items = list(task_items)
        for item in task_items:
            raw = item.get("path") if isinstance(item, dict) else item
            portable = _portable_path(raw)
            if portable:
                receipt_kinds[portable] = "task_modified_file"
        present = set(receipt_kinds)
        for portable in durable_paths:
            receipt_kinds[portable] = "durable_wave_patch_surface"
            if portable not in present:
                source_items.append(portable)

    source = (
        "explicit_acceptance_attestations"
        if explicit
        else "durable_wave_patch_surface"
        if durable_mutation
        else "task_modified_files"
    )
    accepted = _accepted_file_receipts(
        workspace,
        source_items,
        acceptance_files=acceptance_files if explicit else None,
        run_id=run_id,
        wave_id=wave_id,
        receipt_kinds=receipt_kinds,
        receipt_source=source,
    )
    receipt_paths = {
        str(item.get("path") or "")
        for item in accepted.get("files", [])
        if isinstance(item, dict) and str(item.get("path") or "")
    }
    missing_durable_paths = sorted(set(durable_paths).difference(receipt_paths))
    receipts_required = explicit or durable_mutation or bool(task_items)
    if (
        accepted.get("complete") is not True
        or (receipts_required and int(accepted.get("count") or 0) <= 0)
        or missing_durable_paths
    ):
        raise ToolFailure(
            "ACCEPTANCE_FILE_ATTESTATION_REQUIRED",
            "Source mutation was observed but complete accepted file receipts could not be checkpointed.",
            category="runtime",
            retryable=False,
            details={
                "run_id": run_id,
                "wave_id": wave_id,
                "receipt_count": int(accepted.get("count") or 0),
                "incomplete_reasons": list(accepted.get("incomplete_reasons") or []),
                "missing_durable_path_count": len(missing_durable_paths),
            },
        )
    return accepted


def _checkpoint_failure(code: str, reason: str, **details: Any) -> dict[str, Any]:
    return {"ok": False, "code": code, "reason": reason, "details": details}


def _verify_lifecycle_snapshot(lifecycle: Any) -> bool:
    snapshot = lifecycle.get("snapshot") if isinstance(lifecycle, dict) else None
    foreign_key_rows = snapshot.get("foreign_key_check_rows") if isinstance(snapshot, dict) else None
    return bool(
        isinstance(snapshot, dict)
        and snapshot.get("backup_api_copy") is True
        and snapshot.get("immutable") is True
        and snapshot.get("query_only") is True
        and snapshot.get("integrity_check") == ["ok"]
        and not isinstance(foreign_key_rows, bool)
        and isinstance(foreign_key_rows, int)
        and foreign_key_rows == 0
        and _is_hex_digest(snapshot.get("sha256"))
        and _is_hex_digest(snapshot.get("logical_sha256"))
    )


def _verify_activation_source_checkpoint(
    workspace: Path,
    ledger: Any,
    source_checkpoint: Any,
    *,
    current_git_head: str,
    lifecycle: Any,
) -> dict[str, Any]:
    """Verify one exact accepted checkpoint before an internal activation fence."""
    required = {"checkpoint_id", "run_id", "wave_id", "proof_fingerprint", "git_head"}
    if not isinstance(source_checkpoint, dict) or set(source_checkpoint) != required:
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "source_checkpoint_contract_invalid")
    checkpoint_id = source_checkpoint.get("checkpoint_id")
    run_id = source_checkpoint.get("run_id")
    wave_id = source_checkpoint.get("wave_id")
    proof_fingerprint = source_checkpoint.get("proof_fingerprint")
    git_head = source_checkpoint.get("git_head")
    if (
        not isinstance(checkpoint_id, str)
        or not isinstance(run_id, str)
        or not isinstance(wave_id, str)
        or _SOURCE_CHECKPOINT_ID.fullmatch(checkpoint_id) is None
        or _SOURCE_CHECKPOINT_ID.fullmatch(run_id) is None
        or _SOURCE_CHECKPOINT_ID.fullmatch(wave_id) is None
        or not (proof_fingerprint == "" or _is_canonical_hex(proof_fingerprint, 64))
        or not isinstance(git_head, str)
        or len(git_head) not in {40, 64}
        or any(char not in _HEX_DIGITS for char in git_head)
    ):
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "source_checkpoint_identity_invalid")
    if not _verify_lifecycle_snapshot(lifecycle):
        return _checkpoint_failure("ORCHESTRATION_STATE_UNCERTAIN", "lifecycle_snapshot_integrity_failed")
    try:
        run = ledger.get_run(run_id)
        waves = [item for item in ledger.list_waves(run_id) if str(item.get("wave_id") or "") == wave_id]
        checkpoints = [
            item for item in ledger.list_checkpoints(run_id, wave_id=wave_id)
            if str(item.get("checkpoint_id") or "") == checkpoint_id
        ]
        proofs = ledger.list_proofs(run_id, wave_id=wave_id)
        integrity = ledger.verify_chain(run_id)
    except (sqlite3.Error, OSError, ValueError) as exc:
        return _checkpoint_failure(
            "ORCHESTRATION_STATE_UNCERTAIN",
            "source_checkpoint_probe_failed",
            error_type=type(exc).__name__,
        )
    if integrity.get("ok") is not True:
        return _checkpoint_failure("ORCHESTRATION_STATE_UNCERTAIN", "ledger_integrity_failed", run_id=run_id)
    if not isinstance(run, dict) or str(run.get("status") or "") != "accepted":
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "accepted_run_missing", run_id=run_id)
    if len(waves) != 1 or str(waves[0].get("status") or "") != "accepted":
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "accepted_wave_missing", run_id=run_id, wave_id=wave_id)
    if len(checkpoints) != 1:
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "exact_checkpoint_missing", checkpoint_id=checkpoint_id)
    checkpoint = checkpoints[0]
    if (
        str(checkpoint.get("status") or "") != "accepted"
        or checkpoint.get("proof_fingerprint") != proof_fingerprint
        or checkpoint.get("git_head") != git_head
    ):
        return _checkpoint_failure("CHECKPOINT_NOT_ACTIVATABLE", "checkpoint_identity_mismatch", checkpoint_id=checkpoint_id)
    recomputed_proof_fingerprint = passed_proof_fingerprint(proofs)
    if recomputed_proof_fingerprint != proof_fingerprint:
        return _checkpoint_failure(
            "CHECKPOINT_NOT_ACTIVATABLE",
            "proof_fingerprint_mismatch",
            checkpoint_id=checkpoint_id,
            expected=proof_fingerprint,
            observed=recomputed_proof_fingerprint,
        )
    if current_git_head != git_head:
        return _checkpoint_failure("SOURCE_DRIFT", "git_head_changed", expected_git_head=git_head)

    metadata = checkpoint.get("metadata") if isinstance(checkpoint.get("metadata"), dict) else {}
    accepted = metadata.get("accepted_files") if isinstance(metadata.get("accepted_files"), dict) else {}
    files = accepted.get("files") if isinstance(accepted.get("files"), list) else []
    receipt_source = accepted.get("source")
    count = accepted.get("count")
    total_bytes = accepted.get("total_bytes")
    if (
        accepted.get("schema_version") != ACCEPTED_FILE_RECEIPT_SCHEMA_VERSION
        or accepted.get("complete") is not True
        or accepted.get("run_id") != run_id
        or accepted.get("wave_id") != wave_id
        or receipt_source not in {
            "explicit_acceptance_attestations",
            "task_modified_files",
            "durable_wave_patch_surface",
        }
        or accepted.get("incomplete_reasons") != []
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count < 0
        or count > MAX_ACCEPTED_FILE_RECEIPTS
        or count != len(files)
        or isinstance(total_bytes, bool)
        or not isinstance(total_bytes, int)
        or total_bytes < 0
        or total_bytes > MAX_ACCEPTED_RECEIPT_TOTAL_BYTES
    ):
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_contract_invalid", checkpoint_id=checkpoint_id)

    seen: set[str] = set()
    observed_total = 0
    receipt_kinds: dict[str, str] = {}
    for item in files:
        if not isinstance(item, dict):
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_receipt_invalid")
        portable = _portable_path(item.get("path"))
        relative = Path(portable)
        state = str(item.get("state") or "")
        sha256 = item.get("sha256")
        size_bytes = item.get("size_bytes")
        receipt_kind = str(item.get("receipt_kind") or "")
        if (
            not portable
            or portable != str(item.get("path") or "")
            or relative.is_absolute()
            or ".." in relative.parts
            or _is_protected_acceptance_path(portable)
            or portable in seen
            or receipt_kind not in ACCEPTED_FILE_RECEIPT_KINDS
            or item.get("run_id") != run_id
            or item.get("wave_id") != wave_id
            or item.get("restart_safe") is not True
            or state not in {"file", "missing"}
            or isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or size_bytes < 0
            or size_bytes > MAX_ACCEPTED_RECEIPT_FILE_BYTES
        ):
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_provenance_invalid", path=portable)
        if state == "file":
            if not _is_hex_digest(sha256) or item.get("content_addressed") is not True:
                return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_content_address_invalid", path=portable)
        elif sha256 is not None or size_bytes != 0 or item.get("content_addressed") is not False:
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_deletion_receipt_invalid", path=portable)
        if receipt_kind == "explicit_existing_file" and (
            not _is_hex_digest(item.get("expected_sha256"))
            or str(item.get("expected_sha256") or "").lower() != str(sha256 or "").lower()
        ):
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "explicit_receipt_attestation_invalid", path=portable)
        if (
            (receipt_source == "explicit_acceptance_attestations" and receipt_kind != "explicit_existing_file")
            or (receipt_source == "task_modified_files" and receipt_kind != "task_modified_file")
            or (
                receipt_source == "durable_wave_patch_surface"
                and receipt_kind not in {"durable_wave_patch_surface", "task_modified_file"}
            )
        ):
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_source_provenance_invalid", path=portable)
        seen.add(portable)
        receipt_kinds[portable] = receipt_kind
        observed_total += size_bytes
    if observed_total != total_bytes:
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_total_bytes_mismatch")

    try:
        durable_mutation, durable_paths = _durable_wave_acceptance_paths(
            ledger,
            run_id,
            wave_id,
            workspace=workspace,
        )
        current = _accepted_file_receipts(
            workspace,
            sorted(seen),
            run_id=run_id,
            wave_id=wave_id,
            receipt_kinds=receipt_kinds,
            receipt_source=str(receipt_source or ""),
        )
    except ToolFailure as exc:
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "accepted_file_revalidation_failed", error_code=exc.code)
    if current.get("complete") is not True or int(current.get("count") or 0) != count:
        return _checkpoint_failure("SOURCE_DRIFT", "accepted_source_unavailable")
    current_by_path = {
        str(item.get("path") or ""): item
        for item in current.get("files", [])
        if isinstance(item, dict)
    }
    for item in files:
        current_item = current_by_path.get(str(item.get("path") or ""))
        if not current_item or any(current_item.get(key) != item.get(key) for key in ("state", "sha256", "size_bytes")):
            return _checkpoint_failure("SOURCE_DRIFT", "accepted_source_receipt_changed", path=item.get("path"))
    mutation_bearing_receipts = durable_mutation or bool(files)
    if mutation_bearing_receipts and not has_passed_proof(proofs):
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "passed_proof_missing")
    if durable_mutation and (not files or set(durable_paths).difference(seen)):
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "durable_patch_surface_not_covered")
    if durable_mutation:
        expected_kind = "explicit_existing_file" if receipt_source == "explicit_acceptance_attestations" else "durable_wave_patch_surface"
        if receipt_source not in {"explicit_acceptance_attestations", "durable_wave_patch_surface"} or any(
            receipt_kinds.get(path) != expected_kind for path in durable_paths
        ):
            return _checkpoint_failure("RECEIPT_INCOMPLETE", "durable_patch_surface_provenance_invalid")
    elif receipt_source == "durable_wave_patch_surface":
        return _checkpoint_failure("RECEIPT_INCOMPLETE", "durable_patch_surface_evidence_missing")
    return {
        "ok": True,
        "code": "ACTIVATABLE",
        "checkpoint_id": checkpoint_id,
        "run_id": run_id,
        "wave_id": wave_id,
        "proof_fingerprint": proof_fingerprint,
        "git_head": git_head,
        "accepted_file_count": count,
    }
