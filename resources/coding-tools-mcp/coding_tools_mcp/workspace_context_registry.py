from __future__ import annotations

import errno
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA_VERSION = 1
REGISTRY_RELATIVE_PATH = Path(".coding-tools") / "orchestration" / "task-context-workspaces.json"
WINDOWS_ATOMIC_REPLACE_ATTEMPTS = 5
WINDOWS_ATOMIC_REPLACE_WINERRORS = frozenset({5, 32})
WINDOWS_ATOMIC_REPLACE_ERRNOS = frozenset({errno.EACCES, errno.EPERM, errno.EBUSY})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class WorkspaceContextRegistry:
    """Durable binding of an opaque execution context to one workspace root.

    This registry is deliberately small and contains only server-derived
    identities.  It is not a transcript, task-state replacement, or authority
    to discover a new workspace after restart: Runtime reauthorizes every
    recorded root against the current configured root set before using it.
    """

    def __init__(self, primary_workspace: Path) -> None:
        self.primary_workspace = primary_workspace.resolve(strict=False)
        self.path = self.primary_workspace / REGISTRY_RELATIVE_PATH
        self._lock = threading.RLock()
        self._contexts: dict[str, dict[str, Any]] = {}
        self._load_error = ""
        self._load()

    def lookup(self, execution_context_id: object) -> dict[str, Any] | None:
        key = str(execution_context_id or "").strip()
        if not key:
            return None
        with self._lock:
            if self._load_error:
                return {"legacy": True, "reason": self._load_error}
            entry = self._contexts.get(key)
            return dict(entry) if isinstance(entry, dict) else None

    def context_ids_for_workspace(self, canonical_root: Path) -> list[str]:
        """Return opaque execution contexts already bound to one exact root."""
        root = str(canonical_root.resolve(strict=False))
        with self._lock:
            if self._load_error:
                return []
            return sorted(
                context_id
                for context_id, entry in self._contexts.items()
                if isinstance(entry, dict)
                and entry.get("legacy") is not True
                and str(entry.get("canonical_root") or "") == root
            )

    def bind(self, execution_context_id: object, *, workspace_id: object, canonical_root: Path) -> dict[str, Any]:
        context = str(execution_context_id or "").strip()
        workspace = str(workspace_id or "").strip()
        root = str(canonical_root.resolve(strict=False))
        if not context or not workspace or not root:
            raise ValueError("execution context, workspace identity, and canonical root are required")
        with self._lock:
            existing = self._contexts.get(context)
            if isinstance(existing, dict) and existing.get("legacy") is not True:
                existing_workspace = str(existing.get("workspace_id") or "").strip()
                existing_root = str(existing.get("canonical_root") or "").strip()
                if existing_workspace and existing_workspace != workspace:
                    raise ValueError("existing context is bound to a different workspace")
                if existing_root and existing_root != root:
                    raise ValueError("existing context is bound to a different canonical root")
            entry = {
                "schema_version": REGISTRY_SCHEMA_VERSION,
                "workspace_id": workspace,
                "canonical_root": root,
                "created_at": str((existing or {}).get("created_at") or _utc_now()),
                "updated_at": _utc_now(),
            }
            self._contexts[context] = entry
            self._write_locked()
            return dict(entry)

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, UnicodeError, json.JSONDecodeError):
            # A malformed registry must not be silently interpreted as an
            # unbound context.  Its known entries become explicit legacy
            # failures when referenced.
            self._load_error = "registry_unreadable"
            return
        if not isinstance(payload, dict):
            self._load_error = "registry_payload_invalid"
            return
        raw_contexts = payload.get("contexts")
        if not isinstance(raw_contexts, dict):
            return
        schema_version = payload.get("schema_version")
        raw_legacy_contexts = payload.get("legacy_contexts")
        if isinstance(raw_legacy_contexts, dict):
            for raw_context, raw_reason in raw_legacy_contexts.items():
                context = str(raw_context or "").strip()
                if context:
                    self._contexts[context] = {
                        "legacy": True,
                        "reason": str(raw_reason or "legacy_workspace_mapping")[:200],
                    }
        for raw_context, raw_entry in raw_contexts.items():
            context = str(raw_context or "").strip()
            if not context:
                continue
            if schema_version != REGISTRY_SCHEMA_VERSION or not isinstance(raw_entry, dict):
                self._contexts[context] = {"legacy": True, "reason": "unsupported_registry_schema"}
                continue
            workspace_id = str(raw_entry.get("workspace_id") or "").strip()
            canonical_root = str(raw_entry.get("canonical_root") or "").strip()
            if not workspace_id or not canonical_root:
                self._contexts[context] = {"legacy": True, "reason": "workspace_identity_missing"}
                continue
            self._contexts[context] = {
                "schema_version": REGISTRY_SCHEMA_VERSION,
                "workspace_id": workspace_id,
                "canonical_root": canonical_root,
                "created_at": str(raw_entry.get("created_at") or ""),
                "updated_at": str(raw_entry.get("updated_at") or ""),
            }

    def _write_locked(self) -> None:
        payload = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "contexts": {
                key: value
                for key, value in sorted(self._contexts.items())
                if value.get("legacy") is not True
            },
            "legacy_contexts": {
                key: str(value.get("reason") or "legacy_workspace_mapping")[:200]
                for key, value in sorted(self._contexts.items())
                if value.get("legacy") is True
            },
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(
            f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            for attempt in range(WINDOWS_ATOMIC_REPLACE_ATTEMPTS):
                try:
                    os.replace(temporary, self.path)
                    break
                except OSError as exc:
                    retryable = bool(
                        os.name == "nt"
                        and (
                            getattr(exc, "winerror", None) in WINDOWS_ATOMIC_REPLACE_WINERRORS
                            or exc.errno in WINDOWS_ATOMIC_REPLACE_ERRNOS
                        )
                    )
                    if not retryable or attempt + 1 >= WINDOWS_ATOMIC_REPLACE_ATTEMPTS:
                        raise
                    time.sleep(0.025 * (attempt + 1))
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
