"""Minimal Windows/other-node client for enrollment, heartbeat and safe polling.

The default poll command never executes or dequeues an action. The separately
named ``poll-read-only-once`` lane is the only exception: it can forward one
exact, locally policy-admitted ``workspace_context`` observation through
Recovery IPC.
It does not expose the descriptor/token, accept arbitrary arguments, or grant
remote mutation authority.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
import uuid
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
READ_ONLY_TOOL_NAME = "workspace_context"
READ_ONLY_ARGUMENTS = {"detail": "compact", "max_entries": 1}
READ_ONLY_JOURNAL_SCHEMA_VERSION = 1
READ_ONLY_POLICY_SCHEMA_VERSION = 2
READ_ONLY_POLICY_MAX_BYTES = 16 * 1024
READ_ONLY_POLICY_MAX_TTL_MS = 24 * 60 * 60 * 1000
READ_ONLY_POLICY_FILE_NAME = "control-plane-read-only-policy.json"
ROUTE_EVIDENCE_FILE_NAME = "control-plane-route-evidence.json"
ROUTE_EVIDENCE_SCHEMA_VERSION = 1
ROUTE_EVIDENCE_KIND = "control_plane_authenticated_heartbeat"
STANDING_POLICY_OBSERVATION_TTL_MS = 60_000
READ_ONLY_LOOP_MIN_INTERVAL_SECONDS = 15
READ_ONLY_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
READ_ONLY_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
READ_ONLY_AGENT_LOCK_SCHEMA_VERSION = 1
READ_ONLY_AGENT_MAX_BACKOFF_SECONDS = 15 * 60
CONNECTED_AGENT_LOCK_SCHEMA_VERSION = 1
CONNECTED_AGENT_MAX_BACKOFF_SECONDS = 15 * 60
FILE_READ_TOOL_NAME = "workspace_context"
FILE_READ_OPERATION = "read_file"
FILE_READ_JOURNAL_SCHEMA_VERSION = 1
FILE_READ_POLICY_SCHEMA_VERSION = 3
FILE_READ_POLICY_EXACT_SCHEMA_VERSION = 2
FILE_READ_POLICY_LEGACY_SCHEMA_VERSION = 1
FILE_READ_POLICY_STANDING_AUTHORITY = "standing"
FILE_READ_POLICY_MAX_BYTES = 16 * 1024
FILE_READ_POLICY_MAX_TTL_MS = 24 * 60 * 60 * 1000
FILE_READ_POLICY_FILE_NAME = "control-plane-file-read-policy.json"
FILE_READ_MAX_BYTES = 16 * 1024
FILE_READ_MAX_LINES = 200
FILE_READ_MAX_ALLOWED_PATHS = 32
FILE_READ_LOOP_MIN_INTERVAL_SECONDS = 15
FILE_READ_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
FILE_READ_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
FILE_READ_LOOP_LOCK_SCHEMA_VERSION = 1
APPROVED_PATCH_TOOL_NAME = "agent_workflow"
APPROVED_PATCH_OPERATION = "apply_patch"
APPROVED_PATCH_VALIDATION_PROFILE = "targeted"
APPROVED_PATCH_JOURNAL_SCHEMA_VERSION = 1
APPROVED_PATCH_POLICY_SCHEMA_VERSION = 3
APPROVED_PATCH_POLICY_EXACT_SCHEMA_VERSION = 2
APPROVED_PATCH_POLICY_LEGACY_SCHEMA_VERSION = 1
APPROVED_PATCH_POLICY_STANDING_AUTHORITY = "standing"
APPROVED_PATCH_POLICY_MAX_BYTES = 16 * 1024
APPROVED_PATCH_POLICY_MAX_TTL_MS = 24 * 60 * 60 * 1000
APPROVED_PATCH_POLICY_FILE_NAME = "control-plane-approved-patch-policy.json"
APPROVED_PATCH_MAX_BYTES = 32 * 1024
APPROVED_PATCH_MAX_FILE_BYTES = 256 * 1024
APPROVED_PATCH_MAX_ALLOWED_PATHS = 32
APPROVED_PATCH_LOOP_MIN_INTERVAL_SECONDS = 15
APPROVED_PATCH_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
APPROVED_PATCH_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
APPROVED_PATCH_LOOP_LOCK_SCHEMA_VERSION = 1
APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$")
MCP_TASK_ID_PATTERN = re.compile(r"^task_[a-f0-9]{32}$")
DOCUMENT_WRITE_TOOL_NAME = "document_workflow"
DOCUMENT_WRITE_OPERATIONS = frozenset({"document_create", "document_convert"})
DOCUMENT_WRITE_ACTION_IDENTIFIER_PATTERN = APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN
DOCUMENT_WRITE_JOURNAL_SCHEMA_VERSION = 1
DOCUMENT_WRITE_MAX_CONTENT_BYTES = 256 * 1024
DOCUMENT_WRITE_MAX_TITLE_BYTES = 256
DOCUMENT_WRITE_MAX_RESULT_BYTES = 256 * 1024
DOCUMENT_WRITE_TARGET_SUFFIXES = frozenset({".docx", ".md", ".txt"})
DOCUMENT_WRITE_SOURCE_SUFFIXES = frozenset({".pdf", ".docx", ".md", ".txt", ".csv", ".json", ".xml", ".html", ".htm"})
DOCUMENT_WRITE_LOOP_MIN_INTERVAL_SECONDS = 15
DOCUMENT_WRITE_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
DOCUMENT_WRITE_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
DOCUMENT_WRITE_LOOP_LOCK_SCHEMA_VERSION = 1
EXEC_TOOL_NAME = "exec_command"
EXEC_OPERATION = "exec_run"
EXEC_JOURNAL_SCHEMA_VERSION = 1
EXEC_POLICY_SCHEMA_VERSION = 2
EXEC_POLICY_LEGACY_SCHEMA_VERSION = 1
EXEC_POLICY_STANDING_AUTHORITY = "standing"
EXEC_POLICY_MAX_BYTES = 16 * 1024
EXEC_POLICY_MAX_TTL_MS = 24 * 60 * 60 * 1000
EXEC_POLICY_FILE_NAME = "control-plane-exec-policy.json"
EXEC_MAX_ARGV_ITEMS = 8
EXEC_MAX_ARGV_ITEM_BYTES = 256
EXEC_MAX_TIMEOUT_MS = 5 * 60 * 1000
EXEC_MIN_TIMEOUT_MS = 5_000
EXEC_MAX_OUTPUT_BYTES = 64 * 1024
EXEC_MAX_ALLOWED_PREFIXES = 16
EXEC_LOOP_MIN_INTERVAL_SECONDS = 15
EXEC_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
EXEC_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
EXEC_LOOP_LOCK_SCHEMA_VERSION = 1
EXEC_ACTION_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$")
EXEC_COMMAND_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$")
EXEC_LOCAL_HANDLE_PATTERN = re.compile(r"^cp_exec_[a-f0-9]{48}$")
EXEC_CONTROL_OPERATIONS = frozenset({"exec_run", "exec_poll", "exec_stop"})
EXEC_CONTROL_SIGNALS = frozenset({"TERM", "KILL", "INT"})
NODE_CONFIG_SCHEMA_VERSION = 1
NODE_SECRET_PROTECTED_FIELD = "node_secret_dpapi"
NODE_SECRET_PENDING_FIELD = "node_secret_pending"
NODE_SECRET_PENDING_PROTECTED_FIELD = "node_secret_pending_dpapi"
NODE_SECRET_PROTECTED_PREFIX = "dpapi-v1:"
NODE_SECRET_MAX_BYTES = 4096
NODE_SECRET_ENTROPY = b"Tools-Codex-web/control-plane-node/v1"
ENROLLMENT_ID_PATTERN = re.compile(r"^enroll[A-Za-z0-9_.:-]{3,255}$")
NODE_ROTATION_ID_PATTERN = re.compile(r"^rotate_[a-f0-9]{32}$")
NODE_ROTATION_STATES = frozenset({
    "candidate_persisted", "prepared", "activated", "promoted", "completed",
})
ENROLLMENT_STATES = frozenset({
    "unconfigured", "request_sent", "pending_operator_approval", "approved", "revoked", "unknown",
})
AUTHORITY_STATUS_STATES = frozenset({
    "pending_operator_approval", "no_binding", "active", "binding_revoked",
    "workspace_missing", "workspace_retired", "blocked", "revoked", "unknown",
})
AUTHORITY_BINDING_STATES = frozenset({"active", "revoked"})
AUTHORITY_WORKSPACE_STATES = frozenset({"active", "missing", "retired"})
AUTHORITY_PRESENCE_STATES = frozenset({"online", "offline", "unknown"})
AUTHORITY_READINESS_STATES = frozenset({"ready", "degraded", "blocked", "unknown"})
AUTHORITY_POLICY_STATES = frozenset({"unobserved", "enabled", "expired_or_disabled", "unavailable", "unknown"})
AUTHORITY_DISPATCH_STATES = frozenset({
    "dispatchable", "binding_revoked", "node_revoked", "workspace_missing", "workspace_retired",
})
MAX_HTTP_RESPONSE_BYTES = 256 * 1024
POLICY_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$")
WORKSPACE_REGISTRY_SCHEMA_VERSION = 1
WORKSPACE_REGISTRY_MAX_BYTES = 64 * 1024
WORKSPACE_REGISTRY_MAX_ENTRIES = 64
WORKSPACE_REGISTRY_PATH_MAX_CHARS = 16 * 1024
WORKSPACE_REPLACEMENT_SCHEMA_VERSION = 1
WORKSPACE_REPLACEMENT_MAX_BYTES = 16 * 1024
WORKSPACE_REPLACEMENT_FILE_NAME = "control-plane-workspace-replacement.json"
WORKSPACE_REPLACEMENT_PHASES = frozenset({
    "planned", "retire_sent", "retired", "register_sent",
})
WORKSPACE_SUMMARY_SCHEMA_VERSION = 1
WORKSPACE_SUMMARY_MAX_BYTES = 8 * 1024
WORKSPACE_SUMMARY_TEXT_MAX = 256
WORKSPACE_SUMMARY_ENTRY_TYPES = frozenset({"file", "directory", "symlink", "other"})
WORKSPACE_SUMMARY_PROJECT_TYPES = frozenset({"unknown", "electron", "node", "python", "rust", "go"})
FILE_READ_SENSITIVE_DIRECTORY_NAMES = frozenset({
    ".git", ".ssh", ".aws", ".gnupg", "secret", "secrets", "credential", "credentials",
})
FILE_READ_SENSITIVE_BASENAMES = frozenset({
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credential", "credentials",
})
FILE_READ_SENSITIVE_CONTENT_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\/=:-]{20,}"),
    re.compile(r"(?im)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9._~+\/=:-]{16,}"),
)
PRE_EFFECT_REJECTION_CODES = frozenset({
    "CONTROL_PLANE_BRIDGE_ACTION_DENIED",
    "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
    "CONTROL_PLANE_BRIDGE_POLICY_INVALID",
    "CONTROL_PLANE_BRIDGE_POLICY_EXPIRED",
    "CONTROL_PLANE_BRIDGE_DISABLED",
    "CONTROL_PLANE_BRIDGE_REQUEST_INVALID",
    "CONTROL_PLANE_BRIDGE_REQUEST_EXPIRED",
    "CONTROL_PLANE_BRIDGE_REQUEST_TOO_LARGE",
    "CONTROL_PLANE_BRIDGE_TARGET_MISMATCH",
    "CONTROL_PLANE_BRIDGE_TOOL_DENIED",
    "CONTROL_PLANE_BRIDGE_DEVICE_MISMATCH",
    "CONTROL_PLANE_BRIDGE_RUNTIME_UNREADY",
    "CONTROL_PLANE_BRIDGE_IDENTITY_UNPROVEN",
    "CONTROL_PLANE_BRIDGE_UNAVAILABLE",
    "RECOVERY_HOST_INSTALLATION_MISMATCH",
    "MCP_AUTH_UNAVAILABLE",
    "CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE",
    "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT",
    "CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED",
})
FILE_READ_PRE_EFFECT_REJECTION_CODES = frozenset({
    "CONTROL_PLANE_FILE_READ_ACTION_DENIED",
    "CONTROL_PLANE_FILE_READ_POLICY_MISSING",
    "CONTROL_PLANE_FILE_READ_POLICY_INVALID",
    "CONTROL_PLANE_FILE_READ_POLICY_EXPIRED",
    "CONTROL_PLANE_FILE_READ_DISABLED",
    "CONTROL_PLANE_FILE_READ_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_FILE_READ_REQUEST_INVALID",
    "CONTROL_PLANE_FILE_READ_REQUEST_EXPIRED",
    "CONTROL_PLANE_FILE_READ_REQUEST_TOO_LARGE",
    "CONTROL_PLANE_FILE_READ_TARGET_MISMATCH",
    "CONTROL_PLANE_FILE_READ_TOOL_DENIED",
    "CONTROL_PLANE_FILE_READ_CONTRACT_MISMATCH",
    "CONTROL_PLANE_FILE_READ_PATH_DENIED",
    "CONTROL_PLANE_FILE_READ_LIMIT_DENIED",
    "CONTROL_PLANE_FILE_READ_SENSITIVE_PATH",
    # The local bridge recognizes sensitive content and intentionally withholds
    # it before any receipt can relay it.  The terminal rejection says only
    # that the content was withheld; it never includes a byte or path.
    "CONTROL_PLANE_FILE_READ_SENSITIVE_CONTENT",
    "CONTROL_PLANE_FILE_READ_DEVICE_MISMATCH",
    "CONTROL_PLANE_FILE_READ_RUNTIME_UNREADY",
    "CONTROL_PLANE_FILE_READ_IDENTITY_UNPROVEN",
    "CONTROL_PLANE_FILE_READ_UNAVAILABLE",
    "CONTROL_PLANE_FILE_READ_ADMISSION_INVALID",
    "CONTROL_PLANE_FILE_READ_WORKSPACE_MISMATCH",
    "CONTROL_PLANE_FILE_READ_WORKSPACE_REGISTRY_REQUIRED",
    "MCP_AUTH_UNAVAILABLE",
    "CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE",
    "RECOVERY_HOST_INSTALLATION_MISMATCH",
})
READ_ONLY_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
    "CONTROL_PLANE_BRIDGE_POLICY_INVALID",
    "CONTROL_PLANE_BRIDGE_POLICY_EXPIRED",
    "CONTROL_PLANE_BRIDGE_DISABLED",
    "CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH",
})
FILE_READ_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_FILE_READ_POLICY_MISSING",
    "CONTROL_PLANE_FILE_READ_POLICY_INVALID",
    "CONTROL_PLANE_FILE_READ_POLICY_EXPIRED",
    "CONTROL_PLANE_FILE_READ_DISABLED",
    "CONTROL_PLANE_FILE_READ_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT",
    "CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED",
})
APPROVED_PATCH_PRE_EFFECT_REJECTION_CODES = frozenset({
    "CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED",
    "CONTROL_PLANE_APPROVED_PATCH_DISABLED",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRY_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_FACADE_CONTRACT_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_REQUEST_EXPIRED",
    "CONTROL_PLANE_APPROVED_PATCH_REQUEST_TOO_LARGE",
    "CONTROL_PLANE_APPROVED_PATCH_TARGET_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_TOOL_DENIED",
    "CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED",
    "CONTROL_PLANE_APPROVED_PATCH_SENSITIVE_PATH",
    "CONTROL_PLANE_APPROVED_PATCH_ENVELOPE_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_TARGET_MISSING",
    "CONTROL_PLANE_APPROVED_PATCH_REPARSE_DENIED",
    "CONTROL_PLANE_APPROVED_PATCH_FILE_TOO_LARGE",
    "CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_TARGET_ENCODING_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_DEVICE_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_RUNTIME_UNREADY",
    "CONTROL_PLANE_APPROVED_PATCH_IDENTITY_UNPROVEN",
    "CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE",
    "CONTROL_PLANE_APPROVED_PATCH_ADMISSION_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_MISMATCH",
    "CONTROL_PLANE_APPROVED_PATCH_WORKSPACE_REGISTRY_REQUIRED",
    "MCP_AUTH_UNAVAILABLE",
    "CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE",
    "RECOVERY_HOST_INSTALLATION_MISMATCH",
})
APPROVED_PATCH_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED",
    "CONTROL_PLANE_APPROVED_PATCH_DISABLED",
    "CONTROL_PLANE_APPROVED_PATCH_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT",
    "CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED",
})
DOCUMENT_WRITE_PRE_EFFECT_REJECTION_CODES = frozenset({
    "CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_MISSING",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_EXPIRED",
    "CONTROL_PLANE_DOCUMENT_WRITE_DISABLED",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_EXPIRY_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_FACADE_CONTRACT_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_EXPIRED",
    "CONTROL_PLANE_DOCUMENT_WRITE_TARGET_MISMATCH",
    "CONTROL_PLANE_DOCUMENT_WRITE_TOOL_DENIED",
    "CONTROL_PLANE_DOCUMENT_WRITE_CONTRACT_MISMATCH",
    "CONTROL_PLANE_DOCUMENT_WRITE_PATH_DENIED",
    "CONTROL_PLANE_DOCUMENT_WRITE_SENSITIVE_PATH",
    "CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_TARGET_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_REPARSE_DENIED",
    "CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_MISSING",
    "CONTROL_PLANE_DOCUMENT_WRITE_DEVICE_MISMATCH",
    "CONTROL_PLANE_DOCUMENT_WRITE_RUNTIME_UNREADY",
    "CONTROL_PLANE_DOCUMENT_WRITE_IDENTITY_UNPROVEN",
    "CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE",
    "CONTROL_PLANE_DOCUMENT_WRITE_ADMISSION_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_MISMATCH",
    "CONTROL_PLANE_DOCUMENT_WRITE_WORKSPACE_REGISTRY_REQUIRED",
    "MCP_AUTH_UNAVAILABLE",
    "CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE",
    "RECOVERY_HOST_INSTALLATION_MISMATCH",
})
DOCUMENT_WRITE_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_MISSING",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_INVALID",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_EXPIRED",
    "CONTROL_PLANE_DOCUMENT_WRITE_DISABLED",
    "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT",
    "CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED",
})


def _request(url: str, path: str, payload: dict[str, Any], authorization: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(f"{url.rstrip('/')}{path}", data=json.dumps(payload, separators=(",", ":")).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw_response = response.read(MAX_HTTP_RESPONSE_BYTES + 1)
            if len(raw_response) > MAX_HTTP_RESPONSE_BYTES:
                raise RuntimeError("CONTROL_PLANE_RESPONSE_TOO_LARGE")
            parsed = json.loads(raw_response.decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = {}
        raise RuntimeError(str(detail.get("error", {}).get("code") or f"HTTP_{error.code}")) from error
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        # A receipt may already be durable locally, and the central service may
        # even have accepted it before this transport failure reached us.  Keep
        # the error typed so the caller leaves the journal intact for an exact
        # receipt replay; never turn it into permission to repeat a local
        # bridge call.
        raise RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("invalid_server_response")
    return parsed


def _enrollment_server_origin(value: Any) -> str:
    """Accept one credential-free central HTTPS origin for node enrollment.

    A node enrollment does not need a path, query, URL credentials or an
    arbitrary transport downgrade.  HTTP is retained only for an explicit
    loopback fixture so source tests and an isolated local developer service
    stay possible; a real Tailnet/server enrollment must use HTTPS.
    """

    text = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(text)
        port = parsed.port
    except (TypeError, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_SERVER_URL_INVALID") from error
    hostname = str(parsed.hostname or "").strip().lower()
    if (
        parsed.scheme not in {"https", "http"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("CONTROL_PLANE_SERVER_URL_INVALID")
    if parsed.scheme == "http" and hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise RuntimeError("CONTROL_PLANE_SERVER_HTTPS_REQUIRED")
    host = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and not ((parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80)):
        host = f"{host}:{port}"
    return f"{parsed.scheme}://{host}"


def _dpapi_crypt(data: bytes, *, protect: bool) -> bytes:
    """Protect/unprotect bytes with the current Windows user's DPAPI key.

    The node agent can run under the packaged same-user Supervisor without an
    Electron process, so this boundary cannot depend on Electron safeStorage.
    DPAPI is intentionally loaded lazily: non-Windows source tests keep the
    legacy config path, while a packaged Windows node fails closed if DPAPI is
    unavailable rather than writing a plaintext fallback.
    """

    if os.name != "nt":
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE")
    if not isinstance(data, bytes) or not data or len(data) > NODE_SECRET_MAX_BYTES:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_INVALID")
    try:
        import ctypes
        from ctypes import wintypes

        class _DataBlob(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        function_name = "CryptProtectData" if protect else "CryptUnprotectData"
        function = getattr(crypt32, function_name)
        function.restype = wintypes.BOOL
        function.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]

        source_buffer = ctypes.create_string_buffer(data)
        entropy_buffer = ctypes.create_string_buffer(NODE_SECRET_ENTROPY)
        source_blob = _DataBlob(
            len(data),
            ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)),
        )
        entropy_blob = _DataBlob(
            len(NODE_SECRET_ENTROPY),
            ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_ubyte)),
        )
        output_blob = _DataBlob()
        description = ctypes.c_void_p()
        if protect:
            ok = function(
                ctypes.byref(source_blob),
                ctypes.c_wchar_p("Tools-Codex-web node credential"),
                ctypes.byref(entropy_blob),
                None,
                None,
                0,
                ctypes.byref(output_blob),
            )
        else:
            ok = function(
                ctypes.byref(source_blob),
                ctypes.byref(description),
                ctypes.byref(entropy_blob),
                None,
                None,
                0,
                ctypes.byref(output_blob),
            )
        if not ok or not output_blob.pbData or not output_blob.cbData:
            error_code = ctypes.get_last_error()
            raise RuntimeError(
                "CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE"
                if error_code
                else "CONTROL_PLANE_NODE_SECRET_INVALID"
            )
        try:
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)
        finally:
            kernel32.LocalFree(output_blob.pbData)
            if description.value:
                kernel32.LocalFree(description)
    except RuntimeError:
        raise
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE") from error


def _protect_node_secret(secret: str) -> str:
    value = str(secret or "").strip()
    encoded = value.encode("utf-8")
    if len(encoded) < 16 or len(encoded) > NODE_SECRET_MAX_BYTES:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_INVALID")
    protected = _dpapi_crypt(encoded, protect=True)
    return NODE_SECRET_PROTECTED_PREFIX + base64.b64encode(protected).decode("ascii")


def _unprotect_node_secret(value: Any) -> str:
    encoded_value = str(value or "")
    if not encoded_value.startswith(NODE_SECRET_PROTECTED_PREFIX):
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTED_VALUE_INVALID")
    try:
        protected = base64.b64decode(
            encoded_value[len(NODE_SECRET_PROTECTED_PREFIX):],
            validate=True,
        )
    except (ValueError, base64.binascii.Error) as error:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTED_VALUE_INVALID") from error
    if not protected or len(protected) > NODE_SECRET_MAX_BYTES * 2:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTED_VALUE_INVALID")
    secret_bytes = _dpapi_crypt(protected, protect=False)
    try:
        secret = secret_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTED_VALUE_INVALID") from error
    if len(secret.encode("utf-8")) < 16 or len(secret.encode("utf-8")) > NODE_SECRET_MAX_BYTES:
        raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTED_VALUE_INVALID")
    return secret


def _harden_windows_private_file(path: Path) -> None:
    """Remove inherited Windows ACLs and retain only the node owner/system.

    ``chmod(0600)`` has no security meaning on NTFS.  The node config carries
    a DPAPI envelope, but an account that can edit the surrounding JSON can
    still redirect the authenticated node or suppress its runtime.  Harden the
    temporary file *before* the atomic rename so an ACL failure never replaces
    a previously valid config.  SIDs are used instead of localized group
    names, and command output is intentionally not returned to the caller.
    """

    if os.name != "nt" or sys.platform != "win32":
        return
    try:
        identity = subprocess.run(
            ["whoami.exe", "/user", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        match = re.search(r"S-\d-(?:\d+-){1,14}\d+", str(identity.stdout or ""))
        if identity.returncode != 0 or match is None:
            raise RuntimeError("CONTROL_PLANE_NODE_CONFIG_ACL_UNAVAILABLE")
        owner_sid = match.group(0)
        result = subprocess.run(
            [
                "icacls.exe",
                str(path),
                "/inheritance:r",
                "/grant:r",
                f"*{owner_sid}:F",
                "*S-1-5-18:F",       # Local System
                "*S-1-5-32-544:F",   # Built-in Administrators
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_NODE_CONFIG_ACL_UNAVAILABLE") from error
    if result.returncode != 0:
        raise RuntimeError("CONTROL_PLANE_NODE_CONFIG_ACL_UNAVAILABLE")


def _config(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("node_config_missing") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("node_config_invalid")
    protected = parsed.get(NODE_SECRET_PROTECTED_FIELD)
    active_migrated = False
    if protected is not None:
        if parsed.get("node_secret") not in (None, ""):
            raise RuntimeError("CONTROL_PLANE_NODE_SECRET_AMBIGUOUS")
        parsed["node_secret"] = _unprotect_node_secret(protected)
        # This marker is process-local and is never persisted by _write_config.
        parsed["_node_secret_protected"] = True
    elif os.name == "nt" and parsed.get("node_secret") not in (None, ""):
        # Migrate a legacy plaintext config at the first authenticated read.
        # The old file remains intact if DPAPI or the atomic replacement fails;
        # no plaintext backup is created by the migration path.
        _write_config(path, parsed)
        parsed["_node_secret_protected"] = True
        active_migrated = True
    pending_protected = parsed.get(NODE_SECRET_PENDING_PROTECTED_FIELD)
    if pending_protected is not None:
        if parsed.get(NODE_SECRET_PENDING_FIELD) not in (None, ""):
            raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PENDING_AMBIGUOUS")
        parsed[NODE_SECRET_PENDING_FIELD] = _unprotect_node_secret(pending_protected)
        parsed["_node_secret_pending_protected"] = True
    elif os.name == "nt" and parsed.get(NODE_SECRET_PENDING_FIELD) not in (None, "") and not active_migrated:
        # A rotation candidate can be present in a legacy config written by an
        # older source build.  Migrate both active and pending credentials in
        # one atomic replacement before any rotation network boundary.
        _write_config(path, parsed)
        parsed["_node_secret_pending_protected"] = True
    elif active_migrated and parsed.get(NODE_SECRET_PENDING_FIELD) not in (None, ""):
        # The active migration above persisted both values atomically.
        parsed["_node_secret_pending_protected"] = True
    return parsed


def _write_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    persisted = dict(config)
    secret = persisted.pop("node_secret", None)
    pending_secret = persisted.pop(NODE_SECRET_PENDING_FIELD, None)
    # A pending value is always materialized in memory by _config().  Remove
    # any stale protected copy when the rotation reaches ``completed`` rather
    # than accidentally retaining a second credential forever.
    persisted.pop(NODE_SECRET_PENDING_PROTECTED_FIELD, None)
    persisted.pop("_node_secret_protected", None)
    persisted.pop("_node_secret_pending_protected", None)
    if os.name == "nt":
        if secret not in (None, ""):
            persisted[NODE_SECRET_PROTECTED_FIELD] = _protect_node_secret(str(secret))
        elif not persisted.get(NODE_SECRET_PROTECTED_FIELD):
            raise RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE")
        if pending_secret not in (None, ""):
            persisted[NODE_SECRET_PENDING_PROTECTED_FIELD] = _protect_node_secret(str(pending_secret))
    elif secret is not None:
        # Linux/macOS source fixtures retain the legacy shape.  Packaged
        # Windows never reaches this branch; it must use DPAPI above.
        persisted["node_secret"] = secret
        if pending_secret is not None:
            persisted[NODE_SECRET_PENDING_FIELD] = pending_secret
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    descriptor = None
    try:
        descriptor = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        payload = (json.dumps(persisted, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _harden_windows_private_file(temporary)
        os.replace(temporary, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    """Persist local bridge/policy state with the same Windows ACL boundary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _harden_windows_private_file(temporary)
        os.replace(temporary, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _credential_hash(secret: str) -> str:
    return hashlib.sha256(json.dumps({"node_secret": secret}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _enrollment_id(value: Any, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    candidate = str(value or "").strip()
    if ENROLLMENT_ID_PATTERN.fullmatch(candidate) is None:
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    return candidate


def _enrollment_state(value: Any) -> str:
    state = str(value or "").strip().lower()
    if state not in ENROLLMENT_STATES:
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    return state


def _enrollment_request_projection(response: Any, *, config: dict[str, Any]) -> dict[str, Any]:
    """Validate a credential-free enrollment request response.

    The central request endpoint intentionally returns the same durable row on
    retries.  A missing ``approved_at_ms`` is treated as pending so older
    central fixtures remain compatible, while an explicit approval is persisted
    as soon as the node observes it.
    """

    if not isinstance(response, dict):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_RESPONSE_INVALID")
    enrollment_id = _enrollment_id(response.get("enrollment_id"))
    if response.get("device_id") is not None and str(response.get("device_id") or "") != str(config.get("device_id") or ""):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_TARGET_MISMATCH")
    approved_at_ms = response.get("approved_at_ms")
    if approved_at_ms is not None and (not isinstance(approved_at_ms, int) or isinstance(approved_at_ms, bool) or approved_at_ms <= 0):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_RESPONSE_INVALID")
    return {
        "enrollment_id": enrollment_id,
        "device_id": str(config["device_id"]),
        "state": "approved" if approved_at_ms is not None else "pending_operator_approval",
        "approved_at_ms": approved_at_ms,
    }


def _enrollment_status_projection(response: Any, *, config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "enrollment_id", "device_id", "state", "credential_generation",
        "requested_at_ms", "approved_at_ms", "observed_at_ms",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    enrollment_id = _enrollment_id(response.get("enrollment_id"), allow_none=True)
    if str(response.get("device_id") or "") != str(config.get("device_id") or ""):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_TARGET_MISMATCH")
    state = str(response.get("state") or "").strip().lower()
    if state not in {"pending_operator_approval", "approved", "revoked"}:
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    generation = response.get("credential_generation")
    if generation is not None and (not isinstance(generation, int) or isinstance(generation, bool) or generation < 1):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    for name in ("requested_at_ms", "approved_at_ms", "observed_at_ms"):
        value = response.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
            raise RuntimeError("CONTROL_PLANE_ENROLLMENT_STATUS_INVALID")
    return {
        "enrollment_id": enrollment_id,
        "device_id": str(config["device_id"]),
        "state": state,
        "credential_generation": generation,
        "requested_at_ms": response.get("requested_at_ms"),
        "approved_at_ms": response.get("approved_at_ms"),
        "observed_at_ms": response["observed_at_ms"],
    }


def _persist_enrollment_projection(config_path: Path, config: dict[str, Any], projection: dict[str, Any], *, last_error: str | None = None) -> dict[str, Any]:
    updated = dict(config)
    if projection.get("enrollment_id") is not None:
        updated["enrollment_id"] = projection["enrollment_id"]
    updated["enrollment_state"] = projection["state"]
    updated["enrollment_observed_at_ms"] = projection.get("observed_at_ms") or int(time.time() * 1000)
    if projection.get("credential_generation") is not None:
        updated["credential_generation"] = projection["credential_generation"]
    updated["enrollment_last_error"] = last_error
    _write_config(config_path, updated)
    return updated


def _enrollment_local_status(config: dict[str, Any], *, fresh: bool, error_code: str | None = None) -> dict[str, Any]:
    state = str(config.get("enrollment_state") or "unconfigured").strip().lower()
    if state not in ENROLLMENT_STATES:
        state = "unknown"
    # The HTTPS origin is safe, non-secret resume metadata.  Returning it from
    # the node-agent status projection lets the desktop restore an existing
    # enrollment after the ordinary settings field was lost, without exposing
    # the node credential or any operator/account material.
    try:
        server_origin = _enrollment_server_origin(config.get("server_url"))
    except RuntimeError:
        server_origin = None
    return {
        "device_id": str(config.get("device_id") or ""),
        "enrollment_id": _enrollment_id(config.get("enrollment_id"), allow_none=True) if config.get("enrollment_id") else None,
        "state": state,
        "credential_generation": config.get("credential_generation"),
        "fresh": bool(fresh),
        "observed_at_ms": config.get("enrollment_observed_at_ms"),
        "error_code": error_code or config.get("enrollment_last_error"),
        "server_origin": server_origin,
    }


def _authority_status_projection(response: Any, *, config: dict[str, Any]) -> dict[str, Any]:
    """Validate the credential-free node authority projection.

    The exact-key checks are intentional: a future server change must not
    accidentally make an owner/OAuth identifier or local path visible in the
    Windows settings surface.
    """

    expected = {
        "device_id", "state", "node_display_name", "workspace_count", "target_count",
        "dispatchable_target_count", "targets", "observed_at_ms",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    device_id = str(response.get("device_id") or "").strip().lower()
    if device_id != str(config.get("device_id") or "").strip().lower():
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_TARGET_MISMATCH")
    state = str(response.get("state") or "").strip().lower()
    if state not in AUTHORITY_STATUS_STATES - {"unknown"}:
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    for field in ("workspace_count", "target_count", "dispatchable_target_count"):
        value = response.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    observed_at_ms = response.get("observed_at_ms")
    if not isinstance(observed_at_ms, int) or isinstance(observed_at_ms, bool) or observed_at_ms <= 0:
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    display_name = response.get("node_display_name")
    if display_name is not None and (
        not isinstance(display_name, str) or not 1 <= len(display_name) <= 120
        or any(ord(character) < 32 for character in display_name)
    ):
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    targets = response.get("targets")
    if not isinstance(targets, list) or len(targets) > 64 or len(targets) != response["target_count"]:
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    normalized_targets: list[dict[str, Any]] = []
    for target in targets:
        target_legacy_expected = {
            "node_display_name", "workspace_display_name", "capabilities", "binding_state",
            "workspace_state", "presence_state", "readiness", "policy_state",
            "dispatch_state", "dispatch_blockers",
        }
        target_enriched_expected = target_legacy_expected | {"workspace_id", "workspace_generation"}
        target_keys = set(target) if isinstance(target, dict) else None
        if target_keys not in (target_legacy_expected, target_enriched_expected):
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
        target_node = target.get("node_display_name")
        enriched_identity = target_keys == target_enriched_expected
        target_workspace_id = str(target.get("workspace_id") or "").strip().lower() if enriched_identity else None
        target_workspace_generation = str(target.get("workspace_generation") or "").strip().lower() if enriched_identity else None
        target_workspace = target.get("workspace_display_name")
        if (
            not isinstance(target_node, str) or not 1 <= len(target_node) <= 120
            or (enriched_identity and (POLICY_IDENTIFIER_PATTERN.fullmatch(target_workspace_id or "") is None
                                       or POLICY_IDENTIFIER_PATTERN.fullmatch(target_workspace_generation or "") is None))
            or not isinstance(target_workspace, str) or not 1 <= len(target_workspace) <= 120
            or any(ord(character) < 32 for character in target_node + target_workspace)
        ):
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
        capabilities = target.get("capabilities")
        if (
            not isinstance(capabilities, dict)
            or set(capabilities) != {"read", "write", "exec"}
            or any(not isinstance(capabilities[name], bool) for name in ("read", "write", "exec"))
        ):
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
        states = (
            ("binding_state", AUTHORITY_BINDING_STATES),
            ("workspace_state", AUTHORITY_WORKSPACE_STATES),
            ("presence_state", AUTHORITY_PRESENCE_STATES),
            ("readiness", AUTHORITY_READINESS_STATES),
            ("policy_state", AUTHORITY_POLICY_STATES),
            ("dispatch_state", AUTHORITY_DISPATCH_STATES),
        )
        for field, allowed in states:
            if str(target.get(field) or "").strip().lower() not in allowed:
                raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
        blockers = target.get("dispatch_blockers")
        if (
            not isinstance(blockers, list)
            or any(not isinstance(item, str) or item not in AUTHORITY_DISPATCH_STATES for item in blockers)
            or len(blockers) != len(set(blockers))
        ):
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
        normalized_target = {
            "node_display_name": target_node,
            "workspace_display_name": target_workspace,
            "capabilities": {name: capabilities[name] for name in ("read", "write", "exec")},
            "binding_state": str(target["binding_state"]).lower(),
            "workspace_state": str(target["workspace_state"]).lower(),
            "presence_state": str(target["presence_state"]).lower(),
            "readiness": str(target["readiness"]).lower(),
            "policy_state": str(target["policy_state"]).lower(),
            "dispatch_state": str(target["dispatch_state"]).lower(),
            "dispatch_blockers": list(blockers),
        }
        if enriched_identity:
            normalized_target["workspace_id"] = target_workspace_id
            normalized_target["workspace_generation"] = target_workspace_generation
        normalized_targets.append(normalized_target)
    if response["dispatchable_target_count"] != sum(
        1 for target in normalized_targets if target["dispatch_state"] == "dispatchable"
    ):
        raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_INVALID")
    return {
        "device_id": device_id,
        "state": state,
        "node_display_name": display_name,
        "workspace_count": response["workspace_count"],
        "target_count": response["target_count"],
        "dispatchable_target_count": response["dispatchable_target_count"],
        "targets": normalized_targets,
        "observed_at_ms": observed_at_ms,
    }


def _authority_local_status(config: dict[str, Any], *, fresh: bool, error_code: str | None = None) -> dict[str, Any]:
    return {
        "device_id": str(config.get("device_id") or "").strip().lower(),
        "state": "unknown",
        "node_display_name": None,
        "workspace_count": 0,
        "target_count": 0,
        "dispatchable_target_count": 0,
        "targets": [],
        "fresh": bool(fresh),
        "observed_at_ms": None,
        "error_code": error_code,
    }


def _credential_rotation_id(value: Any) -> str:
    rotation_id = str(value or "").strip().lower()
    if NODE_ROTATION_ID_PATTERN.fullmatch(rotation_id) is None:
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_ID_INVALID")
    return rotation_id


def _credential_rotation_projection(response: Any, *, config: dict[str, Any], allowed_states: set[str] | frozenset[str]) -> dict[str, Any]:
    expected = {
        "rotation_id", "device_id", "state", "current_generation", "next_generation",
        "created_at_ms", "activated_at_ms", "completed_at_ms",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_RESPONSE_INVALID")
    rotation_id = _credential_rotation_id(response.get("rotation_id"))
    if rotation_id != str(config.get("credential_rotation_id") or ""):
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_TARGET_MISMATCH")
    if str(response.get("device_id") or "") != str(config.get("device_id") or ""):
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_TARGET_MISMATCH")
    state = str(response.get("state") or "").strip().lower()
    if state not in allowed_states:
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_STATE_INVALID")
    current_generation = response.get("current_generation")
    next_generation = response.get("next_generation")
    if (
        not isinstance(current_generation, int) or isinstance(current_generation, bool) or current_generation < 1
        or not isinstance(next_generation, int) or isinstance(next_generation, bool)
        or next_generation != current_generation + 1
    ):
        raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_GENERATION_INVALID")
    for name in ("created_at_ms", "activated_at_ms", "completed_at_ms"):
        value = response.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
            raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_RESPONSE_INVALID")
    return {
        "rotation_id": rotation_id,
        "device_id": str(config["device_id"]),
        "state": state,
        "current_generation": current_generation,
        "next_generation": next_generation,
        "created_at_ms": response["created_at_ms"],
        "activated_at_ms": response["activated_at_ms"],
        "completed_at_ms": response["completed_at_ms"],
    }


def _credential_rotation_local_status(config: dict[str, Any], *, fresh: bool, error_code: str | None = None) -> dict[str, Any]:
    state = str(config.get("credential_rotation_state") or "idle").strip().lower()
    if state not in NODE_ROTATION_STATES and state != "idle":
        state = "unknown"
    return {
        "device_id": str(config.get("device_id") or ""),
        "rotation_id": _credential_rotation_id(config.get("credential_rotation_id"))
        if config.get("credential_rotation_id") else None,
        "state": state,
        "current_generation": config.get("credential_generation"),
        "next_generation": config.get("credential_rotation_next_generation"),
        "fresh": bool(fresh),
        "error_code": error_code or config.get("credential_rotation_last_error"),
    }


def rotate_node_credential(args: argparse.Namespace) -> int:
    """Rotate a node credential with durable prepare/activate/ack phases.

    The active credential is kept until the central ``activate`` commit is
    observed.  After that commit both old and candidate credentials are valid;
    the node persists the candidate before sending ``ack``.  A lost response or
    process crash therefore resumes with whichever credential the central
    state can still authenticate, without putting a raw secret in SQLite or
    stdout.
    """

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    try:
        server_url = _enrollment_server_origin(config.get("server_url"))
        device_id = str(config.get("device_id") or "").strip()
        node_secret = str(config.get("node_secret") or "")
        generation = config.get("credential_generation")
        if (
            POLICY_IDENTIFIER_PATTERN.fullmatch(device_id) is None
            or len(node_secret) < 16
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
        ):
            raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_CONFIG_INVALID")
        state = str(config.get("credential_rotation_state") or "idle").strip().lower()
        if state == "idle" or state == "completed":
            rotation_id = f"rotate_{secrets.token_hex(16)}"
            pending = secrets.token_urlsafe(32)
            next_generation = generation + 1
            config.update({
                "credential_rotation_id": rotation_id,
                "credential_rotation_state": "candidate_persisted",
                "credential_rotation_next_generation": next_generation,
                "credential_rotation_last_error": None,
                NODE_SECRET_PENDING_FIELD: pending,
            })
            _write_config(config_path, config)
            state = "candidate_persisted"
        elif state not in NODE_ROTATION_STATES:
            raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_STATE_INVALID")
        rotation_id = _credential_rotation_id(config.get("credential_rotation_id"))
        pending = str(config.get(NODE_SECRET_PENDING_FIELD) or "")
        if len(pending) < 16:
            raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_PENDING_SECRET_INVALID")
        current_generation = config.get("credential_generation")
        next_generation = config.get("credential_rotation_next_generation")
        if (
            not isinstance(current_generation, int) or isinstance(current_generation, bool) or current_generation < 1
            or not isinstance(next_generation, int) or isinstance(next_generation, bool)
            or next_generation != current_generation + 1
        ):
            raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_GENERATION_INVALID")

        if state == "candidate_persisted":
            prepared = _request(
                server_url,
                f"/v1/nodes/{device_id}/credential-rotation/prepare",
                {
                    "rotation_id": rotation_id,
                    "current_generation": current_generation,
                    "next_credential_hash": _credential_hash(pending),
                },
                f"Node {node_secret}",
            )
            projection = _credential_rotation_projection(
                prepared,
                config=config,
                allowed_states={"prepared", "activated", "completed"},
            )
            if projection["current_generation"] != current_generation or projection["next_generation"] != next_generation:
                raise RuntimeError("CONTROL_PLANE_CREDENTIAL_ROTATION_GENERATION_INVALID")
            config["credential_rotation_state"] = projection["state"]
            config["credential_rotation_last_error"] = None
            _write_config(config_path, config)
            state = projection["state"]

        if state == "prepared":
            activated = _request(
                server_url,
                f"/v1/nodes/{device_id}/credential-rotation/activate",
                {"rotation_id": rotation_id},
                f"Node {node_secret}",
            )
            projection = _credential_rotation_projection(
                activated,
                config=config,
                allowed_states={"activated", "completed"},
            )
            config["credential_rotation_state"] = projection["state"]
            config["credential_rotation_last_error"] = None
            _write_config(config_path, config)
            state = projection["state"]

        if state == "activated":
            # This write is the local handoff boundary.  The old credential is
            # still accepted centrally until the following acknowledgement.
            config["node_secret"] = pending
            config["credential_rotation_state"] = "promoted"
            config["credential_rotation_last_error"] = None
            _write_config(config_path, config)
            state = "promoted"

        if state == "promoted":
            new_secret = str(config.get("node_secret") or "")
            acknowledged = _request(
                server_url,
                f"/v1/nodes/{device_id}/credential-rotation/ack",
                {"rotation_id": rotation_id},
                f"Node {new_secret}",
            )
            projection = _credential_rotation_projection(
                acknowledged,
                config=config,
                allowed_states={"completed"},
            )
            config["credential_generation"] = projection["next_generation"]
            config["credential_rotation_state"] = "completed"
            config["credential_rotation_next_generation"] = projection["next_generation"]
            config["credential_rotation_last_id"] = rotation_id
            config["credential_rotation_last_error"] = None
            config.pop(NODE_SECRET_PENDING_FIELD, None)
            _write_config(config_path, config)
            state = "completed"
        print(json.dumps(_credential_rotation_local_status(config, fresh=True), separators=(",", ":")))
        return 0
    except RuntimeError as error:
        code = _safe_error_code(str(error), "CONTROL_PLANE_CREDENTIAL_ROTATION_FAILED")
        try:
            config["credential_rotation_last_error"] = code
            _write_config(config_path, config)
        except RuntimeError:
            # Preserve the original failure classification; a failed local
            # persistence attempt must not print credential material.
            pass
        print(json.dumps(_credential_rotation_local_status(config, fresh=False, error_code=code), separators=(",", ":")))
        return 0


def parse_dev_ui_status(output: str) -> dict[str, str]:
    """Extract the machine-readable fields emitted by dev-ui-lifecycle status.

    The parser intentionally accepts only the dedicated status line.  It never
    turns an unrecognised command result into a ready node.
    """
    line = next((value for value in reversed(output.splitlines()) if value.startswith("DEV_UI STATUS ")), "")
    if not line:
        raise RuntimeError("runtime_status_unavailable")
    values: dict[str, str] = {}
    for item in line.removeprefix("DEV_UI STATUS ").split():
        key, separator, value = item.partition("=")
        if not separator or not key or not value:
            continue
        values[key] = value
    if not values:
        raise RuntimeError("runtime_status_invalid")
    return values


def runtime_readiness(status: dict[str, str]) -> tuple[str, str]:
    """Map the Hub's status to a conservative central-node readiness state.

    A central node must not advertise ``ready`` from UI liveness or a compatible
    connector acknowledgement. The bridge needs current MCP source identity and
    an attested current-process rediscovery before even a future read-only
    action may be admitted.
    """
    if status.get("adapter_mode") == "packaged":
        if status.get("strict_ready") == "true":
            return "ready", "strict_packaged_recovery_observation"
        if status.get("strict_ready") == "false":
            return "degraded", "packaged_runtime_unready"
        return "unknown", "packaged_runtime_observation_invalid"
    if status.get("state") == "MISSING" or status.get("host") != "available":
        return "blocked", "runtime_unavailable"
    if status.get("state") != "CURRENT" or status.get("installation") != "current":
        return "degraded", "runtime_identity_unproven"
    if status.get("runtime_telemetry_available") != "true" or status.get("runtime_signal_stale") != "false":
        return "degraded", "runtime_telemetry_unproven"
    if (
        status.get("mcp_update_pending") != "false"
        or status.get("runtime_update_incomplete") != "false"
        or not status.get("mcp_running_revision")
        or status.get("mcp_running_revision") == "none"
        or status.get("mcp_running_revision") != status.get("mcp_disk_revision")
    ):
        return "degraded", "mcp_revision_unproven"
    if status.get("components_ready") != "true" or status.get("fully_ready") != "true":
        return "degraded", "runtime_admission_pending"
    if status.get("error_code") not in {None, "none"}:
        return "degraded", "runtime_error_present"
    if (
        status.get("connector_state") == "CURRENT_ACKNOWLEDGED"
        and status.get("connector_rediscovered") == "true"
        and status.get("connector_rediscovered_at") not in {None, "", "none"}
        and status.get("connector_freshness_mode") == "current_process_discovery"
        and status.get("connector_refresh_required") == "false"
        and status.get("connector_ack_pending") == "false"
        and status.get("connector_current_sha") not in {None, "", "none"}
        and status.get("connector_current_sha") == status.get("connector_ack_sha")
    ):
        return "ready", "strict_current_process_discovery"
    if status.get("runtime_telemetry_available") == "true" or status.get("state") == "CURRENT":
        return "degraded", "strict_connector_rediscovery_required"
    return "unknown", "status_not_actionable"


def _observed_identity(value: Any) -> str | None:
    """Accept compact runtime IDs only; never truncate a claimed identity."""
    value = str(value or "").strip()
    return value if 0 < len(value) <= 128 else None


def observed_runtime_identity(observation: Any) -> dict[str, str] | None:
    """Return an exact, supported Recovery IPC observation or ``None``.

    The Python node agent deliberately treats an unparseable, stale, malformed,
    or merely compatible observation as absent.  It must not reconstruct an
    MCP identity from the Electron/UI lifecycle status.
    """
    if not isinstance(observation, dict):
        return None
    process_instance_id = _observed_identity(observation.get("mcp_process_instance_id"))
    server_instance_id = _observed_identity(observation.get("mcp_server_instance_id"))
    activation_epoch_id = _observed_identity(observation.get("activation_epoch_id"))
    current_epoch_id = _observed_identity(observation.get("current_activation_epoch_id"))
    contract_sha256 = str(observation.get("tool_contract_sha256") or "").strip().lower()
    if (
        int(observation.get("observation_schema_version") or 0) != 1
        or observation.get("observation_kind") != "mcp_identity_read_only"
        or observation.get("mcp_ready") is not True
        or observation.get("identity_current") is not True
        or not process_instance_id
        or not server_instance_id
        or not activation_epoch_id
        or activation_epoch_id != current_epoch_id
        or not SHA256_PATTERN.fullmatch(contract_sha256)
    ):
        return None
    return {
        "runtime_instance_id": process_instance_id,
        "mcp_server_instance_id": server_instance_id,
        "activation_epoch": activation_epoch_id,
        "contract_version": f"sha256:{contract_sha256}",
    }


def runtime_heartbeat_projection(status: dict[str, str], identity_observation: Any = None) -> dict[str, str]:
    """Build one safe heartbeat from strict aggregate plus exact MCP identity.

    ``dev-ui-lifecycle status`` is a useful source-versus-runtime projection,
    but its ``instance`` is Electron UI identity, not the authenticated Coding
    MCP process/server identity.  The sole supported source for that identity
    is the narrow read-only Recovery IPC observation; no fallback may derive it
    from a cached UI lifecycle projection.
    """
    readiness, reason = runtime_readiness(status)
    identity = observed_runtime_identity(identity_observation)
    if readiness == "ready":
        if identity is None:
            readiness, reason = "degraded", "runtime_identity_unproven"
        else:
            return {**identity, "readiness": readiness, "reason": reason}
    return {
        "runtime_instance_id": "unreported",
        "mcp_server_instance_id": "unreported",
        "activation_epoch": "unreported",
        "contract_version": "unreported",
        "readiness": readiness,
        "reason": reason,
    }


def _runtime_mode(args: argparse.Namespace) -> str:
    mode = str(getattr(args, "runtime_mode", "development") or "development").strip().lower()
    if mode not in {"development", "packaged"}:
        raise RuntimeError("runtime_mode_invalid")
    return mode


def _adapter_command(args: argparse.Namespace, script: Path, project_root: Path, *, runtime_status: bool = False) -> tuple[list[str], dict[str, str]]:
    """Build the only supported local adapter invocation.

    Installed mode runs the product Electron executable as Node. The wrapper is
    supplied by the installer, so no global Node.js or source checkout is a
    dependency of the Windows node lane.
    """
    mode = _runtime_mode(args)
    command = [str(args.node), str(script), "--runtime-mode", mode]
    if runtime_status:
        command.append("--runtime-status")
    if mode == "development":
        command.extend(["--project-root", str(project_root)])
    environment = dict(os.environ)
    if mode == "packaged":
        environment["ELECTRON_RUN_AS_NODE"] = "1"
    return command, environment


def _policy_data_root(args: argparse.Namespace) -> Path:
    """Resolve the one profile that Recovery Host will read for this mode.

    Packaged mode intentionally derives the fixed product data root; allowing a
    user-supplied path there could install a convincing policy that the active
    installed Recovery Host never reads. Development mode requires a separately
    named data root so it cannot accidentally alter a packaged profile.
    """

    mode = _runtime_mode(args)
    requested = str(getattr(args, "data_root", "") or "").strip()
    if mode == "packaged":
        if requested:
            raise RuntimeError("CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN")
        appdata = str(os.environ.get("APPDATA", "") or "").strip()
        if not appdata or not Path(appdata).is_absolute():
            raise RuntimeError("CONTROL_PLANE_POLICY_APPDATA_UNAVAILABLE")
        return Path(appdata).resolve() / "web-mcp-assistant"
    if not requested or not Path(requested).is_absolute():
        raise RuntimeError("CONTROL_PLANE_POLICY_DATA_ROOT_REQUIRED")
    return Path(requested).resolve()


def _read_only_policy_path(args: argparse.Namespace) -> Path:
    return _policy_data_root(args) / READ_ONLY_POLICY_FILE_NAME


def _route_evidence_path(args: argparse.Namespace) -> Path:
    """Use the same product data root as Electron's credential-free reader."""
    return _policy_data_root(args) / ROUTE_EVIDENCE_FILE_NAME


def _policy_identifier(value: Any, field: str) -> str:
    candidate = str(value or "").strip()
    if not POLICY_IDENTIFIER_PATTERN.fullmatch(candidate):
        raise RuntimeError(f"CONTROL_PLANE_POLICY_{field.upper()}_INVALID")
    return candidate


def _policy_facade_contract(schema_version: Any, profile: Any, sha256: Any) -> dict[str, int | str]:
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or not 1 <= schema_version <= 1_000_000:
        raise RuntimeError("CONTROL_PLANE_POLICY_FACADE_CONTRACT_INVALID")
    normalized_sha256 = str(sha256 or "").strip().lower()
    if not SHA256_PATTERN.fullmatch(normalized_sha256):
        raise RuntimeError("CONTROL_PLANE_POLICY_FACADE_CONTRACT_INVALID")
    return {
        "schema_version": schema_version,
        "profile": _policy_identifier(profile, "facade_profile"),
        "sha256": normalized_sha256,
    }


def _policy_digest(policy: dict[str, Any]) -> str:
    # Recovery Host fingerprints the admitted v2 policy projection. ``enabled``
    # is a gate checked before that projection is built, so it is intentionally
    # not part of the cross-language policy SHA. A disabled file therefore has
    # no admitted authority even though its future-enabled contract is stable.
    admitted_projection = {key: value for key, value in policy.items() if key != "enabled"}
    return hashlib.sha256(
        json.dumps(admitted_projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _normalise_read_only_policy(policy: Any, *, now_ms: int | None = None, require_enabled: bool = False) -> dict[str, Any]:
    """Validate the exact v2 policy shape without reading a secret or IPC descriptor."""

    expected_fields = {
        "schema_version", "enabled", "server_origin", "owner_id", "device_id",
        "endpoint_id", "workspace_id", "workspace_generation", "expires_at_ms", "facade_contract",
    }
    if not isinstance(policy, dict) or set(policy) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID")
    if policy.get("schema_version") != READ_ONLY_POLICY_SCHEMA_VERSION or not isinstance(policy.get("enabled"), bool):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID")
    if require_enabled and policy["enabled"] is not True:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_DISABLED")
    expires_at_ms = policy.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID")
    if now_ms is not None and expires_at_ms <= now_ms:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_EXPIRED")
    facade = policy.get("facade_contract")
    if not isinstance(facade, dict) or set(facade) != {"schema_version", "profile", "sha256"}:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID")
    try:
        server_origin = _server_origin(policy.get("server_origin"))
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID") from error
    return {
        "schema_version": READ_ONLY_POLICY_SCHEMA_VERSION,
        "enabled": policy["enabled"],
        "server_origin": server_origin,
        "owner_id": _policy_identifier(policy.get("owner_id"), "owner_id"),
        "device_id": _policy_identifier(policy.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(policy.get("endpoint_id"), "endpoint_id"),
        "workspace_id": _policy_identifier(policy.get("workspace_id"), "workspace_id"),
        "workspace_generation": _policy_identifier(policy.get("workspace_generation"), "workspace_generation"),
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade.get("schema_version"), facade.get("profile"), facade.get("sha256")
        ),
    }


def _read_local_policy(policy_path: Path) -> dict[str, Any]:
    try:
        stat = policy_path.stat()
        if not policy_path.is_file() or stat.st_size > READ_ONLY_POLICY_MAX_BYTES:
            raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID")
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_MISSING") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_INVALID") from error
    return _normalise_read_only_policy(value)


def _standing_policy_observation(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any] | None:
    """Observe the installed standing lanes for central route freshness.

    The compact legacy policy is a short-lived read-only pilot artifact.  A
    trusted workspace may instead have only the independent standing
    file-read, approved-patch or exec policies.  Heartbeat must therefore
    reflect that standing authority without treating a policy file as an
    action grant.  ``expires_at_ms`` in this projection is deliberately the
    freshness bound of this observation, not the standing policy's lifetime.

    ``None`` means no standing policy file exists and lets the legacy pilot
    observation remain a compatibility fallback.  Once a standing file is
    present, malformed, mismatched or stale local state is fail-closed.
    """

    candidates = (
        ("file_read", _file_read_policy_path, _read_file_read_policy),
        ("approved_patch", _approved_patch_policy_path, _read_approved_patch_policy),
        ("exec", _exec_policy_path, _read_exec_policy),
    )
    saw_candidate = False
    admitted: list[dict[str, str]] = []
    for lane, path_factory, reader in candidates:
        try:
            policy_path = path_factory(args)
            if not policy_path.exists():
                continue
            saw_candidate = True
            policy = reader(policy_path)
            if (
                policy.get("enabled") is not True
                or policy.get("authority_mode") != "standing"
                or policy.get("expires_at_ms") is not None
                or policy.get("server_origin") != _server_origin(config.get("server_url"))
                or policy.get("device_id") != config.get("device_id")
                or policy.get("endpoint_id") != config.get("endpoint_id")
            ):
                continue
            if hasattr(args, "workspace_registry"):
                if not str(getattr(args, "workspace_registry", "") or "").strip():
                    raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED")
                config_path = Path(args.config).expanduser().resolve()
                _require_current_local_workspace_registration(
                    args,
                    config_path=config_path,
                    workspace_id=policy["workspace_id"],
                    workspace_generation=policy["workspace_generation"],
                )
            elif _runtime_mode(args) == "packaged":
                # The installed Supervisor always supplies the sibling
                # registry.  A packaged caller without it cannot prove the
                # policy still targets a current local root.
                raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED")
            admitted.append({
                "lane": lane,
                "policy_sha256": _policy_digest(policy),
                "workspace_id": policy["workspace_id"],
                "workspace_generation": policy["workspace_generation"],
            })
        except (OSError, RuntimeError, ValueError):
            # Keep the observation credential-free and avoid allowing one
            # malformed lane to make another lane look broader than it is.
            continue

    if not saw_candidate:
        return None
    now_ms = int(time.time() * 1000)
    if not admitted:
        return {
            "state": "unavailable",
            "expires_at_ms": None,
            "policy_sha256": None,
            "reason": "CONTROL_PLANE_STANDING_POLICY_UNAVAILABLE",
        }
    digest_input = json.dumps(sorted(admitted, key=lambda item: item["lane"]), separators=(",", ":"), sort_keys=True)
    return {
        "state": "enabled",
        "expires_at_ms": now_ms + STANDING_POLICY_OBSERVATION_TTL_MS,
        "policy_sha256": hashlib.sha256(digest_input.encode("utf-8")).hexdigest(),
        "reason": "",
    }


def _file_read_policy_path(args: argparse.Namespace) -> Path:
    """Return the independently installed C3 file-content policy path.

    This must never alias the compact workspace-metadata policy.  A node that
    has metadata authority but no file-read file remains unable to return even
    one byte of a workspace file.
    """

    return _policy_data_root(args) / FILE_READ_POLICY_FILE_NAME


def _file_read_relative_path(value: Any, *, code: str) -> str:
    """Mirror the C3 bridge's strict relative-POSIX path boundary.

    The Central service, Python node agent and Electron bridge all validate
    this independently.  Keeping the policy parser stricter than a general
    local file resolver prevents a later local MCP change from widening this
    remote content lane.
    """

    if not isinstance(value, str):
        raise RuntimeError(code)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise RuntimeError(code) from error
    if (
        not encoded
        or len(encoded) > 512
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise RuntimeError(code)
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise RuntimeError(code)
    lowered = [part.lower() for part in parts]
    basename = lowered[-1]
    if (
        any(part in FILE_READ_SENSITIVE_DIRECTORY_NAMES or part.startswith(".env") for part in lowered)
        or basename in FILE_READ_SENSITIVE_BASENAMES
        or basename.endswith((".pem", ".key", ".p12", ".pfx"))
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_SENSITIVE_PATH")
    return value


def _file_read_policy_allowed_paths(value: Any) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= FILE_READ_MAX_ALLOWED_PATHS:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    allowed = [
        _file_read_relative_path(item, code="CONTROL_PLANE_FILE_READ_POLICY_INVALID")
        for item in value
    ]
    if len(allowed) != len(set(allowed)):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    # JavaScript normalises the same policy list in lexical order before it
    # computes the cross-boundary SHA.  Persist the same order here.
    return sorted(allowed)


def _file_read_policy_allowed_prefixes(value: Any) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= FILE_READ_MAX_ALLOWED_PATHS:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    allowed = [
        "." if item == "." else _file_read_relative_path(item, code="CONTROL_PLANE_FILE_READ_POLICY_INVALID")
        for item in value
    ]
    if len(allowed) != len(set(allowed)) or ("." in allowed and len(allowed) != 1):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    return sorted(allowed)


def _policy_path_is_allowed(policy: dict[str, Any], path: str) -> bool:
    """The request is always one validated file; only policy scope can be broad."""

    if "allowed_relative_prefixes" in policy:
        return any(prefix == "." or path == prefix or path.startswith(prefix + "/")
                   for prefix in policy["allowed_relative_prefixes"])
    return path in policy["allowed_relative_paths"]


def _file_read_policy_limits(max_bytes: Any, max_lines: Any, *, code: str) -> tuple[int, int]:
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or not isinstance(max_lines, int)
        or isinstance(max_lines, bool)
        or not 1 <= max_bytes <= FILE_READ_MAX_BYTES
        or not 1 <= max_lines <= FILE_READ_MAX_LINES
    ):
        raise RuntimeError(code)
    return max_bytes, max_lines


def _normalise_file_read_policy(
    policy: Any,
    *,
    now_ms: int | None = None,
    require_enabled: bool = False,
) -> dict[str, Any]:
    """Validate the exact C3 local policy without opening Recovery IPC."""

    schema_version = policy.get("schema_version") if isinstance(policy, dict) else None
    prefixes = schema_version == FILE_READ_POLICY_SCHEMA_VERSION
    standing = prefixes or schema_version == FILE_READ_POLICY_EXACT_SCHEMA_VERSION
    legacy = schema_version == FILE_READ_POLICY_LEGACY_SCHEMA_VERSION
    expected_fields = {
        "schema_version", "enabled", "server_origin", "owner_id", "device_id",
        "endpoint_id", "workspace_id", "workspace_generation", "expires_at_ms",
        "facade_contract", "max_bytes", "max_lines",
    }
    expected_fields.add("allowed_relative_prefixes" if prefixes else "allowed_relative_paths")
    if standing:
        expected_fields.add("authority_mode")
    if (
        not isinstance(policy, dict)
        or set(policy) != expected_fields
        or not (standing or legacy)
        or not isinstance(policy.get("enabled"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    if require_enabled and policy["enabled"] is not True:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_DISABLED")
    authority_mode = FILE_READ_POLICY_STANDING_AUTHORITY if standing else "expiring_legacy"
    if standing and policy.get("authority_mode") != FILE_READ_POLICY_STANDING_AUTHORITY:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    expires_at_ms = policy.get("expires_at_ms")
    if standing:
        if expires_at_ms is not None:
            raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    else:
        if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
            raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
        if now_ms is not None and expires_at_ms <= now_ms:
            raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_EXPIRED")
    facade = policy.get("facade_contract")
    if not isinstance(facade, dict) or set(facade) != {"schema_version", "profile", "sha256"}:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    try:
        server_origin = _server_origin(policy.get("server_origin"))
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID") from error
    max_bytes, max_lines = _file_read_policy_limits(
        policy.get("max_bytes"), policy.get("max_lines"), code="CONTROL_PLANE_FILE_READ_POLICY_INVALID"
    )
    result = {
        "schema_version": schema_version,
        "enabled": policy["enabled"],
        "server_origin": server_origin,
        "owner_id": _policy_identifier(policy.get("owner_id"), "owner_id"),
        "device_id": _policy_identifier(policy.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(policy.get("endpoint_id"), "endpoint_id"),
        "workspace_id": _policy_identifier(policy.get("workspace_id"), "workspace_id"),
        "workspace_generation": _policy_identifier(policy.get("workspace_generation"), "workspace_generation"),
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade.get("schema_version"), facade.get("profile"), facade.get("sha256")
        ),
        "max_bytes": max_bytes,
        "max_lines": max_lines,
    }
    if prefixes:
        result["allowed_relative_prefixes"] = _file_read_policy_allowed_prefixes(policy.get("allowed_relative_prefixes"))
    else:
        result["allowed_relative_paths"] = _file_read_policy_allowed_paths(policy.get("allowed_relative_paths"))
    if standing:
        result["authority_mode"] = authority_mode
    return result


def _read_file_read_policy(policy_path: Path) -> dict[str, Any]:
    try:
        stat = policy_path.stat()
        if not policy_path.is_file() or stat.st_size <= 0 or stat.st_size > FILE_READ_POLICY_MAX_BYTES:
            raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_MISSING") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID") from error
    return _normalise_file_read_policy(value)


def _approved_patch_policy_path(args: argparse.Namespace) -> Path:
    """Return the independently installed C4 exact-patch policy path.

    This lane is deliberately separate from metadata and bounded-file-read
    authority. A policy that permits a root to be observed or read must never
    become authority to modify that root.
    """

    return _policy_data_root(args) / APPROVED_PATCH_POLICY_FILE_NAME


def _approved_patch_relative_path(value: Any, *, code: str) -> str:
    """Mirror the C4 bridge's one-file relative-path boundary exactly."""

    if not isinstance(value, str):
        raise RuntimeError(code)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise RuntimeError(code) from error
    if (
        not encoded
        or len(encoded) > 512
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise RuntimeError(code)
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise RuntimeError(code)
    lowered = [part.lower() for part in parts]
    basename = lowered[-1]
    if (
        any(part in FILE_READ_SENSITIVE_DIRECTORY_NAMES or part.startswith(".env") for part in lowered)
        or basename in FILE_READ_SENSITIVE_BASENAMES
        or basename.endswith((".pem", ".key", ".p12", ".pfx"))
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_SENSITIVE_PATH")
    return value


def _approved_patch_policy_allowed_paths(value: Any) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= APPROVED_PATCH_MAX_ALLOWED_PATHS:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    allowed = [
        _approved_patch_relative_path(item, code="CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
        for item in value
    ]
    if len(allowed) != len(set(allowed)):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    return sorted(allowed)


def _approved_patch_policy_allowed_prefixes(value: Any) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= APPROVED_PATCH_MAX_ALLOWED_PATHS:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    allowed = [
        "." if item == "." else _approved_patch_relative_path(item, code="CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
        for item in value
    ]
    if len(allowed) != len(set(allowed)) or ("." in allowed and len(allowed) != 1):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    return sorted(allowed)


def _approved_patch_policy_limits(max_patch_bytes: Any, max_file_bytes: Any, *, code: str) -> tuple[int, int]:
    if (
        not isinstance(max_patch_bytes, int)
        or isinstance(max_patch_bytes, bool)
        or not isinstance(max_file_bytes, int)
        or isinstance(max_file_bytes, bool)
        or not 1 <= max_patch_bytes <= APPROVED_PATCH_MAX_BYTES
        or not 1 <= max_file_bytes <= APPROVED_PATCH_MAX_FILE_BYTES
    ):
        raise RuntimeError(code)
    return max_patch_bytes, max_file_bytes


def _normalise_approved_patch_policy(
    policy: Any,
    *,
    now_ms: int | None = None,
    require_enabled: bool = False,
) -> dict[str, Any]:
    """Validate the exact C4 default-deny local mutation policy."""

    schema_version = policy.get("schema_version") if isinstance(policy, dict) else None
    prefixes = schema_version == APPROVED_PATCH_POLICY_SCHEMA_VERSION
    standing = prefixes or schema_version == APPROVED_PATCH_POLICY_EXACT_SCHEMA_VERSION
    legacy = schema_version == APPROVED_PATCH_POLICY_LEGACY_SCHEMA_VERSION
    expected_fields = {
        "schema_version", "enabled", "server_origin", "owner_id", "device_id",
        "endpoint_id", "workspace_id", "workspace_generation", "expires_at_ms",
        "facade_contract", "max_patch_bytes",
        "max_file_bytes", "validation_profile",
    }
    expected_fields.add("allowed_relative_prefixes" if prefixes else "allowed_relative_paths")
    if standing:
        expected_fields.add("authority_mode")
    if (
        not isinstance(policy, dict)
        or set(policy) != expected_fields
        or not (standing or legacy)
        or not isinstance(policy.get("enabled"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    if require_enabled and policy["enabled"] is not True:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_DISABLED")
    authority_mode = APPROVED_PATCH_POLICY_STANDING_AUTHORITY if standing else "expiring_legacy"
    if standing and policy.get("authority_mode") != APPROVED_PATCH_POLICY_STANDING_AUTHORITY:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    expires_at_ms = policy.get("expires_at_ms")
    if standing:
        if expires_at_ms is not None:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    else:
        if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
        if now_ms is not None and expires_at_ms <= now_ms:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED")
    if policy.get("validation_profile") != APPROVED_PATCH_VALIDATION_PROFILE:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    facade = policy.get("facade_contract")
    if not isinstance(facade, dict) or set(facade) != {"schema_version", "profile", "sha256"}:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    try:
        server_origin = _server_origin(policy.get("server_origin"))
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID") from error
    max_patch_bytes, max_file_bytes = _approved_patch_policy_limits(
        policy.get("max_patch_bytes"),
        policy.get("max_file_bytes"),
        code="CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID",
    )
    result = {
        "schema_version": schema_version,
        "enabled": policy["enabled"],
        "server_origin": server_origin,
        "owner_id": _policy_identifier(policy.get("owner_id"), "owner_id"),
        "device_id": _policy_identifier(policy.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(policy.get("endpoint_id"), "endpoint_id"),
        "workspace_id": _policy_identifier(policy.get("workspace_id"), "workspace_id"),
        "workspace_generation": _policy_identifier(policy.get("workspace_generation"), "workspace_generation"),
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade.get("schema_version"), facade.get("profile"), facade.get("sha256")
        ),
        "max_patch_bytes": max_patch_bytes,
        "max_file_bytes": max_file_bytes,
        "validation_profile": APPROVED_PATCH_VALIDATION_PROFILE,
    }
    if prefixes:
        result["allowed_relative_prefixes"] = _approved_patch_policy_allowed_prefixes(policy.get("allowed_relative_prefixes"))
    else:
        result["allowed_relative_paths"] = _approved_patch_policy_allowed_paths(policy.get("allowed_relative_paths"))
    if standing:
        result["authority_mode"] = authority_mode
    return result


def _read_approved_patch_policy(policy_path: Path) -> dict[str, Any]:
    try:
        stat = policy_path.stat()
        if not policy_path.is_file() or stat.st_size <= 0 or stat.st_size > APPROVED_PATCH_POLICY_MAX_BYTES:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID") from error
    return _normalise_approved_patch_policy(value)


def _approved_patch_policy_admission(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify exact C4 local write authority before delivery or bridge launch."""

    policy = _normalise_approved_patch_policy(
        _read_approved_patch_policy(_approved_patch_policy_path(args)),
        now_ms=int(time.time() * 1000),
        require_enabled=True,
    )
    if (
        policy["server_origin"] != _server_origin(config.get("server_url"))
        or policy["device_id"] != config.get("device_id")
        or policy["endpoint_id"] != config.get("endpoint_id")
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_CONFIG_MISMATCH")
    entry = _require_policy_workspace_registration(args, config_path=config_path, policy=policy)
    if entry is None or entry["capabilities"].get("write") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return policy, entry


def _file_read_policy_admission(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify the independent C3 policy before a queue dequeue or local read."""

    policy = _normalise_file_read_policy(
        _read_file_read_policy(_file_read_policy_path(args)),
        now_ms=int(time.time() * 1000),
        require_enabled=True,
    )
    if (
        policy["server_origin"] != _server_origin(config.get("server_url"))
        or policy["device_id"] != config.get("device_id")
        or policy["endpoint_id"] != config.get("endpoint_id")
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_CONFIG_MISMATCH")
    entry = _require_policy_workspace_registration(args, config_path=config_path, policy=policy)
    if entry is None or entry["capabilities"].get("read") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return policy, entry


def _admit_file_read_policy_request(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Recheck all local C3 authority immediately before bridge launch."""

    policy, _entry = _file_read_policy_admission(args, config_path=config_path, config=config)
    for field in ("server_origin", "owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation"):
        if request.get(field) != policy[field]:
            raise RuntimeError("CONTROL_PLANE_FILE_READ_TARGET_MISMATCH")
    if request.get("facade_contract") != policy["facade_contract"]:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_CONTRACT_MISMATCH")
    expires_at_ms = request.get("expires_at_ms")
    now_ms = int(time.time() * 1000)
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_REQUEST_INVALID")
    if expires_at_ms <= now_ms:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_REQUEST_EXPIRED")
    if policy["expires_at_ms"] is not None and expires_at_ms > policy["expires_at_ms"]:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_EXPIRED")
    path = _file_read_relative_path(request.get("path"), code="CONTROL_PLANE_FILE_READ_REQUEST_INVALID")
    if not _policy_path_is_allowed(policy, path):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_PATH_DENIED")
    max_bytes, max_lines = _file_read_policy_limits(
        request.get("max_bytes"), request.get("max_lines"), code="CONTROL_PLANE_FILE_READ_REQUEST_INVALID"
    )
    if max_bytes > policy["max_bytes"] or max_lines > policy["max_lines"]:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_LIMIT_DENIED")
    return policy


def _exact_approved_patch_envelope(
    value: Any,
    *,
    expected_path: Any,
    expected_preimage_sha256: Any,
    expected_patch_sha256: Any,
    max_patch_bytes: int,
    max_file_bytes: int,
    code: str = "CONTROL_PLANE_APPROVED_PATCH_ENVELOPE_INVALID",
) -> dict[str, Any]:
    """Validate the one exact-file envelope before it reaches Recovery IPC.

    Recovery Host repeats this validation independently.  This copy makes the
    node agent reject malformed central delivery before a mutation-capable CJS
    process is launched, including compression and UTF-8 checks that protect
    its bounded memory budget.
    """

    if not isinstance(value, str):
        raise RuntimeError(code)
    try:
        expected_path = _approved_patch_relative_path(expected_path, code=code)
        preimage_sha256 = str(expected_preimage_sha256 or "").strip().lower()
        patch_sha256 = str(expected_patch_sha256 or "").strip().lower()
        raw = value.encode("utf-8")
    except (RuntimeError, UnicodeEncodeError) as error:
        raise RuntimeError(code) from error
    if (
        SHA256_PATTERN.fullmatch(preimage_sha256) is None
        or SHA256_PATTERN.fullmatch(patch_sha256) is None
        or not raw
        or len(raw) > max_patch_bytes
        or len(raw) > APPROVED_PATCH_MAX_BYTES
        or "\x00" in value
        or any(
            ord(character) <= 8
            or ord(character) in {11, 12}
            or 14 <= ord(character) <= 31
            or ord(character) == 127
            for character in value
        )
        or hashlib.sha256(raw).hexdigest() != patch_sha256
    ):
        raise RuntimeError(code)
    normalized = value.replace("\r\n", "\n")
    if "\r" in normalized:
        raise RuntimeError(code)
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if (
        len(lines) < 5
        or lines[0] != "*** Begin Patch"
        or lines[-1] != "*** End Patch"
        or lines[1] != f"*** Write Exact File: {expected_path}"
        or not lines[2].startswith("@@ ")
    ):
        raise RuntimeError(code)
    metadata: dict[str, str] = {}
    for token in lines[2][3:].split(" "):
        separator = token.find("=")
        key = token[:separator] if separator > 0 else ""
        metadata_value = token[separator + 1:].lower() if separator > 0 else ""
        if not key or not metadata_value or key in metadata:
            raise RuntimeError(code)
        metadata[key] = metadata_value
    if (
        set(metadata) != {"encoding", "preimage_sha256", "postimage_sha256"}
        or metadata["encoding"] != "zlib-base64"
        or metadata["preimage_sha256"] != preimage_sha256
        or SHA256_PATTERN.fullmatch(metadata["postimage_sha256"]) is None
    ):
        raise RuntimeError(code)
    chunks = lines[3:-1]
    if not chunks or any(not line.startswith("+") for line in chunks):
        raise RuntimeError(code)
    encoded = "".join(line[1:] for line in chunks)
    if not encoded or re.fullmatch(r"(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?", encoded) is None:
        raise RuntimeError(code)
    try:
        compressed = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise RuntimeError(code) from error
    if not compressed or base64.b64encode(compressed).decode("ascii") != encoded:
        raise RuntimeError(code)
    decoder = zlib.decompressobj()
    try:
        postimage = decoder.decompress(compressed, max_file_bytes + 1)
        if decoder.unconsumed_tail:
            raise ValueError("decompressed output exceeds limit")
        postimage += decoder.flush()
    except (zlib.error, ValueError) as error:
        raise RuntimeError(code) from error
    if (
        not decoder.eof
        or decoder.unused_data
        or len(postimage) > max_file_bytes
        or hashlib.sha256(postimage).hexdigest() != metadata["postimage_sha256"]
    ):
        raise RuntimeError(code)
    try:
        decoded = postimage.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(code) from error
    if decoded.encode("utf-8") != postimage:
        raise RuntimeError(code)
    return {
        "postimage_sha256": metadata["postimage_sha256"],
        "postimage_bytes": len(postimage),
    }


def _admit_approved_patch_policy_request(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Revalidate exact C4 policy, scope and patch bytes before mutation."""

    if isinstance(request, dict) and "authority_mode" not in request:
        # Legacy direct fixtures and already persisted owner-review actions
        # predate the explicit mode field.  Treat them as the old reviewed
        # lane; standing actions must carry the field end-to-end.
        request = {**request, "authority_mode": "owner_review"}
    expected_fields = {
        "server_origin", "owner_id", "device_id", "endpoint_id", "workspace_id",
        "workspace_generation", "context_id", "binding_id", "action_id", "attempt_id",
        "task_id", "writer_lease_generation",
        "tool_name", "operation", "permission_request_id", "permission_digest",
        "intent_digest", "path", "preimage_sha256", "patch_sha256", "patch_envelope",
        "validation_profile", "expires_at_ms", "facade_contract", "authority_mode",
    }
    if not isinstance(request, dict) or set(request) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    policy, _entry = _approved_patch_policy_admission(args, config_path=config_path, config=config)
    for field in ("server_origin", "owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation"):
        if request.get(field) != policy[field]:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_TARGET_MISMATCH")
    if request.get("facade_contract") != policy["facade_contract"]:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH")
    if (
        request.get("tool_name") != APPROVED_PATCH_TOOL_NAME
        or request.get("operation") != APPROVED_PATCH_OPERATION
        or request.get("validation_profile") != APPROVED_PATCH_VALIDATION_PROFILE
        or request.get("authority_mode") not in {"owner_review", APPROVED_PATCH_POLICY_STANDING_AUTHORITY}
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_TOOL_DENIED")
    for field in ("context_id", "binding_id", "action_id", "attempt_id", "permission_request_id"):
        value = request.get(field)
        if not isinstance(value, str) or APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN.fullmatch(value) is None:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    if request["authority_mode"] == APPROVED_PATCH_POLICY_STANDING_AUTHORITY:
        if request["permission_request_id"] != "standing":
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    elif request["permission_request_id"] == "standing":
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    task_id = request.get("task_id")
    writer_lease_generation = request.get("writer_lease_generation")
    if (
        not isinstance(task_id, str)
        or MCP_TASK_ID_PATTERN.fullmatch(task_id) is None
        or not isinstance(writer_lease_generation, int)
        or isinstance(writer_lease_generation, bool)
        or not 1 <= writer_lease_generation <= 1_000_000_000
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    for field in ("permission_digest", "intent_digest", "preimage_sha256", "patch_sha256"):
        value = request.get(field)
        if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value.lower()) is None:
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    expires_at_ms = request.get("expires_at_ms")
    now_ms = int(time.time() * 1000)
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    if expires_at_ms <= now_ms:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_REQUEST_EXPIRED")
    if policy["expires_at_ms"] is not None and expires_at_ms > policy["expires_at_ms"]:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED")
    path = _approved_patch_relative_path(request.get("path"), code="CONTROL_PLANE_APPROVED_PATCH_REQUEST_INVALID")
    if not _policy_path_is_allowed(policy, path):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED")
    patch = _exact_approved_patch_envelope(
        request.get("patch_envelope"),
        expected_path=request["path"],
        expected_preimage_sha256=request["preimage_sha256"],
        expected_patch_sha256=request["patch_sha256"],
        max_patch_bytes=policy["max_patch_bytes"],
        max_file_bytes=policy["max_file_bytes"],
    )
    return policy, patch


def _read_only_loop_policy_admission(args: argparse.Namespace) -> None:
    """Reject a loop before it can allocate central delivery work.

    ``poll-read-only-once`` retains its per-action bridge checks so an explicit
    one-shot always records a typed pre-effect receipt when appropriate.  A
    repeating loop must be stricter: an absent, disabled, expired or
    wrong-target policy is a local stop condition, not a reason to dequeue and
    reject new central actions repeatedly.
    """
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    policy = _read_local_policy(_read_only_policy_path(args))
    policy = _normalise_read_only_policy(
        policy,
        now_ms=int(time.time() * 1000),
        require_enabled=True,
    )
    if (
        policy["server_origin"] != _server_origin(config.get("server_url"))
        or policy["device_id"] != config["device_id"]
        or policy["endpoint_id"] != config["endpoint_id"]
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH")
    _require_policy_workspace_registration(args, config_path=config_path, policy=policy)


def read_only_policy_observation(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    """Project local policy state without exposing its content or granting work.

    Standing workspace lanes are preferred when present.  The legacy compact
    policy remains a compatibility fallback for the old read-only pilot.  In
    either case this projection is only typed telemetry; the local bridge and
    each individual action still revalidate authority at the effect boundary.
    """

    try:
        standing = _standing_policy_observation(args, config)
        if standing is not None:
            return standing
        policy = _read_local_policy(_read_only_policy_path(args))
        if (
            policy["server_origin"] != _server_origin(config.get("server_url"))
            or policy["device_id"] != config["device_id"]
            or policy["endpoint_id"] != config["endpoint_id"]
        ):
            raise RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH")
        state = "enabled" if policy["enabled"] is True and policy["expires_at_ms"] > int(time.time() * 1000) else "expired_or_disabled"
        return {
            "state": state,
            "expires_at_ms": policy["expires_at_ms"],
            "policy_sha256": _policy_digest(policy),
            "reason": "",
        }
    except RuntimeError as error:
        return {
            "state": "unavailable",
            "expires_at_ms": None,
            "policy_sha256": None,
            "reason": _safe_error_code(error, default="CONTROL_PLANE_POLICY_OBSERVATION_UNAVAILABLE"),
        }


def _route_evidence_from_heartbeat(
    config: dict[str, Any],
    response: dict[str, Any],
    projection: dict[str, str],
    policy_observation: dict[str, Any],
    *,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Validate the authenticated server echo before publishing local freshness.

    This record carries neither node credential nor workspace path.  It only
    lets Electron show that its same-user node agent recently completed the
    central heartbeat for this exact device.  It never enables an action: the
    local policy and individual bridge request are checked again elsewhere.
    """

    if not isinstance(response, dict):
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")
    server_origin = _server_origin(config.get("server_url"))
    device_id = _policy_identifier(config.get("device_id"), "device_id")
    endpoint_id = _policy_identifier(config.get("endpoint_id"), "endpoint_id")
    if (
        response.get("device_id") != device_id
        or response.get("endpoint_id") != endpoint_id
        or response.get("revoked_at_ms") is not None
        or not isinstance(response.get("credential_generation"), int)
        or isinstance(response.get("credential_generation"), bool)
        or response["credential_generation"] < 1
        or not isinstance(response.get("last_seen_at_ms"), int)
        or isinstance(response.get("last_seen_at_ms"), bool)
        or response["last_seen_at_ms"] <= 0
        or response.get("readiness") != projection["readiness"]
    ):
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")

    policy_state = str(response.get("policy_state") or "").strip().lower()
    if policy_state not in {"enabled", "expired_or_disabled", "unavailable", "unobserved"}:
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")
    policy_expires_at_ms = response.get("policy_expires_at_ms")
    policy_sha256 = response.get("policy_sha256")
    if policy_state in {"enabled", "expired_or_disabled"}:
        if (
            not isinstance(policy_expires_at_ms, int)
            or isinstance(policy_expires_at_ms, bool)
            or policy_expires_at_ms <= 0
            or not isinstance(policy_sha256, str)
            or SHA256_PATTERN.fullmatch(policy_sha256.strip().lower()) is None
        ):
            raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")
        policy_sha256 = policy_sha256.strip().lower()
    elif policy_expires_at_ms is not None or policy_sha256 is not None:
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")

    # The central echo must reflect the policy observation sent in this same
    # authenticated heartbeat.  Do not borrow an earlier node observation as
    # evidence for a changed local policy.
    if policy_state != policy_observation["state"]:
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")
    if policy_state in {"enabled", "expired_or_disabled"} and (
        policy_expires_at_ms != policy_observation["expires_at_ms"]
        or policy_sha256 != policy_observation["policy_sha256"]
    ):
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")

    observed_at_ms = int(time.time() * 1000) if now_ms is None else now_ms
    if not isinstance(observed_at_ms, int) or observed_at_ms <= 0:
        raise RuntimeError("CONTROL_PLANE_ROUTE_RESPONSE_INVALID")
    return {
        "schema_version": ROUTE_EVIDENCE_SCHEMA_VERSION,
        "kind": ROUTE_EVIDENCE_KIND,
        "server_origin": server_origin,
        "device_id": device_id,
        "endpoint_id": endpoint_id,
        "credential_generation": response["credential_generation"],
        "server_last_seen_at_ms": response["last_seen_at_ms"],
        "observed_at_ms": observed_at_ms,
        "runtime_readiness": projection["readiness"],
        "policy_state": policy_state,
        "policy_expires_at_ms": policy_expires_at_ms,
        "policy_sha256": policy_sha256,
    }


def _write_local_policy(policy_path: Path, policy: dict[str, Any], *, replace: bool) -> None:
    if policy_path.exists() and not replace:
        raise RuntimeError("CONTROL_PLANE_POLICY_ALREADY_EXISTS")
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(policy_path, policy)


def _install_read_only_policy_values(
    args: argparse.Namespace,
    *,
    config: dict[str, Any],
    owner_id: Any,
    workspace_id: Any,
    workspace_generation: Any,
    expires_at_ms: Any,
    facade_contract: Any,
) -> dict[str, Any]:
    """Validate and atomically install only the existing v2 read-only policy."""
    now_ms = int(time.time() * 1000)
    if (
        not isinstance(expires_at_ms, int)
        or isinstance(expires_at_ms, bool)
        or expires_at_ms <= now_ms
        or expires_at_ms > now_ms + READ_ONLY_POLICY_MAX_TTL_MS
    ):
        raise RuntimeError("CONTROL_PLANE_POLICY_EXPIRY_INVALID")
    if not isinstance(facade_contract, dict):
        raise RuntimeError("CONTROL_PLANE_POLICY_FACADE_CONTRACT_INVALID")
    policy = {
        "schema_version": READ_ONLY_POLICY_SCHEMA_VERSION,
        "enabled": True,
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _policy_identifier(owner_id, "owner_id"),
        "device_id": _policy_identifier(config.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(config.get("endpoint_id"), "endpoint_id"),
        "workspace_id": _policy_identifier(workspace_id, "workspace_id"),
        "workspace_generation": _policy_identifier(workspace_generation, "workspace_generation"),
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade_contract.get("schema_version"), facade_contract.get("profile"), facade_contract.get("sha256")
        ),
    }
    policy = _normalise_read_only_policy(policy, now_ms=now_ms, require_enabled=True)
    _write_local_policy(_read_only_policy_path(args), policy, replace=getattr(args, "replace", False) is True)
    return policy


def _policy_install_receipt(policy: dict[str, Any], args: argparse.Namespace) -> None:
    print(json.dumps({
        "operation": "control_plane_read_only_policy_installed",
        "enabled": True,
        "expires_at_ms": policy["expires_at_ms"],
        "policy_sha256": _policy_digest(policy),
        "runtime_mode": _runtime_mode(args),
        # chmod is not Windows ACL evidence; this receipt must remain truthful.
        "windows_acl_verified": False,
    }, separators=(",", ":")))


def _read_only_policy_template_from_response(response: Any, config: dict[str, Any]) -> dict[str, Any]:
    """Validate the only server projection accepted for a local read policy.

    The server deliberately omits the context identity from this projection.
    A node may install a policy only when the resulting target still matches
    both its own credential-bound identity and a current local registry entry.
    """

    if not isinstance(response, dict) or set(response) != {"policy_template"}:
        raise RuntimeError("CONTROL_PLANE_POLICY_TEMPLATE_INVALID")
    template = response.get("policy_template")
    expected_fields = {
        "owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation", "expires_at_ms", "facade_contract",
    }
    if not isinstance(template, dict) or set(template) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_POLICY_TEMPLATE_INVALID")
    if template["device_id"] != config["device_id"] or template["endpoint_id"] != config["endpoint_id"]:
        raise RuntimeError("CONTROL_PLANE_POLICY_TEMPLATE_TARGET_MISMATCH")
    return template


def _install_read_only_policy_from_template(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    template: dict[str, Any],
) -> int:
    """Recheck the local root at the effect boundary, then write its policy."""

    _require_current_local_workspace_registration(
        args,
        config_path=config_path,
        workspace_id=template["workspace_id"],
        workspace_generation=template["workspace_generation"],
    )
    policy = _install_read_only_policy_values(
        args,
        config=config,
        owner_id=template["owner_id"],
        workspace_id=template["workspace_id"],
        workspace_generation=template["workspace_generation"],
        expires_at_ms=template["expires_at_ms"],
        facade_contract=template["facade_contract"],
    )
    _policy_install_receipt(policy, args)
    return 0


def install_read_only_policy(args: argparse.Namespace) -> int:
    """Install one explicit, bounded local policy; this never contacts Ubuntu."""

    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_POLICY_CONFIRMATION_REQUIRED")
    config = _config(Path(args.config).expanduser().resolve())
    policy = _install_read_only_policy_values(
        args,
        config=config,
        owner_id=args.owner_id,
        workspace_id=args.workspace_id,
        workspace_generation=args.workspace_generation,
        expires_at_ms=args.expires_at_ms,
        facade_contract={
            "schema_version": args.facade_schema_version,
            "profile": args.facade_profile,
            "sha256": args.facade_sha256,
        },
    )
    _policy_install_receipt(policy, args)
    return 0


def install_read_only_policy_from_context(args: argparse.Namespace) -> int:
    """Fetch one node-scoped live context template after local confirmation."""

    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_POLICY_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    context_id = _policy_identifier(args.context_id, "context_id")
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/read-only-policy-template",
        {"context_id": context_id},
        f"Node {config['node_secret']}",
    )
    template = _read_only_policy_template_from_response(response, config)
    return _install_read_only_policy_from_template(
        args,
        config_path=config_path,
        config=config,
        template=template,
    )


def install_read_only_policy_from_assignment(args: argparse.Namespace) -> int:
    """Install an owner-issued policy for one locally selected registered root.

    Unlike the legacy diagnostic command above, this public onboarding path
    never accepts or reveals a ``ctx_…`` value.  The authenticated node sends
    only its already-registered opaque workspace identity to Ubuntu.  Ubuntu
    resolves exactly one pre-existing, live internal context for that root or
    fails closed when none (or more than one) exists.
    """

    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_POLICY_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    workspace_id = _policy_identifier(args.workspace_id, "workspace_id")
    workspace_generation = _policy_identifier(args.workspace_generation, "workspace_generation")
    # Do not disclose or request an assignment for a root that the local
    # owner has already removed. Recheck again after the HTTP response before
    # writing the policy in case the registry changed concurrently.
    _require_current_local_workspace_registration(
        args,
        config_path=config_path,
        workspace_id=workspace_id,
        workspace_generation=workspace_generation,
    )
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/read-only-policy-assignment",
        {"workspace_id": workspace_id, "workspace_generation": workspace_generation},
        f"Node {config['node_secret']}",
    )
    template = _read_only_policy_template_from_response(response, config)
    if (
        template["workspace_id"] != workspace_id
        or template["workspace_generation"] != workspace_generation
    ):
        raise RuntimeError("CONTROL_PLANE_POLICY_TEMPLATE_TARGET_MISMATCH")
    return _install_read_only_policy_from_template(
        args,
        config_path=config_path,
        config=config,
        template=template,
    )


def inspect_read_only_policy(args: argparse.Namespace) -> int:
    """Print a credential-free policy state; absence/invalidity is not readiness."""

    try:
        policy = _read_local_policy(_read_only_policy_path(args))
        now_ms = int(time.time() * 1000)
        state = "enabled" if policy["enabled"] and policy["expires_at_ms"] > now_ms else "expired_or_disabled"
        result: dict[str, Any] = {
            "operation": "control_plane_read_only_policy_observation",
            "state": state,
            "enabled": policy["enabled"],
            "expires_at_ms": policy["expires_at_ms"],
            "policy_sha256": _policy_digest(policy),
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    except RuntimeError as error:
        result = {
            "operation": "control_plane_read_only_policy_observation",
            "state": "unavailable",
            "reason": str(error),
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    print(json.dumps(result, separators=(",", ":")))
    return 0


def disable_read_only_policy(args: argparse.Namespace) -> int:
    """Fail locally closed without deleting the policy evidence."""

    if getattr(args, "confirm_disable", False) is not True:
        raise RuntimeError("CONTROL_PLANE_POLICY_DISABLE_CONFIRMATION_REQUIRED")
    policy_path = _read_only_policy_path(args)
    policy = _read_local_policy(policy_path)
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    print(json.dumps({
        "operation": "control_plane_read_only_policy_disabled",
        "enabled": False,
        "policy_sha256": _policy_digest(policy),
        "runtime_mode": _runtime_mode(args),
        "windows_acl_verified": False,
    }, separators=(",", ":")))
    return 0


def _file_read_allowed_paths_digest(paths: list[str]) -> str:
    """Fingerprint policy scope without printing the locally selected paths."""

    return hashlib.sha256(
        json.dumps(paths, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _policy_scope_receipt(policy: dict[str, Any]) -> dict[str, Any]:
    if "allowed_relative_prefixes" in policy:
        prefixes = policy["allowed_relative_prefixes"]
        return {
            "allowed_prefix_count": len(prefixes),
            "allowed_prefixes_sha256": _file_read_allowed_paths_digest(prefixes),
        }
    paths = policy["allowed_relative_paths"]
    return {
        "allowed_path_count": len(paths),
        "allowed_paths_sha256": _file_read_allowed_paths_digest(paths),
    }


def _install_file_read_policy_values(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    owner_id: Any,
    workspace_id: Any,
    workspace_generation: Any,
    expires_at_ms: Any,
    facade_contract: Any,
    allowed_relative_paths: Any,
    max_bytes: Any,
    max_lines: Any,
    allowed_relative_prefixes: Any = None,
) -> dict[str, Any]:
    """Install only explicit, locally confirmed C3 content authority.

    The central service never writes this file and an incoming action can never
    create it.  The local workspace registration is required before its exact
    opaque generation is permitted to receive a file-content policy.
    """

    now_ms = int(time.time() * 1000)
    standing = expires_at_ms is None
    if not standing and (
        not isinstance(expires_at_ms, int)
        or isinstance(expires_at_ms, bool)
        or expires_at_ms <= now_ms
        or expires_at_ms > now_ms + FILE_READ_POLICY_MAX_TTL_MS
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_EXPIRY_INVALID")
    if not isinstance(facade_contract, dict):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_FACADE_CONTRACT_INVALID")
    workspace_id = _policy_identifier(workspace_id, "workspace_id")
    workspace_generation = _policy_identifier(workspace_generation, "workspace_generation")
    entry = _require_current_local_workspace_registration(
        args,
        config_path=config_path,
        workspace_id=workspace_id,
        workspace_generation=workspace_generation,
    )
    if entry["capabilities"].get("read") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    if (allowed_relative_prefixes is None) == (allowed_relative_paths is None):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    if allowed_relative_prefixes is not None and not standing:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_INVALID")
    prefixes = allowed_relative_prefixes is not None
    policy = {
        "schema_version": (FILE_READ_POLICY_SCHEMA_VERSION if prefixes else
                           FILE_READ_POLICY_EXACT_SCHEMA_VERSION if standing else FILE_READ_POLICY_LEGACY_SCHEMA_VERSION),
        "enabled": True,
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _policy_identifier(owner_id, "owner_id"),
        "device_id": _policy_identifier(config.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(config.get("endpoint_id"), "endpoint_id"),
        "workspace_id": workspace_id,
        "workspace_generation": workspace_generation,
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade_contract.get("schema_version"), facade_contract.get("profile"), facade_contract.get("sha256")
        ),
        "max_bytes": max_bytes,
        "max_lines": max_lines,
    }
    if prefixes:
        policy["allowed_relative_prefixes"] = _file_read_policy_allowed_prefixes(allowed_relative_prefixes)
    else:
        policy["allowed_relative_paths"] = _file_read_policy_allowed_paths(allowed_relative_paths)
    if standing:
        policy["authority_mode"] = FILE_READ_POLICY_STANDING_AUTHORITY
    policy = _normalise_file_read_policy(policy, now_ms=now_ms, require_enabled=True)
    _write_local_policy(_file_read_policy_path(args), policy, replace=getattr(args, "replace", False) is True)
    return policy


def _file_read_policy_install_receipt(policy: dict[str, Any], args: argparse.Namespace) -> None:
    print(json.dumps({
        "operation": "control_plane_file_read_policy_installed",
        "enabled": True,
        "authority_mode": policy.get("authority_mode", "expiring_legacy"),
        "expires_at_ms": policy["expires_at_ms"],
        "policy_sha256": _policy_digest(policy),
        **_policy_scope_receipt(policy),
        "max_bytes": policy["max_bytes"],
        "max_lines": policy["max_lines"],
        "runtime_mode": _runtime_mode(args),
        # chmod is not Windows ACL evidence; this receipt must remain truthful.
        "windows_acl_verified": False,
    }, separators=(",", ":")))


def install_file_read_policy(args: argparse.Namespace) -> int:
    """Install one bounded file-content policy after explicit local consent."""

    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    policy = _install_file_read_policy_values(
        args,
        config_path=config_path,
        config=config,
        owner_id=args.owner_id,
        workspace_id=args.workspace_id,
        workspace_generation=args.workspace_generation,
        expires_at_ms=getattr(args, "expires_at_ms", None),
        facade_contract={
            "schema_version": args.facade_schema_version,
            "profile": args.facade_profile,
            "sha256": args.facade_sha256,
        },
        allowed_relative_paths=getattr(args, "allowed_relative_path", None),
        max_bytes=args.max_bytes,
        max_lines=args.max_lines,
        allowed_relative_prefixes=getattr(args, "allowed_relative_prefix", None),
    )
    _file_read_policy_install_receipt(policy, args)
    return 0


def inspect_file_read_policy(args: argparse.Namespace) -> int:
    """Report file-read policy state without disclosing its allowed paths."""

    try:
        policy = _read_file_read_policy(_file_read_policy_path(args))
        now_ms = int(time.time() * 1000)
        state = "enabled" if policy["enabled"] and (
            policy.get("authority_mode") == FILE_READ_POLICY_STANDING_AUTHORITY
            or (isinstance(policy["expires_at_ms"], int) and policy["expires_at_ms"] > now_ms)
        ) else "expired_or_disabled"
        result: dict[str, Any] = {
            "operation": "control_plane_file_read_policy_observation",
            "state": state,
            "enabled": policy["enabled"],
            "workspace_id": policy["workspace_id"],
            "workspace_generation": policy["workspace_generation"],
            "authority_mode": policy.get("authority_mode", "expiring_legacy"),
            "expires_at_ms": policy["expires_at_ms"],
            "policy_sha256": _policy_digest(policy),
            **_policy_scope_receipt(policy),
            "max_bytes": policy["max_bytes"],
            "max_lines": policy["max_lines"],
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    except RuntimeError as error:
        result = {
            "operation": "control_plane_file_read_policy_observation",
            "state": "unavailable",
            "reason": _safe_error_code(error, "CONTROL_PLANE_FILE_READ_POLICY_OBSERVATION_UNAVAILABLE"),
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    print(json.dumps(result, separators=(",", ":")))
    return 0


def disable_file_read_policy(args: argparse.Namespace) -> int:
    """Disable file-content authority locally while preserving audit evidence."""

    if getattr(args, "confirm_disable", False) is not True:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_POLICY_DISABLE_CONFIRMATION_REQUIRED")
    policy_path = _file_read_policy_path(args)
    policy = _read_file_read_policy(policy_path)
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    print(json.dumps({
        "operation": "control_plane_file_read_policy_disabled",
        "enabled": False,
        "policy_sha256": _policy_digest(policy),
        "runtime_mode": _runtime_mode(args),
        "windows_acl_verified": False,
    }, separators=(",", ":")))
    return 0


def _install_approved_patch_policy_values(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    owner_id: Any,
    workspace_id: Any,
    workspace_generation: Any,
    expires_at_ms: Any,
    facade_contract: Any,
    allowed_relative_paths: Any,
    max_patch_bytes: Any,
    max_file_bytes: Any,
    allowed_relative_prefixes: Any = None,
) -> dict[str, Any]:
    """Install explicit local C4 exact-patch authority after local consent.

    The server may deliver an already-approved patch, but it cannot create this
    policy or expand it. The selected registry entry must currently permit
    local writes before an owner can enable this narrow remote mutation lane.
    """

    now_ms = int(time.time() * 1000)
    standing = expires_at_ms is None
    if not standing and (
        not isinstance(expires_at_ms, int)
        or isinstance(expires_at_ms, bool)
        or expires_at_ms <= now_ms
        or expires_at_ms > now_ms + APPROVED_PATCH_POLICY_MAX_TTL_MS
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRY_INVALID")
    if not isinstance(facade_contract, dict):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_FACADE_CONTRACT_INVALID")
    workspace_id = _policy_identifier(workspace_id, "workspace_id")
    workspace_generation = _policy_identifier(workspace_generation, "workspace_generation")
    entry = _require_current_local_workspace_registration(
        args,
        config_path=config_path,
        workspace_id=workspace_id,
        workspace_generation=workspace_generation,
    )
    if entry["capabilities"].get("write") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    if (allowed_relative_prefixes is None) == (allowed_relative_paths is None):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    if allowed_relative_prefixes is not None and not standing:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID")
    prefixes = allowed_relative_prefixes is not None
    policy = {
        "schema_version": (APPROVED_PATCH_POLICY_SCHEMA_VERSION if prefixes else
                           APPROVED_PATCH_POLICY_EXACT_SCHEMA_VERSION if standing else APPROVED_PATCH_POLICY_LEGACY_SCHEMA_VERSION),
        "enabled": True,
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _policy_identifier(owner_id, "owner_id"),
        "device_id": _policy_identifier(config.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(config.get("endpoint_id"), "endpoint_id"),
        "workspace_id": workspace_id,
        "workspace_generation": workspace_generation,
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(
            facade_contract.get("schema_version"), facade_contract.get("profile"), facade_contract.get("sha256")
        ),
        "max_patch_bytes": max_patch_bytes,
        "max_file_bytes": max_file_bytes,
        "validation_profile": APPROVED_PATCH_VALIDATION_PROFILE,
    }
    if prefixes:
        policy["allowed_relative_prefixes"] = _approved_patch_policy_allowed_prefixes(allowed_relative_prefixes)
    else:
        policy["allowed_relative_paths"] = _approved_patch_policy_allowed_paths(allowed_relative_paths)
    if standing:
        policy["authority_mode"] = APPROVED_PATCH_POLICY_STANDING_AUTHORITY
    policy = _normalise_approved_patch_policy(policy, now_ms=now_ms, require_enabled=True)
    _write_local_policy(_approved_patch_policy_path(args), policy, replace=getattr(args, "replace", False) is True)
    return policy


def _approved_patch_policy_install_receipt(policy: dict[str, Any], args: argparse.Namespace) -> None:
    print(json.dumps({
        "operation": "control_plane_approved_patch_policy_installed",
        "enabled": True,
        "authority_mode": policy.get("authority_mode", "expiring_legacy"),
        "expires_at_ms": policy["expires_at_ms"],
        "policy_sha256": _policy_digest(policy),
        **_policy_scope_receipt(policy),
        "max_patch_bytes": policy["max_patch_bytes"],
        "max_file_bytes": policy["max_file_bytes"],
        "validation_profile": policy["validation_profile"],
        "runtime_mode": _runtime_mode(args),
        # chmod is not Windows ACL evidence; keep this operator output honest.
        "windows_acl_verified": False,
    }, separators=(",", ":")))


def install_approved_patch_policy(args: argparse.Namespace) -> int:
    """Install one owner-confirmed exact-file write policy without contacting Ubuntu."""

    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    policy = _install_approved_patch_policy_values(
        args,
        config_path=config_path,
        config=config,
        owner_id=args.owner_id,
        workspace_id=args.workspace_id,
        workspace_generation=args.workspace_generation,
        expires_at_ms=getattr(args, "expires_at_ms", None),
        facade_contract={
            "schema_version": args.facade_schema_version,
            "profile": args.facade_profile,
            "sha256": args.facade_sha256,
        },
        allowed_relative_paths=getattr(args, "allowed_relative_path", None),
        max_patch_bytes=args.max_patch_bytes,
        max_file_bytes=args.max_file_bytes,
        allowed_relative_prefixes=getattr(args, "allowed_relative_prefix", None),
    )
    _approved_patch_policy_install_receipt(policy, args)
    return 0


def inspect_approved_patch_policy(args: argparse.Namespace) -> int:
    """Report C4 policy state without returning path or patch authority."""

    try:
        policy = _read_approved_patch_policy(_approved_patch_policy_path(args))
        now_ms = int(time.time() * 1000)
        state = "enabled" if policy["enabled"] and (
            policy.get("authority_mode") == APPROVED_PATCH_POLICY_STANDING_AUTHORITY
            or (isinstance(policy["expires_at_ms"], int) and policy["expires_at_ms"] > now_ms)
        ) else "expired_or_disabled"
        result: dict[str, Any] = {
            "operation": "control_plane_approved_patch_policy_observation",
            "state": state,
            "enabled": policy["enabled"],
            "workspace_id": policy["workspace_id"],
            "workspace_generation": policy["workspace_generation"],
            "authority_mode": policy.get("authority_mode", "expiring_legacy"),
            "expires_at_ms": policy["expires_at_ms"],
            "policy_sha256": _policy_digest(policy),
            **_policy_scope_receipt(policy),
            "max_patch_bytes": policy["max_patch_bytes"],
            "max_file_bytes": policy["max_file_bytes"],
            "validation_profile": policy["validation_profile"],
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    except RuntimeError as error:
        result = {
            "operation": "control_plane_approved_patch_policy_observation",
            "state": "unavailable",
            "reason": _safe_error_code(error, "CONTROL_PLANE_APPROVED_PATCH_POLICY_OBSERVATION_UNAVAILABLE"),
            "runtime_mode": _runtime_mode(args),
            "windows_acl_verified": False,
        }
    print(json.dumps(result, separators=(",", ":")))
    return 0


def disable_approved_patch_policy(args: argparse.Namespace) -> int:
    """Locally revoke C4 write authority while preserving policy evidence."""

    if getattr(args, "confirm_disable", False) is not True:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_POLICY_DISABLE_CONFIRMATION_REQUIRED")
    policy_path = _approved_patch_policy_path(args)
    policy = _read_approved_patch_policy(policy_path)
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    print(json.dumps({
        "operation": "control_plane_approved_patch_policy_disabled",
        "enabled": False,
        "policy_sha256": _policy_digest(policy),
        "runtime_mode": _runtime_mode(args),
        "windows_acl_verified": False,
    }, separators=(",", ":")))
    return 0


def recovery_identity_observation(args: argparse.Namespace, project_root: Path) -> dict[str, Any] | None:
    """Read the one allowlisted identity action without exposing IPC secrets."""
    observer = Path(__file__).with_name("recovery_identity_observer.cjs")
    if not observer.is_file():
        return None
    try:
        command, environment = _adapter_command(args, observer, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    observation = payload.get("observation") if isinstance(payload, dict) and payload.get("ok") is True else None
    return observation if isinstance(observation, dict) else None


def recovery_runtime_status(args: argparse.Namespace, project_root: Path) -> dict[str, str]:
    """Return only the packaged adapter's strict/read-only readiness bit."""
    observer = Path(__file__).with_name("recovery_identity_observer.cjs")
    if not observer.is_file():
        raise RuntimeError("runtime_lifecycle_missing")
    try:
        command, environment = _adapter_command(args, observer, project_root, runtime_status=True)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("runtime_status_unavailable") from error
    if completed.returncode != 0:
        raise RuntimeError("runtime_status_unavailable")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("runtime_status_invalid") from error
    observation = payload.get("status") if isinstance(payload, dict) and payload.get("ok") is True else None
    if not isinstance(observation, dict) or (
        observation.get("observation_schema_version") != 1
        or observation.get("observation_kind") != "recovery_runtime_read_only"
        or observation.get("runtime_mode") != "packaged"
        or not isinstance(observation.get("strict_ready"), bool)
    ):
        raise RuntimeError("runtime_status_invalid")
    return {
        "adapter_mode": "packaged",
        "strict_ready": "true" if observation["strict_ready"] else "false",
    }


def _runtime_status(args: argparse.Namespace, project_root: Path) -> dict[str, str]:
    if _runtime_mode(args) == "packaged":
        return recovery_runtime_status(args, project_root)
    lifecycle = project_root / "scripts" / "dev-ui-lifecycle.js"
    if not lifecycle.is_file():
        raise RuntimeError("runtime_lifecycle_missing")
    try:
        completed = subprocess.run(
            [args.node, str(lifecycle), "status"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("runtime_status_unavailable") from error
    return parse_dev_ui_status(completed.stdout)


def _server_origin(value: Any) -> str:
    """Canonicalize only an origin that can also be represented by local policy."""
    text = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(text)
        hostname = str(parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    host = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    return f"{parsed.scheme}://{host}"


def _action_text(action: dict[str, Any], field: str) -> str:
    value = action.get(field)
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 256:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    return value.strip()


def _read_only_bridge_request(action: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Rebuild one façade-bound request from sealed fields, never raw relay input."""
    if not isinstance(action, dict) or action.get("tool_name") != READ_ONLY_TOOL_NAME:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    try:
        arguments = json.loads(str(action.get("arguments_json") or ""))
    except json.JSONDecodeError as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED") from error
    if arguments != READ_ONLY_ARGUMENTS:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    intent_digest = action.get("mcp_read_only_intent_digest")
    if not isinstance(intent_digest, str) or not SHA256_PATTERN.fullmatch(intent_digest.lower()):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    if action.get("admission_reference") != f"mcp_facade:{intent_digest.lower()}":
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    facade_schema_version = action.get("mcp_facade_schema_version")
    facade_profile = action.get("mcp_facade_profile")
    facade_sha256 = action.get("mcp_facade_contract_sha256")
    if (
        not isinstance(facade_schema_version, int)
        or isinstance(facade_schema_version, bool)
        or not 1 <= facade_schema_version <= 1_000_000
        or not isinstance(facade_profile, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}", facade_profile.strip()) is None
        or not isinstance(facade_sha256, str)
        or SHA256_PATTERN.fullmatch(facade_sha256.strip().lower()) is None
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    expires_at_ms = action.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    return {
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _action_text(action, "owner_id"),
        "device_id": _action_text(action, "device_id"),
        "endpoint_id": _action_text(action, "endpoint_id"),
        "workspace_id": _action_text(action, "workspace_id"),
        "workspace_generation": _action_text(action, "workspace_generation"),
        "context_id": _action_text(action, "context_id"),
        "binding_id": _action_text(action, "binding_id"),
        "action_id": _action_text(action, "action_id"),
        "attempt_id": _action_text(action, "attempt_id"),
        "tool_name": READ_ONLY_TOOL_NAME,
        "arguments": dict(READ_ONLY_ARGUMENTS),
        "expires_at_ms": expires_at_ms,
        "facade_contract": {
            "schema_version": facade_schema_version,
            "profile": facade_profile.strip(),
            "sha256": facade_sha256.strip().lower(),
        },
    }


def _file_read_action_text(action: dict[str, Any], field: str) -> str:
    value = action.get(field)
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 256:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    return value.strip()


def _file_read_bridge_request(action: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Rebuild one C3 request from sealed delivery fields only.

    The central action is already durable, but it remains untrusted at this
    boundary.  This parser intentionally rejects a near-match rather than
    forwarding caller-shaped JSON to Recovery Host or the local Coding MCP.
    """

    if not isinstance(action, dict) or action.get("tool_name") != FILE_READ_TOOL_NAME:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    try:
        arguments = json.loads(str(action.get("arguments_json") or ""))
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED") from error
    if (
        not isinstance(arguments, dict)
        or set(arguments) != {"operation", "path", "start_line", "max_lines", "max_bytes"}
        or arguments.get("operation") != FILE_READ_OPERATION
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    path = _file_read_relative_path(arguments.get("path"), code="CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    start_line = arguments.get("start_line")
    if (
        not isinstance(start_line, int)
        or isinstance(start_line, bool)
        or not 1 <= start_line <= 1_000_000
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    max_bytes, max_lines = _file_read_policy_limits(
        arguments.get("max_bytes"), arguments.get("max_lines"), code="CONTROL_PLANE_FILE_READ_ACTION_DENIED"
    )
    intent_digest = action.get("mcp_file_read_intent_digest")
    if not isinstance(intent_digest, str) or SHA256_PATTERN.fullmatch(intent_digest.strip().lower()) is None:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    intent_digest = intent_digest.strip().lower()
    if action.get("admission_reference") != f"mcp_file_read:{intent_digest}":
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    facade_schema_version = action.get("mcp_file_read_facade_schema_version")
    facade_profile = action.get("mcp_file_read_facade_profile")
    facade_sha256 = action.get("mcp_file_read_facade_contract_sha256")
    try:
        facade_contract = _policy_facade_contract(facade_schema_version, facade_profile, facade_sha256)
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED") from error
    expires_at_ms = action.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    return {
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _file_read_action_text(action, "owner_id"),
        "device_id": _file_read_action_text(action, "device_id"),
        "endpoint_id": _file_read_action_text(action, "endpoint_id"),
        "workspace_id": _file_read_action_text(action, "workspace_id"),
        "workspace_generation": _file_read_action_text(action, "workspace_generation"),
        "context_id": _file_read_action_text(action, "context_id"),
        "binding_id": _file_read_action_text(action, "binding_id"),
        "action_id": _file_read_action_text(action, "action_id"),
        "attempt_id": _file_read_action_text(action, "attempt_id"),
        "tool_name": FILE_READ_TOOL_NAME,
        "operation": FILE_READ_OPERATION,
        "path": path,
        "start_line": start_line,
        "max_lines": max_lines,
        "max_bytes": max_bytes,
        "expires_at_ms": expires_at_ms,
        "facade_contract": facade_contract,
    }


def _approved_patch_action_text(action: dict[str, Any], field: str) -> str:
    value = action.get(field)
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 256:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    return value.strip()


def _approved_patch_action_identifier(action: dict[str, Any], field: str) -> str:
    value = _approved_patch_action_text(action, field)
    if APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    return value


def _writer_lease_authority(action: dict[str, Any], *, code: str) -> tuple[str, int]:
    """Require the central writer fence identity before any local effect."""

    task_id = action.get("mcp_task_id")
    generation = action.get("writer_lease_generation")
    if (
        not isinstance(task_id, str)
        or MCP_TASK_ID_PATTERN.fullmatch(task_id.strip()) is None
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or not 1 <= generation <= 1_000_000_000
    ):
        raise RuntimeError(code)
    return task_id.strip(), generation


def _approved_patch_bridge_request(action: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Rebuild one sealed C4 patch delivery; never forward general arguments.

    Only the dedicated delivery columns are allowed to carry the raw envelope.
    Generic action JSON must contain digests and scope only, and every copy of
    the exact path/hash/contract has to agree before local policy admission.
    """

    if not isinstance(action, dict) or action.get("tool_name") != APPROVED_PATCH_TOOL_NAME:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    try:
        arguments = json.loads(str(action.get("arguments_json") or ""))
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED") from error
    authority_mode = action.get("mcp_approved_patch_authority_mode") or "owner_review"
    if authority_mode not in {"owner_review", APPROVED_PATCH_POLICY_STANDING_AUTHORITY}:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    expected_arguments = {
        "operation", "permission_request_id", "path", "preimage_sha256", "patch_sha256", "validation_profile",
    }
    if authority_mode == APPROVED_PATCH_POLICY_STANDING_AUTHORITY:
        expected_arguments.add("authority_mode")
    if (
        not isinstance(arguments, dict)
        or set(arguments) != expected_arguments
        or arguments.get("operation") != APPROVED_PATCH_OPERATION
        or arguments.get("validation_profile") != APPROVED_PATCH_VALIDATION_PROFILE
        or (authority_mode == APPROVED_PATCH_POLICY_STANDING_AUTHORITY
            and arguments.get("authority_mode") != APPROVED_PATCH_POLICY_STANDING_AUTHORITY)
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    try:
        path = _approved_patch_relative_path(arguments.get("path"), code="CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED") from error
    for field in ("permission_request_id", "preimage_sha256", "patch_sha256"):
        value = arguments.get(field)
        if not isinstance(value, str):
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    permission_request_id = arguments["permission_request_id"].strip()
    preimage_sha256 = arguments["preimage_sha256"].strip().lower()
    patch_sha256 = arguments["patch_sha256"].strip().lower()
    if (
        APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN.fullmatch(permission_request_id) is None
        or SHA256_PATTERN.fullmatch(preimage_sha256) is None
        or SHA256_PATTERN.fullmatch(patch_sha256) is None
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    permission_digest = action.get("mcp_approved_patch_permission_digest")
    intent_digest = action.get("mcp_approved_patch_intent_digest")
    if (
        not isinstance(permission_digest, str)
        or not isinstance(intent_digest, str)
        or SHA256_PATTERN.fullmatch(permission_digest.strip().lower()) is None
        or SHA256_PATTERN.fullmatch(intent_digest.strip().lower()) is None
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    permission_digest = permission_digest.strip().lower()
    intent_digest = intent_digest.strip().lower()
    expected_reference_prefix = (
        "mcp_standing_patch:" if authority_mode == APPROVED_PATCH_POLICY_STANDING_AUTHORITY
        else "mcp_approved_patch:"
    )
    if action.get("admission_reference") != f"{expected_reference_prefix}{intent_digest}":
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    if (
        action.get("mcp_approved_patch_permission_request_id") != permission_request_id
        or action.get("mcp_approved_patch_relative_path") != path
        or str(action.get("mcp_approved_patch_preimage_sha256") or "").strip().lower() != preimage_sha256
        or str(action.get("mcp_approved_patch_sha256") or "").strip().lower() != patch_sha256
        or action.get("mcp_approved_patch_validation_profile") != APPROVED_PATCH_VALIDATION_PROFILE
        or action.get("mcp_approved_patch_authority_mode", "owner_review") != authority_mode
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    patch_envelope = action.get("mcp_approved_patch_envelope")
    if not isinstance(patch_envelope, str):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    try:
        facade_contract = _policy_facade_contract(
            action.get("mcp_approved_patch_facade_schema_version"),
            action.get("mcp_approved_patch_facade_profile"),
            action.get("mcp_approved_patch_facade_contract_sha256"),
        )
        server_origin = _server_origin(config.get("server_url"))
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED") from error
    expires_at_ms = action.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    task_id, writer_lease_generation = _writer_lease_authority(
        action, code="CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED"
    )
    return {
        "server_origin": server_origin,
        "owner_id": _approved_patch_action_text(action, "owner_id"),
        "device_id": _approved_patch_action_text(action, "device_id"),
        "endpoint_id": _approved_patch_action_text(action, "endpoint_id"),
        "workspace_id": _approved_patch_action_text(action, "workspace_id"),
        "workspace_generation": _approved_patch_action_text(action, "workspace_generation"),
        "context_id": _approved_patch_action_identifier(action, "context_id"),
        "binding_id": _approved_patch_action_identifier(action, "binding_id"),
        "action_id": _approved_patch_action_identifier(action, "action_id"),
        "attempt_id": _approved_patch_action_identifier(action, "attempt_id"),
        "task_id": task_id,
        "writer_lease_generation": writer_lease_generation,
        "tool_name": APPROVED_PATCH_TOOL_NAME,
        "operation": APPROVED_PATCH_OPERATION,
        "authority_mode": authority_mode,
        "permission_request_id": permission_request_id,
        "permission_digest": permission_digest,
        "intent_digest": intent_digest,
        "path": path,
        "preimage_sha256": preimage_sha256,
        "patch_sha256": patch_sha256,
        "patch_envelope": patch_envelope,
        "validation_profile": APPROVED_PATCH_VALIDATION_PROFILE,
        "expires_at_ms": expires_at_ms,
        "facade_contract": facade_contract,
    }


def _document_write_action_text(action: dict[str, Any], field: str) -> str:
    value = action.get(field)
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 256:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    return value.strip()


def _document_write_action_identifier(action: dict[str, Any], field: str) -> str:
    value = _document_write_action_text(action, field)
    if DOCUMENT_WRITE_ACTION_IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    return value


def _document_write_relative_path(value: Any, *, code: str) -> str:
    try:
        return _approved_patch_relative_path(value, code=code)
    except RuntimeError as error:
        # The approved-patch helper is intentionally reused for the same
        # root-relative/sensitive-path boundary, but this lane must never leak
        # an approved-patch classification into its receipt contract.
        mapped = str(error).replace("APPROVED_PATCH", "DOCUMENT_WRITE")
        raise RuntimeError(mapped if mapped.startswith("CONTROL_PLANE_DOCUMENT_WRITE_") else code) from error


def _document_write_bridge_request(action: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Rebuild one sealed document intent without forwarding generic action data."""

    if not isinstance(action, dict) or action.get("tool_name") != DOCUMENT_WRITE_TOOL_NAME:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    try:
        arguments = json.loads(str(action.get("arguments_json") or ""))
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED") from error
    expected_arguments = {
        "operation", "authority_mode", "target", "source", "title", "content_sha256", "overwrite",
    }
    if not isinstance(arguments, dict) or set(arguments) != expected_arguments:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    operation = action.get("mcp_document_write_operation")
    if operation not in DOCUMENT_WRITE_OPERATIONS or arguments.get("operation") != operation:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    if arguments.get("authority_mode") != "standing":
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    try:
        target = _document_write_relative_path(
            arguments.get("target"), code="CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED"
        )
        raw_source = arguments.get("source")
        source = None if raw_source is None else _document_write_relative_path(
            raw_source, code="CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED"
        )
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED") from error
    if target != action.get("mcp_document_write_target_path") or source != action.get("mcp_document_write_source_path"):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    title = action.get("mcp_document_write_title")
    content = action.get("mcp_document_write_content")
    if (
        not isinstance(title, str)
        or len(title.encode("utf-8")) > DOCUMENT_WRITE_MAX_TITLE_BYTES
        or any(ord(character) < 32 or ord(character) == 127 for character in title)
        or not isinstance(content, str)
        or len(content.encode("utf-8")) > DOCUMENT_WRITE_MAX_CONTENT_BYTES
        or "\x00" in content
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    content_sha256 = arguments.get("content_sha256")
    if (
        not isinstance(content_sha256, str)
        or SHA256_PATTERN.fullmatch(content_sha256.strip().lower()) is None
        or hashlib.sha256(content.encode("utf-8")).hexdigest() != content_sha256.strip().lower()
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    overwrite = arguments.get("overwrite")
    if not isinstance(overwrite, bool) or overwrite != bool(action.get("mcp_document_write_overwrite")):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    if operation == "document_create":
        # Empty titles are valid for Markdown/text targets; the local MCP tool
        # owns any format-specific title defaulting.
        if source is not None:
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    elif source is None or source == target or not target.lower().endswith(".docx"):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    target_suffix = Path(target).suffix.lower()
    if target_suffix not in DOCUMENT_WRITE_TARGET_SUFFIXES:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_TARGET_INVALID")
    if source is not None and Path(source).suffix.lower() not in DOCUMENT_WRITE_SOURCE_SUFFIXES:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    facade_contract = _policy_facade_contract(
        action.get("mcp_document_write_facade_schema_version"),
        action.get("mcp_document_write_facade_profile"),
        action.get("mcp_document_write_facade_contract_sha256"),
    )
    intent_digest = action.get("mcp_document_write_intent_digest")
    if not isinstance(intent_digest, str) or SHA256_PATTERN.fullmatch(intent_digest.strip().lower()) is None:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    intent_digest = intent_digest.strip().lower()
    if action.get("admission_reference") != f"mcp_document_write:{intent_digest}":
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    task_id, writer_lease_generation = _writer_lease_authority(
        action, code="CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED"
    )
    expires_at_ms = action.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    return {
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _document_write_action_text(action, "owner_id"),
        "device_id": _document_write_action_text(action, "device_id"),
        "endpoint_id": _document_write_action_text(action, "endpoint_id"),
        "workspace_id": _document_write_action_text(action, "workspace_id"),
        "workspace_generation": _document_write_action_text(action, "workspace_generation"),
        "context_id": _document_write_action_identifier(action, "context_id"),
        "binding_id": _document_write_action_identifier(action, "binding_id"),
        "action_id": _document_write_action_identifier(action, "action_id"),
        "attempt_id": _document_write_action_identifier(action, "attempt_id"),
        "task_id": task_id,
        "writer_lease_generation": writer_lease_generation,
        "authority_mode": "standing",
        "tool_name": DOCUMENT_WRITE_TOOL_NAME,
        "operation": operation,
        "target": target,
        "source": source,
        "title": title,
        "content": content,
        "content_sha256": content_sha256.strip().lower(),
        "overwrite": overwrite,
        "intent_digest": intent_digest,
        "admission_reference": f"mcp_document_write:{intent_digest}",
        "expires_at_ms": expires_at_ms,
        "facade_contract": facade_contract,
    }


def _document_write_policy_admission(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reuse the standing approved-patch write policy as document authority."""

    try:
        policy, entry = _approved_patch_policy_admission(args, config_path=config_path, config=config)
    except RuntimeError as error:
        raise RuntimeError(str(error).replace("APPROVED_PATCH", "DOCUMENT_WRITE")) from error
    if (
        policy.get("schema_version") not in (APPROVED_PATCH_POLICY_SCHEMA_VERSION,
                                             APPROVED_PATCH_POLICY_EXACT_SCHEMA_VERSION)
        or policy.get("authority_mode") != APPROVED_PATCH_POLICY_STANDING_AUTHORITY
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_POLICY_INVALID")
    if entry.get("capabilities", {}).get("write") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return policy, entry


def _admit_document_write_policy_request(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    request: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Recheck target, generation, content and local allowlist before effect."""

    expected_fields = {
        "server_origin", "owner_id", "device_id", "endpoint_id", "workspace_id",
        "workspace_generation", "context_id", "binding_id", "action_id", "attempt_id",
        "task_id", "writer_lease_generation", "authority_mode", "tool_name", "operation",
        "target", "source", "title", "content", "content_sha256", "overwrite", "intent_digest",
        "admission_reference", "expires_at_ms", "facade_contract",
    }
    if not isinstance(request, dict) or set(request) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    policy, entry = _document_write_policy_admission(args, config_path=config_path, config=config)
    for field in ("server_origin", "owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation"):
        if request.get(field) != policy[field]:
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_TARGET_MISMATCH")
    if request.get("authority_mode") != "standing" or request.get("tool_name") != DOCUMENT_WRITE_TOOL_NAME:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_TOOL_DENIED")
    if request.get("facade_contract") != policy["facade_contract"]:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_CONTRACT_MISMATCH")
    if request.get("operation") not in DOCUMENT_WRITE_OPERATIONS:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    try:
        target = _document_write_relative_path(request.get("target"), code="CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
        source = None if request.get("source") is None else _document_write_relative_path(
            request.get("source"), code="CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID"
        )
    except RuntimeError as error:
        raise RuntimeError(str(error)) from error
    if target != request["target"] or (source is not None and source != request["source"]):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    if Path(target).suffix.lower() not in DOCUMENT_WRITE_TARGET_SUFFIXES:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_TARGET_INVALID")
    if request["operation"] == "document_create":
        if source is not None:
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    elif source is None or source == target or Path(target).suffix.lower() != ".docx":
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    if source is not None and Path(source).suffix.lower() not in DOCUMENT_WRITE_SOURCE_SUFFIXES:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_SOURCE_INVALID")
    if (
        not isinstance(request.get("title"), str)
        or len(request["title"].encode("utf-8")) > DOCUMENT_WRITE_MAX_TITLE_BYTES
        or any(ord(character) < 32 or ord(character) == 127 for character in request["title"])
        or not isinstance(request.get("content"), str)
        or len(request["content"].encode("utf-8")) > DOCUMENT_WRITE_MAX_CONTENT_BYTES
        or "\x00" in request["content"]
        or not isinstance(request.get("overwrite"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    content_sha256 = str(request.get("content_sha256") or "").strip().lower()
    if SHA256_PATTERN.fullmatch(content_sha256) is None or hashlib.sha256(request["content"].encode("utf-8")).hexdigest() != content_sha256:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    if not isinstance(request.get("intent_digest"), str) or SHA256_PATTERN.fullmatch(request["intent_digest"].lower()) is None:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    if request.get("admission_reference") != f"mcp_document_write:{request['intent_digest'].lower()}":
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    task_id = request.get("task_id")
    generation = request.get("writer_lease_generation")
    if (
        not isinstance(task_id, str)
        or MCP_TASK_ID_PATTERN.fullmatch(task_id) is None
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or not 1 <= generation <= 1_000_000_000
        or task_id != request["task_id"]
        or generation != request["writer_lease_generation"]
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    expires_at_ms = request.get("expires_at_ms")
    now_ms = int(time.time() * 1000)
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_INVALID")
    if expires_at_ms <= now_ms:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_REQUEST_EXPIRED")
    if not _policy_path_is_allowed(policy, target) or (
        source is not None and not _policy_path_is_allowed(policy, source)
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_PATH_DENIED")
    return policy, entry


def _file_read_projection_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _safe_file_read_bridge_result(
    value: Any,
    request: dict[str, Any],
    *,
    expected_policy_sha256: str,
) -> dict[str, Any]:
    """Allowlist one verified C3 file projection into a durable receipt."""

    expected_fields = {
        "schema_version", "operation_kind", "installation_id", "runtime_mode", "action_id", "attempt_id",
        "local_handle", "file_accessed", "policy_sha256", "actor", "runtime_identity",
        "facade_contract", "file", "response_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID")
    if (
        value.get("schema_version") != 1
        or value.get("operation_kind") != "control_plane_bounded_file_read"
        or value.get("action_id") != request["action_id"]
        or value.get("attempt_id") != request["attempt_id"]
        or value.get("file_accessed") is not True
        or not re.fullmatch(r"cp_fr_[a-f0-9]{48}", str(value.get("local_handle") or ""))
        or value.get("actor") != {"client_id": "electron-control-plane-file-read-bridge", "client_type": "electron"}
        or value.get("facade_contract") != request.get("facade_contract")
        or str(value.get("policy_sha256") or "").lower() != expected_policy_sha256
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID")
    installation_id = value.get("installation_id")
    runtime_mode = value.get("runtime_mode")
    if (
        installation_id is not None
        and (not isinstance(installation_id, str) or not 1 <= len(installation_id) <= 128)
    ) or runtime_mode not in {None, "development", "packaged"}:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID")
    identity = value.get("runtime_identity")
    if (
        not isinstance(identity, dict)
        or set(identity) != {
            "activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256",
        }
        or any(
            not isinstance(identity.get(field), str)
            or not 1 <= len(identity[field]) <= 128
            for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")
        )
        or not isinstance(identity.get("tool_contract_sha256"), str)
        or SHA256_PATTERN.fullmatch(identity["tool_contract_sha256"].lower()) is None
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_IDENTITY_INVALID")
    file_value = value.get("file")
    expected_file_fields = {
        "path", "content", "content_sha256", "encoding", "start_line", "end_line",
        "total_lines", "total_bytes", "bytes_read", "truncated", "next_start_line",
    }
    if not isinstance(file_value, dict) or set(file_value) != expected_file_fields:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    path = _file_read_relative_path(file_value.get("path"), code="CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    content = file_value.get("content")
    content_sha256 = str(file_value.get("content_sha256") or "").lower()
    if path != request["path"] or not isinstance(content, str) or file_value.get("encoding") != "utf-8":
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    try:
        content_bytes = content.encode("utf-8")
    except UnicodeEncodeError as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID") from error
    if (
        len(content_bytes) > request["max_bytes"]
        or SHA256_PATTERN.fullmatch(content_sha256) is None
        or hashlib.sha256(content_bytes).hexdigest() != content_sha256
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    if any(pattern.search(content) is not None for pattern in FILE_READ_SENSITIVE_CONTENT_PATTERNS):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_SENSITIVE_CONTENT")
    integer_fields = ("start_line", "end_line", "total_lines", "total_bytes", "bytes_read")
    if any(
        not isinstance(file_value.get(field), int)
        or isinstance(file_value.get(field), bool)
        or file_value[field] < 0
        for field in integer_fields
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    if (
        file_value["start_line"] != request["start_line"]
        or file_value["bytes_read"] != len(content_bytes)
        or file_value["bytes_read"] > request["max_bytes"]
        or file_value["total_bytes"] < file_value["bytes_read"]
        or file_value["total_lines"] < file_value["end_line"]
        or not isinstance(file_value.get("truncated"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    content_line_count = len(content.splitlines())
    requested_end_line = min(
        file_value["total_lines"], request["start_line"] + request["max_lines"] - 1
    )
    out_of_range = file_value["total_lines"] < request["start_line"]
    if (
        content_line_count > request["max_lines"]
        or (
            not out_of_range
            and (
                file_value["end_line"] < request["start_line"]
                or file_value["end_line"] > requested_end_line
                or content_line_count > file_value["end_line"] - request["start_line"] + 1
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
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    has_remaining_lines = file_value["end_line"] < file_value["total_lines"]
    next_start_line = file_value.get("next_start_line")
    if next_start_line is not None and (
        not isinstance(next_start_line, int) or isinstance(next_start_line, bool)
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    if (
        file_value["truncated"] is True
        and has_remaining_lines
        and next_start_line != file_value["end_line"] + 1
    ) or (
        (file_value["truncated"] is not True or not has_remaining_lines)
        and next_start_line is not None
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID")
    safe_file = {
        "path": path,
        "content": content,
        "content_sha256": content_sha256,
        "encoding": "utf-8",
        "start_line": file_value["start_line"],
        "end_line": file_value["end_line"],
        "total_lines": file_value["total_lines"],
        "total_bytes": file_value["total_bytes"],
        "bytes_read": file_value["bytes_read"],
        "truncated": file_value["truncated"],
        "next_start_line": next_start_line,
    }
    response_sha256 = str(value.get("response_sha256") or "").lower()
    if (
        SHA256_PATTERN.fullmatch(response_sha256) is None
        or response_sha256 != _file_read_projection_digest(safe_file)
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_RESULT_DIGEST_INVALID")
    return {
        "schema_version": 1,
        "operation_kind": "control_plane_bounded_file_read",
        "file_accessed": True,
        "local_handle": str(value["local_handle"]),
        "policy_sha256": expected_policy_sha256,
        "actor": {"client_id": "electron-control-plane-file-read-bridge", "client_type": "electron"},
        "runtime_identity": {
            "activation_epoch_id": identity["activation_epoch_id"],
            "process_instance_id": identity["process_instance_id"],
            "server_instance_id": identity["server_instance_id"],
            "tool_contract_sha256": identity["tool_contract_sha256"].lower(),
        },
        "facade_contract": dict(request["facade_contract"]),
        "file": safe_file,
        "response_sha256": response_sha256,
    }


def _approved_patch_projection_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _safe_approved_patch_bridge_result(
    value: Any,
    request: dict[str, Any],
    *,
    expected_policy_sha256: str,
    expected_patch: dict[str, Any],
) -> dict[str, Any]:
    """Allowlist one postimage-verified C4 receipt and omit patch bytes."""

    expected_fields = {
        "schema_version", "operation_kind", "installation_id", "runtime_mode", "action_id", "attempt_id",
        "task_id", "writer_lease_generation", "run_id", "wave_id",
        "local_handle", "patch_applied", "local_semantic_acceptance", "policy_sha256", "actor", "runtime_identity",
        "facade_contract", "file", "response_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID")
    if (
        value.get("schema_version") != 1
        or value.get("operation_kind") != "control_plane_approved_patch"
        or value.get("action_id") != request["action_id"]
        or value.get("attempt_id") != request["attempt_id"]
        or value.get("task_id") != request["task_id"]
        or value.get("writer_lease_generation") != request["writer_lease_generation"]
        or not isinstance(value.get("run_id"), str)
        or not re.fullmatch(r"[a-f0-9]{32}", value["run_id"].lower())
        or not isinstance(value.get("wave_id"), str)
        or not re.fullmatch(r"[a-f0-9]{32}", value["wave_id"].lower())
        or value.get("patch_applied") is not True
        # The local workflow deliberately remains in ACCEPTING until a
        # separately locally-authorized proof/acceptance step. This node relay
        # must never turn a central patch permission into self-acceptance.
        or value.get("local_semantic_acceptance") != "pending"
        or re.fullmatch(r"cp_ap_[a-f0-9]{48}", str(value.get("local_handle") or "")) is None
        or value.get("actor") != {
            "client_id": "electron-control-plane-approved-patch-bridge",
            "client_type": "electron",
        }
        or value.get("facade_contract") != request.get("facade_contract")
        or str(value.get("policy_sha256") or "").lower() != expected_policy_sha256
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID")
    installation_id = value.get("installation_id")
    runtime_mode = value.get("runtime_mode")
    if (
        installation_id is not None
        and (not isinstance(installation_id, str) or not 1 <= len(installation_id) <= 128)
    ) or runtime_mode not in {None, "development", "packaged"}:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID")
    identity = value.get("runtime_identity")
    if (
        not isinstance(identity, dict)
        or set(identity) != {
            "activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256",
        }
        or any(
            not isinstance(identity.get(field), str)
            or not 1 <= len(identity[field]) <= 128
            for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")
        )
        or not isinstance(identity.get("tool_contract_sha256"), str)
        or SHA256_PATTERN.fullmatch(identity["tool_contract_sha256"].lower()) is None
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_IDENTITY_INVALID")
    file_value = value.get("file")
    if not isinstance(file_value, dict) or set(file_value) != {
        "path", "preimage_sha256", "postimage_sha256", "bytes_written",
    }:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID")
    path = _approved_patch_relative_path(
        file_value.get("path"), code="CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID"
    )
    preimage_sha256 = str(file_value.get("preimage_sha256") or "").lower()
    postimage_sha256 = str(file_value.get("postimage_sha256") or "").lower()
    bytes_written = file_value.get("bytes_written")
    if (
        path != request["path"]
        or preimage_sha256 != request["preimage_sha256"]
        or postimage_sha256 != expected_patch["postimage_sha256"]
        or SHA256_PATTERN.fullmatch(preimage_sha256) is None
        or SHA256_PATTERN.fullmatch(postimage_sha256) is None
        or not isinstance(bytes_written, int)
        or isinstance(bytes_written, bool)
        or bytes_written < 0
        or bytes_written != expected_patch["postimage_bytes"]
        or bytes_written > APPROVED_PATCH_MAX_FILE_BYTES
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_FILE_INVALID")
    safe_file = {
        "path": path,
        "preimage_sha256": preimage_sha256,
        "postimage_sha256": postimage_sha256,
        "bytes_written": bytes_written,
    }
    response_sha256 = str(value.get("response_sha256") or "").lower()
    if (
        SHA256_PATTERN.fullmatch(response_sha256) is None
        or response_sha256 != _approved_patch_projection_digest(safe_file)
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_RESULT_DIGEST_INVALID")
    return {
        "schema_version": 1,
        "operation_kind": "control_plane_approved_patch",
        "patch_applied": True,
        "local_semantic_acceptance": "pending",
        "local_handle": str(value["local_handle"]),
        "task_id": str(value["task_id"]),
        "writer_lease_generation": int(value["writer_lease_generation"]),
        "run_id": str(value["run_id"]).lower(),
        "wave_id": str(value["wave_id"]).lower(),
        "policy_sha256": expected_policy_sha256,
        "actor": {
            "client_id": "electron-control-plane-approved-patch-bridge",
            "client_type": "electron",
        },
        "runtime_identity": {
            "activation_epoch_id": identity["activation_epoch_id"],
            "process_instance_id": identity["process_instance_id"],
            "server_instance_id": identity["server_instance_id"],
            "tool_contract_sha256": identity["tool_contract_sha256"].lower(),
        },
        "facade_contract": dict(request["facade_contract"]),
        "file": safe_file,
        "response_sha256": response_sha256,
    }


def _document_write_projection_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _safe_document_write_bridge_result(
    value: Any,
    request: dict[str, Any],
    *,
    expected_policy_sha256: str,
) -> dict[str, Any]:
    """Allowlist one digest-only document result before central receipt."""

    expected_fields = {
        "schema_version", "operation_kind", "local_handle", "action_id", "attempt_id", "task_id",
        "writer_lease_generation", "operation", "target", "source", "result", "actor", "policy_sha256",
        "facade_contract", "runtime_identity", "response_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_ENVELOPE_INVALID")
    if (
        value.get("schema_version") != 1
        or value.get("operation_kind") != "control_plane_document_write"
        or value.get("action_id") != request["action_id"]
        or value.get("attempt_id") != request["attempt_id"]
        or value.get("task_id") != request["task_id"]
        or value.get("writer_lease_generation") != request["writer_lease_generation"]
        or value.get("operation") != request["operation"]
        or value.get("target") != request["target"]
        or value.get("source") != request.get("source")
        or value.get("actor") != {"client_id": "electron-control-plane-document-bridge", "client_type": "electron"}
        or str(value.get("policy_sha256") or "").lower() != expected_policy_sha256
        or value.get("facade_contract") != request.get("facade_contract")
        or re.fullmatch(r"cp_doc_[a-f0-9]{48}", str(value.get("local_handle") or "")) is None
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_ENVELOPE_INVALID")
    identity = value.get("runtime_identity")
    if (
        not isinstance(identity, dict)
        or set(identity) != {"activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256"}
        or any(
            not isinstance(identity.get(field), str) or not 1 <= len(identity[field]) <= 128
            for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")
        )
        or SHA256_PATTERN.fullmatch(str(identity.get("tool_contract_sha256") or "").lower()) is None
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_IDENTITY_INVALID")
    result = value.get("result")
    if not isinstance(result, dict) or set(result) != {"operation", "target", "source", "size", "sha256", "format"}:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID")
    safe_result = {
        "operation": result.get("operation"),
        "target": result.get("target"),
        "source": result.get("source"),
        "size": result.get("size"),
        "sha256": str(result.get("sha256") or "").lower(),
        "format": str(result.get("format") or "").lower(),
    }
    if (
        safe_result["operation"] != request["operation"]
        or safe_result["target"] != request["target"]
        or safe_result["source"] != request.get("source")
        or not isinstance(safe_result["size"], int)
        or isinstance(safe_result["size"], bool)
        or not 1 <= safe_result["size"] <= DOCUMENT_WRITE_MAX_RESULT_BYTES
        or SHA256_PATTERN.fullmatch(safe_result["sha256"]) is None
        or re.fullmatch(r"[a-z0-9]{1,16}", safe_result["format"]) is None
        or safe_result["format"] != Path(request["target"]).suffix.lower().lstrip(".")
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID")
    response_sha256 = str(value.get("response_sha256") or "").lower()
    if SHA256_PATTERN.fullmatch(response_sha256) is None or response_sha256 != _document_write_projection_digest(safe_result):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_RESULT_DIGEST_INVALID")
    return {
        "schema_version": 1,
        "operation_kind": "control_plane_document_write",
        "local_handle": str(value["local_handle"]),
        "action_id": request["action_id"],
        "attempt_id": request["attempt_id"],
        "task_id": request["task_id"],
        "writer_lease_generation": request["writer_lease_generation"],
        "operation": request["operation"],
        "target": request["target"],
        "source": request.get("source"),
        "result": safe_result,
        "actor": {"client_id": "electron-control-plane-document-bridge", "client_type": "electron"},
        "policy_sha256": expected_policy_sha256,
        "facade_contract": dict(request["facade_contract"]),
        "runtime_identity": {
            "activation_epoch_id": identity["activation_epoch_id"],
            "process_instance_id": identity["process_instance_id"],
            "server_instance_id": identity["server_instance_id"],
            "tool_contract_sha256": str(identity["tool_contract_sha256"]).lower(),
        },
        "response_sha256": response_sha256,
    }


def _document_write_journal_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.document-write-bridge-journal.json")


def _read_document_write_journal(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": DOCUMENT_WRITE_JOURNAL_SCHEMA_VERSION, "entries": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_JOURNAL_INVALID") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "entries"}
        or value.get("schema_version") != DOCUMENT_WRITE_JOURNAL_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_JOURNAL_INVALID")
    return value


def _document_write_journal_key(action_id: str, attempt_id: str) -> str:
    if (
        DOCUMENT_WRITE_ACTION_IDENTIFIER_PATTERN.fullmatch(action_id) is None
        or DOCUMENT_WRITE_ACTION_IDENTIFIER_PATTERN.fullmatch(attempt_id) is None
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
    return f"{action_id}|{attempt_id}"


def _document_write_journal_receipt(
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt_state": receipt_state,
        "local_handle": local_handle,
        "payload": payload,
        "receipt_submitted": False,
    }


def _record_document_write_receipt(
    journal_path: Path,
    journal: dict[str, Any],
    *,
    state: str,
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    key = _document_write_journal_key(action_id, attempt_id)
    entry = {
        "state": state,
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt": _document_write_journal_receipt(action_id, attempt_id, receipt_state, local_handle, payload),
    }
    journal["entries"][key] = entry
    _write_json_atomic(journal_path, journal)
    return entry


def _recover_document_write_prepared_entry(
    entry: dict[str, Any],
    diagnostic_code: str = "CONTROL_PLANE_DOCUMENT_WRITE_PREPARED_RECOVERED",
) -> None:
    """Never replay a document effect after the local effect boundary."""

    if entry.get("state") != "prepared":
        return
    action_id = _document_write_action_identifier(entry, "action_id")
    attempt_id = _document_write_action_identifier(entry, "attempt_id")
    entry["state"] = "unknown"
    entry["receipt"] = _document_write_journal_receipt(
        action_id,
        attempt_id,
        "unknown",
        "",
        {
            "schema_version": 1,
            "operation_kind": "control_plane_document_write",
            "code": "CONTROL_PLANE_DOCUMENT_WRITE_EFFECT_UNKNOWN",
            "diagnostic_code": _safe_error_code(
                diagnostic_code,
                "CONTROL_PLANE_DOCUMENT_WRITE_PREPARED_RECOVERED",
            ),
            "reconciliation_required": True,
        },
    )


def _flush_document_write_journal(config: dict[str, Any], journal_path: Path, journal: dict[str, Any]) -> int:
    submitted = 0
    for key in sorted(journal["entries"]):
        entry = journal["entries"][key]
        if not isinstance(entry, dict):
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_JOURNAL_INVALID")
        if entry.get("state") == "prepared":
            _recover_document_write_prepared_entry(entry)
            _write_json_atomic(journal_path, journal)
        receipt = entry.get("receipt")
        if not isinstance(receipt, dict):
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_JOURNAL_INVALID")
        if receipt.get("receipt_submitted") is not True:
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted += 1
    return submitted


def _journal_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.read-only-bridge-journal.json")


def _read_journal(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": READ_ONLY_JOURNAL_SCHEMA_VERSION, "entries": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_JOURNAL_INVALID") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "entries"}
        or value.get("schema_version") != READ_ONLY_JOURNAL_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_JOURNAL_INVALID")
    return value


def _journal_key(action_id: str, attempt_id: str) -> str:
    if not 3 <= len(action_id) <= 256 or not 3 <= len(attempt_id) <= 256:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
    return f"{action_id}|{attempt_id}"


def _safe_error_code(value: Any, default: str = "CONTROL_PLANE_BRIDGE_FAILED") -> str:
    code = str(value or "").strip()
    return code if re.fullmatch(r"[A-Z0-9_]{3,96}", code) else default


def _summary_text(
    value: Any,
    *,
    allow_empty: bool = False,
    max_length: int = WORKSPACE_SUMMARY_TEXT_MAX,
    invalid_code: str = "CONTROL_PLANE_BRIDGE_RESULT_INVALID",
) -> str:
    if not isinstance(value, str) or len(value) > max_length or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise RuntimeError(invalid_code)
    if not allow_empty and not value:
        raise RuntimeError(invalid_code)
    return value


def _safe_workspace_summary(
    value: Any,
    *,
    invalid_code: str = "CONTROL_PLANE_BRIDGE_RESULT_INVALID",
) -> dict[str, Any]:
    """Accept one path-free, metadata-only compact workspace projection."""

    if not isinstance(value, dict) or set(value) != {"schema_version", "project", "entries", "entries_truncated", "git"}:
        raise RuntimeError(invalid_code)
    project = value.get("project")
    entries = value.get("entries")
    git = value.get("git")
    if (
        value.get("schema_version") != WORKSPACE_SUMMARY_SCHEMA_VERSION
        or not isinstance(project, dict)
        or set(project) != {"type", "name", "version"}
        or project.get("type") not in WORKSPACE_SUMMARY_PROJECT_TYPES
        or not isinstance(entries, list)
        or len(entries) > READ_ONLY_ARGUMENTS["max_entries"]
        or not isinstance(value.get("entries_truncated"), bool)
        or not isinstance(git, dict)
        or set(git) != {"is_repo", "branch", "changed_count", "truncated"}
        or not isinstance(git.get("is_repo"), bool)
        or not isinstance(git.get("changed_count"), int)
        or isinstance(git.get("changed_count"), bool)
        or not 0 <= git["changed_count"] <= 100_000
        or not isinstance(git.get("truncated"), bool)
    ):
        raise RuntimeError(invalid_code)
    safe_entries: list[dict[str, Any]] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"name", "type", "size_bytes", "is_hidden", "is_ignored"}
            or entry.get("type") not in WORKSPACE_SUMMARY_ENTRY_TYPES
            or not isinstance(entry.get("size_bytes"), int)
            or isinstance(entry.get("size_bytes"), bool)
            or entry["size_bytes"] < 0
            or not isinstance(entry.get("is_hidden"), bool)
            or not isinstance(entry.get("is_ignored"), bool)
        ):
            raise RuntimeError(invalid_code)
        name = _summary_text(entry.get("name"), invalid_code=invalid_code)
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise RuntimeError(invalid_code)
        safe_entries.append({
            "name": name,
            "type": entry["type"],
            "size_bytes": entry["size_bytes"],
            "is_hidden": entry["is_hidden"],
            "is_ignored": entry["is_ignored"],
        })
    result = {
        "schema_version": WORKSPACE_SUMMARY_SCHEMA_VERSION,
        "project": {
            "type": project["type"],
            "name": _summary_text(project.get("name"), invalid_code=invalid_code),
            "version": _summary_text(project.get("version"), allow_empty=True, max_length=128, invalid_code=invalid_code),
        },
        "entries": safe_entries,
        "entries_truncated": value["entries_truncated"],
        "git": {
            "is_repo": git["is_repo"],
            "branch": _summary_text(git.get("branch"), allow_empty=True, invalid_code=invalid_code),
            "changed_count": git["changed_count"],
            "truncated": git["truncated"],
        },
    }
    if len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")) > WORKSPACE_SUMMARY_MAX_BYTES:
        raise RuntimeError(invalid_code)
    return result


def safe_workspace_summary(value: Any) -> dict[str, Any]:
    """Public generic validation used by the central MCP receipt reader."""

    return _safe_workspace_summary(value)


def _safe_bridge_result(value: Any, request: dict[str, Any]) -> dict[str, Any]:
    """Allowlist a completed receipt; neither workspace paths nor raw MCP data cross this boundary."""
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_ENVELOPE_INVALID")
    identity = value.get("runtime_identity")
    actor = value.get("actor")
    facade_contract = value.get("facade_contract")
    workspace_summary = _safe_workspace_summary(
        value.get("workspace_summary"),
        invalid_code="CONTROL_PLANE_BRIDGE_RESULT_SUMMARY_INVALID",
    )
    workspace_summary_sha256 = str(value.get("workspace_summary_sha256") or "").lower()
    if (
        value.get("operation_kind") != "control_plane_read_only_workspace_context"
        or value.get("action_id") != request["action_id"]
        or value.get("attempt_id") != request["attempt_id"]
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_ACTION_INVALID")
    if (
        value.get("workspace_accessed") is not True
        or not re.fullmatch(r"cp_ro_[a-f0-9]{48}", str(value.get("local_handle") or ""))
        or not SHA256_PATTERN.fullmatch(str(value.get("policy_sha256") or "").lower())
        or actor != {"client_id": "electron-control-plane-bridge", "client_type": "electron"}
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_ENVELOPE_INVALID")
    if (
        not isinstance(identity, dict)
        or not all(isinstance(identity.get(field), str) and 0 < len(identity[field]) <= 128 for field in ("activation_epoch_id", "process_instance_id", "server_instance_id"))
        or not SHA256_PATTERN.fullmatch(str(identity.get("tool_contract_sha256") or "").lower())
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_IDENTITY_INVALID")
    if (
        not isinstance(facade_contract, dict)
        or set(facade_contract) != {"schema_version", "profile", "sha256"}
        or facade_contract != request.get("facade_contract")
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_CONTRACT_INVALID")
    if (
        not SHA256_PATTERN.fullmatch(workspace_summary_sha256)
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_SUMMARY_DIGEST_INVALID")
    if (
        not SHA256_PATTERN.fullmatch(str(value.get("response_sha256") or "").lower())
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_DIGEST_INVALID")
    return {
        "schema_version": 1,
        "operation_kind": "control_plane_read_only_workspace_context",
        "workspace_accessed": True,
        "local_handle": str(value["local_handle"]),
        "policy_sha256": str(value["policy_sha256"]).lower(),
        "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
        "runtime_identity": {
            "activation_epoch_id": identity["activation_epoch_id"],
            "process_instance_id": identity["process_instance_id"],
            "server_instance_id": identity["server_instance_id"],
            "tool_contract_sha256": str(identity["tool_contract_sha256"]).lower(),
        },
        "facade_contract": dict(facade_contract),
        "workspace_summary": workspace_summary,
        "workspace_summary_sha256": workspace_summary_sha256,
        "response_sha256": str(value["response_sha256"]).lower(),
    }


def recovery_read_only_bridge(args: argparse.Namespace, project_root: Path, request: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Call the descriptor-hiding CJS bridge once; errors are returned as typed codes.

    The result stays inside this process until ``poll_read_only_once`` verifies
    and allowlists it immediately before the durable receipt boundary.  Do not
    normalize it here as well: that projection intentionally omits action and
    attempt identifiers, which the final verifier must compare to its request.
    """
    bridge = Path(__file__).with_name("recovery_read_only_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_BRIDGE_UNAVAILABLE"
    try:
        command, environment = _adapter_command(args, bridge, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "CONTROL_PLANE_BRIDGE_TIMEOUT"
    except OSError:
        return None, "CONTROL_PLANE_BRIDGE_UNAVAILABLE"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "CONTROL_PLANE_BRIDGE_RESULT_INVALID"
    if completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True:
        result = payload.get("result")
        if not isinstance(result, dict):
            return None, "CONTROL_PLANE_BRIDGE_RESULT_ENVELOPE_INVALID"
        return result, None
    error = payload.get("error") if isinstance(payload, dict) else None
    return None, _safe_error_code(error.get("code") if isinstance(error, dict) else None)


def recovery_file_read_bridge(args: argparse.Namespace, project_root: Path, request: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Call the independent C3 descriptor-hiding bridge once.

    This must remain a sibling of the metadata bridge rather than sharing a
    generic subprocess adapter.  A packaging omission or a response shape
    drift then fails this capability closed without changing the old lane.
    """

    bridge = Path(__file__).with_name("recovery_file_read_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_FILE_READ_UNAVAILABLE"
    try:
        command, environment = _adapter_command(args, bridge, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "CONTROL_PLANE_FILE_READ_TIMEOUT"
    except OSError:
        return None, "CONTROL_PLANE_FILE_READ_UNAVAILABLE"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "CONTROL_PLANE_FILE_READ_RESULT_INVALID"
    if completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True:
        result = payload.get("result")
        if not isinstance(result, dict):
            return None, "CONTROL_PLANE_FILE_READ_RESULT_ENVELOPE_INVALID"
        return result, None
    error = payload.get("error") if isinstance(payload, dict) else None
    return None, _safe_error_code(error.get("code") if isinstance(error, dict) else None)


def recovery_approved_patch_bridge(
    args: argparse.Namespace,
    project_root: Path,
    request: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Call the independent C4 descriptor-hiding bridge at most once.

    The raw exact-file envelope lives only in the sealed subprocess input. A
    caller receives an allowlisted result or a typed code; it never receives a
    Recovery descriptor, local root, or patch payload back from Electron.
    """

    bridge = Path(__file__).with_name("recovery_approved_patch_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE"
    try:
        command, environment = _adapter_command(args, bridge, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "CONTROL_PLANE_APPROVED_PATCH_TIMEOUT"
    except OSError:
        return None, "CONTROL_PLANE_APPROVED_PATCH_UNAVAILABLE"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "CONTROL_PLANE_APPROVED_PATCH_RESULT_INVALID"
    if completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True:
        result = payload.get("result")
        if not isinstance(result, dict):
            return None, "CONTROL_PLANE_APPROVED_PATCH_RESULT_ENVELOPE_INVALID"
        return result, None
    error = payload.get("error") if isinstance(payload, dict) else None
    return None, _safe_error_code(
        error.get("code") if isinstance(error, dict) else None,
        "CONTROL_PLANE_APPROVED_PATCH_FAILED",
    )


def recovery_exec_bridge(
    args: argparse.Namespace,
    project_root: Path,
    request: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Call the descriptor-hiding Electron exec bridge exactly once.

    The Python node agent never receives the Recovery descriptor/token or the
    local MCP credential.  A successful result is still revalidated by the
    journal/receipt boundary before it is submitted to Ubuntu.
    """

    bridge = Path(__file__).with_name("recovery_exec_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_EXEC_UNAVAILABLE"
    try:
        command, environment = _adapter_command(args, bridge, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "CONTROL_PLANE_EXEC_TIMEOUT"
    except OSError:
        return None, "CONTROL_PLANE_EXEC_UNAVAILABLE"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "CONTROL_PLANE_EXEC_RESULT_INVALID"
    if completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True:
        result = payload.get("result")
        if not isinstance(result, dict):
            return None, "CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID"
        return result, None
    error = payload.get("error") if isinstance(payload, dict) else None
    return None, _safe_error_code(
        error.get("code") if isinstance(error, dict) else None,
        "CONTROL_PLANE_EXEC_FAILED",
    )


def recovery_document_write_bridge(
    args: argparse.Namespace,
    project_root: Path,
    request: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Call the descriptor-hiding document-write bridge exactly once.

    The node agent never receives a Recovery descriptor, local MCP credential,
    absolute workspace root, or document bytes back from Electron.  A result
    is still revalidated by the journal boundary before it becomes a receipt.
    """

    bridge = Path(__file__).with_name("recovery_document_write_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE"
    try:
        command, environment = _adapter_command(args, bridge, project_root)
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "CONTROL_PLANE_DOCUMENT_WRITE_TIMEOUT"
    except OSError:
        return None, "CONTROL_PLANE_DOCUMENT_WRITE_UNAVAILABLE"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID"
    if completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True:
        result = payload.get("result")
        if not isinstance(result, dict):
            return None, "CONTROL_PLANE_DOCUMENT_WRITE_RESULT_ENVELOPE_INVALID"
        return result, None
    error = payload.get("error") if isinstance(payload, dict) else None
    return None, _safe_error_code(
        error.get("code") if isinstance(error, dict) else None,
        "CONTROL_PLANE_DOCUMENT_WRITE_FAILED",
    )


def _journal_receipt(action_id: str, attempt_id: str, receipt_state: str, local_handle: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt_state": receipt_state,
        "local_handle": local_handle,
        "payload": payload,
        "receipt_submitted": False,
    }


def _submit_receipt(config: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    receipt = entry.get("receipt")
    if not isinstance(receipt, dict):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_JOURNAL_INVALID")
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/receipts",
        {
            "action_id": receipt.get("action_id"),
            "attempt_id": receipt.get("attempt_id"),
            "receipt_state": receipt.get("receipt_state"),
            "local_handle": receipt.get("local_handle", ""),
            "payload": receipt.get("payload", {}),
        },
        f"Node {config['node_secret']}",
    )
    receipt["receipt_submitted"] = True
    return response


def _recover_prepared_entry(
    entry: dict[str, Any],
    diagnostic_code: str = "CONTROL_PLANE_BRIDGE_PREPARED_RECOVERED",
) -> None:
    """A crash after preparation may have crossed the local call boundary; never retry it."""
    if entry.get("state") != "prepared":
        return
    action_id = _action_text(entry, "action_id")
    attempt_id = _action_text(entry, "attempt_id")
    entry["state"] = "unknown"
    entry["receipt"] = _journal_receipt(
        action_id,
        attempt_id,
        "unknown",
        "",
        {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "code": "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
            "diagnostic_code": _safe_error_code(
                diagnostic_code,
                "CONTROL_PLANE_BRIDGE_PREPARED_RECOVERED",
            ),
        },
    )


def _flush_journal(config: dict[str, Any], journal_path: Path, journal: dict[str, Any]) -> int:
    submitted = 0
    for key in sorted(journal["entries"]):
        entry = journal["entries"][key]
        if not isinstance(entry, dict):
            raise RuntimeError("CONTROL_PLANE_BRIDGE_JOURNAL_INVALID")
        if entry.get("state") == "prepared":
            _recover_prepared_entry(entry)
            _write_json_atomic(journal_path, journal)
        receipt = entry.get("receipt")
        if not isinstance(receipt, dict):
            raise RuntimeError("CONTROL_PLANE_BRIDGE_JOURNAL_INVALID")
        if receipt.get("receipt_submitted") is not True:
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted += 1
    return submitted


def _file_read_journal_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.file-read-bridge-journal.json")


def _read_file_read_journal(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": FILE_READ_JOURNAL_SCHEMA_VERSION, "entries": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_JOURNAL_INVALID") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "entries"}
        or value.get("schema_version") != FILE_READ_JOURNAL_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_JOURNAL_INVALID")
    return value


def _file_read_journal_key(action_id: str, attempt_id: str) -> str:
    if not 3 <= len(action_id) <= 256 or not 3 <= len(attempt_id) <= 256:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
    return f"{action_id}|{attempt_id}"


def _file_read_journal_receipt(
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt_state": receipt_state,
        "local_handle": local_handle,
        "payload": payload,
        "receipt_submitted": False,
    }


def _record_file_read_receipt(
    journal_path: Path,
    journal: dict[str, Any],
    *,
    state: str,
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    key = _file_read_journal_key(action_id, attempt_id)
    entry = {
        "state": state,
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt": _file_read_journal_receipt(action_id, attempt_id, receipt_state, local_handle, payload),
    }
    journal["entries"][key] = entry
    _write_json_atomic(journal_path, journal)
    return entry


def _recover_file_read_prepared_entry(
    entry: dict[str, Any],
    diagnostic_code: str = "CONTROL_PLANE_FILE_READ_PREPARED_RECOVERED",
) -> None:
    """Never re-run a prepared file read after a worker crash/restart."""

    if entry.get("state") != "prepared":
        return
    action_id = _file_read_action_text(entry, "action_id")
    attempt_id = _file_read_action_text(entry, "attempt_id")
    entry["state"] = "unknown"
    entry["receipt"] = _file_read_journal_receipt(
        action_id,
        attempt_id,
        "unknown",
        "",
        {
            "schema_version": 1,
            "operation_kind": "control_plane_bounded_file_read",
            "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
            "diagnostic_code": _safe_error_code(
                diagnostic_code,
                "CONTROL_PLANE_FILE_READ_PREPARED_RECOVERED",
            ),
        },
    )


def _flush_file_read_journal(config: dict[str, Any], journal_path: Path, journal: dict[str, Any]) -> int:
    submitted = 0
    for key in sorted(journal["entries"]):
        entry = journal["entries"][key]
        if not isinstance(entry, dict):
            raise RuntimeError("CONTROL_PLANE_FILE_READ_JOURNAL_INVALID")
        if entry.get("state") == "prepared":
            _recover_file_read_prepared_entry(entry)
            _write_json_atomic(journal_path, journal)
        receipt = entry.get("receipt")
        if not isinstance(receipt, dict):
            raise RuntimeError("CONTROL_PLANE_FILE_READ_JOURNAL_INVALID")
        if receipt.get("receipt_submitted") is not True:
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted += 1
    return submitted


def _approved_patch_journal_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.approved-patch-bridge-journal.json")


def _read_approved_patch_journal(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": APPROVED_PATCH_JOURNAL_SCHEMA_VERSION, "entries": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_JOURNAL_INVALID") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "entries"}
        or value.get("schema_version") != APPROVED_PATCH_JOURNAL_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_JOURNAL_INVALID")
    return value


def _approved_patch_journal_key(action_id: str, attempt_id: str) -> str:
    if (
        APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN.fullmatch(action_id) is None
        or APPROVED_PATCH_ACTION_IDENTIFIER_PATTERN.fullmatch(attempt_id) is None
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
    return f"{action_id}|{attempt_id}"


def _approved_patch_journal_receipt(
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt_state": receipt_state,
        "local_handle": local_handle,
        "payload": payload,
        "receipt_submitted": False,
    }


def _record_approved_patch_receipt(
    journal_path: Path,
    journal: dict[str, Any],
    *,
    state: str,
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    key = _approved_patch_journal_key(action_id, attempt_id)
    entry = {
        "state": state,
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt": _approved_patch_journal_receipt(action_id, attempt_id, receipt_state, local_handle, payload),
    }
    journal["entries"][key] = entry
    _write_json_atomic(journal_path, journal)
    return entry


def _recover_approved_patch_prepared_entry(
    entry: dict[str, Any],
    diagnostic_code: str = "CONTROL_PLANE_APPROVED_PATCH_PREPARED_RECOVERED",
) -> None:
    """Terminalize an ambiguous mutation boundary rather than replay a patch."""

    if entry.get("state") != "prepared":
        return
    action_id = _approved_patch_action_identifier(entry, "action_id")
    attempt_id = _approved_patch_action_identifier(entry, "attempt_id")
    entry["state"] = "unknown"
    entry["receipt"] = _approved_patch_journal_receipt(
        action_id,
        attempt_id,
        "unknown",
        "",
        {
            "schema_version": 1,
            "operation_kind": "control_plane_approved_patch",
            "code": "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN",
            "diagnostic_code": _safe_error_code(
                diagnostic_code,
                "CONTROL_PLANE_APPROVED_PATCH_PREPARED_RECOVERED",
            ),
        },
    )


def _flush_approved_patch_journal(
    config: dict[str, Any],
    journal_path: Path,
    journal: dict[str, Any],
) -> int:
    submitted = 0
    for key in sorted(journal["entries"]):
        entry = journal["entries"][key]
        if not isinstance(entry, dict):
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_JOURNAL_INVALID")
        if entry.get("state") == "prepared":
            _recover_approved_patch_prepared_entry(entry)
            _write_json_atomic(journal_path, journal)
        receipt = entry.get("receipt")
        if not isinstance(receipt, dict):
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_JOURNAL_INVALID")
        if receipt.get("receipt_submitted") is not True:
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted += 1
    return submitted


def request_enrollment(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    server_url = _enrollment_server_origin(args.server_url)
    requested_target = {
        "server_url": server_url,
        "device_id": str(args.device_id or "").strip(),
        "endpoint_id": str(args.endpoint_id or "").strip(),
    }
    if (
        POLICY_IDENTIFIER_PATTERN.fullmatch(requested_target["device_id"]) is None
        or POLICY_IDENTIFIER_PATTERN.fullmatch(requested_target["endpoint_id"]) is None
        or not 1 <= len(str(args.display_name or "").strip()) <= 120
    ):
        raise RuntimeError("CONTROL_PLANE_ENROLLMENT_ARGUMENTS_INVALID")
    existing = _config(config_path) if config_path.exists() else None
    node_secret = ""
    prior_state: dict[str, Any] = {
        "enrollment_id": None,
        "enrollment_state": "unconfigured",
        "enrollment_observed_at_ms": None,
        "credential_generation": None,
        "enrollment_last_error": None,
    }
    if existing is not None:
        try:
            existing_target = {
                "server_url": _enrollment_server_origin(existing.get("server_url")),
                "device_id": str(existing.get("device_id") or "").strip(),
                "endpoint_id": str(existing.get("endpoint_id") or "").strip(),
            }
            existing_secret = str(existing.get("node_secret") or "")
        except RuntimeError as error:
            raise RuntimeError("CONTROL_PLANE_ENROLLMENT_CONFIG_INVALID") from error
        if existing_target != requested_target:
            if args.replace_existing_config is not True:
                raise RuntimeError("CONTROL_PLANE_ENROLLMENT_CONFIG_REPLACEMENT_REQUIRED")
            # A newly selected central target never inherits a credential that
            # was generated for another server/device/endpoint tuple.
            node_secret = secrets.token_urlsafe(32)
        elif len(existing_secret) < 16:
            raise RuntimeError("CONTROL_PLANE_ENROLLMENT_CONFIG_INVALID")
        else:
            node_secret = existing_secret
            prior_state = {
                key: existing.get(key, default)
                for key, default in prior_state.items()
            }
    if not node_secret:
        node_secret = secrets.token_urlsafe(32)
    config = {
        "schema_version": NODE_CONFIG_SCHEMA_VERSION,
        **requested_target,
        "display_name": args.display_name,
        "node_secret": node_secret,
        **prior_state,
        "enrollment_state": "request_sent",
        "enrollment_last_error": None,
    }
    # Write before sending so a loss after the server records the request is
    # retried with the same node credential and therefore stays idempotent.
    # Replacing an existing target requires the explicit CLI flag above.
    _write_config(config_path, config)
    try:
        response = _request(config["server_url"], "/v1/enrollment-requests", {
            "device_id": config["device_id"],
            "endpoint_id": config["endpoint_id"],
            "display_name": config["display_name"],
            "credential_hash": _credential_hash(node_secret),
        })
        projection = _enrollment_request_projection(response, config=config)
    except RuntimeError as error:
        config["enrollment_last_error"] = _safe_error_code(str(error), "CONTROL_PLANE_ENROLLMENT_REQUEST_FAILED")
        _write_config(config_path, config)
        raise
    _persist_enrollment_projection(config_path, config, projection)
    print(json.dumps({
        "enrollment_id": projection["enrollment_id"],
        "device_id": config["device_id"],
        "state": projection["state"],
    }, separators=(",", ":")))
    return 0


def reconcile_enrollment(args: argparse.Namespace) -> int:
    """Reconcile durable enrollment state after restart or a lost response.

    A transport failure returns the last persisted state with ``fresh=false``;
    it never turns stale approval into a new enrollment or silently grants
    execution.  A successful response updates the same config atomically.
    """

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(json.dumps({
            "device_id": str(args.device_id or ""), "enrollment_id": None, "state": "unconfigured",
            "credential_generation": None, "fresh": False, "observed_at_ms": None,
            "error_code": None, "server_origin": None,
        }, separators=(",", ":")))
        return 0
    config = _config(config_path)
    try:
        server_url = _enrollment_server_origin(config.get("server_url"))
        device_id = str(config.get("device_id") or "").strip()
        endpoint_id = str(config.get("endpoint_id") or "").strip()
        node_secret = str(config.get("node_secret") or "")
        if (POLICY_IDENTIFIER_PATTERN.fullmatch(device_id) is None
            or device_id != str(args.device_id or "").strip()
            or POLICY_IDENTIFIER_PATTERN.fullmatch(endpoint_id) is None
            or len(node_secret) < 16):
            raise RuntimeError("CONTROL_PLANE_ENROLLMENT_CONFIG_INVALID")
        response = _request(
            server_url,
            f"/v1/nodes/{device_id}/enrollment-status",
            {"enrollment_id": config.get("enrollment_id")},
            f"Node {node_secret}",
        )
        projection = _enrollment_status_projection(response, config=config)
    except RuntimeError as error:
        code = _safe_error_code(str(error), "CONTROL_PLANE_ENROLLMENT_RECONCILE_FAILED")
        print(json.dumps(_enrollment_local_status(config, fresh=False, error_code=code), separators=(",", ":")))
        return 0
    updated = _persist_enrollment_projection(config_path, config, projection)
    output = _enrollment_local_status(updated, fresh=True)
    output["enrollment_id"] = projection["enrollment_id"]
    output["state"] = projection["state"]
    output["credential_generation"] = projection["credential_generation"]
    output["observed_at_ms"] = projection["observed_at_ms"]
    output["error_code"] = None
    print(json.dumps(output, separators=(",", ":")))
    return 0


def reconcile_authority_status(args: argparse.Namespace) -> int:
    """Read the account/binding projection for Settings without granting authority."""

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        output = _authority_local_status(
            {"device_id": str(args.device_id or "")},
            fresh=False,
            error_code="CONTROL_PLANE_NODE_CONFIG_MISSING",
        )
        print(json.dumps(output, separators=(",", ":")))
        return 0
    config = _config(config_path)
    try:
        server_url = _enrollment_server_origin(config.get("server_url"))
        device_id = str(config.get("device_id") or "").strip()
        endpoint_id = str(config.get("endpoint_id") or "").strip()
        node_secret = str(config.get("node_secret") or "")
        if (
            POLICY_IDENTIFIER_PATTERN.fullmatch(device_id) is None
            or device_id != str(args.device_id or "").strip()
            or POLICY_IDENTIFIER_PATTERN.fullmatch(endpoint_id) is None
            or len(node_secret) < 16
        ):
            raise RuntimeError("CONTROL_PLANE_AUTHORITY_STATUS_CONFIG_INVALID")
        response = _request(
            server_url,
            f"/v1/nodes/{device_id}/authority-status",
            {},
            f"Node {node_secret}",
        )
        projection = _authority_status_projection(response, config=config)
    except RuntimeError as error:
        code = _safe_error_code(str(error), "CONTROL_PLANE_AUTHORITY_STATUS_FAILED")
        print(json.dumps(_authority_local_status(config, fresh=False, error_code=code), separators=(",", ":")))
        return 0
    output = {
        **projection,
        "fresh": True,
        "error_code": None,
    }
    print(json.dumps(output, separators=(",", ":")))
    return 0


def inspect_policy_authority(args: argparse.Namespace) -> int:
    """Resolve standing-policy metadata for exactly one selected local root.

    The enrolled node obtains the current owner and facade contract from
    Ubuntu. This installs no policy and returns neither a path nor credential.
    Local-registration checks bracket HTTP so a removed/replaced root cannot
    be promoted from stale UI data.
    """

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    workspace_id = _policy_identifier(args.workspace_id, "workspace_id")
    workspace_generation = _policy_identifier(args.workspace_generation, "workspace_generation")
    _require_current_local_workspace_registration(
        args, config_path=config_path,
        workspace_id=workspace_id, workspace_generation=workspace_generation,
    )
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/policy-authority",
        {"workspace_id": workspace_id, "workspace_generation": workspace_generation},
        f"Node {config['node_secret']}",
    )
    expected = {
        "owner_id", "device_id", "endpoint_id", "workspace_id",
        "workspace_generation", "facade_contract", "binding_count",
        "standing_write_enabled", "observed_at_ms",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_POLICY_AUTHORITY_INVALID")
    if (
        response["device_id"] != config["device_id"]
        or response["endpoint_id"] != config["endpoint_id"]
        or response["workspace_id"] != workspace_id
        or response["workspace_generation"] != workspace_generation
    ):
        raise RuntimeError("CONTROL_PLANE_POLICY_AUTHORITY_TARGET_MISMATCH")
    binding_count = response["binding_count"]
    standing_write_enabled = response["standing_write_enabled"]
    observed_at_ms = response["observed_at_ms"]
    if (
        not isinstance(binding_count, int) or isinstance(binding_count, bool) or binding_count < 1
        or not isinstance(standing_write_enabled, bool)
        or not isinstance(observed_at_ms, int) or isinstance(observed_at_ms, bool) or observed_at_ms <= 0
    ):
        raise RuntimeError("CONTROL_PLANE_POLICY_AUTHORITY_INVALID")
    owner_id = _policy_identifier(response["owner_id"], "owner_id")
    contract = response["facade_contract"]
    if not isinstance(contract, dict) or set(contract) != {"schema_version", "profile", "sha256"}:
        raise RuntimeError("CONTROL_PLANE_POLICY_AUTHORITY_INVALID")
    facade_contract = _policy_facade_contract(
        contract["schema_version"], contract["profile"], contract["sha256"],
    )
    _require_current_local_workspace_registration(
        args, config_path=config_path,
        workspace_id=workspace_id, workspace_generation=workspace_generation,
    )
    print(json.dumps({
        "operation": "control_plane_policy_authority_observation",
        "owner_id": owner_id,
        "workspace_id": workspace_id,
        "workspace_generation": workspace_generation,
        "facade_contract": facade_contract,
        "binding_count": binding_count,
        "standing_write_enabled": standing_write_enabled,
        "observed_at_ms": observed_at_ms,
        "runtime_mode": _runtime_mode(args),
    }, separators=(",", ":")))
    return 0


def _workspace_capabilities(value: Any) -> dict[str, bool]:
    """Accept exactly the small local inventory that C2 can register.

    This is deliberately an inventory, not a task grant.  In particular, a
    true ``write`` or ``exec`` value cannot turn into remote authority until a
    later action/policy boundary has been implemented and approved.
    """

    if not isinstance(value, dict) or set(value) != {"read", "write", "exec"}:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_CAPABILITIES_INVALID")
    normalized: dict[str, bool] = {}
    for name in ("read", "write", "exec"):
        enabled = value.get(name)
        if not isinstance(enabled, bool):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_CAPABILITIES_INVALID")
        normalized[name] = enabled
    if not normalized["read"]:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_READ_REQUIRED")
    return normalized


def _workspace_display_name(value: Any) -> str:
    display_name = str(value or "").strip()
    if not 1 <= len(display_name) <= 120 or any(ord(character) < 32 for character in display_name):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_DISPLAY_NAME_INVALID")
    return display_name


def _canonical_workspace_root(value: Any) -> str:
    """Resolve exactly one existing local directory before it enters a registry.

    The returned path is persisted only in the node-local registry.  The
    central request below intentionally sends neither this path nor a digest
    that could be used to correlate the node's filesystem layout.
    """

    raw = str(value or "")
    if not raw or "\x00" in raw or len(raw) > WORKSPACE_REGISTRY_PATH_MAX_CHARS:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_PATH_INVALID")
    try:
        root = Path(raw).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_PATH_INVALID") from error
    try:
        if not root.is_dir():
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_PATH_INVALID")
    except OSError as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_PATH_INVALID") from error
    canonical = str(root)
    if not canonical or len(canonical) > WORKSPACE_REGISTRY_PATH_MAX_CHARS:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_PATH_INVALID")
    return canonical


def _workspace_registry_path(args: argparse.Namespace, config_path: Path) -> Path:
    raw = str(getattr(args, "workspace_registry", "") or "").strip()
    if not raw:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_PATH_INVALID")
    try:
        path = Path(raw).expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_PATH_INVALID") from error
    # The Electron main process selects this fixed sibling path.  Refusing a
    # caller-provided arbitrary directory prevents this narrow helper from
    # becoming a generic local file writer when invoked outside the UI.
    if path.parent != config_path.parent:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_PATH_INVALID")
    return path


def _workspace_replacement_journal_path(config_path: Path) -> Path:
    """Return the same-user, sibling journal used by replacement retries.

    The journal contains only opaque IDs, a local path and the selected
    capability shape.  It is intentionally kept beside the node config so a
    crash between the central retire/register boundaries can resume without
    another credential or a renderer-supplied context.
    """

    return config_path.with_name(f"{config_path.name}.{WORKSPACE_REPLACEMENT_FILE_NAME}")


def _workspace_replacement_record(value: Any) -> dict[str, Any]:
    expected = {
        "schema_version", "phase", "device_id", "workspace_id",
        "old_workspace_generation", "new_workspace_generation",
        "old_display_name", "old_capabilities", "canonical_path",
        "display_name", "capabilities", "created_at_ms",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    if value.get("schema_version") != WORKSPACE_REPLACEMENT_SCHEMA_VERSION:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    phase = value.get("phase")
    if phase not in WORKSPACE_REPLACEMENT_PHASES:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    canonical_path = str(value.get("canonical_path") or "")
    if not canonical_path or len(canonical_path) > WORKSPACE_REGISTRY_PATH_MAX_CHARS:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    try:
        if not Path(canonical_path).is_absolute():
            raise ValueError("not absolute")
    except (OSError, ValueError):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID") from None
    created_at_ms = value.get("created_at_ms")
    if not isinstance(created_at_ms, int) or isinstance(created_at_ms, bool) or created_at_ms <= 0:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    return {
        "schema_version": WORKSPACE_REPLACEMENT_SCHEMA_VERSION,
        "phase": phase,
        "device_id": _policy_identifier(value.get("device_id"), "device_id"),
        "workspace_id": _policy_identifier(value.get("workspace_id"), "workspace_id"),
        "old_workspace_generation": _policy_identifier(value.get("old_workspace_generation"), "old_workspace_generation"),
        "new_workspace_generation": _policy_identifier(value.get("new_workspace_generation"), "new_workspace_generation"),
        "old_display_name": _workspace_display_name(value.get("old_display_name")),
        "old_capabilities": _workspace_capabilities(value.get("old_capabilities")),
        "canonical_path": canonical_path,
        "display_name": _workspace_display_name(value.get("display_name")),
        "capabilities": _workspace_capabilities(value.get("capabilities")),
        "created_at_ms": created_at_ms,
    }


def _read_workspace_replacement_journal(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_UNAVAILABLE") from error
    if len(raw) > WORKSPACE_REPLACEMENT_MAX_BYTES:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_JOURNAL_INVALID") from error
    return _workspace_replacement_record(value)


def _workspace_registry_entry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "workspace_id", "workspace_generation", "canonical_path", "display_name", "capabilities", "created_at_ms",
    }:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    workspace_id = _policy_identifier(value.get("workspace_id"), "workspace_id")
    workspace_generation = _policy_identifier(value.get("workspace_generation"), "workspace_generation")
    canonical_path = str(value.get("canonical_path") or "")
    if not canonical_path or len(canonical_path) > WORKSPACE_REGISTRY_PATH_MAX_CHARS:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    try:
        path = Path(canonical_path)
        if not path.is_absolute():
            raise ValueError("not absolute")
    except (OSError, ValueError):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID") from None
    created_at_ms = value.get("created_at_ms")
    if not isinstance(created_at_ms, int) or isinstance(created_at_ms, bool) or created_at_ms <= 0:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    return {
        "workspace_id": workspace_id,
        "workspace_generation": workspace_generation,
        "canonical_path": canonical_path,
        "display_name": _workspace_display_name(value.get("display_name")),
        "capabilities": _workspace_capabilities(value.get("capabilities")),
        "created_at_ms": created_at_ms,
    }


def _read_workspace_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": WORKSPACE_REGISTRY_SCHEMA_VERSION, "entries": []}
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_UNAVAILABLE") from error
    if len(raw) > WORKSPACE_REGISTRY_MAX_BYTES:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID") from error
    if (
        not isinstance(parsed, dict)
        or set(parsed) != {"schema_version", "entries"}
        or parsed.get("schema_version") != WORKSPACE_REGISTRY_SCHEMA_VERSION
        or not isinstance(parsed.get("entries"), list)
        or len(parsed["entries"]) > WORKSPACE_REGISTRY_MAX_ENTRIES
    ):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    entries = [_workspace_registry_entry(entry) for entry in parsed["entries"]]
    paths = [entry["canonical_path"] for entry in entries]
    identities = [(entry["workspace_id"], entry["workspace_generation"]) for entry in entries]
    if len(paths) != len(set(paths)) or len(identities) != len(set(identities)):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_INVALID")
    return {"schema_version": WORKSPACE_REGISTRY_SCHEMA_VERSION, "entries": entries}


def _workspace_registration_response(
    response: Any,
    *,
    config: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "device_id", "workspace_id", "workspace_generation", "display_name", "capabilities",
        "registered_at_ms", "retired_at_ms", "replayed",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_RESPONSE_INVALID")
    if (
        response.get("device_id") != config.get("device_id")
        or response.get("workspace_id") != entry["workspace_id"]
        or response.get("workspace_generation") != entry["workspace_generation"]
        or response.get("display_name") != entry["display_name"]
        or response.get("capabilities") != entry["capabilities"]
        or response.get("retired_at_ms") is not None
        or not isinstance(response.get("registered_at_ms"), int)
        or isinstance(response.get("registered_at_ms"), bool)
        or response.get("registered_at_ms") <= 0
        or not isinstance(response.get("replayed"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_RESPONSE_INVALID")
    return {
        "workspace_id": entry["workspace_id"],
        "workspace_generation": entry["workspace_generation"],
        "display_name": entry["display_name"],
        "capabilities": entry["capabilities"],
        "replayed": response["replayed"],
    }


def _registered_workspace_entry(
    registry: dict[str, Any],
    *,
    workspace_id: Any,
    workspace_generation: Any,
) -> dict[str, Any]:
    """Resolve one opaque local registration without exposing its path.

    The central service is authoritative for retirement, while this private
    registry is authoritative for which local root an installed node is still
    willing to use. IDs supplied by an Electron renderer are therefore only
    selectors for an exact pre-existing local entry; they cannot create a new
    local root or redirect an existing one.
    """

    normalized_id = _policy_identifier(workspace_id, "workspace_id")
    normalized_generation = _policy_identifier(workspace_generation, "workspace_generation")
    entry = next(
        (
            item
            for item in registry["entries"]
            if item["workspace_id"] == normalized_id
            and item["workspace_generation"] == normalized_generation
        ),
        None,
    )
    if entry is None:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return entry


def _require_current_local_workspace_registration(
    args: argparse.Namespace,
    *,
    config_path: Path,
    workspace_id: Any,
    workspace_generation: Any,
) -> dict[str, Any]:
    """Require a still-present local root before installing a context policy.

    Ubuntu already checks the central registration when it issues a live
    context template. The node must independently verify that its private
    registry still contains that exact generation and that the resolved local
    filesystem root has not disappeared or changed since registration. This
    closes the gap where an old context could otherwise install a policy after
    its local root was removed or replaced.
    """

    registry_path = _workspace_registry_path(args, config_path)
    registry = _read_workspace_registry(registry_path)
    entry = _registered_workspace_entry(
        registry,
        workspace_id=workspace_id,
        workspace_generation=workspace_generation,
    )
    try:
        current_path = _canonical_workspace_root(entry["canonical_path"])
    except RuntimeError as error:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT") from error
    if current_path != entry["canonical_path"]:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return entry


def _require_policy_workspace_registration(
    args: argparse.Namespace,
    *,
    config_path: Path,
    policy: dict[str, Any],
) -> dict[str, Any] | None:
    """Bind a local execution policy to a current private workspace entry.

    Every CLI execution entrypoint now requires ``--workspace-registry``. The
    omitted-attribute branch is retained only for in-process legacy fixtures
    that call internal functions directly rather than a parser-owned command;
    it is not reachable from the installed supervisor or command line.
    """

    if not hasattr(args, "workspace_registry"):
        return None
    if not str(getattr(args, "workspace_registry", "") or "").strip():
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED")
    return _require_current_local_workspace_registration(
        args,
        config_path=config_path,
        workspace_id=policy["workspace_id"],
        workspace_generation=policy["workspace_generation"],
    )


def _workspace_retirement_response(
    response: Any,
    *,
    config: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    """Accept only the exact central retirement receipt before deleting local state."""

    expected = {
        "device_id", "workspace_id", "workspace_generation", "display_name", "capabilities",
        "registered_at_ms", "retired_at_ms", "replayed",
    }
    if not isinstance(response, dict) or set(response) != expected:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_RETIRE_RESPONSE_INVALID")
    retired_at_ms = response.get("retired_at_ms")
    if (
        response.get("device_id") != config.get("device_id")
        or response.get("workspace_id") != entry["workspace_id"]
        or response.get("workspace_generation") != entry["workspace_generation"]
        or response.get("display_name") != entry["display_name"]
        or response.get("capabilities") != entry["capabilities"]
        or not isinstance(response.get("registered_at_ms"), int)
        or isinstance(response.get("registered_at_ms"), bool)
        or response.get("registered_at_ms") <= 0
        or not isinstance(retired_at_ms, int)
        or isinstance(retired_at_ms, bool)
        or retired_at_ms <= 0
        or not isinstance(response.get("replayed"), bool)
    ):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_RETIRE_RESPONSE_INVALID")
    return {
        "workspace_id": entry["workspace_id"],
        "workspace_generation": entry["workspace_generation"],
        "display_name": entry["display_name"],
        "capabilities": entry["capabilities"],
        "replayed": response["replayed"],
    }


def _disable_matching_retired_workspace_policy(args: argparse.Namespace, entry: dict[str, Any]) -> bool:
    """Disable a matching local policy after central retirement is durable.

    Deleting the registry alone must not leave an enabled local policy that
    still describes the retired generation. Missing, malformed or already
    disabled policy files are fail-closed and therefore need no rewrite. A
    valid matching enabled policy is retained as disabled evidence, just like
    the explicit local disable command.
    """

    try:
        policy_path = _read_only_policy_path(args)
    except RuntimeError:
        # Development diagnostics without a data root have no fixed policy
        # profile to inspect. Packaged callers derive one from APPDATA.
        if _runtime_mode(args) == "development":
            return False
        raise
    try:
        policy = _read_local_policy(policy_path)
    except RuntimeError as error:
        if str(error) in {
            "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
            "CONTROL_PLANE_BRIDGE_POLICY_INVALID",
        }:
            return False
        raise
    if (
        policy["workspace_id"] != entry["workspace_id"]
        or policy["workspace_generation"] != entry["workspace_generation"]
        or policy["enabled"] is not True
    ):
        return False
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    return True


def _disable_matching_retired_workspace_file_read_policy(args: argparse.Namespace, entry: dict[str, Any]) -> bool:
    """Fail closed for C3 when a locally registered workspace is retired.

    The bounded file-read policy is intentionally independent from the legacy
    compact-metadata policy.  Retiring a root must therefore disable both
    policy files rather than leave the newer content lane live because an old
    helper only knew about the metadata profile.
    """

    try:
        policy_path = _file_read_policy_path(args)
    except RuntimeError:
        if _runtime_mode(args) == "development":
            return False
        raise
    try:
        policy = _read_file_read_policy(policy_path)
    except RuntimeError as error:
        if str(error) in {
            "CONTROL_PLANE_FILE_READ_POLICY_MISSING",
            "CONTROL_PLANE_FILE_READ_POLICY_INVALID",
        }:
            return False
        raise
    if (
        policy["workspace_id"] != entry["workspace_id"]
        or policy["workspace_generation"] != entry["workspace_generation"]
        or policy["enabled"] is not True
    ):
        return False
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    return True


def _disable_matching_retired_workspace_approved_patch_policy(args: argparse.Namespace, entry: dict[str, Any]) -> bool:
    """Revoke C4 exact-patch authority before a retired root is forgotten."""

    try:
        policy_path = _approved_patch_policy_path(args)
    except RuntimeError:
        if _runtime_mode(args) == "development":
            return False
        raise
    try:
        policy = _read_approved_patch_policy(policy_path)
    except RuntimeError as error:
        if str(error) in {
            "CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING",
            "CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID",
        }:
            return False
        raise
    if (
        policy["workspace_id"] != entry["workspace_id"]
        or policy["workspace_generation"] != entry["workspace_generation"]
        or policy["enabled"] is not True
    ):
        return False
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    return True


def _disable_matching_retired_workspace_exec_policy(args: argparse.Namespace, entry: dict[str, Any]) -> bool:
    """Disable standing exec authority bound to a retired generation."""

    try:
        policy_path = _exec_policy_path(args)
    except RuntimeError:
        if _runtime_mode(args) == "development":
            return False
        raise
    try:
        policy = _read_exec_policy(policy_path)
    except RuntimeError as error:
        if str(error) in {
            "CONTROL_PLANE_EXEC_POLICY_MISSING",
            "CONTROL_PLANE_EXEC_POLICY_INVALID",
            "CONTROL_PLANE_EXEC_POLICY_EXPIRED",
        }:
            return False
        raise
    if (
        policy["workspace_id"] != entry["workspace_id"]
        or policy["workspace_generation"] != entry["workspace_generation"]
        or policy["enabled"] is not True
    ):
        return False
    policy["enabled"] = False
    _write_local_policy(policy_path, policy, replace=True)
    return True


def list_workspaces(args: argparse.Namespace) -> int:
    """List only path-free local workspace inventory for the Electron UI."""

    config_path = Path(args.config).expanduser().resolve()
    # Require the installed node profile even though this command makes no
    # network call. A stray JSON file outside that profile must not become a
    # second user-visible workspace registry.
    _config(config_path)
    registry = _read_workspace_registry(_workspace_registry_path(args, config_path))
    workspaces = [
        {
            key: entry[key]
            for key in ("workspace_id", "workspace_generation", "display_name", "capabilities")
        }
        for entry in registry["entries"]
    ]
    print(json.dumps({"workspaces": workspaces}, separators=(",", ":")))
    return 0


def retire_workspace(args: argparse.Namespace) -> int:
    """Retire a local root only after Ubuntu confirms the exact generation.

    A network error deliberately leaves the local registry unchanged. The next
    invocation reuses the same opaque ID/generation; if Ubuntu committed the
    first request but the response was lost, its idempotent replay receipt
    authorizes this node to remove the entry safely.
    """

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    registry_path = _workspace_registry_path(args, config_path)
    registry = _read_workspace_registry(registry_path)
    entry = _registered_workspace_entry(
        registry,
        workspace_id=args.workspace_id,
        workspace_generation=args.workspace_generation,
    )
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/workspace-registrations/retire",
        {
            "workspace_id": entry["workspace_id"],
            "workspace_generation": entry["workspace_generation"],
        },
        f"Node {config['node_secret']}",
    )
    receipt = _workspace_retirement_response(response, config=config, entry=entry)
    _disable_matching_retired_workspace_policy(args, entry)
    _disable_matching_retired_workspace_file_read_policy(args, entry)
    _disable_matching_retired_workspace_approved_patch_policy(args, entry)
    _disable_matching_retired_workspace_exec_policy(args, entry)
    registry["entries"] = [
        item
        for item in registry["entries"]
        if not (
            item["workspace_id"] == entry["workspace_id"]
            and item["workspace_generation"] == entry["workspace_generation"]
        )
    ]
    _write_json_atomic(registry_path, registry)
    print(json.dumps({**receipt, "state": "retired"}, separators=(",", ":")))
    return 0


def _workspace_replacement_output(
    *,
    config: dict[str, Any],
    journal: dict[str, Any],
    replayed: bool,
) -> dict[str, Any]:
    return {
        "workspace_id": journal["workspace_id"],
        "old_workspace_generation": journal["old_workspace_generation"],
        "workspace_generation": journal["new_workspace_generation"],
        "display_name": journal["display_name"],
        "capabilities": journal["capabilities"],
        "replayed": bool(replayed),
        "state": "replaced",
    }


def _replace_local_workspace_registry_entry(
    registry_path: Path,
    *,
    journal: dict[str, Any],
    old_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Commit the new generation only after central registration is durable."""

    registry = _read_workspace_registry(registry_path)
    old_identity = (journal["workspace_id"], journal["old_workspace_generation"])
    new_identity = (journal["workspace_id"], journal["new_workspace_generation"])
    current_old = next(
        (
            item for item in registry["entries"]
            if (item["workspace_id"], item["workspace_generation"]) == old_identity
        ),
        None,
    )
    current_new = next(
        (
            item for item in registry["entries"]
            if (item["workspace_id"], item["workspace_generation"]) == new_identity
        ),
        None,
    )
    if old_entry is not None and current_old is not None:
        if (
            current_old["canonical_path"] != old_entry["canonical_path"]
            or current_old["display_name"] != journal["old_display_name"]
            or current_old["capabilities"] != journal["old_capabilities"]
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")
    if current_new is not None:
        if (
            current_new["canonical_path"] != journal["canonical_path"]
            or current_new["display_name"] != journal["display_name"]
            or current_new["capabilities"] != journal["capabilities"]
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")
        # A retry after the final local write is idempotent.  Remove any stale
        # old entry below, but do not rewrite the validated new entry.
        replacement = current_new
    else:
        if current_old is None and old_entry is not None:
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")
        if any(
            item["canonical_path"] == journal["canonical_path"]
            and (item["workspace_id"], item["workspace_generation"]) != old_identity
            for item in registry["entries"]
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")
        replacement = {
            "workspace_id": journal["workspace_id"],
            "workspace_generation": journal["new_workspace_generation"],
            "canonical_path": journal["canonical_path"],
            "display_name": journal["display_name"],
            "capabilities": journal["capabilities"],
            "created_at_ms": int(time.time() * 1000),
        }
    entries = [
        item for item in registry["entries"]
        if (item["workspace_id"], item["workspace_generation"]) not in {old_identity, new_identity}
    ]
    entries.append(replacement)
    if len(entries) > WORKSPACE_REGISTRY_MAX_ENTRIES:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_FULL")
    _write_json_atomic(registry_path, {"schema_version": WORKSPACE_REGISTRY_SCHEMA_VERSION, "entries": entries})
    return replacement


def replace_workspace(args: argparse.Namespace) -> int:
    """Replace a registered root's capability/label without silent overwrite.

    The central retirement is committed first.  A small local journal then
    makes a crash between retirement and registration resume the same opaque
    workspace ID/generation transition instead of creating a duplicate root.
    """

    if getattr(args, "confirm_replace", False) is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    registry_path = _workspace_registry_path(args, config_path)
    canonical_path = _canonical_workspace_root(args.workspace_path)
    display_name = _workspace_display_name(args.display_name)
    capabilities = _workspace_capabilities({
        "read": getattr(args, "capability_read", False) is True,
        "write": getattr(args, "capability_write", False) is True,
        "exec": getattr(args, "capability_exec", False) is True,
    })
    journal_path = _workspace_replacement_journal_path(config_path)
    journal = _read_workspace_replacement_journal(journal_path)
    resumed = journal is not None
    registry = _read_workspace_registry(registry_path)
    expected_workspace_id = getattr(args, "expected_workspace_id", None)
    expected_workspace_generation = getattr(args, "expected_workspace_generation", None)
    if (expected_workspace_id is None) != (expected_workspace_generation is None):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_EXPECTED_TARGET_INVALID")
    if expected_workspace_id is not None:
        expected_workspace_id = _policy_identifier(expected_workspace_id, "workspace_id")
        expected_workspace_generation = _policy_identifier(expected_workspace_generation, "workspace_generation")
    if journal is None:
        old_entry = next(
            (item for item in registry["entries"] if item["canonical_path"] == canonical_path),
            None,
        )
        if old_entry is None:
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_NOT_FOUND")
        if expected_workspace_id is not None and (
            old_entry["workspace_id"] != expected_workspace_id
            or old_entry["workspace_generation"] != expected_workspace_generation
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_EXPECTED_TARGET_MISMATCH")
        if old_entry["display_name"] == display_name and old_entry["capabilities"] == capabilities:
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_NO_CHANGE")
        journal = {
            "schema_version": WORKSPACE_REPLACEMENT_SCHEMA_VERSION,
            "phase": "planned",
            "device_id": config["device_id"],
            "workspace_id": old_entry["workspace_id"],
            "old_workspace_generation": old_entry["workspace_generation"],
            "new_workspace_generation": f"generation_{uuid.uuid4().hex}",
            "old_display_name": old_entry["display_name"],
            "old_capabilities": old_entry["capabilities"],
            "canonical_path": canonical_path,
            "display_name": display_name,
            "capabilities": capabilities,
            "created_at_ms": int(time.time() * 1000),
        }
        journal = _workspace_replacement_record(journal)
        _write_json_atomic(journal_path, journal)
    else:
        if expected_workspace_id is not None and (
            journal["workspace_id"] != expected_workspace_id
            or journal["old_workspace_generation"] != expected_workspace_generation
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_EXPECTED_TARGET_MISMATCH")
        if (
            journal["device_id"] != config["device_id"]
            or journal["canonical_path"] != canonical_path
            or journal["display_name"] != display_name
            or journal["capabilities"] != capabilities
        ):
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_IN_PROGRESS")
        old_entry = next(
            (
                item for item in registry["entries"]
                if item["workspace_id"] == journal["workspace_id"]
                and item["workspace_generation"] == journal["old_workspace_generation"]
            ),
            None,
        )
        new_entry = next(
            (
                item for item in registry["entries"]
                if item["workspace_id"] == journal["workspace_id"]
                and item["workspace_generation"] == journal["new_workspace_generation"]
            ),
            None,
        )
        if old_entry is None and new_entry is not None:
            _workspace_replacement_journal_path(config_path).unlink(missing_ok=True)
            print(json.dumps(_workspace_replacement_output(config=config, journal=journal, replayed=True), separators=(",", ":")))
            return 0
        if old_entry is None:
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")

    if (
        old_entry["canonical_path"] != journal["canonical_path"]
        or old_entry["display_name"] != journal["old_display_name"]
        or old_entry["capabilities"] != journal["old_capabilities"]
    ):
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REPLACEMENT_REGISTRY_CONFLICT")
    if journal["phase"] in {"planned", "retire_sent"}:
        journal = _workspace_replacement_record({**journal, "phase": "retire_sent"})
        _write_json_atomic(journal_path, journal)
        response = _request(
            str(config["server_url"]),
            f"/v1/nodes/{config['device_id']}/workspace-registrations/retire",
            {
                "workspace_id": journal["workspace_id"],
                "workspace_generation": journal["old_workspace_generation"],
            },
            f"Node {config['node_secret']}",
        )
        _workspace_retirement_response(response, config=config, entry=old_entry)
        journal = _workspace_replacement_record({**journal, "phase": "retired"})
        _write_json_atomic(journal_path, journal)

    # Central retirement is now durable; revoke every local policy family
    # before the new generation can be registered in the local registry.
    _disable_matching_retired_workspace_policy(args, old_entry)
    _disable_matching_retired_workspace_file_read_policy(args, old_entry)
    _disable_matching_retired_workspace_approved_patch_policy(args, old_entry)
    _disable_matching_retired_workspace_exec_policy(args, old_entry)

    new_entry = {
        "workspace_id": journal["workspace_id"],
        "workspace_generation": journal["new_workspace_generation"],
        "canonical_path": journal["canonical_path"],
        "display_name": journal["display_name"],
        "capabilities": journal["capabilities"],
        "created_at_ms": journal["created_at_ms"],
    }
    if journal["phase"] != "register_sent":
        journal = _workspace_replacement_record({**journal, "phase": "register_sent"})
        _write_json_atomic(journal_path, journal)
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/workspace-registrations",
        {
            "workspace_id": new_entry["workspace_id"],
            "workspace_generation": new_entry["workspace_generation"],
            "display_name": new_entry["display_name"],
            "capabilities": new_entry["capabilities"],
        },
        f"Node {config['node_secret']}",
    )
    registration = _workspace_registration_response(response, config=config, entry=new_entry)
    _replace_local_workspace_registry_entry(registry_path, journal=journal, old_entry=old_entry)
    journal_path.unlink(missing_ok=True)
    replayed = resumed or bool(registration.get("replayed"))
    print(json.dumps(_workspace_replacement_output(config=config, journal=journal, replayed=replayed), separators=(",", ":")))
    return 0


def register_workspace(args: argparse.Namespace) -> int:
    """Register one locally canonicalized root without disclosing its path.

    Persist the local opaque identity before the network call.  A response loss
    can therefore retry the exact same identity/generation rather than create
    a second workspace record or accidentally rebind a target.
    """

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    registry_path = _workspace_registry_path(args, config_path)
    canonical_path = _canonical_workspace_root(args.workspace_path)
    display_name = _workspace_display_name(args.display_name)
    capabilities = _workspace_capabilities({
        "read": getattr(args, "capability_read", False) is True,
        "write": getattr(args, "capability_write", False) is True,
        "exec": getattr(args, "capability_exec", False) is True,
    })
    registry = _read_workspace_registry(registry_path)
    entry = next((item for item in registry["entries"] if item["canonical_path"] == canonical_path), None)
    if entry is None:
        if len(registry["entries"]) >= WORKSPACE_REGISTRY_MAX_ENTRIES:
            raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRY_FULL")
        entry = {
            "workspace_id": f"workspace_{uuid.uuid4().hex}",
            "workspace_generation": f"generation_{uuid.uuid4().hex}",
            "canonical_path": canonical_path,
            "display_name": display_name,
            "capabilities": capabilities,
            "created_at_ms": int(time.time() * 1000),
        }
        registry["entries"].append(entry)
        _write_json_atomic(registry_path, registry)
    elif entry["display_name"] != display_name or entry["capabilities"] != capabilities:
        # A changed capability/label is a new central generation.  Do not
        # overwrite a server-visible identity after a response loss; force a
        # deliberate later replace/retire path instead.
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_REPLACEMENT_REQUIRED")
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/workspace-registrations",
        {
            "workspace_id": entry["workspace_id"],
            "workspace_generation": entry["workspace_generation"],
            "display_name": entry["display_name"],
            "capabilities": entry["capabilities"],
        },
        f"Node {config['node_secret']}",
    )
    receipt = _workspace_registration_response(response, config=config, entry=entry)
    print(json.dumps({**receipt, "state": "registered"}, separators=(",", ":")))
    return 0


def heartbeat(args: argparse.Namespace) -> int:
    config = _config(Path(args.config).expanduser().resolve())
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/heartbeat", {
        "endpoint_id": config["endpoint_id"],
        "runtime_instance_id": args.runtime_instance_id,
        "mcp_server_instance_id": args.mcp_server_instance_id,
        "activation_epoch": args.activation_epoch,
        "contract_version": args.contract_version,
        "readiness": args.readiness,
    }, f"Node {config['node_secret']}")
    print(json.dumps({"device_id": response.get("device_id"), "readiness": response.get("readiness"), "last_seen_at_ms": response.get("last_seen_at_ms")}, separators=(",", ":")))
    return 0


def runtime_heartbeat(args: argparse.Namespace) -> int:
    """Publish a conservative read-only projection of the local Execution Hub.

    This is intentionally a one-shot command.  A platform scheduler may invoke
    it after user login, but it must not be presented as a Windows service or
    as proof that an interactive Electron/runtime can survive logged-out state.
    """
    project_root = Path(args.project_root).expanduser().resolve()
    status = _runtime_status(args, project_root)
    # Do not open the authenticated local IPC read unless the independent
    # aggregate predicate is already strict.  A degraded Hub must remain
    # degraded without probing for a more attractive identity.
    observation = recovery_identity_observation(args, project_root) if runtime_readiness(status)[0] == "ready" else None
    projection = runtime_heartbeat_projection(status, observation)
    config = _config(Path(args.config).expanduser().resolve())
    policy_observation = read_only_policy_observation(args, config)
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/heartbeat", {
        "endpoint_id": config["endpoint_id"],
        "runtime_instance_id": projection["runtime_instance_id"],
        "mcp_server_instance_id": projection["mcp_server_instance_id"],
        "activation_epoch": projection["activation_epoch"],
        "contract_version": projection["contract_version"],
        "readiness": projection["readiness"],
        "policy_observation": policy_observation,
    }, f"Node {config['node_secret']}")
    route_evidence = _route_evidence_from_heartbeat(config, response, projection, policy_observation)
    _write_json_atomic(_route_evidence_path(args), route_evidence)
    print(json.dumps({
        "device_id": response.get("device_id"),
        "readiness": response.get("readiness"),
        "reason": projection["reason"],
        "runtime_identity": "reported" if projection["runtime_instance_id"] != "unreported" else "unreported",
        "runtime_state": status.get("state", "unknown"),
        "fully_ready": status.get("fully_ready", "unknown"),
        "policy_state": policy_observation["state"],
        "route_evidence": "fresh",
    }, separators=(",", ":")))
    return 0


def poll(args: argparse.Namespace) -> int:
    # A central poll allocates an exact delivery attempt before it responds.
    # This legacy command has no receipt-producing execution lane, so it must
    # not dequeue work merely to report that execution is unsupported.
    _config(Path(args.config).expanduser().resolve())
    print(json.dumps({
        "received_action_ids": [],
        "execution": "not_implemented",
        "code": "POLL_EXECUTION_DISABLED",
    }, separators=(",", ":")))
    return 0


def _record_local_receipt(
    journal_path: Path,
    journal: dict[str, Any],
    *,
    state: str,
    action_id: str,
    attempt_id: str,
    receipt_state: str,
    local_handle: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    key = _journal_key(action_id, attempt_id)
    entry = {
        "state": state,
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt": _journal_receipt(action_id, attempt_id, receipt_state, local_handle, payload),
    }
    journal["entries"][key] = entry
    _write_json_atomic(journal_path, journal)
    return entry


def _poll_read_only_once(args: argparse.Namespace) -> int:
    """Run the only admitted execution lane once, with durable no-retry evidence.

    This function intentionally does not extend ``poll``. Operators must name
    the read-only lane explicitly, and a current strict Hub plus exact Recovery
    identity are checked before the node even asks the central queue for work.
    """
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _journal_path(config_path)
    journal = _read_journal(journal_path)
    submitted_receipts = _flush_journal(config, journal_path, journal)

    project_root = Path(args.project_root).expanduser().resolve()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({
            "execution": "not_started",
            "reason": reason,
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({
            "execution": "not_started",
            "reason": "runtime_identity_unproven",
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0

    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/poll",
        {"limit": args.limit},
        f"Node {config['node_secret']}",
    )
    actions = response.get("actions")
    if not isinstance(actions, list):
        raise RuntimeError("invalid_server_response")

    completed: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_BRIDGE_ACTION_DENIED")
        # The central store has already allocated these fields before emitting
        # any action. If they are malformed here, no safe receipt can bind it.
        action_id = _action_text(action, "action_id")
        attempt_id = _action_text(action, "attempt_id")
        received.append(action_id)
        key = _journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            # A duplicate local invocation must only replay its durable receipt.
            submitted_receipts += _flush_journal(config, journal_path, journal)
            continue
        try:
            request = _read_only_bridge_request(action, config)
            _require_policy_workspace_registration(
                args,
                config_path=config_path,
                policy={
                    "workspace_id": request["workspace_id"],
                    "workspace_generation": request["workspace_generation"],
                },
            )
        except RuntimeError as error:
            code = _safe_error_code(error)
            entry = _record_local_receipt(
                journal_path,
                journal,
                state="rejected",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_read_only_workspace_context",
                    "code": code,
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue

        # Persist before subprocess launch. An interruption after this point is
        # intentionally reconciled as unknown rather than replaying a possibly
        # completed local workspace read.
        journal["entries"][key] = {
            "state": "prepared",
            "action_id": action_id,
            "attempt_id": attempt_id,
        }
        _write_json_atomic(journal_path, journal)
        try:
            try:
                result, error_code = recovery_read_only_bridge(args, project_root, request)
            except Exception:
                # The durable prepared marker may already cover an indeterminate
                # local effect. Convert an unexpected bridge-wrapper failure into
                # the same no-retry UNKNOWN receipt instead of terminating the
                # long-lived worker without any typed diagnostic.
                result, error_code = None, "CONTROL_PLANE_BRIDGE_AGENT_EXCEPTION"
            if result is not None:
                entry = _record_local_receipt(
                    journal_path,
                    journal,
                    state="completed",
                    action_id=action_id,
                    attempt_id=attempt_id,
                    receipt_state="completed",
                    local_handle=str(result["local_handle"]),
                    payload=_safe_bridge_result(result, request),
                )
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted_receipts += 1
                completed.append(action_id)
                continue

            code = _safe_error_code(error_code)
            pre_effect = code in PRE_EFFECT_REJECTION_CODES
            entry = _record_local_receipt(
                journal_path,
                journal,
                state="rejected" if pre_effect else "unknown",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected" if pre_effect else "unknown",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_read_only_workspace_context",
                    "code": code if pre_effect else "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
                    # Preserve the typed, allowlisted local failure as diagnostic
                    # evidence without changing UNKNOWN's no-retry semantics or
                    # putting process output/workspace data in the receipt.
                    **({} if pre_effect else {"diagnostic_code": code}),
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            (rejected if pre_effect else unknown).append(action_id)
        except Exception as error:
            # Once the durable ``prepared`` marker exists, any unexpected
            # failure in result validation or receipt construction must be
            # terminalized as UNKNOWN.  Leaving it prepared would otherwise
            # make the next worker infer a crash without recording the cause.
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise
            _recover_prepared_entry(prepared, _safe_error_code(error))
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)

    print(json.dumps({
        "execution": "read_only_once",
        "runtime_identity": "reported",
        "received_action_ids": received,
        "completed_action_ids": completed,
        "rejected_action_ids": rejected,
        "unknown_action_ids": unknown,
        "submitted_receipts": submitted_receipts,
    }, separators=(",", ":")))
    return 0


def poll_read_only_once(args: argparse.Namespace) -> int:
    """Serialise each local queue drain before it can touch the journal.

    The long-lived agent lock owns a process lifetime, but an operator's
    one-shot diagnostic invocation has a different lifetime.  They must never
    concurrently replay a prepared marker while the other caller is inside a
    one-shot bridge effect.
    """
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_read_only_poll_lock(config_path):
        return _poll_read_only_once(args)


def _poll_file_read_once(args: argparse.Namespace) -> int:
    """Run exactly one C3 queue poll under its independent receipt journal."""

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _file_read_journal_path(config_path)
    journal = _read_file_read_journal(journal_path)
    submitted_receipts = _flush_file_read_journal(config, journal_path, journal)

    project_root = Path(args.project_root).expanduser().resolve()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({
            "execution": "file_read_not_started",
            "reason": reason,
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({
            "execution": "file_read_not_started",
            "reason": "runtime_identity_unproven",
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0

    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/poll",
        {"limit": 1, "lane": "bounded_file_read"},
        f"Node {config['node_secret']}",
    )
    actions = response.get("actions")
    if not isinstance(actions, list) or len(actions) > 1:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")

    completed: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_FILE_READ_ACTION_DENIED")
        action_id = _file_read_action_text(action, "action_id")
        attempt_id = _file_read_action_text(action, "attempt_id")
        received.append(action_id)
        key = _file_read_journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            submitted_receipts += _flush_file_read_journal(config, journal_path, journal)
            continue
        try:
            request = _file_read_bridge_request(action, config)
            policy = _admit_file_read_policy_request(
                args,
                config_path=config_path,
                config=config,
                request=request,
            )
            expected_policy_sha256 = _policy_digest(policy)
        except RuntimeError as error:
            code = _safe_error_code(error, "CONTROL_PLANE_FILE_READ_ACTION_DENIED")
            entry = _record_file_read_receipt(
                journal_path,
                journal,
                state="rejected",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_bounded_file_read",
                    "code": code,
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue

        # The prepared marker is durable before the CJS bridge sees the request.
        # A process loss after this point must settle UNKNOWN, never re-read a
        # file simply because its result was not returned to Python.
        journal["entries"][key] = {
            "state": "prepared",
            "action_id": action_id,
            "attempt_id": attempt_id,
        }
        _write_json_atomic(journal_path, journal)
        try:
            try:
                result, error_code = recovery_file_read_bridge(args, project_root, request)
            except Exception:
                result, error_code = None, "CONTROL_PLANE_FILE_READ_AGENT_EXCEPTION"
            if result is not None:
                safe_result = _safe_file_read_bridge_result(
                    result,
                    request,
                    expected_policy_sha256=expected_policy_sha256,
                )
                entry = _record_file_read_receipt(
                    journal_path,
                    journal,
                    state="completed",
                    action_id=action_id,
                    attempt_id=attempt_id,
                    receipt_state="completed",
                    local_handle=str(safe_result["local_handle"]),
                    payload=safe_result,
                )
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted_receipts += 1
                completed.append(action_id)
                continue

            code = _safe_error_code(error_code, "CONTROL_PLANE_FILE_READ_FAILED")
            pre_effect = code in FILE_READ_PRE_EFFECT_REJECTION_CODES
            entry = _record_file_read_receipt(
                journal_path,
                journal,
                state="rejected" if pre_effect else "unknown",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected" if pre_effect else "unknown",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_bounded_file_read",
                    "code": code if pre_effect else "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
                    **({} if pre_effect else {"diagnostic_code": code}),
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            (rejected if pre_effect else unknown).append(action_id)
        except Exception as error:
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise
            _recover_file_read_prepared_entry(prepared, _safe_error_code(error))
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)

    print(json.dumps({
        "execution": "file_read_once",
        "runtime_identity": "reported",
        "received_action_ids": received,
        "completed_action_ids": completed,
        "rejected_action_ids": rejected,
        "unknown_action_ids": unknown,
        "submitted_receipts": submitted_receipts,
    }, separators=(",", ":")))
    return 0


def _poll_approved_patch_once(args: argparse.Namespace) -> int:
    """Run one independently policy-gated exact-patch delivery attempt.

    The durable ``prepared`` journal marker is written before the CJS bridge
    can reach Recovery IPC. Any uncertainty after that point is terminalized
    as UNKNOWN and is never replayed as another patch invocation.
    """

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _approved_patch_journal_path(config_path)
    journal = _read_approved_patch_journal(journal_path)
    submitted_receipts = _flush_approved_patch_journal(config, journal_path, journal)

    project_root = Path(args.project_root).expanduser().resolve()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({
            "execution": "approved_patch_not_started",
            "reason": reason,
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({
            "execution": "approved_patch_not_started",
            "reason": "runtime_identity_unproven",
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0

    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/poll",
        {"limit": 1, "lane": "approved_patch"},
        f"Node {config['node_secret']}",
    )
    actions = response.get("actions")
    if not isinstance(actions, list) or len(actions) > 1:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")

    completed: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
        action_id = _approved_patch_action_identifier(action, "action_id")
        attempt_id = _approved_patch_action_identifier(action, "attempt_id")
        received.append(action_id)
        key = _approved_patch_journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            submitted_receipts += _flush_approved_patch_journal(config, journal_path, journal)
            continue
        try:
            request = _approved_patch_bridge_request(action, config)
            policy, expected_patch = _admit_approved_patch_policy_request(
                args,
                config_path=config_path,
                config=config,
                request=request,
            )
            expected_policy_sha256 = _policy_digest(policy)
        except RuntimeError as error:
            code = _safe_error_code(error, "CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED")
            entry = _record_approved_patch_receipt(
                journal_path,
                journal,
                state="rejected",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_approved_patch",
                    "code": code,
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue

        journal["entries"][key] = {
            "state": "prepared",
            "action_id": action_id,
            "attempt_id": attempt_id,
        }
        _write_json_atomic(journal_path, journal)
        try:
            try:
                result, error_code = recovery_approved_patch_bridge(args, project_root, request)
            except Exception:
                result, error_code = None, "CONTROL_PLANE_APPROVED_PATCH_AGENT_EXCEPTION"
            if result is not None:
                safe_result = _safe_approved_patch_bridge_result(
                    result,
                    request,
                    expected_policy_sha256=expected_policy_sha256,
                    expected_patch=expected_patch,
                )
                entry = _record_approved_patch_receipt(
                    journal_path,
                    journal,
                    state="completed",
                    action_id=action_id,
                    attempt_id=attempt_id,
                    receipt_state="completed",
                    local_handle=str(safe_result["local_handle"]),
                    payload=safe_result,
                )
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted_receipts += 1
                completed.append(action_id)
                continue

            code = _safe_error_code(error_code, "CONTROL_PLANE_APPROVED_PATCH_FAILED")
            pre_effect = code in APPROVED_PATCH_PRE_EFFECT_REJECTION_CODES
            entry = _record_approved_patch_receipt(
                journal_path,
                journal,
                state="rejected" if pre_effect else "unknown",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected" if pre_effect else "unknown",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_approved_patch",
                    "code": code if pre_effect else "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN",
                    **({} if pre_effect else {"diagnostic_code": code}),
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            (rejected if pre_effect else unknown).append(action_id)
        except Exception as error:
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise
            _recover_approved_patch_prepared_entry(prepared, _safe_error_code(error))
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)

    print(json.dumps({
        "execution": "approved_patch_once",
        "runtime_identity": "reported",
        "received_action_ids": received,
        "completed_action_ids": completed,
        "rejected_action_ids": rejected,
        "unknown_action_ids": unknown,
        "submitted_receipts": submitted_receipts,
    }, separators=(",", ":")))
    return 0


def _file_read_poll_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.file-read-poll.lock")


def _file_read_loop_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.file-read-loop.lock")


def _stale_file_read_lock(lock_path: Path) -> bool:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "instance_id", "pid"}
        or value.get("schema_version") != FILE_READ_LOOP_LOCK_SCHEMA_VERSION
        or not isinstance(value.get("instance_id"), str)
        or not value["instance_id"]
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
    ):
        return False
    return not _pid_is_live(value["pid"])


@contextmanager
def _exclusive_file_read_lock(
    lock_path: Path,
    *,
    already_running_code: str,
) -> Iterator[None]:
    """Own one C3 loop/poll lock without sharing the metadata-lane lock."""

    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": FILE_READ_LOOP_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_file_read_lock(lock_path):
                raise RuntimeError(already_running_code)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError(already_running_code) from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError(already_running_code)
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def poll_file_read_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_file_read_lock(
        _file_read_poll_lock_path(config_path),
        already_running_code="CONTROL_PLANE_FILE_READ_POLL_ALREADY_RUNNING",
    ):
        return _poll_file_read_once(args)


def _file_read_loop_interval(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", None)
    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
        or not FILE_READ_LOOP_MIN_INTERVAL_SECONDS <= interval_seconds <= FILE_READ_LOOP_MAX_INTERVAL_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_FILE_READ_LOOP_INTERVAL_INVALID")
    return interval_seconds


def _file_read_loop_policy_admission(args: argparse.Namespace) -> None:
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    _file_read_policy_admission(args, config_path=config_path, config=config)


def _file_read_iteration(args: argparse.Namespace) -> None:
    _file_read_loop_policy_admission(args)
    runtime_heartbeat(args)
    poll_file_read_once(args)


def run_file_read_loop(args: argparse.Namespace) -> int:
    """Run an explicit, bounded C3 worker; no scheduler/service is created."""

    interval_seconds = _file_read_loop_interval(args)
    max_iterations = args.max_iterations
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_LOOP_ITERATIONS_INVALID")
    if interval_seconds * max_iterations > FILE_READ_LOOP_MAX_DURATION_SECONDS:
        raise RuntimeError("CONTROL_PLANE_FILE_READ_LOOP_DURATION_EXCEEDED")
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    completed_iterations = 0
    try:
        with _exclusive_file_read_lock(
            _file_read_loop_lock_path(config_path),
            already_running_code="CONTROL_PLANE_FILE_READ_LOOP_ALREADY_RUNNING",
        ):
            for iteration in range(1, max_iterations + 1):
                try:
                    _file_read_iteration(args)
                    state = "completed"
                    reason = None
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    if reason in FILE_READ_POLICY_STOP_CODES:
                        print(json.dumps({
                            "execution": "file_read_loop_not_started" if iteration == 1 else "file_read_loop_stopped",
                            "reason": reason,
                            "completed_iterations": completed_iterations,
                        }, separators=(",", ":")))
                        return 0
                    state = "degraded"
                completed_iterations = iteration
                print(json.dumps({
                    "execution": "file_read_loop_iteration",
                    "iteration": iteration,
                    "state": state,
                    "reason": reason,
                }, separators=(",", ":")))
                if iteration < max_iterations:
                    time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "file_read_loop_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    return 0


def _poll_document_write_once(args: argparse.Namespace) -> int:
    """Run one policy-gated document create/convert delivery attempt."""

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _document_write_journal_path(config_path)
    journal = _read_document_write_journal(journal_path)
    submitted_receipts = _flush_document_write_journal(config, journal_path, journal)

    project_root = Path(args.project_root).expanduser().resolve()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({
            "execution": "document_write_not_started",
            "reason": reason,
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({
            "execution": "document_write_not_started",
            "reason": "runtime_identity_unproven",
            "received_action_ids": [],
            "submitted_receipts": submitted_receipts,
        }, separators=(",", ":")))
        return 0

    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/poll",
        {"limit": 1, "lane": "document_write"},
        f"Node {config['node_secret']}",
    )
    actions = response.get("actions")
    if not isinstance(actions, list) or len(actions) > 1:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")

    completed: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
        action_id = _document_write_action_identifier(action, "action_id")
        attempt_id = _document_write_action_identifier(action, "attempt_id")
        received.append(action_id)
        key = _document_write_journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            submitted_receipts += _flush_document_write_journal(config, journal_path, journal)
            continue
        try:
            request = _document_write_bridge_request(action, config)
            policy, _entry = _admit_document_write_policy_request(
                args,
                config_path=config_path,
                config=config,
                request=request,
            )
            # RecoveryHost and RuntimeOrchestrator bind the result to this
            # exact policy projection. Keep the digest out of the central
            # action and add it only inside the local bridge envelope.
            request = {**request, "policy_sha256": _policy_digest(policy)}
            expected_policy_sha256 = _policy_digest(policy)
        except RuntimeError as error:
            code = _safe_error_code(error, "CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED")
            entry = _record_document_write_receipt(
                journal_path,
                journal,
                state="rejected",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_document_write",
                    "code": code,
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue

        journal["entries"][key] = {
            "state": "prepared",
            "action_id": action_id,
            "attempt_id": attempt_id,
        }
        _write_json_atomic(journal_path, journal)
        try:
            try:
                result, error_code = recovery_document_write_bridge(args, project_root, request)
            except Exception:
                result, error_code = None, "CONTROL_PLANE_DOCUMENT_WRITE_AGENT_EXCEPTION"
            if result is not None:
                safe_result = _safe_document_write_bridge_result(
                    result,
                    request,
                    expected_policy_sha256=expected_policy_sha256,
                )
                entry = _record_document_write_receipt(
                    journal_path,
                    journal,
                    state="completed",
                    action_id=action_id,
                    attempt_id=attempt_id,
                    receipt_state="completed",
                    local_handle=str(safe_result["local_handle"]),
                    payload=safe_result,
                )
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted_receipts += 1
                completed.append(action_id)
                continue

            code = _safe_error_code(error_code, "CONTROL_PLANE_DOCUMENT_WRITE_FAILED")
            pre_effect = code in DOCUMENT_WRITE_PRE_EFFECT_REJECTION_CODES
            entry = _record_document_write_receipt(
                journal_path,
                journal,
                state="rejected" if pre_effect else "unknown",
                action_id=action_id,
                attempt_id=attempt_id,
                receipt_state="rejected" if pre_effect else "unknown",
                local_handle="",
                payload={
                    "schema_version": 1,
                    "operation_kind": "control_plane_document_write",
                    "code": code if pre_effect else "CONTROL_PLANE_DOCUMENT_WRITE_EFFECT_UNKNOWN",
                    **({} if pre_effect else {"diagnostic_code": code, "reconciliation_required": True}),
                },
            )
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            (rejected if pre_effect else unknown).append(action_id)
        except Exception as error:
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise
            _recover_document_write_prepared_entry(prepared, _safe_error_code(error))
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)

    print(json.dumps({
        "execution": "document_write_once",
        "runtime_identity": "reported",
        "received_action_ids": received,
        "completed_action_ids": completed,
        "rejected_action_ids": rejected,
        "unknown_action_ids": unknown,
        "submitted_receipts": submitted_receipts,
    }, separators=(",", ":")))
    return 0


def _document_write_poll_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.document-write-poll.lock")


def _document_write_loop_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.document-write-loop.lock")


def _stale_document_write_lock(lock_path: Path) -> bool:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return bool(
        isinstance(value, dict)
        and set(value) == {"schema_version", "instance_id", "pid"}
        and value.get("schema_version") == DOCUMENT_WRITE_LOOP_LOCK_SCHEMA_VERSION
        and isinstance(value.get("instance_id"), str)
        and bool(value["instance_id"])
        and isinstance(value.get("pid"), int)
        and not isinstance(value.get("pid"), bool)
        and not _pid_is_live(value["pid"])
    )


@contextmanager
def _exclusive_document_write_lock(
    lock_path: Path,
    *,
    already_running_code: str,
) -> Iterator[None]:
    """Own document-write polling independently from every other lane."""

    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": DOCUMENT_WRITE_LOOP_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_document_write_lock(lock_path):
                raise RuntimeError(already_running_code)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError(already_running_code) from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError(already_running_code)
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def poll_document_write_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_document_write_lock(
        _document_write_poll_lock_path(config_path),
        already_running_code="CONTROL_PLANE_DOCUMENT_WRITE_POLL_ALREADY_RUNNING",
    ):
        return _poll_document_write_once(args)


def _document_write_loop_interval(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", None)
    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
        or not DOCUMENT_WRITE_LOOP_MIN_INTERVAL_SECONDS <= interval_seconds <= DOCUMENT_WRITE_LOOP_MAX_INTERVAL_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_LOOP_INTERVAL_INVALID")
    return interval_seconds


def _document_write_loop_policy_admission(args: argparse.Namespace) -> None:
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    _document_write_policy_admission(args, config_path=config_path, config=config)


def _document_write_iteration(args: argparse.Namespace) -> None:
    _document_write_loop_policy_admission(args)
    runtime_heartbeat(args)
    poll_document_write_once(args)


def run_document_write_loop(args: argparse.Namespace) -> int:
    """Run a bounded, owner-enabled document-write worker."""

    interval_seconds = _document_write_loop_interval(args)
    max_iterations = args.max_iterations
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_LOOP_ITERATIONS_INVALID")
    if interval_seconds * max_iterations > DOCUMENT_WRITE_LOOP_MAX_DURATION_SECONDS:
        raise RuntimeError("CONTROL_PLANE_DOCUMENT_WRITE_LOOP_DURATION_EXCEEDED")
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    completed_iterations = 0
    try:
        with _exclusive_document_write_lock(
            _document_write_loop_lock_path(config_path),
            already_running_code="CONTROL_PLANE_DOCUMENT_WRITE_LOOP_ALREADY_RUNNING",
        ):
            for iteration in range(1, max_iterations + 1):
                try:
                    _document_write_iteration(args)
                    state = "completed"
                    reason = None
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    if reason in DOCUMENT_WRITE_POLICY_STOP_CODES:
                        print(json.dumps({
                            "execution": "document_write_loop_not_started" if iteration == 1 else "document_write_loop_stopped",
                            "reason": reason,
                            "completed_iterations": completed_iterations,
                        }, separators=(",", ":")))
                        return 0
                    state = "degraded"
                completed_iterations = iteration
                print(json.dumps({
                    "execution": "document_write_loop_iteration",
                    "iteration": iteration,
                    "state": state,
                    "reason": reason,
                }, separators=(",", ":")))
                if iteration < max_iterations:
                    time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "document_write_loop_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    return 0


def _approved_patch_poll_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.approved-patch-poll.lock")


def _approved_patch_loop_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.approved-patch-loop.lock")


def _stale_approved_patch_lock(lock_path: Path) -> bool:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "instance_id", "pid"}
        or value.get("schema_version") != APPROVED_PATCH_LOOP_LOCK_SCHEMA_VERSION
        or not isinstance(value.get("instance_id"), str)
        or not value["instance_id"]
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
    ):
        return False
    return not _pid_is_live(value["pid"])


@contextmanager
def _exclusive_approved_patch_lock(
    lock_path: Path,
    *,
    already_running_code: str,
) -> Iterator[None]:
    """Own C4 polling independently from every older execution lane."""

    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": APPROVED_PATCH_LOOP_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_approved_patch_lock(lock_path):
                raise RuntimeError(already_running_code)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError(already_running_code) from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError(already_running_code)
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def poll_approved_patch_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_approved_patch_lock(
        _approved_patch_poll_lock_path(config_path),
        already_running_code="CONTROL_PLANE_APPROVED_PATCH_POLL_ALREADY_RUNNING",
    ):
        return _poll_approved_patch_once(args)


def _approved_patch_loop_interval(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", None)
    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
        or not APPROVED_PATCH_LOOP_MIN_INTERVAL_SECONDS <= interval_seconds <= APPROVED_PATCH_LOOP_MAX_INTERVAL_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_LOOP_INTERVAL_INVALID")
    return interval_seconds


def _approved_patch_loop_policy_admission(args: argparse.Namespace) -> None:
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    _approved_patch_policy_admission(args, config_path=config_path, config=config)


def _approved_patch_iteration(args: argparse.Namespace) -> None:
    # A repeating mutation worker must validate policy before it allocates a
    # central delivery. Explicit one-shot diagnostics still produce a typed
    # receipt if an action is already delivered and rejected locally.
    _approved_patch_loop_policy_admission(args)
    runtime_heartbeat(args)
    poll_approved_patch_once(args)


def run_approved_patch_loop(args: argparse.Namespace) -> int:
    """Run a bounded, owner-enabled C4 worker; it creates no scheduler/service."""

    interval_seconds = _approved_patch_loop_interval(args)
    max_iterations = args.max_iterations
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_LOOP_ITERATIONS_INVALID")
    if interval_seconds * max_iterations > APPROVED_PATCH_LOOP_MAX_DURATION_SECONDS:
        raise RuntimeError("CONTROL_PLANE_APPROVED_PATCH_LOOP_DURATION_EXCEEDED")
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    completed_iterations = 0
    try:
        with _exclusive_approved_patch_lock(
            _approved_patch_loop_lock_path(config_path),
            already_running_code="CONTROL_PLANE_APPROVED_PATCH_LOOP_ALREADY_RUNNING",
        ):
            for iteration in range(1, max_iterations + 1):
                try:
                    _approved_patch_iteration(args)
                    state = "completed"
                    reason = None
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    if reason in APPROVED_PATCH_POLICY_STOP_CODES:
                        print(json.dumps({
                            "execution": "approved_patch_loop_not_started" if iteration == 1 else "approved_patch_loop_stopped",
                            "reason": reason,
                            "completed_iterations": completed_iterations,
                        }, separators=(",", ":")))
                        return 0
                    state = "degraded"
                completed_iterations = iteration
                print(json.dumps({
                    "execution": "approved_patch_loop_iteration",
                    "iteration": iteration,
                    "state": state,
                    "reason": reason,
                }, separators=(",", ":")))
                if iteration < max_iterations:
                    time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "approved_patch_loop_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    return 0


def _read_only_loop_interval(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", None)
    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
        or not READ_ONLY_LOOP_MIN_INTERVAL_SECONDS <= interval_seconds <= READ_ONLY_LOOP_MAX_INTERVAL_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_LOOP_INTERVAL_INVALID")
    return interval_seconds


def _read_only_agent_lock_path(config_path: Path) -> Path:
    """Keep the lock next to the private node configuration, never in the repo."""

    return config_path.with_name(f"{config_path.name}.read-only-agent.lock")


def _pid_is_live(pid: int) -> bool:
    """Return a conservative cross-platform liveness answer for a lock owner."""

    if not isinstance(pid, int) or isinstance(pid, bool) or pid < 1:
        return False
    if os.name == "nt":
        return _windows_pid_is_live(pid)
    try:
        # ``signal 0`` does not terminate the target.  It is available on the
        # supported POSIX Python runtimes and avoids treating a missing process
        # as live.
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as error:
        # An unfamiliar error must not let this process remove a possibly-live
        # lock. The operator can inspect/stop the existing local owner.
        return True
    return True


def _windows_pid_is_live(pid: int) -> bool:
    """Read the Windows process exit code instead of relying on ``os.kill``.

    On Windows ``os.kill(pid, 0)`` can succeed for a PID whose process has
    already exited.  That leaves a crash-owned poll lock unreclaimable.  A
    limited query plus ``GetExitCodeProcess`` distinguishes ``STILL_ACTIVE``
    from a terminated process while preserving fail-closed behavior when the
    process exists but cannot be inspected.
    """

    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        process = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not process:
            # ERROR_INVALID_PARAMETER means the PID no longer exists. Access
            # denied and every unfamiliar failure remain live/fail-closed.
            return ctypes.get_last_error() != 87
        exit_code = wintypes.DWORD()
        try:
            if not kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                return True
            return exit_code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(process)
    except Exception:
        # Never reclaim a lock when process identity cannot be inspected.
        return True


def _stale_read_only_agent_lock(lock_path: Path) -> bool:
    """Only reclaim a well-formed lock after its recorded PID is certainly gone."""

    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "instance_id", "pid"}
        or value.get("schema_version") != READ_ONLY_AGENT_LOCK_SCHEMA_VERSION
        or not isinstance(value.get("instance_id"), str)
        or not value["instance_id"]
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
    ):
        return False
    return not _pid_is_live(value["pid"])


@contextmanager
def _exclusive_read_only_agent_lock(config_path: Path) -> Iterator[None]:
    """Hold one fail-closed local agent lock, reclaiming only a dead owner.

    This prevents two user-session launches from both polling/dequeuing the
    same node. A malformed lock is intentionally not removed automatically;
    silent lock recovery is less important than avoiding a duplicate executor.
    """

    lock_path = _read_only_agent_lock_path(config_path)
    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": READ_ONLY_AGENT_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_read_only_agent_lock(lock_path):
                raise RuntimeError("CONTROL_PLANE_READ_ONLY_AGENT_ALREADY_RUNNING")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError("CONTROL_PLANE_READ_ONLY_AGENT_ALREADY_RUNNING") from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_AGENT_ALREADY_RUNNING")
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _read_only_poll_lock_path(config_path: Path) -> Path:
    """Keep a short-lived queue-drain lock beside the private node config."""

    return config_path.with_name(f"{config_path.name}.read-only-poll.lock")


@contextmanager
def _exclusive_read_only_poll_lock(config_path: Path) -> Iterator[None]:
    """Exclude an overlapping one-shot poll without changing agent ownership."""

    lock_path = _read_only_poll_lock_path(config_path)
    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": READ_ONLY_AGENT_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_read_only_agent_lock(lock_path):
                raise RuntimeError("CONTROL_PLANE_READ_ONLY_POLL_ALREADY_RUNNING")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError("CONTROL_PLANE_READ_ONLY_POLL_ALREADY_RUNNING") from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_POLL_ALREADY_RUNNING")
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _read_only_iteration(args: argparse.Namespace) -> None:
    """Revalidate local policy and runtime immediately before a dequeue poll."""

    _read_only_loop_policy_admission(args)
    runtime_heartbeat(args)
    poll_read_only_once(args)


def run_read_only_loop(args: argparse.Namespace) -> int:
    """Run a deliberately bounded, logged-in read-only polling loop.

    This is an explicit local operator process, not a Windows service or a
    task-scheduler installer. It rechecks policy, runtime identity and
    heartbeat before every potential dequeue, and cannot run beyond one day.
    """

    interval_seconds = _read_only_loop_interval(args)
    max_iterations = args.max_iterations
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1:
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_LOOP_ITERATIONS_INVALID")
    if interval_seconds * max_iterations > READ_ONLY_LOOP_MAX_DURATION_SECONDS:
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_LOOP_DURATION_EXCEEDED")

    completed_iterations = 0
    try:
        for iteration in range(1, max_iterations + 1):
            try:
                _read_only_iteration(args)
                state = "completed"
                reason = None
            except RuntimeError as error:
                reason = _safe_error_code(error)
                if reason in READ_ONLY_POLICY_STOP_CODES:
                    print(json.dumps({
                        "execution": "read_only_loop_not_started" if iteration == 1 else "read_only_loop_stopped",
                        "reason": reason,
                        "completed_iterations": completed_iterations,
                    }, separators=(",", ":")))
                    return 0
                state = "degraded"
            completed_iterations = iteration
            print(json.dumps({
                "execution": "read_only_loop_iteration",
                "iteration": iteration,
                "state": state,
                "reason": reason,
            }, separators=(",", ":")))
            if iteration < max_iterations:
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "read_only_loop_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    return 0


def run_read_only_agent(args: argparse.Namespace) -> int:
    """Run one long-lived, same-user, read-only node agent.

    The command is designed for a future packaged same-user supervisor. It
    deliberately does not create a scheduled task or broaden the read-only
    bridge. A local policy disable/expiry is a terminal stop condition; transport
    and runtime failures are retried with bounded exponential backoff.
    """

    interval_seconds = _read_only_loop_interval(args)
    max_backoff_seconds = getattr(args, "max_backoff_seconds", None)
    max_iterations = getattr(args, "max_iterations", None)
    if (
        not isinstance(max_backoff_seconds, int)
        or isinstance(max_backoff_seconds, bool)
        or not interval_seconds <= max_backoff_seconds <= READ_ONLY_AGENT_MAX_BACKOFF_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_AGENT_BACKOFF_INVALID")
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 0:
        raise RuntimeError("CONTROL_PLANE_READ_ONLY_AGENT_ITERATIONS_INVALID")

    config_path = Path(args.config).expanduser().resolve()
    # Validate the private config before taking a process-wide lock. This never
    # prints its content and prevents a malformed invocation pinning a profile.
    _config(config_path)
    completed_iterations = 0
    failures = 0
    try:
        with _exclusive_read_only_agent_lock(config_path):
            print(json.dumps({
                "execution": "read_only_agent_started",
                "interval_seconds": interval_seconds,
                "max_backoff_seconds": max_backoff_seconds,
            }, separators=(",", ":")))
            while max_iterations == 0 or completed_iterations < max_iterations:
                iteration = completed_iterations + 1
                try:
                    _read_only_iteration(args)
                    state = "completed"
                    reason = None
                    failures = 0
                    delay_seconds = interval_seconds
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    if reason in READ_ONLY_POLICY_STOP_CODES:
                        print(json.dumps({
                            "execution": "read_only_agent_stopped",
                            "reason": reason,
                            "completed_iterations": completed_iterations,
                        }, separators=(",", ":")))
                        return 0
                    state = "degraded"
                    failures += 1
                    delay_seconds = min(max_backoff_seconds, interval_seconds * (2 ** min(failures - 1, 16)))
                completed_iterations = iteration
                print(json.dumps({
                    "execution": "read_only_agent_iteration",
                    "iteration": iteration,
                    "state": state,
                    "reason": reason,
                    "next_delay_seconds": delay_seconds,
                }, separators=(",", ":")))
                if max_iterations == 0 or completed_iterations < max_iterations:
                    time.sleep(delay_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "read_only_agent_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    print(json.dumps({
        "execution": "read_only_agent_stopped",
        "reason": "MAX_ITERATIONS_REACHED",
        "completed_iterations": completed_iterations,
    }, separators=(",", ":")))
    return 0


def _connected_agent_interval(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", None)
    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
        or not READ_ONLY_LOOP_MIN_INTERVAL_SECONDS <= interval_seconds <= READ_ONLY_LOOP_MAX_INTERVAL_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_INTERVAL_INVALID")
    return interval_seconds


def _connected_agent_lock_path(config_path: Path) -> Path:
    """Keep the long-lived connected-agent lock beside the private config."""

    return config_path.with_name(f"{config_path.name}.connected-agent.lock")


def _stale_connected_agent_lock(lock_path: Path) -> bool:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "instance_id", "pid"}
        or value.get("schema_version") != CONNECTED_AGENT_LOCK_SCHEMA_VERSION
        or not isinstance(value.get("instance_id"), str)
        or not value["instance_id"]
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
    ):
        return False
    return not _pid_is_live(value["pid"])


@contextmanager
def _exclusive_connected_agent_lock(config_path: Path) -> Iterator[None]:
    """Allow one connected agent per node profile, reclaiming only dead locks."""

    lock_path = _connected_agent_lock_path(config_path)
    instance_id = uuid.uuid4().hex
    descriptor = {
        "schema_version": CONNECTED_AGENT_LOCK_SCHEMA_VERSION,
        "instance_id": instance_id,
        "pid": os.getpid(),
    }
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_connected_agent_lock(lock_path):
                raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_ALREADY_RUNNING")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_ALREADY_RUNNING") from error
            continue
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_ALREADY_RUNNING")
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id and value.get("pid") == os.getpid():
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _connected_exec_policy_admission(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Check standing exec authority without allocating or consuming an action."""

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    policy = _normalise_exec_policy(
        _read_exec_policy(_exec_policy_path(args)),
        now_ms=int(time.time() * 1000),
        require_enabled=True,
    )
    if (
        policy["server_origin"] != _server_origin(config.get("server_url"))
        or policy["device_id"] != config.get("device_id")
        or policy["endpoint_id"] != config.get("endpoint_id")
    ):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH")
    entry = _require_policy_workspace_registration(args, config_path=config_path, policy=policy)
    if entry is not None and entry["capabilities"].get("exec") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    return policy, entry


def _connected_agent_lane_admission(args: argparse.Namespace, lane: str) -> None:
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    if lane in {"file_read", "artifact"}:
        _file_read_policy_admission(args, config_path=config_path, config=config)
        return
    if lane == "approved_patch":
        _approved_patch_policy_admission(args, config_path=config_path, config=config)
        return
    if lane == "document_write":
        _document_write_policy_admission(args, config_path=config_path, config=config)
        return
    if lane == "exec":
        _connected_exec_policy_admission(args)
        return
    raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_LANE_INVALID")


def _connected_agent_iteration(args: argparse.Namespace) -> list[dict[str, str]]:
    """Heartbeat first, then poll only locally enabled standing capability lanes."""

    runtime_heartbeat(args)
    lanes: list[tuple[str, Any]] = [
        ("file_read", poll_file_read_once),
        ("artifact", poll_artifact_once),
        ("approved_patch", poll_approved_patch_once),
        ("document_write", poll_document_write_once),
        ("exec", poll_exec_once),
    ]
    stop_codes = (
        set(FILE_READ_POLICY_STOP_CODES)
        | set(APPROVED_PATCH_POLICY_STOP_CODES)
        | set(DOCUMENT_WRITE_POLICY_STOP_CODES)
        | set(EXEC_POLICY_STOP_CODES)
        | {"CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT", "CONTROL_PLANE_WORKSPACE_REGISTRY_REQUIRED"}
    )
    result: list[dict[str, str]] = []
    for lane, poller in lanes:
        try:
            _connected_agent_lane_admission(args, lane)
        except RuntimeError as error:
            code = _safe_error_code(error)
            if code in stop_codes:
                result.append({"lane": lane, "state": "disabled", "reason": code})
                continue
            raise
        poller(args)
        result.append({"lane": lane, "state": "polled", "reason": ""})
    return result


def run_connected_agent(args: argparse.Namespace) -> int:
    """Keep an enrolled node connected independently of the read-only pilot.

    A heartbeat is always attempted after enrollment.  Local standing policy
    files decide which capability lanes may dequeue work; a missing/disabled
    lane is reported and skipped, never treated as permission to broaden the
    node.  Transport/runtime/auth failures use bounded reconnect backoff.
    """

    interval_seconds = _connected_agent_interval(args)
    max_backoff_seconds = getattr(args, "max_backoff_seconds", None)
    max_iterations = getattr(args, "max_iterations", None)
    if (
        not isinstance(max_backoff_seconds, int)
        or isinstance(max_backoff_seconds, bool)
        or not interval_seconds <= max_backoff_seconds <= CONNECTED_AGENT_MAX_BACKOFF_SECONDS
    ):
        raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_BACKOFF_INVALID")
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 0:
        raise RuntimeError("CONTROL_PLANE_CONNECTED_AGENT_ITERATIONS_INVALID")

    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    completed_iterations = 0
    failures = 0
    try:
        with _exclusive_connected_agent_lock(config_path):
            print(json.dumps({
                "execution": "connected_agent_started",
                "interval_seconds": interval_seconds,
                "max_backoff_seconds": max_backoff_seconds,
            }, separators=(",", ":")))
            while max_iterations == 0 or completed_iterations < max_iterations:
                iteration = completed_iterations + 1
                lanes: list[dict[str, str]] = []
                try:
                    lanes = _connected_agent_iteration(args)
                    state = "completed"
                    reason = None
                    failures = 0
                    delay_seconds = interval_seconds
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    state = "degraded"
                    failures += 1
                    delay_seconds = min(max_backoff_seconds, interval_seconds * (2 ** min(failures - 1, 16)))
                completed_iterations = iteration
                print(json.dumps({
                    "execution": "connected_agent_iteration",
                    "iteration": iteration,
                    "state": state,
                    "reason": reason,
                    "lanes": lanes,
                    "next_delay_seconds": delay_seconds,
                }, separators=(",", ":")))
                if max_iterations == 0 or completed_iterations < max_iterations:
                    time.sleep(delay_seconds)
    except KeyboardInterrupt:
        print(json.dumps({
            "execution": "connected_agent_interrupted",
            "completed_iterations": completed_iterations,
        }, separators=(",", ":")))
        return 130
    print(json.dumps({
        "execution": "connected_agent_stopped",
        "reason": "MAX_ITERATIONS_REACHED",
        "completed_iterations": completed_iterations,
    }, separators=(",", ":")))
    return 0


EXEC_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_EXEC_POLICY_MISSING",
    "CONTROL_PLANE_EXEC_POLICY_INVALID",
    "CONTROL_PLANE_EXEC_POLICY_EXPIRED",
    "CONTROL_PLANE_EXEC_DISABLED",
    "CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH",
})
def _exec_policy_path(args: argparse.Namespace) -> Path:
    return _policy_data_root(args) / EXEC_POLICY_FILE_NAME


def _exec_journal_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.exec-journal.json")


def _exec_poll_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.exec-poll.lock")


def _exec_loop_lock_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.name}.exec-loop.lock")


def _exec_workspace_lock_path(config_path: Path, workspace_id: str, workspace_generation: str) -> Path:
    safe_ws = re.sub(r"[^A-Za-z0-9_.-]", "_", workspace_id)[:64]
    safe_gen = re.sub(r"[^A-Za-z0-9_.-]", "_", workspace_generation)[:64]
    return config_path.with_name(f"{config_path.name}.exec-ws-{safe_ws}-{safe_gen}.lock")


def _stale_exec_lock(lock_path: Path) -> bool:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "instance_id", "pid"}
        or value.get("schema_version") != EXEC_LOOP_LOCK_SCHEMA_VERSION
        or not isinstance(value.get("instance_id"), str)
        or not value["instance_id"]
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
    ):
        return False
    return not _pid_is_live(value["pid"])


@contextmanager
def _exclusive_exec_lock(lock_path: Path, *, already_running_code: str) -> Iterator[None]:
    instance_id = uuid.uuid4().hex
    descriptor = {"schema_version": EXEC_LOOP_LOCK_SCHEMA_VERSION, "instance_id": instance_id, "pid": os.getpid()}
    acquired = False
    for _attempt in range(2):
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if not _stale_exec_lock(lock_path):
                raise RuntimeError(already_running_code)
            try:
                lock_path.unlink()
            except (FileNotFoundError, OSError) as error:
                raise RuntimeError(already_running_code) from error
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(descriptor, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            try:
                lock_path.unlink()
            except OSError:
                pass
            raise
        acquired = True
        break
    if not acquired:
        raise RuntimeError(already_running_code)
    try:
        yield
    finally:
        try:
            value = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        if isinstance(value, dict) and value.get("instance_id") == instance_id:
            try:
                lock_path.unlink()
            except OSError:
                pass


def _exec_argv_item(value: Any) -> str:
    if not isinstance(value, str):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID") from error
    if not encoded or len(encoded) > EXEC_MAX_ARGV_ITEM_BYTES:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if any(token in value for token in (";", "&&", "||", "`", "$(", "|", ">", "<", "\n", "\r")):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if value != value.strip() or not value:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    return value


def _normalise_exec_policy(policy: Any, *, now_ms: int | None = None, require_enabled: bool = False) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    schema_version = policy.get("schema_version")
    standing = schema_version == EXEC_POLICY_SCHEMA_VERSION
    legacy = schema_version == EXEC_POLICY_LEGACY_SCHEMA_VERSION
    expected = {"schema_version", "enabled", "server_origin", "owner_id", "device_id", "endpoint_id",
                "workspace_id", "workspace_generation", "expires_at_ms", "facade_contract",
                "allowed_argv_prefixes", "max_timeout_ms", "max_output_bytes", "max_concurrent"}
    if standing:
        expected.add("authority_mode")
    if not (standing or legacy) or set(policy) != expected:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if not isinstance(policy.get("enabled"), bool):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if require_enabled and policy["enabled"] is not True:
        raise RuntimeError("CONTROL_PLANE_EXEC_DISABLED")
    authority_mode = EXEC_POLICY_STANDING_AUTHORITY if standing else "expiring_legacy"
    if standing and policy.get("authority_mode") != EXEC_POLICY_STANDING_AUTHORITY:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    expires_at_ms = policy.get("expires_at_ms")
    if standing:
        if expires_at_ms is not None:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    else:
        if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
        if now_ms is not None and expires_at_ms <= now_ms:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_EXPIRED")
    facade = policy.get("facade_contract")
    if not isinstance(facade, dict):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    _policy_facade_contract(facade.get("schema_version"), facade.get("profile"), facade.get("sha256"))
    prefixes = policy.get("allowed_argv_prefixes")
    if not isinstance(prefixes, list) or not 1 <= len(prefixes) <= EXEC_MAX_ALLOWED_PREFIXES:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    normalised_prefixes: list[list[str]] = []
    for prefix in prefixes:
        if not isinstance(prefix, list) or not 1 <= len(prefix) <= EXEC_MAX_ARGV_ITEMS:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
        normalised_prefixes.append([_exec_argv_item(item) for item in prefix])
    max_timeout = policy.get("max_timeout_ms")
    max_output = policy.get("max_output_bytes")
    max_concurrent = policy.get("max_concurrent")
    if not isinstance(max_timeout, int) or isinstance(max_timeout, bool) or not EXEC_MIN_TIMEOUT_MS <= max_timeout <= EXEC_MAX_TIMEOUT_MS:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if not isinstance(max_output, int) or isinstance(max_output, bool) or not 1024 <= max_output <= EXEC_MAX_OUTPUT_BYTES:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    if not isinstance(max_concurrent, int) or isinstance(max_concurrent, bool) or not 1 <= max_concurrent <= 4:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
    return {
        "schema_version": schema_version,
        "enabled": policy["enabled"],
        "authority_mode": authority_mode,
        "server_origin": _server_origin(policy.get("server_origin")),
        "owner_id": _policy_identifier(policy.get("owner_id"), "owner_id"),
        "device_id": _policy_identifier(policy.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(policy.get("endpoint_id"), "endpoint_id"),
        "workspace_id": _policy_identifier(policy.get("workspace_id"), "workspace_id"),
        "workspace_generation": _policy_identifier(policy.get("workspace_generation"), "workspace_generation"),
        "expires_at_ms": expires_at_ms,
        "facade_contract": _policy_facade_contract(facade.get("schema_version"), facade.get("profile"), facade.get("sha256")),
        "allowed_argv_prefixes": normalised_prefixes,
        "max_timeout_ms": max_timeout,
        "max_output_bytes": max_output,
        "max_concurrent": max_concurrent,
    }


def _read_exec_policy(policy_path: Path) -> dict[str, Any]:
    try:
        stat = policy_path.stat()
        if not policy_path.is_file() or stat.st_size <= 0 or stat.st_size > EXEC_POLICY_MAX_BYTES:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_MISSING") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID") from error
    return _normalise_exec_policy(value)


def _install_exec_policy_values(*, owner_id: str, device_id: str, endpoint_id: str, workspace_id: str,
                                workspace_generation: str, server_origin: str, facade_contract: dict[str, Any],
                                allowed_argv_prefixes: list[list[str]], max_timeout_ms: int,
                                max_output_bytes: int) -> dict[str, Any]:
    return _normalise_exec_policy({
        "schema_version": EXEC_POLICY_SCHEMA_VERSION, "enabled": True, "server_origin": server_origin,
        "owner_id": owner_id, "device_id": device_id, "endpoint_id": endpoint_id,
        "workspace_id": workspace_id, "workspace_generation": workspace_generation,
        "authority_mode": EXEC_POLICY_STANDING_AUTHORITY, "expires_at_ms": None,
        "facade_contract": facade_contract,
        "allowed_argv_prefixes": allowed_argv_prefixes, "max_timeout_ms": max_timeout_ms,
        "max_output_bytes": max_output_bytes, "max_concurrent": 2,
    }, require_enabled=True)


def _exec_allowlist_match(argv: list[str], prefixes: list[list[str]]) -> bool:
    for prefix in prefixes:
        if len(argv) >= len(prefix) and argv[:len(prefix)] == prefix:
            return True
    return False


def _exec_bridge_request(action: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    for field in ("action_id", "attempt_id", "owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation", "context_id", "binding_id"):
        value = action.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    if action.get("device_id") != config["device_id"] or action.get("endpoint_id") != config["endpoint_id"]:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    argv_json = action.get("mcp_exec_argv_json")
    try:
        argv_obj = json.loads(argv_json) if isinstance(argv_json, str) else None
    except (TypeError, ValueError) as error:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED") from error
    argv = argv_obj.get("argv") if isinstance(argv_obj, dict) else None
    if not isinstance(argv, list) or not argv:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    argv = [_exec_argv_item(item) for item in argv]
    cwd = action.get("mcp_exec_cwd", "")
    if cwd not in ("", None) and not isinstance(cwd, str):
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    cwd = cwd or ""
    if cwd and (cwd.startswith("/") or "\\" in cwd or ":" in cwd or any(not p or p in {".", ".."} for p in cwd.split("/"))):
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    timeout_ms = action.get("mcp_exec_timeout_ms")
    max_output = action.get("mcp_exec_max_output_bytes")
    if not isinstance(timeout_ms, int) or not EXEC_MIN_TIMEOUT_MS <= timeout_ms <= EXEC_MAX_TIMEOUT_MS:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    if not isinstance(max_output, int) or not 1024 <= max_output <= EXEC_MAX_OUTPUT_BYTES:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    task_id, writer_lease_generation = _writer_lease_authority(
        action, code="CONTROL_PLANE_EXEC_ACTION_DENIED"
    )
    expires_at_ms = action.get("expires_at_ms")
    if not isinstance(expires_at_ms, int) or isinstance(expires_at_ms, bool):
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    return {"server_origin": _server_origin(config.get("server_url")),
            "owner_id": action["owner_id"], "device_id": action["device_id"],
            "endpoint_id": action["endpoint_id"], "workspace_id": action["workspace_id"],
            "workspace_generation": action["workspace_generation"],
            "context_id": action["context_id"], "binding_id": action["binding_id"],
            "action_id": action["action_id"], "attempt_id": action["attempt_id"],
            "expires_at_ms": expires_at_ms,
            "task_id": task_id, "writer_lease_generation": writer_lease_generation,
            "tool_name": EXEC_TOOL_NAME, "operation": "exec_run",
            "argv": argv, "cwd": cwd, "timeout_ms": timeout_ms, "max_output_bytes": max_output,
            "facade_contract": {"schema_version": action.get("mcp_exec_facade_schema_version"),
                                "profile": action.get("mcp_exec_facade_profile"),
                                "sha256": action.get("mcp_exec_facade_contract_sha256")},
            "command_id": None, "job_id": None, "local_handle": None,
            "consumer_id": None, "yield_time_ms": None, "signal": None, "wait_ms": None,
            "run_id": None, "wave_id": None}


def _exec_control_request(base_request: dict[str, Any], result: dict[str, Any], *, operation: str,
                          signal: str | None = None, wait_ms: int | None = None,
                          yield_time_ms: int = 10_000) -> dict[str, Any]:
    """Build a control envelope for one already-created local command.

    The original exec request and its local handle are journal authority.  A
    control poll/stop may observe or terminate that exact handle, but it never
    carries a new argv that could create a replacement process.
    """

    if operation not in {"exec_poll", "exec_stop"}:
        raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    command_id = result.get("command_id")
    job_id = result.get("job_id")
    local_handle = result.get("local_handle")
    if (not isinstance(command_id, str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(command_id) is None
            or not isinstance(job_id, str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(job_id) is None
            or not isinstance(local_handle, str) or EXEC_LOCAL_HANDLE_PATTERN.fullmatch(local_handle) is None):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if not isinstance(yield_time_ms, int) or isinstance(yield_time_ms, bool) or not 0 <= yield_time_ms <= 30_000:
        raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    if operation == "exec_poll":
        if signal is not None or wait_ms is not None:
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    else:
        signal = str(signal or "TERM").strip().upper()
        if signal not in EXEC_CONTROL_SIGNALS or not isinstance(wait_ms, int) or isinstance(wait_ms, bool) or not 0 <= wait_ms <= 30_000:
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    request = dict(base_request)
    request.update({
        "operation": operation,
        "command_id": command_id,
        "job_id": job_id,
        "local_handle": local_handle,
        "consumer_id": f"control-plane-exec:{base_request['task_id']}",
        "yield_time_ms": yield_time_ms,
        "signal": signal,
        "wait_ms": wait_ms,
        "run_id": str(result.get("run_id") or ""),
        "wave_id": str(result.get("wave_id") or ""),
    })
    return request


def _admit_exec_policy_request(args: argparse.Namespace, *, config_path: Path, config: dict[str, Any],
                               request: dict[str, Any]) -> dict[str, Any]:
    operation = request.get("operation")
    if operation not in EXEC_CONTROL_OPERATIONS:
        raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    policy = _read_exec_policy(_exec_policy_path(args))
    if policy["enabled"] is not True:
        raise RuntimeError("CONTROL_PLANE_EXEC_DISABLED")
    now_ms = int(time.time() * 1000)
    # A poll/stop is recovery of an already-created local Job.  It may remain
    # actionable after the short action/policy window, but it must still bind
    # the exact persisted target, argv and command handle below.  New spawns
    # continue to require a live policy.
    if operation == "exec_run":
        if policy["authority_mode"] == "expiring_legacy" and policy["expires_at_ms"] <= now_ms:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_EXPIRED")
        if request.get("expires_at_ms") <= now_ms:
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_EXPIRED")
    for field in ("owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation"):
        if policy[field] != request.get(field):
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH")
    if policy["server_origin"] != _server_origin(config.get("server_url")):
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH")
    if policy["facade_contract"] != request["facade_contract"]:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH")
    if not _exec_allowlist_match(request["argv"], policy["allowed_argv_prefixes"]):
        raise RuntimeError("CONTROL_PLANE_EXEC_ALLOWLIST_DENIED")
    if request["timeout_ms"] > policy["max_timeout_ms"] or request["max_output_bytes"] > policy["max_output_bytes"]:
        raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_TOO_LARGE")
    if operation == "exec_run":
        if any(request.get(field) is not None for field in ("command_id", "job_id", "local_handle", "consumer_id", "yield_time_ms", "signal", "wait_ms", "run_id", "wave_id")):
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    else:
        if (not isinstance(request.get("command_id"), str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(request["command_id"]) is None
                or not isinstance(request.get("job_id"), str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(request["job_id"]) is None
                or not isinstance(request.get("local_handle"), str) or EXEC_LOCAL_HANDLE_PATTERN.fullmatch(request["local_handle"]) is None
                or not isinstance(request.get("consumer_id"), str) or not 1 <= len(request["consumer_id"].strip()) <= 128
                or not isinstance(request.get("yield_time_ms"), int) or isinstance(request["yield_time_ms"], bool)
                or not 0 <= request["yield_time_ms"] <= 30_000
                or not isinstance(request.get("run_id"), str) or len(request["run_id"]) > 128
                or not isinstance(request.get("wave_id"), str) or len(request["wave_id"]) > 128):
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
        if operation == "exec_poll":
            if request.get("signal") is not None or request.get("wait_ms") is not None:
                raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
        elif (str(request.get("signal") or "").upper() not in EXEC_CONTROL_SIGNALS
              or not isinstance(request.get("wait_ms"), int) or isinstance(request["wait_ms"], bool)
              or not 0 <= request["wait_ms"] <= 30_000):
            raise RuntimeError("CONTROL_PLANE_EXEC_REQUEST_INVALID")
    return policy


def _run_bounded_exec(*, argv: list[str], cwd_path: Path, timeout_ms: int, max_output_bytes: int,
                      stop_check=None) -> tuple[dict[str, Any] | None, str | None]:
    """Run argv with shell=False inside cwd_path; poll stop_check for verified stop.

    Returns (result, error_code). result holds exit_code/stdout/stderr/truncated.
    stop_check is a zero-arg callable returning True when a verified stop was
    requested. On stop the tree is killed and the caller reports stopped.
    """
    try:
        proc = subprocess.Popen([str(a) for a in argv], cwd=str(cwd_path), shell=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, ValueError):
        return None, "CONTROL_PLANE_EXEC_SPAWN_FAILED"
    stdout_b, stderr_b = b"", b""
    deadline = time.monotonic() + timeout_ms / 1000.0
    stopped = False
    try:
        while True:
            if stop_check is not None and stop_check():
                stopped = True
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                proc.wait(timeout=min(0.2, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
        if stopped:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                return None, "CONTROL_PLANE_EXEC_STOP_UNCONFIRMED"
            try:
                out, err = proc.communicate(timeout=5)
            except Exception:
                out, err = b"", b""
            stdout_b, stderr_b = (out or b"")[:max_output_bytes], (err or b"")[:max_output_bytes]
            return {"exit_code": 143, "stdout": stdout_b.decode("utf-8", "replace"),
                    "stderr": stderr_b.decode("utf-8", "replace"), "truncated": True, "stopped": True}, None
        try:
            out, err = proc.communicate(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                out, err = proc.communicate(timeout=5)
            except Exception:
                return None, "CONTROL_PLANE_EXEC_TIMEOUT_CLEANUP_UNCERTAIN"
            stdout_b, stderr_b = (out or b"")[:max_output_bytes], (err or b"")[:max_output_bytes]
            return {"exit_code": proc.returncode if proc.returncode is not None else 124,
                    "stdout": stdout_b.decode("utf-8", "replace"), "stderr": stderr_b.decode("utf-8", "replace"),
                    "truncated": True, "timed_out": True}, None
        stdout_b, stderr_b = (out or b"")[:max_output_bytes], (err or b"")[:max_output_bytes]
        truncated = len(out or b"") > max_output_bytes or len(err or b"") > max_output_bytes
        return {"exit_code": proc.returncode if proc.returncode is not None else 1,
                "stdout": stdout_b.decode("utf-8", "replace"), "stderr": stderr_b.decode("utf-8", "replace"),
                "truncated": truncated}, None
    finally:
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass


def _exec_journal_key(action_id: str, attempt_id: str) -> str:
    if (
        EXEC_ACTION_IDENTIFIER_PATTERN.fullmatch(action_id) is None
        or EXEC_ACTION_IDENTIFIER_PATTERN.fullmatch(attempt_id) is None
    ):
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    return f"{action_id}|{attempt_id}"


def _read_exec_journal(journal_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(journal_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": EXEC_JOURNAL_SCHEMA_VERSION, "entries": {}}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CONTROL_PLANE_EXEC_JOURNAL_INVALID") from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "entries"}
        or value.get("schema_version") != EXEC_JOURNAL_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
    ):
        raise RuntimeError("CONTROL_PLANE_EXEC_JOURNAL_INVALID")
    return value


def _record_exec_receipt(journal_path: Path, journal: dict[str, Any], *, state: str, action_id: str,
                         attempt_id: str, receipt_state: str, local_handle: str, payload: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "state": state,
        "action_id": action_id,
        "attempt_id": attempt_id,
        "receipt": _journal_receipt(action_id, attempt_id, receipt_state, local_handle, payload),
    }
    journal["entries"][_exec_journal_key(action_id, attempt_id)] = entry
    _write_json_atomic(journal_path, journal)
    return entry


def _recover_exec_prepared_entry(
    entry: dict[str, Any],
    diagnostic_code: str = "CONTROL_PLANE_EXEC_PREPARED_RECOVERED",
) -> None:
    """Never re-run an exec after its durable pre-effect boundary was crossed."""

    if entry.get("state") != "prepared":
        return
    action_id = str(entry.get("action_id") or "")
    attempt_id = str(entry.get("attempt_id") or "")
    _exec_journal_key(action_id, attempt_id)
    entry["state"] = "unknown"
    entry["receipt"] = _journal_receipt(
        action_id,
        attempt_id,
        "unknown",
        "",
        {
            "schema_version": 1,
            "operation_kind": "control_plane_exec",
            "code": "CONTROL_PLANE_EXEC_EFFECT_UNKNOWN",
            "diagnostic_code": _safe_error_code(
                diagnostic_code,
                "CONTROL_PLANE_EXEC_PREPARED_RECOVERED",
            ),
        },
    )


def _flush_exec_journal(config: dict[str, Any], journal_path: Path, journal: dict[str, Any]) -> int:
    submitted = 0
    for key in sorted(journal["entries"]):
        entry = journal["entries"][key]
        if not isinstance(entry, dict):
            raise RuntimeError("CONTROL_PLANE_EXEC_JOURNAL_INVALID")
        if entry.get("state") == "prepared":
            _recover_exec_prepared_entry(entry)
            _write_json_atomic(journal_path, journal)
        receipt = entry.get("receipt")
        if not isinstance(receipt, dict):
            raise RuntimeError("CONTROL_PLANE_EXEC_JOURNAL_INVALID")
        if receipt.get("receipt_submitted") is not True:
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted += 1
    return submitted


def _safe_exec_bridge_result(
    value: Any,
    request: dict[str, Any],
    expected_policy_sha256: str,
) -> dict[str, Any]:
    """Allowlist one Electron/MCP exec projection before it becomes a receipt."""

    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("operation_kind") != "control_plane_exec":
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("action_id") != request.get("action_id") or value.get("attempt_id") != request.get("attempt_id"):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("task_id") != request.get("task_id") or value.get("writer_lease_generation") != request.get("writer_lease_generation"):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("policy_sha256") != expected_policy_sha256:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("actor") != {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"}:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if value.get("facade_contract") != request.get("facade_contract"):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_CONTRACT_INVALID")
    local_handle = value.get("local_handle") or request.get("local_handle")
    if not isinstance(local_handle, str) or EXEC_LOCAL_HANDLE_PATTERN.fullmatch(local_handle) is None:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    command_id = value.get("command_id") or request.get("command_id")
    job_id = value.get("job_id") or request.get("job_id")
    if not isinstance(command_id, str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(command_id.strip()) is None:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if not isinstance(job_id, str) or EXEC_COMMAND_IDENTIFIER_PATTERN.fullmatch(job_id.strip()) is None:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if request.get("command_id") is not None and command_id.strip() != request["command_id"]:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    if request.get("job_id") is not None and job_id.strip() != request["job_id"]:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID")
    status = value.get("status")
    if status not in {"running", "exited", "terminated", "timeout", "stopped", "reconciled_terminal"}:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    stdout = value.get("stdout", "")
    stderr = value.get("stderr", "")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    if len(stdout.encode("utf-8")) + len(stderr.encode("utf-8")) > int(request["max_output_bytes"]) * 2:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_TOO_LARGE")
    truncated = value.get("truncated")
    timed_out = value.get("timed_out")
    if not isinstance(truncated, bool) or not isinstance(timed_out, bool):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    exit_code = value.get("exit_code")
    if status not in {"running", "reconciled_terminal"} and (not isinstance(exit_code, int) or isinstance(exit_code, bool) or not -255 <= exit_code <= 255):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    if status == "running" and exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    runtime_identity = value.get("runtime_identity")
    if not isinstance(runtime_identity, dict) or set(runtime_identity) != {
        "activation_epoch_id", "process_instance_id", "server_instance_id", "tool_contract_sha256"
    }:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_IDENTITY_INVALID")
    if any(not isinstance(runtime_identity.get(field), str) or not runtime_identity[field].strip() or len(runtime_identity[field]) > 128
           for field in ("activation_epoch_id", "process_instance_id", "server_instance_id")):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_IDENTITY_INVALID")
    if SHA256_PATTERN.fullmatch(str(runtime_identity.get("tool_contract_sha256") or "").lower()) is None:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_IDENTITY_INVALID")
    run_id = value.get("run_id", "")
    wave_id = value.get("wave_id", "")
    if not isinstance(run_id, str) or not isinstance(wave_id, str) or len(run_id) > 128 or len(wave_id) > 128:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    output_refs = value.get("output_refs")
    if output_refs is not None and not isinstance(output_refs, dict):
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_INVALID")
    safe = {
        "status": status,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
        "timed_out": timed_out,
        "command_id": command_id,
        "job_id": job_id,
        "run_id": run_id,
        "wave_id": wave_id,
        "output_refs": output_refs,
    }
    expected_response = hashlib.sha256(json.dumps(
        safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if str(value.get("response_sha256") or "").lower() != expected_response:
        raise RuntimeError("CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID")
    return {
        "schema_version": 1,
        "operation_kind": "control_plane_exec",
        "local_handle": local_handle,
        "action_id": request["action_id"],
        "attempt_id": request["attempt_id"],
        "task_id": request["task_id"],
        "writer_lease_generation": request["writer_lease_generation"],
        "policy_sha256": expected_policy_sha256,
        "actor": {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"},
        "facade_contract": dict(request["facade_contract"]),
        "runtime_identity": {
            "activation_epoch_id": runtime_identity["activation_epoch_id"],
            "process_instance_id": runtime_identity["process_instance_id"],
            "server_instance_id": runtime_identity["server_instance_id"],
            "tool_contract_sha256": str(runtime_identity["tool_contract_sha256"]).lower(),
        },
        "command_id": command_id,
        "job_id": job_id,
        "status": status,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
        "timed_out": timed_out,
        "run_id": run_id,
        "wave_id": wave_id,
        "output_refs": output_refs,
        "response_sha256": expected_response,
    }


EXEC_CONTROL_RECONCILE_CODES = frozenset({
    "CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH",
    "CONTROL_PLANE_EXEC_POLICY_CHANGED",
    "CONTROL_PLANE_EXEC_TARGET_MISMATCH",
    "CONTROL_PLANE_EXEC_DEVICE_MISMATCH",
    "CONTROL_PLANE_EXEC_WORKSPACE_MISMATCH",
    "CONTROL_PLANE_EXEC_CONTRACT_CHANGED",
    "CONTROL_PLANE_EXEC_RESULT_INVALID",
    "CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID",
    "CONTROL_PLANE_EXEC_RESULT_IDENTITY_INVALID",
    "CONTROL_PLANE_EXEC_RESULT_CONTRACT_INVALID",
    "CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID",
    "CONTROL_PLANE_EXEC_MCP_REJECTED",
})


def _exec_terminal_state(result: dict[str, Any], *, operation: str) -> str | None:
    """Map one verified bridge result to the central receipt state."""

    status = result.get("status")
    if status == "running":
        return None
    if status == "stopped":
        return "stopped"
    if status == "reconciled_terminal" and result.get("exit_code") is None:
        return "unknown"
    exit_code = result.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return "unknown"
    return "completed" if exit_code == 0 else "failed"


def _store_running_exec_observation(journal_path: Path, journal: dict[str, Any], entry: dict[str, Any], result: dict[str, Any]) -> None:
    entry["state"] = "running"
    entry["result"] = result
    entry.pop("last_control_error", None)
    entry["last_observed_at_ms"] = int(time.time() * 1000)
    _write_json_atomic(journal_path, journal)


def _record_control_result(
    *,
    journal_path: Path,
    journal: dict[str, Any],
    entry: dict[str, Any],
    result: dict[str, Any],
    config: dict[str, Any],
    operation: str,
) -> tuple[str, int]:
    """Persist a poll/stop observation without ever spawning a replacement."""

    state = _exec_terminal_state(result, operation=operation)
    if state is None:
        _store_running_exec_observation(journal_path, journal, entry, result)
        return "running", 0
    action_id = str(entry.get("action_id") or "")
    attempt_id = str(entry.get("attempt_id") or "")
    local_handle = str(result.get("local_handle") or "")
    if state == "unknown":
        payload = dict(result)
        payload["code"] = "CONTROL_PLANE_EXEC_TERMINAL_EVIDENCE_UNCERTAIN"
    else:
        payload = result
    next_entry = _record_exec_receipt(
        journal_path,
        journal,
        state=state,
        action_id=action_id,
        attempt_id=attempt_id,
        receipt_state=state,
        local_handle=local_handle,
        payload=payload,
    )
    next_entry["request"] = entry.get("request")
    next_entry["policy_sha256"] = entry.get("policy_sha256")
    next_entry["result"] = result
    _write_json_atomic(journal_path, journal)
    _submit_receipt(config, next_entry)
    _write_json_atomic(journal_path, journal)
    return state, 1


def _record_exec_control_unknown(
    *, journal_path: Path, journal: dict[str, Any], entry: dict[str, Any], config: dict[str, Any], code: str
) -> int:
    payload = {
        "schema_version": 1,
        "operation_kind": "control_plane_exec",
        "code": code,
        "reconciliation_required": True,
    }
    next_entry = _record_exec_receipt(
        journal_path,
        journal,
        state="unknown",
        action_id=str(entry.get("action_id") or ""),
        attempt_id=str(entry.get("attempt_id") or ""),
        receipt_state="unknown",
        local_handle=str((entry.get("result") or {}).get("local_handle") or ""),
        payload=payload,
    )
    next_entry["request"] = entry.get("request")
    next_entry["policy_sha256"] = entry.get("policy_sha256")
    _write_json_atomic(journal_path, journal)
    _submit_receipt(config, next_entry)
    _write_json_atomic(journal_path, journal)
    return 1


def _control_bridge_observation(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    journal_path: Path,
    journal: dict[str, Any],
    entry: dict[str, Any],
    project_root: Path,
    operation: str,
    signal: str | None = None,
    wait_ms: int | None = None,
) -> tuple[str, int]:
    """Poll or stop one journaled command using only its durable handle."""

    request = entry.get("request")
    prior = entry.get("result")
    if not isinstance(request, dict) or not isinstance(prior, dict):
        return "unknown", _record_exec_control_unknown(
            journal_path=journal_path, journal=journal, entry=entry, config=config,
            code="CONTROL_PLANE_EXEC_JOURNAL_INVALID",
        )
    try:
        control_request = _exec_control_request(
            request,
            prior,
            operation=operation,
            signal=signal,
            wait_ms=wait_ms,
            yield_time_ms=min(30_000, max(0, int(getattr(args, "timeout_seconds", 20) * 1000))),
        )
        policy = _admit_exec_policy_request(args, config_path=config_path, config=config, request=control_request)
        expected_policy_sha256 = _policy_digest(policy)
        if expected_policy_sha256 != entry.get("policy_sha256"):
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CHANGED")
        result, error_code = recovery_exec_bridge(args, project_root, control_request)
        if result is None:
            code = _safe_error_code(error_code, "CONTROL_PLANE_EXEC_CONTROL_UNAVAILABLE")
            if code in EXEC_CONTROL_RECONCILE_CODES:
                return "unknown", _record_exec_control_unknown(
                    journal_path=journal_path, journal=journal, entry=entry, config=config, code=code,
                )
            entry["last_control_error"] = code
            entry["last_observed_at_ms"] = int(time.time() * 1000)
            _write_json_atomic(journal_path, journal)
            return "running", 0
        safe = _safe_exec_bridge_result(result, control_request, expected_policy_sha256)
        # The initial exec_run receipt adds this projection before it is
        # submitted.  Control observations are independently validated and
        # must carry the same bounded byte count before a terminal receipt is
        # relayed; otherwise the central MCP status verifier would discard a
        # valid terminal result as incomplete.
        safe["output_bytes"] = len(safe["stdout"].encode("utf-8")) + len(safe["stderr"].encode("utf-8"))
        state, submitted = _record_control_result(
            journal_path=journal_path, journal=journal, entry=entry, result=safe,
            config=config, operation=operation,
        )
        return state, submitted
    except RuntimeError as error:
        code = _safe_error_code(error, "CONTROL_PLANE_EXEC_CONTROL_INVALID")
        if code in EXEC_CONTROL_RECONCILE_CODES or code in {"CONTROL_PLANE_EXEC_JOURNAL_INVALID", "CONTROL_PLANE_EXEC_POLICY_CHANGED"}:
            return "unknown", _record_exec_control_unknown(
                journal_path=journal_path, journal=journal, entry=entry, config=config, code=code,
            )
        entry["last_control_error"] = code
        entry["last_observed_at_ms"] = int(time.time() * 1000)
        _write_json_atomic(journal_path, journal)
        return "running", 0


def _resume_running_exec_entries(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    journal_path: Path,
    journal: dict[str, Any],
    project_root: Path,
) -> tuple[dict[str, list[str]], int]:
    """Resume exact running handles before accepting any new exec action."""

    summary: dict[str, list[str]] = {"completed": [], "failed": [], "stopped": [], "unknown": [], "running": []}
    submitted = 0
    for key in sorted(list(journal.get("entries", {}))):
        entry = journal["entries"].get(key)
        if not isinstance(entry, dict) or entry.get("state") != "running":
            continue
        state, count = _control_bridge_observation(
            args,
            config_path=config_path,
            config=config,
            journal_path=journal_path,
            journal=journal,
            entry=entry,
            project_root=project_root,
            operation="exec_poll",
        )
        submitted += count
        action_id = str(entry.get("action_id") or "")
        summary.setdefault(state, []).append(action_id)
    return summary, submitted


def _poll_exec_stop_requests(
    args: argparse.Namespace,
    *,
    config_path: Path,
    config: dict[str, Any],
    journal_path: Path,
    journal: dict[str, Any],
    project_root: Path,
) -> tuple[list[str], list[str], int]:
    """Consume stop requests and acknowledge only after terminal evidence."""

    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/exec-stops",
        {},
        f"Node {config['node_secret']}",
    )
    stop_requests = response.get("stop_requests")
    if not isinstance(stop_requests, list):
        raise RuntimeError("CONTROL_PLANE_EXEC_STOP_RESPONSE_INVALID")
    acknowledged: list[str] = []
    pending: list[str] = []
    submitted = 0
    by_action = {
        str(entry.get("action_id")): entry
        for entry in journal.get("entries", {}).values()
        if isinstance(entry, dict) and entry.get("action_id")
    }
    for stop in stop_requests:
        if not isinstance(stop, dict):
            continue
        action_id = str(stop.get("action_id") or "")
        entry = by_action.get(action_id)
        if entry is None:
            pending.append(action_id)
            continue
        state = entry.get("state")
        if state in {"completed", "failed", "stopped", "rejected"}:
            receipt = entry.get("receipt")
            if isinstance(receipt, dict) and receipt.get("receipt_submitted") is not True:
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted += 1
            _request(
                str(config["server_url"]),
                f"/v1/nodes/{config['device_id']}/exec-stops/{action_id}/acknowledge",
                {},
                f"Node {config['node_secret']}",
            )
            acknowledged.append(action_id)
            continue
        if state != "running":
            pending.append(action_id)
            continue
        next_state, count = _control_bridge_observation(
            args,
            config_path=config_path,
            config=config,
            journal_path=journal_path,
            journal=journal,
            entry=entry,
            project_root=project_root,
            operation="exec_stop",
            signal="TERM",
            wait_ms=3_000,
        )
        submitted += count
        if next_state in {"completed", "failed", "stopped", "rejected"}:
            _request(
                str(config["server_url"]),
                f"/v1/nodes/{config['device_id']}/exec-stops/{action_id}/acknowledge",
                {},
                f"Node {config['node_secret']}",
            )
            acknowledged.append(action_id)
        else:
            pending.append(action_id)
    return acknowledged, pending, submitted


def _poll_exec_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _exec_journal_path(config_path)
    journal = _read_exec_journal(journal_path)
    submitted_receipts = _flush_exec_journal(config, journal_path, journal)
    project_root = Path(args.project_root).expanduser().resolve() if getattr(args, "project_root", "") else Path.cwd()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({"execution": "exec_not_started", "reason": reason, "received_action_ids": [],
                          "submitted_receipts": submitted_receipts}, separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({"execution": "exec_not_started", "reason": "runtime_identity_unproven",
                          "received_action_ids": [], "submitted_receipts": submitted_receipts}, separators=(",", ":")))
        return 0
    resumed, resumed_submitted = _resume_running_exec_entries(
        args,
        config_path=config_path,
        config=config,
        journal_path=journal_path,
        journal=journal,
        project_root=project_root,
    )
    submitted_receipts += resumed_submitted
    acknowledged_stops, pending_stops, stop_submitted = _poll_exec_stop_requests(
        args,
        config_path=config_path,
        config=config,
        journal_path=journal_path,
        journal=journal,
        project_root=project_root,
    )
    submitted_receipts += stop_submitted
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/poll",
                        {"limit": 1, "lane": "bounded_exec"}, f"Node {config['node_secret']}")
    actions = response.get("actions")
    if not isinstance(actions, list) or len(actions) > 1:
        raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
    completed: list[str] = []
    failed: list[str] = []
    stopped: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
        action_id = str(action.get("action_id") or "")
        attempt_id = str(action.get("attempt_id") or "")
        if not action_id or not attempt_id:
            raise RuntimeError("CONTROL_PLANE_EXEC_ACTION_DENIED")
        received.append(action_id)
        key = _exec_journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            submitted_receipts += _flush_exec_journal(config, journal_path, journal)
            continue
        try:
            request = _exec_bridge_request(action, config)
            policy = _admit_exec_policy_request(args, config_path=config_path, config=config, request=request)
            expected_policy_sha256 = _policy_digest(policy)
        except RuntimeError as error:
            code = _safe_error_code(error, "CONTROL_PLANE_EXEC_ACTION_DENIED")
            entry = _record_exec_receipt(journal_path, journal, state="rejected", action_id=action_id,
                                         attempt_id=attempt_id, receipt_state="rejected", local_handle="",
                                         payload={"schema_version": 1, "operation_kind": "control_plane_exec", "code": code})
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue
        registry = _read_workspace_registry(_workspace_registry_path(args, config_path))
        entry = _registered_workspace_entry(
            registry, workspace_id=request["workspace_id"], workspace_generation=request["workspace_generation"])
        root = Path(entry["canonical_path"]).resolve()
        cwd_path = (root / request["cwd"]).resolve() if request["cwd"] else root.resolve()
        try:
            cwd_path.relative_to(root.resolve())
        except ValueError:
            entry = _record_exec_receipt(journal_path, journal, state="rejected", action_id=action_id,
                                         attempt_id=attempt_id, receipt_state="rejected", local_handle="",
                                         payload={"schema_version": 1, "operation_kind": "control_plane_exec",
                                                   "code": "CONTROL_PLANE_EXEC_REQUEST_INVALID"})
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue
        ws_lock = _exec_workspace_lock_path(config_path, request["workspace_id"], request["workspace_generation"])
        try:
            ws_file = os.open(str(ws_lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(ws_file)
            ws_locked = True
        except FileExistsError:
            entry = _record_exec_receipt(journal_path, journal, state="rejected", action_id=action_id,
                                         attempt_id=attempt_id, receipt_state="rejected", local_handle="",
                                         payload={"schema_version": 1, "operation_kind": "control_plane_exec",
                                                   "code": "CONTROL_PLANE_EXEC_WORKSPACE_BUSY"})
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            rejected.append(action_id)
            continue
        try:
            journal["entries"][key] = {
                "state": "prepared",
                "action_id": action_id,
                "attempt_id": attempt_id,
                "request": request,
                "policy_sha256": expected_policy_sha256,
            }
            _write_json_atomic(journal_path, journal)
            result, error_code = recovery_exec_bridge(args, project_root, request)
            if result is not None:
                safe = _safe_exec_bridge_result(result, request, expected_policy_sha256)
                safe["output_bytes"] = len(safe["stdout"].encode("utf-8")) + len(safe["stderr"].encode("utf-8"))
                status = safe["status"]
                if status == "running":
                    # The initial MCP yield returned a durable command handle.
                    # Keep the original request and handle in the journal; a
                    # later poll wave will use command_control and must never
                    # spawn a replacement command.
                    journal["entries"][key] = {
                        "state": "running",
                        "action_id": action_id,
                        "attempt_id": attempt_id,
                        "request": request,
                        "policy_sha256": expected_policy_sha256,
                        "result": safe,
                    }
                    entry = _record_exec_receipt(
                        journal_path, journal, state="running", action_id=action_id,
                        attempt_id=attempt_id, receipt_state="accepted",
                        local_handle=safe["local_handle"], payload=safe,
                    )
                    entry["request"] = request
                    entry["policy_sha256"] = expected_policy_sha256
                    entry["result"] = safe
                    journal["entries"][key] = entry
                    # Persist the complete running projection before crossing
                    # the central receipt boundary.  If the central service
                    # commits the receipt but the response/ACK is lost, the
                    # next invocation must still have the exact request and
                    # local handle needed for poll/stop; otherwise it could
                    # downgrade a live effect to an unrecoverable unknown.
                    _write_json_atomic(journal_path, journal)
                    _submit_receipt(config, entry)
                    _write_json_atomic(journal_path, journal)
                    submitted_receipts += 1
                    completed.append(f"{action_id}:running")
                    continue
                terminal = _exec_terminal_state(safe, operation="exec_run")
                if terminal is None:
                    terminal = "unknown"
                entry = _record_exec_receipt(
                    journal_path, journal, state=terminal, action_id=action_id,
                    attempt_id=attempt_id, receipt_state=terminal,
                    local_handle=safe["local_handle"], payload=safe,
                )
                _submit_receipt(config, entry)
                _write_json_atomic(journal_path, journal)
                submitted_receipts += 1
                (completed if terminal == "completed" else stopped if terminal == "stopped"
                 else failed if terminal == "failed" else unknown).append(action_id)
                continue
            code = _safe_error_code(error_code, "CONTROL_PLANE_EXEC_FAILED")
            # The durable ``prepared`` marker was written before the bridge
            # subprocess was invoked.  From this point a bridge error cannot
            # prove that no local effect crossed the Recovery boundary (the
            # Recovery process may have accepted the request and then died),
            # so it must never be converted into a pre-effect ``rejected``
            # receipt.  Preserve the marker as UNKNOWN and require explicit
            # reconciliation; otherwise a later poll could redeliver exec_run.
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise RuntimeError("CONTROL_PLANE_EXEC_JOURNAL_INVALID")
            _recover_exec_prepared_entry(prepared, code)
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)
        except Exception as error:
            # Once the durable prepared marker exists, the command may have
            # started.  Never turn a crash, bridge failure, or receipt-format
            # regression into another execution attempt.  A terminal receipt
            # that merely failed transport remains pending in the journal and
            # will be replayed unchanged on the next poll.
            prepared = journal["entries"].get(key)
            if not isinstance(prepared, dict) or prepared.get("state") != "prepared":
                raise
            _recover_exec_prepared_entry(prepared, _safe_error_code(error))
            _write_json_atomic(journal_path, journal)
            _submit_receipt(config, prepared)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            unknown.append(action_id)
        finally:
            try:
                ws_lock.unlink()
            except OSError:
                pass
    print(json.dumps({"execution": "exec_once", "runtime_identity": "reported", "received_action_ids": received,
                      "completed_action_ids": completed, "failed_action_ids": failed,
                      "stopped_action_ids": stopped, "rejected_action_ids": rejected,
                      "unknown_action_ids": unknown, "submitted_receipts": submitted_receipts,
                      "resumed": resumed, "acknowledged_stop_action_ids": acknowledged_stops,
                      "pending_stop_action_ids": pending_stops},
                     separators=(",", ":")))
    return 0


def poll_exec_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_exec_lock(_exec_poll_lock_path(config_path),
                              already_running_code="CONTROL_PLANE_EXEC_POLL_ALREADY_RUNNING"):
        return _poll_exec_once(args)


def run_exec_loop(args: argparse.Namespace) -> int:
    interval_seconds = getattr(args, "interval_seconds", 60)
    if not isinstance(interval_seconds, int) or isinstance(interval_seconds, bool) or not 15 <= interval_seconds <= 3600:
        raise RuntimeError("CONTROL_PLANE_EXEC_LOOP_INTERVAL_INVALID")
    max_iterations = args.max_iterations
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or max_iterations < 1:
        raise RuntimeError("CONTROL_PLANE_EXEC_LOOP_ITERATIONS_INVALID")
    if interval_seconds * max_iterations > EXEC_LOOP_MAX_DURATION_SECONDS:
        raise RuntimeError("CONTROL_PLANE_EXEC_LOOP_DURATION_EXCEEDED")
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    completed_iterations = 0
    try:
        with _exclusive_exec_lock(_exec_loop_lock_path(config_path),
                                  already_running_code="CONTROL_PLANE_EXEC_LOOP_ALREADY_RUNNING"):
            for iteration in range(1, max_iterations + 1):
                try:
                    runtime_heartbeat(args)
                    poll_exec_once(args)
                    state, reason = "completed", None
                except RuntimeError as error:
                    reason = _safe_error_code(error)
                    if reason in EXEC_POLICY_STOP_CODES:
                        print(json.dumps({"execution": "exec_loop_stopped", "reason": reason,
                                          "completed_iterations": completed_iterations}, separators=(",", ":")))
                        return 0
                    state = "degraded"
                completed_iterations = iteration
                print(json.dumps({"execution": "exec_loop_iteration", "iteration": iteration,
                                  "state": state, "reason": reason}, separators=(",", ":")))
                if iteration < max_iterations:
                    time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(json.dumps({"execution": "exec_loop_interrupted",
                          "completed_iterations": completed_iterations}, separators=(",", ":")))
        return 130
    return 0


def install_exec_policy(args: argparse.Namespace) -> int:
    if getattr(args, "confirm_install", False) is not True:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_CONFIRMATION_REQUIRED")
    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    raw_prefixes = getattr(args, "allowed_argv_prefix", None) or []
    prefixes: list[list[str]] = []
    for raw in raw_prefixes:
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError) as error:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID") from error
        if not isinstance(parsed, list) or not parsed:
            raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_INVALID")
        prefixes.append([_exec_argv_item(item) for item in parsed])
    if getattr(args, "expires_at_ms", None) is not None:
        raise RuntimeError("CONTROL_PLANE_EXEC_POLICY_EXPIRY_UNSUPPORTED")
    workspace_id = _policy_identifier(getattr(args, "workspace_id", ""), "workspace_id")
    workspace_generation = _policy_identifier(getattr(args, "workspace_generation", ""), "workspace_generation")
    entry = _require_current_local_workspace_registration(
        args, config_path=config_path, workspace_id=workspace_id, workspace_generation=workspace_generation)
    if entry["capabilities"].get("exec") is not True:
        raise RuntimeError("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT")
    policy = _normalise_exec_policy({
        "schema_version": EXEC_POLICY_SCHEMA_VERSION, "enabled": True,
        "authority_mode": EXEC_POLICY_STANDING_AUTHORITY,
        "server_origin": _server_origin(config.get("server_url")),
        "owner_id": _policy_identifier(getattr(args, "owner_id", ""), "owner_id"),
        "device_id": _policy_identifier(config.get("device_id"), "device_id"),
        "endpoint_id": _policy_identifier(config.get("endpoint_id"), "endpoint_id"),
        "workspace_id": workspace_id, "workspace_generation": workspace_generation,
        "expires_at_ms": None,
        "facade_contract": _policy_facade_contract(
            getattr(args, "facade_schema_version", None), getattr(args, "facade_profile", None),
            getattr(args, "facade_sha256", None)),
        "allowed_argv_prefixes": prefixes,
        "max_timeout_ms": getattr(args, "max_timeout_ms", None),
        "max_output_bytes": getattr(args, "max_output_bytes", None),
        "max_concurrent": 2,
    }, require_enabled=True)
    _write_local_policy(_exec_policy_path(args), policy, replace=getattr(args, "replace", False) is True)
    print(json.dumps({"execution": "exec_policy_installed", "policy_sha256": _policy_digest(policy),
                      "authority_mode": policy["authority_mode"], "expires_at_ms": None}, separators=(",", ":")))
    return 0


def inspect_exec_policy(args: argparse.Namespace) -> int:
    policy = _read_exec_policy(_exec_policy_path(args))
    print(json.dumps({"execution": "exec_policy_inspected", "policy_sha256": _policy_digest(policy),
                      "authority_mode": policy["authority_mode"], "expires_at_ms": None,
                      "enabled": policy["enabled"]},
                     separators=(",", ":")))
    return 0


def disable_exec_policy(args: argparse.Namespace) -> int:
    path = _exec_policy_path(args)
    try:
        policy = _read_exec_policy(path)
    except RuntimeError as error:
        if _safe_error_code(error) == "CONTROL_PLANE_EXEC_POLICY_MISSING":
            print(json.dumps({"execution": "exec_policy_disabled", "reason": "already_missing"},
                             separators=(",", ":")))
            return 0
        raise
    policy["enabled"] = False
    _write_json_atomic(path, policy)
    print(json.dumps({"execution": "exec_policy_disabled"}, separators=(",", ":")))
    return 0


def _artifact_action_text(action: dict[str, Any], field: str) -> str:
    value = action.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
    return value


def _poll_artifact_once(args: argparse.Namespace) -> int:
    """Poll one scoped document/image read under the file-read allowlist.

    Artifacts reuse the C3 file-read policy allowlist so no second path
    universe is introduced. Docs must decode as UTF-8 within caps; images
    must match the MIME allowlist by magic bytes and size caps. Every
    rejection is a durable receipt, never a silent skip.
    """
    import base64 as _b64

    config_path = Path(args.config).expanduser().resolve()
    config = _config(config_path)
    journal_path = _file_read_journal_path(config_path)
    journal = _read_file_read_journal(journal_path)
    submitted_receipts = _flush_file_read_journal(config, journal_path, journal)
    project_root = Path(args.project_root).expanduser().resolve() if getattr(args, "project_root", "") else Path.cwd()
    status = _runtime_status(args, project_root)
    readiness, reason = runtime_readiness(status)
    if readiness != "ready":
        print(json.dumps({"execution": "artifact_not_started", "reason": reason,
                          "received_action_ids": [], "submitted_receipts": submitted_receipts},
                         separators=(",", ":")))
        return 0
    identity = observed_runtime_identity(recovery_identity_observation(args, project_root))
    if identity is None:
        print(json.dumps({"execution": "artifact_not_started", "reason": "runtime_identity_unproven",
                          "received_action_ids": [], "submitted_receipts": submitted_receipts},
                         separators=(",", ":")))
        return 0
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/poll",
                        {"limit": 1, "lane": "bounded_artifact"}, f"Node {config['node_secret']}")
    actions = response.get("actions")
    if not isinstance(actions, list) or len(actions) > 1:
        raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
    completed: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    received: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
        action_id = _artifact_action_text(action, "action_id")
        attempt_id = _artifact_action_text(action, "attempt_id")
        received.append(action_id)
        key = _file_read_journal_key(action_id, attempt_id)
        if key in journal["entries"]:
            submitted_receipts += _flush_file_read_journal(config, journal_path, journal)
            continue
        try:
            kind = action.get("mcp_artifact_kind")
            rel = action.get("mcp_artifact_path")
            if kind not in ("document", "image"):
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            if not isinstance(rel, str) or not rel:
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            if action.get("device_id") != config["device_id"] or action.get("endpoint_id") != config["endpoint_id"]:
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            policy, entry = _file_read_policy_admission(
                args,
                config_path=config_path,
                config=config,
            )
            for field in ("owner_id", "device_id", "endpoint_id", "workspace_id", "workspace_generation"):
                if action.get(field) != policy[field]:
                    raise RuntimeError("CONTROL_PLANE_FILE_READ_TARGET_MISMATCH")
            rel = _file_read_relative_path(rel, code="CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            if not _policy_path_is_allowed(policy, rel):
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ALLOWLIST_DENIED")
            declared_root = Path(entry["canonical_path"]).absolute()
            root = declared_root.resolve(strict=True)
            if os.path.normcase(str(root)) != os.path.normcase(str(declared_root)):
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            target = root
            for part in rel.split("/"):
                target = target / part
                direct = target.resolve(strict=True)
                if os.path.normcase(str(direct)) != os.path.normcase(str(target.absolute())):
                    raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            if not target.is_file():
                raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            contract = {"schema_version": action.get("mcp_artifact_facade_schema_version"),
                        "profile": action.get("mcp_artifact_facade_profile"),
                        "sha256": action.get("mcp_artifact_facade_contract_sha256")}
            _policy_facade_contract(contract["schema_version"], contract["profile"], contract["sha256"])
            if contract != policy["facade_contract"]:
                raise RuntimeError("CONTROL_PLANE_FILE_READ_CONTRACT_MISMATCH")
            local_handle = f"cp_artifact_{secrets.token_hex(24)}"
            if kind == "document":
                raw = target.read_bytes()
                if len(raw) > 256 * 1024:
                    raise RuntimeError("CONTROL_PLANE_ARTIFACT_TOO_LARGE")
                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED") from error
                for pattern in FILE_READ_SENSITIVE_CONTENT_PATTERNS:
                    if pattern.search(content):
                        raise RuntimeError("CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
                response_sha = hashlib.sha256(json.dumps(
                    {"path": rel, "content": content},
                    ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                payload = {"schema_version": 1, "operation_kind": "control_plane_artifact_document",
                           "local_handle": local_handle, "policy_sha256": _policy_digest(policy),
                           "actor": {"client_id": "electron-control-plane-artifact-bridge", "client_type": "electron"},
                           "facade_contract": contract, "path": rel, "content": content,
                           "response_sha256": response_sha,
                           "runtime_identity": {"activation_epoch_id": identity.get("activation_epoch_id", "epoch"),
                                                "process_instance_id": identity.get("process_instance_id", "proc"),
                                                "server_instance_id": identity.get("server_instance_id", "srv"),
                                                "tool_contract_sha256": identity.get("tool_contract_sha256", "f" * 64)}}
            else:
                raw = target.read_bytes()
                if len(raw) > 1024 * 1024:
                    raise RuntimeError("CONTROL_PLANE_ARTIFACT_TOO_LARGE")
                if raw.startswith(b"\x89PNG\r\n\x1a\n"):
                    mime = "image/png"
                elif raw.startswith(b"\xff\xd8\xff"):
                    mime = "image/jpeg"
                elif raw.startswith(b"RIFF") and b"WEBP" in raw[:16]:
                    mime = "image/webp"
                else:
                    raise RuntimeError("CONTROL_PLANE_ARTIFACT_MIME_DENIED")
                data_b64 = _b64.b64encode(raw).decode("ascii")
                response_sha = hashlib.sha256(json.dumps(
                    {"path": rel, "mime": mime, "data_base64": data_b64},
                    ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                payload = {"schema_version": 1, "operation_kind": "control_plane_artifact_image",
                           "local_handle": local_handle, "policy_sha256": _policy_digest(policy),
                           "actor": {"client_id": "electron-control-plane-artifact-bridge", "client_type": "electron"},
                           "facade_contract": contract, "path": rel, "mime": mime, "data_base64": data_b64,
                           "response_sha256": response_sha,
                           "runtime_identity": {"activation_epoch_id": identity.get("activation_epoch_id", "epoch"),
                                                "process_instance_id": identity.get("process_instance_id", "proc"),
                                                "server_instance_id": identity.get("server_instance_id", "srv"),
                                                "tool_contract_sha256": identity.get("tool_contract_sha256", "f" * 64)}}
        except RuntimeError as error:
            code = _safe_error_code(error, "CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
            pre_effect = code in FILE_READ_PRE_EFFECT_REJECTION_CODES | {
                "CONTROL_PLANE_ARTIFACT_ALLOWLIST_DENIED", "CONTROL_PLANE_ARTIFACT_MIME_DENIED",
                "CONTROL_PLANE_ARTIFACT_TOO_LARGE"}
            entry = _record_file_read_receipt(
                journal_path, journal, state="rejected" if pre_effect else "unknown",
                action_id=action_id, attempt_id=attempt_id,
                receipt_state="rejected" if pre_effect else "unknown", local_handle="",
                payload={"schema_version": 1, "operation_kind": "control_plane_artifact_document"
                         if action.get("mcp_artifact_kind") == "document" else "control_plane_artifact_image",
                         "code": code})
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            (rejected if pre_effect else unknown).append(action_id)
            continue
        journal["entries"][key] = {"state": "prepared", "action_id": action_id, "attempt_id": attempt_id}
        _write_json_atomic(journal_path, journal)
        try:
            entry = _record_file_read_receipt(
                journal_path, journal, state="completed", action_id=action_id, attempt_id=attempt_id,
                receipt_state="completed", local_handle=local_handle, payload=payload)
            _submit_receipt(config, entry)
            _write_json_atomic(journal_path, journal)
            submitted_receipts += 1
            completed.append(action_id)
        except Exception:
            prepared = journal["entries"].get(key)
            if isinstance(prepared, dict) and prepared.get("state") == "prepared":
                journal["entries"][key] = {**prepared, "state": "unknown"}
                _write_json_atomic(journal_path, journal)
                unknown.append(action_id)
            else:
                raise
    print(json.dumps({"execution": "artifact_once", "runtime_identity": "reported",
                      "received_action_ids": received, "completed_action_ids": completed,
                      "rejected_action_ids": rejected, "unknown_action_ids": unknown,
                      "submitted_receipts": submitted_receipts}, separators=(",", ":")))
    return 0


def poll_artifact_once(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    _config(config_path)
    with _exclusive_file_read_lock(_file_read_poll_lock_path(config_path),
                                   already_running_code="CONTROL_PLANE_ARTIFACT_POLL_ALREADY_RUNNING"):
        return _poll_artifact_once(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    enroll = subcommands.add_parser("request-enrollment")
    enroll.add_argument("--config", required=True)
    enroll.add_argument("--server-url", required=True)
    enroll.add_argument("--device-id", required=True)
    enroll.add_argument("--endpoint-id", required=True)
    enroll.add_argument("--display-name", required=True)
    enroll.add_argument("--replace-existing-config", action="store_true")
    # ``node-agent.cmd`` always pins these values to the installed packaged
    # tree. Enrollment does not use the runtime yet, but it must accept the
    # fixed launcher contract so an installed node can bootstrap without a
    # source checkout or a second launcher.
    enroll.add_argument("--project-root", default="")
    enroll.add_argument("--node", default="node")
    enroll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    reconcile = subcommands.add_parser("reconcile-enrollment")
    reconcile.add_argument("--config", required=True)
    reconcile.add_argument("--device-id", required=True)
    reconcile.add_argument("--project-root", default="")
    reconcile.add_argument("--node", default="node")
    reconcile.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    authority_status = subcommands.add_parser("reconcile-authority-status")
    authority_status.add_argument("--config", required=True)
    authority_status.add_argument("--device-id", required=True)
    authority_status.add_argument("--project-root", default="")
    authority_status.add_argument("--node", default="node")
    authority_status.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    policy_authority = subcommands.add_parser("inspect-policy-authority")
    policy_authority.add_argument("--config", required=True)
    policy_authority.add_argument("--workspace-registry", required=True)
    policy_authority.add_argument("--workspace-id", required=True)
    policy_authority.add_argument("--workspace-generation", required=True)
    policy_authority.add_argument("--project-root", default="")
    policy_authority.add_argument("--node", default="node")
    policy_authority.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    rotate = subcommands.add_parser("rotate-credential")
    rotate.add_argument("--config", required=True)
    rotate.add_argument("--project-root", default="")
    rotate.add_argument("--node", default="node")
    rotate.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    register_workspace_parser = subcommands.add_parser("register-workspace")
    register_workspace_parser.add_argument("--config", required=True)
    register_workspace_parser.add_argument("--workspace-registry", required=True)
    register_workspace_parser.add_argument("--workspace-path", required=True)
    register_workspace_parser.add_argument("--display-name", required=True)
    register_workspace_parser.add_argument("--capability-read", action="store_true")
    register_workspace_parser.add_argument("--capability-write", action="store_true")
    register_workspace_parser.add_argument("--capability-exec", action="store_true")
    register_workspace_parser.add_argument("--project-root", default="")
    register_workspace_parser.add_argument("--node", default="node")
    register_workspace_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    list_workspaces_parser = subcommands.add_parser("list-workspaces")
    list_workspaces_parser.add_argument("--config", required=True)
    list_workspaces_parser.add_argument("--workspace-registry", required=True)
    list_workspaces_parser.add_argument("--project-root", default="")
    list_workspaces_parser.add_argument("--node", default="node")
    list_workspaces_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    retire_workspace_parser = subcommands.add_parser("retire-workspace")
    retire_workspace_parser.add_argument("--config", required=True)
    retire_workspace_parser.add_argument("--workspace-registry", required=True)
    retire_workspace_parser.add_argument("--workspace-id", required=True)
    retire_workspace_parser.add_argument("--workspace-generation", required=True)
    retire_workspace_parser.add_argument("--data-root", default="")
    retire_workspace_parser.add_argument("--project-root", default="")
    retire_workspace_parser.add_argument("--node", default="node")
    retire_workspace_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    replace_workspace_parser = subcommands.add_parser("replace-workspace")
    replace_workspace_parser.add_argument("--config", required=True)
    replace_workspace_parser.add_argument("--workspace-registry", required=True)
    replace_workspace_parser.add_argument("--workspace-path", required=True)
    replace_workspace_parser.add_argument("--display-name", required=True)
    replace_workspace_parser.add_argument("--capability-read", action="store_true")
    replace_workspace_parser.add_argument("--capability-write", action="store_true")
    replace_workspace_parser.add_argument("--capability-exec", action="store_true")
    replace_workspace_parser.add_argument("--confirm-replace", action="store_true")
    replace_workspace_parser.add_argument("--expected-workspace-id")
    replace_workspace_parser.add_argument("--expected-workspace-generation")
    replace_workspace_parser.add_argument("--data-root", default="")
    replace_workspace_parser.add_argument("--project-root", default="")
    replace_workspace_parser.add_argument("--node", default="node")
    replace_workspace_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    heart = subcommands.add_parser("heartbeat")
    heart.add_argument("--config", required=True)
    heart.add_argument("--runtime-instance-id", default="unverified")
    heart.add_argument("--mcp-server-instance-id", default="unverified")
    heart.add_argument("--activation-epoch", default="unverified")
    heart.add_argument("--contract-version", default="smart-v3-unverified")
    heart.add_argument("--readiness", choices=("ready", "degraded", "blocked", "unknown"), default="unknown")
    heart.add_argument("--project-root", default="")
    heart.add_argument("--node", default="node")
    heart.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    runtime_heart = subcommands.add_parser("runtime-heartbeat")
    runtime_heart.add_argument("--config", required=True)
    runtime_heart.add_argument("--workspace-registry", required=False, default="")
    runtime_heart.add_argument("--project-root", required=True)
    runtime_heart.add_argument("--node", default="node")
    runtime_heart.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    runtime_heart.add_argument("--timeout-seconds", type=int, default=20)
    runtime_heart.add_argument("--data-root", default="")
    polling = subcommands.add_parser("poll")
    polling.add_argument("--config", required=True)
    polling.add_argument("--limit", type=int, default=10)
    polling.add_argument("--project-root", default="")
    polling.add_argument("--node", default="node")
    polling.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    read_only_poll = subcommands.add_parser("poll-read-only-once")
    read_only_poll.add_argument("--config", required=True)
    read_only_poll.add_argument("--workspace-registry", required=True)
    read_only_poll.add_argument("--project-root", required=True)
    read_only_poll.add_argument("--node", default="node")
    read_only_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    read_only_poll.add_argument("--timeout-seconds", type=int, default=20)
    read_only_poll.add_argument("--limit", type=int, default=1)
    read_only_poll.add_argument("--data-root", default="")
    read_only_loop = subcommands.add_parser("run-read-only-loop")
    read_only_loop.add_argument("--config", required=True)
    read_only_loop.add_argument("--workspace-registry", required=True)
    read_only_loop.add_argument("--project-root", required=True)
    read_only_loop.add_argument("--node", default="node")
    read_only_loop.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    read_only_loop.add_argument("--timeout-seconds", type=int, default=20)
    read_only_loop.add_argument("--limit", type=int, default=1)
    read_only_loop.add_argument("--interval-seconds", type=int, default=60)
    read_only_loop.add_argument("--max-iterations", type=int, default=1)
    read_only_loop.add_argument("--data-root", default="")
    read_only_agent = subcommands.add_parser("run-read-only-agent")
    read_only_agent.add_argument("--config", required=True)
    read_only_agent.add_argument("--workspace-registry", required=True)
    read_only_agent.add_argument("--project-root", required=True)
    read_only_agent.add_argument("--node", default="node")
    read_only_agent.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    read_only_agent.add_argument("--timeout-seconds", type=int, default=20)
    read_only_agent.add_argument("--limit", type=int, default=1)
    read_only_agent.add_argument("--interval-seconds", type=int, default=15)
    read_only_agent.add_argument("--max-backoff-seconds", type=int, default=5 * 60)
    # ``0`` is the production default: the same-user supervisor owns process
    # lifetime. A finite value is retained only for focused test/diagnostic
    # runs, never as an implied Windows scheduler installation.
    read_only_agent.add_argument("--max-iterations", type=int, default=0)
    read_only_agent.add_argument("--data-root", default="")
    connected_agent = subcommands.add_parser("run-connected-agent")
    connected_agent.add_argument("--config", required=True)
    connected_agent.add_argument("--workspace-registry", required=True)
    connected_agent.add_argument("--project-root", required=True)
    connected_agent.add_argument("--node", default="node")
    connected_agent.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    connected_agent.add_argument("--timeout-seconds", type=int, default=20)
    connected_agent.add_argument("--interval-seconds", type=int, default=15)
    connected_agent.add_argument("--max-backoff-seconds", type=int, default=5 * 60)
    connected_agent.add_argument("--max-iterations", type=int, default=0)
    connected_agent.add_argument("--data-root", default="")
    file_read_poll = subcommands.add_parser("poll-file-read-once")
    file_read_poll.add_argument("--config", required=True)
    file_read_poll.add_argument("--workspace-registry", required=True)
    file_read_poll.add_argument("--project-root", required=True)
    file_read_poll.add_argument("--node", default="node")
    file_read_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    file_read_poll.add_argument("--timeout-seconds", type=int, default=20)
    file_read_poll.add_argument("--data-root", default="")
    file_read_loop = subcommands.add_parser("run-file-read-loop")
    file_read_loop.add_argument("--config", required=True)
    file_read_loop.add_argument("--workspace-registry", required=True)
    file_read_loop.add_argument("--project-root", required=True)
    file_read_loop.add_argument("--node", default="node")
    file_read_loop.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    file_read_loop.add_argument("--timeout-seconds", type=int, default=20)
    file_read_loop.add_argument("--interval-seconds", type=int, default=60)
    file_read_loop.add_argument("--max-iterations", type=int, default=1)
    file_read_loop.add_argument("--data-root", default="")
    install_file_read_policy_parser = subcommands.add_parser("install-file-read-policy")
    install_file_read_policy_parser.add_argument("--config", required=True)
    install_file_read_policy_parser.add_argument("--workspace-registry", required=True)
    install_file_read_policy_parser.add_argument("--owner-id", required=True)
    install_file_read_policy_parser.add_argument("--workspace-id", required=True)
    install_file_read_policy_parser.add_argument("--workspace-generation", required=True)
    install_file_read_policy_parser.add_argument("--facade-schema-version", type=int, required=True)
    install_file_read_policy_parser.add_argument("--facade-profile", required=True)
    install_file_read_policy_parser.add_argument("--facade-sha256", required=True)
    file_read_scope = install_file_read_policy_parser.add_mutually_exclusive_group(required=True)
    file_read_scope.add_argument("--allowed-relative-path", action="append")
    file_read_scope.add_argument("--allowed-relative-prefix", action="append")
    install_file_read_policy_parser.add_argument("--max-bytes", type=int, required=True)
    install_file_read_policy_parser.add_argument("--max-lines", type=int, required=True)
    # Omitted expiry installs standing local file-read authority.  The hidden
    # compatibility form remains parseable so an explicit legacy migration can
    # be audited and bounded by FILE_READ_POLICY_MAX_TTL_MS.
    install_file_read_policy_parser.add_argument("--expires-at-ms", type=int, required=False, help=argparse.SUPPRESS)
    install_file_read_policy_parser.add_argument("--confirm-install", action="store_true")
    install_file_read_policy_parser.add_argument("--replace", action="store_true")
    install_file_read_policy_parser.add_argument("--data-root", default="")
    install_file_read_policy_parser.add_argument("--project-root", default="")
    install_file_read_policy_parser.add_argument("--node", default="node")
    install_file_read_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    inspect_file_read_policy_parser = subcommands.add_parser("inspect-file-read-policy")
    inspect_file_read_policy_parser.add_argument("--data-root", default="")
    inspect_file_read_policy_parser.add_argument("--project-root", default="")
    inspect_file_read_policy_parser.add_argument("--node", default="node")
    inspect_file_read_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    disable_file_read_policy_parser = subcommands.add_parser("disable-file-read-policy")
    disable_file_read_policy_parser.add_argument("--confirm-disable", action="store_true")
    disable_file_read_policy_parser.add_argument("--data-root", default="")
    disable_file_read_policy_parser.add_argument("--project-root", default="")
    disable_file_read_policy_parser.add_argument("--node", default="node")
    disable_file_read_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    approved_patch_poll = subcommands.add_parser("poll-approved-patch-once")
    approved_patch_poll.add_argument("--config", required=True)
    approved_patch_poll.add_argument("--workspace-registry", required=True)
    approved_patch_poll.add_argument("--project-root", required=True)
    approved_patch_poll.add_argument("--node", default="node")
    approved_patch_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    approved_patch_poll.add_argument("--timeout-seconds", type=int, default=20)
    approved_patch_poll.add_argument("--data-root", default="")
    approved_patch_loop = subcommands.add_parser("run-approved-patch-loop")
    approved_patch_loop.add_argument("--config", required=True)
    approved_patch_loop.add_argument("--workspace-registry", required=True)
    approved_patch_loop.add_argument("--project-root", required=True)
    approved_patch_loop.add_argument("--node", default="node")
    approved_patch_loop.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    approved_patch_loop.add_argument("--timeout-seconds", type=int, default=20)
    approved_patch_loop.add_argument("--interval-seconds", type=int, default=60)
    approved_patch_loop.add_argument("--max-iterations", type=int, default=1)
    approved_patch_loop.add_argument("--data-root", default="")
    document_write_poll = subcommands.add_parser("poll-document-write-once")
    document_write_poll.add_argument("--config", required=True)
    document_write_poll.add_argument("--workspace-registry", required=True)
    document_write_poll.add_argument("--project-root", required=True)
    document_write_poll.add_argument("--node", default="node")
    document_write_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    document_write_poll.add_argument("--timeout-seconds", type=int, default=20)
    document_write_poll.add_argument("--data-root", default="")
    document_write_loop = subcommands.add_parser("run-document-write-loop")
    document_write_loop.add_argument("--config", required=True)
    document_write_loop.add_argument("--workspace-registry", required=True)
    document_write_loop.add_argument("--project-root", required=True)
    document_write_loop.add_argument("--node", default="node")
    document_write_loop.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    document_write_loop.add_argument("--timeout-seconds", type=int, default=20)
    document_write_loop.add_argument("--interval-seconds", type=int, default=60)
    document_write_loop.add_argument("--max-iterations", type=int, default=1)
    document_write_loop.add_argument("--data-root", default="")
    install_approved_patch_policy_parser = subcommands.add_parser("install-approved-patch-policy")
    install_approved_patch_policy_parser.add_argument("--config", required=True)
    install_approved_patch_policy_parser.add_argument("--workspace-registry", required=True)
    install_approved_patch_policy_parser.add_argument("--owner-id", required=True)
    install_approved_patch_policy_parser.add_argument("--workspace-id", required=True)
    install_approved_patch_policy_parser.add_argument("--workspace-generation", required=True)
    install_approved_patch_policy_parser.add_argument("--facade-schema-version", type=int, required=True)
    install_approved_patch_policy_parser.add_argument("--facade-profile", required=True)
    install_approved_patch_policy_parser.add_argument("--facade-sha256", required=True)
    approved_patch_scope = install_approved_patch_policy_parser.add_mutually_exclusive_group(required=True)
    approved_patch_scope.add_argument("--allowed-relative-path", action="append")
    approved_patch_scope.add_argument("--allowed-relative-prefix", action="append")
    install_approved_patch_policy_parser.add_argument("--max-patch-bytes", type=int, required=True)
    install_approved_patch_policy_parser.add_argument("--max-file-bytes", type=int, required=True)
    # Omitted expiry installs standing local patch authority.  An explicit
    # expiry remains a bounded legacy compatibility installation.
    install_approved_patch_policy_parser.add_argument("--expires-at-ms", type=int, required=False, help=argparse.SUPPRESS)
    install_approved_patch_policy_parser.add_argument("--confirm-install", action="store_true")
    install_approved_patch_policy_parser.add_argument("--replace", action="store_true")
    install_approved_patch_policy_parser.add_argument("--data-root", default="")
    install_approved_patch_policy_parser.add_argument("--project-root", default="")
    install_approved_patch_policy_parser.add_argument("--node", default="node")
    install_approved_patch_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    inspect_approved_patch_policy_parser = subcommands.add_parser("inspect-approved-patch-policy")
    inspect_approved_patch_policy_parser.add_argument("--data-root", default="")
    inspect_approved_patch_policy_parser.add_argument("--project-root", default="")
    inspect_approved_patch_policy_parser.add_argument("--node", default="node")
    inspect_approved_patch_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    disable_approved_patch_policy_parser = subcommands.add_parser("disable-approved-patch-policy")
    disable_approved_patch_policy_parser.add_argument("--confirm-disable", action="store_true")
    disable_approved_patch_policy_parser.add_argument("--data-root", default="")
    disable_approved_patch_policy_parser.add_argument("--project-root", default="")
    disable_approved_patch_policy_parser.add_argument("--node", default="node")
    disable_approved_patch_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    exec_poll = subcommands.add_parser("poll-exec-once")
    exec_poll.add_argument("--config", required=True)
    exec_poll.add_argument("--workspace-registry", required=True)
    exec_poll.add_argument("--project-root", required=True)
    exec_poll.add_argument("--node", default="node")
    exec_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    exec_poll.add_argument("--timeout-seconds", type=int, default=20)
    exec_poll.add_argument("--data-root", default="")
    exec_loop = subcommands.add_parser("run-exec-loop")
    exec_loop.add_argument("--config", required=True)
    exec_loop.add_argument("--workspace-registry", required=True)
    exec_loop.add_argument("--project-root", required=True)
    exec_loop.add_argument("--node", default="node")
    exec_loop.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    exec_loop.add_argument("--timeout-seconds", type=int, default=20)
    exec_loop.add_argument("--interval-seconds", type=int, default=60)
    exec_loop.add_argument("--max-iterations", type=int, default=1)
    exec_loop.add_argument("--data-root", default="")
    install_exec_policy_parser = subcommands.add_parser("install-exec-policy")
    install_exec_policy_parser.add_argument("--config", required=True)
    install_exec_policy_parser.add_argument("--workspace-registry", required=True)
    install_exec_policy_parser.add_argument("--owner-id", required=True)
    install_exec_policy_parser.add_argument("--workspace-id", required=True)
    install_exec_policy_parser.add_argument("--workspace-generation", required=True)
    install_exec_policy_parser.add_argument("--facade-schema-version", type=int, required=True)
    install_exec_policy_parser.add_argument("--facade-profile", required=True)
    install_exec_policy_parser.add_argument("--facade-sha256", required=True)
    install_exec_policy_parser.add_argument("--allowed-argv-prefix", action="append", required=True)
    install_exec_policy_parser.add_argument("--max-timeout-ms", type=int, required=True)
    install_exec_policy_parser.add_argument("--max-output-bytes", type=int, required=True)
    # Standing local exec authority is intentionally not time-limited.  Keep
    # the legacy option parseable only to return a typed migration error.
    install_exec_policy_parser.add_argument("--expires-at-ms", type=int, required=False, help=argparse.SUPPRESS)
    install_exec_policy_parser.add_argument("--confirm-install", action="store_true")
    install_exec_policy_parser.add_argument("--replace", action="store_true")
    install_exec_policy_parser.add_argument("--data-root", default="")
    install_exec_policy_parser.add_argument("--project-root", default="")
    install_exec_policy_parser.add_argument("--node", default="node")
    install_exec_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    inspect_exec_policy_parser = subcommands.add_parser("inspect-exec-policy")
    inspect_exec_policy_parser.add_argument("--data-root", default="")
    inspect_exec_policy_parser.add_argument("--project-root", default="")
    inspect_exec_policy_parser.add_argument("--node", default="node")
    inspect_exec_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    disable_exec_policy_parser = subcommands.add_parser("disable-exec-policy")
    disable_exec_policy_parser.add_argument("--confirm-disable", action="store_true")
    disable_exec_policy_parser.add_argument("--data-root", default="")
    disable_exec_policy_parser.add_argument("--project-root", default="")
    disable_exec_policy_parser.add_argument("--node", default="node")
    disable_exec_policy_parser.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    artifact_poll = subcommands.add_parser("poll-artifact-once")
    artifact_poll.add_argument("--config", required=True)
    artifact_poll.add_argument("--workspace-registry", required=True)
    artifact_poll.add_argument("--project-root", required=True)
    artifact_poll.add_argument("--node", default="node")
    artifact_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    artifact_poll.add_argument("--timeout-seconds", type=int, default=20)
    artifact_poll.add_argument("--data-root", default="")
    install_policy = subcommands.add_parser("install-read-only-policy")
    install_policy.add_argument("--config", required=True)
    install_policy.add_argument("--owner-id", required=True)
    install_policy.add_argument("--workspace-id", required=True)
    install_policy.add_argument("--workspace-generation", required=True)
    install_policy.add_argument("--facade-schema-version", type=int, required=True)
    install_policy.add_argument("--facade-profile", required=True)
    install_policy.add_argument("--facade-sha256", required=True)
    install_policy.add_argument("--expires-at-ms", type=int, required=True)
    install_policy.add_argument("--confirm-install", action="store_true")
    install_policy.add_argument("--replace", action="store_true")
    install_policy.add_argument("--data-root", default="")
    install_policy.add_argument("--project-root", default="")
    install_policy.add_argument("--node", default="node")
    install_policy.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    install_policy_context = subcommands.add_parser("install-read-only-policy-from-context")
    install_policy_context.add_argument("--config", required=True)
    install_policy_context.add_argument("--workspace-registry", required=True)
    install_policy_context.add_argument("--context-id", required=True)
    install_policy_context.add_argument("--confirm-install", action="store_true")
    install_policy_context.add_argument("--replace", action="store_true")
    install_policy_context.add_argument("--data-root", default="")
    install_policy_context.add_argument("--project-root", default="")
    install_policy_context.add_argument("--node", default="node")
    install_policy_context.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    install_policy_assignment = subcommands.add_parser("install-read-only-policy-from-assignment")
    install_policy_assignment.add_argument("--config", required=True)
    install_policy_assignment.add_argument("--workspace-registry", required=True)
    install_policy_assignment.add_argument("--workspace-id", required=True)
    install_policy_assignment.add_argument("--workspace-generation", required=True)
    install_policy_assignment.add_argument("--confirm-install", action="store_true")
    install_policy_assignment.add_argument("--replace", action="store_true")
    install_policy_assignment.add_argument("--data-root", default="")
    install_policy_assignment.add_argument("--project-root", default="")
    install_policy_assignment.add_argument("--node", default="node")
    install_policy_assignment.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    inspect_policy = subcommands.add_parser("inspect-read-only-policy")
    inspect_policy.add_argument("--data-root", default="")
    inspect_policy.add_argument("--project-root", default="")
    inspect_policy.add_argument("--node", default="node")
    inspect_policy.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    disable_policy = subcommands.add_parser("disable-read-only-policy")
    disable_policy.add_argument("--confirm-disable", action="store_true")
    disable_policy.add_argument("--data-root", default="")
    disable_policy.add_argument("--project-root", default="")
    disable_policy.add_argument("--node", default="node")
    disable_policy.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    args = parser.parse_args(argv)
    try:
        return {
            "request-enrollment": request_enrollment,
            "reconcile-enrollment": reconcile_enrollment,
            "reconcile-authority-status": reconcile_authority_status,
            "inspect-policy-authority": inspect_policy_authority,
            "rotate-credential": rotate_node_credential,
            "register-workspace": register_workspace,
            "list-workspaces": list_workspaces,
            "retire-workspace": retire_workspace,
            "replace-workspace": replace_workspace,
            "heartbeat": heartbeat,
            "runtime-heartbeat": runtime_heartbeat,
            "poll": poll,
            "poll-read-only-once": poll_read_only_once,
            "run-read-only-loop": run_read_only_loop,
            "run-read-only-agent": run_read_only_agent,
            "run-connected-agent": run_connected_agent,
            "poll-file-read-once": poll_file_read_once,
            "run-file-read-loop": run_file_read_loop,
            "install-file-read-policy": install_file_read_policy,
            "inspect-file-read-policy": inspect_file_read_policy,
            "disable-file-read-policy": disable_file_read_policy,
            "poll-approved-patch-once": poll_approved_patch_once,
            "run-approved-patch-loop": run_approved_patch_loop,
            "poll-document-write-once": poll_document_write_once,
            "run-document-write-loop": run_document_write_loop,
            "install-approved-patch-policy": install_approved_patch_policy,
            "inspect-approved-patch-policy": inspect_approved_patch_policy,
            "disable-approved-patch-policy": disable_approved_patch_policy,
            "poll-exec-once": poll_exec_once,
            "run-exec-loop": run_exec_loop,
            "install-exec-policy": install_exec_policy,
            "inspect-exec-policy": inspect_exec_policy,
            "disable-exec-policy": disable_exec_policy,
            "poll-artifact-once": poll_artifact_once,
            "install-read-only-policy": install_read_only_policy,
            "install-read-only-policy-from-context": install_read_only_policy_from_context,
            "install-read-only-policy-from-assignment": install_read_only_policy_from_assignment,
            "inspect-read-only-policy": inspect_read_only_policy,
            "disable-read-only-policy": disable_read_only_policy,
        }[args.command](args)
    except RuntimeError as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
