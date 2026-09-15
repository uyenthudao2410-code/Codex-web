"""Minimal Windows/other-node client for enrollment, heartbeat and safe polling.

The agent never executes a received action. It prepares the authenticated node
transport and leaves local Coding Tools admission/execution for the next phase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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
    """Map the existing Hub's fail-closed status projection to a node state."""
    if status.get("fully_ready") == "true" and status.get("components_ready") == "true" and status.get("error_code") in {None, "none"}:
        return "ready", "fully_ready"
    if status.get("state") == "MISSING" or status.get("host") != "available":
        return "blocked", "runtime_unavailable"
    if status.get("runtime_telemetry_available") == "true" or status.get("state") == "CURRENT":
        return "degraded", "admission_or_connector_pending"
    return "unknown", "status_not_actionable"


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
    status = parse_dev_ui_status(completed.stdout)
    readiness, reason = runtime_readiness(status)
    config = _config(Path(args.config).expanduser().resolve())
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/heartbeat", {
        "endpoint_id": config["endpoint_id"],
        "runtime_instance_id": status.get("instance", "unreported"),
        "activation_epoch": "unreported",
        "contract_version": "smart-v3",
        "readiness": readiness,
    }, f"Node {config['node_secret']}")
    print(json.dumps({
        "device_id": response.get("device_id"),
        "readiness": response.get("readiness"),
        "reason": reason,
        "runtime_state": status.get("state", "unknown"),
        "fully_ready": status.get("fully_ready", "unknown"),
    }, separators=(",", ":")))
    return 0


def poll(args: argparse.Namespace) -> int:
    config = _config(Path(args.config).expanduser().resolve())
    response = _request(str(config["server_url"]), f"/v1/nodes/{config['device_id']}/poll", {"limit": args.limit}, f"Node {config['node_secret']}")
    actions = response.get("actions")
    print(json.dumps({"received_action_ids": [item.get("action_id") for item in actions if isinstance(item, dict)] if isinstance(actions, list) else [], "execution": "not_implemented"}, separators=(",", ":")))
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
    args = parser.parse_args(argv)
    try:
        return {"request-enrollment": request_enrollment, "heartbeat": heartbeat, "runtime-heartbeat": runtime_heartbeat, "poll": poll}[args.command](args)
    except RuntimeError as error:
        print(json.dumps({"error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
