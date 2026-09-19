"""Fail-closed, context-scoped root MCP facade.

This module gives one authenticated, time-bounded, context-scoped MCP
principal a way to discover the exact eight tool public surface, inspect that
context's central state, and atomically record exactly one fixed read-only
intent. After the separately admitted node action completes, it can expose one
allowlisted compact receipt projection. It never calls a node, forwards a
client credential, polls, or turns a central record into local authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .node_agent import APPROVED_PATCH_MAX_FILE_BYTES, safe_workspace_summary
from .store import (
    MCP_APPROVED_PATCH_MAX_BYTES,
    MCP_APPROVED_PATCH_OPERATION,
    MCP_APPROVED_PATCH_TOOL_NAME,
    MCP_PATCH_PERMISSION_OPERATION,
    MCP_PATCH_PERMISSION_TOOL_NAME,
    MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
    ControlPlaneError,
    ControlPlaneStore,
    PermissionError,
    ValidationError,
)


MCP_PROTOCOL_VERSION = "2025-11-25"
STATELESS_MCP_PROTOCOL_VERSION = "2026-07-28"
# The initialize handshake only negotiates legacy revisions. The modern
# revision uses per-request metadata and server/discover instead.
# Do not advertise 2025-03-26: its batching and older result contract are not
# implemented here. Unsupported offers negotiate our latest supported revision.
LEGACY_MCP_PROTOCOL_VERSIONS = (MCP_PROTOCOL_VERSION, "2025-06-18")
SUPPORTED_MCP_PROTOCOL_VERSIONS = (STATELESS_MCP_PROTOCOL_VERSION, *LEGACY_MCP_PROTOCOL_VERSIONS)
# Keep the pilot contract byte-stable until a selected rollout changes it. The
# OAuth account-inventory contract is a distinct revision because it has a
# different authority boundary and cannot be accepted by a local read-only
# policy issued for the context-scoped pilot.
FACADE_SCHEMA_VERSION = 6
FACADE_PROFILE = "control-plane-scoped-read-only-relay-v5"
OAUTH_FACADE_SCHEMA_VERSION = 7
OAUTH_FACADE_PROFILE = "control-plane-oauth-account-inventory-v1"
# This is deliberately a distinct contract from OAuth inventory.  Turning on
# the candidate-only bounded-file relay changes authority and must force a
# client to rediscover the exact tool surface rather than silently treating an
# inventory contract as a file-access contract.
OAUTH_FILE_READ_FACADE_SCHEMA_VERSION = 8
OAUTH_FILE_READ_FACADE_PROFILE = "control-plane-oauth-bounded-file-read-v1"
# Permission requests are a separate candidate profile.  They do not make a
# write relay available: they only record an exact owner-reviewed patch scope
# for a future local bridge to revalidate.
OAUTH_PERMISSION_REQUEST_FACADE_SCHEMA_VERSION = 9
OAUTH_PERMISSION_REQUEST_FACADE_PROFILE = "control-plane-oauth-permission-request-v1"
# An approved patch is a distinct public surface from permission review.  A
# client must rediscover it and obtain the dedicated OAuth write scope before
# it can queue any local mutation candidate.
OAUTH_APPROVED_PATCH_FACADE_SCHEMA_VERSION = 10
OAUTH_APPROVED_PATCH_FACADE_PROFILE = "control-plane-oauth-approved-patch-v1"
FILE_READ_MAX_BYTES = 16 * 1024
FILE_READ_MAX_LINES = 200
PUBLIC_TOOL_NAMES = (
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _rpc_error(request_id: str | int | None, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _response_id(request: dict[str, Any]) -> str | int | None:
    value = request.get("id")
    return value if isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool)) else None


def _workspace_context_input_schema(*, oauth_enabled: bool, oauth_file_read_enabled: bool = False) -> dict[str, Any]:
    """Describe the implemented root-facade operation for the auth mode.

    OAuth starts with inventory only. The historical grant mode retains the
    narrow fixed read-only intent; neither schema grants local authority.
    """
    if oauth_enabled and not oauth_file_read_enabled:
        return {
            "type": "object",
            "required": ["operation"],
            "additionalProperties": False,
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["inventory"],
                    "description": "Return only the linked account's authorized node/workspace inventory. This does not create a context, task grant, policy, or action.",
                },
            },
        }
    if oauth_enabled:
        return {
            "type": "object",
            "required": ["operation"],
            "additionalProperties": False,
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["inventory", "read_file", "read_status"],
                    "description": "inventory lists account targets only. read_file queues one bounded local file read for an explicit binding. read_status observes only that OAuth principal's own bounded-file action.",
                },
                "binding_id": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 128,
                    "description": "Required for read_file. Exact opaque target from inventory; display names and last-used targets are never accepted.",
                },
                "path": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 512,
                    "description": "Required for read_file. Exact normalized relative POSIX path admitted by the Windows local policy.",
                },
                "start_line": {"type": "integer", "minimum": 1, "maximum": 1_000_000},
                "max_lines": {"type": "integer", "minimum": 1, "maximum": FILE_READ_MAX_LINES},
                "max_bytes": {"type": "integer", "minimum": 1, "maximum": FILE_READ_MAX_BYTES},
                "idempotency_key": {
                    "type": "string",
                    "minLength": 8,
                    "maxLength": 256,
                    "description": "Required for read_file; it replays only the exact same target, path and bounds.",
                },
                "expected_facade_contract": {
                    "type": "object",
                    "required": ["schema_version", "profile", "sha256"],
                    "additionalProperties": False,
                    "properties": {
                        "schema_version": {"type": "integer", "minimum": 1},
                        "profile": {"type": "string", "minLength": 3, "maxLength": 128},
                        "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                    },
                },
                "action_id": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 128,
                    "description": "Required for read_status. Only actions created by this OAuth principal may be observed.",
                },
            },
        }
    return {
        "type": "object",
        "required": ["context_id"],
        "additionalProperties": False,
        "properties": {
            "context_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Immutable control-plane context selected by the authenticated owner.",
            },
            "action_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Optional existing action under this context; observation only.",
            },
            "operation": {
                "type": "string",
                "enum": ["status", "request_read_only"],
                "description": "Defaults to status. request_read_only queues only the fixed local workspace_context operation.",
            },
            "idempotency_key": {
                "type": "string",
                "minLength": 8,
                "maxLength": 256,
                "description": "Required for request_read_only; replays only an immutable matching central intent.",
            },
            "expires_at_ms": {
                "type": "integer",
                "minimum": 1,
                "description": "Required for request_read_only; must be within the selected context's live expiry.",
            },
            "expected_facade_contract": {
                "type": "object",
                "required": ["schema_version", "profile", "sha256"],
                "additionalProperties": False,
                "properties": {
                    "schema_version": {"type": "integer", "minimum": 1},
                    "profile": {"type": "string", "minLength": 3, "maxLength": 128},
                    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                },
                "description": "Required for request_read_only; pin the exact façade contract from initialize or tools/list.",
            },
        },
    }


def _permission_request_input_schema(*, enabled: bool) -> dict[str, Any]:
    """Describe the one non-executable C4 permission-request operation."""

    if not enabled:
        return _unavailable_tool_input_schema()
    return {
        "type": "object",
        "required": ["operation"],
        "additionalProperties": False,
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["request_patch", "status"],
                "description": "request_patch records one immutable proposed patch scope for owner review. It never queues, writes, runs, or locally approves anything. status observes only the caller's own request.",
            },
            "binding_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Required for request_patch. Exact opaque target from account inventory.",
            },
            "path": {
                "type": "string",
                "minLength": 1,
                "maxLength": 512,
                "description": "Required for request_patch. Exact relative path; never an absolute Windows path.",
            },
            "preimage_sha256": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
                "description": "Required for request_patch. Digest of the file version the future patch must revalidate.",
            },
            "patch_sha256": {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
                "description": "Required for request_patch. Digest of an independently supplied future patch; patch text is never stored here.",
            },
            "validation_profile": {
                "type": "string",
                "enum": [MCP_PATCH_PERMISSION_VALIDATION_PROFILE],
                "description": "Required for request_patch. Fixed local validation profile; a future bridge still decides whether it can run it.",
            },
            "idempotency_key": {
                "type": "string",
                "minLength": 8,
                "maxLength": 256,
                "description": "Required for request_patch. It replays only the exact immutable proposed scope.",
            },
            "expected_facade_contract": {
                "type": "object",
                "required": ["schema_version", "profile", "sha256"],
                "additionalProperties": False,
                "properties": {
                    "schema_version": {"type": "integer", "minimum": 1},
                    "profile": {"type": "string", "minLength": 3, "maxLength": 128},
                    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                },
            },
            "permission_request_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Required for status. Only a request created by the authenticated OAuth principal may be observed.",
            },
        },
    }


def _approved_patch_input_schema(*, enabled: bool) -> dict[str, Any]:
    """Describe the single C4 action shape; this is not a shell interface."""

    if not enabled:
        return _unavailable_tool_input_schema()
    return {
        "type": "object",
        "required": ["operation"],
        "additionalProperties": False,
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["apply_patch", "patch_status"],
                "description": "apply_patch queues exactly one owner-approved Write Exact File envelope for local Windows policy admission. patch_status observes only the caller's own action. Neither operation accepts command text or a filesystem root.",
            },
            "permission_request_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Required for apply_patch. Exact approved owner-review record; it can be consumed by one action only.",
            },
            "patch_envelope": {
                "type": "string",
                "minLength": 1,
                "maxLength": MCP_APPROVED_PATCH_MAX_BYTES,
                "description": "Required for apply_patch. One exact Coding Tools Write Exact File envelope whose UTF-8 SHA-256 matches the reviewed patch digest.",
            },
            "idempotency_key": {
                "type": "string",
                "minLength": 8,
                "maxLength": 256,
                "description": "Required for apply_patch; it can replay only the same approved patch bytes and target.",
            },
            "expected_facade_contract": {
                "type": "object",
                "required": ["schema_version", "profile", "sha256"],
                "additionalProperties": False,
                "properties": {
                    "schema_version": {"type": "integer", "minimum": 1},
                    "profile": {"type": "string", "minLength": 3, "maxLength": 128},
                    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                },
            },
            "action_id": {
                "type": "string",
                "minLength": 3,
                "maxLength": 128,
                "description": "Required for patch_status. Only an action created by the authenticated OAuth principal may be observed.",
            },
        },
    }


def _unavailable_tool_input_schema() -> dict[str, Any]:
    """Do not advertise a context/operation that the facade cannot relay.

    The public smart-v3 names stay stable, but only ``workspace_context`` has
    an implemented central operation today. An empty schema prevents a client
    from inferring that the other seven tools accept a context, queue work, or
    have the Windows tool's local argument schema.
    """

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }


def _tool_description(
    name: str,
    *,
    oauth_enabled: bool,
    oauth_file_read_enabled: bool = False,
    oauth_permission_requests_enabled: bool = False,
    oauth_approved_patch_enabled: bool = False,
) -> str:
    if name == "workspace_context":
        if oauth_enabled and oauth_file_read_enabled:
            return "List the authenticated account's path-free targets, queue one policy-bounded read of an explicitly selected Windows workspace file, or observe its verified receipt. This never grants write, shell, arbitrary path, or local authority."
        if oauth_enabled:
            return "Return the authenticated account's authorized, path-free node/workspace inventory. Context selection and local execution remain unavailable until a separate relay is accepted."
        return "Return central status, queue only the fixed read-only workspace_context action, or show its verified compact completed receipt; this facade never directly accesses a local workspace."
    if name == "request_permissions" and oauth_permission_requests_enabled:
        return (
            "Record or observe one exact owner-reviewed proposed patch scope. Approval does not itself queue an action, "
            "change Windows policy, write a file, launch a process, or grant local authority."
        )
    if name == "agent_workflow" and oauth_approved_patch_enabled:
        return (
            "Queue or observe one exact owner-approved Write Exact File patch for an explicitly selected Windows workspace. "
            "It requires a distinct OAuth write scope and an independent local patch policy; it is not remote shell or arbitrary workspace access."
        )
    return "Declared public tool name. Relay is unavailable until a separate local admission bridge is accepted."


def _tool_contract_entry(
    name: str,
    *,
    oauth_scopes: tuple[str, ...],
    oauth_file_read_enabled: bool = False,
    oauth_permission_requests_enabled: bool = False,
    oauth_patch_write_scope: str | None = None,
    oauth_approved_patch_enabled: bool = False,
) -> dict[str, Any]:
    oauth_enabled = bool(oauth_scopes)
    if name == "workspace_context":
        entry: dict[str, Any] = {
            "name": name,
            "description": _tool_description(
                name,
                oauth_enabled=oauth_enabled,
                oauth_file_read_enabled=oauth_file_read_enabled,
                oauth_permission_requests_enabled=oauth_permission_requests_enabled,
                oauth_approved_patch_enabled=oauth_approved_patch_enabled,
            ),
            "inputSchema": _workspace_context_input_schema(
                oauth_enabled=oauth_enabled,
                oauth_file_read_enabled=oauth_file_read_enabled,
            ),
            "annotations": {"readOnlyHint": True},
            "_meta": {
                "control_plane": {
                    "capability_state": (
                        "implemented" if not oauth_enabled
                        else "bounded_file_read_candidate" if oauth_file_read_enabled
                        else "account_inventory_only"
                    ),
                    "implemented_operations": (
                        ["status", "request_read_only"] if not oauth_enabled
                        else ["inventory", "read_file", "read_status"] if oauth_file_read_enabled
                        else ["inventory"]
                    ),
                    "target_binding": "context_id" if not oauth_enabled else "explicit_binding_id" if oauth_file_read_enabled else "account_owner",
                    "execution": "local_admission_required" if not oauth_enabled or oauth_file_read_enabled else "no_local_execution",
                }
            },
        }
    elif name == "request_permissions" and oauth_permission_requests_enabled:
        entry = {
            "name": name,
            "description": _tool_description(
                name,
                oauth_enabled=oauth_enabled,
                oauth_file_read_enabled=oauth_file_read_enabled,
                oauth_permission_requests_enabled=oauth_permission_requests_enabled,
                oauth_approved_patch_enabled=oauth_approved_patch_enabled,
            ),
            "inputSchema": _permission_request_input_schema(enabled=True),
            "annotations": {"readOnlyHint": False},
            "_meta": {
                "control_plane": {
                    "capability_state": "permission_request_candidate",
                    "implemented_operations": ["request_patch", "status"],
                    "execution": "no_local_execution",
                    "reason": "LOCAL_MUTATION_BRIDGE_REQUIRED",
                }
            },
        }
    elif name == "agent_workflow" and oauth_approved_patch_enabled:
        entry = {
            "name": name,
            "description": _tool_description(
                name,
                oauth_enabled=oauth_enabled,
                oauth_file_read_enabled=oauth_file_read_enabled,
                oauth_permission_requests_enabled=oauth_permission_requests_enabled,
                oauth_approved_patch_enabled=oauth_approved_patch_enabled,
            ),
            "inputSchema": _approved_patch_input_schema(enabled=True),
            "annotations": {"readOnlyHint": False},
            "_meta": {
                "control_plane": {
                    "capability_state": "approved_patch_candidate",
                    "implemented_operations": ["apply_patch", "patch_status"],
                    "execution": "local_patch_policy_required",
                    "reason": "WINDOWS_APPROVED_PATCH_BRIDGE_REQUIRED",
                }
            },
        }
    else:
        entry = {
            "name": name,
            "description": _tool_description(
                name,
                oauth_enabled=oauth_enabled,
                oauth_file_read_enabled=oauth_file_read_enabled,
                oauth_permission_requests_enabled=oauth_permission_requests_enabled,
                oauth_approved_patch_enabled=oauth_approved_patch_enabled,
            ),
            "inputSchema": _unavailable_tool_input_schema(),
            "annotations": {"readOnlyHint": False},
            "_meta": {
                "control_plane": {
                    "capability_state": "unavailable",
                    "implemented_operations": [],
                    "execution": "not_implemented",
                    "reason": "LOCAL_ADMISSION_BRIDGE_REQUIRED",
                }
            },
        }
    if oauth_enabled:
        # The descriptor field is the MCP authorization contract.  Mirror it
        # under ``_meta`` for clients that still read the compatibility copy;
        # both forms remain part of this OAuth-only contract digest.
        required_scopes = oauth_scopes
        if name == "request_permissions" and oauth_permission_requests_enabled:
            required_scopes = (*oauth_scopes, str(oauth_patch_write_scope or ""))
        elif name == "agent_workflow" and oauth_approved_patch_enabled:
            required_scopes = (*oauth_scopes, str(oauth_patch_write_scope or ""))
        security_schemes = [{"type": "oauth2", "scopes": list(required_scopes)}]
        entry["securitySchemes"] = security_schemes
        entry["_meta"]["securitySchemes"] = security_schemes
    return entry


def _central_lifecycle_state(action: dict[str, Any]) -> str:
    """Name only a state directly supported by central durable records.

    This intentionally does not infer a local job state, a workspace result,
    acceptance, or an outcome. ``dispatch_unconfirmed`` is evidence that the
    central store emitted an attempt, not evidence that the node executed it.
    A settled action without a receipt can result from central expiry/revoke or
    cancellation, so it must remain distinguishable from terminal receipts.
    """
    delivery_state = action.get("delivery_state")
    if delivery_state in {"queued", "dispatch_unconfirmed", "accepted", "reconcile_required"}:
        return str(delivery_state)
    if delivery_state != "settled":
        return "unrecognized_central_lifecycle_state"
    receipts = action.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        return "settled_without_receipt"
    latest = receipts[-1]
    receipt_state = latest.get("receipt_state") if isinstance(latest, dict) else None
    if receipt_state in {"completed", "rejected", "failed"}:
        return str(receipt_state)
    return "settled_with_nonterminal_receipt"


def _completed_workspace_relay(action: dict[str, Any], contract: dict[str, int | str]) -> dict[str, Any] | None:
    """Return only the exact, bounded local summary from a completed receipt.

    Receipts are untrusted network input even after they are durable.  The
    node agent performs the first allowlist, but this final client-facing
    boundary validates it again and never returns the raw receipt payload,
    absolute Windows workspace, local handle, or a summary from a stale
    facade contract.
    """

    if action.get("tool_name") != "workspace_context":
        return None
    receipts = action.get("receipts")
    if not isinstance(receipts, list):
        return None
    for receipt in reversed(receipts):
        if not isinstance(receipt, dict) or receipt.get("receipt_state") != "completed":
            continue
        raw_payload = receipt.get("payload_json")
        if not isinstance(raw_payload, str) or len(raw_payload.encode("utf-8")) > 16 * 1024:
            continue
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError):
            continue
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != 1
            or payload.get("operation_kind") != "control_plane_read_only_workspace_context"
            or payload.get("workspace_accessed") is not True
            or payload.get("actor") != {"client_id": "electron-control-plane-bridge", "client_type": "electron"}
            or payload.get("facade_contract") != contract
            or not isinstance(payload.get("workspace_summary_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["workspace_summary_sha256"].lower()) is None
            or not isinstance(payload.get("response_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["response_sha256"].lower()) is None
        ):
            continue
        try:
            summary = safe_workspace_summary(payload.get("workspace_summary"))
        except RuntimeError:
            continue
        summary_sha256 = payload["workspace_summary_sha256"].lower()
        expected_summary_sha256 = hashlib.sha256(
            _canonical_json(summary).encode("utf-8")
        ).hexdigest()
        if summary_sha256 != expected_summary_sha256:
            continue
        return {
            "receipt_id": receipt.get("receipt_id"),
            "received_at_ms": receipt.get("received_at_ms"),
            "workspace_summary": summary,
            "workspace_summary_sha256": summary_sha256,
            "response_sha256": payload["response_sha256"].lower(),
        }
    return None


_SENSITIVE_FILE_CONTENT_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\/=:-]{20,}"),
    re.compile(r"(?im)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9._~+\/=:-]{16,}"),
)
_SENSITIVE_FILE_DIRECTORY_NAMES = frozenset({
    ".git", ".ssh", ".aws", ".gnupg", "secret", "secrets", "credential", "credentials",
})
_SENSITIVE_FILE_BASENAMES = frozenset({
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credential", "credentials",
})


def _safe_bounded_relative_path(value: Any) -> str | None:
    """Return one canonical relative POSIX path or ``None``.

    The central facade validates this again even though Windows performs the
    authority check.  It prevents a malformed receipt from turning an action
    record into an arbitrary local-path disclosure.
    """

    if not isinstance(value, str):
        return None
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return None
    if (
        not encoded
        or len(encoded) > 512
        or "\\" in value
        or ":" in value
        or value.startswith("/")
    ):
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        return None
    lowered = [part.lower() for part in parts]
    basename = lowered[-1]
    if (
        any(part in _SENSITIVE_FILE_DIRECTORY_NAMES or part.startswith(".env") for part in lowered)
        or basename in _SENSITIVE_FILE_BASENAMES
        or basename.endswith((".pem", ".key", ".p12", ".pfx"))
    ):
        return None
    return value


def _contains_sensitive_file_content(content: str) -> bool:
    return any(pattern.search(content) is not None for pattern in _SENSITIVE_FILE_CONTENT_PATTERNS)


def _completed_bounded_file_read_relay(
    action: dict[str, Any],
    contract: dict[str, int | str],
) -> dict[str, Any] | None:
    """Return one bounded, verified local file receipt for its exact action.

    The node has already checked the policy and sensitive-content detector.
    This is defense in depth at the last user-facing boundary: it validates
    the action's immutable argument selection, strips all runtime/local fields
    and refuses to relay a suspicious payload rather than returning partial
    bytes.
    """

    if action.get("tool_name") != "workspace_context":
        return None
    try:
        action_arguments = json.loads(str(action.get("arguments_json") or ""))
    except (TypeError, ValueError):
        return None
    if (
        not isinstance(action_arguments, dict)
        or set(action_arguments) != {"operation", "path", "start_line", "max_lines", "max_bytes"}
        or action_arguments.get("operation") != "read_file"
    ):
        return None
    requested_path = _safe_bounded_relative_path(action_arguments.get("path"))
    if requested_path is None:
        return None
    requested_start_line = action_arguments.get("start_line")
    requested_max_lines = action_arguments.get("max_lines")
    requested_max_bytes = action_arguments.get("max_bytes")
    if (
        not isinstance(requested_start_line, int) or isinstance(requested_start_line, bool) or requested_start_line < 1
        or not isinstance(requested_max_lines, int) or isinstance(requested_max_lines, bool) or not 1 <= requested_max_lines <= FILE_READ_MAX_LINES
        or not isinstance(requested_max_bytes, int) or isinstance(requested_max_bytes, bool) or not 1 <= requested_max_bytes <= FILE_READ_MAX_BYTES
    ):
        return None
    receipts = action.get("receipts")
    if not isinstance(receipts, list):
        return None
    for receipt in reversed(receipts):
        if not isinstance(receipt, dict) or receipt.get("receipt_state") != "completed":
            continue
        raw_payload = receipt.get("payload_json")
        if not isinstance(raw_payload, str) or len(raw_payload.encode("utf-8")) > FILE_READ_MAX_BYTES * 3:
            continue
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError):
            continue
        if (
            not isinstance(payload, dict)
            or set(payload) != {
                "schema_version", "operation_kind", "file_accessed", "local_handle", "policy_sha256",
                "actor", "runtime_identity", "facade_contract", "file", "response_sha256",
            }
            or payload.get("schema_version") != 1
            or payload.get("operation_kind") != "control_plane_bounded_file_read"
            or payload.get("file_accessed") is not True
            or payload.get("actor") != {"client_id": "electron-control-plane-file-read-bridge", "client_type": "electron"}
            or payload.get("facade_contract") != contract
            or not isinstance(payload.get("local_handle"), str)
            or re.fullmatch(r"cp_fr_[a-f0-9]{48}", payload["local_handle"]) is None
            or not isinstance(payload.get("policy_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["policy_sha256"].lower()) is None
            or not isinstance(payload.get("response_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["response_sha256"].lower()) is None
        ):
            continue
        runtime_identity = payload.get("runtime_identity")
        if (
            not isinstance(runtime_identity, dict)
            or set(runtime_identity) != {
                "activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256",
            }
            or any(
                not isinstance(runtime_identity.get(field), str)
                or not 1 <= len(runtime_identity[field]) <= 128
                for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")
            )
            or not isinstance(runtime_identity.get("tool_contract_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", runtime_identity["tool_contract_sha256"].lower()) is None
        ):
            continue
        file_value = payload.get("file")
        if not isinstance(file_value, dict) or set(file_value) != {
            "path", "content", "content_sha256", "encoding", "start_line", "end_line",
            "total_lines", "total_bytes", "bytes_read", "truncated", "next_start_line",
        }:
            continue
        path = _safe_bounded_relative_path(file_value.get("path"))
        content = file_value.get("content")
        content_sha256 = file_value.get("content_sha256")
        if (
            path != requested_path
            or not isinstance(content, str)
            or file_value.get("encoding") != "utf-8"
            or not isinstance(content_sha256, str)
            or re.fullmatch(r"[a-f0-9]{64}", content_sha256.lower()) is None
        ):
            continue
        try:
            content_bytes = content.encode("utf-8")
        except UnicodeEncodeError:
            continue
        if (
            len(content_bytes) > requested_max_bytes
            or hashlib.sha256(content_bytes).hexdigest() != content_sha256.lower()
            or _contains_sensitive_file_content(content)
        ):
            continue
        integer_fields = ("start_line", "end_line", "total_lines", "total_bytes", "bytes_read")
        if any(
            not isinstance(file_value.get(field), int) or isinstance(file_value.get(field), bool) or file_value[field] < 0
            for field in integer_fields
        ):
            continue
        content_line_count = len(content.splitlines())
        requested_end_line = min(
            file_value["total_lines"], requested_start_line + requested_max_lines - 1
        )
        out_of_range = file_value["total_lines"] < requested_start_line
        if (
            file_value["start_line"] != requested_start_line
            or file_value["bytes_read"] != len(content_bytes)
            or file_value["bytes_read"] > requested_max_bytes
            or file_value["total_lines"] < file_value["end_line"]
            or file_value["total_bytes"] < file_value["bytes_read"]
            or not isinstance(file_value.get("truncated"), bool)
            or content_line_count > requested_max_lines
            or (
                not out_of_range
                and (
                    file_value["end_line"] < requested_start_line
                    or file_value["end_line"] > requested_end_line
                    or content_line_count > file_value["end_line"] - requested_start_line + 1
                )
            )
            or (
                out_of_range
                and (
                    file_value["end_line"] != file_value["total_lines"]
                    or content != ""
                    or content_line_count != 0
                )
            )
        ):
            continue
        has_remaining_lines = file_value["end_line"] < file_value["total_lines"]
        if (
            file_value["truncated"] is True
            and has_remaining_lines
            and file_value["next_start_line"] != file_value["end_line"] + 1
        ) or (
            (file_value["truncated"] is not True or not has_remaining_lines)
            and file_value["next_start_line"] is not None
        ):
            continue
        safe_file = {
            "path": path,
            "content": content,
            "content_sha256": content_sha256.lower(),
            "encoding": "utf-8",
            "start_line": file_value["start_line"],
            "end_line": file_value["end_line"],
            "total_lines": file_value["total_lines"],
            "total_bytes": file_value["total_bytes"],
            "bytes_read": file_value["bytes_read"],
            "truncated": file_value["truncated"],
            "next_start_line": file_value["next_start_line"],
        }
        expected_response_sha256 = hashlib.sha256(
            _canonical_json(safe_file).encode("utf-8")
        ).hexdigest()
        if payload["response_sha256"].lower() != expected_response_sha256:
            continue
        return {
            "receipt_id": receipt.get("receipt_id"),
            "received_at_ms": receipt.get("received_at_ms"),
            "file": safe_file,
            "response_sha256": expected_response_sha256,
        }
    return None


def _completed_approved_patch_relay(
    action: dict[str, Any],
    contract: dict[str, int | str],
    expected_file: dict[str, Any],
) -> dict[str, Any] | None:
    """Project one sealed, locally verified exact-patch receipt.

    The raw patch envelope is intentionally absent from the public action
    observation.  ``expected_file`` is retrieved privately from the durable
    intent and contains only the path and digest values required to reject a
    fabricated or stale completed receipt.  This projection never returns the
    patch body, policy digest, local handle, absolute workspace root, or
    runtime identity.
    """

    if action.get("tool_name") != MCP_APPROVED_PATCH_TOOL_NAME:
        return None
    try:
        action_arguments = json.loads(str(action.get("arguments_json") or ""))
    except (TypeError, ValueError):
        return None
    expected_action_fields = {
        "operation", "permission_request_id", "path", "preimage_sha256", "patch_sha256", "validation_profile",
    }
    if (
        not isinstance(action_arguments, dict)
        or set(action_arguments) != expected_action_fields
        or action_arguments.get("operation") != MCP_APPROVED_PATCH_OPERATION
        or action_arguments.get("validation_profile") != MCP_PATCH_PERMISSION_VALIDATION_PROFILE
    ):
        return None
    expected_path = _safe_bounded_relative_path(expected_file.get("path"))
    expected_preimage_sha256 = expected_file.get("preimage_sha256")
    expected_postimage_sha256 = expected_file.get("postimage_sha256")
    expected_patch_sha256 = expected_file.get("patch_sha256")
    if (
        expected_path is None
        or not all(
            isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value.lower()) is not None
            for value in (expected_preimage_sha256, expected_postimage_sha256, expected_patch_sha256)
        )
        or expected_file.get("facade_contract") != contract
        or action_arguments.get("path") != expected_path
        or action_arguments.get("preimage_sha256") != expected_preimage_sha256
        or action_arguments.get("patch_sha256") != expected_patch_sha256
    ):
        return None
    receipts = action.get("receipts")
    if not isinstance(receipts, list):
        return None
    for receipt in reversed(receipts):
        if not isinstance(receipt, dict) or receipt.get("receipt_state") != "completed":
            continue
        raw_payload = receipt.get("payload_json")
        if not isinstance(raw_payload, str) or len(raw_payload.encode("utf-8")) > 16 * 1024:
            continue
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError):
            continue
        if (
            not isinstance(payload, dict)
            or set(payload) != {
                "schema_version", "operation_kind", "patch_applied", "local_handle", "policy_sha256",
                "local_semantic_acceptance", "actor", "runtime_identity", "facade_contract", "file", "response_sha256",
            }
            or payload.get("schema_version") != 1
            or payload.get("operation_kind") != "control_plane_approved_patch"
            or payload.get("patch_applied") is not True
            # A completed node receipt proves the exact postimage, but never
            # claims that the local RUN/WAVE has been semantically accepted.
            or payload.get("local_semantic_acceptance") != "pending"
            or not isinstance(payload.get("local_handle"), str)
            or re.fullmatch(r"cp_ap_[a-f0-9]{48}", payload["local_handle"]) is None
            or not isinstance(payload.get("policy_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["policy_sha256"].lower()) is None
            or payload.get("actor") != {
                "client_id": "electron-control-plane-approved-patch-bridge",
                "client_type": "electron",
            }
            or payload.get("facade_contract") != contract
            or not isinstance(payload.get("response_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", payload["response_sha256"].lower()) is None
        ):
            continue
        runtime_identity = payload.get("runtime_identity")
        if (
            not isinstance(runtime_identity, dict)
            or set(runtime_identity) != {
                "activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256",
            }
            or any(
                not isinstance(runtime_identity.get(field), str)
                or not 1 <= len(runtime_identity[field]) <= 128
                for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")
            )
            or not isinstance(runtime_identity.get("tool_contract_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", runtime_identity["tool_contract_sha256"].lower()) is None
        ):
            continue
        file_value = payload.get("file")
        if not isinstance(file_value, dict) or set(file_value) != {
            "path", "preimage_sha256", "postimage_sha256", "bytes_written",
        }:
            continue
        path = _safe_bounded_relative_path(file_value.get("path"))
        preimage_sha256 = file_value.get("preimage_sha256")
        postimage_sha256 = file_value.get("postimage_sha256")
        bytes_written = file_value.get("bytes_written")
        if (
            path != expected_path
            or not isinstance(preimage_sha256, str)
            or preimage_sha256.lower() != expected_preimage_sha256
            or not isinstance(postimage_sha256, str)
            or postimage_sha256.lower() != expected_postimage_sha256
            or not isinstance(bytes_written, int)
            or isinstance(bytes_written, bool)
            or not 0 <= bytes_written <= APPROVED_PATCH_MAX_FILE_BYTES
        ):
            continue
        safe_file = {
            "path": path,
            "preimage_sha256": preimage_sha256.lower(),
            "postimage_sha256": postimage_sha256.lower(),
            "bytes_written": bytes_written,
        }
        expected_response_sha256 = hashlib.sha256(
            _canonical_json(safe_file).encode("utf-8")
        ).hexdigest()
        if payload["response_sha256"].lower() != expected_response_sha256:
            continue
        return {
            "receipt_id": receipt.get("receipt_id"),
            "received_at_ms": receipt.get("received_at_ms"),
            "local_semantic_acceptance": "pending",
            "file": safe_file,
            "response_sha256": expected_response_sha256,
        }
    return None


def tool_contract(
    *,
    oauth_scopes: tuple[str, ...] = (),
    oauth_file_read_enabled: bool = False,
    oauth_permission_requests_enabled: bool = False,
    oauth_patch_write_scope: str | None = None,
    oauth_approved_patch_enabled: bool = False,
) -> dict[str, Any]:
    if any(not isinstance(scope, str) or not scope for scope in oauth_scopes):
        raise ValueError("OAuth tool scopes are invalid.")
    oauth_enabled = bool(oauth_scopes)
    if oauth_file_read_enabled and not oauth_enabled:
        raise ValueError("OAuth bounded file reads require OAuth tool scopes.")
    if oauth_permission_requests_enabled and (not oauth_enabled or not oauth_file_read_enabled):
        raise ValueError("OAuth permission requests require the OAuth bounded-file-read candidate contract.")
    if oauth_permission_requests_enabled:
        if (
            not isinstance(oauth_patch_write_scope, str)
            or not re.fullmatch(r"[A-Za-z0-9._:-]{3,128}", oauth_patch_write_scope)
            or oauth_patch_write_scope in oauth_scopes
        ):
            raise ValueError("OAuth permission requests require one distinct OAuth write scope.")
    elif oauth_patch_write_scope is not None:
        raise ValueError("OAuth write scope requires the permission-request candidate contract.")
    if oauth_approved_patch_enabled and not oauth_permission_requests_enabled:
        raise ValueError("OAuth approved patches require the permission-request candidate contract.")
    tools = [
        _tool_contract_entry(
            name,
            oauth_scopes=oauth_scopes,
            oauth_file_read_enabled=oauth_file_read_enabled,
            oauth_permission_requests_enabled=oauth_permission_requests_enabled,
            oauth_patch_write_scope=oauth_patch_write_scope,
            oauth_approved_patch_enabled=oauth_approved_patch_enabled,
        )
        for name in PUBLIC_TOOL_NAMES
    ]
    schema_version = (
        OAUTH_APPROVED_PATCH_FACADE_SCHEMA_VERSION if oauth_approved_patch_enabled
        else OAUTH_PERMISSION_REQUEST_FACADE_SCHEMA_VERSION if oauth_permission_requests_enabled
        else OAUTH_FILE_READ_FACADE_SCHEMA_VERSION if oauth_file_read_enabled
        else OAUTH_FACADE_SCHEMA_VERSION if oauth_enabled
        else FACADE_SCHEMA_VERSION
    )
    profile = (
        OAUTH_APPROVED_PATCH_FACADE_PROFILE if oauth_approved_patch_enabled
        else OAUTH_PERMISSION_REQUEST_FACADE_PROFILE if oauth_permission_requests_enabled
        else OAUTH_FILE_READ_FACADE_PROFILE if oauth_file_read_enabled
        else OAUTH_FACADE_PROFILE if oauth_enabled
        else FACADE_PROFILE
    )
    digest_input = {
        "schema_version": schema_version,
        "profile": profile,
        "tools": tools,
    }
    return {
        "schema_version": schema_version,
        "profile": profile,
        "sha256": hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest(),
        "tools": tools,
    }


def _contract_metadata(contract: dict[str, Any]) -> dict[str, int | str]:
    return {key: contract[key] for key in ("schema_version", "profile", "sha256")}


def _expected_contract(value: Any) -> dict[str, int | str]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "profile", "sha256"}:
        raise ValidationError("expected_facade_contract is invalid.")
    schema_version = value.get("schema_version")
    profile = value.get("profile")
    sha256 = value.get("sha256")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or not 1 <= schema_version <= 1_000_000
        or not isinstance(profile, str)
        or not 3 <= len(profile.strip()) <= 128
        or not isinstance(sha256, str)
        or re.fullmatch(r"[a-f0-9]{64}", sha256.strip().lower()) is None
    ):
        raise ValidationError("expected_facade_contract is invalid.")
    return {"schema_version": schema_version, "profile": profile.strip(), "sha256": sha256.strip().lower()}


class ContractMismatchError(ControlPlaneError):
    code = "CONTRACT_MISMATCH"


class ControlPlaneMcpFacade:
    """Stateless JSON-RPC boundary for one authenticated control-plane owner."""

    def __init__(
        self,
        store: ControlPlaneStore,
        *,
        oauth_scopes: tuple[str, ...] = (),
        oauth_file_read_enabled: bool = False,
        oauth_permission_requests_enabled: bool = False,
        oauth_patch_write_scope: str | None = None,
        oauth_approved_patch_enabled: bool = False,
    ) -> None:
        self.store = store
        self.oauth_scopes = oauth_scopes
        self.oauth_enabled = bool(oauth_scopes)
        if oauth_file_read_enabled and not self.oauth_enabled:
            raise ValueError("OAuth bounded file reads require OAuth tool scopes.")
        if oauth_permission_requests_enabled and (not self.oauth_enabled or not oauth_file_read_enabled):
            raise ValueError("OAuth permission requests require the OAuth bounded-file-read candidate contract.")
        if oauth_permission_requests_enabled:
            if (
                not isinstance(oauth_patch_write_scope, str)
                or not re.fullmatch(r"[A-Za-z0-9._:-]{3,128}", oauth_patch_write_scope)
                or oauth_patch_write_scope in oauth_scopes
            ):
                raise ValueError("OAuth permission requests require one distinct OAuth write scope.")
        elif oauth_patch_write_scope is not None:
            raise ValueError("OAuth write scope requires the permission-request candidate contract.")
        if oauth_approved_patch_enabled and not oauth_permission_requests_enabled:
            raise ValueError("OAuth approved patches require the permission-request candidate contract.")
        self.oauth_file_read_enabled = bool(oauth_file_read_enabled)
        self.oauth_permission_requests_enabled = bool(oauth_permission_requests_enabled)
        self.oauth_patch_write_scope = oauth_patch_write_scope
        self.oauth_approved_patch_enabled = bool(oauth_approved_patch_enabled)
        self.contract = tool_contract(
            oauth_scopes=oauth_scopes,
            oauth_file_read_enabled=self.oauth_file_read_enabled,
            oauth_permission_requests_enabled=self.oauth_permission_requests_enabled,
            oauth_patch_write_scope=self.oauth_patch_write_scope,
            oauth_approved_patch_enabled=self.oauth_approved_patch_enabled,
        )

    @property
    def _access_scope(self) -> str:
        return "oauth_account" if self.oauth_enabled else "server_issued_context_grant"

    @property
    def _execution_mode(self) -> str:
        if self.oauth_approved_patch_enabled:
            return "bounded_file_read_plus_approved_patch_local_policy_required"
        if self.oauth_permission_requests_enabled:
            return "bounded_file_read_plus_permission_request_local_mutation_bridge_required"
        if self.oauth_file_read_enabled:
            return "bounded_file_read_local_admission_required"
        return "no_local_execution" if self.oauth_enabled else "local_admission_required"

    def _result(self, request: dict[str, Any], value: dict[str, Any]) -> dict[str, Any] | None:
        if "id" not in request or request.get("id") is None:
            return None
        return {"jsonrpc": "2.0", "id": _response_id(request), "result": value}

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        requested = params.get("protocolVersion", MCP_PROTOCOL_VERSION)
        if not isinstance(requested, str) or not requested.strip():
            raise ValidationError("MCP protocol version must be a non-empty string.")
        negotiated = requested if requested in LEGACY_MCP_PROTOCOL_VERSIONS else MCP_PROTOCOL_VERSION
        return {
            "protocolVersion": negotiated,
            "serverInfo": {"name": "coding-tools-control-plane", "version": "0.1.0"},
            "capabilities": {"tools": {"listChanged": False}},
            "instructions": (
                "This facade returns account inventory, can queue one explicitly approved exact-file patch only under a distinct OAuth write scope and an "
                "independent local Windows patch policy, and can record owner-reviewed patch permission scopes. It cannot launch processes, select a last-used "
                "target, use remote shell, or access a workspace directly."
                if self.oauth_approved_patch_enabled
                else "This facade returns account inventory, can queue only one explicitly selected, policy-bounded read-only file action, and can record one "
                "owner-reviewed proposed patch permission scope. Permission approval is not an action or local grant. It cannot write files, launch processes, "
                "select a last-used target, or access a workspace directly."
                if self.oauth_permission_requests_enabled
                else "This facade returns account inventory and can queue only one explicitly selected, policy-bounded read-only file action. "
                "It cannot grant local authority, write files, launch processes, select a last-used target, or access a workspace directly."
                if self.oauth_file_read_enabled
                else "This facade returns only the authenticated account's authorized, path-free target inventory. It cannot select a target, "
                "create a context, queue an action, access a local workspace, or grant local admission."
                if self.oauth_enabled
                else "This facade is context-scoped central status plus a queued fixed read-only intent and a verified compact completed "
                "receipt projection. It never directly accesses a local workspace, calls a node, or grants local admission; a separate "
                "local bridge must accept and complete the action."
            ),
            "_meta": {
                "control_plane": {
                    "execution": self._execution_mode,
                    "access_scope": self._access_scope,
                    "tool_contract": {
                        key: self.contract[key] for key in ("schema_version", "profile", "sha256")
                    },
                }
            },
        }

    def _tools_list(self) -> dict[str, Any]:
        return {
            "tools": self.contract["tools"],
            "_meta": {
                "control_plane": {
                    "execution": self._execution_mode,
                    "access_scope": self._access_scope,
                    "tool_contract": {
                        key: self.contract[key] for key in ("schema_version", "profile", "sha256")
                    },
                }
            },
        }

    @staticmethod
    def _validate_stateless_params(params: dict[str, Any]) -> None:
        meta = params.get("_meta")
        if not isinstance(meta, dict) or meta.get("io.modelcontextprotocol/protocolVersion") != STATELESS_MCP_PROTOCOL_VERSION:
            raise ValidationError("MCP 2026-07-28 requires matching params._meta protocolVersion.")
        if not isinstance(meta.get("io.modelcontextprotocol/clientCapabilities"), dict):
            raise ValidationError("MCP 2026-07-28 requires params._meta clientCapabilities.")
        if "io.modelcontextprotocol/clientInfo" in meta:
            info = meta["io.modelcontextprotocol/clientInfo"]
            if not isinstance(info, dict) or not all(isinstance(info.get(key), str) for key in ("name", "version")):
                raise ValidationError("MCP clientInfo must contain string name and version fields when present.")

    @staticmethod
    def _stateless_result(result: dict[str, Any], *, cacheable: bool) -> dict[str, Any]:
        # Decorate the response, not the tool contract or any durable record.
        # Legacy and modern clients therefore observe the same authority and
        # exact eight-tool schema hash.
        decorated = {**result, "resultType": "complete"}
        decorated["_meta"] = {
            **result.get("_meta", {}),
            "io.modelcontextprotocol/serverInfo": {"name": "coding-tools-control-plane", "version": "0.1.0"},
        }
        if cacheable:
            decorated.update({"ttlMs": 0, "cacheScope": "private"})
        return decorated

    @staticmethod
    def _call_error(*, code: str, message: str, tool_name: str) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": message}],
            "structuredContent": {"code": code, "tool_name": tool_name, "execution": "not_implemented"},
            "isError": True,
        }

    def _arguments(self, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        name = params.get("name")
        if not isinstance(name, str) or name not in PUBLIC_TOOL_NAMES:
            raise ValidationError("tools/call name is unsupported.")
        arguments = params.get("arguments")
        if not isinstance(arguments, dict):
            raise ValidationError("tools/call arguments must be an object.")
        if name == "request_permissions" and self.oauth_permission_requests_enabled:
            operation = arguments.get("operation")
            if operation == "request_patch":
                required = {
                    "operation", "binding_id", "path", "preimage_sha256", "patch_sha256",
                    "validation_profile", "idempotency_key", "expected_facade_contract",
                }
                if set(arguments) != required:
                    raise ValidationError("request_patch requires one exact target, patch digests, validation profile, idempotency key and expected facade contract.")
                binding_id = arguments.get("binding_id")
                path = arguments.get("path")
                key = arguments.get("idempotency_key")
                if not isinstance(binding_id, str) or not 3 <= len(binding_id.strip()) <= 128:
                    raise ValidationError("binding_id is invalid.")
                try:
                    path_bytes = path.encode("utf-8") if isinstance(path, str) else b""
                except UnicodeEncodeError:
                    path_bytes = b""
                if not isinstance(path, str) or not 1 <= len(path_bytes) <= 512:
                    raise ValidationError("path is invalid.")
                if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
                    raise ValidationError("idempotency_key is invalid.")
                hashes = {
                    field: arguments.get(field)
                    for field in ("preimage_sha256", "patch_sha256")
                }
                if any(
                    not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value.strip().lower()) is None
                    for value in hashes.values()
                ):
                    raise ValidationError("patch scope digest is invalid.")
                if arguments.get("validation_profile") != MCP_PATCH_PERMISSION_VALIDATION_PROFILE:
                    raise ValidationError("validation_profile is invalid.")
                return name, {
                    "operation": "request_patch",
                    "binding_id": binding_id.strip(),
                    "path": path,
                    "preimage_sha256": str(hashes["preimage_sha256"]).strip().lower(),
                    "patch_sha256": str(hashes["patch_sha256"]).strip().lower(),
                    "validation_profile": MCP_PATCH_PERMISSION_VALIDATION_PROFILE,
                    "idempotency_key": key.strip(),
                    "expected_facade_contract": _expected_contract(arguments.get("expected_facade_contract")),
                }
            if operation == "status":
                if set(arguments) != {"operation", "permission_request_id"}:
                    raise ValidationError("permission request status requires an exact permission_request_id and no other arguments.")
                permission_request_id = arguments.get("permission_request_id")
                if not isinstance(permission_request_id, str) or not 3 <= len(permission_request_id.strip()) <= 128:
                    raise ValidationError("permission_request_id is invalid.")
                return name, {"operation": "status", "permission_request_id": permission_request_id.strip()}
            raise ValidationError("request_permissions operation is unsupported.")
        if name == "agent_workflow" and self.oauth_approved_patch_enabled:
            operation = arguments.get("operation")
            if operation == "apply_patch":
                required = {
                    "operation", "permission_request_id", "patch_envelope",
                    "idempotency_key", "expected_facade_contract",
                }
                if set(arguments) != required:
                    raise ValidationError("apply_patch requires one approved permission request, exact patch envelope, idempotency key and expected facade contract.")
                permission_request_id = arguments.get("permission_request_id")
                patch_envelope = arguments.get("patch_envelope")
                key = arguments.get("idempotency_key")
                if not isinstance(permission_request_id, str) or not 3 <= len(permission_request_id.strip()) <= 128:
                    raise ValidationError("permission_request_id is invalid.")
                if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
                    raise ValidationError("idempotency_key is invalid.")
                try:
                    patch_bytes = patch_envelope.encode("utf-8") if isinstance(patch_envelope, str) else b""
                except UnicodeEncodeError:
                    patch_bytes = b""
                if not patch_bytes or len(patch_bytes) > MCP_APPROVED_PATCH_MAX_BYTES:
                    raise ValidationError("patch_envelope is invalid.")
                return name, {
                    "operation": "apply_patch",
                    "permission_request_id": permission_request_id.strip(),
                    "patch_envelope": patch_envelope,
                    "idempotency_key": key.strip(),
                    "expected_facade_contract": _expected_contract(arguments.get("expected_facade_contract")),
                }
            if operation == "patch_status":
                if set(arguments) != {"operation", "action_id"}:
                    raise ValidationError("patch_status requires an exact action_id and no other arguments.")
                action_id = arguments.get("action_id")
                if not isinstance(action_id, str) or not 3 <= len(action_id.strip()) <= 128:
                    raise ValidationError("action_id is invalid.")
                return name, {"operation": "patch_status", "action_id": action_id.strip()}
            raise ValidationError("agent_workflow operation is unsupported.")
        if name != "workspace_context":
            if arguments:
                raise ValidationError(f"{name} does not accept arguments while its relay is unavailable.")
            return name, {}
        if self.oauth_enabled:
            operation = arguments.get("operation")
            if operation == "inventory":
                if arguments != {"operation": "inventory"}:
                    raise ValidationError("OAuth account inventory requires operation=inventory and no target arguments.")
                return name, {"operation": "inventory"}
            if not self.oauth_file_read_enabled:
                raise ValidationError("OAuth account inventory requires operation=inventory and no target arguments.")
            if operation == "read_file":
                allowed = {
                    "operation", "binding_id", "path", "start_line", "max_lines", "max_bytes",
                    "idempotency_key", "expected_facade_contract",
                }
                required = {"operation", "binding_id", "path", "idempotency_key", "expected_facade_contract"}
                if not required <= set(arguments) or not set(arguments) <= allowed:
                    raise ValidationError("read_file requires an exact binding, path, idempotency key and expected facade contract.")
                binding_id = arguments.get("binding_id")
                path = arguments.get("path")
                key = arguments.get("idempotency_key")
                if not isinstance(binding_id, str) or not 3 <= len(binding_id.strip()) <= 128:
                    raise ValidationError("binding_id is invalid.")
                try:
                    path_bytes = path.encode("utf-8") if isinstance(path, str) else b""
                except UnicodeEncodeError:
                    path_bytes = b""
                if not isinstance(path, str) or not 1 <= len(path_bytes) <= 512:
                    raise ValidationError("path is invalid.")
                if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
                    raise ValidationError("idempotency_key is invalid.")
                result: dict[str, Any] = {
                    "operation": "read_file",
                    "binding_id": binding_id.strip(),
                    "path": path,
                    "start_line": arguments.get("start_line", 1),
                    "max_lines": arguments.get("max_lines", FILE_READ_MAX_LINES),
                    "max_bytes": arguments.get("max_bytes", FILE_READ_MAX_BYTES),
                    "idempotency_key": key.strip(),
                    "expected_facade_contract": _expected_contract(arguments.get("expected_facade_contract")),
                }
                for field, maximum in (("start_line", 1_000_000), ("max_lines", FILE_READ_MAX_LINES), ("max_bytes", FILE_READ_MAX_BYTES)):
                    value = result[field]
                    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
                        raise ValidationError(f"{field} is invalid.")
                return name, result
            if operation == "read_status":
                if set(arguments) != {"operation", "action_id"}:
                    raise ValidationError("read_status requires an exact action_id and no other arguments.")
                action_id = arguments.get("action_id")
                if not isinstance(action_id, str) or not 3 <= len(action_id.strip()) <= 128:
                    raise ValidationError("action_id is invalid.")
                return name, {"operation": "read_status", "action_id": action_id.strip()}
            raise ValidationError("OAuth workspace_context operation is unsupported.")
        context_id = arguments.get("context_id")
        if not isinstance(context_id, str) or not 3 <= len(context_id.strip()) <= 128:
            raise ValidationError("context_id is invalid.")
        operation = arguments.get("operation", "status")
        if operation not in {"status", "request_read_only"}:
            raise ValidationError("operation is unsupported.")
        result = {"context_id": context_id.strip(), "operation": operation}
        if operation == "status":
            if not set(arguments) <= {"context_id", "action_id", "operation"}:
                raise ValidationError("status operation accepts context_id and optional action_id only.")
            if "action_id" not in arguments:
                return name, result
            action_id = arguments.get("action_id")
            if not isinstance(action_id, str) or not 3 <= len(action_id.strip()) <= 128:
                raise ValidationError("action_id is invalid.")
            result["action_id"] = action_id.strip()
            return name, result
        if set(arguments) != {"context_id", "operation", "idempotency_key", "expires_at_ms", "expected_facade_contract"}:
            raise ValidationError("request_read_only requires exact context, idempotency, expiry and expected facade contract.")
        key = arguments.get("idempotency_key")
        if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
            raise ValidationError("idempotency_key is invalid.")
        expiry = arguments.get("expires_at_ms")
        if not isinstance(expiry, int) or isinstance(expiry, bool) or expiry <= 0:
            raise ValidationError("expires_at_ms is invalid.")
        result["idempotency_key"] = key.strip()
        result["expires_at_ms"] = expiry
        result["expected_facade_contract"] = _expected_contract(arguments.get("expected_facade_contract"))
        return name, result

    def _action_status(self, *, owner_id: str, context_id: str, action_id: str) -> dict[str, Any]:
        """Return an allowlisted lifecycle projection for this exact context.

        Receipt payloads may be implementation-specific and action arguments
        belong to the sealed authority record, so neither is a facade status
        field. A caller can learn that a receipt exists, not its raw content.
        """
        action = self.store.action_observation(owner_id=owner_id, action_id=action_id)
        if action.get("context_id") != context_id:
            raise ValidationError("action_id does not belong to context_id.")
        return {
            "action_id": action["action_id"],
            "action_digest": action["action_digest"],
            "tool_name": action["tool_name"],
            "created_at_ms": action["created_at_ms"],
            "expires_at_ms": action["expires_at_ms"],
            "delivery_state": action["delivery_state"],
            "central_lifecycle_state": _central_lifecycle_state(action),
            "settled_at_ms": action["settled_at_ms"],
            "attempts": [
                {
                    "attempt_id": attempt["attempt_id"],
                    "attempt_number": attempt["attempt_number"],
                    "dispatched_at_ms": attempt["dispatched_at_ms"],
                }
                for attempt in action["attempts"]
            ],
            "receipts": [
                {
                    "receipt_id": receipt["receipt_id"],
                    "receipt_state": receipt["receipt_state"],
                    "received_at_ms": receipt["received_at_ms"],
                    "receipt_digest": receipt["receipt_digest"],
                }
                for receipt in action["receipts"]
            ],
        }

    def _workspace_context(self, *, owner_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
        context = self.store.context(owner_id=owner_id, context_id=arguments["context_id"])
        node = self.store.node_observation(owner_id=owner_id, device_id=str(context["device_id"]))
        now = self.store.clock()
        if context["closed_at_ms"] is not None:
            context_state = "closed"
        elif int(context["expires_at_ms"]) <= now:
            context_state = "expired"
        else:
            context_state = "active"
        observation = {
            "schema_version": self.contract["schema_version"],
            "observation_kind": "control_plane_workspace_status",
            "workspace_accessed": False,
            "execution": "not_implemented",
            "local_admission": "unverified",
            "context": {
                key: context[key]
                for key in (
                    "context_id",
                    "binding_id",
                    "device_id",
                    "endpoint_id",
                    "workspace_id",
                    "workspace_generation",
                    "created_at_ms",
                    "expires_at_ms",
                    "closed_at_ms",
                )
            },
            "context_state": context_state,
            "node": {
                key: node[key]
                for key in (
                    "device_id",
                    "endpoint_id",
                    "revoked_at_ms",
                    "last_seen_at_ms",
                    "runtime_instance_id",
                    "mcp_server_instance_id",
                    "activation_epoch",
                    "contract_version",
                    "readiness",
                )
            },
        }
        content = "Central status only; no local workspace was accessed."
        if "action_id" in arguments:
            observation["action"] = self._action_status(
                owner_id=owner_id,
                context_id=context["context_id"],
                action_id=arguments["action_id"],
            )
            action = self.store.action_observation(owner_id=owner_id, action_id=arguments["action_id"])
            relay = _completed_workspace_relay(action, _contract_metadata(self.contract))
            if relay is not None:
                observation.update({
                    "workspace_accessed": True,
                    "execution": "completed_read_relay",
                    "local_admission": "completed",
                    "workspace_read": relay,
                })
                content = "Compact workspace metadata was read by the selected local node and relayed through its completed receipt."
        return {
            "content": [{"type": "text", "text": content}],
            "structuredContent": observation,
            "isError": False,
        }

    def _request_read_only_workspace_context(
        self,
        *,
        owner_id: str,
        principal_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        current_contract = _contract_metadata(self.contract)
        if arguments["expected_facade_contract"] != current_contract:
            raise ContractMismatchError("expected facade contract does not match this control-plane surface.")
        intent = self.store.request_mcp_read_only_workspace_context(
            owner_id=owner_id,
            context_id=arguments["context_id"],
            idempotency_key=arguments["idempotency_key"],
            expires_at_ms=arguments["expires_at_ms"],
            facade_contract=current_contract,
            principal_id=principal_id,
        )
        action = self._action_status(
            owner_id=owner_id,
            context_id=arguments["context_id"],
            action_id=intent["action_id"],
        )
        return {
            "content": [{"type": "text", "text": "Read-only intent is queued for local admission; no local workspace was accessed by the facade."}],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_read_only_intent",
                "workspace_accessed": False,
                "execution": "queued_for_local_admission",
                "local_admission": "required",
                "request_id": intent["request_id"],
                "action_id": intent["action_id"],
                "intent_digest": intent["intent_digest"],
                "facade_contract": intent["facade_contract"],
                "replayed": intent["replayed"],
                "action": action,
            },
            "isError": False,
        }

    def _account_inventory(self, *, owner_id: str, principal_id: str) -> dict[str, Any]:
        """Expose account targets without materializing a task context or action."""

        targets = self.store.list_account_targets(owner_id=owner_id)
        return {
            "content": [{"type": "text", "text": "Authorized target inventory only; no workspace was accessed and no task authority was created."}],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_account_target_inventory",
                "workspace_accessed": False,
                "execution": "no_local_execution",
                "local_admission": "not_requested",
                "principal_id": principal_id,
                "targets": targets,
            },
            "isError": False,
        }

    @staticmethod
    def _action_lifecycle_projection(action: dict[str, Any]) -> dict[str, Any]:
        """Expose lifecycle evidence without sealed arguments or local handles."""

        return {
            "action_id": action["action_id"],
            "action_digest": action["action_digest"],
            "tool_name": action["tool_name"],
            "created_at_ms": action["created_at_ms"],
            "expires_at_ms": action["expires_at_ms"],
            "delivery_state": action["delivery_state"],
            "central_lifecycle_state": _central_lifecycle_state(action),
            "settled_at_ms": action["settled_at_ms"],
            "attempts": [
                {
                    "attempt_id": attempt["attempt_id"],
                    "attempt_number": attempt["attempt_number"],
                    "dispatched_at_ms": attempt["dispatched_at_ms"],
                }
                for attempt in action["attempts"]
            ],
            "receipts": [
                {
                    "receipt_id": receipt["receipt_id"],
                    "receipt_state": receipt["receipt_state"],
                    "received_at_ms": receipt["received_at_ms"],
                    "receipt_digest": receipt["receipt_digest"],
                }
                for receipt in action["receipts"]
            ],
        }

    def _request_bounded_file_read(
        self,
        *,
        owner_id: str,
        principal_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        current_contract = _contract_metadata(self.contract)
        if arguments["expected_facade_contract"] != current_contract:
            raise ContractMismatchError("expected facade contract does not match this control-plane surface.")
        intent = self.store.request_mcp_bounded_file_read(
            owner_id=owner_id,
            principal_id=principal_id,
            binding_id=arguments["binding_id"],
            path=arguments["path"],
            start_line=arguments["start_line"],
            max_lines=arguments["max_lines"],
            max_bytes=arguments["max_bytes"],
            idempotency_key=arguments["idempotency_key"],
            facade_contract=current_contract,
        )
        action = self.store.mcp_file_read_action_observation(
            owner_id=owner_id,
            principal_id=principal_id,
            action_id=intent["action_id"],
        )
        return {
            "content": [{"type": "text", "text": "Bounded file-read intent is queued for local Windows policy admission; no local file was accessed by the facade."}],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_bounded_file_read_intent",
                "file_accessed": False,
                "execution": "queued_for_local_admission",
                "local_admission": "required",
                "request_id": intent["request_id"],
                "action_id": intent["action_id"],
                "intent_digest": intent["intent_digest"],
                "facade_contract": intent["facade_contract"],
                "replayed": intent["replayed"],
                "action": self._action_lifecycle_projection(action),
            },
            "isError": False,
        }

    def _bounded_file_read_status(
        self,
        *,
        owner_id: str,
        principal_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        action = self.store.mcp_file_read_action_observation(
            owner_id=owner_id,
            principal_id=principal_id,
            action_id=action_id,
        )
        relay = _completed_bounded_file_read_relay(action, _contract_metadata(self.contract))
        observation: dict[str, Any] = {
            "schema_version": self.contract["schema_version"],
            "observation_kind": "control_plane_bounded_file_read_status",
            "file_accessed": relay is not None,
            "execution": "completed_file_read_relay" if relay is not None else "local_admission_pending_or_unverified",
            "local_admission": "completed" if relay is not None else "required_or_pending",
            "action": self._action_lifecycle_projection(action),
        }
        content = "Bounded file-read action has no verified completed receipt yet."
        if relay is not None:
            observation["file_read"] = relay
            content = "The selected local Windows node read one policy-bounded file and relayed its verified receipt."
        return {
            "content": [{"type": "text", "text": content}],
            "structuredContent": observation,
            "isError": False,
        }

    def _request_patch_permission(
        self,
        *,
        owner_id: str,
        principal_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Create one C4 approval request without creating an action/effect."""

        current_contract = _contract_metadata(self.contract)
        if arguments["expected_facade_contract"] != current_contract:
            raise ContractMismatchError("expected facade contract does not match this control-plane surface.")
        request = self.store.request_mcp_patch_permission(
            owner_id=owner_id,
            principal_id=principal_id,
            binding_id=arguments["binding_id"],
            path=arguments["path"],
            preimage_sha256=arguments["preimage_sha256"],
            patch_sha256=arguments["patch_sha256"],
            validation_profile=arguments["validation_profile"],
            idempotency_key=arguments["idempotency_key"],
            facade_contract=current_contract,
        )
        return {
            "content": [{
                "type": "text",
                "text": "Patch permission request is pending owner review. It did not queue an action, change Windows policy, read a workspace, write a file, or launch a process.",
            }],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_patch_permission_request",
                "execution": "not_started",
                "workspace_accessed": False,
                "local_admission": "not_requested",
                "permission_request": request,
            },
            "isError": False,
        }

    def _patch_permission_status(
        self,
        *,
        owner_id: str,
        principal_id: str,
        permission_request_id: str,
    ) -> dict[str, Any]:
        request = self.store.mcp_permission_request_observation(
            owner_id=owner_id,
            principal_id=principal_id,
            permission_request_id=permission_request_id,
        )
        return {
            "content": [{
                "type": "text",
                "text": "Permission request status only. Even an approved request has no local execution effect until a future Windows mutation bridge independently revalidates it.",
            }],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_patch_permission_status",
                "execution": "not_started",
                "workspace_accessed": False,
                "local_admission": "not_requested",
                "permission_request": request,
            },
            "isError": False,
        }

    def _request_approved_patch(
        self,
        *,
        owner_id: str,
        principal_id: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Seal a reviewed patch without treating queue persistence as effect."""

        current_contract = _contract_metadata(self.contract)
        if arguments["expected_facade_contract"] != current_contract:
            raise ContractMismatchError("expected facade contract does not match this control-plane surface.")
        intent = self.store.request_mcp_approved_patch(
            owner_id=owner_id,
            principal_id=principal_id,
            permission_request_id=arguments["permission_request_id"],
            patch_envelope=arguments["patch_envelope"],
            idempotency_key=arguments["idempotency_key"],
            facade_contract=current_contract,
        )
        action = self.store.mcp_approved_patch_action_observation(
            owner_id=owner_id,
            principal_id=principal_id,
            action_id=intent["action_id"],
        )
        return {
            "content": [{
                "type": "text",
                "text": "Approved patch action is queued for independent local Windows patch-policy admission. The root MCP has not written a file or launched a process.",
            }],
            "structuredContent": {
                "schema_version": self.contract["schema_version"],
                "observation_kind": "control_plane_approved_patch_intent",
                "execution": "queued_for_local_patch_policy",
                "workspace_accessed": False,
                "patch_applied": False,
                "local_admission": "required",
                "request_id": intent["request_id"],
                "action_id": intent["action_id"],
                "intent_digest": intent["intent_digest"],
                "facade_contract": intent["facade_contract"],
                "replayed": intent["replayed"],
                "action": self._action_lifecycle_projection(action),
            },
            "isError": False,
        }

    def _approved_patch_status(
        self,
        *,
        owner_id: str,
        principal_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        action = self.store.mcp_approved_patch_action_observation(
            owner_id=owner_id,
            principal_id=principal_id,
            action_id=action_id,
        )
        expected_file = self.store.mcp_approved_patch_expected_file(
            owner_id=owner_id,
            principal_id=principal_id,
            action_id=action_id,
        )
        relay = _completed_approved_patch_relay(
            action,
            _contract_metadata(self.contract),
            expected_file,
        )
        # A durable ``unknown`` receipt is materially different from a
        # not-yet-delivered patch.  It means the node crossed its prepared
        # boundary and cannot prove whether the effect occurred.  Do not let
        # a generic "pending" label encourage a caller to queue the same
        # exact write again: recovery must inspect/reconcile the local target
        # under local authority first.
        if action["delivery_state"] == "reconcile_required":
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        "The local approved-patch delivery has an unknown effect and requires local reconciliation. "
                        "Do not retry or create a replacement patch action automatically; the local owner must inspect "
                        "the exact target and reconcile it before any new mutation is considered."
                    ),
                }],
                "structuredContent": {
                    "schema_version": self.contract["schema_version"],
                    "observation_kind": "control_plane_approved_patch_status",
                    "execution": "local_patch_effect_unknown_reconcile_required",
                    "workspace_accessed": False,
                    # ``None`` is intentional: ``false`` would claim that a
                    # patch was not applied, which the durable UNKNOWN state
                    # cannot establish.
                    "patch_applied": None,
                    "patch_effect_state": "unknown",
                    "local_admission": "unknown_effect_do_not_retry",
                    "local_semantic_acceptance": "unknown",
                    "reconciliation_required": True,
                    "action": self._action_lifecycle_projection(action),
                },
                "isError": False,
            }
        observation: dict[str, Any] = {
            "schema_version": self.contract["schema_version"],
            "observation_kind": "control_plane_approved_patch_status",
            "execution": "effect_applied_pending_local_acceptance" if relay is not None else "local_patch_receipt_pending_or_unverified",
            "workspace_accessed": False,
            "patch_applied": relay is not None,
            "patch_effect_state": "verified_applied" if relay is not None else "not_verified",
            "local_admission": "effect_applied_local_acceptance_pending" if relay is not None else "required_or_pending",
            "action": self._action_lifecycle_projection(action),
        }
        content = "Approved patch action has no verified completed local receipt yet."
        if relay is not None:
            observation["patch"] = relay
            observation["local_semantic_acceptance"] = relay["local_semantic_acceptance"]
            content = (
                "The selected local Windows node applied the exact approved patch and relayed a verified receipt. "
                "Its local Coding Tools RUN still requires separate proof and semantic acceptance."
            )
        return {
            "content": [{"type": "text", "text": content}],
            "structuredContent": observation,
            "isError": False,
        }

    def _has_patch_write_scope(self, oauth_scopes: frozenset[str]) -> bool:
        if not self.oauth_permission_requests_enabled or not isinstance(self.oauth_patch_write_scope, str):
            return False
        return set(self.oauth_scopes) <= set(oauth_scopes) and self.oauth_patch_write_scope in oauth_scopes

    @staticmethod
    def _require_granted_context(*, requested_context_id: str, granted_context_id: str | None) -> None:
        if requested_context_id != granted_context_id:
            raise PermissionError("MCP client access grant does not cover context_id.")

    def _call_tool(
        self,
        *,
        owner_id: str,
        principal_id: str,
        granted_context_id: str | None,
        oauth_scopes: frozenset[str],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        name, arguments = self._arguments(params)
        if name == "request_permissions" and self.oauth_permission_requests_enabled:
            if not self._has_patch_write_scope(oauth_scopes):
                return self._call_error(
                    code="OAUTH_WRITE_SCOPE_REQUIRED",
                    message="This mutation candidate requires the dedicated OAuth write scope.",
                    tool_name=name,
                )
            if arguments["operation"] == "request_patch":
                return self._request_patch_permission(
                    owner_id=owner_id,
                    principal_id=principal_id,
                    arguments=arguments,
                )
            return self._patch_permission_status(
                owner_id=owner_id,
                principal_id=principal_id,
                permission_request_id=arguments["permission_request_id"],
            )
        if name == "agent_workflow" and self.oauth_approved_patch_enabled:
            if not self._has_patch_write_scope(oauth_scopes):
                return self._call_error(
                    code="OAUTH_WRITE_SCOPE_REQUIRED",
                    message="This mutation candidate requires the dedicated OAuth write scope.",
                    tool_name=name,
                )
            if arguments["operation"] == "apply_patch":
                return self._request_approved_patch(
                    owner_id=owner_id,
                    principal_id=principal_id,
                    arguments=arguments,
                )
            return self._approved_patch_status(
                owner_id=owner_id,
                principal_id=principal_id,
                action_id=arguments["action_id"],
            )
        if name != "workspace_context":
            return self._call_error(
                code="LOCAL_ADMISSION_BRIDGE_REQUIRED",
                message="This tool is advertised as unavailable until its local admission bridge and relay scope are implemented.",
                tool_name=name,
            )
        if self.oauth_enabled:
            if arguments["operation"] == "inventory":
                return self._account_inventory(owner_id=owner_id, principal_id=principal_id)
            if arguments["operation"] == "read_file":
                return self._request_bounded_file_read(
                    owner_id=owner_id,
                    principal_id=principal_id,
                    arguments=arguments,
                )
            return self._bounded_file_read_status(
                owner_id=owner_id,
                principal_id=principal_id,
                action_id=arguments["action_id"],
            )
        self._require_granted_context(
            requested_context_id=arguments["context_id"],
            granted_context_id=granted_context_id,
        )
        if arguments["operation"] == "request_read_only":
            return self._request_read_only_workspace_context(
                owner_id=owner_id,
                principal_id=principal_id,
                arguments=arguments,
            )
        return self._workspace_context(owner_id=owner_id, arguments=arguments)

    def handle(
        self,
        request: dict[str, Any],
        *,
        owner_id: str,
        principal_id: str,
        granted_context_id: str | None,
        oauth_scopes: frozenset[str] | None = None,
        stateless_2026: bool = False,
    ) -> dict[str, Any] | None:
        """Handle one authenticated JSON-RPC request without persistent session state."""
        request_id = _response_id(request)
        if oauth_scopes is None:
            # Direct facade tests and the legacy grant path have no HTTP
            # verifier.  The real OAuth ingress always supplies the verified
            # access-token scope set below; do not make the constructor's
            # advertised scope an HTTP authority substitute.
            effective_oauth_scopes = frozenset(self.oauth_scopes) if self.oauth_enabled else frozenset()
        elif not isinstance(oauth_scopes, frozenset) or any(not isinstance(scope, str) for scope in oauth_scopes):
            raise ValidationError("OAuth scope set is invalid.")
        else:
            effective_oauth_scopes = oauth_scopes
        if "id" not in request:
            # This stateless facade has no client notifications to persist or
            # dispatch. Accept initialized (and ignore unknown notifications)
            # without a JSON-RPC response. Invalid notifications are rejected
            # by the HTTP boundary, never interpreted as tool requests.
            if (
                request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)
                or not request["method"].startswith("notifications/")
                or not request["method"][len("notifications/"):]
                or not isinstance(request.get("params", {}), dict)
            ):
                raise ValidationError("MCP notification is invalid or a request id is missing.")
            return None
        try:
            if (
                request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)
                or not request["method"]
                or request_id is None
            ):
                return _rpc_error(request_id, -32600, "Invalid Request")
            params = request.get("params", {})
            if params is None:
                params = {}
            if not isinstance(params, dict):
                raise ValidationError("MCP method params must be an object.")
            method = request["method"]
            if stateless_2026:
                self._validate_stateless_params(params)
            if stateless_2026 and method in {"initialize", "ping"}:
                return _rpc_error(request_id, -32601, "Method not found")
            if method == "initialize":
                if request_id is None:
                    return _rpc_error(None, -32600, "Invalid Request: initialize requires a non-null request id")
                result = self._initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = self._tools_list()
            elif method == "server/discover":
                if stateless_2026:
                    initialized = self._initialize({})
                    result = {
                        "supportedVersions": list(SUPPORTED_MCP_PROTOCOL_VERSIONS),
                        "capabilities": initialized["capabilities"],
                        "instructions": initialized["instructions"],
                        "_meta": initialized["_meta"],
                    }
                else:
                    result = {**self._initialize({}), **self._tools_list()}
            elif method == "tools/call":
                result = self._call_tool(
                    owner_id=owner_id,
                    principal_id=principal_id,
                    granted_context_id=granted_context_id,
                    oauth_scopes=effective_oauth_scopes,
                    params=params,
                )
            else:
                return _rpc_error(request_id, -32601, f"Unknown method: {method}")
            if stateless_2026:
                result = self._stateless_result(result, cacheable=method in {"server/discover", "tools/list"})
            return self._result(request, result)
        except ControlPlaneError as error:
            return _rpc_error(request_id, -32602, "Invalid params", {"code": error.code, "message": str(error)})
