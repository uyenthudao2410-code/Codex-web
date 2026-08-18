from __future__ import annotations

import os
from pathlib import Path
from types import ModuleType

from .errors import ToolFailure


def _native_path(value: Path | str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(value))))


def _path_is_within(candidate: Path | str, root: Path | str) -> bool:
    normalized_candidate = _native_path(candidate)
    normalized_root = _native_path(root)
    try:
        return os.path.commonpath((normalized_candidate, normalized_root)) == normalized_root
    except ValueError:
        return False


def _path_belongs_to_root(candidate: Path, root: Path) -> bool:
    if _path_is_within(candidate, root):
        return True
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError):
        return False
    return _path_is_within(resolved, root)


def install_workspace_truth_guard(server_module: ModuleType) -> ModuleType:
    """Make the Runtime-configured workspace authoritative for absolute paths.

    Relative paths continue to resolve from the active workspace/default cwd.
    Absolute paths are accepted only when they belong to the active workspace
    or one of the explicitly configured authorized roots. Canonical aliases
    into an allowed root remain valid; the existing resolver still performs
    the final symlink/canonical security checks.
    """

    current = server_module.Workspace
    if getattr(current, "_workspace_truth_guard_installed", False):
        return server_module

    class AuthoritativeWorkspace(current):
        _workspace_truth_guard_installed = True

        def _candidate(self, base: Path, raw_path: str) -> Path:
            if isinstance(raw_path, str) and raw_path and "\x00" not in raw_path:
                supplied = Path(raw_path).expanduser()
                if supplied.is_absolute() and not any(
                    _path_belongs_to_root(supplied, root) for root in self.authorized_roots
                ):
                    raise ToolFailure(
                        "STALE_WORKSPACE_CONTEXT",
                        "Absolute path does not belong to the active workspace or authorized roots. "
                        "Use '.' for the active workspace or explicitly authorize the external root.",
                        category="security",
                        retryable=False,
                        details={
                            "active_workspace": str(self.root),
                            "requested_path": str(supplied),
                        },
                    )
            return super()._candidate(base, raw_path)

    AuthoritativeWorkspace.__name__ = "Workspace"
    AuthoritativeWorkspace.__qualname__ = "Workspace"
    server_module.Workspace = AuthoritativeWorkspace
    return server_module
