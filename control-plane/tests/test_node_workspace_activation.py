"""Local folder selection ensures permanent bindings without pilot authority."""

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
from control_plane.store import ConflictError, ControlPlaneStore, NotFoundError, PermissionError, ValidationError


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
        self.store.set_admission_mode(mode="open")

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
        return action

    def test_activation_returns_active_binding_shape_without_pilot(self) -> None:
        grants_before = self.table("mcp_service_grants")
        result = self.activate()
        self.assertEqual(set(result), {"device_id", "workspace_id", "workspace_generation", "binding_id", "state"})
        self.assertEqual(result["state"], "active")
        self.assertEqual(result["workspace_id"], "workspace-autocad")
        self.assertTrue(result["binding_id"].startswith("bind_"))
        self.assertEqual(self.table("scoped_pilot_decisions"), [])
        self.assertEqual(self.store.admission_status()["admission_mode"], "open")
        self.assertEqual(self.table("mcp_service_grants"), grants_before)
        self.assertEqual(len(self.table("bindings")), 2)

    def test_existing_binding_and_lost_response_retry_do_not_duplicate_authority(self) -> None:
        existing = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-autocad",
            workspace_generation="generation-1", display_name="Autocad",
        )
        result = self.activate()
        snapshot = {name: self.table(name) for name in ("bindings", "scoped_pilot_decisions", "events")}
        retry = self.activate()
        self.assertEqual(retry, result)
        self.assertEqual(result["binding_id"], existing["binding_id"])
        self.assertEqual({name: self.table(name) for name in snapshot}, snapshot)
        # A retry does not change scope and must remain observable during work.
        self.store.create_mcp_task_session(owner_id="owner_default", principal_id=self.principal,
                                          binding_id=result["binding_id"], label="Started after activation")
        self.assertEqual(self.activate(), result)

    def test_same_owner_principal_shares_binding_foreign_principal_or_device_or_generation_rejected(self) -> None:
        other = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        foreign = self.store.create_private_tunnel_service_principal(owner_id="owner_other")["principal_id"]
        self.store.enroll_node(owner_id="owner_default", device_id="device-other",
                               endpoint_id="endpoint-other", display_name="Other node")
        first = self.activate()
        self.assertEqual(self.activate(principal_id=other), first)
        for overrides, error in (({"principal_id": foreign}, PermissionError),
                                 ({"device_id": "device-other"}, (ConflictError, PermissionError, NotFoundError)),
                                 ({"workspace_generation": "generation-missing"}, (ConflictError, PermissionError, NotFoundError))):
            with self.subTest(overrides=overrides), self.assertRaises(error):
                self.activate(**overrides)

    def test_activation_ignores_admission_mode_and_unresolved_actions(self) -> None:
        for mode in ("open", "recovery"):
            with self.subTest(mode=mode):
                self.store.set_admission_mode(mode=mode)
                result = self.activate()
                self.assertEqual(result["state"], "active")
        self.store.set_admission_mode(mode="open")
        self.read()
        for state in ("queued", "dispatch_unconfirmed", "accepted", "reconcile_required"):
            with self.subTest(state=state):
                with self.store._connection() as connection:
                    connection.execute("UPDATE actions SET delivery_state=?", (state,))
                before = {name: self.table(name) for name in ("actions", "delivery_attempts", "receipts")}
                self.activate()
                self.assertEqual({name: self.table(name) for name in before}, before)
                self.assertEqual(len(self.table("bindings")), 2)
                self.assertEqual(self.table("scoped_pilot_decisions"), [])

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

    def test_failed_commit_rolls_back_binding_and_audit_together(self) -> None:
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

    def test_binding_poll_and_revocation_fence_only_the_exact_workspace(self) -> None:
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
        self.store.revoke_binding(owner_id="owner_default", binding_id=result["binding_id"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                                workspace_id="workspace-autocad", workspace_generation="generation-1"), [])
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read",
                                            workspace_id="workspace-alpha", workspace_generation="generation-1")
        self.assertEqual([item["action_id"] for item in delivered], [alpha["action_id"]])
        self.assertNotEqual(self.store.action(owner_id="owner_default", action_id=autocad["action_id"])["delivery_state"], "queued")

    def test_unresolved_actions_no_longer_veto_activation(self) -> None:
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
        self.store.revoke_binding(owner_id="owner_default", binding_id=result["binding_id"])
        history = {name: self.table(name) for name in ("actions", "delivery_attempts", "receipts")}
        again = self.activate()
        self.assertEqual(again["workspace_id"], "workspace-autocad")
        self.assertNotEqual(again["binding_id"], result["binding_id"])
        self.assertEqual({name: self.table(name) for name in history}, history)
        self.store.quarantine_historical_unknown_actions(owner_id="owner_default", device_id="device-alpha",
            action_ids=[read["action_id"]], declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT")
        self.assertEqual(self.activate()["workspace_id"], "workspace-autocad")

    def test_recovery_mode_does_not_revoke_bindings(self) -> None:
        self.activate()
        self.store.set_admission_mode(mode="recovery")
        self.assertEqual({row["revoked_at_ms"] for row in self.table("bindings")}, {None})
        self.store.set_admission_mode(mode="open")
        self.assertEqual(len(self.authority()["targets"]), 2)

    def test_cross_root_retired_quarantined_read_is_preserved_without_replay(self) -> None:
        action = self.quarantine_retired_read()
        names = ("actions", "action_reconciliations", "delivery_attempts", "receipts")
        before = {name: self.table(name) for name in names}
        result = self.activate()
        self.assertEqual(result["workspace_id"], "workspace-autocad")
        self.assertEqual({name: self.table(name) for name in names}, before)
        self.assertIsNone(self.store.action(owner_id="owner_default", action_id=action["action_id"])["settled_at_ms"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])

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
        self.assertEqual(set(response), {"device_id", "workspace_id", "workspace_generation", "binding_id", "state"})
        self.assertEqual(post(body, "Node " + self.node["node_secret"])[1], response)
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

    def test_private_authority_projection_includes_both_exact_live_workspaces(self) -> None:
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

    def test_private_authority_projection_fails_closed_after_binding_node_or_workspace_revocation(self) -> None:
        self.activate()
        mutations = [
            ("UPDATE bindings SET revoked_at_ms=? WHERE device_id='device-alpha'", (self.now,),
             "UPDATE bindings SET revoked_at_ms=NULL WHERE device_id='device-alpha'", ()),
            ("UPDATE nodes SET revoked_at_ms=? WHERE device_id='device-alpha'", (self.now,),
             "UPDATE nodes SET revoked_at_ms=NULL WHERE device_id='device-alpha'", ()),
            ("UPDATE node_workspaces SET retired_at_ms=? WHERE device_id='device-alpha'", (self.now,),
             "UPDATE node_workspaces SET retired_at_ms=NULL WHERE device_id='device-alpha'", ()),
        ]
        for mutation, parameters, restore, restore_parameters in mutations:
            with self.subTest(mutation=mutation), self.store._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(mutation, parameters)
                connection.execute("COMMIT")
                try:
                    projection = self.authority()
                    self.assertEqual(projection["targets"], [])
                    self.assertIn(projection["state"], ("blocked", "revoked"))
                finally:
                    connection.execute(restore, restore_parameters)

    def test_private_authority_projection_no_longer_scoped_by_principal(self) -> None:
        # Deliberate no-pilot contract: authority is per owner/device live
        # bindings, not per principal. Any valid service principal of the
        # owner sees the same live targets; node endpoint replacement no
        # longer fences this projection (it did so only via the deleted
        # decision endpoint comparison), while binding, node, and workspace
        # liveness still fence it (see the revocation test above).
        self.activate()
        expected = {target["workspace_id"] for target in self.authority()["targets"]}
        other = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        foreign = self.store.create_private_tunnel_service_principal(owner_id="owner_other")["principal_id"]
        for principal in (other, foreign):
            with self.subTest(principal=principal):
                self.assertEqual({target["workspace_id"] for target in self.authority(principal_id=principal)["targets"]}, expected)


if __name__ == "__main__":
    unittest.main()
