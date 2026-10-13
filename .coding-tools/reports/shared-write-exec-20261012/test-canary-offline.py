"""Offline controller tests: no network, repository write target or MCP effects."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("write_canary", Path(__file__).with_name("run-shared-write-exec-canary.py"))
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)
TASK = "task_" + "1" * 32
CONTRACT = {"schema_version": 32, "profile": "control-plane-private-tunnel-service-v1", "sha256": "a" * 64}


class Cursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Db:
    def __init__(self):
        self.task = None
        self.actions = {}
        self.closed = False
        self.released = False

    def execute(self, sql, parameters=()):
        if "SELECT closed_at_ms" in sql:
            return Cursor({"closed_at_ms": 123 if self.closed else None})
        if "mcp_task_writer_leases" in sql:
            return Cursor([0 if self.released else 1])
        return Cursor([0])

    def close(self):
        pass


class Client:
    def __init__(self, database, lost=None, unknown=None):
        self.database = database
        self.calls = []
        self.lost = lost
        self.unknown = unknown

    def call(self, tool, args):
        operation = args["operation"]
        self.calls.append((tool, args))
        if operation == "task_open":
            self.database.task = TASK
            if self.lost == "task":
                raise OSError("simulated lost reply")
            return {"task": {"task_id": TASK}}
        if operation == "writer_claim":
            return {"writer_lease": {"state": "held", "task_id": TASK, "binding_id": "bind_fixture", "lease_generation": 1}}
        if operation == "writer_release":
            self.database.released = True
            return {}
        if operation == "task_close":
            self.database.closed = True
            return {}
        if operation in {"doc_create", "read_file", "apply_patch", "exec_run"}:
            lane = args["idempotency_key"].split(":")[-1]
            action_id = "act_" + str(len(self.database.actions) + 1) * 32
            self.database.actions[lane] = action_id
            if self.lost == lane:
                raise OSError("simulated lost reply")
            return {"action_id": action_id, "replayed": False}
        if operation.endswith("status"):
            lane = next(lane for lane, action in self.database.actions.items() if action == args["action_id"])
            result = {"action": {"action_id": args["action_id"], "settled_at_ms": 123}}
            if lane == self.unknown:
                return {**result, "reconciliation_required": True, "process_state": "unknown"}
            if lane == "create":
                result.update(execution="completed_document_write_relay", document={})
            if lane in {"read_initial", "read_final"}:
                text = canary.INITIAL if lane == "read_initial" else canary.FINAL
                result.update(execution="completed_file_read_relay", file_accessed=True, file_read={"file": {
                    "path": canary.TARGET, "content": text, "content_sha256": canary.hashlib.sha256(text.encode()).hexdigest(),
                    "truncated": False, "total_bytes": len(text.encode()), "bytes_read": len(text.encode())}})
            if lane == "patch":
                result.update(patch_applied=True, patch_effect_state="verified_applied", patch={})
            if lane == "exec":
                result.update(execution="completed_exec_relay", process_state="completed", exit_code=0,
                              exec={"local_handle": "cp_exec_fixture"})
            return result
        if operation == "exec_output":
            return {"has_output": True, "exit_code": 0, "truncated": False, "total_bytes": 100,
                    "output": canary.MARKER + " sha256=" + canary.hashlib.sha256(canary.FINAL.encode()).hexdigest()}
        raise AssertionError((tool, args))


def receipt(_db, result, key, _args, _contract, _task, _lease, _actor, kind):
    payload = {}
    if key == "document":
        payload = {"target": canary.TARGET, "operation": "document_create", "result": {
            "sha256": canary.hashlib.sha256(canary.INITIAL.encode()).hexdigest(), "size": len(canary.INITIAL.encode())}}
    if key == "patch":
        payload = {"file": {"path": canary.TARGET, "preimage_sha256": canary.patch_envelope()[1],
                            "postimage_sha256": canary.patch_envelope()[2], "bytes_written": len(canary.FINAL.encode())},
                   "local_semantic_acceptance": "pending", "run_id": "run_fixture", "wave_id": "wave_fixture"}
    if key == "exec":
        payload = {"local_handle": "cp_exec_fixture", "job_id": "original_job", "command_id": "original_command"}
    return payload, {"receipt_id": "fixture_receipt", "action_id": result["action"]["action_id"]}


class ControllerTest(unittest.TestCase):
    def run_controller(self, lost=None, unknown=None, used=False):
        database = Db()
        if used:
            database.task = TASK
        client = Client(database, lost, unknown)
        argv = ["canary", "--binding-id", "bind_fixture", "--new-generation", "generation_" + "2" * 32,
                "--pilot-decision-id", "pilot_fixture", "--activation-epoch", "activation_fixture",
                "--process-instance-id", "process_fixture", "--server-instance-id", "server_fixture",
                "--local-tool-contract-sha256", "b" * 64, "--facade-contract-sha256", "a" * 64,
                "--facade-schema-version", "32", "--service-pid", "123", "--attempt-id", "3" * 32,
                "--credential-file", "/offline/never-read", "--execute-confirmed-ready-pilot"]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(canary, "service_state", return_value=(123, 8766, database)), \
                patch.object(canary, "service_state_pid", return_value=123), \
                patch.object(canary, "existing_credential", return_value="offline-fixture"), \
                patch.object(canary, "Mcp", return_value=client), \
                patch.object(canary, "check_target", return_value=CONTRACT), \
                patch.object(canary, "verified_receipt", side_effect=receipt), \
                patch.object(canary, "recover_handles", side_effect=lambda *_: (database.task, dict(database.actions))), \
                contextlib.redirect_stdout(output):
            code = canary.main()
        final = json.loads(output.getvalue().splitlines()[-1])
        return code, final, client, database

    def test_success_only_one_dispatch_per_lane_and_truthful_pending(self):
        code, result, client, _db = self.run_controller()
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        dispatch = [args["operation"] for _tool, args in client.calls if args["operation"] in {"doc_create", "read_file", "apply_patch", "exec_run"}]
        self.assertEqual(dispatch, ["doc_create", "read_file", "apply_patch", "read_file", "exec_run"])
        self.assertFalse(result["semantic_acceptance_performed"])
        self.assertEqual(result["proofs"]["patch"]["receipt"]["local_semantic_acceptance"], "pending")

    def test_lost_replies_recover_original_handles_without_replacement(self):
        for lane in ("task", "create", "exec"):
            with self.subTest(lane=lane):
                code, result, client, database = self.run_controller(lost=lane)
                self.assertEqual(code, 1)
                self.assertEqual(result["task_id"], TASK)
                self.assertTrue(database.closed)
                if lane != "task":
                    self.assertEqual(result["action_ids"][lane], database.actions[lane])
                self.assertLessEqual(sum(args["operation"] == "exec_run" for _tool, args in client.calls), 1)

    def test_settled_unknown_preserves_task_and_writer(self):
        code, result, _client, database = self.run_controller(unknown="create")
        self.assertEqual(code, 1)
        self.assertEqual(result["unresolved_original_actions"], ["create"])
        self.assertTrue(result["cleanup_deferred_pending_effect"])
        self.assertFalse(database.closed)
        self.assertFalse(database.released)

    def test_used_attempt_has_no_dispatch_or_cleanup_of_foreign_handles(self):
        code, result, client, database = self.run_controller(used=True)
        self.assertEqual(code, 1)
        self.assertEqual(result["error_code"], "ATTEMPT_ALREADY_USED_DO_NOT_REDISPATCH")
        self.assertEqual(client.calls, [])
        self.assertFalse(database.closed)

    def test_exact_patch_payload_decodes_and_hashes(self):
        envelope, preimage, postimage = canary.patch_envelope()
        lines = envelope.splitlines()
        decoded = canary.zlib.decompress(canary.base64.b64decode(lines[3][1:])).decode()
        self.assertEqual(decoded, canary.FINAL)
        self.assertEqual(preimage, canary.hashlib.sha256(canary.INITIAL.encode()).hexdigest())
        self.assertEqual(postimage, canary.hashlib.sha256(decoded.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
