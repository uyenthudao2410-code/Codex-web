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
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
READ_ONLY_TOOL_NAME = "workspace_context"
READ_ONLY_ARGUMENTS = {"detail": "compact", "max_entries": 1}
READ_ONLY_JOURNAL_SCHEMA_VERSION = 1
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


def _request(url: str, path: str, payload: dict[str, Any], authorization: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(f"{url.rstrip('/')}{path}", data=json.dumps(payload, separators=(",", ":")).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            parsed = json.loads(response.read().decode("utf-8"))
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


def recovery_identity_observation(args: argparse.Namespace, project_root: Path) -> dict[str, Any] | None:
    """Read the one allowlisted identity action without exposing IPC secrets."""
    observer = Path(__file__).with_name("recovery_identity_observer.cjs")
    if not observer.is_file():
        return None
    try:
        completed = subprocess.run(
            [args.node, str(observer), "--project-root", str(project_root)],
            cwd=project_root,
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


def _runtime_status(args: argparse.Namespace, project_root: Path) -> dict[str, str]:
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


def _safe_bridge_result(value: Any, request: dict[str, Any]) -> dict[str, Any]:
    """Allowlist a completed receipt; neither workspace paths nor raw MCP data cross this boundary."""
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_INVALID")
    identity = value.get("runtime_identity")
    actor = value.get("actor")
    facade_contract = value.get("facade_contract")
    if (
        value.get("operation_kind") != "control_plane_read_only_workspace_context"
        or value.get("action_id") != request["action_id"]
        or value.get("attempt_id") != request["attempt_id"]
        or value.get("workspace_accessed") is not True
        or not re.fullmatch(r"cp_ro_[a-f0-9]{48}", str(value.get("local_handle") or ""))
        or not SHA256_PATTERN.fullmatch(str(value.get("policy_sha256") or "").lower())
        or actor != {"client_id": "electron-control-plane-bridge", "client_type": "electron"}
        or not isinstance(identity, dict)
        or not all(isinstance(identity.get(field), str) and 0 < len(identity[field]) <= 128 for field in ("activation_epoch_id", "process_instance_id", "server_instance_id"))
        or not SHA256_PATTERN.fullmatch(str(identity.get("tool_contract_sha256") or "").lower())
        or not isinstance(facade_contract, dict)
        or set(facade_contract) != {"schema_version", "profile", "sha256"}
        or facade_contract != request.get("facade_contract")
        or not SHA256_PATTERN.fullmatch(str(value.get("response_sha256") or "").lower())
    ):
        raise RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_INVALID")
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
        "response_sha256": str(value["response_sha256"]).lower(),
    }


def recovery_read_only_bridge(args: argparse.Namespace, project_root: Path, request: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Call the descriptor-hiding CJS bridge once; errors are returned as typed codes."""
    bridge = Path(__file__).with_name("recovery_read_only_bridge.cjs")
    if not bridge.is_file():
        return None, "CONTROL_PLANE_BRIDGE_UNAVAILABLE"
    try:
        completed = subprocess.run(
            [args.node, str(bridge), "--project-root", str(project_root)],
            cwd=project_root,
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
        try:
            return _safe_bridge_result(payload.get("result"), request), None
        except RuntimeError as error:
            return None, _safe_error_code(error)
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


def _recover_prepared_entry(entry: dict[str, Any]) -> None:
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
    existing = _config(config_path) if config_path.exists() else {}
    node_secret = str(existing.get("node_secret") or secrets.token_urlsafe(32))
    config = {
        "server_url": args.server_url.rstrip("/"),
        "device_id": args.device_id,
        "endpoint_id": args.endpoint_id,
        "display_name": args.display_name,
        "node_secret": node_secret,
    }
    response = _request(config["server_url"], "/v1/enrollment-requests", {
        "device_id": config["device_id"],
        "endpoint_id": config["endpoint_id"],
        "display_name": config["display_name"],
        "credential_hash": _credential_hash(node_secret),
    })
    _write_config(config_path, config)
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
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/heartbeat", {
        "endpoint_id": config["endpoint_id"],
        "runtime_instance_id": projection["runtime_instance_id"],
        "mcp_server_instance_id": projection["mcp_server_instance_id"],
        "activation_epoch": projection["activation_epoch"],
        "contract_version": projection["contract_version"],
        "readiness": projection["readiness"],
    }, f"Node {config['node_secret']}")
    print(json.dumps({
        "device_id": response.get("device_id"),
        "readiness": response.get("readiness"),
        "reason": projection["reason"],
        "runtime_identity": "reported" if projection["runtime_instance_id"] != "unreported" else "unreported",
        "runtime_state": status.get("state", "unknown"),
        "fully_ready": status.get("fully_ready", "unknown"),
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


def poll_read_only_once(args: argparse.Namespace) -> int:
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
        result, error_code = recovery_read_only_bridge(args, project_root, request)
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
            },
        )
        _submit_receipt(config, entry)
        _write_json_atomic(journal_path, journal)
        submitted_receipts += 1
        (rejected if pre_effect else unknown).append(action_id)

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    enroll = subcommands.add_parser("request-enrollment")
    enroll.add_argument("--config", required=True)
    enroll.add_argument("--server-url", required=True)
    enroll.add_argument("--device-id", required=True)
    enroll.add_argument("--endpoint-id", required=True)
    enroll.add_argument("--display-name", required=True)
    heart = subcommands.add_parser("heartbeat")
    heart.add_argument("--config", required=True)
    heart.add_argument("--runtime-instance-id", default="unverified")
    heart.add_argument("--mcp-server-instance-id", default="unverified")
    heart.add_argument("--activation-epoch", default="unverified")
    heart.add_argument("--contract-version", default="smart-v3-unverified")
    heart.add_argument("--readiness", choices=("ready", "degraded", "blocked", "unknown"), default="unknown")
    runtime_heart = subcommands.add_parser("runtime-heartbeat")
    runtime_heart.add_argument("--config", required=True)
    runtime_heart.add_argument("--project-root", required=True)
    runtime_heart.add_argument("--node", default="node")
    runtime_heart.add_argument("--timeout-seconds", type=int, default=20)
    polling = subcommands.add_parser("poll")
    polling.add_argument("--config", required=True)
    polling.add_argument("--limit", type=int, default=10)
    read_only_poll = subcommands.add_parser("poll-read-only-once")
    read_only_poll.add_argument("--config", required=True)
    read_only_poll.add_argument("--project-root", required=True)
    read_only_poll.add_argument("--node", default="node")
    read_only_poll.add_argument("--timeout-seconds", type=int, default=20)
    read_only_poll.add_argument("--limit", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        return {
            "request-enrollment": request_enrollment,
            "heartbeat": heartbeat,
            "runtime-heartbeat": runtime_heartbeat,
            "poll": poll,
            "poll-read-only-once": poll_read_only_once,
        }[args.command](args)
    except RuntimeError as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
