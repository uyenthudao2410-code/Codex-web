"""Offline SQLite/context tests; no SSH, API or original canary main invocation."""
import ast
import copy
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("observer", HERE / "observe-r11.py")
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "db.sqlite3"
        self.common = types.SimpleNamespace(BINDING="binding", DEVICE="device", WORKSPACE="workspace", GENERATION="generation", PRINCIPAL="principal")
        self.pins = {"context_id": "owner-context", "requested_at_ms": 100000, "expires_at_ms": 3700000}
        self.family = {"action_id": observer.ACTION, "task_id": observer.TASK, "request_id": "request"}
        target = {"owner_id": "owner", "binding_id": "binding", "device_id": "device", "endpoint_id": "endpoint", "workspace_id": "workspace", "workspace_generation": "generation"}
        self.context = {"context_id": "action-context", **target, "created_at_ms": 200000, "expires_at_ms": 800000, "closed_at_ms": None}
        self.owner_context = {**self.context, "context_id": "owner-context", "created_at_ms": 100000, "expires_at_ms": 3700000}
        records = {
            "contexts": [self.context, self.owner_context],
            "actions": [{**target, "action_id": observer.ACTION, "request_id": "request", "context_id": "action-context", "created_at_ms": 200000, "expires_at_ms": 800000}],
            "work_requests": [{"request_id": "request", "owner_id": "owner", "context_id": "action-context", "created_at_ms": 200000, "expires_at_ms": 800000, "canceled_at_ms": None}],
            "mcp_standing_patch_intents": [{"owner_id": "owner", "principal_id": "principal", "binding_id": "binding", "task_id": observer.TASK, "action_id": observer.ACTION, "request_id": "request", "authority_mode": "standing", "created_at_ms": 200000}],
            "mcp_task_action_links": [{"task_id": observer.TASK, "action_id": observer.ACTION}],
            "mcp_task_sessions": [{**target, "task_id": observer.TASK, "principal_id": "principal"}]}
        with closing(sqlite3.connect(self.database)) as conn:
            for table, rows in records.items():
                fields = list(rows[0])
                conn.execute("CREATE TABLE " + table + " (" + ",".join(fields) + ")")
                conn.executemany("INSERT INTO " + table + " VALUES (" + ",".join("?" for _ in fields) + ")", [tuple(row[key] for key in fields) for row in rows])
            conn.commit()
        source = ast.parse((HERE.parent / "activation-server/r11_common.py").read_bytes())
        func = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "renewed_authority")
        namespace = {"require": observer.require, "BINDING": "binding", "DEVICE": "device", "WORKSPACE": "workspace", "GENERATION": "generation", "PRINCIPAL": "principal"}
        exec(compile(ast.Module(body=[func], type_ignores=[]), "frozen-pure-authority", "exec"), namespace)
        self.common.renewed_authority = namespace["renewed_authority"]
        self.pins["pilot_id"] = "pilot"
        self.overview = {"observed_at_ms": 300000, "contexts": [self.owner_context, self.context], "scoped_pilot_decisions": [{"decision_id": "pilot", "binding_id": "binding", "device_id": "device", "workspace_id": "workspace", "workspace_generation": "generation", "principal_id": "principal", "expires_at_ms": 3700000, "revoked_at_ms": None}]}

    def consume(self):
        return observer.context_family(self.database, self.common, self.pins, self.family)

    def change(self, sql, args=()):
        with closing(sqlite3.connect(self.database)) as conn:
            conn.execute(sql, args)
            conn.commit()

    def test_exact_causal_context_accepted_and_database_unchanged(self):
        before = self.database.read_bytes()
        self.assertEqual(self.consume(), self.context)
        self.assertEqual(self.database.read_bytes(), before)

    def test_broken_request_link_and_wrong_owner_rejected(self):
        for sql in ("UPDATE work_requests SET context_id='other'", "UPDATE contexts SET owner_id='other' WHERE context_id='action-context'"):
            with self.subTest(sql=sql):
                self.change(sql)
                with self.assertRaises(observer.Failure):
                    self.consume()
                self.change("UPDATE work_requests SET context_id='action-context'")

    def test_unrelated_action_or_task_refused(self):
        self.family["action_id"] = "other"
        with self.assertRaises(observer.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "EXACT_DISPATCHED_FAMILY_REQUIRED")

    def test_context_reuse_refused(self):
        self.change("INSERT INTO actions SELECT owner_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,'other',request_id,context_id,created_at_ms,expires_at_ms FROM actions")
        with self.assertRaises(observer.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "ACTION_CONTEXT_REUSED_BY_OTHER_WORK")

    def test_expiry_or_target_changed_refused(self):
        self.change("UPDATE contexts SET expires_at_ms=800001 WHERE context_id='action-context'")
        with self.assertRaises(observer.Failure) as error:
            self.consume()
        self.assertEqual(error.exception.code, "ACTION_CONTEXT_WINDOW_CHANGED")

    def test_filtered_view_preserves_source_and_original_authority(self):
        before = copy.deepcopy(self.overview)
        view = observer.authority_view(self.common, self.pins, self.overview, self.consume())
        self.assertEqual(self.overview, before)
        self.assertEqual(view["contexts"], [self.owner_context])

    def test_unrelated_live_context_still_refused(self):
        self.overview["contexts"].append({**self.context, "context_id": "unrelated"})
        with self.assertRaises(observer.Failure) as error:
            observer.authority_view(self.common, self.pins, self.overview, self.consume())
        self.assertEqual(error.exception.code, "RENEWED_CONTEXT_CHANGED")

    def test_changed_owner_context_or_pilot_still_refused(self):
        self.overview["contexts"][0] = {**self.owner_context, "expires_at_ms": 3700001}
        with self.assertRaises(observer.Failure):
            observer.authority_view(self.common, self.pins, self.overview, self.consume())

    def test_no_mutating_calls_or_common_inspect(self):
        tree = ast.parse((HERE / "observe-r11.py").read_bytes())
        calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        for prohibited in ("inspect", "main", "exclusive", "save", "rpc", "call"):
            self.assertNotIn(prohibited, calls)
        self.assertIn("?mode=ro", (HERE / "observe-r11.py").read_text())
        self.assertIn("connection.close()", (HERE / "observe-r11.py").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
