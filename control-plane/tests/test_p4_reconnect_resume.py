"""P4 open-and-use: reconnect resume invariants.

Covers the two layers P4 can honestly pin from the Windows checkout:

* Store layer (control_plane.store): after a simulated disconnect and a
  fresh-heartbeat reconnect, poll dispatches only still-queued actions;
  settled actions are never re-dispatched. Pilot renewal keeps scope
  (only expiry changes), an expired pilot cannot be renewed, and workspace
  activation replays the live pilot (re-homing) without minting authority.
* Node-agent layer (control_plane.node_agent): the connected-agent loop
  classifies reconnect moments (agent start / readiness transition) and
  summarises reconnect authority observations without minting anything.

What this file deliberately does NOT claim: operator-token pilot renewal
and admission reopen are server-side operator operations (see
store.renew_scoped_pilot_decision and http_api admission routes) and are
not available to the node agent, which holds no operator token.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane import node_agent as node_agent_module
from control_plane.node_agent import (
    reconnect_authority_state,
    reconnect_transition_kind,
    run_connected_agent,
)
from control_plane.store import ConflictError, ControlPlaneStore

CONTRACT = {"schema_version": 3, "profile": "control-plane-read-only-queue-v2", "sha256": "f" * 64}


class ReconnectStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="p4-reconnect-")
        self.addCleanup(temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.store.enroll_node(owner_id="owner_default", device_id="device-alpha",
                               endpoint_id="endpoint-alpha", display_name="Windows node")
        for workspace in ("alpha", "autocad"):
            self.store.register_node_workspace(
                device_id="device-alpha", workspace_id="workspace-" + workspace,
                workspace_generation="generation-1", display_name=workspace,
                capabilities={"read": True, "write": True, "exec": True},
            )
        self.binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Alpha",
        )
        self.principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")["principal_id"]
        self.store.heartbeat(device_id="device-alpha", endpoint_id="endpoint-alpha",
                             runtime_instance_id="runtime-alpha", mcp_server_instance_id="server-alpha",
                             activation_epoch="epoch-alpha", contract_version="smart-v3", readiness="ready")
        self.store.set_admission_mode(mode="recovery")
        self.pilot = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            expires_at_ms=self.now + 20 * 60 * 60 * 1000, reason="P4 reconnect pilot",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=self.principal,
            binding_id=self.binding["binding_id"], label="P4 work",
        )

    def read(self, key: str) -> dict:
        return self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=self.principal, binding_id=self.binding["binding_id"],
            path="README.md", start_line=1, max_lines=5, max_bytes=1024, idempotency_key=key,
            facade_contract=CONTRACT,
        )

    def action_state(self, action_id: str) -> str:
        return self.store.action(owner_id="owner_default", action_id=action_id)["delivery_state"]

    def test_reconnect_dispatches_only_queued_actions(self) -> None:
        settled = self.read(key="p4-read-settled")
        delivery = self.store.poll_actions(device_id="device-alpha", limit=1, lane="bounded_file_read")
        self.assertEqual(len(delivery), 1)
        self.assertEqual(delivery[0]["action_id"], settled["action_id"])
        self.store.record_receipt(
            device_id="device-alpha", action_id=settled["action_id"],
            attempt_id=delivery[0]["attempt_id"], receipt_state="completed",
            local_handle="local-p4-settled", payload={},
        )
        self.assertEqual(self.action_state(settled["action_id"]), "settled")
        queued = self.read(key="p4-read-queued")
        # Disconnect: the clock moves past the 60s heartbeat age, so the node
        # is no longer dispatchable and the queued action must not move.
        self.now += 120_000
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        # Reconnect: a fresh heartbeat with a new runtime identity.
        self.store.heartbeat(device_id="device-alpha", endpoint_id="endpoint-alpha",
                             runtime_instance_id="runtime-beta", mcp_server_instance_id="server-beta",
                             activation_epoch="epoch-beta", contract_version="smart-v3", readiness="ready")
        redelivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")
        self.assertEqual([row["action_id"] for row in redelivered], [queued["action_id"]])
        # No duplicate delivery: the same poll again returns nothing, and
        # settling the queued action ends the story.
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        self.store.record_receipt(
            device_id="device-alpha", action_id=queued["action_id"],
            attempt_id=redelivered[0]["attempt_id"], receipt_state="completed",
            local_handle="local-p4-queued", payload={},
        )
        self.assertEqual(self.action_state(queued["action_id"]), "settled")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])

    def _fresh_pilot_on_autocad(self) -> dict:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-autocad",
            workspace_generation="generation-1", display_name="Autocad",
        )
        self.store.set_admission_mode(mode="recovery")
        pilot = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=self.principal, binding_id=binding["binding_id"],
            expires_at_ms=self.now + 120_000, reason="P4 renew pilot",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        return pilot

    def test_renew_expired_pilot_raises_conflict(self) -> None:
        pilot = self._fresh_pilot_on_autocad()
        self.now = pilot["expires_at_ms"] + 1
        with self.assertRaises(ConflictError):
            self.store.renew_scoped_pilot_decision(
                owner_id="owner_default", decision_id=pilot["decision_id"],
                expires_at_ms=self.now + 3_600_000,
            )

    def test_renew_live_pilot_preserves_scope(self) -> None:
        pilot = self._fresh_pilot_on_autocad()
        renewed = self.store.renew_scoped_pilot_decision(
            owner_id="owner_default", decision_id=pilot["decision_id"],
            expires_at_ms=self.now + 3_600_000,
        )
        self.assertEqual(renewed["decision_id"], pilot["decision_id"])
        self.assertEqual(renewed["binding_id"], pilot["binding_id"])
        self.assertEqual(renewed["device_id"], pilot["device_id"])
        self.assertEqual(renewed["workspace_id"], pilot["workspace_id"])
        self.assertEqual(renewed["workspace_generation"], pilot["workspace_generation"])
        self.assertEqual(renewed["principal_id"], pilot["principal_id"])
        self.assertEqual(renewed["expires_at_ms"], self.now + 3_600_000)
        self.assertIsNone(renewed["revoked_at_ms"])

    def test_activate_replay_rehomes_without_new_authority(self) -> None:
        first = self.store.activate_node_workspace(
            device_id="device-alpha", principal_id=self.principal,
            workspace_id="workspace-autocad", workspace_generation="generation-1",
        )
        self.assertFalse(first["replayed"])
        with self.store._connection() as connection:
            decisions_before = connection.execute("SELECT COUNT(*) FROM scoped_pilot_decisions").fetchone()[0]
        second = self.store.activate_node_workspace(
            device_id="device-alpha", principal_id=self.principal,
            workspace_id="workspace-autocad", workspace_generation="generation-1",
        )
        self.assertTrue(second["replayed"])
        self.assertEqual(second["pilot_decision_id"], first["pilot_decision_id"])
        self.assertEqual(second["expires_at_ms"], first["expires_at_ms"])
        self.assertEqual(second["binding_id"], first["binding_id"])
        with self.store._connection() as connection:
            decisions_after = connection.execute("SELECT COUNT(*) FROM scoped_pilot_decisions").fetchone()[0]
        self.assertEqual(decisions_after, decisions_before)


class ReconnectTransitionTests(unittest.TestCase):
    def test_transition_kinds(self) -> None:
        self.assertEqual(reconnect_transition_kind(None, "ready"), "agent_start")
        self.assertEqual(reconnect_transition_kind("degraded", "ready"), "readiness_transition")
        self.assertEqual(reconnect_transition_kind("blocked", "ready"), "readiness_transition")
        self.assertEqual(reconnect_transition_kind("unknown", "ready"), "readiness_transition")
        self.assertIsNone(reconnect_transition_kind("ready", "ready"))
        self.assertIsNone(reconnect_transition_kind("ready", "degraded"))
        self.assertIsNone(reconnect_transition_kind(None, "degraded"))
        self.assertIsNone(reconnect_transition_kind("degraded", "degraded"))

    def test_authority_states(self) -> None:
        self.assertEqual(reconnect_authority_state([]), "unknown")
        self.assertEqual(reconnect_authority_state([{"binding_count": 1, "exec_binding_count": 1}]), "live")
        self.assertEqual(
            reconnect_authority_state([{"binding_count": 0, "exec_binding_count": 0},
                                       {"binding_count": 0, "exec_binding_count": 0}]),
            "no_live_binding",
        )
        # A binding without exec is not live exec authority, but it is also
        # not proof of "no binding": the node must not misreport it.
        self.assertEqual(reconnect_authority_state([{"binding_count": 1, "exec_binding_count": 0}]), "unknown")
        self.assertEqual(reconnect_authority_state([{"error": "CONTROL_PLANE_TIMEOUT"}]), "unknown")
        self.assertEqual(
            reconnect_authority_state([{"error": "CONTROL_PLANE_TIMEOUT"},
                                       {"binding_count": 1, "exec_binding_count": 1}]),
            "live",
        )
        self.assertEqual(
            reconnect_authority_state([{"binding_count": 0, "exec_binding_count": 0},
                                       {"error": "CONTROL_PLANE_TIMEOUT"}]),
            "unknown",
        )


class ConnectedAgentReconnectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.args = SimpleNamespace(
            config=str(Path(self.tempdir.name) / "node.json"),
            workspace_registry=str(Path(self.tempdir.name) / "workspaces.json"),
            project_root=self.tempdir.name,
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            data_root=self.tempdir.name,
            interval_seconds=15,
            max_backoff_seconds=30,
            max_iterations=1,
        )
        self.addCleanup(setattr, node_agent_module, "_LAST_RUNTIME_HEARTBEAT_PROJECTION", None)

    def _run(self, projections, observations) -> list[dict]:
        calls = {"count": 0}

        def iteration(_args, *, on_heartbeat_success):
            projection = projections[calls["count"]]
            calls["count"] += 1
            node_agent_module._LAST_RUNTIME_HEARTBEAT_PROJECTION = dict(projection)
            on_heartbeat_success()
            return []

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._config", return_value={}), \
             mock.patch("control_plane.node_agent._connected_agent_iteration", side_effect=iteration), \
             mock.patch("control_plane.node_agent._reconnect_authority_observations",
                        return_value=observations) as authority, \
             mock.patch("time.sleep"), \
             redirect_stdout(output):
            self.assertEqual(run_connected_agent(self.args), 0)
        lines = [json.loads(line) for line in output.getvalue().splitlines() if line.strip()]
        self.iteration_lines = [line for line in lines if line.get("execution") == "connected_agent_iteration"]
        self.authority_calls = authority.call_count
        return self.iteration_lines

    def test_agent_start_reports_reconnect_once(self) -> None:
        lines = self._run(
            [{"readiness": "ready"}],
            [{"workspace_id": "workspace-alpha", "workspace_generation": "generation-1",
              "binding_count": 1, "exec_binding_count": 1, "exec_enabled": True}],
        )
        self.assertEqual(len(lines), 1)
        reconnect = lines[0].get("reconnect")
        self.assertIsNotNone(reconnect)
        self.assertEqual(reconnect["kind"], "agent_start")
        self.assertIsNone(reconnect["previous_readiness"])
        self.assertEqual(reconnect["authority"], "live")
        self.assertEqual(self.authority_calls, 1)

    def test_readiness_transition_reports_reconnect_and_steady_state_does_not(self) -> None:
        self.args.max_iterations = 2
        lines = self._run(
            [{"readiness": "degraded"}, {"readiness": "ready"}],
            [{"workspace_id": "workspace-alpha", "workspace_generation": "generation-1",
              "binding_count": 0, "exec_binding_count": 0, "exec_enabled": False}],
        )
        self.assertEqual(len(lines), 2)
        self.assertNotIn("reconnect", lines[0])
        reconnect = lines[1].get("reconnect")
        self.assertIsNotNone(reconnect)
        self.assertEqual(reconnect["kind"], "readiness_transition")
        self.assertEqual(reconnect["previous_readiness"], "degraded")
        self.assertEqual(reconnect["authority"], "no_live_binding")
        self.assertEqual(self.authority_calls, 1)

    def test_steady_ready_does_not_revalidate_every_iteration(self) -> None:
        self.args.max_iterations = 2
        lines = self._run(
            [{"readiness": "ready"}, {"readiness": "ready"}],
            [{"workspace_id": "workspace-alpha", "workspace_generation": "generation-1",
              "binding_count": 1, "exec_binding_count": 1, "exec_enabled": True}],
        )
        self.assertEqual(len(lines), 2)
        self.assertIn("reconnect", lines[0])
        self.assertNotIn("reconnect", lines[1])
        self.assertEqual(self.authority_calls, 1)


if __name__ == "__main__":
    unittest.main()
