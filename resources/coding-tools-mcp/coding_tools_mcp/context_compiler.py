from __future__ import annotations

import hashlib
import json
import os
from pathlib import PurePosixPath
from typing import Any


CONTEXT_COMPILER_SCHEMA_VERSION = 1
CONTEXT_COMPILER_ENV = "CODING_TOOLS_MCP_CONTEXT_COMPILER"
MAX_COMPILER_TOKEN_BUDGET = 131_072
MAX_OMITTED_CANDIDATES = 100
MAX_SEMANTIC_RECORDS = 200


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="surrogatepass")
    return hashlib.sha256(encoded).hexdigest()


def _safe_path(value: Any) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    if not raw or "\x00" in raw or raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        return ""
    parts = PurePosixPath(raw).parts
    if any(part in {"", ".", ".."} for part in parts):
        return ""
    return "/".join(parts)


def _token_cost(text: Any) -> int:
    size = len(str(text or "").encode("utf-8", errors="surrogatepass"))
    return 0 if size == 0 else max(1, (size + 3) // 4)


def _bounded_budget(value: Any) -> int:
    if isinstance(value, bool):
        return 1
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 1
    return min(max(parsed, 1), MAX_COMPILER_TOKEN_BUDGET)


def _scope_paths(requested_scope: Any) -> list[str]:
    raw = requested_scope.get("paths", []) if isinstance(requested_scope, dict) else requested_scope
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for value in raw:
        path = _safe_path(value)
        if path and path not in result:
            result.append(path)
    return result[:100]


def _in_scope(path: str, scope: list[str]) -> bool:
    if not scope:
        return True
    return any(path == item or path.startswith(item.rstrip("/") + "/") for item in scope)


def _is_test_path(path: str) -> bool:
    lowered = f"/{path.lower()}"
    name = PurePosixPath(path).name.lower()
    return (
        "/test/" in lowered
        or "/tests/" in lowered
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or "_test." in name
    )


def _is_config_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return name in {
        "agents.md",
        "package.json",
        "pyproject.toml",
        "cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "settings.gradle",
        "tsconfig.json",
        "vite.config.js",
        "vite.config.ts",
    } or name.endswith((".config.js", ".config.ts", ".config.json", ".yaml", ".yml"))


def context_compiler_treatment(env: dict[str, str] | None = None) -> dict[str, Any]:
    source = os.environ if env is None else env
    requested = str(source.get(CONTEXT_COMPILER_ENV, "off") or "off").strip().lower()
    if requested in {"", "off"}:
        return {"requested": requested or "off", "mode": "off", "auto_inject": False, "reason": None}
    if requested == "shadow":
        return {"requested": requested, "mode": "shadow", "auto_inject": False, "reason": None}
    return {
        "requested": requested[:80],
        "mode": "off",
        "auto_inject": False,
        "reason": "CONTEXT_COMPILER_MODE_UNSUPPORTED",
    }


def compile_context(
    task_intent: str,
    repo_revision: str,
    token_budget: int,
    current_evidence: dict[str, Any],
    already_seen: list[str] | None,
    requested_scope: Any,
) -> dict[str, Any]:
    """Compile only supplied evidence; this function never reads the repository itself."""
    budget = _bounded_budget(token_budget)
    seen = {str(item).strip() for item in (already_seen or []) if str(item).strip()}
    scope = _scope_paths(requested_scope)
    evidence = current_evidence if isinstance(current_evidence, dict) else {}
    files = evidence.get("files") if isinstance(evidence.get("files"), list) else []
    searches = evidence.get("searches") if isinstance(evidence.get("searches"), list) else []
    semantic_records = evidence.get("semantic_records") if isinstance(evidence.get("semantic_records"), list) else []
    instructions = evidence.get("instructions") if isinstance(evidence.get("instructions"), dict) else {}
    dirty_diff = evidence.get("dirty_diff") if isinstance(evidence.get("dirty_diff"), list) else []
    graph_status = evidence.get("semantic_graph") if isinstance(evidence.get("semantic_graph"), dict) else {}

    warnings: list[str] = []
    omitted: list[dict[str, str]] = []
    omitted_total = 0

    def omit(kind: str, identifier: str, reason: str) -> None:
        nonlocal omitted_total
        omitted_total += 1
        if len(omitted) < MAX_OMITTED_CANDIDATES:
            omitted.append({"kind": kind, "id": identifier[:512], "reason": reason})

    if not str(repo_revision or "").strip():
        warnings.append("repo_revision_unavailable")
    if graph_status.get("provider_available") is False:
        warnings.append("semantic_provider_unavailable")
    if str(graph_status.get("completeness") or "").lower() == "partial":
        warnings.append("semantic_graph_partial")

    path_hits: dict[str, int] = {}
    for search in searches[:24]:
        if not isinstance(search, dict):
            continue
        for match in search.get("matches", []) if isinstance(search.get("matches"), list) else []:
            if not isinstance(match, dict):
                continue
            path = _safe_path(match.get("path"))
            if path:
                path_hits[path] = path_hits.get(path, 0) + 1

    unique_files: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(files[:100]):
        if not isinstance(item, dict):
            continue
        path = _safe_path(item.get("path"))
        if not path or path in unique_files:
            if path:
                omit("file", path, "duplicate")
            continue
        content = str(item.get("content") or "")
        content_sha = hashlib.sha256(content.encode("utf-8", errors="surrogatepass")).hexdigest()
        file_fp = _canonical_sha256({"path": path, "content_sha256": content_sha, "truncated": bool(item.get("truncated"))})
        unique_files[path] = {
            "path": path,
            "content": content,
            "content_bytes": len(content.encode("utf-8", errors="surrogatepass")),
            "estimated_tokens": _token_cost(content),
            "truncated": bool(item.get("truncated")),
            "fingerprint": file_fp,
            "rank": index,
        }

    ordered_files = sorted(
        unique_files.values(),
        key=lambda item: (
            -int(any(item["path"] == requested or item["path"].startswith(requested.rstrip("/") + "/") for requested in scope)),
            -path_hits.get(item["path"], 0),
            item["rank"],
            item["path"],
        ),
    )

    primary_files: list[dict[str, Any]] = []
    remaining = budget
    selected_paths: set[str] = set()
    for item in ordered_files:
        path = item["path"]
        if not _in_scope(path, scope):
            omit("file", path, "out_of_scope")
            continue
        if path in seen or f"file:{path}" in seen or item["fingerprint"] in seen:
            omit("file", path, "already_seen")
            continue
        cost = int(item["estimated_tokens"])
        if cost > remaining:
            omit("file", path, "token_budget")
            continue
        primary_files.append({key: value for key, value in item.items() if key != "rank"})
        selected_paths.add(path)
        remaining -= cost
        if item["truncated"]:
            warnings.append(f"truncated_file:{path}")

    semantic_by_id: dict[str, dict[str, Any]] = {}
    for record in semantic_records[:MAX_SEMANTIC_RECORDS]:
        if not isinstance(record, dict):
            continue
        path = _safe_path(record.get("path"))
        symbol = str(record.get("symbol") or "").strip()[:500]
        if not path or not symbol:
            continue
        record_id = str(record.get("symbol_id") or _canonical_sha256({"path": path, "symbol": symbol, "kind": record.get("kind"), "line": record.get("line")}))
        if record_id in semantic_by_id:
            omit("symbol", record_id, "duplicate")
            continue
        if record.get("stale") is True or record.get("current") is False:
            omit("symbol", record_id, "stale")
            continue
        if not _in_scope(path, scope) or (selected_paths and path not in selected_paths):
            omit("symbol", record_id, "file_not_selected")
            continue
        if record_id in seen or f"symbol:{record_id}" in seen:
            omit("symbol", record_id, "already_seen")
            continue
        semantic_by_id[record_id] = {
            "symbol_id": record_id,
            "path": path,
            "symbol": symbol,
            "kind": str(record.get("kind") or "match")[:120],
            "line": record.get("line") if isinstance(record.get("line"), int) and not isinstance(record.get("line"), bool) else None,
            "provider": str(record.get("provider") or "")[:120] or None,
            "provider_version": str(record.get("provider_version") or "")[:120] or None,
            "confidence": str(record.get("confidence") or "unknown")[:40],
            "completeness": str(record.get("completeness") or "partial")[:40],
            "test_association": bool(record.get("test_association")) or _is_test_path(path),
        }

    primary_symbols = sorted(semantic_by_id.values(), key=lambda item: (item["path"], item["line"] or 0, item["symbol_id"]))
    entry_points = [item for item in primary_symbols if item["kind"] in {"definition", "import"}]
    relations = [item for item in primary_symbols if item["kind"] in {"reference", "import"}]
    relevant_tests = [item for item in primary_symbols if item["test_association"]]
    relevant_config = [
        {key: value for key, value in item.items() if key != "content"}
        for item in primary_files
        if _is_config_path(item["path"])
    ]

    rules: list[dict[str, Any]] = []
    for item in instructions.get("root", []) if isinstance(instructions.get("root"), list) else []:
        if not isinstance(item, dict):
            continue
        path = _safe_path(item.get("path"))
        content = str(item.get("content") or "")
        if not path or not content:
            continue
        fp = _canonical_sha256({"path": path, "content": content, "truncated": bool(item.get("truncated"))})
        if path in seen or f"rule:{path}" in seen or fp in seen:
            omit("rule", path, "already_seen")
            continue
        cost = _token_cost(content)
        if cost > remaining:
            omit("rule", path, "token_budget")
            continue
        rules.append({"path": path, "content": content, "estimated_tokens": cost, "truncated": bool(item.get("truncated")), "fingerprint": fp})
        remaining -= cost

    related_dirty_diff: list[dict[str, Any]] = []
    for item in dirty_diff[:100]:
        if not isinstance(item, dict):
            continue
        path = _safe_path(item.get("path"))
        diff = str(item.get("diff") or "")
        if not path or not diff or not _in_scope(path, scope):
            continue
        if selected_paths and path not in selected_paths:
            omit("diff", path, "file_not_selected")
            continue
        fp = _canonical_sha256({"path": path, "diff": diff})
        if path in seen or f"diff:{path}" in seen or fp in seen:
            omit("diff", path, "already_seen")
            continue
        cost = _token_cost(diff)
        if cost > remaining:
            omit("diff", path, "token_budget")
            continue
        related_dirty_diff.append({"path": path, "diff": diff, "estimated_tokens": cost, "fingerprint": fp})
        remaining -= cost

    if omitted_total > len(omitted):
        warnings.append("omitted_candidates_truncated")
    if any(item["completeness"] != "complete" for item in primary_symbols):
        warnings.append("semantic_evidence_partial")
    warnings = list(dict.fromkeys(warnings))[:100]

    normalized_input = {
        "task_intent": str(task_intent or "")[:4000],
        "repo_revision": str(repo_revision or "")[:256],
        "token_budget": budget,
        "scope": scope,
        "already_seen": sorted(seen),
        "current_evidence_sha256": _canonical_sha256(evidence),
        "file_fingerprints": sorted((item["path"], item["fingerprint"]) for item in unique_files.values()),
        "semantic_ids": sorted(semantic_by_id),
        "rule_fingerprints": sorted((item["path"], item["fingerprint"]) for item in rules),
        "diff_fingerprints": sorted((item["path"], item["fingerprint"]) for item in related_dirty_diff),
    }
    input_fingerprint = _canonical_sha256(normalized_input)
    compiled_core = {
        "schema_version": CONTEXT_COMPILER_SCHEMA_VERSION,
        "task_intent": str(task_intent or "")[:4000],
        "repo_revision": str(repo_revision or "")[:256],
        "token_budget": budget,
        "estimated_tokens": budget - remaining,
        "primary_files": primary_files,
        "primary_symbols": primary_symbols,
        "entry_points": entry_points,
        "relations": relations,
        "relevant_tests": relevant_tests,
        "relevant_config": relevant_config,
        "rules": rules,
        "related_dirty_diff": related_dirty_diff,
        "uncertainty": warnings,
        "omitted_candidates": omitted,
        "omitted_candidate_count": omitted_total,
        "completeness": "partial" if warnings or omitted_total else "complete",
    }
    return {
        **compiled_core,
        "fingerprints": {
            "input_sha256": input_fingerprint,
            "compiled_sha256": _canonical_sha256(compiled_core),
        },
    }
