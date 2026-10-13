"""Bounded per-lane policy collection; individual authority schemas stay intact."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable

MAX_COLLECTION_BYTES = 2 * 1024 * 1024
MAX_POLICIES = 64
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$")


def scope(value: dict[str, Any]) -> tuple[str, str]:
    result = value.get("workspace_id"), value.get("workspace_generation")
    if any(not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in result):
        raise RuntimeError("CONTROL_PLANE_POLICY_SCOPE_INVALID")
    return result


def entries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
    if "policies" in value:
        if set(value) != {"schema_version", "policies"} or type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
        result = value["policies"]
        if not isinstance(result, list) or not 1 <= len(result) <= MAX_POLICIES:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
    else:
        result = [value]
    seen = set()
    for policy in result:
        if not isinstance(policy, dict) or "policies" in policy:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
        identity = scope(policy)
        if identity in seen:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
        seen.add(identity)
    return result


def read_entries(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.stat().st_size <= 0 or path.stat().st_size > MAX_COLLECTION_BYTES:
        raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_INVALID")
    return entries(json.loads(path.read_text(encoding="utf-8")))


def select(value: Any, target: dict[str, Any] | None = None) -> dict[str, Any]:
    policies = entries(value)
    if target is None:
        if len(policies) != 1:
            raise RuntimeError("CONTROL_PLANE_POLICY_TARGET_REQUIRED")
        return policies[0]
    identity = scope(target)
    matches = [policy for policy in policies if scope(policy) == identity]
    if len(matches) != 1:
        raise RuntimeError("CONTROL_PLANE_POLICY_TARGET_NOT_FOUND")
    return matches[0]


def read_selected(path: Path, target: dict[str, Any] | None = None) -> dict[str, Any]:
    policies = read_entries(path)
    return select({"schema_version": 1, "policies": policies}, target)


def write_policy(path: Path, policy: dict[str, Any], *, replace: bool,
                 atomic_writer: Callable[[Path, dict[str, Any]], None]) -> None:
    """Merge only the exact scope under a cross-process bounded install lock.

    A crash leaves the lock for explicit operator recovery. It is never stolen
    based on age/PID and never permits last-writer-wins scope loss.
    """
    identity = scope(policy)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".install.lock")
    deadline = time.monotonic() + 5
    while True:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError("CONTROL_PLANE_POLICY_INSTALL_BUSY")
            time.sleep(0.05)
    try:
        policies = read_entries(path) if path.exists() else []
        existing = [index for index, prior in enumerate(policies) if scope(prior) == identity]
        if existing and not replace:
            raise RuntimeError("CONTROL_PLANE_POLICY_ALREADY_EXISTS")
        if existing:
            policies[existing[0]] = policy
        else:
            policies.append(policy)
        if len(policies) > MAX_POLICIES:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_FULL")
        value = policies[0] if len(policies) == 1 else {"schema_version": 1, "policies": sorted(policies, key=scope)}
        if len(json.dumps(value).encode()) > MAX_COLLECTION_BYTES:
            raise RuntimeError("CONTROL_PLANE_POLICY_COLLECTION_FULL")
        atomic_writer(path, value)
    finally:
        os.close(descriptor)
        lock.unlink()
