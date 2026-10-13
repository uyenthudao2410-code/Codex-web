"""Two-root shared MCP overlap canary; preparation alone performs no live work.

Imports the reviewed single-root canary's authority and receipt checks. Remote
stdin launch supplies the same module in memory. Original handles are recovered
from read-only SQLite after response loss; no lane is redispatched.
"""

import argparse
import base64
import importlib.util
import importlib
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace
import zlib

if "_BASE_CANARY" not in globals():
    spec = importlib.util.spec_from_file_location("reviewed_native_canary", Path(__file__).with_name("run-native-first-canary-timefix2.py"))
    _BASE_CANARY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_BASE_CANARY)
base = _BASE_CANARY
FIXTURE = "tests/fixtures/parallel-native-overlap-20261012"
LABELS = ("Codex-web", "Autocad")
LANES = {"read_probe": base.READ, "patch_probe": base.PATCH,
         "readback_probe": base.READ, "node_overlap": base.EXEC}
base.LANES.update(LANES)
COMMON_IDENTITIES = ("principal_id", "grant_id", "device_id", "activation_epoch", "process_instance_id", "server_instance_id")
COMMON_DIGESTS = ("local_tool_contract_sha256", "facade_contract_sha256", "serving_mcp_facade_sha256", "serving_node_agent_sha256", "serving_store_sha256")
TARGET_IDENTITIES = ("workspace_id", "workspace_generation", "binding_id", "pilot_decision_id")


def emit(phase, **fields):
    print(json.dumps({"operation": "parallel_native_overlap_canary", "phase": phase,
                      "observed_at_ms": int(time.time() * 1000), **fields}, separators=(",", ":")), flush=True)


def probe_content(label, patched=False):
    base.require(label in LABELS, "WORKSPACE_LABEL_INVALID")
    return f"PARALLEL_NATIVE_FIRST_V1\nworkspace={label}\nstage={'patched' if patched else 'seed'}\n"


def hold_source(label):
    base.require(label in LABELS, "WORKSPACE_LABEL_INVALID")
    return ("'use strict';\nconst assert = require('node:assert/strict');\n"
            "assert.equal(process.platform, 'win32');\n"
            f"const workspace = {json.dumps(label)};\n"
            "const started_at_ms = Date.now();\nconst clock = process.hrtime.bigint();\n"
            "setTimeout(() => {\n"
            "  const duration_ms = Number(process.hrtime.bigint() - clock) / 1e6;\n"
            "  console.log(JSON.stringify({marker:'PARALLEL_NATIVE_OVERLAP_V1',workspace,"
            "pid:process.pid,started_at_ms,finished_at_ms:Date.now(),duration_ms}));\n"
            "}, 5000);\n")


def fixture_files(label):
    return {FIXTURE + "/probe.txt": probe_content(label).encode(),
            FIXTURE + "/hold.cjs": hold_source(label).encode()}


def patch_envelope(label):
    before, after = probe_content(label).encode(), probe_content(label, True).encode()
    text = (f"*** Begin Patch\n*** Write Exact File: {FIXTURE}/probe.txt\n"
            f"@@ encoding=zlib-base64 preimage_sha256={base.sha(before)} postimage_sha256={base.sha(after)}\n"
            f"+{base64.b64encode(zlib.compress(after)).decode()}\n*** End Patch\n")
    return text, base.sha(before), base.sha(after)


def reviewed_targets(pins, credential_file, *, require_native_fixture=True):
    base.require(isinstance(pins, dict) and pins.get("schema_version") == 1, "PINS_SCHEMA_INVALID")
    for key in COMMON_IDENTITIES:
        base.require(isinstance(pins.get(key), str) and base.IDENTIFIER.fullmatch(pins[key]), "PINS_IDENTITY_INVALID")
    for key in COMMON_DIGESTS:
        base.require(isinstance(pins.get(key), str) and base.SHA.fullmatch(pins[key]), "PINS_DIGEST_INVALID")
    base.require(type(pins.get("service_pid")) is int and pins["service_pid"] > 1
                 and type(pins.get("facade_schema_version")) is int and pins["facade_schema_version"] >= 32,
                 "PINS_SERVICE_INVALID")
    entries = pins.get("targets")
    base.require(isinstance(entries, list) and len(entries) == 2
                 and {item.get("workspace_label") for item in entries if isinstance(item, dict)} == set(LABELS),
                 "EXACT_TWO_AUTHORIZED_TARGETS_REQUIRED")
    targets = []
    for value in sorted(entries, key=lambda item: LABELS.index(item["workspace_label"])):
        label = value["workspace_label"]
        for key in TARGET_IDENTITIES:
            base.require(isinstance(value.get(key), str) and base.IDENTIFIER.fullmatch(value[key]), "PINS_TARGET_INVALID")
        base.require(value.get("activation_verified") is True, "EXACT_READY_TARGET_REQUIRED")
        if require_native_fixture:
            base.require(value.get("native_fixture_explicitly_approved") is True, "EXACT_READY_NATIVE_FIXTURE_APPROVAL_REQUIRED")
            base.require(value.get("native_argv") == ["node", FIXTURE + "/hold.cjs"] and value.get("native_cwd") == ""
                         and value.get("native_source_sha256") == base.sha(hold_source(label).encode()),
                         "EXACT_NATIVE_FIXTURE_PIN_REQUIRED")
        else:
            base.require(pins.get("purpose") == "isolated-idle" and value.get("execution_mode") ==
                         ("isolated" if label == "Codex-web" else "native_first"), "EXACT_ISOLATED_IDLE_TARGET_REQUIRED")
        base.require(isinstance(value.get("exec_policy_sha256"), str) and base.SHA.fullmatch(value["exec_policy_sha256"]),
                     "EXACT_EXEC_POLICY_PIN_REQUIRED")
        retained = value.get("retained_unknown_actions", [])
        base.require(isinstance(retained, list) and len(set(retained)) == len(retained)
                     and all(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id) for action_id in retained)
                     and (len(retained) == 0 or (label == "Autocad" and len(retained) == 3)),
                     "EXACT_RETAINED_UNKNOWN_ALLOWLIST_REQUIRED")
        common = {key: pins[key] for key in (*COMMON_IDENTITIES, *COMMON_DIGESTS, "service_pid", "facade_schema_version")}
        targets.append(SimpleNamespace(**common, **{key: value[key] for key in TARGET_IDENTITIES},
                                       workspace_label=label, exec_policy_sha256=value["exec_policy_sha256"],
                                       retained_unknown_actions=retained, credential_file=credential_file))
    for key in ("workspace_id", "binding_id", "pilot_decision_id"):
        base.require(len({getattr(item, key) for item in targets}) == 2, "TARGET_SCOPES_NOT_DISTINCT")
    return targets


def canonical_quarantine_verifier(args):
    """Load only the serving, pinned store; skip Store construction and writes."""
    base.require(base.service_pid() == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
    environment = dict(item.split("=", 1) for item in Path(f"/proc/{args.service_pid}/environ").read_text().split("\0") if "=" in item)
    packages = {(Path(value).resolve() / "control_plane").resolve()
                for value in environment.get("PYTHONPATH", "").split(":")
                if value and (Path(value) / "control_plane/store.py").is_file()}
    base.require(len(packages) == 1, "SERVING_QUARANTINE_VERIFIER_NOT_UNIQUE")
    package = packages.pop()
    base.require(package.is_relative_to(Path.home().resolve())
                 and base.sha((package / "store.py").read_bytes()) == args.serving_store_sha256,
                 "SERVING_QUARANTINE_VERIFIER_PIN_CHANGED")
    sys.path.insert(0, str(package.parent))
    module = importlib.import_module("control_plane.store")
    base.require(Path(module.__file__).resolve() == package / "store.py", "SERVING_QUARANTINE_VERIFIER_PACKAGE_CHANGED")
    store = object.__new__(module.ControlPlaneStore)
    return store._quarantined_file_read_unknown_matches_pilot_target


def verify_existing_unsettled(args, connection):
    rows = connection.execute("SELECT * FROM actions WHERE device_id=? AND workspace_id=? AND workspace_generation=? AND settled_at_ms IS NULL",
                              (args.device_id, args.workspace_id, args.workspace_generation)).fetchall()
    retained = getattr(args, "retained_unknown_actions", [])
    base.require({row["action_id"] for row in rows} == set(retained), "CURRENT_TARGET_HAS_UNREVIEWED_UNSETTLED_ACTION")
    if not retained:
        return
    predicate = canonical_quarantine_verifier(args)
    now = int(time.time() * 1000)
    for action in rows:
        base.require(action["expires_at_ms"] <= now and action["settled_at_ms"] is None
                     and predicate(connection, action=action, owner_id="owner_default", principal_id=args.principal_id,
                                   binding_id=args.binding_id, workspace_id=args.workspace_id,
                                   workspace_generation=args.workspace_generation),
                     "RETAINED_UNKNOWN_QUARANTINE_NOT_EXACT")
    emit("historical_unknowns_verified_preserved", workspace_label=args.workspace_label, action_ids=sorted(retained),
         disposition="quarantined_unknown", declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT", settled=False, replayed=False)


class Session:
    def __init__(self, args, connection, client, attempt):
        self.args, self.connection, self.client = args, connection, client
        self.attempt = f"parallel-overlap-20261012:{attempt}:{args.workspace_label}"
        self.task_id = self.generation = self.contract = None
        self.actions, self.proofs = {}, {}
        self.owned = False

    def open(self):
        base.require(base.recover(self.connection, self.args.principal_id, self.attempt) == (None, {}),
                     "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        self.contract = base.check_target(self.args, self.connection, self.client)
        base.require(self.connection.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE binding_id=? AND closed_at_ms IS NULL",
                     (self.args.binding_id,)).fetchone()[0] == 0, "CURRENT_TARGET_HAS_OPEN_TASK")
        verify_existing_unsettled(self.args, self.connection)
        self.owned = True
        opened = self.client.call("workspace_context", {"operation": "task_open", "binding_id": self.args.binding_id,
            "label": "Two-root native overlap fixture", "idempotency_key": self.attempt + ":task"})
        self.task_id = opened.get("task", {}).get("task_id")
        base.require(isinstance(self.task_id, str) and re.fullmatch(r"task_[a-f0-9]{32}", self.task_id), "TASK_HANDLE_INVALID")
        lease = self.client.call("task_control", {"operation": "writer_claim", "task_id": self.task_id}).get("writer_lease", {})
        base.require(lease.get("state") == "held" and lease.get("task_id") == self.task_id
                     and lease.get("binding_id") == self.args.binding_id, "WRITER_LEASE_NOT_HELD")
        self.generation = lease["lease_generation"]
        emit("task_and_writer_held", workspace_label=self.args.workspace_label,
             task_id=self.task_id, writer_lease_generation=self.generation)

    def queue(self, lane, arguments):
        base.require(base.check_target(self.args, self.connection, self.client, self.task_id) == self.contract,
                     "FACADE_CONTRACT_CHANGED")
        base.renew(self.client, self.task_id, self.generation)
        base.require(lane not in base.recover(self.connection, self.args.principal_id, self.attempt)[1],
                     "LANE_ALREADY_USED_DO_NOT_REDISPATCH")
        queued = self.client.call(LANES[lane][1], {**arguments, "binding_id": self.args.binding_id,
            "task_id": self.task_id, "idempotency_key": self.attempt + ":" + lane,
            "expected_facade_contract": self.contract})
        action_id = queued.get("action_id")
        base.require(isinstance(action_id, str) and re.fullmatch(r"act_[a-f0-9]{32}", action_id), "ACTION_HANDLE_INVALID")
        base.require(queued.get("replayed") is False, "UNEXPECTED_REPLAY")
        self.actions[lane] = action_id
        emit("queued_original_action", workspace_label=self.args.workspace_label, lane=lane, action_id=action_id)
        return action_id

    def settle(self, lane):
        result = base.observe(self.client, lane, self.actions[lane], self.task_id, self.generation)
        base.require(result.get("action", {}).get("settled_at_ms") is not None and not base.unknown(result),
                     "ORIGINAL_ACTION_NOT_SETTLED")
        return result

    def read(self, lane, patched=False):
        path, expected = FIXTURE + "/probe.txt", probe_content(self.args.workspace_label, patched)
        self.queue(lane, {"operation": "read_file", "path": path, "start_line": 1, "max_lines": 20, "max_bytes": 4096})
        result = self.settle(lane)
        file = result.get("file_read", {}).get("file", {})
        base.require(result.get("execution") == "completed_file_read_relay" and result.get("file_accessed") is True
                     and file.get("path") == path and file.get("content") == expected and file.get("truncated") is False
                     and file.get("content_sha256") == base.sha(expected.encode())
                     and file.get("total_bytes") == len(expected.encode()) and file.get("bytes_read") == len(expected.encode()),
                     "EXACT_READ_NOT_VERIFIED")
        _, proof = base.receipt(self.connection, result, "file_read", self.args, self.contract, self.task_id, self.generation,
                               "electron-control-plane-file-read-bridge", "control_plane_bounded_file_read")
        self.proofs[lane] = {**proof, "path": path, "content_sha256": file["content_sha256"]}
        emit("read_verified", workspace_label=self.args.workspace_label, lane=lane, **self.proofs[lane])

    def patch(self):
        text, before, after = patch_envelope(self.args.workspace_label)
        self.queue("patch_probe", {"operation": "apply_patch", "path": FIXTURE + "/probe.txt", "preimage_sha256": before,
            "patch_sha256": base.sha(text.encode()), "validation_profile": "targeted", "patch_envelope": text})
        result = self.settle("patch_probe")
        payload, proof = base.receipt(self.connection, result, "patch", self.args, self.contract, self.task_id, self.generation,
                                     "electron-control-plane-approved-patch-bridge", "control_plane_approved_patch")
        base.require(result.get("patch_applied") is True and result.get("patch_effect_state") == "verified_applied"
                     and payload.get("file") == {"path": FIXTURE + "/probe.txt", "preimage_sha256": before,
                     "postimage_sha256": after, "bytes_written": len(probe_content(self.args.workspace_label, True).encode())}
                     and isinstance(payload.get("run_id"), str) and isinstance(payload.get("wave_id"), str) and payload.get("local_semantic_acceptance") == "pending",
                     "EXACT_PATCH_NOT_VERIFIED")
        self.proofs["patch_probe"] = {**proof, "postimage_sha256": after, "run_id": payload["run_id"], "wave_id": payload["wave_id"]}
        emit("patch_verified", workspace_label=self.args.workspace_label, **self.proofs["patch_probe"])

    def running_receipt(self):
        rows = self.connection.execute("SELECT receipt_id,received_at_ms,payload_json FROM receipts WHERE action_id=? AND receipt_state='accepted' ORDER BY received_at_ms",
                                       (self.actions["node_overlap"],)).fetchall()
        if not rows:
            return None
        base.require(len(rows) == 1, "RUNNING_RECEIPT_NOT_UNIQUE")
        row, expected = rows[0], self.args
        payload = json.loads(row["payload_json"])
        runtime = {"activation_epoch_id": expected.activation_epoch, "process_instance_id": expected.process_instance_id,
                   "server_instance_id": expected.server_instance_id, "tool_contract_sha256": expected.local_tool_contract_sha256}
        base.require(payload.get("status") == "running" and payload.get("runtime_identity") == runtime
                     and payload.get("facade_contract") == self.contract and payload.get("policy_sha256") == expected.exec_policy_sha256
                     and payload.get("task_id") == self.task_id and payload.get("writer_lease_generation") == self.generation
                     and payload.get("execution_backend") == "native" and payload.get("isolation_level") == "process_container"
                     and payload.get("policy_decision") == "native_explicit_approval", "RUNNING_RECEIPT_NOT_EXACT")
        base.require(re.fullmatch(r"cp_exec_[a-f0-9]{48}", str(payload.get("local_handle", "")))
                     and all(isinstance(payload.get(key), str) and re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.:-]{2,255}", payload[key])
                             for key in ("job_id", "command_id")), "RUNNING_JOB_HANDLE_INVALID")
        return {"receipt_id": row["receipt_id"], "accepted_at_ms": row["received_at_ms"],
                **{key: payload[key] for key in ("job_id", "command_id", "local_handle")}}

    def native_completion(self, running):
        result = self.settle("node_overlap")
        base.require(result.get("execution") == "completed_exec_relay" and result.get("process_state") == "completed"
                     and result.get("exit_code") == 0, "ORIGINAL_EXEC_NOT_VERIFIED_SUCCESS")
        payload, proof = base.receipt(self.connection, result, "exec", self.args, self.contract, self.task_id, self.generation,
                                     "electron-control-plane-exec-bridge", "control_plane_exec")
        base.require(payload.get("execution_backend") == "native" and payload.get("isolation_level") == "process_container"
                     and payload.get("policy_decision") == "native_explicit_approval"
                     and payload.get("policy_sha256") == self.args.exec_policy_sha256
                     and payload.get("status") == "exited" and payload.get("timed_out") is False
                     and payload.get("truncated") is False and payload.get("stderr") == ""
                     and all(payload.get(key) == running[key] for key in ("job_id", "command_id", "local_handle"))
                     and isinstance(payload.get("run_id"), str) and isinstance(payload.get("wave_id"), str), "NATIVE_TERMINAL_RECEIPT_NOT_EXACT")
        marker = json.loads(payload.get("stdout", ""))
        base.require(set(marker) == {"marker", "workspace", "pid", "started_at_ms", "finished_at_ms", "duration_ms"}
                     and marker["marker"] == "PARALLEL_NATIVE_OVERLAP_V1" and marker["workspace"] == self.args.workspace_label
                     and all(type(marker[key]) is int and marker[key] > 0 for key in ("pid", "started_at_ms", "finished_at_ms"))
                     and isinstance(marker["duration_ms"], (int, float)) and 4900 <= marker["duration_ms"] <= 30000
                     and marker["finished_at_ms"] - marker["started_at_ms"] >= 4900, "EXACT_HOLD_TIMESTAMPS_NOT_VERIFIED")
        self.proofs["node_overlap"] = {**proof, **running, **{key: marker[key] for key in ("pid", "started_at_ms", "finished_at_ms", "duration_ms")},
            "stdout_sha256": base.sha(payload["stdout"].encode()), "run_id": payload["run_id"], "wave_id": payload["wave_id"],
            "execution_backend": "native", "isolation_level": "process_container", "policy_decision": "native_explicit_approval"}
        emit("native_job_verified", workspace_label=self.args.workspace_label, **self.proofs["node_overlap"])
        return self.proofs["node_overlap"]

    def cleanup(self):
        outcome = {"workspace_label": self.args.workspace_label, "binding_id": self.args.binding_id,
                   "workspace_id": self.args.workspace_id, "workspace_generation": self.args.workspace_generation,
                   "proofs": self.proofs, "ok": True,
                   "retained_historical_unknown_actions": getattr(self.args, "retained_unknown_actions", [])}
        if self.owned:
            try:
                task, actions = base.recover(self.connection, self.args.principal_id, self.attempt)
                self.task_id = self.task_id or task
                self.actions.update(actions)
                if self.task_id and self.generation is None:
                    lease = self.connection.execute("SELECT lease_generation FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL",
                                                    (self.task_id,)).fetchall()
                    base.require(len(lease) <= 1, "ORIGINAL_WRITER_LEASE_AMBIGUOUS")
                    self.generation = lease[0]["lease_generation"] if lease else None
            except Exception as error:
                outcome.update(ok=False, handle_recovery_error=base.error_code(error))
        unresolved = []
        for lane, action_id in self.actions.items():
            try:
                _, tool, operation = LANES[lane]
                result = self.client.call(tool, {"operation": operation, "action_id": action_id})
                if result.get("action", {}).get("settled_at_ms") is None and not base.unknown(result) and self.task_id and self.generation:
                    if LANES[lane] == base.EXEC:
                        self.client.call("command_control", {"operation": "exec_stop", "action_id": action_id})
                    result = base.observe(self.client, lane, action_id, self.task_id, self.generation, seconds=120)
                outcome.setdefault("final_action_status", {})[lane] = base.summary(result)
                if result.get("action", {}).get("settled_at_ms") is None or base.unknown(result):
                    unresolved.append(lane)
            except Exception as error:
                outcome.setdefault("final_observation_errors", {})[lane] = base.error_code(error)
                unresolved.append(lane)
        outcome.update(task_id=self.task_id, writer_lease_generation=self.generation, action_ids=self.actions,
                       unresolved_original_actions=unresolved, requires_reconciliation=bool(unresolved))
        if self.task_id and not unresolved and "handle_recovery_error" not in outcome:
            for tool, operation, extra in (("task_control", "writer_release", {"reason": "parallel_overlap_canary_finished"}),
                                           ("workspace_context", "task_close", {})):
                try:
                    self.client.call(tool, {"operation": operation, "task_id": self.task_id, **extra})
                except Exception as error:
                    outcome.update(ok=False, **{operation + "_error": base.error_code(error)})
            task = self.connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (self.task_id,)).fetchone()
            held = self.connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (self.task_id,)).fetchone()[0]
            outcome.update(task_closed_verified=task is not None and task["closed_at_ms"] is not None, writer_released_verified=held == 0)
            outcome["ok"] = outcome["ok"] and outcome["task_closed_verified"] and held == 0
        elif self.task_id:
            outcome.update(ok=False, cleanup_deferred_pending_effect=True)
        return outcome


def verify_overlap(proofs):
    base.require(len(proofs) == 2 and len({value["job_id"] for value in proofs}) == 2
                 and len({value["command_id"] for value in proofs}) == 2 and len({value["pid"] for value in proofs}) == 2,
                 "ORIGINAL_NATIVE_JOBS_NOT_DISTINCT")
    start = max(value["started_at_ms"] for value in proofs)
    finish = min(value["finished_at_ms"] for value in proofs)
    base.require(finish > start, "NATIVE_JOB_INTERVALS_DO_NOT_OVERLAP")
    return {"overlap_started_at_ms": start, "overlap_finished_at_ms": finish, "overlap_duration_ms": finish - start,
            "clock_source": "same_windows_node_Date_now_correlated_with_hrtime_duration"}


def run(args, targets):
    port, connection = base.service_state(targets[0])
    sessions = []
    outcome = {"ok": False, "attempt_id": args.attempt_id, "service_pid": targets[0].service_pid,
               "reviewed_pins_sha256": args.reviewed_pins_sha256, "semantic_acceptance_performed": False,
               "fixture_preparation": "local_additive_seeds_separate_from_remote_effect_proof"}
    started = time.monotonic()
    try:
        token = base.credential(targets[0], connection)
        client = base.Mcp(port, token)
        sessions = [Session(target, connection, client, args.attempt_id) for target in targets]
        for session in sessions:
            session.open()
        base.require(len({session.task_id for session in sessions}) == 2, "TASK_HANDLES_NOT_DISTINCT")
        emit("wave_completed", wave="both_tasks_and_writer_leases_held")
        # The two lanes share one node but have independent writer leases.
        # Keep both leases alive while the other scope is being observed; the
        # original sequential loop let the first 60-second lease expire during
        # the second scope's file operations and then treated the resulting
        # generation renewal as a safety failure.
        def keepalive_all():
            for active in sessions:
                base.renew(client, active.task_id, active.generation)

        for lane in ("read_probe", "patch_probe", "readback_probe"):
            for session in sessions:
                keepalive_all()
                if lane == "read_probe":
                    session.read(lane)
                elif lane == "patch_probe":
                    session.patch()
                else:
                    session.read(lane, patched=True)
        emit("wave_completed", wave="two_root_reads_guarded_patches_readbacks", action_count=6)
        for session in sessions:
            session.queue("node_overlap", {"operation": "exec_run", "argv": ["node", FIXTURE + "/hold.cjs"], "cwd": "",
                                           "timeout_ms": 30000, "max_output_bytes": 4096})
        deadline, running = time.monotonic() + 45, None
        while time.monotonic() < deadline:
            running = [session.running_receipt() for session in sessions]
            if all(running):
                break
            for session in sessions:
                base.renew(client, session.task_id, session.generation)
                status = client.call("exec_command", {"operation": "exec_status", "action_id": session.actions["node_overlap"]})
                base.require(not base.unknown(status), "ORIGINAL_NATIVE_ACTION_UNKNOWN")
                if status.get("action", {}).get("settled_at_ms") is not None and not session.running_receipt():
                    raise RuntimeError("NATIVE_JOB_RUNNING_HANDLE_NOT_OBSERVED")
            time.sleep(0.2)
        base.require(running and all(running), "TWO_RUNNING_NATIVE_HANDLES_NOT_OBSERVED")
        emit("both_running_handles_observed", jobs=[{"workspace_label": session.args.workspace_label, **value}
                                                   for session, value in zip(sessions, running)])
        # Recreate only the HTTP observation client. Original actions, leases,
        # running handles and actor/runtime/contract pins remain authoritative.
        client = base.Mcp(port, token)
        for session in sessions:
            session.client = client
            base.require(base.check_target(session.args, connection, client, session.task_id) == session.contract,
                         "RECONNECTED_TARGET_OR_CONTRACT_CHANGED")
        outcome["observation_client_recreated"] = True
        outcome["reconnect_scope"] = "client_transport_only"
        emit("observation_client_reconnected", original_action_ids=[session.actions["node_overlap"] for session in sessions],
             scope="client_transport_only", runtime_restart_performed=False, native_job_redispatched=False)
        proofs = [session.native_completion(value) for session, value in zip(sessions, running)]
        for session in sessions:
            prefix = session.attempt + ":"
            intents = connection.execute("SELECT action_id FROM mcp_exec_intents WHERE principal_id=? AND substr(idempotency_key,1,?)=?",
                                         (session.args.principal_id, len(prefix), prefix)).fetchall()
            base.require(len(intents) == 1 and intents[0]["action_id"] == session.actions["node_overlap"],
                         "SECOND_EXEC_INTENT_DETECTED_AFTER_RECONNECT")
        outcome["no_second_exec_verified"] = True
        outcome["overlap"] = verify_overlap(proofs)
        outcome["ok"] = True
        emit("wave_completed", wave="two_native_job_intervals_overlap", **outcome["overlap"])
    except Exception as error:
        outcome["error_code"] = base.error_code(error)
    finally:
        cleanups = []
        for session in sessions:
            try:
                cleanups.append(session.cleanup())
            except Exception as error:
                cleanups.append({"workspace_label": session.args.workspace_label, "ok": False,
                                 "cleanup_error": base.error_code(error), "requires_reconciliation": True,
                                 "task_id": session.task_id, "action_ids": session.actions})
        outcome["targets"] = cleanups
        outcome["ok"] = outcome["ok"] and len(cleanups) == 2 and all(item["ok"] for item in cleanups)
        outcome["elapsed_seconds"] = round(time.monotonic() - started, 3)
        connection.close()
        emit("final", **outcome)
    return 0 if outcome["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-pins")
    parser.add_argument("--reviewed-pins-sha256", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--credential-file", required=True)
    parser.add_argument("--execute-confirmed-ready-two-root-canary", action="store_true", required=True)
    args = parser.parse_args()
    base.require(base.SHA.fullmatch(args.reviewed_pins_sha256) and re.fullmatch(r"[a-f0-9]{32}", args.attempt_id), "CANARY_ARGUMENT_INVALID")
    if "_REVIEWED_PINS_BYTES" in globals():
        raw = _REVIEWED_PINS_BYTES
    else:
        path = Path(args.reviewed_pins or "")
        base.require(path.is_absolute() and path.is_file() and path.stat().st_size <= 32768, "REVIEWED_PINS_PATH_INVALID")
        raw = path.read_bytes()
    base.require(len(raw) <= 32768 and base.sha(raw) == args.reviewed_pins_sha256, "REVIEWED_PINS_CHANGED")
    return run(args, reviewed_targets(json.loads(raw.decode("utf-8-sig")), args.credential_file))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("preflight_failed", ok=False, error_code=base.error_code(error))
        sys.exit(1)
