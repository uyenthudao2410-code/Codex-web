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
import errno
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
READ_ONLY_LOOP_MIN_INTERVAL_SECONDS = 15
READ_ONLY_LOOP_MAX_INTERVAL_SECONDS = 60 * 60
READ_ONLY_LOOP_MAX_DURATION_SECONDS = 24 * 60 * 60
READ_ONLY_AGENT_LOCK_SCHEMA_VERSION = 1
READ_ONLY_AGENT_MAX_BACKOFF_SECONDS = 15 * 60
NODE_CONFIG_SCHEMA_VERSION = 1
MAX_HTTP_RESPONSE_BYTES = 256 * 1024
POLICY_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$")
WORKSPACE_SUMMARY_SCHEMA_VERSION = 1
WORKSPACE_SUMMARY_MAX_BYTES = 8 * 1024
WORKSPACE_SUMMARY_TEXT_MAX = 256
WORKSPACE_SUMMARY_ENTRY_TYPES = frozenset({"file", "directory", "symlink", "other"})
WORKSPACE_SUMMARY_PROJECT_TYPES = frozenset({"unknown", "electron", "node", "python", "rust", "go"})
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
})
READ_ONLY_POLICY_STOP_CODES = frozenset({
    "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
    "CONTROL_PLANE_BRIDGE_POLICY_INVALID",
    "CONTROL_PLANE_BRIDGE_POLICY_EXPIRED",
    "CONTROL_PLANE_BRIDGE_DISABLED",
    "CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH",
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


def _config(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError("node_config_missing") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("node_config_invalid")
    return parsed


def _write_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    """Persist non-secret local bridge evidence before an external boundary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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


def _read_only_loop_policy_admission(args: argparse.Namespace) -> None:
    """Reject a loop before it can allocate central delivery work.

    ``poll-read-only-once`` retains its per-action bridge checks so an explicit
    one-shot always records a typed pre-effect receipt when appropriate.  A
    repeating loop must be stricter: an absent, disabled, expired or
    wrong-target policy is a local stop condition, not a reason to dequeue and
    reject new central actions repeatedly.
    """
    config = _config(Path(args.config).expanduser().resolve())
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


def read_only_policy_observation(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    """Project local policy state without exposing its content or granting work.

    The policy remains entirely local authority.  This projection is merely a
    small, typed operator diagnostic that lets the central UI distinguish a
    missing/expired/mismatched policy from an otherwise-ready runtime.
    """

    try:
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
    config = _config(Path(args.config).expanduser().resolve())
    context_id = _policy_identifier(args.context_id, "context_id")
    response = _request(
        str(config["server_url"]),
        f"/v1/nodes/{config['device_id']}/read-only-policy-template",
        {"context_id": context_id},
        f"Node {config['node_secret']}",
    )
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
    if not node_secret:
        node_secret = secrets.token_urlsafe(32)
    config = {
        "schema_version": NODE_CONFIG_SCHEMA_VERSION,
        **requested_target,
        "display_name": args.display_name,
        "node_secret": node_secret,
    }
    # Write before sending so a loss after the server records the request is
    # retried with the same node credential and therefore stays idempotent.
    # Replacing an existing target requires the explicit CLI flag above.
    _write_config(config_path, config)
    response = _request(config["server_url"], "/v1/enrollment-requests", {
        "device_id": config["device_id"],
        "endpoint_id": config["endpoint_id"],
        "display_name": config["display_name"],
        "credential_hash": _credential_hash(node_secret),
    })
    print(json.dumps({"enrollment_id": response.get("enrollment_id"), "device_id": config["device_id"], "state": "pending_operator_approval"}, separators=(",", ":")))
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
    try:
        # ``signal 0`` does not terminate the target.  It is available on the
        # supported Windows/POSIX Python runtimes and avoids introducing a
        # second platform-specific process-control adapter for this one lock.
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as error:
        # On Windows, os.kill(pid, 0) reports a missing PID as WinError 87
        # (and commonly errno=EINVAL), not ProcessLookupError.  Treat that
        # one documented missing-process result as dead so a crashed same-user
        # agent cannot pin its read-only lock forever.  Every other unfamiliar
        # failure remains live/fail-closed.
        if os.name == "nt" and (
            getattr(error, "winerror", None) == 87
            or getattr(error, "errno", None) == errno.EINVAL
        ):
            return False
        # An unfamiliar error must not let this process remove a possibly-live
        # lock. The operator can inspect/stop the existing local owner.
        return True
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
    read_only_poll.add_argument("--project-root", required=True)
    read_only_poll.add_argument("--node", default="node")
    read_only_poll.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
    read_only_poll.add_argument("--timeout-seconds", type=int, default=20)
    read_only_poll.add_argument("--limit", type=int, default=1)
    read_only_poll.add_argument("--data-root", default="")
    read_only_loop = subcommands.add_parser("run-read-only-loop")
    read_only_loop.add_argument("--config", required=True)
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
    install_policy_context.add_argument("--context-id", required=True)
    install_policy_context.add_argument("--confirm-install", action="store_true")
    install_policy_context.add_argument("--replace", action="store_true")
    install_policy_context.add_argument("--data-root", default="")
    install_policy_context.add_argument("--project-root", default="")
    install_policy_context.add_argument("--node", default="node")
    install_policy_context.add_argument("--runtime-mode", choices=("development", "packaged"), default="development")
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
            "heartbeat": heartbeat,
            "runtime-heartbeat": runtime_heartbeat,
            "poll": poll,
            "poll-read-only-once": poll_read_only_once,
            "run-read-only-loop": run_read_only_loop,
            "run-read-only-agent": run_read_only_agent,
            "install-read-only-policy": install_read_only_policy,
            "install-read-only-policy-from-context": install_read_only_policy_from_context,
            "inspect-read-only-policy": inspect_read_only_policy,
            "disable-read-only-policy": disable_read_only_policy,
        }[args.command](args)
    except RuntimeError as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
