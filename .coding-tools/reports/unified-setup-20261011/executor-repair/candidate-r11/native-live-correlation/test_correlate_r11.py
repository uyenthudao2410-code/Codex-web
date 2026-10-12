"""Offline fixtures; never open the real runtime ledger/journal or execute argv."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import correlate_r11 as c


class CorrelationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="r11-correlation-fixture-")
        self.root = Path(self.temporary.name)
        target = self.root / c.TARGET
        target.parent.mkdir(parents=True)
        target.write_bytes(b"fixture postimage")
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.addCleanup(self.temporary.cleanup)
        self.run, self.wave, self.proof = "1" * 32, "2" * 32, "3" * 32
        self.pins = {"requested_at_ms": 1000000, "expires_at_ms": 4600000, "runtime_instance_id": "native-r11"}
        self.identity = {"worktree_fp": "4" * 64}
        self.db.executescript("""
            CREATE TABLE runs(run_id TEXT PRIMARY KEY,status TEXT);
            CREATE TABLE waves(wave_id TEXT PRIMARY KEY,run_id TEXT,base_head TEXT,worktree_fp TEXT,contract_fp TEXT,execution_mode TEXT,status TEXT);
            CREATE TABLE checkpoints(run_id TEXT,status TEXT);
            CREATE TABLE managed_process_jobs(job_id TEXT,command_id TEXT,run_id TEXT,wave_id TEXT,owner TEXT,lifecycle_state TEXT,root_pid INTEGER,root_process_token TEXT,finished_at TEXT,process_instance_id TEXT,metadata_json TEXT);
            CREATE TABLE proofs(proof_id TEXT,run_id TEXT,wave_id TEXT,stage_id TEXT,stage_version TEXT,input_fingerprint TEXT,status TEXT,command_hash TEXT,finished_at TEXT,exit_code INTEGER,cache_hit INTEGER,upstream_json TEXT,metadata_json BLOB);
        """)
        self.db.execute("INSERT INTO runs VALUES(?,?)", (c.OLD_RUN, "running"))
        self.db.execute("INSERT INTO waves VALUES(?,?,?,?,?,?,?)", (c.OLD_WAVE, c.OLD_RUN, c.HEAD, "old-fp", "contract", "mcp_only", "AWAITING_ACCEPTANCE"))
        self.preserved = {name: c.sha(c.canonical(dict(self.db.execute("SELECT * FROM " + name).fetchone()), ascii=True)) for name in ("runs", "waves")}
        self.db.execute("INSERT INTO runs VALUES(?,?)", (self.run, "running"))
        self.db.execute("INSERT INTO waves VALUES(?,?,?,?,?,?,?)", (self.wave, self.run, c.HEAD, "pre-patch-fp", "contract", "mcp_only", "AWAITING_ACCEPTANCE"))
        command = "structured-argv:" + c.PLAN_SHA
        binding = {"schema_version": 1, "base_head": c.HEAD, "contract_fp": "contract", "paths": [c.TARGET], "path_fingerprint": c.path_fingerprint(self.root, [c.TARGET])}
        result = {"status": "passed", "ok": True, "exit_code": 0, "command_id": "new-command", "job_id": "new-job", "timed_out": False, "cancelled": False, "command": command, "effective_timeout_ms": 60000}
        meta = {"result": result, "proof_source_binding": binding, "initial_verification": c.PLAN, "plan_sha256": c.PLAN_SHA, "workdir": str(self.root), "authority_expires_at_ms": 4000000}
        input_fp = c.sha(c.canonical({"stage_id": "initial-verification:" + c.PLAN_SHA[:16], "stage_version": "1", "base_head": c.HEAD, "worktree_fp": self.identity["worktree_fp"], "contract_fp": "contract", "path_fp": binding["path_fingerprint"], "config": {"command_hash": c.sha(command.encode()), "workdir": str(self.root), "timeout_ms": 60000, "initial_verification": c.PLAN, "authority_expires_at_ms": 4000000}, "upstream_proof_ids": []}))
        self.db.execute("INSERT INTO proofs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (self.proof, self.run, self.wave, "initial-verification:" + c.PLAN_SHA[:16], "1", input_fp, "passed", c.sha(command.encode()), "2026-10-11T16:00:00Z", 0, 0, "[]", c.canonical(meta).decode()))
        self.db.execute("INSERT INTO managed_process_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?)", ("new-job", "new-command", self.run, self.wave, "default", "exited", 123, "start-token", "2026-10-11T16:00:00Z", "native-r11", c.canonical({"command_sha256": c.sha(" ".join(c.PLAN["argv"]).encode()), "exit_code": 0}).decode()))
        self.summary = {"run_id": self.run, "wave_id": self.wave, "initial_verification": {"command_id": "new-command", "job_id": "new-job", "proof_ids": [self.proof], "proof_fingerprint": c.sha((self.proof + ":" + input_fp).encode())}}
        self.db.commit()

    def correlate(self):
        self.db.execute("PRAGMA query_only=ON")
        self.db.execute("BEGIN")
        try:
            return c.correlate_ledger(self.db, self.summary, self.pins, self.root, self.identity, self.preserved)
        finally:
            self.db.rollback()

    def test_new_correlated_job_and_source_bound_proof(self):
        before = self.db.total_changes
        evidence = self.correlate()
        self.assertEqual(evidence["exit_code"], 0)
        self.assertTrue(evidence["old_pending_records_unchanged"])
        self.assertEqual(self.db.total_changes, before)
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute("UPDATE runs SET status='accepted'")

    def test_job_wrong_wave_rejected(self):
        self.db.execute("UPDATE managed_process_jobs SET wave_id=?", (c.OLD_WAVE,)); self.db.commit()
        with self.assertRaisesRegex(c.Rejected, "JOB_TERMINAL_LINEAGE_MISMATCH"):
            self.correlate()

    def test_old_pending_change_rejected(self):
        self.db.execute("UPDATE runs SET status='accepted' WHERE run_id=?", (c.OLD_RUN,)); self.db.commit()
        with self.assertRaisesRegex(c.Rejected, "OLD_PENDING_RECORD_CHANGED"):
            self.correlate()

    def test_source_input_drift_rejected(self):
        self.identity["worktree_fp"] = "5" * 64
        with self.assertRaisesRegex(c.Rejected, "PROOF_INPUT_FINGERPRINT_MISMATCH"):
            self.correlate()

    def test_aggregate_mismatch_rejected(self):
        self.summary["initial_verification"]["proof_fingerprint"] = "0" * 64
        with self.assertRaisesRegex(c.Rejected, "AGGREGATE_PROOF_FINGERPRINT_MISMATCH"):
            self.correlate()

    def test_exact_tap_output_and_wrong_command(self):
        content = "TAP version 13\n" + "\n".join("ok " + str(i) + " - " + name for i, name in enumerate(c.NAMES, 1)) + "\n1..4\n# tests 4\n# pass 4\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
        output = {"command_id": "new-command", "session_id": "new-command", "stream": "stdout", "stream_output_ref": "command:new-command:stdout", "ok": True, "requested_offset": 0, "offset": 0, "next_offset": None, "truncated": False, "omitted_bytes": 0, "stream_dropped_bytes": 0, "content": content, "total_stream_bytes": len(content.encode())}
        self.assertEqual(c.validate_output(output, self.summary)["checker_pass"], 4)
        output["command_id"] = "old-command"
        with self.assertRaisesRegex(c.Rejected, "OUTPUT_CAPTURE_INCOMPLETE_OR_WRONG_COMMAND"):
            c.validate_output(output, self.summary)

    def test_public_settled_receipt_and_submitted_native_journal(self):
        family = {"task_id": "task_" + "a" * 32, "action_id": "act_" + "b" * 32,
                  "request_id": "req_" + "c" * 32, "writer_lease_generation": 1,
                  "state": "settled", "settled": True, "attempt_ids": ["attempt_" + "d" * 32],
                  "receipt_states": ["accepted", "completed"]}
        self.summary["file"] = {"path": c.TARGET, "preimage_sha256": c.PRE, "postimage_sha256": c.POST, "bytes_written": 414}
        self.summary["initial_verification"].update(plan_sha256=c.PLAN_SHA, proof_status="passed")
        self.summary["response_sha256"] = c.sha(c.canonical({"file": self.summary["file"], "initial_verification": self.summary["initial_verification"]}))
        value = {"ok": True, "phase": "observe", "provenance": "central_mcp_service_trial", "family": family,
                 "verified_patch_and_initial_proof_summary": self.summary, "native_semantic_acceptance": "pending", "replay_forbidden": True}
        self.assertEqual(c.public_result(value), (family, self.summary))
        pins = {"activation_epoch": "epoch", "runtime_instance_id": "process", "mcp_server_instance_id": "server", "native_tool_contract_sha256": "a" * 64}
        identity = {"activation_epoch_id": "epoch", "process_instance_id": "process", "server_instance_id": "server", "tool_contract_sha256": "a" * 64}
        payload = {key: self.summary[key] for key in ("file", "initial_verification", "run_id", "wave_id", "response_sha256")}
        payload.update(schema_version=1, operation_kind="control_plane_approved_patch", patch_applied=True,
                       local_semantic_acceptance="pending", actor={"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"},
                       task_id=family["task_id"], writer_lease_generation=1, runtime_identity=identity)
        receipt = {"action_id": family["action_id"], "attempt_id": family["attempt_ids"][0], "receipt_state": "completed", "receipt_submitted": True, "payload": payload}
        entry = {"state": "completed", "action_id": family["action_id"], "attempt_id": family["attempt_ids"][0], "receipt": receipt}
        journal = {"schema_version": 1, "entries": {family["action_id"] + "|" + family["attempt_ids"][0]: entry}}
        self.assertEqual(c.correlate_journal(journal, family, self.summary, pins), identity)
        family["unapproved_raw_field"] = "must not enter public evidence"
        with self.assertRaisesRegex(c.Rejected, "ACTION_NOT_EXACT_SETTLED"):
            c.public_result(value)


if __name__ == "__main__":
    unittest.main()
