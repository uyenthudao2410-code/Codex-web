"""Read-only local correlation of the one r13 initial-proof canary.

No Runtime/ledger constructor, network request, execution, replay or acceptance.
Only the final allowlisted observation is written, using exclusive creation.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import zlib

ROOT = Path(r"E:\Github\Tools-Codex-web")
HERE = Path(__file__).resolve().parent
LEDGER = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
JOURNAL = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant\control-plane-node.json.approved-patch-bridge-journal.json")
HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
TARGET = "tests/fixtures/initial-proof-canary-target.cjs"
CHECKER = "tests/fixtures/initial-proof-canary-check.cjs"
PRE = "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650"
POST = "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e"
CHECKER_SHA = "059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230"
PLAN = {"argv": ["node", "--test", CHECKER], "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768}
PLAN_SHA = "235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7"
OLD_RUN = "95e909f0040a448faa9f1f3257e2ee2c"
OLD_WAVE = "c101beadfc6d4f2fbc13845052c84693"
OLD_HASHES = {"runs": "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590",
              "waves": "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce"}
NAMES = ["passed proof is ready for genuine controller acceptance",
         "failed proof retains the applied patch for replanning",
         "timed-out proof retains the applied patch for replanning",
         "an unapplied patch cannot be ready for acceptance"]


class Rejected(Exception):
    pass


def need(condition, code):
    if not condition:
        raise Rejected(code)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value, ascii=False):
    return json.dumps(value, ensure_ascii=ascii, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path):
    need(path.is_absolute(), "ABSOLUTE_INPUT_REQUIRED")
    raw = path.read_bytes()
    need(len(raw) <= 2 * 1024 * 1024, "INPUT_TOO_LARGE")
    return json.loads(raw), sha(raw)


def metadata(value):
    if isinstance(value, bytes):
        need(len(value) <= 1024 * 1024, "METADATA_TOO_LARGE")
        if value.startswith(b"WCPM1\0"):
            decoder = zlib.decompressobj()
            value = decoder.decompress(value[6:], 1024 * 1024 + 1)
            need(decoder.eof and len(value) <= 1024 * 1024, "COMPRESSED_METADATA_INVALID")
        value = value.decode("utf-8")
    result = json.loads(value)
    need(isinstance(result, dict), "METADATA_NOT_OBJECT")
    return result


def path_fingerprint(root, paths, extra=None):
    digest = hashlib.sha256()
    for raw in sorted(set(paths)):
        need(raw and not raw.startswith("/") and ".." not in raw.split("/"), "SOURCE_PATH_INVALID")
        digest.update(raw.encode("utf-8", errors="replace"))
        target = (root / Path(*raw.split("/"))).resolve(strict=False)
        need(target.is_relative_to(root.resolve()), "SOURCE_PATH_OUTSIDE_ROOT")
        if target.is_file():
            with target.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        elif target.exists():
            digest.update(b"<non-file>")
        else:
            digest.update(b"<missing>")
    if extra:
        digest.update(canonical(extra))
    return digest.hexdigest()


def source_identity(root):
    def git(*args):
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=15, shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        need(result.returncode == 0 and len(result.stdout) <= 2 * 1024 * 1024, "GIT_OBSERVATION_FAILED")
        return result.stdout.decode("utf-8", errors="strict")
    head, branch = git("rev-parse", "HEAD").strip(), git("branch", "--show-current").strip()
    need(head == HEAD and branch == "main", "SOURCE_HEAD_BRANCH_CHANGED")
    raw = git("status", "--porcelain=v1", "-z", "-b", "--untracked-files=all")
    need(raw.endswith("\0"), "GIT_STATUS_INCOMPLETE")
    records, entries, cursor = raw[:-1].split("\0"), [], 1
    need(records[0].startswith("## main"), "GIT_BRANCH_RECORD_INVALID")
    while cursor < len(records):
        record = records[cursor]
        need(len(record) >= 4 and record[2] == " ", "GIT_STATUS_RECORD_INVALID")
        path = record[3:].replace("\\", "/")
        if record[0] in "RC" or record[1] in "RC":
            cursor += 1
            need(cursor < len(records) and records[cursor], "GIT_RENAME_RECORD_INVALID")
        if path.casefold() != ".coding-tools" and not path.casefold().startswith(".coding-tools/"):
            entries.append({"path": path, "index_status": record[0], "worktree_status": record[1]})
        cursor += 1
    need(len(records) <= 2001, "GIT_STATUS_EXCEEDS_RUNTIME_BOUND")
    return {"base_head": head, "worktree_fp": path_fingerprint(root, [x["path"] for x in entries],
            {"head": head, "branch": branch, "entries": entries})}


def public_result(value):
    if "public_receipts" in value:
        candidates = [x for x in value["public_receipts"] if isinstance(x, dict) and x.get("phase") in {"observe", "cleanup"}]
        need(value.get("ok") is True and len(candidates) == 1, "TRANSPORT_RESULT_INVALID")
        value = candidates[0]
    need(value.get("ok") is True and value.get("phase") in {"observe", "cleanup"}
         and value.get("provenance") == "central_mcp_service_trial"
         and value.get("native_semantic_acceptance") == "pending" and value.get("replay_forbidden") is True,
         "PUBLIC_RESULT_INVALID")
    family, summary = value.get("family"), value.get("verified_patch_and_initial_proof_summary")
    family_keys = {"task_id", "action_id", "request_id", "writer_lease_generation", "state", "settled", "attempt_ids", "receipt_states"}
    need(isinstance(family, dict) and set(family) == family_keys and isinstance(summary, dict) and family.get("settled") is True
         and family.get("state") != "reconcile_required" and len(family.get("attempt_ids", [])) == 1, "ACTION_NOT_EXACT_SETTLED")
    need(re.fullmatch(r"act_[a-f0-9]{32}", str(family["action_id"]))
         and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", str(family["attempt_ids"][0]))
         and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", str(family["task_id"]))
         and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", str(family["request_id"]))
         and type(family["writer_lease_generation"]) is int and family["writer_lease_generation"] >= 1
         and family["state"] == "settled"
         and all(x in {"accepted", "running", "completed", "failed", "unknown", "rejected", "cancelled"} for x in family["receipt_states"]), "PUBLIC_FAMILY_IDENTIFIERS_INVALID")
    need(summary.get("file") == {"path": TARGET, "preimage_sha256": PRE, "postimage_sha256": POST, "bytes_written": 414}, "PATCH_EFFECT_MISMATCH")
    run, wave = summary.get("run_id"), summary.get("wave_id")
    need(all(isinstance(x, str) and re.fullmatch(r"[a-f0-9]{32}", x) for x in (run, wave))
         and run != OLD_RUN and wave != OLD_WAVE, "NEW_RUN_WAVE_REQUIRED")
    proof = summary.get("initial_verification")
    need(isinstance(proof, dict) and set(proof) == {"plan_sha256", "proof_status", "proof_ids", "proof_fingerprint", "command_id", "job_id"}
         and proof["plan_sha256"] == PLAN_SHA and proof["proof_status"] == "passed"
         and len(proof["proof_ids"]) == 1 and re.fullmatch(r"[a-f0-9]{32}", proof["proof_ids"][0]), "PASSED_INITIAL_PROOF_REQUIRED")
    need(all(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", str(proof[x])) for x in ("command_id", "job_id"))
         and re.fullmatch(r"[a-f0-9]{64}", str(proof["proof_fingerprint"])), "PROOF_IDENTIFIERS_INVALID")
    need(summary.get("response_sha256") == sha(canonical({"file": summary["file"], "initial_verification": proof})), "RESPONSE_DIGEST_MISMATCH")
    return family, summary


def correlate_journal(journal, family, summary, pins):
    need(journal.get("schema_version") == 1 and isinstance(journal.get("entries"), dict), "JOURNAL_INVALID")
    action, attempt = family["action_id"], family["attempt_ids"][0]
    entries = [entry for entry in journal["entries"].values() if entry.get("action_id") == action]
    need(len(entries) == 1 and entries[0].get("attempt_id") == attempt, "JOURNAL_ACTION_ATTEMPT_MISMATCH")
    entry, receipt = entries[0], entries[0].get("receipt", {})
    payload = receipt.get("payload", {})
    need(entry.get("state") == "completed" and receipt.get("receipt_state") == "completed"
         and receipt.get("receipt_submitted") is True and receipt.get("action_id") == action
         and receipt.get("attempt_id") == attempt, "COMPLETED_SUBMITTED_JOURNAL_REQUIRED")
    need(payload.get("schema_version") == 1 and payload.get("operation_kind") == "control_plane_approved_patch"
         and payload.get("patch_applied") is True and payload.get("local_semantic_acceptance") == "pending"
         and payload.get("actor") == {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"}, "NATIVE_RECEIPT_ACTOR_INVALID")
    for key in ("file", "initial_verification", "run_id", "wave_id", "response_sha256"):
        need(payload.get(key) == summary[key], "NATIVE_CENTRAL_RECEIPT_MISMATCH")
    need(payload.get("task_id") == family.get("task_id")
         and payload.get("writer_lease_generation") == family.get("writer_lease_generation"), "NATIVE_TASK_GENERATION_MISMATCH")
    expected_identity = {"activation_epoch_id": pins["activation_epoch"], "process_instance_id": pins["runtime_instance_id"],
                         "server_instance_id": pins["mcp_server_instance_id"], "tool_contract_sha256": pins["native_tool_contract_sha256"]}
    need(payload.get("runtime_identity") == expected_identity, "NATIVE_RUNTIME_IDENTITY_MISMATCH")
    return expected_identity


def correlate_ledger(connection, summary, pins, root, identity, preserved=OLD_HASHES):
    old = {}
    for table, column, value in (("runs", "run_id", OLD_RUN), ("waves", "wave_id", OLD_WAVE)):
        rows = connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (value,)).fetchall()
        need(len(rows) == 1, "OLD_PENDING_RECORD_MISSING")
        old[table] = sha(canonical(dict(rows[0]), ascii=True))
        need(old[table] == preserved[table], "OLD_PENDING_RECORD_CHANGED")
    run, wave, proof = summary["run_id"], summary["wave_id"], summary["initial_verification"]
    run_row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run,)).fetchone()
    wave_row = connection.execute("SELECT * FROM waves WHERE wave_id=? AND run_id=?", (wave, run)).fetchone()
    need(run_row is not None and wave_row is not None and wave_row["base_head"] == HEAD
         and wave_row["execution_mode"] == "mcp_only", "RUN_WAVE_LINEAGE_MISMATCH")
    need(run_row["status"] != "accepted" and wave_row["status"] != "ACCEPTED"
         and not connection.execute("SELECT 1 FROM checkpoints WHERE run_id=? AND status='accepted' LIMIT 1", (run,)).fetchone(), "UNEXPECTED_SEMANTIC_ACCEPTANCE")
    rows = connection.execute("SELECT * FROM managed_process_jobs WHERE job_id=? AND command_id=?", (proof["job_id"], proof["command_id"])).fetchall()
    need(len(rows) == 1, "EXACT_DURABLE_JOB_MISSING")
    job = dict(rows[0]); job_meta = metadata(job["metadata_json"])
    need(job["run_id"] == run and job["wave_id"] == wave and job["owner"] == "default"
         and job["lifecycle_state"] == "exited" and job["root_pid"] > 0 and bool(job["root_process_token"])
         and bool(job["finished_at"]) and job_meta.get("exit_code") == 0
         and job["process_instance_id"] == pins["runtime_instance_id"]
         and job_meta.get("command_sha256") == sha(" ".join(PLAN["argv"]).encode()), "JOB_TERMINAL_LINEAGE_MISMATCH")
    need(not connection.execute("SELECT 1 FROM managed_process_jobs WHERE run_id=? AND wave_id=? AND lifecycle_state IN ('starting','active','waiting','idle','running','orphaned') LIMIT 1", (run, wave)).fetchone(), "CANARY_JOB_NOT_QUIESCENT")
    proofs = [dict(row) for row in connection.execute("SELECT * FROM proofs WHERE run_id=? AND wave_id=? ORDER BY finished_at,proof_id", (run, wave))]
    need(len(proofs) == 1 and [x["proof_id"] for x in proofs] == proof["proof_ids"], "EXACT_PROOF_SET_MISMATCH")
    row = proofs[0]; meta = metadata(row["metadata_json"]); result = meta.get("result", {})
    binding = meta.get("proof_source_binding", {})
    expected_binding = {"schema_version": 1, "base_head": HEAD, "contract_fp": wave_row["contract_fp"],
                        "paths": [TARGET], "path_fingerprint": path_fingerprint(root, [TARGET])}
    command = "structured-argv:" + PLAN_SHA
    command_hash = sha(command.encode())
    need(row["status"] == "passed" and row["exit_code"] == 0 and row["cache_hit"] == 0
         and row["stage_version"] == "1" and row["stage_id"] == "initial-verification:" + PLAN_SHA[:16]
         and row["command_hash"] == command_hash and json.loads(row["upstream_json"]) == []
         and binding == expected_binding and meta.get("initial_verification") == PLAN and meta.get("plan_sha256") == PLAN_SHA,
         "SOURCE_BOUND_EXECUTED_PROOF_REQUIRED")
    need(result.get("status") == "passed" and result.get("ok") is True and result.get("exit_code") == 0
         and result.get("command_id") == proof["command_id"] and result.get("job_id") == proof["job_id"]
         and result.get("timed_out") is False and result.get("cancelled") is False and result.get("command") == command,
         "PROOF_RESULT_JOB_MISMATCH")
    timeout, workdir, expiry = result.get("effective_timeout_ms"), meta.get("workdir"), meta.get("authority_expires_at_ms")
    need(type(timeout) is int and 1000 <= timeout <= PLAN["timeout_ms"] and workdir in {".", "", str(root)}
         and type(expiry) is int and pins["requested_at_ms"] < expiry <= pins["expires_at_ms"], "PROOF_PLAN_BOUND_INVALID")
    config = {"command_hash": command_hash, "workdir": workdir, "timeout_ms": timeout,
              "initial_verification": PLAN, "authority_expires_at_ms": expiry}
    expected_input = sha(canonical({"stage_id": row["stage_id"], "stage_version": "1", "base_head": HEAD,
                        "worktree_fp": identity["worktree_fp"], "contract_fp": wave_row["contract_fp"],
                        "path_fp": binding["path_fingerprint"], "config": config, "upstream_proof_ids": []}))
    need(row["input_fingerprint"] == expected_input, "PROOF_INPUT_FINGERPRINT_MISMATCH")
    aggregate = sha((row["proof_id"] + ":" + row["input_fingerprint"]).encode())
    need(proof["proof_fingerprint"] == aggregate, "AGGREGATE_PROOF_FINGERPRINT_MISMATCH")
    completed_ms = int(datetime.fromisoformat(job["finished_at"].replace("Z", "+00:00")).timestamp() * 1000)
    return {"run_id": run, "wave_id": wave, "run_status": run_row["status"], "wave_status": wave_row["status"],
            "command_id": job["command_id"], "job_id": job["job_id"], "job_lifecycle": job["lifecycle_state"],
            "job_row_sha256": sha(canonical(job)), "exit_code": 0, "completed_at_ms": completed_ms, "proof_ids": proof["proof_ids"],
            "proof_fingerprint": aggregate, "proof_input_fingerprint": expected_input,
            "proof_source_binding": expected_binding, "proof_cache_hit": False,
            "old_pending_record_sha256": old, "old_pending_records_unchanged": True, "canary_jobs_quiescent": True}


def validate_output(value, summary):
    # Root captures the existing native read_output result, never reruns argv.
    proof = summary["initial_verification"]
    need(value.get("command_id") == proof["command_id"] and value.get("session_id") == proof["command_id"]
         and value.get("stream") == "stdout" and value.get("stream_output_ref") == "command:" + proof["command_id"] + ":stdout"
         and value.get("ok") is True and value.get("requested_offset") == 0 and value.get("offset") == 0
         and value.get("next_offset") is None and value.get("truncated") is False
         and value.get("omitted_bytes") == 0 and value.get("stream_dropped_bytes") == 0, "OUTPUT_CAPTURE_INCOMPLETE_OR_WRONG_COMMAND")
    content = value.get("content")
    need(isinstance(content, str) and len(content.encode()) <= 32768
         and len(content.encode()) == value.get("total_stream_bytes"), "OUTPUT_CAPTURE_BYTES_INVALID")
    lines = content.splitlines()
    need("TAP version 13" in lines and "1..4" in lines and "# tests 4" in lines
         and "# pass 4" in lines and "# fail 0" in lines and "# cancelled 0" in lines
         and "# skipped 0" in lines and "# todo 0" in lines and not any(re.match(r"\s*not ok\b", x) for x in lines), "TAP_4_OF_4_REQUIRED")
    for number, name in enumerate(NAMES, 1):
        need(any(re.fullmatch(r"ok " + str(number) + " - " + re.escape(name) + r"(?:\s+#.*)?", x) for x in lines), "TAP_TEST_IDENTITY_MISMATCH")
    return {"checker_pass": 4, "checker_fail": 0, "stdout_sha256": sha(content.encode()),
            "stdout_bytes": len(content.encode()), "output_ref": value["stream_output_ref"]}


def validate_capture(value, summary, family, runtime_identity, completed_at_ms, observation_sha):
    expected_keys = {"ok", "phase", "observed_at_ms", "provenance", "client_id", "client_type", "attestation_claimed",
                     "native_semantic_acceptance", "tool", "action", "observation_sha256", "completed_at_ms", "action_id",
                     "task_id", "command_id", "job_id", "run_id", "wave_id", "proof_ids", "proof_fingerprint", "plan_sha256",
                     "runtime_identity", "stdout", "stderr", "tap", "remote_mutation"}
    need(isinstance(value, dict) and set(value) == expected_keys and value["ok"] is True
         and value["phase"] == "native_canary_output_capture" and value["provenance"] == "local_authenticated_read_only"
         and value["client_id"] == "electron-r13-canary-output-reader" and value["client_type"] == "electron"
         and value["attestation_claimed"] is False and value["native_semantic_acceptance"] == "pending"
         and value["tool"] == "command_control" and value["action"] == "read" and value["remote_mutation"] is False,
         "OUTPUT_READER_PROVENANCE_INVALID")
    proof = summary["initial_verification"]
    expected = {"action_id": family["action_id"], "task_id": family["task_id"], "run_id": summary["run_id"],
                "wave_id": summary["wave_id"], "runtime_identity": runtime_identity, "completed_at_ms": completed_at_ms,
                "observation_sha256": observation_sha,
                **{key: proof[key] for key in ("command_id", "job_id", "proof_ids", "proof_fingerprint", "plan_sha256")}}
    need(all(value.get(key) == item for key, item in expected.items()), "OUTPUT_CAPTURE_LINEAGE_MISMATCH")
    need(type(value["observed_at_ms"]) is int and 0 <= value["observed_at_ms"] - completed_at_ms < 300000,
         "OUTPUT_CAPTURE_OUTSIDE_RETENTION_WINDOW")
    result = validate_output(value["stdout"], summary)
    need(value["stdout"].get("content_sha256") == result["stdout_sha256"]
         and value["tap"] == {"tests": 4, "pass": 4, "fail": 0, "content_sha256": result["stdout_sha256"]}, "OUTPUT_CAPTURE_DIGEST_MISMATCH")
    stderr = value["stderr"]
    need(stderr.get("ok") is True and stderr.get("command_id") == proof["command_id"]
         and stderr.get("session_id") == proof["command_id"] and stderr.get("stream") == "stderr"
         and stderr.get("stream_output_ref") == "command:" + proof["command_id"] + ":stderr"
         and stderr.get("content") == "" and stderr.get("content_sha256") == sha(b"")
         and stderr.get("total_stream_bytes") == 0 and stderr.get("requested_offset") == 0 and stderr.get("offset") == 0
         and stderr.get("next_offset") is None and stderr.get("truncated") is False
         and stderr.get("omitted_bytes") == 0 and stderr.get("stream_dropped_bytes") == 0, "OUTPUT_STDERR_CAPTURE_INVALID")
    return {**result, "stderr_sha256": sha(b""), "stderr_bytes": 0, "captured_at_ms": value["observed_at_ms"],
            "attestation_claimed": False, "provenance": "local_authenticated_read_only"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--pins", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path)
    args = parser.parse_args()
    receipt, receipt_sha = load(args.receipt); pins, pins_sha = load(args.pins)
    family, summary = public_result(receipt)
    need(sha(canonical(PLAN)) == PLAN_SHA and type(pins["requested_at_ms"]) is int
         and pins["expires_at_ms"] - pins["requested_at_ms"] == 3600000, "AUTHORITY_PLAN_PINS_INVALID")
    need(all(re.fullmatch(r"[A-Za-z0-9_-]{1,256}", str(pins[x])) for x in ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id"))
         and re.fullmatch(r"[a-f0-9]{64}", str(pins["native_tool_contract_sha256"])), "RUNTIME_PINS_INVALID")
    need(sha((ROOT / TARGET).read_bytes()) == POST and (ROOT / TARGET).stat().st_size == 414
         and sha((ROOT / CHECKER).read_bytes()) == CHECKER_SHA, "EXACT_LIVE_POSTIMAGE_CHECKER_REQUIRED")
    identity = source_identity(ROOT)
    journal, journal_sha = load(JOURNAL)
    native_identity = correlate_journal(journal, family, summary, pins)
    with closing(sqlite3.connect(LEDGER.resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=10)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        evidence = correlate_ledger(connection, summary, pins, ROOT, identity)
        connection.rollback()
    need(source_identity(ROOT) == identity, "SOURCE_CHANGED_DURING_CORRELATION")
    output = None; output_sha = None
    if args.output_receipt:
        output_value, output_sha = load(args.output_receipt)
        output = validate_capture(output_value, summary, family, native_identity, evidence["completed_at_ms"], receipt_sha)
    result = {"ok": True, "observed_at": datetime.now(timezone.utc).isoformat(),
              "kind": "r13_query_only_native_correlation", "source_head": HEAD, "source_worktree_fp": identity["worktree_fp"],
              "target_postimage_sha256": POST, "checker_sha256": CHECKER_SHA, "plan_sha256": PLAN_SHA,
              "central_receipt_sha256": receipt_sha, "pins_sha256": pins_sha, "journal_sha256": journal_sha,
              "runtime_identity": native_identity, "family": family, "correlation": evidence,
              "checker_output": output, "output_receipt_sha256": output_sha,
              "strongest_proof": "patch_job_source_bound_proof_and_tap_4_of_4" if output else "patch_job_source_bound_proof",
              "remaining_gaps": ["NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE"] + ([] if output else ["NATIVE_TAP_OUTPUT_NOT_CAPTURED"]),
              "native_semantic_acceptance": "pending", "mutated_canonical_ledger": False,
              "executed_or_replayed_command": False, "network_calls": 0}
    destination = HERE / ("correlation-" + str(time.time_ns()) + ".json")
    with destination.open("xb") as handle:
        handle.write(canonical(result) + b"\n")
    return {"ok": True, "evidence_path": str(destination), "evidence_sha256": sha(destination.read_bytes()),
            "strongest_proof": result["strongest_proof"], "remaining_gaps": result["remaining_gaps"]}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except Exception as error:
        print(json.dumps({"ok": False, "code": str(error) if isinstance(error, Rejected) else type(error).__name__,
                          "mutated_canonical_ledger": False, "executed_or_replayed_command": False, "network_calls": 0}))
        raise SystemExit(2)
