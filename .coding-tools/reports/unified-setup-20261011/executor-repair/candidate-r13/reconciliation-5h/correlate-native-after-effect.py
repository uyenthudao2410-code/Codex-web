"""Read-only source/Job/proof capsule for exact r13 timeout; no central settlement."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import time
import zlib

HERE = Path(__file__).resolve().parent
CORRELATOR = HERE.parent / "canary-5h/correlate_r13_5h_source_identity.py"
CORRELATOR_SHA = "8dd49d77566f64ea846746af8b23455257cf8bf11b75fa2ab4ef176a060b4c76"
ACTION = "act_b2335c57472b4d68931d10dda1572ff9"
TASK = "task_3b2a2a860ca54ef7889d2efce6923dc7"
RUN = "fbaf4b0700d04794af4062671c1bcd2b"
WAVE = "e712eca9463e465fb1905264c998f50c"
JOB = "e0d55c2194fa404eae7f3f4dcaf383bf"
COMMAND = "mSj-X1p4ZcQ97Q_TX-xnzzUD"
PROOF = "796459e8115c431e993f577c27992750"
KEY = "cpap_36e1306a273cfffb7594fdc1ee64889d01f6439e7223c9506a432414"
REQUEST_HASH = "efe791944feb94101e060b86d95edeef140d7a94c4bc2fc699a68178735e0023"
BACKGROUND = "uq9c0b-AooIedgo6"
UNKNOWN = "rcpt_9da35cd224ce47a2843d0a556a059589"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(value, code):
    if not value:
        raise ValueError(code)


def module():
    need(sha(CORRELATOR.read_bytes()) == CORRELATOR_SHA, "CORRELATOR_CHANGED")
    spec = importlib.util.spec_from_file_location("r13_source_job_correlation", CORRELATOR)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    return c


def decoded_summary(row):
    if row["summary_codec"] == "plain_json":
        raw = row["summary_json"].encode()
    else:
        need(row["summary_codec"] == "zlib_json" and isinstance(row["summary_blob"], bytes), "IDEMPOTENCY_CODEC_INVALID")
        decoder = zlib.decompressobj()
        raw = decoder.decompress(row["summary_blob"], 1048577)
        need(decoder.eof and len(raw) <= 1048576, "IDEMPOTENCY_SUMMARY_TOO_LARGE")
    value = json.loads(raw)
    need(isinstance(value, dict), "IDEMPOTENCY_SUMMARY_NOT_OBJECT")
    return value, sha(raw)


def collect(query_path, pins_path):
    c = module()
    query, query_sha = c.load(query_path)
    pins, pins_sha = c.load(pins_path)
    need(pins_sha == "e3b93a862fc0dd955f450c5f17bbe512232d52f8d8422f1ab587c9aad0af51f6", "ACTUAL_PINS_CHANGED")
    rows = query.get("public_receipts", [query])
    observed = [r for r in rows if r.get("ok") is True and r.get("action_id") == ACTION and r.get("task_id") == TASK]
    need(len(observed) == 1, "EXACT_SERVER_QUERY_REQUIRED")
    central = observed[0]
    need(central["delivery_state"] == "reconcile_required" and central["settled_at_ms"] is None
         and len(central["attempts"]) == 1 and not central["reconciliations"] and not central["dispatch_dispositions"], "CENTRAL_UNKNOWN_STATE_CHANGED")
    unknown = [r for r in central["receipts"] if r["receipt_id"] == UNKNOWN and r["receipt_state"] == "unknown"]
    need(len(unknown) == 1 and unknown[0]["diagnostic_code"] == "CONTROL_PLANE_APPROVED_PATCH_TIMEOUT", "EXACT_TIMEOUT_RECEIPT_REQUIRED")
    attempt = central["attempts"][0]["attempt_id"]
    need(sha((c.ROOT / c.TARGET).read_bytes()) == c.POST and sha((c.ROOT / c.CHECKER).read_bytes()) == c.CHECKER_SHA, "LIVE_POSTIMAGE_CHECKER_CHANGED")
    identity = c.source_identity(c.ROOT)
    journal, journal_sha = c.load(c.JOURNAL)
    entries = [r for r in journal["entries"].values() if r.get("action_id") == ACTION]
    need(len(entries) == 1 and entries[0].get("attempt_id") == attempt, "EXACT_JOURNAL_ATTEMPT_REQUIRED")
    entry = entries[0]
    receipt = entry.get("receipt", {})
    payload = receipt.get("payload", {})
    need(entry["state"] == receipt["receipt_state"] == "unknown" and receipt["receipt_submitted"] is True
         and receipt["action_id"] == ACTION and receipt["attempt_id"] == attempt
         and payload.get("code") == "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN"
         and payload.get("diagnostic_code") == "CONTROL_PLANE_APPROVED_PATCH_TIMEOUT", "EXACT_NATIVE_UNKNOWN_TIMEOUT_REQUIRED")
    with closing(sqlite3.connect(c.LEDGER.resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=10)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        records = db.execute("SELECT * FROM idempotency_records WHERE run_id=? AND operation='agent_workflow'", (RUN,)).fetchall()
        need(len(records) == 1, "EXACT_IDEMPOTENCY_RECORD_REQUIRED")
        record = dict(records[0])
        need(record["idempotency_key"] == KEY and record["request_hash"] == REQUEST_HASH
             and record["status"] == "completed" and record["process_instance_id"] == pins["runtime_instance_id"]
             and record["run_id"] == RUN and record["wave_id"] == WAVE and record["error_code"] == "", "IDEMPOTENCY_LINEAGE_CHANGED")
        summary, summary_sha = decoded_summary(record)
        proof = summary.get("initial_verification", {})
        need(summary.get("workflow") == "custom" and summary.get("phase") == "execute"
             and summary.get("execution_status") == "passed" and summary.get("execution_ok") is True
             and summary.get("orchestration_state") == "ACCEPTING"
             and summary.get("run_id") == RUN and summary.get("wave_id") == WAVE
             and summary.get("patch_effect") == {"applied": True, "affected_files": [{"operation": "update", "path": c.TARGET}]}
             and proof.get("command_id") == COMMAND and proof.get("job_id") == JOB and proof.get("proof_ids") == [PROOF]
             and proof.get("plan_sha256") == c.PLAN_SHA and proof.get("proof_status") == "passed"
             and proof.get("proof_fingerprint") == summary.get("proof_fingerprint"), "GENUINE_NATIVE_PATCH_PROOF_SUMMARY_REQUIRED")
        native_summary = {"run_id": RUN, "wave_id": WAVE, "initial_verification": proof}
        evidence = c.correlate_ledger(db, native_summary, pins, c.ROOT, identity)
        background = dict(db.execute("SELECT * FROM background_operations WHERE operation_id=?", (BACKGROUND,)).fetchone())
        bg_summary = json.loads(background["summary_json"])
        need(background["tool"] == "agent_workflow" and background["run_id"] == RUN and background["wave_id"] == WAVE
             and background["status"] == "completed" and bg_summary.get("worker_terminalized") is True, "BACKGROUND_TERMINAL_LINEAGE_REQUIRED")
        db.rollback()
    need(c.source_identity(c.ROOT) == identity and sha((c.ROOT / c.TARGET).read_bytes()) == c.POST, "SOURCE_CHANGED_DURING_CORRELATION")
    return {"ok": True, "kind": "r13_5h_after_effect_diagnostic_correlation", "observed_at_ms": int(time.time() * 1000),
            "action_id": ACTION, "task_id": TASK, "attempt_id": attempt, "unknown_receipt_id": UNKNOWN,
            "central_delivery_state": "reconcile_required", "central_action_settled": False,
            "query_receipt_sha256": query_sha, "pins_sha256": pins_sha, "journal_sha256": journal_sha,
            "unknown_payload_sha256": unknown[0]["payload_sha256"], "native_diagnostic_code": payload["diagnostic_code"],
            "source_head": c.HEAD, "source_worktree_fp": identity["worktree_fp"], "source_identity_current_matches_proof": True,
            "patch_applied": True, "target_postimage_sha256": c.POST, "checker_sha256": c.CHECKER_SHA,
            "native_identity": {"activation_epoch_id": pins["activation_epoch"], "process_instance_id": pins["runtime_instance_id"],
                                "server_instance_id": pins["mcp_server_instance_id"], "tool_contract_sha256": pins["native_tool_contract_sha256"]},
            "idempotency": {"key": KEY, "request_hash": REQUEST_HASH, "status": "completed", "summary_sha256": summary_sha,
                            "finished_at": record["finished_at"], "orchestration_state": summary["orchestration_state"]},
            "background": {"operation_id": BACKGROUND, "status": background["status"], "finished_at": background["finished_at"],
                           "row_sha256": sha(c.canonical(background)), "full_result_persisted": False},
            "correlation": evidence, "initial_verification": proof, "proof_status": "passed", "proof_exit_code": 0,
            "checker_4_of_4": "not_observed", "native_semantic_acceptance": "pending", "attestation_claimed": False,
            "strongest_proof": "applied_postimage_source_bound_exited_job_and_passed_initial_proof",
            "remaining_gaps": ["CENTRAL_RESULT_DELIVERY_TIMEOUT", "NATIVE_TAP_OUTPUT_NOT_CAPTURED", "NATIVE_SEMANTIC_ACCEPTANCE_PENDING"],
            "mutated_canonical_ledger": False, "external_mutation": False, "replay_forbidden": True,
            "raw_payload_disclosed": False, "raw_error_disclosed": False, "network_calls": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, type=Path)
    parser.add_argument("--pins", required=True, type=Path)
    args = parser.parse_args()
    result = collect(args.query, args.pins)
    destination = HERE / ("native-correlation-" + str(time.time_ns()) + ".json")
    raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    with destination.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"ok": True, "evidence_path": str(destination), "evidence_sha256": sha(raw),
                      "strongest_proof": result["strongest_proof"], "remaining_gaps": result["remaining_gaps"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        code = str(exc) if isinstance(exc, ValueError) and str(exc).replace("_", "").isalnum() and str(exc).isupper() else "SAFE_NATIVE_CORRELATION_FAILED"
        print(json.dumps({"ok": False, "code": code, "replay_forbidden": True, "mutated_canonical_ledger": False, "raw_error_disclosed": False}))
        raise SystemExit(2) from None
