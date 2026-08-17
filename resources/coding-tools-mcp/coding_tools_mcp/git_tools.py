from __future__ import annotations

import base64
import difflib
import hashlib
import hmac
import json
from typing import Any

from .errors import ToolFailure
from .patching import read_text_preserve_newlines
from .fs_utils import truncation_fields
from .git_utils import (
    DIFF_CONTINUATION_OPERATION,
    DIFF_CONTINUATION_READ_TRACK_LIMIT,
    DIFF_CONTINUATION_SCHEMA_VERSION,
    PROCESS_DIFF_CONTINUATION_READS,
    PROCESS_DIFF_CONTINUATION_READS_LOCK,
    PROCESS_DIFF_CONTINUATION_SECRET,
    parse_branch_line,
    parse_git_blame_porcelain,
    require_git,
    validate_git_ref,
)
from .textutils import DEFAULT_MAX_LINES, truncate_text_head
from .tool_schema import DIFF_CONTINUATION_TOKEN_MAX_CHARS


def parse_diff_files(diff_text: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                current = {"path": path, "status": "modified", "binary": False}
                files.append(current)
        elif current is not None and line.startswith("new file mode"):
            current["status"] = "added"
        elif current is not None and line.startswith("deleted file mode"):
            current["status"] = "deleted"
        elif current is not None and line.startswith("Binary files"):
            current["binary"] = True
    return files


class GitToolsMixin:
    def git_status(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", ".")))
        max_entries = int(args.get("max_entries", 1000))
        include_untracked = bool(args.get("include_untracked", True))
        git = require_git()
        git_env = self._git_env()
        root_check = self._run_git_text(
            [git, "-C", str(resolved.path), "rev-parse", "--show-toplevel"], env=git_env
        )
        if root_check.returncode != 0:
            return self._git_status_not_repo(root_check)
        status_cmd = [git, "-C", str(resolved.path), "status", "--porcelain=v1", "-b"]
        if not include_untracked:
            status_cmd.append("--untracked-files=no")
        completed = self._run_git_text(status_cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git status failed", category="runtime")
        lines = completed.stdout.splitlines()
        branch = ""
        upstream = ""
        ahead = 0
        behind = 0
        entries: list[dict[str, Any]] = []
        for line in lines:
            if line.startswith("## "):
                branch, upstream, ahead, behind = parse_branch_line(line[3:])
                continue
            if not line:
                continue
            path_text = line[3:]
            original = None
            if " -> " in path_text:
                original, path_text = path_text.split(" -> ", 1)
            entries.append(
                {
                    "path": path_text,
                    "original_path": original,
                    "index_status": line[0],
                    "worktree_status": line[1],
                }
            )
            if len(entries) >= max_entries:
                break
        return {
            "is_repo": True,
            "branch": branch,
            "head": self._git_rev_parse(resolved.path, "HEAD", env=git_env),
            "upstream": upstream,
            "ahead": ahead,
            "behind": behind,
            "clean": not entries,
            "entries": entries,
            "truncated": len(entries) >= max_entries and len(lines) > max_entries + 1,
        }

    @staticmethod
    def _diff_fingerprint(value: dict[str, Any]) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _encode_diff_continuation(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        signature = hmac.new(PROCESS_DIFF_CONTINUATION_SECRET, raw, hashlib.sha256).digest()
        body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        proof = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        return f"{body}.{proof}"

    def _decode_diff_continuation(self, token: str) -> dict[str, Any]:
        if not token or len(token) > DIFF_CONTINUATION_TOKEN_MAX_CHARS or token.count(".") != 1:
            raise ToolFailure("INVALID_CONTINUATION", "Invalid diff continuation token.", category="validation")
        body, proof = token.split(".", 1)
        try:
            raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
            signature = base64.urlsafe_b64decode(proof + "=" * (-len(proof) % 4))
            canonical_body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
            canonical_proof = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
            if body != canonical_body or proof != canonical_proof:
                raise ValueError("non-canonical base64url encoding")
            expected = hmac.new(PROCESS_DIFF_CONTINUATION_SECRET, raw, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("signature mismatch")
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ToolFailure("INVALID_CONTINUATION", "Invalid diff continuation token.", category="validation") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != DIFF_CONTINUATION_SCHEMA_VERSION
            or payload.get("operation_kind") != DIFF_CONTINUATION_OPERATION
            or not isinstance(payload.get("options"), dict)
            or isinstance(payload.get("position"), bool)
        ):
            raise ToolFailure("INVALID_CONTINUATION", "Unsupported diff continuation token.", category="validation")
        try:
            position = int(payload.get("position", -1))
        except (TypeError, ValueError) as exc:
            raise ToolFailure("INVALID_CONTINUATION", "Invalid diff continuation position.", category="validation") from exc
        if position < 0:
            raise ToolFailure("INVALID_CONTINUATION", "Invalid diff continuation position.", category="validation")
        payload["position"] = position
        return payload

    def _mark_diff_continuation_read(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with PROCESS_DIFF_CONTINUATION_READS_LOCK:
            reread = token_hash in PROCESS_DIFF_CONTINUATION_READS
            if not reread:
                if len(PROCESS_DIFF_CONTINUATION_READS) >= DIFF_CONTINUATION_READ_TRACK_LIMIT:
                    PROCESS_DIFF_CONTINUATION_READS.pop()
                PROCESS_DIFF_CONTINUATION_READS.add(token_hash)
        return reread

    def _diff_identity(
        self,
        combined: bytes,
        *,
        path_filters: list[str],
        staged: bool,
        unstaged: bool,
        context: int,
        max_bytes: int,
    ) -> tuple[str, str, str, dict[str, Any]]:
        workspace_identity = self._orchestration_workspace_identity(".")
        raw_sha256 = hashlib.sha256(combined).hexdigest()
        scope_fingerprint = self._diff_fingerprint({"paths": path_filters})
        options = {
            "paths": path_filters,
            "staged": bool(staged),
            "unstaged": bool(unstaged),
            "context_lines": int(context),
            "max_bytes": max(1, int(max_bytes)),
            "max_lines": DEFAULT_MAX_LINES,
        }
        options_fingerprint = self._diff_fingerprint(options)
        source_fingerprint = self._diff_fingerprint({
            "base_head": workspace_identity.get("base_head"),
            "worktree_fp": workspace_identity.get("worktree_fp"),
            "diff_sha256": raw_sha256,
        })
        return source_fingerprint, scope_fingerprint, options_fingerprint, options

    def _diff_page(
        self,
        combined: bytes,
        *,
        source_fingerprint: str,
        scope_fingerprint: str,
        options_fingerprint: str,
        options: dict[str, Any],
        position: int = 0,
        continuation_read: bool = False,
        continuation_reread: bool = False,
    ) -> dict[str, Any]:
        rendered = combined.decode("utf-8", errors="replace")
        rendered_bytes = rendered.encode("utf-8")
        if position > len(rendered_bytes):
            raise ToolFailure("STALE_CONTINUATION", "Diff continuation position no longer matches the source.", category="runtime")
        remaining = rendered_bytes[position:].decode("utf-8")
        truncation = truncate_text_head(remaining, max_lines=int(options["max_lines"]), max_bytes=int(options["max_bytes"]))
        next_position = position + truncation.output_bytes
        truncated = next_position < len(rendered_bytes)
        if truncated and next_position <= position:
            raise ToolFailure("CONTINUATION_PAGE_EMPTY", "Diff page limit could not make forward progress.", category="runtime")
        continuation = None
        if truncated:
            continuation = self._encode_diff_continuation({
                "schema_version": DIFF_CONTINUATION_SCHEMA_VERSION,
                "operation_kind": DIFF_CONTINUATION_OPERATION,
                "source_fingerprint": source_fingerprint,
                "scope_fingerprint": scope_fingerprint,
                "options_fingerprint": options_fingerprint,
                "options": options,
                "position": next_position,
            })
        diff_text = truncation.content
        return {
            "diff": diff_text,
            "files": parse_diff_files(diff_text),
            **truncation_fields(truncation),
            "truncated": truncated,
            "continuation": continuation,
            "source_fingerprint": source_fingerprint,
            "scope_fingerprint": scope_fingerprint,
            "options_fingerprint": options_fingerprint,
            "page": {
                "schema_version": DIFF_CONTINUATION_SCHEMA_VERSION,
                "start_byte": position,
                "next_byte": next_position,
                "total_bytes": len(rendered_bytes),
                "max_bytes": int(options["max_bytes"]),
                "max_lines": int(options["max_lines"]),
            },
            "result_tail": {
                "source_total_bytes": len(rendered_bytes),
                "page_output_bytes": truncation.output_bytes,
                "remaining_bytes": max(0, len(rendered_bytes) - next_position),
                "truncated": truncated,
                "continuation_offered": bool(continuation),
                "continuation_read": continuation_read,
                "continuation_reread": continuation_reread,
                "continuation_stale": False,
            },
            "warnings": ["diff truncated"] if truncated else [],
        }

    def git_diff(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        continuation_token = str(args.get("continuation", "") or "").strip()
        if continuation_token:
            payload = self._decode_diff_continuation(continuation_token)
            options = payload["options"]
            expected_paths = [str(item) for item in options.get("paths", [])]
            if "path" in args or "paths" in args:
                if self._git_path_filters(args) != expected_paths:
                    raise ToolFailure("CONTINUATION_SCOPE_MISMATCH", "Diff continuation scope cannot be changed between pages.", category="validation")
            for key in ("staged", "unstaged", "context_lines", "max_bytes"):
                if key in args:
                    requested = int(args[key]) if key in {"context_lines", "max_bytes"} else bool(args[key])
                    if requested != options.get(key):
                        raise ToolFailure("CONTINUATION_OPTIONS_MISMATCH", "Diff continuation options cannot be changed between pages.", category="validation")
            staged = bool(options.get("staged", False))
            unstaged = bool(options.get("unstaged", True))
            context = int(options.get("context_lines", 3))
            max_bytes = max(1, int(options.get("max_bytes", 262144)))
            path_filters = expected_paths
        else:
            staged = bool(args.get("staged", False))
            unstaged = bool(args.get("unstaged", True))
            context = int(args.get("context_lines", 3))
            max_bytes = max(1, int(args.get("max_bytes", 262144)))
            path_filters = self._git_path_filters(args)
        if not self._is_git_repo(self.workspace.root, env=git_env):
            if continuation_token:
                raise ToolFailure("INVALID_CONTINUATION", "Diff continuation requires a Git workspace.", category="runtime")
            return self._fallback_diff(path_filters, max_bytes)
        chunks: list[bytes] = []
        if unstaged:
            chunks.append(self._run_git_diff(git, context, path_filters, cached=False, env=git_env))
        if staged:
            chunks.append(self._run_git_diff(git, context, path_filters, cached=True, env=git_env))
        combined = b""
        for chunk in chunks:
            if combined and chunk and not combined.endswith(b"\n"):
                combined += b"\n"
            combined += chunk
        source_fingerprint, scope_fingerprint, options_fingerprint, normalized_options = self._diff_identity(
            combined,
            path_filters=path_filters,
            staged=staged,
            unstaged=unstaged,
            context=context,
            max_bytes=max_bytes,
        )
        if continuation_token:
            if (
                payload.get("source_fingerprint") != source_fingerprint
                or payload.get("scope_fingerprint") != scope_fingerprint
                or payload.get("options_fingerprint") != options_fingerprint
            ):
                raise ToolFailure(
                    "STALE_CONTINUATION",
                    "Diff source changed after the continuation was issued; restart from the first page.",
                    category="runtime",
                    details={"result_tail": {"continuation_stale": True}},
                )
            reread = self._mark_diff_continuation_read(continuation_token)
            position = int(payload["position"])
        else:
            reread = False
            position = 0
        return self._diff_page(
            combined,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            options_fingerprint=options_fingerprint,
            options=normalized_options,
            position=position,
            continuation_read=bool(continuation_token),
            continuation_reread=reread,
        )

    def _run_git_diff(
        self, git: str, context: int, path_filters: list[str], *, cached: bool, env: dict[str, str] | None = None
    ) -> bytes:
        cmd = [git, "-C", str(self.workspace.root), "diff", f"--unified={context}"]
        if cached:
            cmd.append("--cached")
        if path_filters:
            cmd.append("--")
            cmd.extend(path_filters)
        completed = self._run_git_bytes(cmd, timeout=10, env=env)
        if completed.returncode not in {0, 1}:
            raise ToolFailure("GIT_ERROR", completed.stderr.decode("utf-8", errors="replace"), category="runtime")
        return completed.stdout

    def _fallback_diff(self, path_filters: list[str], max_bytes: int) -> dict[str, Any]:
        selected = set(path_filters)
        chunks: list[str] = []
        files: list[dict[str, Any]] = []
        for rel, before in sorted(self.patch_baselines.items()):
            if selected and rel not in selected:
                continue
            current_path = self.workspace.resolve_for_write(rel).path
            after = read_text_preserve_newlines(current_path) if current_path.exists() and not current_path.is_dir() else None
            if before == after:
                continue
            before_lines = [] if before is None else before.splitlines(keepends=True)
            after_lines = [] if after is None else after.splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before_lines,
                    after_lines,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="",
                )
            )
            status = "added" if before is None else "deleted" if after is None else "modified"
            files.append({"path": rel, "status": status, "binary": False})
        diff = "\n".join(chunks)
        if diff and not diff.endswith("\n"):
            diff += "\n"
        diff_truncation = truncate_text_head(diff, max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        diff_text = diff_truncation.content
        truncated = diff_truncation.truncated
        return {
            "diff": diff_text,
            "files": files,
            **truncation_fields(diff_truncation),
            "warnings": ["non-git diff fallback"] + (["diff truncated"] if truncated else []),
        }

    def git_log(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        requested_path = str(args.get("path", "."))
        resolved = self.resolve_existing(requested_path)
        if not self._is_git_repo(resolved.path, env=git_env):
            return {"is_repo": False, "commits": [], "truncated": False, "warnings": []}
        ref = validate_git_ref(str(args.get("ref", "HEAD")))
        max_count = int(args.get("max_count", 20))
        skip = int(args.get("skip", 0))
        path_filter = resolved.display
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "log",
            f"--max-count={max_count + 1}",
            f"--skip={skip}",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s%x1e",
            ref,
        ]
        if path_filter != ".":
            cmd.extend(["--", path_filter])
        completed = self._run_git_text(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git log failed", category="runtime")
        commits: list[dict[str, Any]] = []
        for record in completed.stdout.split("\x1e"):
            fields = record.strip("\n").split("\x1f")
            if len(fields) < 6 or not fields[0]:
                continue
            commits.append(
                {
                    "hash": fields[0],
                    "short_hash": fields[1],
                    "author_name": fields[2],
                    "author_email": fields[3],
                    "author_date": fields[4],
                    "subject": fields[5],
                }
            )
        truncated = len(commits) > max_count
        result = {
            "is_repo": True,
            "ref": ref,
            "path": path_filter,
            "max_count": max_count,
            "skip": skip,
            "commits": commits[:max_count],
            "truncated": truncated,
            "warnings": ["commit limit reached"] if truncated else [],
        }
        if truncated:
            result["next_action"] = {
                "tool": "git_log",
                "arguments": {
                    "path": requested_path,
                    "ref": ref,
                    "max_count": max_count,
                    "skip": skip + max_count,
                },
            }
        return result

    def git_show(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        if not self._is_git_repo(self.workspace.root, env=git_env):
            return {"is_repo": False, "content": "", "files": [], "truncated": False, "warnings": []}
        rev = validate_git_ref(str(args.get("rev", "HEAD")))
        context = int(args.get("context_lines", 3))
        max_bytes = int(args.get("max_bytes", 262144))
        include_diff = bool(args.get("include_diff", True))
        normalized_filters = self._git_path_filters(args)
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "show",
            "--no-ext-diff",
            "--format=fuller",
            f"--unified={context}",
        ]
        if not include_diff:
            cmd.append("--no-patch")
        cmd.append(rev)
        if normalized_filters:
            cmd.append("--")
            cmd.extend(normalized_filters)
        completed = self._run_git_bytes(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.decode("utf-8", errors="replace").strip() or "git show failed", category="runtime")
        truncation = truncate_text_head(completed.stdout.decode("utf-8", errors="replace"), max_lines=DEFAULT_MAX_LINES, max_bytes=max_bytes)
        content = truncation.content
        return {
            "is_repo": True,
            "rev": rev,
            "content": content,
            "files": parse_diff_files(content),
            **truncation_fields(truncation),
            "warnings": ["output truncated"] if truncation.truncated else [],
        }

    def git_blame(self, args: dict[str, Any]) -> dict[str, Any]:
        git = require_git()
        git_env = self._git_env()
        requested_path = str(args.get("path", ""))
        resolved = self.resolve_existing(requested_path)
        if resolved.path.is_dir():
            raise ToolFailure("IS_DIRECTORY", "Path is a directory.", category="validation")
        if not self._is_git_repo(self.workspace.root, env=git_env):
            return {"is_repo": False, "path": resolved.display, "lines": [], "truncated": False, "warnings": []}
        ref_arg = args.get("rev")
        ref = validate_git_ref(str(ref_arg)) if isinstance(ref_arg, str) and ref_arg else None
        start_line = int(args.get("start_line", 1))
        end_line = args.get("end_line")
        max_lines = int(args.get("max_lines", 200))
        if end_line is None:
            requested_final_line = start_line + max_lines - 1
        else:
            requested_final_line = int(end_line)
        if requested_final_line < start_line:
            raise ToolFailure("INVALID_ARGUMENT", "end_line must be >= start_line.", category="validation")
        requested_lines = requested_final_line - start_line + 1
        truncated = requested_lines > max_lines
        final_line = min(requested_final_line, start_line + max_lines - 1)
        cmd = [
            git,
            "-C",
            str(self.workspace.root),
            "blame",
            "--line-porcelain",
            "-L",
            f"{start_line},{final_line}",
        ]
        if ref:
            cmd.append(ref)
        cmd.extend(["--", resolved.display])
        completed = self._run_git_text(cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            raise ToolFailure("GIT_ERROR", completed.stderr.strip() or "git blame failed", category="runtime")
        lines = parse_git_blame_porcelain(completed.stdout)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True
        result = {
            "is_repo": True,
            "path": resolved.display,
            "rev": ref,
            "start_line": start_line,
            "end_line": final_line,
            "max_lines": max_lines,
            "lines": lines,
            "truncated": truncated,
            "warnings": ["line limit reached"] if truncated else [],
        }
        if truncated and final_line < requested_final_line:
            next_arguments: dict[str, Any] = {
                "path": requested_path,
                "start_line": final_line + 1,
                "end_line": requested_final_line,
                "max_lines": max_lines,
            }
            if ref:
                next_arguments["rev"] = ref
            result["next_action"] = {
                "tool": "git_blame",
                "arguments": next_arguments,
            }
        return result

