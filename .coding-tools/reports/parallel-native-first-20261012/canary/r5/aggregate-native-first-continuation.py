"""Join the reviewed r4 canary and its additive native-exec continuations.

This is an offline evidence joiner.  It never calls the control plane, changes
policy, or treats a failed parent receipt as a pass.  The original file API
receipt and each continuation are linked by immutable SHA-256 references and
the same runtime identity.  A report from this tool means that all required
lanes have independently verified receipts; semantic acceptance remains a
separate gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path


MAX_BYTES = 8 * 1024 * 1024
SHA256 = re.compile(r"^[a-f0-9]{64}$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


def fail(code: str) -> None:
    raise RuntimeError(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        fail(code)


def load_receipt(path_value: str) -> tuple[Path, bytes, list[dict], dict]:
    path = Path(path_value)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(),
            "ABSOLUTE_RECEIPT_REQUIRED")
    raw = path.read_bytes()
    require(0 < len(raw) <= MAX_BYTES, "RECEIPT_SIZE_OUT_OF_BOUNDS")
    rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    require(rows and all(isinstance(row, dict) for row in rows), "NDJSON_OBJECT_ROWS_REQUIRED")
    finals = [row for row in rows if row.get("phase") == "final"]
    require(len(finals) == 1, "SINGLE_FINAL_RECEIPT_REQUIRED")
    source = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "record_count": len(rows),
    }
    return path, raw, rows, {"final": finals[0], "source": source}


def source_ref(value: dict, field: str, expected: dict) -> None:
    reference = value.get(field)
    require(isinstance(reference, dict), f"{field.upper()}_REFERENCE_REQUIRED")
    require(reference.get("sha256") == expected["sha256"], f"{field.upper()}_HASH_LINK_MISMATCH")
    require(reference.get("record_count") == expected["record_count"],
            f"{field.upper()}_RECORD_COUNT_LINK_MISMATCH")


def source_final(value: dict, field: str, expected: dict) -> None:
    require(value[field].get("final") == expected, f"{field.upper()}_EMBEDDED_FINAL_MISMATCH")


def scope(final: dict) -> dict:
    return {key: final.get(key) for key in
            ("workspace_id", "workspace_generation", "binding_id")}


def identity_from_proofs(final: dict) -> dict:
    proofs = final.get("proofs", {})
    require(isinstance(proofs, dict) and proofs and all(
        isinstance(proof, dict) and isinstance(proof.get("runtime_identity"), dict)
        for proof in proofs.values()), "RUNTIME_IDENTITY_MISSING_FROM_PROOF")
    identities = {
        tuple(sorted(proof["runtime_identity"].items()))
        for proof in proofs.values()
    }
    require(len(identities) == 1, "RUNTIME_IDENTITY_NOT_UNIQUE")
    return dict(next(iter(identities)))


def check_scope_and_identity(final: dict, expected_scope: dict, expected_identity: dict) -> None:
    require(scope(final) == expected_scope, "CONTINUATION_SCOPE_CHANGED")
    if final.get("proofs"):
        require(identity_from_proofs(final) == expected_identity, "CONTINUATION_RUNTIME_IDENTITY_CHANGED")
    for key in ("activation_epoch", "process_instance_id", "server_instance_id"):
        if key in final:
            mapped = {"activation_epoch": "activation_epoch_id"}.get(key, key)
            require(final[key] == expected_identity[mapped], "CONTINUATION_TOP_LEVEL_IDENTITY_CHANGED")
    if "local_tool_contract_sha256" in final:
        require(final["local_tool_contract_sha256"] == expected_identity["tool_contract_sha256"],
                "CONTINUATION_TOOL_CONTRACT_CHANGED")


def count_required_proofs(final: dict, lanes: list[str], code: str) -> dict:
    proofs = final.get("proofs")
    require(isinstance(proofs, dict), f"{code}_PROOFS_REQUIRED")
    require(all(lane in proofs and isinstance(proofs[lane], dict) for lane in lanes),
            f"{code}_PROOFS_INCOMPLETE")
    require(set(proofs) == set(lanes), f"{code}_UNEXPECTED_PROOF_LANES")
    actions = final.get("action_ids", {})
    for lane, proof in proofs.items():
        require(all(isinstance(proof.get(key), str) and IDENTIFIER.fullmatch(proof[key])
                    for key in ("receipt_id", "action_id", "attempt_id")),
                f"{code}_RECEIPT_IDENTITY_INCOMPLETE")
        require(actions.get(lane) == proof["action_id"], f"{code}_ORIGINAL_ACTION_HANDLE_MISMATCH")
        require(proof.get("attempt_number") == 1
                and SHA256.fullmatch(str(proof.get("response_sha256", ""))),
                f"{code}_VERIFIED_RECEIPT_METADATA_MISSING")
    return proofs


def check_native_jobs(proofs: dict, lanes: list[str], code: str) -> list[dict]:
    jobs = []
    for lane in lanes:
        proof = proofs[lane]
        for key in ("job_id", "command_id", "local_handle"):
            require(isinstance(proof.get(key), str) and proof[key], f"{code}_{lane.upper()}_{key.upper()}_MISSING")
        require(proof.get("execution_backend") == "native"
                and proof.get("isolation_level") == "process_container",
                f"{code}_{lane.upper()}_NOT_NATIVE")
        jobs.append({"lane": lane, **{key: proof[key] for key in
                                      ("job_id", "command_id", "local_handle")}})
    require(len({job["job_id"] for job in jobs}) == len(jobs), f"{code}_JOB_IDS_NOT_UNIQUE")
    require(len({job["command_id"] for job in jobs}) == len(jobs), f"{code}_COMMAND_IDS_NOT_UNIQUE")
    require(len({job["local_handle"] for job in jobs}) == len(jobs), f"{code}_LOCAL_HANDLES_NOT_UNIQUE")
    return jobs


def validate(args: argparse.Namespace) -> dict:
    loaded = [load_receipt(value) for value in
              (args.original, args.continuation, args.resume, args.readback)]
    original, continuation, resume, readback = [item[3] for item in loaded]
    original_final = original["final"]
    all_finals = [item["final"] for item in (original, continuation, resume, readback)]
    require(len({value.get("attempt_id") for value in all_finals}) == 4
            and len({value.get("task_id") for value in all_finals}) == 4,
            "CONTINUATION_ATTEMPT_OR_TASK_REUSED")
    timestamps = [value.get("observed_at_ms") for value in all_finals]
    require(all(type(stamp) is int for stamp in timestamps) and timestamps == sorted(timestamps)
            and len(set(timestamps)) == len(timestamps), "CONTINUATION_EVENT_ORDER_INVALID")
    require(original_final.get("operation") == "native_first_shared_mcp_canary",
            "ORIGINAL_OPERATION_MISMATCH")
    require(original_final.get("ok") is False
            and original_final.get("error_code") == "ORIGINAL_JOB_IDENTITY_NOT_VERIFIED",
            "ORIGINAL_TERMINAL_STATE_UNEXPECTED")
    require(original_final.get("proof_counts") ==
            {"reads": 100, "patches": 20, "readbacks": 20, "node_jobs": 0, "git_jobs": 0},
            "ORIGINAL_FILE_API_COUNTS_UNEXPECTED")
    require(original_final.get("task_closed_verified") is True
            and original_final.get("writer_released_verified") is True
            and original_final.get("requires_reconciliation") is False
            and original_final.get("unresolved_original_actions") == [],
            "ORIGINAL_CLEANUP_OR_SETTLEMENT_UNPROVEN")
    expected_scope = scope(original_final)
    expected_identity = identity_from_proofs(original_final)
    original_proofs = count_required_proofs(
        original_final, [f"read_{index:03}" for index in range(1, 101)]
        + [f"patch_{index:03}" for index in range(1, 21)]
        + [f"readback_{index:03}" for index in range(1, 21)], "ORIGINAL")
    original_status = original_final.get("final_action_status")
    require(isinstance(original_status, dict) and set(original_proofs) <= set(original_status)
            and set(original_status) - set(original_proofs) <= {"node_01"},
            "ORIGINAL_TERMINAL_STATUS_LANES_INCOMPLETE")
    for lane, status in original_status.items():
        if lane.startswith("node_"):
            valid = (status.get("state") == "completed"
                     and status.get("process_state") == "completed")
        else:
            valid = (status.get("state") == "completed"
                     and status.get("process_state") is None)
        require(valid and status.get("reconciliation_required") is False
                and (lane not in original_proofs
                     or status.get("action_id") == original_proofs[lane]["action_id"]),
                "ORIGINAL_TERMINAL_STATUS_NOT_EXACT")
    for index in range(1, 21):
        require(original_proofs[f"patch_{index:03}"].get("postimage_sha256")
                == original_proofs[f"readback_{index:03}"].get("content_sha256"),
                "ORIGINAL_PATCH_READBACK_HASH_MISMATCH")
    for index in range(1, 101):
        proof = original_proofs[f"read_{index:03}"]
        expected_path = f"tests/fixtures/native-first-canary/file-{index:03}.txt"
        expected = f"NATIVE_FIRST_CANARY_V1\nfile={index:03}\nstage=seed\n".encode()
        require(proof.get("path") == expected_path
                and proof.get("content_sha256") == hashlib.sha256(expected).hexdigest(),
                "ORIGINAL_FILE_READ_PATH_OR_HASH_MISMATCH")
        if index <= 20:
            readback_proof = original_proofs[f"readback_{index:03}"]
            patched = f"NATIVE_FIRST_CANARY_V1\nfile={index:03}\nstage=patched\n".encode()
            require(readback_proof.get("path") == expected_path
                    and readback_proof.get("content_sha256") == hashlib.sha256(patched).hexdigest(),
                    "ORIGINAL_PATCH_READBACK_PATH_OR_HASH_MISMATCH")

    continuation_final = continuation["final"]
    require(continuation_final.get("operation") == "native_exec_continuation"
            and continuation_final.get("ok") is False
            and continuation_final.get("error_code") == "EXEC_TERMINAL_PAYLOAD_INVALID",
            "CONTINUATION_TERMINAL_STATE_UNEXPECTED")
    source_ref(continuation_final, "source_partial", original["source"])
    source_final(continuation_final, "source_partial", original_final)
    check_scope_and_identity(continuation_final, expected_scope, expected_identity)
    require(continuation_final.get("proof_counts") ==
            {"node_jobs": 10, "git_jobs": 1, "approved_build": 0, "build_readback": 0},
            "CONTINUATION_COUNTS_UNEXPECTED")
    continuation_proofs = count_required_proofs(
        continuation_final, [f"node_{index:02}" for index in range(1, 11)] + ["git_status"],
        "CONTINUATION")
    jobs = check_native_jobs(continuation_proofs,
                             [f"node_{index:02}" for index in range(1, 11)] + ["git_status"],
                             "CONTINUATION")
    require(continuation_final.get("task_closed_verified") is True
            and continuation_final.get("writer_released_verified") is True,
            "CONTINUATION_CLEANUP_UNPROVEN")

    resume_final = resume["final"]
    require(resume_final.get("operation") == "native_exec_continuation_resume"
            and resume_final.get("ok") is False
            and resume_final.get("error_code") == "KeyError",
            "RESUME_TERMINAL_STATE_UNEXPECTED")
    source_ref(resume_final, "source_continuation", continuation["source"])
    source_final(resume_final, "source_continuation", continuation_final)
    check_scope_and_identity(resume_final, expected_scope, expected_identity)
    require(resume_final.get("proof_counts") ==
            {"git_jobs": 2, "approved_build": 1, "build_readback": 0},
            "RESUME_COUNTS_UNEXPECTED")
    resume_proofs = count_required_proofs(resume_final, ["git_diff", "git_log", "build"], "RESUME")
    jobs.extend(check_native_jobs(resume_proofs, ["git_diff", "git_log", "build"], "RESUME"))
    for key in ("job_id", "command_id", "local_handle"):
        require(len({job[key] for job in jobs}) == len(jobs), "CROSS_ATTEMPT_NATIVE_JOB_IDENTITY_REUSED")
    require(resume_final.get("task_closed_verified") is True
            and resume_final.get("writer_released_verified") is True,
            "RESUME_CLEANUP_UNPROVEN")

    readback_final = readback["final"]
    require(readback_final.get("operation") == "native_exec_readback_finalizer"
            and readback_final.get("ok") is True,
            "READBACK_FINALIZER_NOT_SUCCESSFUL")
    source_ref(readback_final, "source_resume", resume["source"])
    source_final(readback_final, "source_resume", resume_final)
    check_scope_and_identity(readback_final, expected_scope, expected_identity)
    require(readback_final.get("proof_counts") == {"build_readback": 1},
            "READBACK_COUNTS_UNEXPECTED")
    readback_proofs = count_required_proofs(readback_final, ["build_readback"], "READBACK")
    artifact = readback_proofs["build_readback"]
    require(artifact.get("path") == "tests/fixtures/native-first-canary/build-artifact.txt"
            and SHA256.fullmatch(str(artifact.get("content_sha256", ""))),
            "BUILD_READBACK_ARTIFACT_UNVERIFIED")
    require(artifact["content_sha256"] == resume_proofs["build"].get("stdout_sha256")
            and resume_proofs["build"].get("policy_decision") == "native_explicit_approval",
            "BUILD_MARKER_OR_EXPLICIT_APPROVAL_MISMATCH")
    for proofs in (continuation_proofs, resume_proofs):
        require(all(proof.get("policy_decision") == "native_safe_command"
                    for lane, proof in proofs.items() if lane != "build"),
                "SAFE_COMMAND_POLICY_PROOF_MISMATCH")
    require(readback_final.get("task_closed_verified") is True
            and readback_final.get("writer_released_verified") is True,
            "READBACK_CLEANUP_UNPROVEN")

    all_proofs = {**original_proofs, **continuation_proofs, **resume_proofs, **readback_proofs}
    require(len({proof["action_id"] for proof in all_proofs.values()}) == len(all_proofs)
            and len({proof["receipt_id"] for proof in all_proofs.values()}) == len(all_proofs)
            and len({proof["attempt_id"] for proof in all_proofs.values()}) == len(all_proofs),
            "CROSS_LANE_ACTION_RECEIPT_OR_ATTEMPT_REUSED")
    combined = {name: sum(lane.startswith(prefix) for lane in all_proofs)
                for name, prefix in (("reads", "read_"), ("patches", "patch_"),
                                     ("readbacks", "readback_"), ("node_jobs", "node_"),
                                     ("git_jobs", "git_"))}
    combined.update({"approved_build": int("build" in all_proofs),
                     "build_readback": int("build_readback" in all_proofs)})
    return {
        "schema_version": 1,
        "operation": "native_first_continuation_evidence_join",
        "observed_at_ms": int(time.time() * 1000),
        "status": "lanes_complete_semantic_gate_separate",
        "semantic_acceptance_performed": False,
        "replayed_original_actions": False,
        "scope": expected_scope,
        "runtime_identity": expected_identity,
        "combined_proof_counts": combined,
        "counts_derived_from_exact_unique_lanes": True,
        "distinct_proven_native_job_count": len({job["job_id"] for job in jobs}),
        "native_jobs": jobs,
        "source_receipts": [item["source"] for item in
                            (original, continuation, resume, readback)],
        "source_chain": {
            "continuation_source_partial_sha256": continuation_final["source_partial"]["sha256"],
            "resume_source_continuation_sha256": resume_final["source_continuation"]["sha256"],
            "readback_source_resume_sha256": readback_final["source_resume"]["sha256"],
        },
        "all_contributing_tasks_closed": True,
        "all_contributing_writers_released": True,
        "original_failed_harness_states_preserved": [
            {key: value.get(key) for key in ("operation", "attempt_id", "ok", "error_code")}
            for value in all_finals
        ],
        "separate_gates_not_evaluated": ["semantic_acceptance", "autocad_unknown_reconciliation", "real_dotnet_autocad_build"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "continuation", "resume", "readback"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(output.is_absolute() and not output.exists() and output.parent.is_dir(),
            "NEW_ABSOLUTE_OUTPUT_REQUIRED")
    report = validate(args)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"operation": report["operation"], "status": report["status"],
                      "output": str(output), "combined_proof_counts": report["combined_proof_counts"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"operation": "native_first_continuation_evidence_join_failed",
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        raise SystemExit(1)
