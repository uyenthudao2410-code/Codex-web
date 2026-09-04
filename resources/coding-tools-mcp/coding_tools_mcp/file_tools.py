from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from .fs_utils import (
    ResolvedPath,
    DEFAULT_EXCLUDED_NAMES,
    cached_which,
    entry_for_path,
    file_entry,
    find_literal,
    matches_any_glob,
    normalize_rel_display,
    path_batches,
    search_match_item,
    sort_value,
    walk_files,
)
from .patching import FileBaseline, StagedFile, apply_update_hunks, parse_patch
from .processes import hidden_process_popen_kwargs
from .textutils import DEFAULT_MAX_LINES, truncate_text_head


class FileToolsMixin:
    def _patch_scope_path(self, resolved: ResolvedPath) -> ResolvedPath:
        scope_root = self._current_request_workspace_root().resolve(strict=False)
        containing_root = self.workspace._containing_root(resolved.path.resolve(strict=False))
        if containing_root is None or containing_root.resolve(strict=False) != scope_root:
            raise ToolFailure(
                "ORCHESTRATION_WORKSPACE_MISMATCH",
                "Patch path does not belong to the request-bound workspace.",
                category="security",
                retryable=False,
            )
        return ResolvedPath(
            normalize_rel_display(resolved.path, scope_root),
            resolved.path,
            resolved.existed,
        )

    def _patch_resolve_existing(self, raw_path: str) -> ResolvedPath:
        return self._patch_scope_path(self.resolve_existing(raw_path))

    def _patch_resolve_for_write(self, raw_path: str) -> ResolvedPath:
        return self._patch_scope_path(self.resolve_for_write(raw_path))

    def read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        requested_path = str(args.get("path", ""))
        resolved = self.resolve_existing(requested_path)
        if resolved.path.is_dir():
            raise ToolFailure("IS_DIRECTORY", "Path is a directory.", category="validation")
        max_bytes = int(args.get("max_bytes", 131072))
        start_line = int(args.get("start_line", 1))
        end_line = args.get("end_line")
        max_lines = args.get("max_lines")
        if end_line is not None and max_lines is not None:
            calculated_end_line = start_line + int(max_lines) - 1
            if int(end_line) != calculated_end_line:
                raise ToolFailure("INVALID_ARGUMENT", "end_line and max_lines select different ranges.", category="validation")
        if end_line is None and max_lines is not None:
            end_line = start_line + int(max_lines) - 1
        encoding = args.get("encoding", "utf-8")
        if encoding != "utf-8":
            raise ToolFailure("UNSUPPORTED_ENCODING", "Only utf-8 is supported.", category="validation")
        total_bytes = resolved.path.stat().st_size
        with resolved.path.open("rb") as raw_handle:
            if b"\x00" in raw_handle.read(4096):
                raise ToolFailure("BINARY_FILE", "Binary file read blocked for text tool.", category="validation")
        if start_line < 1:
            raise ToolFailure("INVALID_ARGUMENT", "start_line must be >= 1.", category="validation")
        requested_end = int(end_line) if end_line is not None else None
        selected_parts: list[str] = []
        selected_bytes = 0
        total_lines = 0
        selection_complete = False
        try:
            with resolved.path.open("r", encoding="utf-8", errors="strict", newline="") as handle:
                for total_lines, line in enumerate(handle, start=1):
                    if total_lines < start_line:
                        continue
                    if requested_end is not None and total_lines > requested_end:
                        continue
                    if selection_complete:
                        continue
                    selected_parts.append(line)
                    selected_bytes += len(line.encode("utf-8"))
                    if len(selected_parts) > DEFAULT_MAX_LINES or selected_bytes > max_bytes:
                        selection_complete = True
        except UnicodeDecodeError as exc:
            raise ToolFailure("UNSUPPORTED_ENCODING", "File is not valid utf-8.", category="validation") from exc
        selected = "".join(selected_parts)
        truncation = truncate_text_head(selected, max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        selected = truncation.content
        truncated = truncation.truncated or selection_complete
        end = requested_end if requested_end is not None else total_lines
        if end < start_line:
            selected = ""
        actual_end = min(end, total_lines)
        if truncated and truncation.output_lines > 0:
            actual_end = min(total_lines, start_line + truncation.output_lines - 1)
        next_start_line = actual_end + 1 if truncated and actual_end < total_lines else None
        warnings = []
        if truncated:
            warnings.append("content truncated")
        if truncation.first_line_exceeds_limit:
            warnings.append("first selected line exceeds max_bytes")
        result = {
            "path": resolved.display,
            "content": selected,
            "encoding": "utf-8",
            "max_bytes": max_bytes,
            "start_line": start_line,
            "end_line": actual_end,
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "bytes_read": len(selected.encode("utf-8")),
            "truncated": truncated,
            "truncated_by": truncation.truncated_by or ("bytes" if selection_complete else None),
            "first_line_exceeds_limit": truncation.first_line_exceeds_limit,
            "output_lines": truncation.output_lines,
            "output_bytes": truncation.output_bytes,
            "next_start_line": next_start_line,
            "warnings": warnings,
        }
        if next_start_line is not None:
            result["next_action"] = {
                "tool": "read_file",
                "arguments": {
                    "path": requested_path,
                    "start_line": next_start_line,
                    "max_bytes": max_bytes,
                },
            }
        return result

    def list_dir(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        if not resolved.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Path is not a directory.", category="validation")
        recursive = bool(args.get("recursive", False))
        max_depth = int(args.get("max_depth", 1))
        max_entries = int(args.get("max_entries", 1000))
        include_hidden = bool(args.get("include_hidden", False))
        include_ignored = bool(args.get("include_ignored", False))
        sort_key = args.get("sort", "name")
        entries: list[dict[str, Any]] = []
        truncated = False

        def visit(directory: Path, depth: int) -> None:
            nonlocal truncated
            if truncated:
                return
            try:
                children = list(directory.iterdir())
            except OSError:
                return
            child_rel_paths = [normalize_rel_display(child, self.workspace.root) for child in children]
            ignored = set() if include_ignored else self.workspace.git_ignored_paths(child_rel_paths)
            for child in children:
                if self.workspace.is_ignored_path(
                    child,
                    include_hidden=include_hidden,
                    include_ignored=include_ignored,
                    git_ignored=ignored,
                ):
                    continue
                entries.append(entry_for_path(child, self.workspace.root))
                if len(entries) >= max_entries:
                    truncated = True
                    return
                if recursive and depth < max_depth and child.is_dir() and not child.is_symlink():
                    visit(child, depth + 1)

        visit(resolved.path, 1)
        entries.sort(key=lambda item: sort_value(item, sort_key))
        return {
            "path": resolved.display,
            "entries": entries,
            "truncated": truncated,
            "warnings": ["entry limit reached"] if truncated else [],
        }

    def list_files(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        if not resolved.path.is_dir():
            raise ToolFailure("NOT_A_DIRECTORY", "Path is not a directory.", category="validation")
        patterns_arg = args.get("patterns")
        glob_arg = args.get("glob")
        if isinstance(patterns_arg, list) and patterns_arg:
            patterns = [str(item) for item in patterns_arg]
        elif isinstance(glob_arg, str) and glob_arg:
            patterns = [glob_arg]
        else:
            patterns = ["**/*"]
        exclude_patterns = [str(item) for item in args.get("exclude_patterns", [])]
        include_hidden = bool(args.get("include_hidden", False))
        include_ignored = bool(args.get("include_ignored", False))
        max_results = int(args.get("max_results", 5000))
        fast_result = self._list_files_with_fd(
            resolved,
            patterns,
            exclude_patterns,
            include_hidden=include_hidden,
            include_ignored=include_ignored,
            max_results=max_results,
            sort_key=str(args.get("sort", "path")),
        )
        if fast_result is not None:
            return fast_result
        files: list[dict[str, Any]] = []
        truncated = False
        for batch in path_batches(walk_files(resolved.path), 256):
            # Filter by glob first so git check-ignore only sees candidates.
            candidates = [
                (path, rel)
                for path, rel in ((path, normalize_rel_display(path, self.workspace.root)) for path in batch)
                if matches_any_glob(rel, patterns) and not matches_any_glob(rel, exclude_patterns)
            ]
            ignored = set() if include_ignored else self.workspace.git_ignored_paths([rel for _, rel in candidates])
            for path, rel in candidates:
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                if self.workspace.is_ignored_path(
                    path,
                    include_hidden=include_hidden,
                    include_ignored=include_ignored,
                    git_ignored=ignored,
                ):
                    continue
                files.append(file_entry(path, rel, path.lstat()))
                if len(files) >= max_results:
                    truncated = True
                    break
            if truncated:
                break
        files.sort(key=lambda item: item["modified"] if args.get("sort") == "modified" else item["path"])
        return {
            "path": resolved.display,
            "files": files,
            "truncated": truncated,
            "warnings": ["result limit reached"] if truncated else [],
        }

    def _list_files_with_fd(
        self,
        resolved: ResolvedPath,
        patterns: list[str],
        exclude_patterns: list[str],
        *,
        include_hidden: bool,
        include_ignored: bool,
        max_results: int,
        sort_key: str,
    ) -> dict[str, Any] | None:
        fd = cached_which("fd", "fdfind")
        if not fd or not resolved.path.is_dir():
            return None
        args_base = [
            fd,
            "--glob",
            "--color=never",
            "--type",
            "f",
            "--type",
            "l",
            "--max-results",
            str(max_results),
            "--no-require-git",
        ]
        if include_hidden:
            args_base.append("--hidden")
        if include_ignored:
            args_base.append("--no-ignore")
        else:
            for name in sorted(DEFAULT_EXCLUDED_NAMES):
                args_base.extend(["--exclude", name])
        for pattern in exclude_patterns:
            args_base.extend(["--exclude", pattern])

        paths: dict[str, Path] = {}
        for pattern in patterns:
            effective = pattern
            args = list(args_base)
            if "/" in pattern:
                args.append("--full-path")
                if not pattern.startswith("/") and not pattern.startswith("**/") and pattern != "**":
                    effective = f"**/{pattern}"
            args.extend(["--", effective, "."])
            try:
                completed = subprocess.run(
                    args,
                    cwd=str(resolved.path),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    **hidden_process_popen_kwargs(),
                )
            except Exception:
                return None
            if completed.returncode not in {0, 1}:
                return None
            for raw in completed.stdout.splitlines():
                rel_to_search = raw.strip().removeprefix("./")
                if not rel_to_search:
                    continue
                path = resolved.path / rel_to_search
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                rel = normalize_rel_display(path, self.workspace.root)
                if matches_any_glob(rel, exclude_patterns):
                    continue
                paths[rel] = path
                if len(paths) >= max_results:
                    break
            if len(paths) >= max_results:
                break
        ignored = set() if include_ignored else self.workspace.git_ignored_paths(list(paths))
        files: list[dict[str, Any]] = []
        for rel, path in paths.items():
            if self.workspace.is_ignored_path(
                path,
                include_hidden=include_hidden,
                include_ignored=include_ignored,
                git_ignored=ignored,
            ):
                continue
            try:
                stat = path.lstat()
            except OSError:
                continue
            files.append(file_entry(path, rel, stat))
        files.sort(key=lambda item: item["modified"] if sort_key == "modified" else item["path"])
        truncated = len(paths) >= max_results
        return {
            "path": resolved.display,
            "files": files,
            "truncated": truncated,
            "engine": "fd",
            "warnings": ["result limit reached"] if truncated else [],
        }

    def search_text(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", ""))
        if not query:
            raise ToolFailure("INVALID_ARGUMENT", "query is required.", category="validation")
        resolved = self.resolve_existing(str(args.get("path", ".")))
        regex = bool(args.get("regex", False))
        case_sensitive = bool(args.get("case_sensitive", False))
        include_globs = [str(item) for item in args.get("include_globs", [])]
        if isinstance(args.get("glob"), str):
            include_globs.append(str(args["glob"]))
        exclude_globs = [str(item) for item in args.get("exclude_globs", [])]
        context_lines = int(args.get("context_lines", 0))
        max_results = int(args.get("max_results", 1000))
        max_preview_bytes = int(args.get("max_preview_bytes", 512))
        fast_result = self._search_text_with_rg(
            resolved,
            query,
            regex=regex,
            case_sensitive=case_sensitive,
            include_globs=include_globs,
            exclude_globs=exclude_globs,
            context_lines=context_lines,
            max_results=max_results,
            max_preview_bytes=max_preview_bytes,
        )
        if fast_result is not None:
            return fast_result
        matches: list[dict[str, Any]] = []
        total = 0
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(query, flags) if regex else None
        except re.error as exc:
            raise ToolFailure("INVALID_ARGUMENT", f"Invalid regex: {exc}", category="validation") from exc
        needle = query if case_sensitive else query.lower()

        roots = [resolved.path] if resolved.path.is_file() else walk_files(resolved.path)
        for batch in path_batches(roots, 256):
            # Filter by glob first so git check-ignore runs once per batch of
            # candidates instead of once per walked file.
            candidates = []
            for path in batch:
                if path.is_dir():
                    continue
                if path.is_symlink() and not self.workspace.is_safe_existing_path(path):
                    continue
                rel = normalize_rel_display(path, self.workspace.root)
                if include_globs and not matches_any_glob(rel, include_globs):
                    continue
                if matches_any_glob(rel, exclude_globs):
                    continue
                candidates.append((path, rel))
            ignored = self.workspace.git_ignored_paths([rel for _, rel in candidates])
            for path, rel in candidates:
                if self.workspace.is_ignored_path(path, git_ignored=ignored):
                    continue
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                if b"\x00" in data[:4096]:
                    continue
                try:
                    lines = data.decode("utf-8").splitlines()
                except UnicodeDecodeError:
                    continue
                for index, line in enumerate(lines):
                    if compiled:
                        found = compiled.search(line)
                        if not found:
                            continue
                        column = found.start() + 1
                    else:
                        literal_index = find_literal(line, needle, case_sensitive)
                        if literal_index < 0:
                            continue
                        column = literal_index + 1
                    total += 1
                    if len(matches) >= max_results:
                        continue
                    before = lines[max(0, index - context_lines) : index]
                    after = lines[index + 1 : index + 1 + context_lines]
                    matches.append(search_match_item(rel, index + 1, column, line, before, after, max_preview_bytes))
        return {
            "query": query,
            "matches": matches,
            "total_matches": total,
            "truncated": total > len(matches),
            "warnings": ["result limit reached"] if total > len(matches) else [],
        }

    def _search_text_with_rg(
        self,
        resolved: ResolvedPath,
        query: str,
        *,
        regex: bool,
        case_sensitive: bool,
        include_globs: list[str],
        exclude_globs: list[str],
        context_lines: int,
        max_results: int,
        max_preview_bytes: int,
    ) -> dict[str, Any] | None:
        rg = cached_which("rg")
        if not rg:
            return None
        args = [rg, "--json", "--line-number", "--color=never"]
        if not case_sensitive:
            args.append("--ignore-case")
        if not regex:
            args.append("--fixed-strings")
        for name in sorted(DEFAULT_EXCLUDED_NAMES):
            args.extend(["--glob", f"!{name}/**"])
        for pattern in include_globs:
            args.extend(["--glob", pattern])
        for pattern in exclude_globs:
            args.extend(["--glob", f"!{pattern}"])
        search_path = resolved.display if resolved.display != "." else "."
        args.extend(["--", query, search_path])
        try:
            process = subprocess.Popen(
                args,
                cwd=str(self.workspace.root),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                **hidden_process_popen_kwargs(),
            )
        except OSError:
            return None
        timed_out = threading.Event()

        def stop_timed_out_search() -> None:
            timed_out.set()
            try:
                process.kill()
            except OSError:
                pass

        timeout = threading.Timer(10, stop_timed_out_search)
        timeout.daemon = True
        timeout.start()
        matches: list[dict[str, Any]] = []
        total = 0
        truncated = False
        file_cache: dict[str, list[str]] = {}
        assert process.stdout is not None
        try:
            for raw in process.stdout:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "match":
                    continue
                data = event.get("data") if isinstance(event.get("data"), dict) else {}
                path_text = data.get("path", {}).get("text") if isinstance(data.get("path"), dict) else None
                line_number = data.get("line_number")
                line_text = data.get("lines", {}).get("text") if isinstance(data.get("lines"), dict) else ""
                if not isinstance(path_text, str) or not isinstance(line_number, int):
                    continue
                total += 1
                if len(matches) >= max_results:
                    truncated = True
                    process.terminate()
                    break
                rel = normalize_rel_display((self.workspace.root / path_text).resolve(), self.workspace.root)
                submatches = data.get("submatches") if isinstance(data.get("submatches"), list) else []
                first_submatch = submatches[0] if submatches and isinstance(submatches[0], dict) else {}
                column = int(first_submatch.get("start", 0)) + 1
                sanitized = str(line_text).replace("\r\n", "\n").replace("\r", "").rstrip("\n")
                lines: list[str] = []
                if context_lines > 0:
                    lines = file_cache.get(rel, [])
                    if rel not in file_cache:
                        try:
                            lines = (self.workspace.root / rel).read_text(encoding="utf-8").splitlines()
                        except OSError:
                            lines = []
                        file_cache[rel] = lines
                index = line_number - 1
                before = lines[max(0, index - context_lines) : index] if lines else []
                after = lines[index + 1 : index + 1 + context_lines] if lines else []
                matches.append(search_match_item(rel, line_number, column, sanitized, before, after, max_preview_bytes))
        finally:
            timeout.cancel()
            try:
                process.stdout.close()
            except OSError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        if timed_out.is_set():
            return None
        if not truncated and process.returncode not in {0, 1}:
            return None
        return {
            "query": query,
            "matches": matches,
            "total_matches": total,
            "total_matches_exact": not truncated,
            "truncated": truncated,
            "engine": "rg",
            "warnings": ["result limit reached; search stopped early"] if truncated else [],
        }

    def apply_patch(self, args: dict[str, Any]) -> dict[str, Any]:
        patch = str(args.get("patch", ""))
        dry_run = bool(args.get("dry_run", False))
        with self.patch_lock:
            operations = parse_patch(patch)
            staged: dict[str, StagedFile] = {}
            summaries: list[str] = []
            affected: list[dict[str, str]] = []
            additions = 0
            removals = 0
            for op in operations:
                self._validate_patch_path(op.path, require_existing=op.kind in {"update", "delete"})
                if op.kind in {"add", "update", "delete", "write_exact"}:
                    self.workspace.reject_write_symlink_at(self._request_default_cwd(), op.path)
                if op.move_to:
                    self._validate_patch_path(op.move_to, require_existing=False)
                    self.workspace.reject_write_symlink_at(self._request_default_cwd(), op.move_to)
                if op.kind == "add":
                    target = self._patch_resolve_for_write(op.path)
                    if target.existed:
                        raise ToolFailure("PATCH_FAILED", "Cannot add file that already exists.", category="validation")
                    baseline = FileBaseline.capture(target.path)
                    staged[target.display] = StagedFile(
                        target.display,
                        target.path,
                        op.add_content or "",
                        baseline,
                        None,
                    )
                    affected.append({"path": target.display, "operation": "add"})
                    summaries.append(f"A {target.display}")
                    additions += len((op.add_content or "").splitlines())
                elif op.kind == "write_exact":
                    target = self._patch_resolve_for_write(op.path)
                    if target.display in staged:
                        raise ToolFailure(
                            "PATCH_FAILED",
                            "An exact file path may appear only once in a patch envelope.",
                            category="validation",
                            details={"path": target.display},
                        )
                    baseline = FileBaseline.capture(target.path)
                    actual_preimage = baseline.digest or "absent"
                    expected_preimage = str(op.preimage_sha256 or "")
                    if actual_preimage != expected_preimage:
                        raise ToolFailure(
                            "PATCH_EXACT_PREIMAGE_MISMATCH",
                            "Exact file preimage does not match the current workspace bytes.",
                            category="validation",
                            retryable=True,
                            details={
                                "path": target.display,
                                "expected_sha256": expected_preimage,
                                "actual_sha256": actual_preimage,
                                "retry_hint": "Recapture the current file and regenerate the exact write operation.",
                            },
                        )
                    exact_content = op.add_content or ""
                    actual_postimage = hashlib.sha256(exact_content.encode("utf-8")).hexdigest()
                    if actual_postimage != op.postimage_sha256:
                        raise ToolFailure(
                            "PATCH_EXACT_POSTIMAGE_MISMATCH",
                            "Exact file content changed after patch parsing.",
                            category="validation",
                            details={
                                "path": target.display,
                                "expected_sha256": op.postimage_sha256,
                                "actual_sha256": actual_postimage,
                            },
                        )
                    staged[target.display] = StagedFile(
                        target.display,
                        target.path,
                        exact_content,
                        baseline,
                        baseline.mode,
                    )
                    operation = "update" if baseline.data is not None else "add"
                    affected.append({"path": target.display, "operation": operation})
                    summaries.append(f"M {target.display}" if operation == "update" else f"A {target.display}")
                    additions += len(exact_content.splitlines())
                    removals += len((baseline.data or b"").splitlines())
                elif op.kind == "delete":
                    target = self._patch_resolve_existing(op.path)
                    if target.path.is_dir():
                        raise ToolFailure("PATCH_FAILED", "Cannot delete a directory.", category="validation")
                    prior = staged.get(target.display)
                    baseline = prior.baseline if prior is not None else FileBaseline.capture(target.path)
                    staged[target.display] = StagedFile(target.display, target.path, None, baseline, baseline.mode)
                    affected.append({"path": target.display, "operation": "delete"})
                    summaries.append(f"D {target.display}")
                    removals += len((baseline.data or b"").splitlines())
                elif op.kind == "update":
                    source = self._patch_resolve_existing(op.path)
                    if source.path.is_dir():
                        raise ToolFailure("PATCH_FAILED", "Cannot update a directory.", category="validation")
                    prior = staged.get(source.display)
                    if prior is not None and prior.content is None:
                        raise ToolFailure("PATCH_FAILED", "Cannot update a deleted file.", category="validation")
                    baseline = prior.baseline if prior is not None else FileBaseline.capture(source.path)
                    content = prior.content if prior is not None else baseline.text(source.display)
                    assert content is not None
                    updated = apply_update_hunks(content, op.hunks, op.path)
                    for hunk in op.hunks:
                        for line in hunk:
                            additions += line.startswith("+")
                            removals += line.startswith("-")
                    source_mode = prior.mode if prior is not None else baseline.mode
                    if op.move_to:
                        dest = self._patch_resolve_for_write(op.move_to)
                        if dest.existed and dest.display != source.display:
                            raise ToolFailure("PATCH_FAILED", "Cannot move over an existing file.", category="validation")
                        dest_baseline = baseline if dest.display == source.display else FileBaseline.capture(dest.path)
                        staged[source.display] = StagedFile(
                            source.display,
                            source.path,
                            None,
                            baseline,
                            source_mode,
                        )
                        staged[dest.display] = StagedFile(
                            dest.display,
                            dest.path,
                            updated,
                            dest_baseline,
                            source_mode,
                        )
                        affected.append({"path": dest.display, "old_path": source.display, "operation": "move"})
                        summaries.append(f"R {source.display} -> {dest.display}")
                    else:
                        staged[source.display] = StagedFile(
                            source.display,
                            source.path,
                            updated,
                            baseline,
                            source_mode,
                        )
                        affected.append({"path": source.display, "operation": "update"})
                        summaries.append(f"M {source.display}")
            if not affected:
                raise ToolFailure("PATCH_FAILED", "No files were modified.", category="validation")
            if not dry_run:
                self._commit_staged_files(list(staged.values()))
        return {
            "dry_run": dry_run,
            "clean": True,
            "summary": "\n".join(summaries),
            "affected_files": affected,
            "additions": additions,
            "removals": removals,
            "warnings": [],
        }

    def _validate_patch_path(self, raw_path: str, *, require_existing: bool) -> None:
        if require_existing:
            self._patch_resolve_existing(raw_path)
        else:
            self._patch_resolve_for_write(raw_path)

    def _commit_staged_files(self, staged: list[StagedFile]) -> None:
        self.patch_committer.commit(staged)
        for change in staged:
            if change.display in self.patch_baselines:
                continue
            self.patch_baselines[change.display] = (
                None if change.baseline.data is None else change.baseline.data.decode("utf-8", errors="replace")
            )


    def read_files(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_items = args.get("files")
        if raw_items is None:
            raw_items = args.get("paths", [])
        if not isinstance(raw_items, list) or not raw_items:
            raise ToolFailure("INVALID_ARGUMENT", "files or paths must be a non-empty list.", category="validation")
        results: list[dict[str, Any]] = []
        total_bytes = 0
        max_total = min(max(int(args.get("max_total_bytes", 262144)), 1024), 1048576)
        for item in raw_items[:50]:
            spec = {"path": item} if isinstance(item, str) else dict(item) if isinstance(item, dict) else None
            if not spec or not spec.get("path"):
                continue
            remaining = max_total - total_bytes
            if remaining <= 0:
                break
            spec["max_bytes"] = min(int(spec.get("max_bytes", 131072)), remaining)
            payload = self.read_file(spec)
            total_bytes += len(str(payload.get("content", "")).encode("utf-8"))
            results.append(payload)
        return {"files": results, "count": len(results), "total_content_bytes": total_bytes, "truncated": len(results) < len(raw_items)}

    def file_batch(self, args: dict[str, Any]) -> dict[str, Any]:
        operations = args.get("operations", [])
        if not isinstance(operations, list) or not operations:
            raise ToolFailure("INVALID_ARGUMENT", "operations must be a non-empty list.", category="validation")
        dry_run = bool(args.get("dry_run", False))
        results: list[dict[str, Any]] = []
        affected: list[dict[str, str]] = []
        for item in operations[:100]:
            if not isinstance(item, dict):
                raise ToolFailure("INVALID_ARGUMENT", "Each operation must be an object.", category="validation")
            action = str(item.get("action", "")).lower()
            source_raw = str(item.get("path", item.get("source", "")))
            if action == "mkdir":
                target = self.resolve_for_write(source_raw)
                if not dry_run:
                    target.path.mkdir(parents=bool(item.get("parents", True)), exist_ok=bool(item.get("exist_ok", True)))
                results.append({"action": action, "path": target.display})
                affected.append({"path": target.display, "operation": "mkdir"})
                continue
            source = self.resolve_existing(source_raw)
            if action in {"copy", "move"}:
                target = self.resolve_for_write(str(item.get("target", "")))
                if not dry_run:
                    target.path.parent.mkdir(parents=True, exist_ok=True)
                    if target.path.exists() and not bool(item.get("overwrite", False)):
                        raise FileExistsError(target.path)
                    if action == "copy":
                        shutil.copytree(source.path, target.path, dirs_exist_ok=bool(item.get("overwrite", False))) if source.path.is_dir() else shutil.copy2(source.path, target.path)
                    else:
                        if target.path.exists() and not bool(item.get("overwrite", False)):
                            raise FileExistsError(target.path)
                        shutil.move(str(source.path), str(target.path))
                results.append({"action": action, "source": source.display, "target": target.display})
                affected.append({"path": target.display, "operation": action})
            elif action == "delete":
                if not dry_run:
                    if source.path.is_dir():
                        if any(source.path.iterdir()):
                            raise ToolFailure("DIRECTORY_NOT_EMPTY", "Batch delete only removes empty directories.", category="validation", details={"path": source.display})
                        source.path.rmdir()
                    else:
                        source.path.unlink()
                results.append({"action": action, "path": source.display})
                affected.append({"path": source.display, "operation": "delete"})
            else:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown batch action: {action}", category="validation")
        return {"dry_run": dry_run, "results": results, "count": len(results), "affected_files": [] if dry_run else affected}

