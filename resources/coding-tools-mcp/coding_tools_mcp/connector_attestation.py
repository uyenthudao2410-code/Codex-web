from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from typing import Any


CONNECTOR_ATTESTATION_HEADER = "X-Coding-Tools-Connector-Attestation"
CONNECTOR_ATTESTATION_ENV = "CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET"
CONNECTOR_ATTESTATION_VERSION = "v1"
CONNECTOR_ATTESTATION_MAX_AGE_MS = 15 * 60 * 1000
CONNECTOR_ATTESTATION_MAX_FUTURE_SKEW_MS = 5_000
_FIELD_RE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_NONCE_RE = re.compile(r"^[0-9a-f]{16,128}$")


def _text(value: object) -> str:
    return str(value or "").strip()


def _canonical(
    *,
    client_id: str,
    client_type: str,
    activation_epoch_id: str,
    process_instance_id: str,
    server_instance_id: str,
    contract_sha256: str,
    issued_at_unix_ms: int,
    nonce: str,
) -> str:
    return "|".join(
        (
            CONNECTOR_ATTESTATION_VERSION,
            client_id,
            client_type,
            activation_epoch_id,
            process_instance_id,
            server_instance_id,
            contract_sha256,
            str(issued_at_unix_ms),
            nonce,
        )
    )


def build_connector_attestation(
    secret: object,
    *,
    client_id: object,
    client_type: object,
    activation_epoch_id: object,
    process_instance_id: object,
    server_instance_id: object,
    contract_sha256: object,
    issued_at_unix_ms: int | None = None,
    nonce: str | None = None,
) -> str:
    """Build the static transport proof injected by the managed tunnel.

    The secret is never included in the wire value.  The value binds the
    caller label and the exact runtime identities so a receipt cannot be
    replayed after a process, server, epoch, or contract replacement.
    """

    key = _text(secret).encode("utf-8")
    if not key:
        raise ValueError("connector attestation secret is required")
    values = {
        "client_id": _text(client_id),
        "client_type": _text(client_type).lower().replace("-", "_"),
        "activation_epoch_id": _text(activation_epoch_id),
        "process_instance_id": _text(process_instance_id),
        "server_instance_id": _text(server_instance_id),
        "contract_sha256": _text(contract_sha256).lower(),
        "issued_at_unix_ms": int(issued_at_unix_ms if issued_at_unix_ms is not None else time.time() * 1000),
        "nonce": _text(nonce) or secrets.token_hex(16),
    }
    if not _FIELD_RE.fullmatch(values["client_id"]):
        raise ValueError("invalid connector attestation client id")
    if not _FIELD_RE.fullmatch(values["client_type"]):
        raise ValueError("invalid connector attestation client type")
    for field in ("activation_epoch_id", "process_instance_id", "server_instance_id"):
        if values[field] and not _FIELD_RE.fullmatch(values[field]):
            raise ValueError(f"invalid connector attestation {field}")
    if not _HEX64_RE.fullmatch(values["contract_sha256"]):
        raise ValueError("invalid connector attestation contract sha256")
    if not _NONCE_RE.fullmatch(values["nonce"]):
        raise ValueError("invalid connector attestation nonce")
    canonical = _canonical(**values)
    signature = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{canonical}|{signature}"


def verify_connector_attestation(
    value: object,
    secret: object,
    *,
    client_id: object,
    client_type: object,
    activation_epoch_id: object,
    process_instance_id: object,
    server_instance_id: object,
    contract_sha256: object,
    now_unix_ms: int | None = None,
) -> tuple[bool, str]:
    """Verify an attestation without returning secret-bearing diagnostics."""

    key = _text(secret).encode("utf-8")
    raw = _text(value)
    if not key:
        return False, "secret_unavailable"
    parts = raw.split("|")
    if len(parts) != 10 or parts[0] != CONNECTOR_ATTESTATION_VERSION:
        return False, "format_invalid"
    _, supplied_client_id, supplied_client_type, supplied_epoch, supplied_process, supplied_server, supplied_sha, supplied_issued, supplied_nonce, supplied_signature = parts
    if not _FIELD_RE.fullmatch(supplied_client_id) or not _FIELD_RE.fullmatch(supplied_client_type):
        return False, "identity_invalid"
    for item in (supplied_epoch, supplied_process, supplied_server):
        if item and not _FIELD_RE.fullmatch(item):
            return False, "identity_invalid"
    if not _HEX64_RE.fullmatch(supplied_sha) or not _NONCE_RE.fullmatch(supplied_nonce):
        return False, "binding_invalid"
    if not re.fullmatch(r"[0-9a-f]{64}", supplied_signature):
        return False, "signature_invalid"
    try:
        issued_at = int(supplied_issued)
    except (TypeError, ValueError):
        return False, "timestamp_invalid"
    now = int(now_unix_ms if now_unix_ms is not None else time.time() * 1000)
    if issued_at <= 0 or issued_at > now + CONNECTOR_ATTESTATION_MAX_FUTURE_SKEW_MS:
        return False, "timestamp_invalid"
    if now - issued_at > CONNECTOR_ATTESTATION_MAX_AGE_MS:
        return False, "timestamp_expired"
    expected_values = {
        "client_id": _text(client_id),
        "client_type": _text(client_type).lower().replace("-", "_"),
        "activation_epoch_id": _text(activation_epoch_id),
        "process_instance_id": _text(process_instance_id),
        "server_instance_id": _text(server_instance_id),
        "contract_sha256": _text(contract_sha256).lower(),
        "issued_at_unix_ms": issued_at,
        "nonce": supplied_nonce,
    }
    supplied_values = {
        "client_id": supplied_client_id,
        "client_type": supplied_client_type,
        "activation_epoch_id": supplied_epoch,
        "process_instance_id": supplied_process,
        "server_instance_id": supplied_server,
        "contract_sha256": supplied_sha,
        "issued_at_unix_ms": issued_at,
        "nonce": supplied_nonce,
    }
    if any(expected_values[field] != supplied_values[field] for field in expected_values):
        return False, "binding_mismatch"
    canonical = _canonical(**supplied_values)
    expected_signature = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, supplied_signature):
        return False, "signature_invalid"
    return True, "verified"


def attestation_metadata(identity: dict[str, Any]) -> dict[str, Any]:
    """Return safe, non-secret provenance fields for receipts."""

    return {
        "attestation_verified": identity.get("attestation_verified") is True,
        "attestation_source": _text(identity.get("attestation_source")) or "none",
    }

