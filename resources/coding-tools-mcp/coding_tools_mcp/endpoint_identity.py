from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from .envutils import ENV_PREFIX


ENDPOINT_IDENTITY_SCHEMA_VERSION = 1
ENDPOINT_META_KEY = "io.coding-tools/endpoint"
ENDPOINT_ROUTING_INSTRUCTIONS_META_KEY = "io.coding-tools/routingInstructions"


def _sha256_identity(kind: str, value: str) -> str:
    return hashlib.sha256(
        f"coding-tools-{kind}-v1\0{value}".encode("utf-8", errors="replace")
    ).hexdigest()


def _normalized_root(root: Path) -> str:
    return os.path.normcase(os.path.normpath(str(root.resolve(strict=False))))


def _bounded_label(value: object, fallback: str) -> str:
    label = " ".join(str(value or "").strip().split())
    label = "".join(character for character in label if ord(character) >= 32)
    return (label[:80] or fallback[:80] or "Local device").strip()


def _route_key(label: str, endpoint_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    return f"{slug[:40] or 'device'}-{endpoint_id[:8]}"


def workspace_binding_id(
    *,
    device_instance_id: object = "",
    workspace_root: object = None,
    generation: object = 0,
) -> str:
    """Return the opaque binding for (device instance, workspace, generation).

    The binding rotates whenever the device instance changes, the active
    workspace switches, or the workspace generation bumps. Only the digest
    leaves this function, so it is safe to carry in receipts, health, and
    attestation metadata without exposing the raw path.
    """
    try:
        generation_value = int(generation or 0)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        generation_value = 0
    try:
        normalized = (
            _normalized_root(Path(workspace_root).resolve(strict=False))  # type: ignore[arg-type]
            if workspace_root is not None
            else ""
        )
    except (TypeError, ValueError, OSError):
        normalized = ""
    return _sha256_identity(
        "workspace-binding",
        f"{str(device_instance_id or '').strip()}\0{normalized}\0{generation_value}",
    )


def endpoint_identity_payload(
    runtime: Any,
    *,
    workspace_root: Path | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Return a non-secret, automatically derived endpoint routing identity.

    Electron supplies a durable installation ``device_id``. Standalone runtimes
    fall back to a workspace-scoped identity instead of collecting an implicit
    machine fingerprint. Dynamic process/epoch fields let clients invalidate a
    stale pin without changing the stable endpoint identity.
    """

    root = (workspace_root or runtime.workspace.root).resolve(strict=False)
    normalized_root = _normalized_root(root)
    device_id = str(os.environ.get(f"{ENV_PREFIX}_DEVICE_ID", "")).strip().lower()
    device_instance_id = str(
        os.environ.get(f"{ENV_PREFIX}_DEVICE_INSTANCE_ID", "")
    ).strip()
    display_name = _bounded_label(
        os.environ.get(f"{ENV_PREFIX}_DEVICE_DISPLAY_NAME", ""),
        root.name or "Local device",
    )
    if device_id:
        endpoint_scope = "device_installation"
        endpoint_id = _sha256_identity("endpoint", device_id)
    else:
        endpoint_scope = "workspace_runtime"
        endpoint_id = _sha256_identity("workspace-endpoint", normalized_root)
    resolved_workspace_id = str(workspace_id or "").strip()
    if not resolved_workspace_id:
        resolver = getattr(runtime, "_content_free_workspace_root_id", None)
        resolved_workspace_id = (
            str(resolver(root))
            if callable(resolver)
            else _sha256_identity("workspace-root", normalized_root)
        )
    activation_epoch_id = str(
        getattr(runtime, "activation_epoch_id", None) or ""
    ).strip()
    generation = int(getattr(runtime, "workspace_generation", 0) or 0)
    return {
        "schema_version": ENDPOINT_IDENTITY_SCHEMA_VERSION,
        "endpoint_id": endpoint_id,
        "endpoint_scope": endpoint_scope,
        "route_key": _route_key(display_name, endpoint_id),
        "display_name": display_name,
        "device_instance_id": device_instance_id or None,
        "workspace": str(root),
        "workspace_name": root.name or str(root),
        "workspace_id": resolved_workspace_id,
        "workspace_generation": generation,
        "workspace_binding_id": workspace_binding_id(
            device_instance_id=device_instance_id,
            workspace_root=root,
            generation=generation,
        ),
        "process_instance_id": str(getattr(runtime, "process_instance_id", "") or "") or None,
        "server_instance_id": str(getattr(runtime, "server_instance_id", "") or "") or None,
        "activation_epoch_id": activation_epoch_id or None,
        "pinning": "endpoint_id+workspace_id+workspace_generation",
        "automatic": True,
    }


def endpoint_server_title(endpoint: dict[str, Any]) -> str:
    label = _bounded_label(endpoint.get("display_name"), "Local device")
    workspace = _bounded_label(endpoint.get("workspace_name"), "workspace")
    return f"Coding Tools · {label} · {workspace}"


def endpoint_routing_instructions(endpoint: dict[str, Any]) -> str:
    return (
        "Automatic endpoint identity: "
        f"route_key={endpoint.get('route_key')}, "
        f"endpoint_id={endpoint.get('endpoint_id')}, "
        f"device={endpoint.get('display_name')}, "
        f"workspace={endpoint.get('workspace')}, "
        f"workspace_id={endpoint.get('workspace_id')}, "
        f"workspace_generation={endpoint.get('workspace_generation')}. "
        "This endpoint is already bound to that device and workspace. Reuse it "
        "for the same task without probing other Coding Tools endpoints merely "
        "to compare identities. Select another endpoint only when the user names "
        "another device/workspace or this endpoint returns a typed unavailable or "
        "stale-identity result. Never silently fail over a mutating task."
    )
