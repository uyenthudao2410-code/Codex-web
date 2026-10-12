"""One admitted initial proof for the attested approved-patch workflow.

The object token never crosses JSON. It identifies the workflow-owned call to
the structured executor without borrowing continuation or exec-bridge authority.
"""
from __future__ import annotations

import hashlib
import json
from time import time as authority_clock
from dataclasses import dataclass, replace
from typing import Any

from .errors import ToolFailure
from .patching import parse_patch


APPROVED_PATCH_VERIFICATION_ORIGIN = object()
APPROVED_PATCH_CLIENT_ID = "electron-control-plane-approved-patch-bridge"


def require_approved_patch_actor(runtime: Any) -> None:
    identity = runtime._current_hub_client() or {}
    if (identity.get("client_id") != APPROVED_PATCH_CLIENT_ID
            or identity.get("client_type") != "electron"
            or identity.get("identity_source") != "attested_transport"
            or identity.get("attestation_verified") is not True):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_ACTOR_DENIED",
                          "Initial structured verification requires the attested approved-patch actor.", category="security")


@dataclass(frozen=True)
class InitialVerificationPlan:
    argv: tuple[str, ...]
    cwd: str
    timeout_ms: int
    max_output_bytes: int
    expires_at_ms: int = 0
    patch_sha256: str = ""

    def public(self) -> dict[str, Any]:
        return {"argv": list(self.argv), "cwd": self.cwd,
                "timeout_ms": self.timeout_ms, "max_output_bytes": self.max_output_bytes}

    @property
    def sha256(self) -> str:
        encoded = json.dumps(self.public(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_initial_verification(value: Any, *, expires_at_ms: int = 0) -> InitialVerificationPlan:
    def invalid() -> None:
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_INVALID", "Initial verification must be one bounded exact argv plan.", category="validation")
    if not isinstance(value, dict) or set(value) != {"argv", "cwd", "timeout_ms", "max_output_bytes"}:
        invalid()
    argv, cwd = value["argv"], value["cwd"]
    if not isinstance(argv, list) or not 1 <= len(argv) <= 32:
        invalid()
    if any(not isinstance(item, str) or not item or item != item.strip()
           or any(ord(character) < 32 or ord(character) == 127 for character in item)
           or any(token in item for token in (";", "&&", "||", "`", "$(", "|", ">", "<")) for item in argv):
        invalid()
    if any(token in argv[0] for token in ("/", "\\", ":")):
        invalid()
    if (not isinstance(cwd, str) or "\\" in cwd or ":" in cwd
            or (cwd != "" and any(part in {"", ".", ".."} for part in cwd.split("/")))
            or any(ord(character) < 32 or ord(character) == 127 for character in cwd)):
        invalid()
    try:
        if (any(len(item.encode("utf-8")) > 2048 for item in argv)
                or len("\0".join(argv).encode("utf-8")) > 8192 or len(cwd.encode("utf-8")) > 512):
            invalid()
    except UnicodeEncodeError:
        invalid()
    if type(value["timeout_ms"]) is not int or not 5000 <= value["timeout_ms"] <= 300000:
        invalid()
    if type(value["max_output_bytes"]) is not int or not 1024 <= value["max_output_bytes"] <= 65536:
        invalid()
    return InitialVerificationPlan(tuple(argv), cwd, value["timeout_ms"], value["max_output_bytes"], expires_at_ms)


def admit_initial_verification(runtime: Any, args: dict[str, Any]) -> InitialVerificationPlan | None:
    if "initial_verification" not in args:
        if "initial_verification_expires_at_ms" in args:
            raise ToolFailure("APPROVED_PATCH_VERIFICATION_INVALID", "Verification expiry requires its exact initial plan.", category="validation")
        return None
    require_approved_patch_actor(runtime)
    expiry = args.get("initial_verification_expires_at_ms")
    if type(expiry) is not int or expiry <= 0:
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_INVALID", "Initial verification requires its admitted authority expiry.", category="validation")
    plan = normalize_initial_verification(args["initial_verification"], expires_at_ms=expiry)
    if (args.get("workflow") != "custom" or args.get("phase") != "execute"
            or args.get("execution_mode") != "mcp_only" or args.get("execution_route") != "deterministic"
            or args.get("verification") != "none" or args.get("dry_run", False) is not False
            or not isinstance(args.get("patch"), str) or not args["patch"].strip()
            or any(args.get(key) for key in ("patches", "commands", "checks", "test_command", "build_command",
                                           "adopt_existing_files", "files", "directories", "continuation", "committed_review"))):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_WORKFLOW_DENIED", "Initial verification requires one exact custom execute patch and no other execution steps.", category="security")
    operations = parse_patch(args["patch"])
    if (len(operations) != 1 or operations[0].kind != "write_exact" or operations[0].move_to
            or not operations[0].preimage_sha256 or operations[0].preimage_sha256 == "absent"
            or not operations[0].postimage_sha256):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_WORKFLOW_DENIED", "Initial verification requires exactly one existing-file update.", category="security")
    validate_initial_verification_execution(runtime, plan)
    return replace(plan, patch_sha256=hashlib.sha256(args["patch"].encode("utf-8")).hexdigest())


def validate_initial_verification_execution(runtime: Any, plan: InitialVerificationPlan) -> None:
    require_approved_patch_actor(runtime)
    if plan.expires_at_ms <= int(authority_clock() * 1000):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_EXPIRED", "Initial verification authority has expired; no command was started.", category="permission")
    workdir = runtime.resolve_existing(plan.cwd or ".")
    if not workdir.path.is_dir():
        raise ToolFailure("NOT_A_DIRECTORY", "Initial verification cwd must be a workspace directory.", category="validation")
    runtime._check_structured_argv_policy(list(plan.argv), {})


def require_initial_verification_origin(runtime: Any, args: dict[str, Any]) -> InitialVerificationPlan:
    plan = args.get("_approved_patch_verification_plan")
    if (args.get("_approved_patch_verification_origin") is not APPROVED_PATCH_VERIFICATION_ORIGIN
            or not isinstance(plan, InitialVerificationPlan) or args.get("_continuation_internal") is not None
            or args.get("_argv") != list(plan.argv) or "cmd" in args or "argv" in args
            or args.get("workdir") != (plan.cwd or ".")
            or type(args.get("timeout_ms")) is not int or not 1000 <= args["timeout_ms"] <= plan.timeout_ms
            or args.get("max_output_bytes") != plan.max_output_bytes
            or not args.get("run_id") or not args.get("wave_id")):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_ORIGIN_DENIED", "Structured initial verification must be owned by its admitted workflow.", category="security")
    validate_initial_verification_execution(runtime, plan)
    return plan


def require_initial_verification_patch_origin(runtime: Any, args: dict[str, Any]) -> None:
    plan = args.get("_approved_patch_verification_plan")
    if (args.get("_approved_patch_verification_origin") is not APPROVED_PATCH_VERIFICATION_ORIGIN
            or not isinstance(plan, InitialVerificationPlan) or args.get("dry_run", False) is not False
            or not isinstance(args.get("patch"), str) or not plan.patch_sha256
            or hashlib.sha256(args["patch"].encode("utf-8")).hexdigest() != plan.patch_sha256):
        raise ToolFailure("APPROVED_PATCH_VERIFICATION_ORIGIN_DENIED", "The exact patch must retain its private initial-proof admission.", category="security")
    validate_initial_verification_execution(runtime, plan)


def project_initial_verification_readiness(readiness: dict[str, Any], plan: InitialVerificationPlan) -> None:
    readiness["verification"]["steps"] = [{"kind": "initial_verification", "status": "AVAILABLE",
                                            "plan_sha256": plan.sha256, "reason_code": None}]
    missing = readiness["acceptance"]["missing"]
    if "passed_initial_verification_proof" not in missing:
        missing.insert(0, "passed_initial_verification_proof")


def initial_verification_summary(plan: InitialVerificationPlan, result: dict[str, Any],
                                 proof_ids: list[str], proof_fingerprint: str | None = None) -> dict[str, Any]:
    status = "passed" if result.get("status") == "passed" else ("timed_out" if result.get("timed_out") else "failed")
    summary: dict[str, Any] = {"plan_sha256": plan.sha256, "proof_status": status,
                              "proof_ids": list(proof_ids), "proof_fingerprint": proof_fingerprint if status == "passed" else None}
    if result.get("command_id") and result.get("job_id"):
        summary.update(command_id=result["command_id"], job_id=result["job_id"])
    return summary


def bounded_patch_effect(execution: dict[str, Any]) -> dict[str, Any] | None:
    files = execution.get("affected_files")
    patches = execution.get("patch_results")
    if (isinstance(files, list) and len(files) == 1 and isinstance(files[0], dict)
            and files[0].get("operation") == "update" and isinstance(files[0].get("path"), str)
            and isinstance(patches, list) and len(patches) == 1 and isinstance(patches[0], dict) and patches[0].get("dry_run") is False
            and patches[0].get("clean") is True):
        return {"applied": True, "affected_files": [{"path": files[0]["path"], "operation": "update"}]}
    return None
