"""Observe one original native rejection; append FAILED only after plan review.

Default mode is read-only apart from a new content-free evidence file. Execution
uses the existing protected node credential and receipt API exactly once. It
never invokes a workflow, polls delivery, edits a journal, or writes a database.
The failure conclusion comes from the original native guard/audit and exact
source order. Unchanged bytes are corroboration, not the source of the outcome.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(r"E:\DEV\Codex-web")
REPORTS = ROOT / ".coding-tools/reports/shared-write-exec-20261012"
CANDIDATE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-machine-write-exec-1012-r5b/win-unpacked"
PROFILE = Path(os.environ.get("APPDATA", "")) / "web-mcp-assistant"
HEAD = "7999c4151cb501db86f2e4d0a2275d33fc248324"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
PILOT = "pilot_dfb3174078d842299c41c6638830e505"
ACTION = "act_051f354f679c45779fc32dab793e43c6"
ATTEMPT = "try_764317ee30904d34ab41452a7c25bfb7"
TASK = "task_44cc616e4b8b4180b046974651f52557"
UNKNOWN = "rcpt_8816464bf6db4589a0e58316c5fee19f"
RUN = "4ea601f3f7154ecda879a6986a5d7f41"
WAVE = "2b840f59702f4d4ba34e2b3f96496ab5"
EPOCH = "activation-mv4r64ul-235cac58cc9592bd08ffc95abe94a111"
PROCESS = "ev_bVSX46CWc8WG5"
SERVER = "XobFwIqZETgu9SLo"
CONTRACT = "0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"
POLICY_SHA = "7c91e5868f2b6e65b38cd3a3663f5de802a8fba4fc82224fd9d71a3e6eea02b6"
PREIMAGE = "b3084c24820d66e71ac91588ae169f283969a26d7630551cb0d098f4592931ce"
TARGET = ".coding-tools/reports/shared-write-exec-20261012/shared-write-proof.txt"
NATIVE_IDEM = "cpap_0320d9d467b0c0fb72a721709786f60b613d4dd78df3c74d67d3fb21"
NATIVE_CONTEXT = "cpap_ec84998048093669b0a8114dac0226e058016266b284122236d94156"
OBSERVATION_SHA = "9db05b3d40f9bfb39cf99ee1726ba138cb4d530422fc201ac4dc1c468931e944"
RESOURCE_SHA = "9945acc95e5c6527e2693b40cde4d118c35144660bba205848dc6f075b94d1e2"
OBSERVER_SHA = "8dcc69a9afc8c151ab5dee9dae9107b8defd29523d0afe3330e66f1e23cc10bc"
PACKAGE_HASHES = {
    "resources/app.asar": "3e5b87823089d08058620fdda56e3c410e92387c258add1ec2beeae6e4c771ba",
    "Coding Tools MCP.exe": "960adeec5aebad36374f556718d738ca50482540f427bf62cbc3178fe4078f5f",
    "resources/resources/control-plane/node_agent.py": "bc28e81636d4d1edb35fcfd4b05e905241f4f63ba18ceac38e8c9043cce56840",
    "resources/resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py": "6b75a3b4e7785b5fd5740140a5cd3bee95e31703dbe733124b5d65c48e983ba9",
    "resources/resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py": "b2df54b2450237cfff50b9662a5746704855fda8708a7076ea606a43e0b36ebb",
}


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def readonly(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    return connection


def server_snapshot():
    # SSH runs only this read-only snapshot; no DB writer/store is instantiated.
    script = r'''
import json, sqlite3, subprocess
from pathlib import Path
pid=int(subprocess.check_output(['systemctl','--user','show','codex-control-plane.service','--property=MainPID','--value'],text=True))
environment=dict(item.split('=',1) for item in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in item)
c=sqlite3.connect(Path(environment['CONTROL_PLANE_DB']).resolve().as_uri()+'?mode=ro',uri=True)
c.row_factory=sqlite3.Row
c.execute('PRAGMA query_only=ON'); c.execute('BEGIN')
def one(sql, parameters):
 row=c.execute(sql,parameters).fetchone()
 return dict(row) if row is not None else None
action=one('SELECT * FROM actions WHERE action_id=?',('__ACTION__',))
intent=one('SELECT * FROM mcp_standing_patch_intents WHERE action_id=?',('__ACTION__',))
result={'service_pid':pid,'action':action,'intent':intent,
 'attempts':[dict(r) for r in c.execute('SELECT * FROM delivery_attempts WHERE action_id=?',('__ACTION__',))],
 'receipts':[dict(r) for r in c.execute('SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms,receipt_id',('__ACTION__',))],
 'task':one('SELECT task_id,principal_id,binding_id,workspace_id,workspace_generation,closed_at_ms,expires_at_ms FROM mcp_task_sessions WHERE task_id=?',('__TASK__',)),
 'writer':one('SELECT task_id,binding_id,lease_generation,released_at_ms FROM mcp_task_writer_leases WHERE task_id=?',('__TASK__',)),
 'node':one('SELECT device_id,readiness,runtime_instance_id,mcp_server_instance_id,activation_epoch,last_seen_at_ms FROM nodes WHERE device_id=?',('__DEVICE__',)),
 'pilot':one('SELECT decision_id,principal_id,binding_id,device_id,workspace_id,workspace_generation,expires_at_ms,revoked_at_ms FROM scoped_pilot_decisions WHERE decision_id=?',('__PILOT__',)),
 'unsettled_generation_actions':c.execute('SELECT COUNT(*) FROM actions WHERE workspace_generation=? AND settled_at_ms IS NULL',('__GENERATION__',)).fetchone()[0],
 'open_generation_tasks':c.execute('SELECT COUNT(*) FROM mcp_task_sessions WHERE workspace_generation=? AND closed_at_ms IS NULL',('__GENERATION__',)).fetchone()[0],
 'serving_pythonpath':environment.get('PYTHONPATH'),
 'serving_store_sha256':__import__('hashlib').sha256(Path(environment['PYTHONPATH']).joinpath('control_plane/store.py').read_bytes()).hexdigest()}
c.close()
print(json.dumps(result,separators=(',',':')))
'''
    for key, value in {"ACTION": ACTION, "TASK": TASK, "DEVICE": DEVICE,
                       "PILOT": PILOT, "GENERATION": GENERATION}.items():
        script = script.replace("__" + key + "__", value)
    result = subprocess.run(["ssh.exe", "-T", "-o", "BatchMode=yes", "-o",
                             "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes",
                             "svhome@100.116.112.22", "python3", "-"],
                            input=script, text=True, encoding="utf-8", capture_output=True,
                            timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(result.returncode == 0, "READONLY_SERVER_OBSERVATION_FAILED")
    require(len(result.stdout) <= 196608, "SERVER_OBSERVATION_TOO_LARGE")
    return json.loads(result.stdout)


def validate_server(snapshot, *, settled_payload=None):
    now = int(time.time() * 1000)
    require(snapshot["service_pid"] == 921509
            and snapshot["serving_pythonpath"] == "/home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-9cae1044-scoped-artifacts-94b96e1b0fe2/control-plane"
            and snapshot["serving_store_sha256"] == "94b96e1b0fe2aa82410a9cba556761a9ea525b835d689d1dc88bd1d02f1f3472",
            "EXACT_REVIEWED_SERVING_STORE_CHANGED")
    a, intent = snapshot["action"], snapshot["intent"]
    require(a and intent and a["action_id"] == ACTION and a["device_id"] == DEVICE
            and a["workspace_id"] == WORKSPACE and a["workspace_generation"] == GENERATION
            and a["binding_id"] == BINDING and a["tool_name"] == "agent_workflow"
            and a["writer_lease_generation"] == 1 and a["scoped_pilot_decision_id"] == PILOT,
            "ORIGINAL_ACTION_IDENTITY_CHANGED")
    require(intent["task_id"] == TASK and intent["writer_lease_generation"] == 1
            and intent["relative_path"] == TARGET and intent["preimage_sha256"] == PREIMAGE
            and intent["authority_mode"] == "standing" and intent["verification_json"] is None,
            "ORIGINAL_SEALED_PATCH_CHANGED")
    require(hashlib.sha256(intent["patch_envelope"].encode()).hexdigest() == intent["patch_sha256"],
            "ORIGINAL_ENVELOPE_HASH_MISMATCH")
    attempts = snapshot["attempts"]
    require(len(attempts) == 1 and attempts[0]["attempt_id"] == ATTEMPT
            and attempts[0]["action_id"] == ACTION, "ORIGINAL_DELIVERY_ATTEMPT_CHANGED")
    receipts = snapshot["receipts"]
    unknown = [r for r in receipts if r["receipt_id"] == UNKNOWN]
    require(len(unknown) == 1 and unknown[0]["receipt_state"] == "unknown"
            and unknown[0]["local_handle"] == ""
            and json.loads(unknown[0]["payload_json"]) == {
                "schema_version": 1, "operation_kind": "control_plane_approved_patch",
                "code": "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_APPROVED_PATCH_MCP_REJECTED"},
            "ORIGINAL_UNKNOWN_RECEIPT_CHANGED")
    task, writer, node, pilot = (snapshot[key] for key in ("task", "writer", "node", "pilot"))
    require(task and writer and task["closed_at_ms"] is None and writer["released_at_ms"] is None
            and writer["lease_generation"] == 1 and task["binding_id"] == BINDING
            and task["workspace_id"] == WORKSPACE and task["workspace_generation"] == GENERATION,
            "ORIGINAL_CENTRAL_TASK_AUTHORITY_CHANGED")
    require(node and node["readiness"] == "ready" and node["runtime_instance_id"] == PROCESS
            and node["mcp_server_instance_id"] == SERVER and node["activation_epoch"] == EPOCH
            and 0 <= now - node["last_seen_at_ms"] <= 30000, "EXACT_R5_NODE_NOT_CURRENT_READY")
    require(pilot and pilot["binding_id"] == BINDING and pilot["device_id"] == DEVICE
            and pilot["workspace_id"] == WORKSPACE and pilot["workspace_generation"] == GENERATION
            and pilot["revoked_at_ms"] is None and pilot["expires_at_ms"] > now + 60000
            and pilot["principal_id"] == task["principal_id"], "CURRENT_PILOT_CHANGED")
    require(snapshot["open_generation_tasks"] == 1, "OTHER_OPEN_TASK_PRESENT")
    if settled_payload is None:
        require(a["delivery_state"] == "reconcile_required" and a["settled_at_ms"] is None
                and len(receipts) == 1 and snapshot["unsettled_generation_actions"] == 1,
                "ORIGINAL_UNKNOWN_NOT_EXCLUSIVE_UNSETTLED_ACTION")
    else:
        terminal = [r for r in receipts if r["receipt_state"] == "failed"]
        require(a["delivery_state"] == "settled" and a["settled_at_ms"] is not None
                and len(receipts) == 2 and len(terminal) == 1
                and terminal[0]["local_handle"] == ""
                and json.loads(terminal[0]["payload_json"]) == settled_payload
                and snapshot["unsettled_generation_actions"] == 0,
                "TERMINAL_FAILED_RECEIPT_NOT_VERIFIED")
    return unknown[0]


def native_observation(snapshot):
    evidence_path = REPORTS / "original-patch-native-failure-observation.json"
    require(file_sha(evidence_path) == OBSERVATION_SHA, "REVIEWED_NATIVE_OBSERVATION_CHANGED")
    require(file_sha(REPORTS / "original-patch-resource-census.json") == RESOURCE_SHA,
            "REVIEWED_NATIVE_RESOURCE_CENSUS_CHANGED")
    evidence = read_json(evidence_path)
    policy_path = PROFILE / "control-plane-approved-patch-policy.json"
    policy = read_json(policy_path)
    require(policy.get("enabled") is True
            and digest({k: v for k, v in policy.items() if k != "enabled"}) == POLICY_SHA,
            "ORIGINAL_ADMITTED_POLICY_CHANGED")
    intent = snapshot["intent"]
    contract = {"schema_version": intent["facade_schema_version"],
                "profile": intent["facade_profile"], "sha256": intent["facade_contract_sha256"]}
    common = {"action_id": ACTION, "attempt_id": ATTEMPT, "task_id": TASK,
              "writer_lease_generation": 1, "facade_contract": contract}
    context = "cpap_" + digest({**common, "policy_sha256": POLICY_SHA,
                                "workspace_id": WORKSPACE, "workspace_generation": GENERATION})[:56]
    idem = "cpap_" + digest({**common, "patch_sha256": intent["patch_sha256"]})[:56]
    require(context == NATIVE_CONTEXT and idem == NATIVE_IDEM
            and evidence["native_context_id"] == context
            and evidence["native_idempotency"]["idempotency_key"] == idem,
            "NATIVE_ACTION_POLICY_FINGERPRINT_MISMATCH")
    scoped_path = ROOT / evidence["native_context_projection_path"]
    require(scoped_path.name == hashlib.sha256(("mcp2026:" + context).encode()).hexdigest()[:24] + ".json",
            "NATIVE_CONTEXT_PROJECTION_PATH_MISMATCH")
    scoped = read_json(scoped_path)
    orchestration = scoped["orchestration"]
    require(orchestration["run_id"] == RUN and orchestration["wave_id"] == WAVE
            and orchestration["orchestration_state"] == "REPLAN"
            and orchestration["write_owner"] == "" and orchestration["write_lease_id"] == ""
            and scoped["modified_files"] == [] and scoped["current_command"] is None,
            "NATIVE_SCOPE_NOT_QUIESCENT_REPLAN")
    with readonly(ROOT / ".coding-tools/orchestration/ledger.sqlite3") as c:
        native = dict(c.execute("SELECT * FROM idempotency_records WHERE idempotency_key=?", (idem,)).fetchone())
        require(native["operation"] == "agent_workflow" and native["status"] == "unknown"
                and native["error_code"] == "PROTECTED_PATH_WRITE"
                and native["workflow_patch_preflight"] == 0
                and native["process_instance_id"] == PROCESS,
                "EXACT_NATIVE_GUARD_REJECTION_MISSING")
        rows = [dict(r) for r in c.execute("SELECT * FROM events WHERE run_id=? ORDER BY seq", (RUN,))]
        require(len(rows) == 14 and len(rows) == len(evidence["events"]), "ORIGINAL_RUN_AUDIT_CHANGED")
        for row, recorded in zip(rows, evidence["events"]):
            require(row["wave_id"] == WAVE
                    and all(row[k] == recorded[k] for k in ("seq", "event_id", "event_type", "state_before",
                                                           "state_after", "event_time", "event_hash"))
                    and hashlib.sha256(row["payload_json"].encode()).hexdigest() == recorded["payload_sha256"],
                    "CANONICAL_ORIGINAL_AUDIT_DIFFERS_FROM_REVIEWED_EVIDENCE")
        audit = [{k: r[k] for k in ("seq", "event_id", "event_type", "event_hash")} for r in rows]
        acquire = next(r for r in rows if r["event_type"] == "write_lease_acquired")
        revoke = next(r for r in rows if r["event_type"] == "write_lease_revoked")
        granted, revoked = json.loads(acquire["payload_json"]), json.loads(revoke["payload_json"])
        require(granted["lease_id"] == revoked["lease_id"] and revoked["lease_state"] == "released"
                and revoked["reason"] == "state_transition:replan"
                and granted["allowed_paths"] == [TARGET]
                and ".coding-tools" in granted["protected_paths"], "ORIGINAL_NATIVE_LEASE_NOT_REVOKED")
        fences = c.execute("SELECT lease_id,wave_id,status FROM write_fences WHERE run_id=?", (RUN,)).fetchall()
        require(len(fences) == 1 and fences[0]["lease_id"] == revoked["lease_id"]
                and fences[0]["wave_id"] == WAVE and fences[0]["status"] == "released",
                "ORIGINAL_NATIVE_WRITE_FENCE_NOT_RELEASED")
        replan = next(r for r in rows if r["event_type"] == "state_transition" and r["state_after"] == "REPLAN")
        require(json.loads(replan["payload_json"])["reason"] == "PROTECTED_PATH_WRITE",
                "ORIGINAL_REPLAN_REASON_NOT_EXACT_GUARD_FAILURE")
        quiet = json.loads(rows[-1]["payload_json"])
        require(rows[-1]["event_type"] == "wave_processes_quiesced" and quiet["quiescent"] is True
                and quiet["active_command_count"] == 0 and quiet["terminated"] == 0
                and quiet["run_id"] == RUN and quiet["wave_id"] == WAVE,
                "ORIGINAL_WAVE_NOT_QUIESCED")
        run = c.execute("SELECT task_id FROM runs WHERE run_id=?", (RUN,)).fetchone()
        wave = c.execute("SELECT run_id,base_head,worktree_fp,contract_fp FROM waves WHERE wave_id=?", (WAVE,)).fetchone()
        require(run["task_id"] == scoped["task_id"] and wave["run_id"] == RUN
                and wave["base_head"] == HEAD
                and wave["worktree_fp"] == orchestration["worktree_fp"]
                and wave["contract_fp"] == orchestration["contract_fp"], "ORIGINAL_RUN_WAVE_LINEAGE_CHANGED")
        for table in ("managed_process_jobs", "controller_leases", "proofs", "agent_lanes"):
            require(c.execute("SELECT COUNT(*) FROM " + table + " WHERE run_id=?", (RUN,)).fetchone()[0] == 0,
                    "ORIGINAL_NATIVE_RUN_HAS_OWNED_RESOURCE_" + table.upper())
        background = c.execute("SELECT wave_id,status,finished_at FROM background_operations WHERE run_id=?", (RUN,)).fetchall()
        require(len(background) == 1 and background[0]["wave_id"] == WAVE
                and background[0]["status"] == "completed" and bool(background[0]["finished_at"]),
                "ORIGINAL_BACKGROUND_OPERATION_NOT_COMPLETED")
    require((ROOT / TARGET).stat().st_size == 62 and file_sha(ROOT / TARGET) == PREIMAGE,
            "ORIGINAL_TARGET_PREIMAGE_CHANGED")
    # These exact reviewed packaged source hashes prove guard-before-mutation
    # ordering for the typed error above. No outcome is inferred from bytes alone.
    return {"native_context_id": context, "native_idempotency_key": idem,
            "native_error_code": native["error_code"], "native_process_instance_id": native["process_instance_id"],
            "native_audit_sha256": digest(audit), "native_observation_sha256": OBSERVATION_SHA,
            "native_resource_census_sha256": RESOURCE_SHA, "native_scope_sha256": file_sha(scoped_path),
            "policy_sha256": POLICY_SHA, "patch_sha256": intent["patch_sha256"],
            "preimage_sha256": PREIMAGE, "native_write_lease_id": revoked["lease_id"],
            "run_id": RUN, "wave_id": WAVE, "effect_classification": "native_guard_rejected_before_apply_changes_and_verify"}


def package_and_runtime():
    require(Path.cwd().resolve() == ROOT and subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip() == HEAD, "EXACT_WORKSPACE_HEAD_REQUIRED")
    for name, expected in PACKAGE_HASHES.items():
        require(file_sha(CANDIDATE / name) == expected, "EXACT_R5_PACKAGE_CHANGED")
    observer = REPORTS / "observe-r5-machine.cjs"
    require(file_sha(observer) == OBSERVER_SHA, "REVIEWED_READONLY_RUNTIME_OBSERVER_CHANGED")
    environment = {**os.environ, "ELECTRON_RUN_AS_NODE": "1"}
    result = subprocess.run([str(CANDIDATE / "Coding Tools MCP.exe"), str(observer), str(CANDIDATE), EPOCH],
                            env=environment, capture_output=True, text=True, encoding="utf-8", timeout=50,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(result.returncode == 0, "FRESH_EXACT_R5_RUNTIME_OBSERVATION_FAILED")
    lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
    observation = json.loads(lines[-1])
    require(observation["ok"] is True and observation["ledger_idle"] is True
            and observation["epoch"]["activation_epoch_id"] == EPOCH
            and observation["runtime"]["toolContract"]["sha256"] == CONTRACT
            and observation["host"]["pid"] == 31528
            and observation["host"]["instance_id"] == "6452779ae83ab14a0b3711590ca63274"
            and observation["native_os_observation"]["live_process_count"] == 0,
            "FRESH_EXACT_R5_RUNTIME_OR_RESOURCES_CHANGED")
    return {"runtime_report_path": observation["report_path"], "runtime_report_sha256": file_sha(Path(observation["report_path"])),
            "activation_epoch": EPOCH, "process_instance_id": PROCESS, "server_instance_id": SERVER,
            "contract_sha256": CONTRACT, "package_hashes": PACKAGE_HASHES}


def protected_local_state():
    require(PROFILE.is_absolute(), "EXACT_PROTECTED_PROFILE_REQUIRED")
    config_path = PROFILE / "control-plane-node.json"
    config = read_json(config_path)
    require(config["device_id"] == DEVICE and config["server_url"] == "https://svhome.tail0e4032.ts.net"
            and config.get("node_secret") in (None, "") and bool(config.get("node_secret_dpapi"))
            and config.get("node_secret_pending") in (None, ""), "PROTECTED_NODE_CONFIG_REQUIRED_NO_MIGRATION")
    journal_path = PROFILE / "control-plane-node.json.approved-patch-bridge-journal.json"
    journal = read_json(journal_path)
    entry = journal["entries"][ACTION + "|" + ATTEMPT]
    require(entry["state"] == "unknown" and entry["action_id"] == ACTION and entry["attempt_id"] == ATTEMPT
            and entry["receipt"]["receipt_state"] == "unknown"
            and entry["receipt"]["receipt_submitted"] is True
            and entry["receipt"]["local_handle"] == ""
            and entry["receipt"]["payload"]["diagnostic_code"] == "CONTROL_PLANE_APPROVED_PATCH_MCP_REJECTED",
            "ORIGINAL_PROTECTED_NODE_JOURNAL_CHANGED")
    return {"node_config_sha256": file_sha(config_path), "node_journal_sha256": file_sha(journal_path)}


def receipt_payload(native, protected, unknown):
    return {"schema_version": 1, "operation_kind": "control_plane_approved_patch",
            "code": "PROTECTED_PATH_WRITE", "failure_category": "native_policy_rejection",
            "diagnostic_code": "ORIGINAL_NATIVE_GUARD_FAILURE_OBSERVED",
            "local_semantic_acceptance": False,
            "reconciliation": {"observer_kind": "authenticated_node_native_failure_observer",
                               "producer_sha256": file_sha(Path(__file__)),
                               "original_unknown_receipt_id": UNKNOWN,
                               "original_unknown_receipt_digest": unknown["receipt_digest"],
                               "original_action_id": ACTION, "original_attempt_id": ATTEMPT,
                               "activation_epoch": EPOCH, "local_contract_sha256": CONTRACT,
                               "package_hashes": PACKAGE_HASHES, **native, **protected}}


def write_new(path, report):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"operation": report["operation"], "ok": True, "report_path": str(path),
                      "report_sha256": file_sha(path), "receipt_submitted": report["receipt_submitted"]}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-reviewed-plan", type=Path)
    parser.add_argument("--reviewed-plan-sha256")
    args = parser.parse_args()
    require(bool(args.execute_reviewed_plan) == bool(args.reviewed_plan_sha256), "EXACT_REVIEWED_PLAN_AND_HASH_REQUIRED")
    reviewed = None
    if args.execute_reviewed_plan:
        require(args.execute_reviewed_plan.resolve().parent == REPORTS
                and file_sha(args.execute_reviewed_plan) == args.reviewed_plan_sha256,
                "REVIEWED_PLAN_HASH_CHANGED")
        reviewed = read_json(args.execute_reviewed_plan)
        require(reviewed["receipt_submitted"] is False
                and reviewed["producer_sha256"] == file_sha(Path(__file__))
                and 0 <= int(time.time() * 1000) - reviewed["observed_at_ms"] <= 900000,
                "REVIEWED_PLAN_NOT_CURRENT_OR_PRODUCER_CHANGED")
    runtime = package_and_runtime()
    protected = protected_local_state()
    snapshot = server_snapshot()
    unknown = validate_server(snapshot)
    native = native_observation(snapshot)
    payload = receipt_payload(native, protected, unknown)
    prepared = {"schema_version": 1, "operation": "prepare_observed_original_native_failure_reconciliation",
                "observed_at_ms": int(time.time() * 1000), "producer_sha256": file_sha(Path(__file__)),
                "receipt_submitted": False, "database_writer_instantiated": False, "node_journal_modified": False,
                "native_semantic_acceptance_performed": False, "original_action_replayed": False,
                "action_id": ACTION, "attempt_id": ATTEMPT, "receipt_state": "failed", "local_handle": "",
                "receipt_payload": payload, "receipt_payload_sha256": digest(payload), "runtime": runtime}
    if reviewed is None:
        return write_new(REPORTS / ("original-patch-failure-reconciliation-plan-" + str(prepared["observed_at_ms"]) + ".json"), prepared)
    require(reviewed["receipt_payload"] == payload and reviewed["receipt_payload_sha256"] == digest(payload),
            "REVIEWED_RECONCILIATION_EVIDENCE_CHANGED")
    # Recheck the decisive evidence immediately before the only mutation.
    final_before = server_snapshot()
    validate_server(final_before)
    native_again = native_observation(final_before)
    require(native_again == native and protected_local_state() == protected,
            "ORIGINAL_EVIDENCE_CHANGED_BEFORE_RECEIPT")
    packaged_agent = CANDIDATE / "resources/resources/control-plane/node_agent.py"
    spec = importlib.util.spec_from_file_location("exact_packaged_node_receipt_client", packaged_agent)
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)
    config = agent._config(PROFILE / "control-plane-node.json")
    require(protected_local_state() == protected, "NODE_CONFIG_CHANGED_WHILE_LOADING_DPAPI")
    entry = {"receipt": {"action_id": ACTION, "attempt_id": ATTEMPT, "receipt_state": "failed",
                         "local_handle": "", "payload": payload, "receipt_submitted": False}}
    response = agent._submit_receipt(config, entry)
    require(response.get("action_id") == ACTION and response.get("attempt_id") == ATTEMPT
            and response.get("receipt_state") == "failed" and response.get("delivery_state") == "settled",
            "FAILED_RECEIPT_RESPONSE_NOT_EXACT")
    after = server_snapshot()
    after_unknown = validate_server(after, settled_payload=payload)
    require(after_unknown == unknown and protected_local_state() == protected
            and native_observation(after) == native, "POST_RECEIPT_EVIDENCE_NOT_PRESERVED")
    prepared.update(operation="reconcile_observed_original_native_failure", receipt_submitted=True,
                    observed_at_ms=int(time.time() * 1000), reviewed_plan_sha256=args.reviewed_plan_sha256,
                    receipt_response=response, central_delivery_state="settled",
                    original_unknown_receipt_preserved=True, node_journal_preserved=True)
    write_new(REPORTS / ("original-patch-failure-reconciliation-receipt-" + str(prepared["observed_at_ms"]) + ".json"), prepared)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never print external response payloads, environment, config or tokens.
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation": "observe_or_reconcile_original_native_failure", "ok": False, "code": code}), file=sys.stderr)
        sys.exit(1)
