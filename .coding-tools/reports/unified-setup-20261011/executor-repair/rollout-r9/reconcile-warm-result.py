"""Evidence-bound reconciliation of one completed Job whose relay was rejected.

No command replay, output fabrication, journal rewriting or semantic acceptance.
The action receipt is failed because its output relay was rejected; the exact
native Job exit is retained separately and does not establish a TAP verdict.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import zlib

ROOT = Path(r"E:\Github\Tools-Codex-web")
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_fc024ff0b54c4a8ba4c7c7b0228a7e76"
ATTEMPT = "try_89bba4cdf2d94c0d8fee58111cd56839"
TASK = "task_3b1889c84dbd4e54a2ac9729a8a4da1f"
KEY = "cpex_1ab70f60045c8e4c03a0b678176dd5b05f3262d03fa76cabdf6ea636"
JOB = "771c4ec8b0d1488fb495dcb6af64bf56"
COMMAND = "-4hBa9tkNAYi4ngWamUIO4Ba"
CANDIDATE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-executor-lifecycle-1011-r9/win-unpacked"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    args = parser.parse_args()
    require(not args.submit or args.operator_approved and Path(__file__).with_name("authorization.md").is_file(),
            "OPERATOR_AUTHORIZATION_REQUIRED")
    journal_path = PROFILE / "control-plane-node.json.exec-journal.json"
    journal_sha = hashlib.sha256(journal_path.read_bytes()).hexdigest()
    journal = json.loads(journal_path.read_text())
    entries = [row for row in journal["entries"].values() if row.get("action_id") == ACTION]
    require(len(entries) == 1 and entries[0]["attempt_id"] == ATTEMPT and entries[0]["state"] == "unknown",
            "EXACT_UNKNOWN_JOURNAL_REQUIRED")
    entry = entries[0]
    require(entry["receipt"]["receipt_submitted"] is True
            and entry["receipt"]["payload"]["diagnostic_code"] == "CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID",
            "EXACT_ORIGINAL_RELAY_DIAGNOSTIC_REQUIRED")
    request = entry["request"]
    require(request["task_id"] == TASK and request["operation"] == "exec_run"
            and request["argv"] == ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"],
            "EXACT_TEST_REQUEST_REQUIRED")
    material = {name: request[name] for name in ("action_id", "attempt_id", "writer_lease_generation", "operation", "argv",
                "timeout_ms", "max_output_bytes", "facade_contract", "yield_time_ms", "wait_ms")}
    material["task_id"] = request["task_id"].strip()
    for name in ("command_id", "job_id", "local_handle", "consumer_id", "signal", "run_id", "wave_id", "cwd"):
        material[name] = request[name] or ""
    derived = "cpex_" + hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False,
                                                separators=(",", ":")).encode()).hexdigest()[:56]
    require(derived == KEY, "EXACT_REQUEST_NATIVE_CORRELATION_REQUIRED")
    with sqlite3.connect((ROOT / ".coding-tools/orchestration/ledger.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        idem = db.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?", (KEY,)).fetchone()
        job = db.execute("SELECT * FROM managed_process_jobs WHERE job_id=? AND command_id=?", (JOB, COMMAND)).fetchone()
        require(idem is not None and job is not None and idem["operation"] == "exec_command"
                and idem["status"] == "completed" and not idem["error_code"] and idem["finished_at"],
                "COMPLETED_NATIVE_IDEMPOTENCY_REQUIRED")
        require(job["owner"] == "control-plane-exec-bridge" and job["lifecycle_state"] == "exited"
                and job["root_pid"] > 0 and job["finished_at"] is not None, "EXACT_TERMINAL_NATIVE_JOB_REQUIRED")
        require(db.execute("SELECT COUNT(*) FROM managed_process_jobs WHERE lifecycle_state IN "
                           "('starting','active','waiting','idle','running','terminating')").fetchone()[0] == 0,
                "ACTIVE_NATIVE_JOB_REMAINS")
        require(idem["summary_codec"] == "zlib_json", "EXPECTED_NATIVE_SUMMARY_CODEC_REQUIRED")
        summary = json.loads(zlib.decompress(idem["summary_blob"]))
        structured = summary["tool_result"]["structuredContent"]
        require(summary["tool_result"]["isError"] is False and structured["command_id"] == COMMAND
                and structured["execution_owner"]["job_id"] == JOB and structured["status"] == "exited"
                and structured["exit_code"] == 0 and structured["timed_out"] is False,
                "EXACT_NATIVE_SUCCESS_SUMMARY_REQUIRED")
        for stream in ("stdout", "stderr"):
            retained = structured[stream]
            require(isinstance(retained, dict) and retained["redacted"] is True
                    and isinstance(retained["sha256"], str) and len(retained["sha256"]) == 64,
                    "EXPECTED_HASH_ONLY_OUTPUT_EVIDENCE_REQUIRED")
        payload = {"schema_version": 1, "operation_kind": "control_plane_exec",
            "code": "CONTROL_PLANE_EXEC_RESULT_REJECTED_AFTER_PROCESS",
            "diagnostic_code": "CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID",
            "action_id": ACTION, "attempt_id": ATTEMPT, "task_id": TASK,
            "writer_lease_generation": request["writer_lease_generation"],
            "command_id": COMMAND, "job_id": JOB, "native_idempotency_key": KEY,
            "native_job_lifecycle": job["lifecycle_state"], "native_job_root_pid": job["root_pid"],
            "native_job_finished_at": job["finished_at"], "native_exit_code": structured["exit_code"],
            "execution_started": True, "output_verified": False,
            "native_stdout_sha256": structured["stdout"]["sha256"],
            "native_stderr_sha256": structured["stderr"]["sha256"],
            "reconciliation_evidence": "exact_request_idempotency_summary_and_terminal_native_job; relay_rejected_valid_native_identifier"}
    node_file = CANDIDATE / "resources/resources/control-plane/node_agent.py"
    parity = json.loads(Path(__file__).parents[1].joinpath("candidate-parity-executor-lifecycle-1011-r9-20261011T110727929Z.json").read_text())
    expected = next(item["source_sha256"] for item in parity["source_parity"] if item["source"] == "control-plane/control_plane/node_agent.py")
    require(hashlib.sha256(node_file.read_bytes()).hexdigest() == expected, "EXACT_R9_NODE_AGENT_REQUIRED")
    spec = importlib.util.spec_from_file_location("r9_node_agent_reconciliation", node_file)
    node = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(node)
    response = None
    if args.submit:
        receipt = node._journal_receipt(ACTION, ATTEMPT, "failed", "", payload)
        response = node._submit_receipt(node._config(PROFILE / "control-plane-node.json"), {"receipt": receipt})
        require(response.get("action_id") == ACTION and response.get("attempt_id") == ATTEMPT
                and response.get("receipt_state") == "failed" and response.get("delivery_state") == "settled",
                "TERMINAL_RELAY_FAILURE_ACK_REQUIRED")
    require(hashlib.sha256(journal_path.read_bytes()).hexdigest() == journal_sha, "ORIGINAL_UNKNOWN_JOURNAL_CHANGED")
    report = {"observed_at": datetime.now(timezone.utc).isoformat(),
        "phase": "warm_relay_reconciliation_submitted" if args.submit else "warm_relay_reconciliation_prepared",
        "ok": True, "submitted": args.submit, "action_id": ACTION, "attempt_id": ATTEMPT, "task_id": TASK,
        "receipt_state": "failed", "code": payload["code"], "job_id": JOB, "command_id": COMMAND,
        "native_exit_code": 0, "native_job_lifecycle": "exited", "native_job_root_pid": payload["native_job_root_pid"],
        "output_verified": False, "tap_verdict_verified": False, "command_replayed": False,
        "original_journal_sha256": journal_sha, "original_journal_preserved": True,
        "server_ack": {name: response.get(name) for name in ("receipt_id", "receipt_state", "delivery_state", "replayed")} if response else None}
    with Path(__file__).with_name("warm-reconciliation.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps(report, separators=(",", ":")))


try:
    main()
except Exception as error:
    print(json.dumps({"phase": "warm_reconciliation_refused", "ok": False,
                      "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}, separators=(",", ":")))
    raise SystemExit(1) from None
