from __future__ import annotations

import hashlib
import json
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from pathlib import Path
from typing import Any

from . import __version__
from .build_verify import verify_build as run_build_verification
from .errors import ToolFailure
from .orchestration_control import OrchestrationControlError, RunContext
from .patching import parse_patch
from .performance_trace import IDEMPOTENCY_POLICY_EPOCH
from .semantic_localization import run_semantic_localization, semantic_provider_status
from .tool_contract import AGENT_EXECUTION_ROUTES, tool_metadata_contract
from .tool_schema import EVALUATION_SCHEMA_VERSION


_CONTEXT_BUNDLE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CONTEXT_BUNDLE_CACHE_LOCK = threading.Lock()
CONTEXT_BUNDLE_CACHE_TTL_SECONDS = 30


class ContextToolsMixin:
    def workspace_context(self, args: dict[str, Any]) -> dict[str, Any]:
        detail = str(args.get("detail", "compact")).lower()
        cache_args = {"path": str(args.get("path", ".")), "max_entries": int(args.get("max_entries", 40)), "detail": detail}
        cache_key = self._fast_cache_key("workspace_context", cache_args)
        cached = self._fast_cache_get(cache_key, 30)
        if cached is not None:
            return cached
        root_entries = self.list_dir({
            "path": str(args.get("path", ".")),
            "max_entries": min(int(args.get("max_entries", 40)), 500),
            "max_depth": 1,
            "recursive": False,
        })
        try:
            git = self.git_status({"path": str(args.get("path", ".")), "max_entries": 100})
        except Exception as exc:  # non-Git folders remain valid workspaces
            git = {"is_repo": False, "warnings": [str(exc)]}
        project = {"type": "unknown", "name": self.workspace.root.name, "version": ""}
        package = self.workspace.root / "package.json"
        if package.is_file():
            try:
                metadata = json.loads(package.read_text(encoding="utf-8"))
                project = {
                    "type": "electron" if metadata.get("main") else "node",
                    "name": str(metadata.get("name") or self.workspace.root.name),
                    "version": str(metadata.get("version") or ""),
                }
            except (OSError, ValueError):
                pass
        elif (self.workspace.root / "pyproject.toml").is_file():
            project["type"] = "python"
        elif (self.workspace.root / "Cargo.toml").is_file():
            project["type"] = "rust"
        elif (self.workspace.root / "go.mod").is_file():
            project["type"] = "go"
        task = self.task_state.get()
        if detail != "full":
            task = {key: task.get(key) for key in ("task_id", "objective", "status", "current_step", "next_step", "failure")}
            git = {
                "is_repo": git.get("is_repo", False),
                "branch": git.get("branch") or git.get("head"),
                "changed_count": len(git.get("entries", [])) if isinstance(git.get("entries"), list) else int(git.get("changed_count", 0) or 0),
                "truncated": bool(git.get("truncated", False)),
            }
        payload = {
            "workspace": str(self.workspace.root),
            "default_cwd": self.default_cwd_display(),
            "project": project,
            "entries": root_entries.get("entries", []),
            "entries_truncated": root_entries.get("truncated", False),
            "git": git,
            "task": task,
            "tool_mode": self.tool_mode,
            "detail": detail,
            "cache": {"hit": False, "age_ms": 0},
        }
        if detail == "full":
            source = self._orchestration_workspace_identity(args.get("path", "."))
            unresolved_stale_runs = self.orchestration_ledger.stale_run_candidates(
                stale_after_seconds=self.stale_run_seconds
            )
            payload["runtime"] = {
                "runtime_version": __version__,
                "server_instance_id": self.server_instance_id,
                "process_instance_id": self.process_instance_id,
                "performance_trace_version": self.performance_trace.schema_version,
                "idempotency_policy_epoch": IDEMPOTENCY_POLICY_EPOCH,
                "loaded_behavior": self._loaded_behavior_identity(),
                "source": {
                    "is_repo": bool(source.get("is_repo")),
                    "git_head": str(source.get("base_head") or ""),
                    "branch": str(source.get("branch") or ""),
                    "worktree_fp": str(source.get("worktree_fp") or ""),
                    "dirty": bool(source.get("dirty_paths")),
                },
                "tool_contract": dict(self.tool_contract),
                "tool_metadata": tool_metadata_contract(),
                "semantic_localization": semantic_provider_status(self.semantic_localizer),
                "stale_orchestration_runs": len(unresolved_stale_runs),
                "unresolved_stale_orchestration_runs": len(unresolved_stale_runs),
                "reconciled_stale_orchestration_runs": len(self.reconciled_stale_orchestration_runs),
                "stale_run_threshold_seconds": int(self.stale_run_seconds),
                "task_orchestration_projection_reconciled": bool(self.reconciled_task_orchestration),
                "orphaned_background_operations": int(self.orphaned_background_operations),
                "orphaned_idempotency_records": int(self.orphaned_idempotency_records),
                "agent_lanes_waiting_after_restart": int(self.recovered_agent_lanes),
            }
        self._fast_cache_put(cache_key, payload)
        return payload

    def _context_bundle_cache_key(self, args: dict[str, Any]) -> str:
        normalized = {key: value for key, value in args.items() if key != "force_refresh"}
        encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{self.workspace.root}\n{encoded}".encode("utf-8")).hexdigest()

    def _clear_context_bundle_cache(self) -> None:
        workspace_prefix = hashlib.sha256(f"{self.workspace.root}\n".encode("utf-8")).hexdigest()[:12]
        with _CONTEXT_BUNDLE_CACHE_LOCK:
            stale = [key for key in _CONTEXT_BUNDLE_CACHE if key.startswith(workspace_prefix)]
            for key in stale:
                _CONTEXT_BUNDLE_CACHE.pop(key, None)

    def prepare_coding_context(self, args: dict[str, Any]) -> dict[str, Any]:
        """Build the context a coding model normally gathers through many round trips."""
        composite_started = time.monotonic()
        cache_key = self._context_bundle_cache_key(args)
        namespaced_key = hashlib.sha256(f"{self.workspace.root}\n".encode("utf-8")).hexdigest()[:12] + cache_key
        now = time.time()
        if not bool(args.get("force_refresh", False)):
            with _CONTEXT_BUNDLE_CACHE_LOCK:
                cached = _CONTEXT_BUNDLE_CACHE.get(namespaced_key)
            if cached and now - cached[0] <= CONTEXT_BUNDLE_CACHE_TTL_SECONDS:
                payload = json.loads(json.dumps(cached[1], ensure_ascii=False))
                payload["cache_hit"] = True
                payload["cache_age_ms"] = int((now - cached[0]) * 1000)
                composite = payload.get("composite_read")
                if isinstance(composite, dict):
                    composite["cache"] = {
                        "hit": True,
                        "age_ms": payload["cache_age_ms"],
                        "source": "cached_previous_execution",
                    }
                return payload

        objective = str(args.get("objective", "")).strip()
        raw_queries = args.get("queries", [])
        raw_paths = args.get("paths", [])
        queries = list(dict.fromkeys(str(item).strip() for item in raw_queries if str(item).strip()))[:12]
        requested_paths = list(dict.fromkeys(str(item).strip() for item in raw_paths if str(item).strip()))[:40]
        max_files = min(max(int(args.get("max_files", 12)), 1), 30)
        max_total_bytes = min(max(int(args.get("max_total_bytes", 262144)), 4096), 1048576)
        max_matches = min(max(int(args.get("max_matches_per_query", 20)), 1), 100)

        search_workers = min(4, len(queries)) if queries else 0
        semantic_status = semantic_provider_status(self.semantic_localizer)
        semantic_enabled = bool(queries) and semantic_status.get("available") is True and not bool(args.get("regex", False))
        composite_plan = {
            "schema_version": 1,
            "mode": "model_free",
            "query_count": len(queries),
            "requested_path_count": len(requested_paths),
            "limits": {
                "max_files": max_files,
                "max_total_bytes": max_total_bytes,
                "max_matches_per_query": max_matches,
            },
            "stages": [
                {"id": "workspace", "kind": "workspace_context", "max_operations": 1, "parallel_safe": False},
                {
                    "id": "localize",
                    "kind": "semantic_then_text_fallback",
                    "max_operations": len(queries) * 2,
                    "parallel_safe": True,
                    "max_workers": search_workers,
                    "semantic_available": semantic_enabled,
                    "semantic_provider": semantic_status.get("provider"),
                },
                {"id": "materialize", "kind": "read_file", "max_operations": max_files, "parallel_safe": False, "byte_budget": max_total_bytes},
            ],
        }
        composite_plan_bytes = json.dumps(
            composite_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        composite_plan["plan_sha256"] = hashlib.sha256(composite_plan_bytes).hexdigest()
        composite_operations: list[dict[str, Any]] = []

        workspace_started = time.monotonic()
        workspace = self.workspace_context({"path": str(args.get("path", ".")), "max_entries": int(args.get("max_entries", 120))})
        workspace_ms = max(0, int((time.monotonic() - workspace_started) * 1000))
        composite_operations.append({
            "id": "workspace:0",
            "stage": "workspace",
            "kind": "workspace_context",
            "status": "completed",
            "duration_ms": workspace_ms,
        })
        instructions = {
            "root": [
                {"path": item.path, "content": item.content, "truncated": item.truncated}
                for item in self.project_context.root_files
            ],
            "nested_paths": list(self.project_context.nested_files),
            "warnings": list(self.project_context.warnings),
        }
        searches: list[dict[str, Any]] = []
        path_scores: dict[str, int] = {path: 1_000_000 - index for index, path in enumerate(requested_paths)}
        search_results_by_index: dict[int, dict[str, Any]] = {}
        fallback_pairs = list(enumerate(queries))
        semantic_attempted = 0
        semantic_handled = 0
        semantic_admission: dict[str, Any] | None = None

        if queries and bool(args.get("regex", False)):
            semantic_status = dict(semantic_status)
            semantic_status["reason"] = "REGEX_QUERY_REQUIRES_TEXT_SEARCH"
        elif semantic_enabled:
            semantic_path = str(args.get("path", "."))
            if len(requested_paths) == 1:
                candidate = requested_paths[0].replace("\\", "/")
                candidate_path = Path(candidate)
                if (
                    not candidate_path.is_absolute()
                    and ".." not in candidate_path.parts
                    and (self.workspace.root / candidate_path).is_file()
                ):
                    semantic_path = candidate
            semantic_mode = "single_file" if semantic_path != "." else "workspace"
            semantic_cost = "MEDIUM" if semantic_mode == "single_file" else "HEAVY"
            semantic_admission = self.execution_resource_governor.semantic_native_admission(
                mode=semantic_mode,
                cost=semantic_cost,
            )
            semantic_status = dict(semantic_status)
            semantic_status["admission"] = dict(semantic_admission)
            composite_operations.append({
                "id": "semantic-admission:0",
                "stage": "localize",
                "kind": "semantic_admission",
                "status": "completed" if semantic_admission["allowed"] else "fallback",
                "mode": semantic_admission["mode"],
                "cost": semantic_admission["cost"],
                "reason_code": semantic_admission["reason_code"],
            })
            if semantic_admission["allowed"]:
                semantic_batch = run_semantic_localization(
                    self.semantic_localizer,
                    workspace=self.workspace.root,
                    path=semantic_path,
                    queries=queries,
                    max_results=max_matches,
                )
                semantic_status = dict(semantic_batch.get("provider") or semantic_status)
                semantic_status["admission"] = dict(semantic_admission)
                fallback_pairs = []
                for item in semantic_batch.get("results", []):
                    if not isinstance(item, dict):
                        continue
                    index = int(item.get("query_index", -1))
                    if index < 0 or index >= len(queries):
                        continue
                    semantic_attempted += 1
                    matches = list(item.get("matches") or [])
                    handled = item.get("handled") is True
                    composite_operations.append({
                        "id": f"semantic:{index}",
                        "stage": "localize",
                        "kind": "semantic_navigation",
                        "status": "completed" if handled else "fallback",
                        "query_sha256": hashlib.sha256(queries[index].encode("utf-8")).hexdigest(),
                        "match_count": len(matches),
                        "provider": semantic_status.get("provider"),
                    })
                    if handled:
                        semantic_handled += 1
                        search_results_by_index[index] = {
                            "query": queries[index],
                            "engine": f"semantic:{semantic_status.get('provider') or 'provider'}",
                            "total_matches": len(matches),
                            "truncated": False,
                            "matches": matches,
                        }
                    else:
                        fallback_pairs.append((index, queries[index]))

        def search_once(index_and_query: tuple[int, str]) -> tuple[dict[str, Any], dict[str, Any]]:
            index, query = index_and_query
            started = time.monotonic()
            try:
                result = self.search_text({
                    "query": query,
                    "path": str(args.get("path", ".")),
                    "regex": bool(args.get("regex", False)),
                    "case_sensitive": bool(args.get("case_sensitive", False)),
                    "include_globs": args.get("include_globs", []),
                    "exclude_globs": args.get("exclude_globs", []),
                    "context_lines": 1,
                    "max_results": max_matches,
                    "max_preview_bytes": 360,
                })
                matches = result.get("matches", [])
                search_result = {
                    "query": query,
                    "engine": result.get("engine"),
                    "total_matches": result.get("total_matches", len(matches)),
                    "truncated": result.get("truncated", False),
                    "matches": matches,
                }
            except (ToolFailure, OSError, ValueError) as exc:
                search_result = {"query": query, "error": str(exc), "matches": []}
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            operation = {
                "id": f"search:{index}",
                "stage": "localize",
                "kind": "search_text",
                "status": "failed" if "error" in search_result else "completed",
                "duration_ms": duration_ms,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "match_count": len(search_result.get("matches", [])),
            }
            return search_result, operation

        localization_started = time.monotonic()
        fallback_search_workers = min(4, len(fallback_pairs)) if fallback_pairs else 0
        if fallback_pairs:
            with ThreadPoolExecutor(max_workers=fallback_search_workers, thread_name_prefix="context-search") as pool:
                search_pairs = list(pool.map(search_once, fallback_pairs))
            for (search_result, operation), (index, _query) in zip(search_pairs, fallback_pairs):
                search_results_by_index[index] = search_result
                composite_operations.append(operation)
        searches = [search_results_by_index[index] for index in range(len(queries)) if index in search_results_by_index]
        localization_ms = max(0, int((time.monotonic() - localization_started) * 1000))
        for result in searches:
            for match in result.get("matches", []):
                path = str(match.get("path", ""))
                if path:
                    path_scores[path] = path_scores.get(path, 0) + 1

        ranked_paths = sorted(path_scores, key=lambda item: (-path_scores[item], item))[:max_files]
        files: list[dict[str, Any]] = []
        total_bytes = 0
        materialization_started = time.monotonic()
        for read_index, path in enumerate(ranked_paths):
            remaining = max_total_bytes - total_bytes
            if remaining <= 0:
                break
            read_started = time.monotonic()
            try:
                item = self.read_file({"path": path, "max_bytes": min(remaining, 131072), "max_lines": 2000})
            except (ToolFailure, OSError, UnicodeError) as exc:
                files.append({"path": path, "error": str(exc)})
                composite_operations.append({
                    "id": f"read:{read_index}",
                    "stage": "materialize",
                    "kind": "read_file",
                    "path": path,
                    "status": "failed",
                    "duration_ms": max(0, int((time.monotonic() - read_started) * 1000)),
                    "content_bytes": 0,
                })
                continue
            content_bytes = len(str(item.get("content", "")).encode("utf-8"))
            total_bytes += content_bytes
            files.append(item)
            composite_operations.append({
                "id": f"read:{read_index}",
                "stage": "materialize",
                "kind": "read_file",
                "path": str(item.get("path") or path),
                "status": "completed",
                "duration_ms": max(0, int((time.monotonic() - read_started) * 1000)),
                "content_bytes": content_bytes,
                "truncated": bool(item.get("truncated", False)),
            })
        materialization_ms = max(0, int((time.monotonic() - materialization_started) * 1000))
        composite_total_ms = max(0, int((time.monotonic() - composite_started) * 1000))
        composite_read = {
            "schema_version": 1,
            "plan": composite_plan,
            "execution": {
                "status": "completed",
                "operation_count": len(composite_operations),
                "operations": composite_operations,
                "selected_path_count": len(ranked_paths),
                "materialized_file_count": sum(1 for item in files if "error" not in item),
                "content_bytes": total_bytes,
                "localization": {
                    "strategy": "semantic_first_text_fallback",
                    "provider": semantic_status,
                    "semantic_attempted": semantic_attempted,
                    "semantic_handled": semantic_handled,
                    "text_fallback_queries": len(fallback_pairs),
                    "native_admission": semantic_admission,
                },
                "parallelism": {
                    "search_parallel": bool(fallback_search_workers > 1),
                    "search_max_workers": fallback_search_workers,
                    "materialization_parallel": False,
                },
                "phase_timing": {
                    "source": "monotonic_local",
                    "workspace_ms": workspace_ms,
                    "localization_ms": localization_ms,
                    "materialization_ms": materialization_ms,
                    "total_ms": composite_total_ms,
                },
            },
            "cache": {"hit": False, "age_ms": 0, "source": "live_execution"},
        }

        current_task = self.task_state.get()
        task_resume = {
            "task_id": current_task.get("task_id"),
            "status": current_task.get("status"),
            "current_step": current_task.get("current_step"),
            "next_step": current_task.get("next_step"),
            "orchestration": dict(current_task.get("orchestration") or {}) if isinstance(current_task.get("orchestration"), dict) else {},
        }
        payload = {
            "objective": objective,
            "workspace": workspace,
            "instructions": instructions,
            "searches": searches,
            "files": files,
            "selected_paths": ranked_paths,
            "total_content_bytes": total_bytes,
            "composite_read": composite_read,
            "task_resume": task_resume,
            "cache_hit": False,
            "cache_ttl_seconds": CONTEXT_BUNDLE_CACHE_TTL_SECONDS,
            "recommended_next_action": "Use apply_changes_and_verify with all related patches and required checks in one call.",
        }
        with _CONTEXT_BUNDLE_CACHE_LOCK:
            if len(_CONTEXT_BUNDLE_CACHE) >= 64:
                oldest = min(_CONTEXT_BUNDLE_CACHE, key=lambda key: _CONTEXT_BUNDLE_CACHE[key][0])
                _CONTEXT_BUNDLE_CACHE.pop(oldest, None)
            _CONTEXT_BUNDLE_CACHE[namespaced_key] = (now, payload)
        return payload

    def _run_continuous_check(self, command: str, workdir: str, timeout_ms: int) -> dict[str, Any]:
        started = time.time()
        payload = self.exec_command({
            "cmd": command,
            "workdir": workdir,
            "timeout_ms": timeout_ms,
            "yield_time_ms": 30000,
            "max_output_bytes": 131072,
            "verbosity": "summary",
        })
        terminal_tool = "exec_command"
        terminal_args: dict[str, Any] = {"cmd": command}
        while payload.get("status") == "running":
            terminal_args = {
                "session_id": str(payload.get("session_id", "")),
                "chars": "",
                "yield_time_ms": 30000,
                "max_output_bytes": 131072,
                "verbosity": "summary",
            }
            payload = self.write_stdin(terminal_args)
            terminal_tool = "write_stdin"
        try:
            # These internal calls intentionally bypass _call_tool_sync, so
            # explicitly close the TaskState command lifecycle once with the
            # raw terminal payload before reducing it to a compact proof row.
            self.task_state.record_tool_result(terminal_tool, terminal_args, payload)
        except Exception:
            # Check truth must not depend on auxiliary task-state persistence.
            pass
        return {
            "command": command,
            "status": "passed" if payload.get("exit_code") == 0 else str(payload.get("status") or "failed"),
            "exit_code": payload.get("exit_code"),
            "duration_ms": int((time.time() - started) * 1000),
            "summary": str(payload.get("summary") or payload.get("stderr") or payload.get("stdout") or "")[:8000],
            "session_id": payload.get("session_id"),
        }

    def apply_changes_and_verify(self, args: dict[str, Any]) -> dict[str, Any]:
        """Apply one coherent change set, record proof identity, and avoid redundant proof reruns."""
        objective = str(args.get("objective", "")).strip() or "Apply and verify workspace changes"
        orchestration_ctx = args.get("_orchestration_context")
        ctx = orchestration_ctx if isinstance(orchestration_ctx, RunContext) else None
        raw_patches = args.get("patches", [])
        patches = [str(item) for item in raw_patches if str(item).strip()]
        single_patch = str(args.get("patch", "")).strip()
        if single_patch:
            patches.insert(0, single_patch)
        checks = list(dict.fromkeys(str(item).strip() for item in args.get("checks", []) if str(item).strip()))[:8]
        verification = str(args.get("verification", "tests")).lower()
        if verification not in {"none", "tests", "build", "all"}:
            raise ToolFailure("INVALID_ARGUMENT", "verification must be none, tests, build, or all.", category="validation")
        if not patches and not checks and verification == "none":
            raise ToolFailure("INVALID_ARGUMENT", "Provide a patch, check command, or verification step.", category="validation")

        workflow_steps: list[dict[str, str]] = []
        if patches:
            workflow_steps.append({"id": "apply", "text": "Apply workspace changes", "status": "pending"})
        if checks:
            workflow_steps.append({"id": "checks", "text": "Run requested checks", "status": "pending"})
        if verification != "none":
            workflow_steps.append({"id": "verify", "text": "Run tests and build verification", "status": "pending"})
        workflow_steps.append({"id": "finalize", "text": "Finalize verified result", "status": "pending"})

        def set_stage(stage_id: str, current_step: str, *, failed: bool = False) -> None:
            reached = False
            for step in workflow_steps:
                if step["id"] == stage_id:
                    step["status"] = "failed" if failed else "in_progress"
                    reached = True
                elif not reached and step["status"] != "failed":
                    step["status"] = "completed"
                elif reached and step["status"] not in {"completed", "failed"}:
                    step["status"] = "pending"
            self.task_state.update({"steps": workflow_steps, "current_step": current_step})

        def record_failure(code: object, **details: Any) -> None:
            if ctx is None or ctx.state in {"REPLAN", "BLOCKED", "ABORTED", "CHECKPOINTED"}:
                return
            self.orchestration_control.record_failure(ctx, code, payload=details)
            self._project_orchestration(ctx, event="orchestration_failure_projected")

        first_stage = workflow_steps[0]["id"]
        first_text = {
            "apply": "Applying complete change set",
            "checks": "Running requested checks",
            "verify": "Testing and building",
            "finalize": "Finalizing result",
        }[first_stage]
        workflow_steps[0]["status"] = "in_progress"

        self.task_state.update({
            "objective": objective,
            "status": "active",
            "steps": workflow_steps,
            "current_step": first_text,
            "next_step": "Run all requested checks and summarize the result.",
        }, event="continuous_workflow_started")

        workdir = str(args.get("workdir", args.get("path", ".")))
        if ctx is not None:
            identity_before = self._orchestration_workspace_identity(args.get("path", "."))
            try:
                self.orchestration_control.assert_write_allowed(
                    ctx,
                    owner="MCP",
                    base_head=str(identity_before.get("base_head") or ""),
                    worktree_fp=str(identity_before.get("worktree_fp") or ""),
                )
            except OrchestrationControlError as exc:
                record_failure(exc.code, details=exc.details)
                raise ToolFailure(exc.code, str(exc), category="runtime", retryable=True, details=exc.details) from exc

        patch_results: list[dict[str, Any]] = []
        affected_files: list[dict[str, str]] = []
        try:
            for patch_text in patches:
                result = self.apply_patch({"patch": patch_text, "dry_run": bool(args.get("dry_run", False))})
                patch_results.append(result)
                affected_files.extend(result.get("affected_files", []))
        except ToolFailure as exc:
            record_failure(exc.code, message=str(exc))
            raise
        if patches and not bool(args.get("dry_run", False)):
            self._clear_context_bundle_cache()

        if ctx is not None and ctx.state == "EXECUTING":
            self.orchestration_control.begin_proof(ctx)
            self._project_orchestration(ctx, event="orchestration_proving")

        proof_identity = self._orchestration_workspace_identity(args.get("path", ".")) if ctx is not None else {}
        affected_paths = sorted({
            str(item.get("path", "")).strip().replace("\\", "/")
            for item in affected_files
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        })
        proof_ids: list[str] = []
        proof_cache_eligible = 0
        proof_cache_hits = 0
        proof_cache_misses = 0
        proof_cache_miss_reasons: dict[str, int] = {}
        proof_cache_saved_ms = 0
        upstream_proof_ids: list[str] = []

        def observe_proof_cache(result: dict[str, Any]) -> None:
            nonlocal proof_cache_eligible, proof_cache_hits, proof_cache_misses, proof_cache_saved_ms
            if not result.get("proof_cache_eligible"):
                return
            proof_cache_eligible += 1
            if result.get("cache_hit"):
                proof_cache_hits += 1
                proof_cache_saved_ms += max(0, int(result.get("cache_saved_ms", 0) or 0))
                return
            proof_cache_misses += 1
            reason = str(result.get("proof_cache_miss_reason") or "unknown")[:80]
            proof_cache_miss_reasons[reason] = proof_cache_miss_reasons.get(reason, 0) + 1

        def current_proof_summary() -> dict[str, Any]:
            return {
                "proof_ids": list(proof_ids),
                "eligible": proof_cache_eligible,
                "cache_hits": proof_cache_hits,
                "cache_misses": proof_cache_misses,
                "cache_miss_reasons": dict(sorted(proof_cache_miss_reasons.items())),
                "cache_saved_ms": proof_cache_saved_ms,
            }

        command_results: list[dict[str, Any]] = []
        timeout_ms = min(max(int(args.get("timeout_ms", 600000)), 1000), 600000)
        if checks:
            set_stage("checks", "Running requested checks")
        for command in checks:
            if ctx is None:
                result = self._run_continuous_check(command, workdir, timeout_ms)
            else:
                command_hash = hashlib.sha256(command.encode("utf-8", errors="replace")).hexdigest()
                stage_id = f"check:{command_hash[:16]}"
                proof_fp = self.proof_ledger.fingerprint(
                    stage_id=stage_id,
                    base_head=str(proof_identity.get("base_head") or ctx.base_head),
                    worktree_fp=str(proof_identity.get("worktree_fp") or ""),
                    contract_fp=ctx.contract_fp,
                    input_paths=affected_paths,
                    config={"command_hash": command_hash, "workdir": workdir, "timeout_ms": timeout_ms},
                    upstream_proof_ids=upstream_proof_ids,
                )
                result, proof_id = self.proof_ledger.run_cached(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    stage_id=stage_id,
                    input_fingerprint=proof_fp,
                    command=command,
                    upstream_proof_ids=upstream_proof_ids,
                    metadata={"kind": "check", "workdir": workdir},
                    runner=lambda command=command: self._run_continuous_check(command, workdir, timeout_ms),
                )
                proof_ids.append(proof_id)
                upstream_proof_ids.append(proof_id)
                observe_proof_cache(result)
            command_results.append(result)
            if result.get("exit_code") != 0:
                failure = f"Check failed: {command}"
                set_stage("checks", "Requested check failed", failed=True)
                record_failure("CHECK_FAILED", command_hash=hashlib.sha256(command.encode("utf-8")).hexdigest())
                self.task_state.update({"status": "waiting", "failure": failure, "current_step": "Replan required", "next_step": "Replan from the failed check; do not retry unchanged."})
                return {
                    "ok": False,
                    "status": "failed",
                    "objective": objective,
                    "patch_results": patch_results,
                    "affected_files": affected_files,
                    "check_results": command_results,
                    "build_report": None,
                    "proof_summary": current_proof_summary(),
                    "error": {"code": "CHECK_FAILED", "message": failure, "category": "runtime", "retryable": True, "details": {}},
                }

        build_report = None
        if verification != "none":
            set_stage("verify", "Testing and building")
            verify_args = {
                "path": str(args.get("path", ".")),
                "workdir": workdir,
                "run_tests": verification in {"tests", "all"},
                "run_build": verification in {"build", "all"},
                "test_command": args.get("test_command", ""),
                "build_command": args.get("build_command", ""),
                "artifact_paths": args.get("artifact_paths", []),
                "hash_algorithm": args.get("hash_algorithm", "sha256"),
                "timeout_seconds": min(max(int(args.get("timeout_seconds", 600)), 1), 600),
            }
            if ctx is None:
                build_report = self.verify_build(verify_args)
            else:
                stage_id = f"verify:{verification}"
                proof_fp = self.proof_ledger.fingerprint(
                    stage_id=stage_id,
                    base_head=str(proof_identity.get("base_head") or ctx.base_head),
                    worktree_fp=str(proof_identity.get("worktree_fp") or ""),
                    contract_fp=ctx.contract_fp,
                    input_paths=affected_paths,
                    config=verify_args,
                    upstream_proof_ids=upstream_proof_ids,
                )
                build_report, proof_id = self.proof_ledger.run_cached(
                    run_id=ctx.run_id,
                    wave_id=ctx.wave_id,
                    stage_id=stage_id,
                    input_fingerprint=proof_fp,
                    command=f"verify_build:{verification}",
                    upstream_proof_ids=upstream_proof_ids,
                    metadata={"kind": "verify", "verification": verification},
                    runner=lambda: self.verify_build(verify_args),
                )
                proof_ids.append(proof_id)
                upstream_proof_ids.append(proof_id)
                observe_proof_cache(build_report)
            if build_report.get("ok") is False:
                set_stage("verify", "Verification failed", failed=True)
                error = build_report.get("error") if isinstance(build_report.get("error"), dict) else {}
                record_failure(error.get("code") or "VERIFICATION_FAILED", verification=verification)
                self.task_state.update({
                    "status": "waiting",
                    "failure": str(error.get("message") or "Verification failed"),
                    "current_step": "Replan required",
                    "next_step": "Replan from the failed proof stage; completed proof fingerprints remain auditable.",
                })
                return {
                    "ok": False,
                    "status": "failed",
                    "objective": objective,
                    "patch_results": patch_results,
                    "affected_files": affected_files,
                    "check_results": command_results,
                    "build_report": build_report,
                    "proof_summary": current_proof_summary(),
                    "error": build_report.get("error"),
                }

        diff = None
        if bool(args.get("include_diff", True)) and affected_files:
            try:
                diff_args: dict[str, Any] = {
                    "unstaged": True,
                    "max_bytes": int(args.get("max_diff_bytes", 131072)),
                }
                if affected_paths:
                    diff_args["paths"] = affected_paths
                else:
                    diff_args["path"] = str(args.get("path", "."))
                diff = self.git_diff(diff_args)
            except (ToolFailure, OSError, ValueError):
                diff = None
        set_stage("finalize", "Finalizing result")
        for step in workflow_steps:
            step["status"] = "completed"
        final_status = "waiting" if ctx is not None else "completed"
        final_step = "Waiting for final acceptance" if ctx is not None else "Completed"
        final_next = (
            "ChatWeb Sol must accept or reject this proven wave via task_control before another implementation wave."
            if ctx is not None
            else "Review the verified changes or continue with the next task."
        )
        proof_fingerprint = hashlib.sha256("|".join(proof_ids).encode("utf-8")).hexdigest() if proof_ids else ""
        self.task_state.update({
            "status": final_status,
            "steps": workflow_steps,
            "current_step": final_step,
            "next_step": final_next,
            "failure": None,
        }, event="continuous_workflow_completed")
        return {
            "ok": True,
            "status": "passed",
            "objective": objective,
            "patch_results": patch_results,
            "affected_files": affected_files,
            "check_results": command_results,
            "build_report": build_report,
            "git_diff": diff,
            "proof_summary": {
                **current_proof_summary(),
                "proof_fingerprint": proof_fingerprint,
                "worktree_fp": str(proof_identity.get("worktree_fp") or ""),
            },
            "next_step": final_next,
        }
