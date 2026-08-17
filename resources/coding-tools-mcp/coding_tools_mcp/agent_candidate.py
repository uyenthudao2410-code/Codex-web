from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .codex_bridge import CodexBridgeError
from .envutils import ENV_PREFIX
from .errors import ToolFailure
from .orchestration_control import RunContext, normalize_failure_class
from .tool_contract import AGENT_EXECUTION_ROUTES


AGENT_EXTERNAL_REVIEW_ENV = f"{ENV_PREFIX}_EXTERNAL_REVIEW"
AGENT_REVIEW_PACKET_MAX_DIFF_CHARS = 12_000
AGENT_REVIEW_DEADLINE_MS = 8_000
AGENT_REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["accept", "fix", "blocked"]},
        "findings": {
            "type": "array",
            "maxItems": 5,
            "items": {"type": "string", "maxLength": 500},
        },
        "missing_proof": {
            "type": "array",
            "maxItems": 5,
            "items": {"type": "string", "maxLength": 500},
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["verdict", "findings", "missing_proof", "confidence"],
}

AGENT_CANDIDATE_PACKET_MAX_CHARS = 14_000
AGENT_CANDIDATE_SNIPPET_BUDGET_CHARS = 6_000
AGENT_CANDIDATE_SNIPPET_MAX_CHARS = 1_500
AGENT_CANDIDATE_SNIPPET_MAX_COUNT = 4
AGENT_CANDIDATE_SNIPPET_RADIUS_LINES = 12

AGENT_CANDIDATE_OUTPUT_SCHEMA = {

    "type": "object",

    "additionalProperties": False,

    "properties": {

        "status": {"type": "string", "enum": ["ready", "blocked"]},

        "summary": {"type": "string", "maxLength": 1_000},

        "replacements": {

            "type": "array",

            "maxItems": 8,

            "items": {

                "type": "object",

                "additionalProperties": False,

                "properties": {

                    "path": {"type": "string", "maxLength": 500},

                    "old": {"type": "string", "maxLength": 8_000},

                    "new": {"type": "string", "maxLength": 8_000},

                },

                "required": ["path", "old", "new"],

            },

        },

        "new_files": {

            "type": "array",

            "maxItems": 4,

            "items": {

                "type": "object",

                "additionalProperties": False,

                "properties": {

                    "path": {"type": "string", "maxLength": 500},

                    "content": {"type": "string", "maxLength": 12_000},

                },

                "required": ["path", "content"],

            },

        },

        "proof": {

            "type": "array",

            "maxItems": 4,

            "items": {"type": "string", "maxLength": 500},

        },

        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},

    },

    "required": ["status", "summary", "replacements", "new_files", "proof", "confidence"],

}


class AgentCandidateMixin:
    @staticmethod
    def _agent_review_proof(execution: dict[str, Any], verification: str) -> tuple[dict[str, Any], bool]:
        check_rows: list[dict[str, Any]] = []
        raw_checks = execution.get("check_results", [])
        for item in raw_checks if isinstance(raw_checks, list) else []:
            if not isinstance(item, dict):
                continue
            check_rows.append({
                "exit_code": item.get("exit_code"),
                "timed_out": bool(item.get("timed_out", False)),
                "summary": str(item.get("summary") or "")[:240],
            })
        report = execution.get("build_report") if isinstance(execution.get("build_report"), dict) else {}
        test_result = report.get("test_result") if isinstance(report.get("test_result"), dict) else {}
        build_result = report.get("build_result") if isinstance(report.get("build_result"), dict) else {}
        proof = {
            "verification": verification,
            "checks": check_rows,
            "build": {
                "overall_status": report.get("overall_status"),
                "test_status": test_result.get("status"),
                "build_status": build_result.get("status"),
                "artifact_count": len(report.get("artifacts", [])) if isinstance(report.get("artifacts"), list) else 0,
            },
        }
        strong_oracle = False
        if verification == "tests":
            strong_oracle = test_result.get("status") == "passed"
        elif verification == "build":
            strong_oracle = build_result.get("status") == "passed"
        elif verification == "all":
            strong_oracle = test_result.get("status") == "passed" and build_result.get("status") == "passed"
        return proof, strong_oracle

    @staticmethod

    def _normalize_candidate_path(value: object) -> str:

        path = str(value or "").strip().replace("\\", "/")

        while path.startswith("./"):

            path = path[2:]

        parts = path.split("/") if path else []

        if (

            not path

            or path.startswith("/")

            or re.match(r"^[A-Za-z]:", path)

            or any(part in {"", ".", ".."} for part in parts)

        ):

            raise ToolFailure("INVALID_CANDIDATE_PATH", f"Invalid candidate path: {value}", category="validation")

        return "/".join(parts)



    def _select_agent_execution_route(

        self,

        *,

        workflow: str,

        prepared: dict[str, Any] | None,

        requested: str,

        allow_high_cost: bool,
        strong_oracle: bool = False,

    ) -> dict[str, Any]:

        requested_name = str(requested or "auto").strip().lower() or "auto"

        supported = {"auto", "deterministic", *AGENT_EXECUTION_ROUTES}

        if requested_name not in supported:

            raise ToolFailure(

                "INVALID_EXECUTION_ROUTE",

                f"Unknown execution route: {requested_name}",

                category="validation",

                details={"supported": sorted(supported)},

            )

        if requested_name in {"sol_max", "sol_ultra"} and not allow_high_cost:

            raise ToolFailure(

                "HIGH_COST_ACK_REQUIRED",

                f"execution_route={requested_name} requires allow_high_cost=true.",

                category="validation",

                details={"route": requested_name},

            )

        if requested_name != "auto":

            selected = requested_name

            reason = "explicit_request"

        else:

            # Cost/time-to-accepted-result is the routing objective. Until the
            # paired representative evaluator has enough quality-preserving ROI
            # evidence, `auto` must not create a model bill merely because a task
            # matches a capability heuristic. Mini/Luna remain explicit paired
            # study routes; Sol/Terra remain explicit escalation/experiments.
            selected = "deterministic"

            reason = "roi_gate_hold_insufficient_paired_evidence"

        if selected == "deterministic":

            return {

                "requested": requested_name,

                "selected": selected,

                "reason": reason,

                "profile": None,

                "model": None,

                "effort": None,

                "high_cost": False,

            }

        spec = AGENT_EXECUTION_ROUTES[selected]

        return {

            "requested": requested_name,

            "selected": selected,

            "reason": reason,

            **spec,

        }



    def _agent_candidate_packet(

        self,

        *,

        workflow: str,

        objective: str,

        prepared: dict[str, Any],

        proof: dict[str, Any],

        selected_route: str,

    ) -> tuple[dict[str, Any], list[str]]:

        allowed_paths = []

        for raw_path in list(prepared.get("selected_paths") or [])[:20]:

            try:

                path = self._normalize_candidate_path(raw_path)

            except ToolFailure:

                continue

            if path not in allowed_paths:

                allowed_paths.append(path)

        files: list[dict[str, str]] = []

        remaining = AGENT_CANDIDATE_PACKET_MAX_CHARS

        snippets: list[dict[str, Any]] = []

        snippet_remaining = min(AGENT_CANDIDATE_SNIPPET_BUDGET_CHARS, remaining)

        seen_snippets: set[tuple[str, int]] = set()

        for result in list(prepared.get("searches") or [])[:6]:

            if len(snippets) >= AGENT_CANDIDATE_SNIPPET_MAX_COUNT:

                break

            if not isinstance(result, dict):

                continue

            query = str(result.get("query") or "")

            for match in list(result.get("matches") or [])[:3]:

                if not isinstance(match, dict) or snippet_remaining <= 0:

                    continue

                try:

                    path = self._normalize_candidate_path(match.get("path"))

                    line = int(match.get("line") or 0)

                except (ToolFailure, TypeError, ValueError):

                    continue

                if path not in allowed_paths or line < 1 or (path, line) in seen_snippets:

                    continue

                seen_snippets.add((path, line))

                start_line = max(1, line - AGENT_CANDIDATE_SNIPPET_RADIUS_LINES)

                max_lines = AGENT_CANDIDATE_SNIPPET_RADIUS_LINES * 2 + 1

                max_chars = min(AGENT_CANDIDATE_SNIPPET_MAX_CHARS, snippet_remaining)

                try:

                    local = self.read_file({

                        "path": path,

                        "start_line": start_line,

                        "max_lines": max_lines,

                        "max_bytes": max_chars,

                    })

                except (ToolFailure, OSError, UnicodeError):

                    continue

                content = str(local.get("content") or "")[:max_chars]

                if not content:

                    continue

                snippets.append({

                    "query": query,

                    "path": path,

                    "match_line": line,

                    "start_line": int(local.get("start_line") or start_line),

                    "end_line": int(local.get("end_line") or line),

                    "content": content,

                })

                consumed = len(content)

                snippet_remaining -= consumed

                remaining -= consumed

        for item in list(prepared.get("files") or []):

            if not isinstance(item, dict):

                continue

            try:

                path = self._normalize_candidate_path(item.get("path"))

            except ToolFailure:

                continue

            if path not in allowed_paths:

                continue

            content = str(item.get("content") or "")

            if not content or remaining <= 0:

                continue

            take = min(len(content), 5_000, remaining)

            files.append({"path": path, "content": content[:take]})

            remaining -= take

        searches: list[dict[str, Any]] = []

        for result in list(prepared.get("searches") or [])[:6]:

            if not isinstance(result, dict):

                continue

            matches = []

            for match in list(result.get("matches") or [])[:3]:

                if not isinstance(match, dict):

                    continue

                matches.append({

                    "path": match.get("path"),

                    "line": match.get("line"),

                    "preview": str(match.get("preview") or match.get("text") or "")[:360],

                })

            searches.append({"query": result.get("query"), "matches": matches})

        return ({

            "objective": objective,

            "workflow": workflow,

            "selected_route": selected_route,

            "allowed_paths": allowed_paths,

            "proof": proof,

            "searches": searches,

            "snippets": snippets,

            "files": files,

            "contract": (

                "Return exact replacements only within allowed_paths. old must be a non-empty exact contiguous substring. "

                "Do not modify tests or unrelated files unless they are explicitly in allowed_paths. If another path or unsettled "

                "semantic decision is required, return status=blocked."

            ),

        }, allowed_paths)



    def _candidate_payload_to_patches(

        self,

        payload: dict[str, Any],

        *,

        allowed_paths: list[str],

    ) -> tuple[list[str], list[dict[str, str]]]:

        allowed = set(allowed_paths)

        replacements = list(payload.get("replacements") or [])

        new_files = list(payload.get("new_files") or [])

        if not replacements and not new_files:

            raise ToolFailure("EMPTY_CANDIDATE", "Candidate returned no changes.", category="validation")

        patches: list[str] = []

        normalized_new_files: list[dict[str, str]] = []

        for item in replacements:

            if not isinstance(item, dict):

                raise ToolFailure("INVALID_CANDIDATE", "Replacement must be an object.", category="validation")

            path = self._normalize_candidate_path(item.get("path"))

            if path not in allowed:

                raise ToolFailure(

                    "CANDIDATE_SCOPE_VIOLATION",

                    f"Candidate tried to modify an unapproved path: {path}",

                    category="validation",

                    details={"allowed_paths": sorted(allowed)},

                )

            old = str(item.get("old") or "")

            new = str(item.get("new") or "")

            if not old:

                raise ToolFailure("INVALID_CANDIDATE", f"Replacement old text is empty for {path}.", category="validation")

            target = (self.workspace.root / Path(*path.split("/"))).resolve(strict=False)

            root = self.workspace.root.resolve(strict=False)

            if not target.is_relative_to(root) or not target.is_file():

                raise ToolFailure("CANDIDATE_TARGET_MISSING", f"Candidate target is not a workspace file: {path}", category="validation")

            try:

                current = target.read_text(encoding="utf-8")

            except (OSError, UnicodeError) as exc:

                raise ToolFailure("CANDIDATE_TARGET_UNREADABLE", str(exc), category="filesystem") from exc

            target_newline = "\r\n" if "\r\n" in current else "\n"
            normalized_old = old.replace("\r\n", "\n").replace("\r", "\n").replace("\n", target_newline)
            normalized_new = new.replace("\r\n", "\n").replace("\r", "\n").replace("\n", target_newline)
            count = current.count(normalized_old)
            if count == 1:
                old, new = normalized_old, normalized_new

            if count != 1:

                raise ToolFailure(

                    "CANDIDATE_NOT_UNIQUE",

                    f"Candidate old text must match exactly once in {path}; matched {count} times.",

                    category="validation",

                    details={"path": path, "matches": count},

                )

            sections = ["*** Begin Patch", f"*** Update File: {path}", "@@"]

            sections.extend(f"-{line}" for line in old.splitlines())

            sections.extend(f"+{line}" for line in new.splitlines())

            sections.append("*** End Patch")

            patches.append("\n".join(sections))

        for item in new_files:

            if not isinstance(item, dict):

                raise ToolFailure("INVALID_CANDIDATE", "new_files entries must be objects.", category="validation")

            path = self._normalize_candidate_path(item.get("path"))

            if path not in allowed:

                raise ToolFailure(

                    "CANDIDATE_SCOPE_VIOLATION",

                    f"Candidate tried to create an unapproved path: {path}",

                    category="validation",

                    details={"allowed_paths": sorted(allowed)},

                )

            target = (self.workspace.root / Path(*path.split("/"))).resolve(strict=False)

            root = self.workspace.root.resolve(strict=False)

            if not target.is_relative_to(root) or target.exists():

                raise ToolFailure("CANDIDATE_NEW_FILE_INVALID", f"Candidate new file is invalid or already exists: {path}", category="validation")

            normalized_new_files.append({"path": path, "content": str(item.get("content") or "")})

        new_file_patch = self._new_files_patch(normalized_new_files)

        if new_file_patch:

            patches.append(new_file_patch)

        return patches, normalized_new_files



    def _generate_agent_candidate(

        self,

        *,

        workflow: str,

        objective: str,

        prepared: dict[str, Any],

        requested_route: str,

        allow_high_cost: bool,

        proof: dict[str, Any],

        routing: dict[str, Any] | None = None,

        orchestration_ctx: RunContext | None = None,

    ) -> dict[str, Any]:

        preflight_test = proof.get("preflight_test") if isinstance(proof.get("preflight_test"), dict) else None
        preflight_build = proof.get("preflight_build") if isinstance(proof.get("preflight_build"), dict) else None
        strong_oracle = any(
            item is not None and item.get("exit_code") not in {None, 0}
            for item in (preflight_test, preflight_build)
        )
        if routing is None:
            routing = self._select_agent_execution_route(

                workflow=workflow,

                prepared=prepared,

                requested=requested_route,

                allow_high_cost=allow_high_cost,
                strong_oracle=strong_oracle,

            )
        else:
            routing = dict(routing)

        if routing["selected"] == "deterministic":

            return {"status": "deterministic", "routing": routing, "patches": []}

        packet, allowed_paths = self._agent_candidate_packet(

            workflow=workflow,

            objective=objective,

            prepared=prepared,

            proof=proof,

            selected_route=str(routing["selected"]),

        )

        if not allowed_paths:

            return {"status": "blocked", "reason": "candidate_scope_missing", "routing": routing, "patches": []}

        prompt = (

            "Bounded implementation candidate packet:\n"

            + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))

            + "\nReturn the structured candidate only. MCP will validate scope, apply the change, and run proof independently."

        )

        if orchestration_ctx is not None:
            self.orchestration_ledger.append_event(
                orchestration_ctx.run_id,
                wave_id=orchestration_ctx.wave_id,
                delegation_id=orchestration_ctx.delegation_id,
                event_type="model_dispatch_started",
                state_before=orchestration_ctx.state,
                state_after=orchestration_ctx.state,
                payload={
                    "route": routing.get("selected"),
                    "profile": routing.get("profile"),
                    "model": routing.get("model"),
                    "effort": routing.get("effort"),
                    "allowed_paths": allowed_paths,
                    "packet_bytes": len(prompt.encode("utf-8")),
                },
            )

        try:

            bridge_result = self._codex_bridge.run(

                prompt,

                profile=str(routing["profile"]),

                model=str(routing["model"]),

                effort=str(routing["effort"]),

                deadline_ms=int(AGENT_EXECUTION_ROUTES[str(routing["selected"])].get("deadline_ms", 0) or 0),

                output_schema=AGENT_CANDIDATE_OUTPUT_SCHEMA,

            )

        except CodexBridgeError as exc:

            if orchestration_ctx is not None:
                self.orchestration_ledger.append_event(
                    orchestration_ctx.run_id,
                    wave_id=orchestration_ctx.wave_id,
                    delegation_id=orchestration_ctx.delegation_id,
                    event_type="model_dispatch_finished",
                    state_before=orchestration_ctx.state,
                    state_after=orchestration_ctx.state,
                    payload={"status": "error", "failure_class": normalize_failure_class(exc.code), "retryable": exc.retryable},
                )

            return {

                "status": "blocked",

                "reason": exc.code,

                "retryable": exc.retryable,

                "routing": routing,

                "patches": [],

                "recommended_next_action": "Return to ChatWeb Sol or choose one different policy-approved route; do not retry unchanged.",

            }

        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}

        status = str(observation.get("status") or bridge_result.get("status") or "unknown")

        if orchestration_ctx is not None:
            self.orchestration_ledger.append_event(
                orchestration_ctx.run_id,
                wave_id=orchestration_ctx.wave_id,
                delegation_id=orchestration_ctx.delegation_id,
                event_type="model_dispatch_finished",
                state_before=orchestration_ctx.state,
                state_after=orchestration_ctx.state,
                payload={
                    "status": status,
                    "wall_time_ms": observation.get("wall_time_ms"),
                    "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
                    "economics": observation.get("economics"),
                },
            )

        base = {

            "routing": routing,

            "model_status": status,

            "wall_time_ms": observation.get("wall_time_ms"),

            "economics": observation.get("economics"),

            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),

            "patches": [],

        }

        if status != "completed":

            return {

                **base,

                "status": "blocked",

                "reason": "candidate_model_not_completed",

                "error": observation.get("error"),

                "recommended_next_action": "Return to ChatWeb Sol; do not serially cascade through every model tier.",

            }

        text = str(observation.get("agent_text") or "").strip()

        try:

            parsed = json.loads(text)

        except (TypeError, ValueError, json.JSONDecodeError):

            parsed = None

        if not isinstance(parsed, dict):

            return {**base, "status": "blocked", "reason": "candidate_output_invalid", "candidate_text": text[:2_000]}

        if str(parsed.get("status") or "blocked") != "ready":

            return {

                **base,

                "status": "blocked",

                "reason": "candidate_reported_blocked",

                "summary": str(parsed.get("summary") or "")[:1_000],

                "confidence": parsed.get("confidence"),

            }

        try:

            patches, new_files = self._candidate_payload_to_patches(parsed, allowed_paths=allowed_paths)

        except ToolFailure as exc:

            return {

                **base,

                "status": "blocked",

                "reason": exc.code,

                "summary": str(parsed.get("summary") or "")[:1_000],

                "validation_error": exc.message,

                "recommended_next_action": "Return candidate validation evidence to ChatWeb Sol; do not apply partial changes.",

            }

        return {

            **base,

            "status": "ready",

            "patches": patches,

            "new_files": new_files,

            "summary": str(parsed.get("summary") or "")[:1_000],

            "proof": list(parsed.get("proof") or [])[:4],

            "confidence": parsed.get("confidence"),

            "allowed_paths": allowed_paths,

        }

    def _maybe_agent_workflow_external_review(
        self,
        *,
        workflow: str,
        objective: str,
        verification: str,
        execution: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        raw_mode = str(os.environ.get(AGENT_EXTERNAL_REVIEW_ENV, "off")).strip().lower()
        if raw_mode in {"0", "false", "off", "none", "disabled"}:
            return {"plane": "none", "status": "skipped", "reason": "external_review_disabled"}
        force_packet = raw_mode in {"1", "true", "on", "packet", "always"}
        if dry_run:
            return {"plane": "none", "status": "skipped", "reason": "dry_run"}
        if not execution.get("ok"):
            return {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"}
        if workflow in {"diagnose", "document", "resume"}:
            return {"plane": "none", "status": "skipped", "reason": "workflow_has_no_review_value"}

        raw_affected = execution.get("affected_files", [])
        affected_paths = sorted({
            str(item.get("path", "")).strip()
            for item in raw_affected if isinstance(raw_affected, list)
            if isinstance(item, dict) and str(item.get("path", "")).strip()
        })[:32]
        if not affected_paths:
            return {"plane": "none", "status": "skipped", "reason": "no_code_change"}

        diff_result = execution.get("git_diff") if isinstance(execution.get("git_diff"), dict) else {}
        diff_text = str(diff_result.get("diff") or "")
        if not diff_text:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "packet_evidence_missing",
                "recommended_profile": "scoped",
                "affected_paths": affected_paths,
            }
        if bool(diff_result.get("truncated")) or len(diff_text) > AGENT_REVIEW_PACKET_MAX_DIFF_CHARS:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "packet_evidence_too_large",
                "recommended_profile": "scoped",
                "affected_paths": affected_paths,
                "diff_sha256": hashlib.sha256(diff_text.encode("utf-8")).hexdigest(),
            }

        proof, strong_oracle = self._agent_review_proof(execution, verification)
        localized = len(affected_paths) <= 2 and len(diff_text) <= 6_000
        if not force_packet and workflow in {"bugfix", "test_failure"} and strong_oracle and localized:
            return {
                "plane": "none",
                "status": "skipped",
                "reason": "localized_change_with_strong_oracle",
                "affected_paths": affected_paths,
            }

        diff_sha256 = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
        packet = {
            "objective": objective,
            "workflow": workflow,
            "accept": "Find no material defect in the supplied change evidence, or identify a concrete fix/proof gap.",
            "affected_paths": affected_paths,
            "diff_sha256": diff_sha256,
            "proof": proof,
            "diff": diff_text,
            "question": "Review only this packet for material correctness, regression, or missing proof. Do not inspect the repository.",
        }
        prompt = "Independent evidence-only review packet:\n" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
        try:
            bridge_result = self._codex_bridge.run(
                prompt,
                profile="packet",
                deadline_ms=AGENT_REVIEW_DEADLINE_MS,
                output_schema=AGENT_REVIEW_OUTPUT_SCHEMA,
            )
        except CodexBridgeError as exc:
            return {
                "plane": "external_mcp",
                "profile": "packet",
                "status": "unavailable",
                "reason": exc.code,
                "retryable": exc.retryable,
                "affected_paths": affected_paths,
                "diff_sha256": diff_sha256,
                "recommended_next_action": "Continue with Sol acceptance; do not repeat an unchanged external-review failure.",
            }

        observation = bridge_result.get("observation") if isinstance(bridge_result.get("observation"), dict) else {}
        status = str(observation.get("status") or bridge_result.get("status") or "unknown")
        review: dict[str, Any] = {
            "plane": "external_mcp",
            "profile": "packet",
            "status": status,
            "route": observation.get("route") or bridge_result.get("route"),
            "wall_time_ms": observation.get("wall_time_ms"),
            "economics": observation.get("economics"),
            "deadline_hit": bool(observation.get("deadline_hit", bridge_result.get("deadline_hit", False))),
            "affected_paths": affected_paths,
            "diff_sha256": diff_sha256,
        }
        if status != "completed":
            review["error"] = observation.get("error")
            review["recommended_next_action"] = "Continue with Sol acceptance or choose one different policy-approved route; do not retry unchanged."
            return review
        reviewer_text = str(observation.get("agent_text") or "").strip()
        try:
            parsed = json.loads(reviewer_text)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, dict):
            verdict = str(parsed.get("verdict") or "blocked")
            review.update({
                "verdict": verdict,
                "findings": list(parsed.get("findings", []))[:5],
                "missing_proof": list(parsed.get("missing_proof", []))[:5],
                "confidence": parsed.get("confidence"),
                "attention_required": verdict != "accept",
            })
        else:
            review.update({"verdict": "blocked", "reviewer_text": reviewer_text[:4_000], "attention_required": True})
        return review
