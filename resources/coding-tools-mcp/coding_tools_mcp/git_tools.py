from __future__ import annotations

import base64
import difflib
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
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
from .result_handoff import large_result_handoff, truncation_reason
from .textutils import DEFAULT_MAX_LINES, truncate_text_head
from .tool_schema import DIFF_CONTINUATION_TOKEN_MAX_CHARS


COMMITTED_REVIEW_SCHEMA_VERSION = 1
COMMITTED_REVIEW_OPERATION = "committed_review"
COMMITTED_REVIEW_MAX_FILES = 100
COMMITTED_REVIEW_MAX_BYTES = 262_144
COMMITTED_REVIEW_MAX_LINES = 2_000
MAX_EXACT_STATUS_ENTRIES = 2_000
_COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|secret|password)\b\s*[:=]"
)
_AUTHORIZATION_RE = re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|token)\b")
_PRIVATE_KEY_BEGIN_RE = re.compile(r"(?i)-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_PRIVATE_KEY_END_RE = re.compile(r"(?i)-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")


def _parse_git_status_porcelain_v1_z(raw: bytes) -> tuple[str, str, int, int, list[dict[str, Any]]]:
    """Parse one complete NUL-delimited porcelain-v1 status result."""
    try:
        decoded = bytes(raw).decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ToolFailure(
            "GIT_STATUS_MALFORMED",
            "Git status contained non-UTF-8 path bytes.",
            category="runtime",
        ) from exc
    if not decoded.endswith("\0"):
        raise ToolFailure(
            "GIT_STATUS_MALFORMED",
            "Git status did not use complete NUL-delimited records.",
            category="runtime",
        )
    records = decoded[:-1].split("\0")
    branch = ""
    upstream = ""
    ahead = 0
    behind = 0
    index = 0
    if records and records[0].startswith("## "):
        branch, upstream, ahead, behind = parse_branch_line(records[0][3:])
        index = 1
    entries: list[dict[str, Any]] = []
    while index < len(records):
        record = records[index]
        if not record or len(record) < 4 or record[2] != " " or record.startswith("## "):
            raise ToolFailure(
                "GIT_STATUS_MALFORMED",
                "Git status contained a malformed porcelain record.",
                category="runtime",
            )
        index_status = record[0]
        worktree_status = record[1]
        path_text = record[3:]
        if not path_text:
            raise ToolFailure("GIT_STATUS_MALFORMED", "Git status contained an empty path.", category="runtime")
        original = None
        if index_status in {"R", "C"} or worktree_status in {"R", "C"}:
            index += 1
            original = records[index] if index < len(records) else ""
            if not original:
                raise ToolFailure(
                    "GIT_STATUS_MALFORMED",
                    "Git rename/copy status omitted its original path.",
                    category="runtime",
                )
        entries.append({
            "path": path_text,
            "original_path": original,
            "index_status": index_status,
            "worktree_status": worktree_status,
        })
        index += 1
    if len(entries) > MAX_EXACT_STATUS_ENTRIES:
        raise ToolFailure(
            "WORKTREE_STATUS_TOO_LARGE",
            "Git status exceeded the bounded exact-source identity limit.",
            category="validation",
            details={"max_entries": MAX_EXACT_STATUS_ENTRIES, "observed_entries": len(entries)},
        )
    return branch, upstream, ahead, behind, entries


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
    @staticmethod
    def _committed_review_paths(value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list) or len(value) > 20:
            raise ToolFailure(
                "COMMITTED_REVIEW_PATHS_INVALID",
                "Committed review paths must be a list containing at most 20 repository-relative paths.",
                category="validation",
            )
        paths: set[str] = set()
        for item in value:
            path = str(item or "").strip().replace("\\", "/")
            if not path or path.startswith("/") or ":" in path or any(part in {"", ".", ".."} for part in path.split("/")):
                raise ToolFailure(
                    "COMMITTED_REVIEW_PATHS_INVALID",
                    "Committed review paths must be normalized repository-relative paths.",
                    category="validation",
                )
            paths.add(path)
        return sorted(paths)

    @staticmethod
    def _committed_review_integer(value: object, *, name: str, default: int, minimum: int, maximum: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool):
            raise ToolFailure("COMMITTED_REVIEW_OPTIONS_INVALID", f"{name} must be an integer.", category="validation")
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ToolFailure("COMMITTED_REVIEW_OPTIONS_INVALID", f"{name} must be an integer.", category="validation") from exc
        if not minimum <= parsed <= maximum:
            raise ToolFailure(
                "COMMITTED_REVIEW_OPTIONS_INVALID",
                f"{name} must be between {minimum} and {maximum}.",
                category="validation",
            )
        return parsed

    def _committed_review_options(self, args: dict[str, Any]) -> dict[str, Any]:
        base_commit = str(args.get("base_commit") or "").strip().lower()
        head_commit = str(args.get("head_commit") or "").strip().lower()
        if not _COMMIT_SHA_RE.fullmatch(base_commit) or not _COMMIT_SHA_RE.fullmatch(head_commit):
            raise ToolFailure(
                "COMMITTED_REVIEW_COMMIT_INVALID",
                "base_commit and head_commit must each be an exact lowercase-or-uppercase 40-character Git object id.",
                category="validation",
            )
        return {
            "base_commit": base_commit,
            "head_commit": head_commit,
            "paths": self._committed_review_paths(args.get("paths")),
            "max_bytes": self._committed_review_integer(
                args.get("max_bytes"), name="max_bytes", default=65_536, minimum=1_024, maximum=COMMITTED_REVIEW_MAX_BYTES
            ),
            "max_lines": self._committed_review_integer(
                args.get("max_lines"), name="max_lines", default=1_000, minimum=10, maximum=COMMITTED_REVIEW_MAX_LINES
            ),
        }

    @staticmethod
    def _redact_committed_review_text(value: str) -> tuple[str, int]:
        redactions = 0
        in_private_key = False
        redacted_lines: list[str] = []
        for line in value.splitlines(keepends=True):
            newline = "\n" if line.endswith("\n") else ""
            if in_private_key:
                redactions += 1
                redacted_lines.append("<redacted-private-key-material>" + newline)
                if _PRIVATE_KEY_END_RE.search(line):
                    in_private_key = False
                continue
            if _PRIVATE_KEY_BEGIN_RE.search(line):
                redactions += 1
                redacted_lines.append("<redacted-private-key-material>" + newline)
                in_private_key = not bool(_PRIVATE_KEY_END_RE.search(line))
                continue
            assignment = _SENSITIVE_ASSIGNMENT_RE.search(line)
            authorization = _AUTHORIZATION_RE.search(line)
            marker = assignment or authorization
            if marker is None:
                redacted_lines.append(line)
                continue
            redactions += 1
            redacted_lines.append(line[:marker.end()] + " <redacted>" + newline)
        return "".join(redacted_lines), redactions

    def _encode_committed_review_continuation(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        signature = hmac.new(PROCESS_DIFF_CONTINUATION_SECRET, raw, hashlib.sha256).digest()
        body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        proof = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        return f"{body}.{proof}"

    def _decode_committed_review_continuation(self, token: object) -> dict[str, Any]:
        text = str(token or "").strip()
        if not text or len(text) > DIFF_CONTINUATION_TOKEN_MAX_CHARS or text.count(".") != 1:
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Invalid committed review continuation.", category="validation")
        body, proof = text.split(".", 1)
        try:
            raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
            signature = base64.urlsafe_b64decode(proof + "=" * (-len(proof) % 4))
            if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != body or base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=") != proof:
                raise ValueError("non-canonical base64url encoding")
            expected = hmac.new(PROCESS_DIFF_CONTINUATION_SECRET, raw, hashlib.sha256).digest()
            payload = json.loads(raw.decode("utf-8"))
            if not hmac.compare_digest(signature, expected):
                raise ValueError("signature mismatch")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Invalid committed review continuation.", category="validation") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != COMMITTED_REVIEW_SCHEMA_VERSION
            or payload.get("operation_kind") != COMMITTED_REVIEW_OPERATION
            or not isinstance(payload.get("options"), dict)
            or not isinstance(payload.get("source_sha256"), str)
        ):
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Unsupported committed review continuation.", category="validation")
        try:
            payload["position"] = int(payload.get("position", -1))
        except (TypeError, ValueError) as exc:
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Invalid committed review continuation position.", category="validation") from exc
        if payload["position"] < 0:
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Invalid committed review continuation position.", category="validation")
        return payload

    @staticmethod
    def _committed_review_file_metadata(files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
        rendered: list[dict[str, Any]] = []
        subsystems: set[str] = set()
        risks: set[str] = set()
        for item in files[:COMMITTED_REVIEW_MAX_FILES]:
            path = str(item.get("path") or "")
            lowered = path.casefold()
            subsystem = "/".join(path.split("/")[:2]) or "root"
            file_risks: list[str] = []
            if any(marker in lowered for marker in ("auth", "oauth", "permission", "credential", "secret", "token")):
                file_risks.append("security_boundary")
            if any(marker in lowered for marker in ("workflow", "orchestration", "ledger", "runtime", "process")):
                file_risks.append("execution_lifecycle")
            if any(marker in lowered for marker in ("package", "cargo", "pyproject", "npm", "build", "ci", "workflow")):
                file_risks.append("build_or_delivery")
            if any(marker in lowered for marker in ("git", "patch", "source", "worktree", "base")):
                file_risks.append("source_identity")
            subsystems.add(subsystem)
            risks.update(file_risks)
            rendered.append({
                "path": path,
                "status": str(item.get("status") or "modified"),
                "binary": bool(item.get("binary")),
                "subsystem": subsystem,
                "risk_labels": file_risks,
            })
        return rendered, sorted(subsystems)[:16], sorted(risks)

    def committed_review(self, args: dict[str, Any]) -> dict[str, Any]:
        """Produce bounded, deterministic evidence for an immutable local commit range.

        This is intentionally an internal ``agent_workflow`` capability rather
        than another public MCP tool.  It never resolves refs lazily, fetches,
        or consults the mutable worktree diff.
        """
        if not self._is_git_repo(self.workspace.root, env=self._git_env()):
            raise ToolFailure("COMMITTED_REVIEW_NOT_GIT", "Committed review requires a Git workspace.", category="runtime")
        options = self._committed_review_options(args)
        continuation = args.get("continuation")
        continuation_payload = self._decode_committed_review_continuation(continuation) if continuation else None
        if continuation_payload is not None and continuation_payload.get("options") != options:
            raise ToolFailure(
                "COMMITTED_REVIEW_CONTINUATION_MISMATCH",
                "Committed review continuation cannot change commit, scope, or output bounds.",
                category="validation",
            )

        git = require_git()
        git_env = {**self._git_env(), "GIT_ATTR_NOSYSTEM": "1"}
        for commit in (options["base_commit"], options["head_commit"]):
            object_check = self._run_git_bytes(
                [git, "-C", str(self.workspace.root), "cat-file", "-e", f"{commit}^{{commit}}"], timeout=10, env=git_env
            )
            if object_check.returncode != 0:
                raise ToolFailure(
                    "COMMITTED_REVIEW_COMMIT_MISSING",
                    "Committed review requires both exact commit objects to be available locally; it never fetches missing history.",
                    category="runtime",
                    details={"commit": commit},
                )
        merge_base = self._run_git_bytes(
            [git, "-C", str(self.workspace.root), "merge-base", options["base_commit"], options["head_commit"]], timeout=10, env=git_env
        )
        if merge_base.returncode != 0 or not _COMMIT_SHA_RE.fullmatch(merge_base.stdout.decode("ascii", errors="ignore").strip()):
            raise ToolFailure(
                "COMMITTED_REVIEW_MERGE_BASE_MISSING",
                "Committed review requires a deterministic local merge base; it never infers a range from mutable branch state.",
                category="runtime",
            )
        effective_base = merge_base.stdout.decode("ascii").strip()
        diff_cmd = [
            git, "-C", str(self.workspace.root), "-c", f"core.attributesfile={os.devnull}", "diff",
            "--no-ext-diff", "--no-textconv", "--unified=3", effective_base, options["head_commit"],
        ]
        if options["paths"]:
            diff_cmd.extend(["--", *options["paths"]])
        diff_result = self._run_git_bytes(diff_cmd, timeout=20, env=git_env)
        if diff_result.returncode not in {0, 1}:
            raise ToolFailure("COMMITTED_REVIEW_GIT_ERROR", "Git could not render the committed review range.", category="runtime")
        source_text = diff_result.stdout.decode("utf-8", errors="replace")
        rendered_text, redaction_count = self._redact_committed_review_text(source_text)
        source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        if continuation_payload is not None and continuation_payload.get("source_sha256") != source_sha256:
            raise ToolFailure(
                "COMMITTED_REVIEW_SOURCE_DRIFT",
                "Committed review source did not match its signed continuation; restart from the first page.",
                category="runtime",
            )

        numstat_cmd = [
            git, "-C", str(self.workspace.root), "-c", f"core.attributesfile={os.devnull}", "diff",
            "--no-ext-diff", "--no-textconv", "--numstat", "-z", effective_base, options["head_commit"],
        ]
        if options["paths"]:
            numstat_cmd.extend(["--", *options["paths"]])
        numstat_result = self._run_git_bytes(numstat_cmd, timeout=10, env=git_env)
        if numstat_result.returncode not in {0, 1}:
            raise ToolFailure("COMMITTED_REVIEW_GIT_ERROR", "Git could not summarize the committed review range.", category="runtime")
        insertions = 0
        deletions = 0
        binary_numstat_files = 0
        for record in numstat_result.stdout.split(b"\0"):
            fields = record.split(b"\t", 2)
            if len(fields) < 2:
                continue
            if fields[0] == b"-" or fields[1] == b"-":
                binary_numstat_files += 1
                continue
            try:
                insertions += int(fields[0])
                deletions += int(fields[1])
            except ValueError:
                continue
        parsed_files = parse_diff_files(source_text)
        files, subsystems, risk_labels = self._committed_review_file_metadata(parsed_files)
        commit_result = self._run_git_bytes(
            [git, "-C", str(self.workspace.root), "rev-list", "--reverse", "--max-count=33", f"{effective_base}..{options['head_commit']}"],
            timeout=10,
            env=git_env,
        )
        if commit_result.returncode != 0:
            raise ToolFailure("COMMITTED_REVIEW_GIT_ERROR", "Git could not enumerate the committed review range.", category="runtime")
        commits = [line for line in commit_result.stdout.decode("ascii", errors="ignore").splitlines() if _COMMIT_SHA_RE.fullmatch(line)]
        commits_truncated = len(commits) > 32
        total_bytes = len(rendered_text.encode("utf-8"))
        position = int(continuation_payload.get("position", 0)) if continuation_payload is not None else 0
        if position > total_bytes:
            raise ToolFailure("INVALID_COMMITTED_REVIEW_CONTINUATION", "Committed review continuation is past the bounded source.", category="validation")
        remaining = rendered_text.encode("utf-8")[position:]
        page = truncate_text_head(remaining.decode("utf-8", errors="replace"), max_lines=options["max_lines"], max_bytes=options["max_bytes"])
        page_bytes = page.content.encode("utf-8")
        next_position = position + len(page_bytes)
        has_more = next_position < total_bytes
        token = ""
        if has_more:
            token = self._encode_committed_review_continuation({
                "schema_version": COMMITTED_REVIEW_SCHEMA_VERSION,
                "operation_kind": COMMITTED_REVIEW_OPERATION,
                "options": options,
                "source_sha256": source_sha256,
                "position": next_position,
            })
        binary_count = sum(1 for item in parsed_files if bool(item.get("binary")))
        warnings: list[str] = []
        if has_more:
            warnings.append("committed diff truncated")
        if commits_truncated:
            warnings.append("commit list truncated")
        if len(parsed_files) > COMMITTED_REVIEW_MAX_FILES:
            warnings.append("file list truncated")
        if redaction_count:
            warnings.append("sensitive values redacted from diff output")
        handoff = None
        if has_more:
            next_review = {**options, "continuation": token}
            handoff = large_result_handoff(
                kind="DIFF_PAGE",
                source_identity={"source_sha256": source_sha256},
                scope_identity={
                    "scope_fingerprint": self._diff_fingerprint(options),
                },
                reason=truncation_reason(page.truncated_by),
                next_operation={
                    "tool": "agent_workflow",
                    "arguments": {
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "committed_review": next_review,
                    },
                },
                continuation=token,
                has_more=True,
                continuation_recovers_all_omitted_data=True,
            )
        return {
            "schema_version": COMMITTED_REVIEW_SCHEMA_VERSION,
            "deterministic": True,
            "llm_summary": False,
            "range": {
                "base_commit": options["base_commit"],
                "head_commit": options["head_commit"],
                "effective_base_commit": effective_base,
                "paths": options["paths"],
            },
            "commits": commits[:32],
            "files": files,
            "summary": {
                "commit_count": len(commits),
                "commit_count_truncated": commits_truncated,
                "file_count": len(parsed_files),
                "binary_file_count": binary_count,
                "binary_numstat_file_count": binary_numstat_files,
                "insertions": insertions,
                "deletions": deletions,
                "hunk_count": source_text.count("\n@@"),
                "subsystems": subsystems,
                "risk_labels": risk_labels,
            },
            "integrity": {
                "source_diff_sha256": source_sha256,
                "presented_diff_sha256": hashlib.sha256(rendered_text.encode("utf-8")).hexdigest(),
                "redaction_count": redaction_count,
                "attributes": "system_and_global_attributes_disabled; external_diff_and_textconv_disabled",
            },
            "diff": page.content,
            "continuation": token or None,
            **({"large_result_handoff": handoff} if handoff is not None else {}),
            "result_tail": {
                "source_total_bytes": total_bytes,
                "page_output_bytes": len(page_bytes),
                "remaining_bytes": max(0, total_bytes - next_position),
                "truncated": has_more,
                "continuation_offered": bool(token),
                "continuation_read": bool(continuation_payload),
            },
            "warnings": warnings,
        }

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
        status_cmd = [git, "-C", str(resolved.path), "status", "--porcelain=v1", "-z", "-b"]
        status_cmd.append("--untracked-files=all" if include_untracked else "--untracked-files=no")
        completed = self._run_git_bytes(status_cmd, timeout=10, env=git_env)
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise ToolFailure("GIT_ERROR", message or "git status failed", category="runtime")
        branch, upstream, ahead, behind, all_entries = _parse_git_status_porcelain_v1_z(completed.stdout)
        entries = all_entries[:max_entries]
        return {
            "is_repo": True,
            "branch": branch,
            "head": self._git_rev_parse(resolved.path, "HEAD", env=git_env),
            "upstream": upstream,
            "ahead": ahead,
            "behind": behind,
            "clean": not all_entries,
            "entries": entries,
            "truncated": len(all_entries) > max_entries,
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
        handoff = None
        if truncated:
            handoff = large_result_handoff(
                kind="DIFF_PAGE",
                source_identity={"source_fingerprint": source_fingerprint},
                scope_identity={
                    "scope_fingerprint": scope_fingerprint,
                    "options_fingerprint": options_fingerprint,
                },
                reason=truncation_reason(truncation.truncated_by),
                next_operation={
                    "tool": "agent_workflow",
                    "arguments": {
                        "workflow": "resume",
                        "phase": "resume",
                        "continuation": continuation,
                    },
                },
                continuation=continuation,
                has_more=True,
                continuation_recovers_all_omitted_data=True,
            )
        return {
            "diff": diff_text,
            "files": parse_diff_files(diff_text),
            **truncation_fields(truncation),
            "truncated": truncated,
            "continuation": continuation,
            **({"large_result_handoff": handoff} if handoff is not None else {}),
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
        scope_root = self._current_request_workspace_root().resolve(strict=False)
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
        if not self._is_git_repo(scope_root, env=git_env):
            if continuation_token:
                raise ToolFailure("INVALID_CONTINUATION", "Diff continuation requires a Git workspace.", category="runtime")
            return self._fallback_diff(path_filters, max_bytes)
        chunks: list[bytes] = []
        if unstaged:
            chunks.append(self._run_git_diff(git, scope_root, context, path_filters, cached=False, env=git_env))
        if staged:
            chunks.append(self._run_git_diff(git, scope_root, context, path_filters, cached=True, env=git_env))
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
        self, git: str, root: Path, context: int, path_filters: list[str], *, cached: bool, env: dict[str, str] | None = None
    ) -> bytes:
        cmd = [git, "-C", str(root), "diff", f"--unified={context}"]
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
            current_path = self.resolve_for_write(rel).path
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

