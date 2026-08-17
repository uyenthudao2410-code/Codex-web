from __future__ import annotations

import fnmatch
import os
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .textutils import TextTruncation, truncate_text_head


DEFAULT_EXCLUDED_NAMES = {
    ".git",
    ".reference",
    "node_modules",
    "target",
    "dist",
    "build",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
GREP_MAX_LINE_CHARS = 500

_TOOL_PATHS: dict[str, str] = {}

def cached_which(*names: str) -> str | None:
    """shutil.which with a success-only cache: absence keeps re-probing so a
    tool installed mid-session is still picked up."""
    cached = _TOOL_PATHS.get(names[0])
    if cached:
        return cached
    for name in names:
        path = shutil.which(name)
        if path:
            _TOOL_PATHS[names[0]] = path
            return path
    return None

def entry_for_path(path: Path, root: Path) -> dict[str, Any]:
    stat = path.lstat()
    if path.is_symlink():
        kind = "symlink"
    elif path.is_dir():
        kind = "directory"
    elif path.is_file():
        kind = "file"
    else:
        kind = "other"
    item: dict[str, Any] = {
        "name": path.name,
        "path": normalize_rel_display(path, root),
        "type": kind,
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "is_hidden": path.name.startswith("."),
        "is_ignored": False,
    }
    if path.is_symlink():
        try:
            item["symlink_target"] = os.readlink(path)
        except OSError:
            pass
    return item


def sort_value(item: dict[str, Any], sort_key: str) -> Any:
    if sort_key == "type":
        return (item.get("type", ""), item.get("name", ""))
    if sort_key == "modified":
        return (item.get("modified", ""), item.get("name", ""))
    return item.get("name", "")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False

def truncate_bytes(data: bytes, limit: int) -> tuple[str, bool]:
    if limit <= 0:
        limit = 1
    truncated = len(data) > limit
    if truncated:
        marker = b"\n... output truncated ...\n"
        if limit > len(marker) + 2:
            remaining = limit - len(marker)
            head = max(1, remaining // 2)
            tail = max(1, remaining - head)
            data = data[:head] + marker + data[-tail:]
        else:
            data = data[:limit]
    return data.decode("utf-8", errors="replace"), truncated


def truncate_line_chars(line: str, max_chars: int = GREP_MAX_LINE_CHARS) -> tuple[str, bool]:
    if len(line) <= max_chars:
        return line, False
    suffix = " ... [truncated]"
    keep = max(0, max_chars - len(suffix))
    return line[:keep] + suffix, True


def normalize_rel_display(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return path.as_posix()
    text = rel.as_posix()
    return "." if text == "" else text


def matches_any_glob(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) or PurePosixPath(rel).match(pattern) for pattern in patterns)


def file_entry(path: Path, rel: str, path_stat: os.stat_result) -> dict[str, Any]:
    return {
        "path": rel,
        "type": "symlink" if path.is_symlink() else "file",
        "size_bytes": path_stat.st_size,
        "modified": datetime.fromtimestamp(path_stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def search_match_item(
    rel: str,
    line_number: int,
    column: int,
    line: str,
    before: list[str],
    after: list[str],
    max_preview_bytes: int,
) -> dict[str, Any]:
    preview, line_truncated = truncate_line_chars(line)
    preview_truncation = truncate_text_head(preview, max_lines=1, max_bytes=max_preview_bytes)
    item: dict[str, Any] = {
        "path": rel,
        "line": line_number,
        "column": column,
        "preview": preview_truncation.content,
        "before": before,
        "after": after,
    }
    if line_truncated or preview_truncation.truncated:
        item["preview_truncated"] = True
        item["preview_truncated_by"] = "chars" if line_truncated else preview_truncation.truncated_by
    return item



def walk_files(root: Path) -> Iterator[Path]:
    if root.is_file() or root.is_symlink():
        yield root
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in DEFAULT_EXCLUDED_NAMES]
        current_path = Path(current)
        for name in files:
            yield current_path / name


def path_batches(paths: Iterator[Path], size: int) -> Iterator[list[Path]]:
    batch: list[Path] = []
    for path in paths:
        batch.append(path)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def find_literal(line: str, needle: str, case_sensitive: bool) -> int:
    """Return the match index of a pre-normalized needle (lowered unless
    case_sensitive) in line, or -1."""
    haystack = line if case_sensitive else line.lower()
    return haystack.find(needle)


def truncation_fields(truncation: TextTruncation) -> dict[str, Any]:
    return {
        "truncated": truncation.truncated,
        "truncated_by": truncation.truncated_by,
        "output_lines": truncation.output_lines,
        "output_bytes": truncation.output_bytes,
    }

@dataclass
class ResolvedPath:
    display: str
    path: Path
    existed: bool
