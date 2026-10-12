"""Read-only exact immutable transport -> journal -> durable terminal Job proof.

Root supplies explicit artifact hashes and receipt family. No command replay,
native call, authority mutation, raw output or ProofLedger/acceptance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")
ARGV = ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"]
CANARY_SHA = "54f8ee88889e60437c7831410aae7845b2481401ce3f73bf7daa33a77e3ea047"


def need(value, code):
    if not value:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def artifact(file, expected):
    need(file.resolve(strict=True).parent == BASE and not file.is_symlink(), "EXACT_EVIDENCE_DIRECTORY_REQUIRED")
    raw = file.read_bytes()
    need(0 < len(raw) <= 1048576 and re.fullmatch(r"[a-f0-9]{64}", expected or "") and sha(raw) == expected,
         "EXPLICIT_ARTIFACT_HASH_MISMATCH")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pins-file", type=Path, required=True)
    parser.add_argument("--pins-sha256", required=True)
    parser.add_argument("--transport-file", type=Path, required=True)
    parser.add_argument("--transport-sha256", required=True)
    parser.add_argument("--mode", choices=("cold", "warm"), required=True)
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--response-sha256", required=True)
    parser.add_argument("--output-sha256", required=True)
    args = parser.parse_args()
    need(re.fullmatch(r"act_[a-f0-9]{32}", args.action_id) and re.fullmatch(r"task_[a-f0-9]{32}", args.task_id)
         and all(re.fullmatch(r"[a-f0-9]{64}", value) for value in (args.response_sha256, args.output_sha256)), "EXPLICIT_RECEIPT_PINS_INVALID")
    pins = json.loads(artifact(args.pins_file, args.pins_sha256))
    rows = [json.loads(line) for line in artifact(args.transport_file, args.transport_sha256).decode("utf-8").splitlines() if line]

    def one(phase):
        found = [row for row in rows if row.get("phase") == phase]
        need(len(found) == 1, "EXACT_TRANSPORT_PHASE_REQUIRED")
        return found[0]

    started, preflight = one("root_mcp_transport_started"), one("r10_mcp_canary_preflight")
    opened, queued = one("r10_mcp_canary_task_opened"), one("r10_mcp_canary_queued")
    terminal, cleanup = one("r10_mcp_canary_terminal"), one("r10_mcp_canary_cleanup_complete")
    complete, finished = one("r10_mcp_canary_complete"), one("root_mcp_transport_finished")
    request = preflight["preflight"]
    need(started["action"] == "execute" and started["mode"] == args.mode and started["helper_sha256"] == CANARY_SHA
         and started["pins_sha256"] == args.pins_sha256 and started["expected_state_sha256"] == preflight["state_sha256"]
         and preflight["ok"] is True and preflight["remote_mutation"] is False
         and request["pins"] == pins and request["mode"] == args.mode and request["argv"] == ARGV
         and request["timeout_ms"] == 300000 and request["max_output_bytes"] == 32768
         and request["binding_id"] == "bind_3e05bf64cb3e4bab93d930ae1692bebb"
         and request["source_revision"] == "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
         and request["package_source_sha256"] == "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
         and opened["task_id"] == args.task_id and opened["mode"] == args.mode
         and queued["task_id"] == args.task_id and queued["action_id"] == args.action_id and queued["mode"] == args.mode
         and queued["replayed"] is False, "EXACT_REQUEST_TRANSPORT_REQUIRED")
    need(terminal["ok"] is True and terminal["mode"] == args.mode and terminal["action_id"] == args.action_id
         and terminal["task_id"] == args.task_id and terminal["response_sha256"] == args.response_sha256
         and terminal["output_sha256"] == args.output_sha256 and terminal["exit_code"] == 0
         and terminal["status"] == "exited" and terminal["timed_out"] is False
         and cleanup["action_id"] == args.action_id and cleanup["task_id"] == args.task_id
         and cleanup["command_replayed"] is False and cleanup["writer_released"] is True and cleanup["task_closed"] is True
         and complete["ok"] is True and complete["mode"] == args.mode and complete["action_id"] == args.action_id
         and complete["task_id"] == args.task_id and complete["retained_history_preserved"] is True
         and finished["ok"] is True and finished["action"] == "execute" and finished["mode"] == args.mode
         and finished["remote_exit_code"] == 0, "EXACT_TERMINAL_TRANSPORT_REQUIRED")
    attempt, command, job_id = (terminal[key] for key in ("attempt_id", "command_id", "job_id"))
    need(re.fullmatch(r"try_[a-f0-9]{32}", attempt)
         and all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) for value in (command, job_id)), "EXACT_JOB_IDENTIFIERS_REQUIRED")
    journal_raw = (PROFILE / "control-plane-node.json.exec-journal.json").read_bytes()
    need(0 < len(journal_raw) <= 16777216, "JOURNAL_SIZE_INVALID")
    journal = json.loads(journal_raw)
    need(set(journal) == {"schema_version", "entries"} and journal["schema_version"] == 1, "EXACT_JOURNAL_SCHEMA_REQUIRED")
    entries = [(key, value) for key, value in journal["entries"].items() if value.get("action_id") == args.action_id]
    need(len(entries) == 1, "EXACT_ONE_ATTEMPT_REQUIRED")
    key, entry = entries[0]
    need(key == f"{args.action_id}|{attempt}" and set(entry) == {"action_id", "attempt_id", "receipt", "state"}
         and entry["attempt_id"] == attempt and entry["state"] == "completed", "EXACT_JOURNAL_ENTRY_REQUIRED")
    receipt = entry["receipt"]; payload = receipt["payload"]
    need(set(receipt) == {"action_id", "attempt_id", "local_handle", "payload", "receipt_state", "receipt_submitted"}
         and receipt["action_id"] == args.action_id and receipt["attempt_id"] == attempt
         and receipt["receipt_state"] == "completed" and receipt["receipt_submitted"] is True
         and receipt["local_handle"] == payload["local_handle"], "EXACT_SUBMITTED_RECEIPT_REQUIRED")
    need(payload["schema_version"] == 1 and payload["operation_kind"] == "control_plane_exec"
         and payload["action_id"] == args.action_id and payload["task_id"] == args.task_id and payload["attempt_id"] == attempt
         and payload["command_id"] == command and payload["job_id"] == job_id
         and payload["status"] == "exited" and payload["exit_code"] == 0 and payload["timed_out"] is False
         and payload["truncated"] is False and type(payload["writer_lease_generation"]) is int and payload["writer_lease_generation"] > 0
         and payload["actor"] == {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"}
         and payload["facade_contract"] == pins["facade_contract"]
         and re.fullmatch(r"cp_exec_[a-f0-9]{48}", payload["local_handle"])
         and re.fullmatch(r"[a-f0-9]{64}", payload["policy_sha256"]), "EXACT_TERMINAL_PAYLOAD_REQUIRED")
    identity = payload["runtime_identity"]
    need(identity == terminal["runtime_identity"] and all(identity[name] == pins[name] for name in ("activation_epoch_id", "process_instance_id", "server_instance_id"))
         and identity["tool_contract_sha256"] == pins["native_contract_sha256"], "EXACT_NATIVE_IDENTITY_REQUIRED")
    projection = {name: payload[name] for name in ("status", "exit_code", "stdout", "stderr", "truncated", "timed_out", "command_id", "job_id", "run_id", "wave_id", "output_refs")}
    need(sha(json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()) == payload["response_sha256"] == args.response_sha256,
         "RECOMPUTED_RESPONSE_HASH_MISMATCH")
    raw_output = (payload["stdout"] + payload["stderr"]).encode("utf-8")
    need(sha(raw_output) == args.output_sha256 and len(raw_output) == payload["output_bytes"] == terminal["output_bytes"], "EXACT_OUTPUT_HASH_REQUIRED")
    with sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON"); connection.execute("BEGIN")
        found = connection.execute("SELECT * FROM managed_process_jobs WHERE job_id=? AND command_id=?", (job_id, command)).fetchall()
        need(len(found) == 1, "EXACT_DURABLE_JOB_REQUIRED")
        job = dict(found[0]); metadata = json.loads(job["metadata_json"])
        need(type(job["root_pid"]) is int and job["root_pid"] > 0 and isinstance(job["root_process_token"], str)
             and re.fullmatch(r"[0-9]{8,32}", job["root_process_token"])
             and job["started_at"] and job["finished_at"] and job["finished_at"] >= job["started_at"]
             and job["lifecycle_state"] == "exited" and job["owner"] == "control-plane-exec-bridge"
             and job["process_instance_id"] == pins["process_instance_id"] and job["runtime_instance_id"] == pins["server_instance_id"]
             and job["run_id"] == payload["run_id"] and job["wave_id"] == payload["wave_id"]
             and bool(job["run_id"]) == bool(job["wave_id"])
             and all(not value or re.fullmatch(r"[a-f0-9]{32}", value) for value in (job["run_id"], job["wave_id"]))
             and metadata["command_sha256"] == sha(ARGV[0].encode()) and metadata["exit_code"] == 0, "REAL_TERMINAL_JOB_OR_LINEAGE_MISMATCH")
        safe_job = {name: job[name] for name in ("job_id", "command_id", "run_id", "wave_id", "root_pid", "root_process_token", "owner", "lifecycle_state", "started_at", "finished_at", "process_instance_id", "runtime_instance_id")}
    print(json.dumps({"phase": "r10_native_job_correlated_v3", "ok": True, "mode": args.mode, "action_id": args.action_id,
                      "attempt_id": attempt, "task_id": args.task_id, "job": safe_job, "runtime_identity": identity,
                      "response_sha256": args.response_sha256, "output_sha256": args.output_sha256, "output_bytes": len(raw_output),
                      "pins_sha256": args.pins_sha256, "transport_sha256": args.transport_sha256,
                      "helper_sha256": sha(Path(__file__).read_bytes()), "request_evidence_location": "immutable_transport",
                      "run_wave_correlation": "exact_equal" if job["run_id"] else "standalone_exec_both_empty",
                      "proof_ledger_or_acceptance_proven": False, "ledger_mutated": False, "journal_mutated": False,
                      "command_replayed": False}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "r10_native_job_correlation_failed_v3", "ok": False,
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__,
                          "command_replayed": False}, separators=(",", ":")))
        raise SystemExit(1) from None
