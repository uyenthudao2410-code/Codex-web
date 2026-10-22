from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .envutils import ENV_PREFIX
from .errors import ToolFailure
from .fs_utils import DEFAULT_EXCLUDED_NAMES, ResolvedPath, is_relative_to, normalize_rel_display
from .processes import hidden_process_popen_kwargs


class Workspace:
    """Workspace and explicitly authorized-root path boundary."""

    def __init__(self, root: Path, authorized_roots: list[Path] | None = None) -> None:
        self.root = root.expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ToolFailure("INVALID_ARGUMENT", "Workspace root must be a directory.", category="validation")
        unsafe_roots = {"/"}
        try:
            unsafe_roots.add(str(Path.home().resolve()))
        except RuntimeError:
            pass
        if str(self.root) in unsafe_roots:
            raise ToolFailure("INVALID_ARGUMENT", "Unsafe workspace root rejected.", category="security")
        roots: list[Path] = [self.root]
        seen = {os.path.normcase(str(self.root))}
        for raw in authorized_roots or []:
            try:
                resolved = raw.expanduser().resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if not resolved.is_dir() or resolved.parent == resolved:
                continue
            key = os.path.normcase(str(resolved))
            if key in seen:
                continue
            seen.add(key)
            roots.append(resolved)
        self.authorized_roots = tuple(roots)
        self.git_path = shutil.which("git")

    def add_authorized_root(self, root: Path) -> bool:
        """Dynamically authorize an additional workspace root at runtime.

        Supports Claude Code-like flexibility in local mode: the operator can
        point the agent at any project directory without restarting the server
        or editing configuration. Returns True if the root was added, False if
        it was already authorized or invalid.
        """
        try:
            resolved = root.expanduser().resolve(strict=True)
        except (OSError, RuntimeError):
            return False
        if not resolved.is_dir() or resolved.parent == resolved:
            return False
        key = os.path.normcase(str(resolved))
        if any(os.path.normcase(str(item)) == key for item in self.authorized_roots):
            return False
        self.authorized_roots = self.authorized_roots + (resolved,)
        return True

    def _candidate(self, base: Path, raw_path: str) -> Path:
        if not isinstance(raw_path, str) or not raw_path:
            raise ToolFailure("INVALID_ARGUMENT", "Path must be a non-empty string.", category="validation")
        if "\x00" in raw_path:
            raise ToolFailure("INVALID_ARGUMENT", "Path contains a NUL byte.", category="validation")
        candidate = Path(raw_path).expanduser()
        if candidate.is_absolute():
            return candidate
        pure = PurePosixPath(raw_path.replace("\\", "/"))
        if any(part == ".." for part in pure.parts):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Path escapes the configured workspace.", category="security")
        return base.joinpath(candidate)

    def _containing_root(self, path: Path) -> Path | None:
        for root in sorted(self.authorized_roots, key=lambda item: len(str(item)), reverse=True):
            if path == root or is_relative_to(path, root):
                return root
        return None

    def _is_allowed(self, path: Path) -> bool:
        return self._containing_root(path) is not None

    def resolve_existing(self, raw_path: str = ".") -> ResolvedPath:
        return self.resolve_existing_at(self.root, raw_path)

    def resolve_existing_at(self, base: Path, raw_path: str = ".") -> ResolvedPath:
        base = self._validate_base(base)
        candidate = self._candidate(base, raw_path or ".")
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", f"Path not found: {raw_path}", category="not_found") from exc
        if not self._is_allowed(resolved):
            code = "SYMLINK_ESCAPE" if candidate.is_symlink() else "PATH_OUTSIDE_WORKSPACE"
            raise ToolFailure(code, "Path is outside the configured workspace and authorized roots.", category="security")
        return ResolvedPath(normalize_rel_display(resolved, self.root), resolved, True)

    def resolve_for_write(self, raw_path: str) -> ResolvedPath:
        return self.resolve_for_write_at(self.root, raw_path)

    def resolve_for_write_at(self, base: Path, raw_path: str) -> ResolvedPath:
        candidate_input = Path(raw_path).expanduser()
        if candidate_input.name in {"", ".", ".."}:
            raise ToolFailure("INVALID_ARGUMENT", "Invalid write target.", category="validation")
        base = self._validate_base(base)
        candidate = self._candidate(base, raw_path)
        if candidate.exists() or candidate.is_symlink():
            resolved = candidate.resolve(strict=True)
            if not self._is_allowed(resolved):
                raise ToolFailure("SYMLINK_ESCAPE", "Path escapes the configured workspace.", category="security")
            return ResolvedPath(normalize_rel_display(resolved, self.root), resolved, True)

        parent = candidate.parent
        missing: list[Path] = []
        while not parent.exists():
            missing.append(parent)
            if any(parent == root for root in self.authorized_roots) or parent.parent == parent:
                break
            parent = parent.parent
        try:
            resolved_parent = parent.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", f"Parent directory not found: {raw_path}", category="not_found") from exc
        if not self._is_allowed(resolved_parent):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Path is outside the configured workspace and authorized roots.", category="security")
        target = resolved_parent.joinpath(*reversed([p.name for p in missing]), candidate.name)
        return ResolvedPath(normalize_rel_display(target, self.root), target, False)

    def _validate_base(self, base: Path) -> Path:
        try:
            resolved = base.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ToolFailure("NOT_FOUND", "Default cwd path no longer exists.", category="not_found") from exc
        if not resolved.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Default cwd is not a directory.", category="validation")
        if not self._is_allowed(resolved):
            raise ToolFailure("PATH_OUTSIDE_WORKSPACE", "Default cwd is outside the configured workspace and authorized roots.", category="security")
        return resolved

    def reject_write_symlink(self, raw_path: str) -> None:
        self.reject_write_symlink_at(self.root, raw_path)

    def reject_write_symlink_at(self, base: Path, raw_path: str) -> None:
        base = self._validate_base(base)
        candidate = self._candidate(base, raw_path)
        if candidate.is_symlink():
            raise ToolFailure("SYMLINK_ESCAPE", "Writing through symlinks is denied.", category="security")

    def is_ignored_path(
        self,
        path: Path,
        *,
        include_hidden: bool = False,
        include_ignored: bool = False,
        git_ignored: set[str] | None = None,
    ) -> bool:
        resolved_path = path.resolve(strict=False)
        boundary = self._containing_root(resolved_path)
        if boundary is None:
            return True
        rel = resolved_path.relative_to(boundary)
        parts = rel.parts
        if not include_hidden and any(part.startswith(".") for part in parts if part not in {".", ""}):
            return True
        if not include_ignored and any(part in DEFAULT_EXCLUDED_NAMES for part in parts):
            return True
        if include_ignored:
            return False
        rel_text = rel.as_posix()
        if boundary == self.root and rel_text in (git_ignored if git_ignored is not None else self.git_ignored_paths([rel_text])):
            return True
        return False

    def is_safe_existing_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError:
            return False
        return self._is_allowed(resolved)

    def git_ignored_paths(self, rel_paths: list[str]) -> set[str]:
        if not rel_paths:
            return set()
        git = self.git_path
        if not git:
            return set()
        try:
            completed = subprocess.run(
                [git, "-C", str(self.root), "check-ignore", "--stdin", "-z"],
                input="\0".join(rel_paths) + "\0",
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=2,
                **hidden_process_popen_kwargs(),
            )
        except (OSError, subprocess.SubprocessError):
            return set()
        if completed.returncode not in {0, 1}:
            return set()
        return {path for path in completed.stdout.split("\0") if path}


class _PrimaryLedgerCompatibilityView:
    """Read-compatible view for exact durable-ID lookups across workspace ledgers."""

    _FALLBACK_READS = frozenset({
        "get_run", "get_controller_lease", "get_write_fence", "get_wave",
        "list_waves", "get_background_operation", "get_idempotency",
    })

    def __init__(self, runtime: Any, primary: Any) -> None:
        self._runtime = runtime
        self._primary = primary

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._primary, name)
        if name not in self._FALLBACK_READS or not callable(attribute):
            return attribute

        def lookup(*args: Any, **kwargs: Any) -> Any:
            result = attribute(*args, **kwargs)
            if result not in (None, [], {}):
                return result
            for ledger in self._runtime._orchestration_ledgers.values():
                if ledger is self._primary:
                    continue
                candidate = getattr(ledger, name)(*args, **kwargs)
                if candidate not in (None, [], {}):
                    return candidate
            return result

        return lookup


def configured_authorized_roots() -> list[Path]:
    raw = os.environ.get(f"{ENV_PREFIX}_AUTHORIZED_ROOTS", "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = [item for item in raw.split(os.pathsep) if item]
    if not isinstance(parsed, list):
        return []
    return [Path(str(item)) for item in parsed if str(item).strip()]
