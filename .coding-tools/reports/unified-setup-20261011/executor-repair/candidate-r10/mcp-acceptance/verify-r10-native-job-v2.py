"""Root-only read-only correlation of exact cold public transport and durable Job.

Journal v1 stores only entry/receipt, not request. Request proof is the immutable
public cold transport. No stdout, stderr, protected config or full journal emitted.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

sys.dont_write_bytecode = True
ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")
HERE = Path(__file__).resolve().parent
ACTION = "act_9482be2aef814d82b3ff4722b5979a25"
TASK = "task_80e2fb1ba3e449edbfb05d5a53055642"
ATTEMPT = "try_78e2a7ebbe404afc8d432e5efa5f4152"
COMMAND = "2e54DFBMUi5oQG3R4qV0BpHm"
JOB = "4978280465374604b7eb7e04b4297327"
RESPONSE = "dd7a305f5be0ec9383bbf1119e655002345c6a2e685a544879b50b4679ee0b39"
OUTPUT = "32214fedb8fb33cebf30bf69a4c16347819a5899c3da7e730fa8a92fc2d03af4"
ORIGINAL = "b620253eb7cd1851fd38c862cfaa3be2abc407c2ddd3ad8534af96739048baf5"
PINS = "28e8dff65226c5001184ad7dbd34fd6e65b2e05af106c10bdb0d73d01aae7b67"
TRANSPORT = "c3ab3f3cb0d80c5023f32efc20a964586fdd3dcfdd7bea361f2e91120eba4e6a"
ARGV = ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"]


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, limit=1048576):
    raw = path.read_bytes()
    require(0 < len(raw) <= limit, "ARTIFACT_SIZE_INVALID")
    return raw


def main():
    require(len(sys.argv) == 6, "EXACT_COLD_ARGUMENTS_REQUIRED")
    pins_path, action, task, response, output = sys.argv[1:]
    require((action, task, response, output) == (ACTION, TASK, RESPONSE, OUTPUT), "EXACT_COLD_ARGUMENTS_REQUIRED")
    require(Path(pins_path).resolve() == (HERE / "pins.root-reviewed.cold.json").resolve(), "EXACT_PINS_FILE_REQUIRED")
    require(sha(read(HERE / "verify-r10-native-job.py")) == ORIGINAL, "ORIGINAL_VERIFIER_CHANGED")
    raw = read(Path(pins_path)); require(sha(raw) == PINS, "REVIEWED_COLD_PINS_CHANGED")
    pins = json.loads(raw)
    raw = read(HERE / "transport-execute-cold-20261011T130654124612Z.jsonl")
    require(sha(raw) == TRANSPORT, "IMMUTABLE_COLD_TRANSPORT_CHANGED")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]

    def one(phase):
        matches = [row for row in rows if row.get("phase") == phase]
        require(len(matches) == 1, "EXACT_PUBLIC_PHASE_REQUIRED")
        return matches[0]

    started, preflight = one("root_mcp_transport_started"), one("r10_mcp_canary_preflight")
    opened, queued = one("r10_mcp_canary_task_opened"), one("r10_mcp_canary_queued")
    terminal, cleanup = one("r10_mcp_canary_terminal"), one("r10_mcp_canary_cleanup_complete")
    complete, finished = one("r10_mcp_canary_complete"), one("root_mcp_transport_finished")
    request = preflight["preflight"]
    require(started["action"] == "execute" and started["mode"] == "cold" and started["pins_sha256"] == PINS
            and started["expected_state_sha256"] == preflight["state_sha256"]
            and preflight["ok"] is True and preflight["remote_mutation"] is False
            and request["mode"] == "cold" and request["pins"] == pins
            and request["binding_id"] == "bind_3e05bf64cb3e4bab93d930ae1692bebb"
            and request["argv"] == ARGV and request["timeout_ms"] == 300000 and request["max_output_bytes"] == 32768
            and opened["task_id"] == TASK and opened["mode"] == "cold"
            and queued["task_id"] == TASK and queued["action_id"] == ACTION and queued["mode"] == "cold"
            and queued["replayed"] is False, "EXACT_COLD_REQUEST_TRANSPORT_REQUIRED")
    require(terminal["ok"] is True and terminal["mode"] == "cold" and terminal["action_id"] == ACTION
            and terminal["task_id"] == TASK and terminal["attempt_id"] == ATTEMPT
            and terminal["command_id"] == COMMAND and terminal["job_id"] == JOB
            and terminal["response_sha256"] == RESPONSE and terminal["output_sha256"] == OUTPUT
            and terminal["output_bytes"] == 1069 and terminal["exit_code"] == 0
            and terminal["status"] == "exited" and terminal["timed_out"] is False
            and cleanup["action_id"] == ACTION and cleanup["task_id"] == TASK and cleanup["command_replayed"] is False
            and cleanup["writer_released"] is True and cleanup["task_closed"] is True
            and complete["ok"] is True and complete["retained_history_preserved"] is True
            and finished["ok"] is True and finished["remote_exit_code"] == 0, "EXACT_TERMINAL_PUBLIC_FAMILY_REQUIRED")
    journal = json.loads(read(PROFILE / "control-plane-node.json.exec-journal.json", 16 * 1048576))
    require(set(journal) == {"schema_version", "entries"} and journal["schema_version"] == 1, "EXACT_EXEC_JOURNAL_SCHEMA_REQUIRED")
    entries = [(key, value) for key, value in journal["entries"].items() if value.get("action_id") == ACTION]
    require(len(entries) == 1, "EXACT_ONE_ATTEMPT_REQUIRED")
    key, entry = entries[0]
    require(key == f"{ACTION}|{ATTEMPT}" and set(entry) == {"action_id", "attempt_id", "receipt", "state"}
            and entry["action_id"] == ACTION and entry["attempt_id"] == ATTEMPT and entry["state"] == "completed",
            "EXACT_JOURNAL_ENTRY_REQUIRED")
    receipt = entry["receipt"]; payload = receipt["payload"]
    require(set(receipt) == {"action_id", "attempt_id", "local_handle", "payload", "receipt_state", "receipt_submitted"}
            and receipt["action_id"] == ACTION and receipt["attempt_id"] == ATTEMPT
            and receipt["receipt_submitted"] is True and receipt["receipt_state"] == "completed"
            and receipt["local_handle"] == payload["local_handle"], "EXACT_SUBMITTED_JOURNAL_RECEIPT_REQUIRED")
    require(payload["schema_version"] == 1 and payload["operation_kind"] == "control_plane_exec"
            and payload["action_id"] == ACTION and payload["attempt_id"] == ATTEMPT and payload["task_id"] == TASK
            and payload["command_id"] == COMMAND and payload["job_id"] == JOB
            and payload["response_sha256"] == RESPONSE and payload["exit_code"] == 0 and payload["status"] == "exited"
            and payload["timed_out"] is False and payload["truncated"] is False and payload["writer_lease_generation"] == 1
            and payload["actor"] == {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"}
            and payload["facade_contract"] == pins["facade_contract"]
            and re.fullmatch(r"cp_exec_[a-f0-9]{48}", payload["local_handle"])
            and payload["policy_sha256"] == "31125fd75f5147770eecde7b926e3c46efd1f5ee83a55b58d180f8b200966367",
            "EXACT_R10_TERMINAL_PAYLOAD_REQUIRED")
    identity = payload["runtime_identity"]
    require(identity == terminal["runtime_identity"]
            and all(identity[field] == pins[field] for field in ("activation_epoch_id", "process_instance_id", "server_instance_id"))
            and identity["tool_contract_sha256"] == pins["native_contract_sha256"], "EXACT_R10_NATIVE_IDENTITY_REQUIRED")
    # Recompute the same bounded output digest used by the local bridge.
    projection_fields = ("status", "exit_code", "stdout", "stderr", "truncated", "timed_out", "command_id", "job_id", "run_id", "wave_id", "output_refs")
    projection = {name: payload[name] for name in projection_fields}
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    require(sha(encoded) == RESPONSE, "RECOMPUTED_RESPONSE_HASH_MISMATCH")
    raw_output = (payload["stdout"] + payload["stderr"]).encode("utf-8")
    require(len(raw_output) == 1069 == payload["output_bytes"] and sha(raw_output) == OUTPUT, "EXACT_SERVER_OUTPUT_HASH_REQUIRED")
    database = ROOT / ".coding-tools/orchestration/ledger.sqlite3"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON"); connection.execute("BEGIN")
        jobs = connection.execute("SELECT * FROM managed_process_jobs WHERE job_id=? AND command_id=?", (JOB, COMMAND)).fetchall()
        require(len(jobs) == 1, "EXACT_DURABLE_JOB_REQUIRED")
        job = dict(jobs[0]); metadata = json.loads(job["metadata_json"])
        require(job["root_pid"] == 20952 and job["root_process_token"] == "134361976541467217"
                and job["started_at"] == "2026-10-11T13:07:13.377Z" and job["finished_at"] == "2026-10-11T13:07:42.392Z"
                and job["lifecycle_state"] == "exited" and job["owner"] == "control-plane-exec-bridge"
                and job["process_instance_id"] == pins["process_instance_id"] and job["runtime_instance_id"] == pins["server_instance_id"]
                and job["checkout_id"] == "8c2a02b70c57dcf4dfdd6d6c0c317df0038f2f85572180fcb1bd623391f9ebdc"
                and job["run_id"] == payload["run_id"] == "" and job["wave_id"] == payload["wave_id"] == ""
                and metadata["command_sha256"] == sha(b"node") and metadata["exit_code"] == 0,
                "EXACT_REAL_TERMINAL_PROCESS_REQUIRED")
        safe_job = {name: job[name] for name in ("job_id", "command_id", "run_id", "wave_id", "root_pid", "root_process_token", "owner", "lifecycle_state", "started_at", "finished_at", "process_instance_id", "runtime_instance_id")}
    print(json.dumps({"phase": "r10_native_job_correlated_v2", "ok": True, "action_id": ACTION, "attempt_id": ATTEMPT,
                      "task_id": TASK, "job": safe_job, "exit_code": 0, "response_sha256": RESPONSE,
                      "output_sha256": OUTPUT, "output_bytes": len(raw_output), "runtime_identity": identity,
                      "pins_sha256": PINS, "cold_transport_sha256": TRANSPORT,
                      "original_verifier_sha256": ORIGINAL, "helper_sha256": sha(Path(__file__).read_bytes()),
                      "request_evidence_location": "immutable_cold_transport", "journal_request_absent_by_schema": True,
                      "run_wave_correlation": "standalone_exec_both_empty", "proof_ledger_or_acceptance_proven": False,
                      "ledger_mutated": False, "journal_mutated": False, "command_replayed": False}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "r10_native_job_correlation_failed_v2", "ok": False,
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__,
                          "command_replayed": False}, separators=(",", ":")))
        raise SystemExit(1) from None
