"""Local folder selection preserves exact node and immutable pilot authority."""

from __future__ import annotations

from contextlib import contextmanager
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from control_plane.http_api import ControlPlaneHttpServer
from control_plane.mcp_oauth import PrivateTunnelServiceConfiguration
from control_plane.store import ConflictError, ControlPlaneStore, PermissionError, ValidationError


CONTRACT = {"schema_version": 3, "profile": "control-plane-read-only-queue-v2", "sha256": "f" * 64}


class NodeWorkspaceActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="node-workspace-activation-")
        self.addCleanup(temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.node = self.store.enroll_node(owner_id="owner_default", device_id="device-alpha",
                                           endpoint_id="endpoint-alpha", display_name="Windows node")
        for workspace in ("alpha", "autocad"):
            self.register(workspace)
        self.binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Alpha",
        )
        self.principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        self.store.heartbeat(device_id="device-alpha", endpoint_id="endpoint-alpha", runtime_instance_id="runtime-alpha",
                             mcp_server_instance_id="server-alpha", activation_epoch="epoch-alpha",
                             contract_version="smart-v3", readiness="ready")
        self.store.set_admission_mode(mode="recovery")
        self.pilot = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            expires_at_ms=self.now + 120_000, reason="Existing approved node pilot",
        )
        self.store.set_admission_mode(mode="scoped_pilot")

    def register(self, workspace: str, generation: str = "generation-1") -> dict:
        return self.store.register_node_workspace(
            device_id="device-alpha", workspace_id="workspace-" + workspace,
            workspace_generation=generation, display_name=workspace,
            capabilities={"read": True, "write": True, "exec": True},
        )

    def activate(self, **overrides: str) -> dict:
        return self.store.activate_node_workspace(**{
            "device_id": "device-alpha", "principal_id": self.principal,
            "workspace_id": "workspace-autocad", "workspace_generation": "generation-1", **overrides,
        })

    def table(self, name: str) -> list[dict]:
        with self.store._connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM " + name)]

    def task(self) -> dict:
        return self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"], label="Work",
        )

    def read(self, key: str = "activation-read-0001") -> dict:
        return self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key=key,
            facade_contract=CONTRACT,
        )

    def quarantine_retired_read(self) -> dict:
        intent = self.read()
        delivery = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")[0]
        self.store.record_receipt(
            device_id="device-alpha", action_id=intent["action_id"], attempt_id=delivery["attempt_id"],
            receipt_state="unknown", local_handle="", payload={
                "schema_version": 1, "operation_kind": "control_plane_bounded_file_read",
                "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
            },
        )
        self.store.quarantine_historical_unknown_actions(
            owner_id="owner_default", device_id="device-alpha", action_ids=[intent["action_id"]],
            declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT",
        )
        action = self.store.action(owner_id="owner_default", action_id=intent["action_id"])
        self.now = action["expires_at_ms"] + 1
        self.register("alpha", "generation-2")
        self.binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-2", display_name="Alpha replacement",
        )
        self.store.set_admission_mode(mode="recovery")
        self.pilot = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            expires_at_ms=self.now + 120_000, reason="Current pilot with audited retired read history",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        return action

    def test_activation_preserves_expiry_principal_and_immutable_previous_target(self) -> None:
        grants_before = self.table("mcp_service_grants")
        result = self.activate()
        self.assertFalse(result["replayed"])
        self.assertEqual(result["expires_at_ms"], self.pilot["expires_at_ms"])
        self.assertNotEqual(result["pilot_decision_id"], self.pilot["decision_id"])
        previous = self.store.scoped_pilot_decision(owner_id="owner_default", decision_id=self.pilot["decision_id"])
        self.assertEqual(previous, self.pilot)
        current = self.store.scoped_pilot_decision(owner_id="owner_default", decision_id=result["pilot_decision_id"])
        self.assertEqual(current["principal_id"], self.principal)
        self.assertEqual(current["workspace_id"], "workspace-autocad")
        self.assertEqual(self.store.admission_status()["admission_mode"], "scoped_pilot")
        self.assertEqual(self.table("mcp_service_grants"), grants_before)
        self.assertEqual(len([row for row in self.table("scoped_pilot_decisions") if row["revoked_at_ms"] is None]), 2)

    def test_existing_binding_and_lost_response_retry_do_not_duplicate_authority(self) -> None:
        existing = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-autocad",
            workspace_generation="generation-1", display_name="Autocad",
        )
        result = self.activate()
        snapshot = {name: self.table(name) for name in ("bindings", "scoped_pilot_decisions", "events")}
        retry = self.activate()
        self.assertEqual(retry, {**result, "replayed": True})
        self.assertEqual(result["binding_id"], existing["binding_id"])
        self.assertEqual({name: self.table(name) for name in snapshot}, snapshot)
        # A retry does not change scope and must remain observable during work.
        self.store.create_mcp_task_session(owner_id="owner_default", principal_id=self.principal,
                                          binding_id=result["binding_id"], label="Started after activation")
        self.assertTrue(self.activate()["replayed"])

    def test_other_device_principal_owner_or_generation_cannot_inherit_pilot(self) -> None:
        other = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        foreign = self.store.create_private_tunnel_service_principal(owner_id="owner_other")["principal_id"]
        self.store.enroll_node(owner_id="owner_default", device_id="device-other",
                               endpoint_id="endpoint-other", display_name="Other node")
        for overrides in ({"principal_id": other}, {"principal_id": foreign}, {"device_id": "device-other"},
                          {"workspace_generation": "generation-missing"}):
            with self.subTest(overrides=overrides), self.assertRaises((ConflictError, PermissionError)):
                self.activate(**overrides)
        self.assertEqual(self.store.scoped_pilot_decision(owner_id="owner_default", decision_id=self.pilot["decision_id"]), self.pilot)

    def test_expired_revoked_or_unscoped_pilot_cannot_activate(self) -> None:
        for mode in ("open", "recovery"):
            with self.subTest(mode=mode):
                self.store.set_admission_mode(mode=mode)
                with self.assertRaises(ConflictError):
                    self.activate()
        with self.store._connection() as connection:
            connection.execute("UPDATE control_plane_state SET state_value='scoped_pilot' WHERE state_key='admission_mode'")
            connection.execute("UPDATE scoped_pilot_decisions SET revoked_at_ms=NULL")
        self.now = self.pilot["expires_at_ms"]
        with self.assertRaises(ConflictError):
            self.activate()

    def test_parallel_tasks_and_writer_leases_remain_independent(self) -> None:
        task = self.task()
        lease = self.store.claim_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=task["task_id"])
        before_task = self.table("mcp_task_sessions")[0]
        result = self.activate()
        other = self.store.create_mcp_task_session(owner_id="owner_default", principal_id=self.principal,
                                                 binding_id=result["binding_id"], label="Independent workspace")
        other_lease = self.store.claim_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=other["task_id"])
        self.assertEqual(self.table("mcp_task_sessions")[0], before_task)
        self.assertNotEqual(lease["binding_id"], other_lease["binding_id"])
        self.assertEqual(len([row for row in self.table("mcp_task_writer_leases") if row["released_at_ms"] is None]), 2)
        competing = self.task()
        with self.assertRaises(ConflictError):
            self.store.claim_mcp_task_writer_lease(owner_id="owner_default", principal_id=self.principal, task_id=competing["task_id"])

    def test_unrelated_queued_and_unresolved_actions_do_not_block_additive_activation(self) -> None:
        self.read()
        for state in ("queued", "dispatch_unconfirmed", "accepted", "reconcile_required"):
            with self.subTest(state=state):
                with self.store._connection() as connection:
                    connection.execute("UPDATE actions SET delivery_state=?", (state,))
                before = {name: self.table(name) for name in ("actions", "delivery_attempts", "receipts")}
                self.activate()
                self.assertEqual({name: self.table(name) for name in before}, before)
                self.assertEqual(len(self.table("bindings")), 2)
                self.assertIsNone(self.table("scoped_pilot_decisions")[0]["revoked_at_ms"])

    def test_failed_commit_rolls_back_binding_pilot_and_audit_together(self) -> None:
        original_connection = self.store._connection

        class CommitFailure:
            def __init__(self, connection):
                self.connection = connection

            def execute(self, statement, parameters=()):
                if statement.strip().upper() == "COMMIT":
                    self.connection.execute("ROLLBACK")
                    raise sqlite3.OperationalError("simulated durable commit failure")
                return self.connection.execute(statement, parameters)

            def __getattr__(self, name):
                return getattr(self.connection, name)

        @contextmanager
        def failed_connection():
            with original_connection() as connection:
                yield CommitFailure(connection)

        before = {name: self.table(name) for name in ("bindings", "scoped_pilot_decisions", "events")}
        with mock.patch.object(self.store, "_connection", failed_connection), self.assertRaises(sqlite3.OperationalError):
            self.activate()
        self.assertEqual({name: self.table(name) for name in before}, before)

    def test_scoped_poll_and_revocation_fence_only_the_exact_workspace(self) -> None:
        result = self.activate()
        alpha = self.read()
        autocad = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=result["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key="autocad-read-0001",
            facade_contract=CONTRACT,
        )
        for scope in ({"workspace_id": "workspace-alpha"}, {"workspace_generation": "generation-1"}):
            with self.assertRaises(ValidationError):
                self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read", **scope)
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                                workspace_id="workspace-autocad", workspace_generation="generation-other"), [])
        self.store.revoke_scoped_pilot_decision(owner_id="owner_default", decision_id=result["pilot_decision_id"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                                workspace_id="workspace-autocad", workspace_generation="generation-1"), [])
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                            workspace_id="workspace-alpha", workspace_generation="generation-1")
        self.assertEqual([item["action_id"] for item in delivered], [alpha["action_id"]])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=autocad["action_id"])["delivery_state"], "queued")

    def test_exact_workspace_unknown_requires_supported_quarantine_before_reissue(self) -> None:
        result = self.activate()
        read = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=result["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key="autocad-unknown-0001",
            facade_contract=CONTRACT,
        )
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                            workspace_id="workspace-autocad", workspace_generation="generation-1")[0]
        self.store.record_receipt(device_id="device-alpha", action_id=read["action_id"], attempt_id=delivered["attempt_id"],
                                  receipt_state="unknown", local_handle="", payload={"schema_version": 1,
                                  "operation_kind": "control_plane_bounded_file_read", "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN"})
        self.store.revoke_scoped_pilot_decision(owner_id="owner_default", decision_id=result["pilot_decision_id"])
        history = {name: self.table(name) for name in ("actions", "delivery_attempts", "receipts")}
        with self.assertRaisesRegex(ConflictError, "unresolved"):
            self.activate()
        self.store.quarantine_historical_unknown_actions(owner_id="owner_default", device_id="device-alpha",
            action_ids=[read["action_id"]], declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT")
        self.activate()
        self.assertEqual({name: self.table(name) for name in history}, history)

    def test_operator_can_issue_multiple_exact_decisions_and_recovery_revokes_all(self) -> None:
        binding = self.store.create_binding(owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-autocad",
                                            workspace_generation="generation-1", display_name="Autocad")
        self.store.create_scoped_pilot_decision(owner_id="owner_default", principal_id=self.principal,
            binding_id=binding["binding_id"], expires_at_ms=self.pilot["expires_at_ms"], reason="Parallel authorized workspace")
        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(owner_id="owner_default", principal_id=self.principal,
                binding_id=binding["binding_id"], expires_at_ms=self.pilot["expires_at_ms"], reason="Duplicate target denied")
        self.store.set_admission_mode(mode="open")
        self.store.set_admission_mode(mode="scoped_pilot")
        self.assertEqual(len(self.authority()["targets"]), 2)
        self.store.set_admission_mode(mode="recovery")
        self.assertEqual({item["revoked_at_ms"] for item in self.table("scoped_pilot_decisions")}, {self.now})
        with self.assertRaises(ConflictError):
            self.store.set_admission_mode(mode="scoped_pilot")

    def test_cross_root_retired_quarantined_read_is_preserved_without_replay(self) -> None:
        action = self.quarantine_retired_read()
        names = ("actions", "action_reconciliations", "delivery_attempts", "receipts")
        before = {name: self.table(name) for name in names}
        result = self.activate()
        self.assertEqual(result["workspace_id"], "workspace-autocad")
        self.assertEqual({name: self.table(name) for name in names}, before)
        self.assertIsNone(self.store.action(owner_id="owner_default", action_id=action["action_id"])["settled_at_ms"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])

    def test_same_workspace_historical_exception_rejects_missing_fences_or_corrupt_evidence(self) -> None:
        action = self.quarantine_retired_read()
        mutations = [
            ("node_workspaces", "retired_at_ms", None, "workspace_id='workspace-alpha' AND workspace_generation='generation-1'", ()),
            ("bindings", "revoked_at_ms", None, "binding_id=?", (action["binding_id"],)),
            ("contexts", "closed_at_ms", None, "context_id=?", (action["context_id"],)),
            ("actions", "expires_at_ms", self.now + 1, "action_id=?", (action["action_id"],)),
            ("receipts", "local_handle", "unknown-handle", "action_id=?", (action["action_id"],)),
            ("actions", "action_digest", "0" * 64, "action_id=?", (action["action_id"],)),
            ("action_reconciliations", "evidence_digest", "0" * 64, "action_id=?", (action["action_id"],)),
            ("actions", "tool_name", "exec_command", "action_id=?", (action["action_id"],)),
            ("actions", "tool_name", "agent_workflow", "action_id=?", (action["action_id"],)),
        ]
        for table, column, value, where, params in mutations:
            with self.subTest(table=table, column=column), self.store._connection() as connection:
                previous = connection.execute("SELECT " + column + " FROM " + table + " WHERE " + where, params).fetchone()[0]
                connection.execute("UPDATE " + table + " SET " + column + "=? WHERE " + where, (value, *params))
                try:
                    self.assertEqual(self.store._blocking_unresolved_action_count_for_pilot(
                        connection, device_id="device-alpha", owner_id="owner_default", principal_id=self.principal,
                        binding_id=self.binding["binding_id"], workspace_id="workspace-alpha", workspace_generation="generation-2"), 1)
                finally:
                    connection.execute("UPDATE " + table + " SET " + column + "=? WHERE " + where, (previous, *params))

    def test_http_requires_exact_node_secret_confirmation_and_configured_principal(self) -> None:
        server = ControlPlaneHttpServer(("127.0.0.1", 0), self.store, "o" * 40,
            mcp_private_service=PrivateTunnelServiceConfiguration(principal_id=self.principal,
                required_scope="control-plane.inventory", file_read_enabled=True))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        body = {"workspace_id": "workspace-autocad", "workspace_generation": "generation-1", "confirm_activate": True}

        def post(payload, authorization):
            request = Request(f"http://127.0.0.1:{server.server_port}/v1/nodes/device-alpha/activate-workspace",
                data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": authorization},
                method="POST")
            try:
                with urlopen(request, timeout=2) as response:
                    return response.status, json.loads(response.read())
            except HTTPError as error:
                with error:
                    return error.code, json.loads(error.read())

        self.assertEqual(post(body, "Bearer " + "o" * 40)[0], 403)
        self.assertEqual(post(body, "Node " + "wrong-node-secret-0000000000000000000000")[0], 403)
        for invalid in ({**body, "confirm_activate": False}, {**body, "owner_id": "owner_default"},
                        {**body, "principal_id": self.principal}, {**body, "workspace_path": "E:\\DEV\\Autocad"}):
            with self.subTest(invalid=invalid):
                self.assertEqual(post(invalid, "Node " + self.node["node_secret"])[0], 400)
        server.mcp_private_service = None
        self.assertEqual(post(body, "Node " + self.node["node_secret"])[0], 409)
        server.mcp_private_service = PrivateTunnelServiceConfiguration(principal_id=self.principal,
                                                                       required_scope="control-plane.inventory")
        status, response = post(body, "Node " + self.node["node_secret"])
        self.assertEqual(status, 200)
        self.assertEqual(set(response), {"device_id", "workspace_id", "workspace_generation", "binding_id",
                                         "pilot_decision_id", "expires_at_ms", "replayed", "state"})
        self.assertEqual(response["expires_at_ms"], self.pilot["expires_at_ms"])
        self.assertEqual(post(body, "Node " + self.node["node_secret"])[1], {**response, "replayed": True})
        request = Request(f"http://127.0.0.1:{server.server_port}/v1/nodes/device-alpha/authority-status",
            data=b"{}", headers={"Content-Type": "application/json", "Authorization": "Node " + self.node["node_secret"]},
            method="POST")
        with urlopen(request, timeout=2) as observed:
            authority = json.loads(observed.read())
        self.assertEqual({target["workspace_id"] for target in authority["targets"]}, {"workspace-alpha", "workspace-autocad"})
        for workspace, expected_status in (("workspace-alpha", 200), ("workspace-autocad", 200)):
            request = Request(f"http://127.0.0.1:{server.server_port}/v1/nodes/device-alpha/policy-authority",
                data=json.dumps({"workspace_id": workspace, "workspace_generation": "generation-1"}).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Node " + self.node["node_secret"]},
                method="POST")
            try:
                with urlopen(request, timeout=2) as observed:
                    status = observed.status
            except HTTPError as error:
                with error:
                    status = error.code
            self.assertEqual(status, expected_status)

    def authority(self, **overrides) -> dict:
        return self.store.node_authority_status(**{
            "device_id": "device-alpha", "node_secret": self.node["node_secret"],
            "principal_id": self.principal, **overrides,
        })

    def test_private_authority_projection_includes_both_exact_delegated_workspaces(self) -> None:
        self.assertEqual([target["workspace_id"] for target in self.authority()["targets"]], ["workspace-alpha"])
        self.activate()
        projection = self.authority()
        self.assertEqual({target["workspace_id"] for target in projection["targets"]}, {"workspace-alpha", "workspace-autocad"})
        self.assertEqual(projection["target_count"], 2)
        self.assertEqual(projection["dispatchable_target_count"], 2)
        self.assertEqual(projection["workspace_count"], 2)
        self.assertEqual(projection["state"], "active")
        self.assertEqual(len(self.authority(principal_id=None)["targets"]), 2)
        self.assertIsNone(self.store.binding(owner_id="owner_default", binding_id=self.binding["binding_id"])["revoked_at_ms"])

    def test_private_authority_projection_fails_closed_after_expiry_revocation_or_recovery(self) -> None:
        for mutation, parameters in (
            ("UPDATE scoped_pilot_decisions SET expires_at_ms=?", (self.now,)),
            ("UPDATE scoped_pilot_decisions SET revoked_at_ms=?", (self.now,)),
            ("UPDATE control_plane_state SET state_value='recovery' WHERE state_key='admission_mode'", ()),
            ("UPDATE oauth_principals SET revoked_at_ms=? WHERE principal_id=?", (self.now, self.principal)),
        ):
            with self.subTest(mutation=mutation), self.store._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(mutation, parameters)
                # Separate read connections see durable state, not an uncommitted fixture.
                connection.execute("COMMIT")
                try:
                    projection = self.authority()
                    self.assertEqual(projection["targets"], [])
                    self.assertEqual(projection["state"], "blocked")
                finally:
                    connection.execute("UPDATE scoped_pilot_decisions SET expires_at_ms=?, revoked_at_ms=NULL",
                                       (self.pilot["expires_at_ms"],))
                    connection.execute("UPDATE control_plane_state SET state_value='scoped_pilot' WHERE state_key='admission_mode'")
                    connection.execute("UPDATE oauth_principals SET revoked_at_ms=NULL WHERE principal_id=?", (self.principal,))

    def test_private_authority_projection_rejects_other_principal_owner_and_stale_endpoint(self) -> None:
        other = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        foreign = self.store.create_private_tunnel_service_principal(owner_id="owner_other")["principal_id"]
        for principal in (other, foreign):
            with self.subTest(principal=principal):
                self.assertEqual(self.authority(principal_id=principal)["targets"], [])
        with self.store._connection() as connection:
            connection.execute("UPDATE nodes SET endpoint_id='endpoint-replaced' WHERE device_id='device-alpha'")
        self.assertEqual(self.authority()["targets"], [])


if __name__ == "__main__":
    unittest.main()
