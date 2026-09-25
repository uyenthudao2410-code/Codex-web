from __future__ import annotations

import argparse
import errno
import io
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import sqlite3
import threading
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from contextlib import contextmanager, redirect_stderr, redirect_stdout

from control_plane.maintenance import main as maintenance_main
from control_plane.node_agent import (
    READ_ONLY_JOURNAL_SCHEMA_VERSION,
    _config,
    _journal_path,
    _pid_is_live,
    _read_only_poll_lock_path,
    _request,
    _read_journal,
    _read_only_bridge_request,
    _read_only_loop_policy_admission,
    _safe_bridge_result,
    _write_json_atomic,
    parse_dev_ui_status,
    poll,
    poll_read_only_once,
    read_only_policy_observation,
    run_connected_agent,
    run_read_only_agent,
    run_read_only_loop,
    recovery_identity_observation,
    recovery_read_only_bridge,
    recovery_runtime_status,
    runtime_heartbeat,
    observed_runtime_identity,
    runtime_heartbeat_projection,
    runtime_readiness,
    STANDING_POLICY_OBSERVATION_TTL_MS,
    main as node_agent_main,
)
from control_plane.store import (
    ConflictError,
    ControlPlaneStore,
    NotFoundError,
    PermissionError,
    SCHEMA_VERSION,
    ValidationError,
    create_recovery_restore_candidate,
    create_verified_backup,
    inspect_verified_snapshot,
)


FACADE_CONTRACT = {
    "schema_version": 3,
    "profile": "control-plane-read-only-queue-v2",
    "sha256": "f" * 64,
}


class _CommitFailingConnection:
    """Inject a post-write COMMIT failure while keeping SQLite rollback real."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def execute(self, statement: str, parameters: object = ()) -> sqlite3.Cursor:
        if statement.strip().upper() == "COMMIT":
            self._connection.execute("ROLLBACK")
            raise sqlite3.OperationalError("simulated durable commit failure")
        return self._connection.execute(statement, parameters)

    def __getattr__(self, name: str) -> object:
        return getattr(self._connection, name)


class ControlPlaneStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3", clock=lambda: self.now)
        enrolled = self.store.enroll_node(owner_id="owner_default", device_id="device-alpha", endpoint_id="endpoint-alpha", display_name="Windows Canary")
        self.node_secret = enrolled["node_secret"]
        self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-alpha",
            workspace_generation="generation-1",
            display_name="Canary workspace",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _register_workspace(
        self,
        *,
        device_id: str,
        workspace_id: str,
        workspace_generation: str,
        display_name: str,
    ) -> dict:
        return self.store.register_node_workspace(
            device_id=device_id,
            workspace_id=workspace_id,
            workspace_generation=workspace_generation,
            display_name=display_name,
            capabilities={"read": True, "write": False, "exec": False},
        )

    def _request(self) -> tuple[dict, dict]:
        binding = self.store.create_binding(owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha", workspace_generation="generation-1", display_name="Canary workspace")
        context = self.store.create_context(owner_id="owner_default", binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000)
        request = self.store.create_work_request(owner_id="owner_default", context_id=context["context_id"], objective="Inspect canary", criteria={"kind": "read_only"}, scope={"root": "canary"}, expires_at_ms=self.now + 30_000)
        return context, request

    def _ready_node(self, *, runtime_instance_id: str = "runtime-alpha", mcp_server_instance_id: str = "server-alpha", activation_epoch: str = "epoch-alpha", contract_version: str = "smart-v3") -> None:
        self.store.heartbeat(
            device_id="device-alpha",
            endpoint_id="endpoint-alpha",
            runtime_instance_id=runtime_instance_id,
            mcp_server_instance_id=mcp_server_instance_id,
            activation_epoch=activation_epoch,
            contract_version=contract_version,
            readiness="ready",
        )

    def _quarantine_service_file_read_unknown(self, *, local_handle: str = "") -> tuple[dict, dict, dict]:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Canary workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self._ready_node()
        self.store.set_admission_mode(mode="recovery")
        initial = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000,
            reason="Initial bounded-read canary",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        intent = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], path="README.md", start_line=1,
            max_lines=5, max_bytes=1024, idempotency_key="quarantined-file-read-001",
            facade_contract=FACADE_CONTRACT,
        )
        action = self.store.action(owner_id="owner_default", action_id=intent["action_id"])
        self.assertEqual(action["scoped_pilot_decision_id"], initial["decision_id"])
        delivery = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")[0]
        self.store.record_receipt(
            device_id="device-alpha", action_id=intent["action_id"],
            attempt_id=delivery["attempt_id"], receipt_state="unknown",
            local_handle=local_handle,
            payload={
                "schema_version": 1,
                "operation_kind": "control_plane_bounded_file_read",
                "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_FILE_READ_AGENT_EXCEPTION",
            },
        )
        self.store.quarantine_historical_unknown_actions(
            owner_id="owner_default", device_id="device-alpha",
            action_ids=[intent["action_id"]],
            declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT",
        )
        return binding, principal, action

    def test_node_policy_observation_is_compact_and_does_not_replace_on_legacy_heartbeat(self) -> None:
        policy = {
            "state": "enabled",
            "expires_at_ms": self.now + 60_000,
            "policy_sha256": "a" * 64,
            "reason": "",
        }
        self.store.heartbeat(
            device_id="device-alpha",
            endpoint_id="endpoint-alpha",
            runtime_instance_id="runtime-policy-0001",
            mcp_server_instance_id="server-policy-0001",
            activation_epoch="epoch-policy-0001",
            contract_version="sha256:" + "b" * 64,
            readiness="ready",
            policy_observation=policy,
        )
        observed = self.store.node_observation(owner_id="owner_default", device_id="device-alpha")
        self.assertEqual(observed["policy_state"], "enabled")
        self.assertEqual(observed["policy_expires_at_ms"], self.now + 60_000)
        self.assertEqual(observed["policy_sha256"], "a" * 64)
        self.assertIsNone(observed["policy_reason"])

        # An older node sends no policy projection.  Its runtime heartbeat must
        # not erase the last truthful local observation with a synthetic value.
        self.store.heartbeat(
            device_id="device-alpha",
            endpoint_id="endpoint-alpha",
            runtime_instance_id="runtime-policy-0002",
            mcp_server_instance_id="server-policy-0002",
            activation_epoch="epoch-policy-0002",
            contract_version="sha256:" + "c" * 64,
            readiness="degraded",
        )
        preserved = self.store.node_observation(owner_id="owner_default", device_id="device-alpha")
        self.assertEqual(preserved["policy_state"], "enabled")
        self.assertEqual(preserved["policy_sha256"], "a" * 64)

        self.store.heartbeat(
            device_id="device-alpha",
            endpoint_id="endpoint-alpha",
            runtime_instance_id="runtime-policy-0003",
            mcp_server_instance_id="server-policy-0003",
            activation_epoch="epoch-policy-0003",
            contract_version="sha256:" + "d" * 64,
            readiness="degraded",
            policy_observation={
                "state": "unavailable",
                "expires_at_ms": None,
                "policy_sha256": None,
                "reason": "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
            },
        )
        unavailable = self.store.node_observation(owner_id="owner_default", device_id="device-alpha")
        self.assertEqual(unavailable["policy_state"], "unavailable")
        self.assertEqual(unavailable["policy_reason"], "CONTROL_PLANE_BRIDGE_POLICY_MISSING")
        self.assertIsNone(unavailable["policy_sha256"])

        with self.assertRaises(ValidationError):
            self.store.heartbeat(
                device_id="device-alpha",
                endpoint_id="endpoint-alpha",
                runtime_instance_id="runtime-policy-invalid",
                mcp_server_instance_id="server-policy-invalid",
                activation_epoch="epoch-policy-invalid",
                contract_version="sha256:" + "e" * 64,
                readiness="ready",
                policy_observation={
                    "state": "enabled",
                    "expires_at_ms": self.now + 60_000,
                    "policy_sha256": "not-a-digest",
                    "reason": "",
                },
            )

    def test_workspace_registration_is_path_free_current_and_fences_replaced_generation(self) -> None:
        with self.assertRaisesRegex(ConflictError, "workspace registration is not current"):
            self.store.create_binding(
                owner_id="owner_default",
                device_id="device-alpha",
                workspace_id="workspace-rotation",
                workspace_generation="generation-rotation-0001",
                display_name="Rotating workspace",
            )

        registered = self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-rotation",
            workspace_generation="generation-rotation-0001",
            display_name="Rotating workspace",
        )
        self.assertFalse(registered["replayed"])
        self.assertEqual(registered["capabilities"], {"read": True, "write": False, "exec": False})
        self.assertNotIn("path", registered)
        replayed = self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-rotation",
            workspace_generation="generation-rotation-0001",
            display_name="Rotating workspace",
        )
        self.assertTrue(replayed["replayed"])

        binding = self.store.create_binding(
            owner_id="owner_default",
            device_id="device-alpha",
            workspace_id="workspace-rotation",
            workspace_generation="generation-rotation-0001",
            display_name="Owner label may be different from node label",
        )
        context = self.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )
        request = self.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="Fence old root before it is delivered",
            criteria={"kind": "read_only"},
            scope={"root": "rotation"},
            expires_at_ms=self.now + 30_000,
        )
        queued = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="workspace-rotation-action-0001",
            admission_reference="workspace-rotation-admission-0001",
            expires_at_ms=self.now + 20_000,
        )

        replaced = self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-rotation",
            workspace_generation="generation-rotation-0002",
            display_name="Rotating workspace v2",
        )
        self.assertFalse(replaced["replayed"])
        inventory = self.store.list_node_workspaces(owner_id="owner_default", device_id="device-alpha")
        old = next(item for item in inventory if item["workspace_generation"] == "generation-rotation-0001")
        current = next(item for item in inventory if item["workspace_generation"] == "generation-rotation-0002")
        self.assertEqual(old["retired_at_ms"], self.now)
        self.assertIsNone(current["retired_at_ms"])
        with self.assertRaises(ConflictError):
            self.store.binding(owner_id="owner_default", binding_id=binding["binding_id"])
        self.assertEqual(self.store.context(owner_id="owner_default", context_id=context["context_id"])["closed_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=queued["action_id"])["delivery_state"], "settled")
        with self.assertRaisesRegex(ConflictError, "workspace registration is not current"):
            self.store.create_binding(
                owner_id="owner_default",
                device_id="device-alpha",
                workspace_id="workspace-rotation",
                workspace_generation="generation-rotation-0001",
                display_name="Old generation",
            )
        with self.assertRaises(PermissionError):
            self.store.list_node_workspaces(owner_id="another_owner", device_id="device-alpha")

    def test_context_is_owner_and_binding_scoped(self) -> None:
        context, _ = self._request()
        with self.assertRaises(PermissionError):
            self.store.context(owner_id="another_owner", context_id=context["context_id"])
        self.assertEqual(context["device_id"], "device-alpha")
        self.assertEqual(context["workspace_id"], "workspace-alpha")

    def test_explicit_workspace_retirement_closes_context_and_only_settles_queued_actions(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default",
            device_id="device-alpha",
            workspace_id="workspace-alpha",
            workspace_generation="generation-1",
            display_name="Canary workspace",
        )
        context = self.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )
        request = self.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="Prove retirement never rewrites a dispatched action",
            criteria={"kind": "read_only"},
            scope={"root": "canary"},
            expires_at_ms=self.now + 30_000,
        )
        dispatched = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="workspace-retire-dispatched-0001",
            admission_reference="workspace-retire-dispatched-0001",
            expires_at_ms=self.now + 20_000,
        )
        queued = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="workspace-retire-queued-0001",
            admission_reference="workspace-retire-queued-0001",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        delivered = self.store.poll_actions(device_id="device-alpha", limit=1)
        self.assertEqual([item["action_id"] for item in delivered], [dispatched["action_id"]])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=dispatched["action_id"])["delivery_state"], "dispatch_unconfirmed")
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=queued["action_id"])["delivery_state"], "queued")

        retired = self.store.retire_node_workspace(
            device_id="device-alpha",
            workspace_id="workspace-alpha",
            workspace_generation="generation-1",
        )
        self.assertFalse(retired["replayed"])
        self.assertEqual(retired["retired_at_ms"], self.now)
        self.assertEqual(self.store.context(owner_id="owner_default", context_id=context["context_id"])["closed_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=queued["action_id"])["delivery_state"], "settled")
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=dispatched["action_id"])["delivery_state"], "dispatch_unconfirmed")
        replayed = self.store.retire_node_workspace(
            device_id="device-alpha",
            workspace_id="workspace-alpha",
            workspace_generation="generation-1",
        )
        self.assertTrue(replayed["replayed"])

    def test_mcp_access_grant_is_context_bound_expiring_and_revocable(self) -> None:
        context, _request = self._request()
        grant = self.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="openai-tunnel-fixture",
            expires_at_ms=self.now + 30_000,
        )
        self.assertRegex(grant["access_token"], r"^mcp_[A-Za-z0-9_-]{32,}$")
        self.assertNotIn("token_digest", grant)
        principal = self.store.authenticate_mcp_access_token(access_token=grant["access_token"])
        self.assertEqual(
            principal,
            {
                "grant_id": grant["grant_id"],
                "owner_id": "owner_default",
                "principal_id": "openai-tunnel-fixture",
                "context_id": context["context_id"],
                "expires_at_ms": self.now + 30_000,
            },
        )
        listed = self.store.list_mcp_access_grants(owner_id="owner_default")
        self.assertEqual(len(listed), 1)
        self.assertNotIn("token_digest", listed[0])
        self.assertNotIn("access_token", listed[0])
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_access_token(access_token="mcp_not-the-grant")

        revoked = self.store.revoke_mcp_access_grant(owner_id="owner_default", grant_id=grant["grant_id"])
        self.assertEqual(revoked["grant_id"], grant["grant_id"])
        self.assertEqual(revoked["revoked_at_ms"], self.now)
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_access_token(access_token=grant["access_token"])

        expired = self.store.create_mcp_access_grant(
            owner_id="owner_default",
            context_id=context["context_id"],
            principal_id="openai-tunnel-expiry-fixture",
            expires_at_ms=self.now + 40_000,
        )
        self.now += 40_000
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_access_token(access_token=expired["access_token"])

    def test_private_tunnel_service_grant_is_bounded_redacted_and_revocable(self) -> None:
        service = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        grant = self.store.create_mcp_service_grant(
            owner_id="owner_default",
            principal_id=service["principal_id"],
            expires_at_ms=self.now + 60_000,
            scopes=["control-plane.inventory", "control-plane.read", "control-plane.patch"],
        )
        self.assertRegex(grant["access_token"], r"^mcpsvc_[A-Za-z0-9_-]{32,}$")
        self.assertEqual(
            self.store.authenticate_mcp_service_token(access_token=grant["access_token"]),
            {
                "grant_id": grant["grant_id"],
                "owner_id": "owner_default",
                "principal_id": service["principal_id"],
                "expires_at_ms": self.now + 60_000,
                "scopes": frozenset({"control-plane.inventory", "control-plane.read", "control-plane.patch"}),
            },
        )
        listed = self.store.list_mcp_service_grants(owner_id="owner_default")
        self.assertEqual(len(listed), 1)
        self.assertNotIn("access_token", listed[0])
        self.assertNotIn("token_digest", listed[0])
        self.assertEqual(listed[0]["scopes"], ["control-plane.inventory", "control-plane.patch", "control-plane.read"])
        with self.store._connection() as connection:
            row = connection.execute(
                "SELECT token_digest FROM mcp_service_grants WHERE grant_id = ?", (grant["grant_id"],)
            ).fetchone()
        self.assertNotEqual(row["token_digest"], grant["access_token"])
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token="mcpsvc_not-the-grant")
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token="mcp_wrong-token-type")
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_access_token(access_token=grant["access_token"])
        with self.assertRaises(ValidationError):
            self.store.create_mcp_service_grant(
                owner_id="owner_default",
                principal_id=service["principal_id"],
                expires_at_ms=self.now + 30 * 24 * 60 * 60 * 1000 + 1,
                scopes=["control-plane.inventory"],
            )
        with self.assertRaises(PermissionError):
            self.store.revoke_mcp_service_grant(owner_id="another_owner", grant_id=grant["grant_id"])
        revoked = self.store.revoke_mcp_service_grant(owner_id="owner_default", grant_id=grant["grant_id"])
        self.assertEqual(revoked["revoked_at_ms"], self.now)
        self.assertNotIn("access_token", revoked)
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token=grant["access_token"])

        expiring = self.store.create_mcp_service_grant(
            owner_id="owner_default",
            principal_id=service["principal_id"],
            expires_at_ms=self.now + 1,
            scopes=["control-plane.inventory"],
        )
        self.now += 1
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token=expiring["access_token"])

    def test_private_tunnel_service_grant_renewal_preserves_bearer_and_scopes(self) -> None:
        service = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        grant = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=service["principal_id"],
            expires_at_ms=self.now + 60_000,
            scopes=["control-plane.inventory", "control-plane.read", "control-plane.patch"],
        )
        renewed = self.store.renew_mcp_service_grant(
            owner_id="owner_default", grant_id=grant["grant_id"], expires_at_ms=self.now + 120_000,
        )
        self.assertEqual(renewed["expires_at_ms"], self.now + 120_000)
        self.assertEqual(renewed["scopes"], ["control-plane.inventory", "control-plane.patch", "control-plane.read"])
        self.assertEqual(
            self.store.authenticate_mcp_service_token(access_token=grant["access_token"])["expires_at_ms"],
            self.now + 120_000,
        )
        with self.assertRaises(ValidationError):
            self.store.renew_mcp_service_grant(
                owner_id="owner_default", grant_id=grant["grant_id"], expires_at_ms=self.now + 30_000,
            )
        self.now += 120_000
        with self.assertRaises(ConflictError):
            self.store.renew_mcp_service_grant(
                owner_id="owner_default", grant_id=grant["grant_id"], expires_at_ms=self.now + 60_000,
            )

    def test_service_grant_scopes_are_immutable_and_invalid_scopes_fail_closed(self) -> None:
        service = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        inventory = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=service["principal_id"],
            expires_at_ms=self.now + 60_000, scopes=["control-plane.inventory"],
        )
        patch = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=service["principal_id"],
            expires_at_ms=self.now + 60_000,
            scopes=["control-plane.patch", "control-plane.read", "control-plane.inventory"],
        )
        self.assertEqual(inventory["scopes"], ["control-plane.inventory"])
        self.assertEqual(patch["scopes"], ["control-plane.inventory", "control-plane.patch", "control-plane.read"])
        with self.assertRaises(ValidationError):
            self.store.create_mcp_service_grant(
                owner_id="owner_default", principal_id=service["principal_id"],
                expires_at_ms=self.now + 60_000,
                scopes=["control-plane.inventory", "control-plane.patch"],
            )
        # A later configuration change can only affect a newly issued grant.
        self.assertEqual(
            self.store.authenticate_mcp_service_token(access_token=inventory["access_token"])["scopes"],
            frozenset({"control-plane.inventory"}),
        )
        self.assertEqual(
            self.store.authenticate_mcp_service_token(access_token=patch["access_token"])["scopes"],
            frozenset({"control-plane.inventory", "control-plane.read", "control-plane.patch"}),
        )
        for invalid in (
            [], ["control-plane.patch"], ["control-plane.inventory", "control-plane.inventory"],
            ["control-plane.inventory", "control-plane.exec"], "control-plane.inventory",
        ):
            with self.subTest(scopes=invalid), self.assertRaises(ValidationError):
                self.store.create_mcp_service_grant(
                    owner_id="owner_default", principal_id=service["principal_id"],
                    expires_at_ms=self.now + 60_000, scopes=invalid,
                )
        with self.store._connection() as connection:
            connection.execute(
                "UPDATE mcp_service_grants SET scopes_json = ? WHERE grant_id = ?",
                ('["control-plane.exec"]', inventory["grant_id"]),
            )
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token=inventory["access_token"])

    def test_service_principal_is_not_an_oauth_account_and_revocation_stops_grants(self) -> None:
        oauth = self.store.link_oauth_principal(
            owner_id="owner_default", issuer="https://accounts.example.com", subject="user-one"
        )
        service = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self.assertEqual(
            [item["principal_id"] for item in self.store.list_oauth_principals(owner_id="owner_default")],
            [oauth["principal_id"]],
        )
        self.assertEqual(
            self.store.resolve_oauth_principal(issuer="https://accounts.example.com", subject="user-one"),
            {"owner_id": "owner_default", "principal_id": oauth["principal_id"]},
        )
        with self.assertRaises(NotFoundError):
            self.store.revoke_oauth_principal(owner_id="owner_default", principal_id=service["principal_id"])
        with self.assertRaises(NotFoundError):
            self.store.create_mcp_service_grant(
                owner_id="owner_default", principal_id=oauth["principal_id"],
                expires_at_ms=self.now + 60_000,
                scopes=["control-plane.inventory"],
            )
        grant = self.store.create_mcp_service_grant(
            owner_id="owner_default", principal_id=service["principal_id"],
            expires_at_ms=self.now + 60_000,
            scopes=["control-plane.inventory"],
        )
        context, _ = self._request()
        # A shared service grant is identity, not admission. Even global open
        # cannot create its task without an exact scoped pilot decision.
        with self.assertRaises(ConflictError):
            self.store.create_mcp_task_session(
                owner_id="owner_default", principal_id=service["principal_id"],
                binding_id=context["binding_id"], label="Shared tunnel task",
                idempotency_key="service-task-0001",
            )
        principals = self.store.list_private_tunnel_service_principals(owner_id="owner_default")
        self.assertEqual([item["principal_id"] for item in principals], [service["principal_id"]])
        self.assertNotIn("subject_digest", principals[0])
        self.assertNotIn("issuer", principals[0])
        self.store.revoke_private_tunnel_service_principal(
            owner_id="owner_default", principal_id=service["principal_id"]
        )
        with self.assertRaises(PermissionError):
            self.store.authenticate_mcp_service_token(access_token=grant["access_token"])
        with self.assertRaises(ConflictError):
            self.store.create_mcp_service_grant(
                owner_id="owner_default", principal_id=service["principal_id"],
                expires_at_ms=self.now + 60_000,
                scopes=["control-plane.inventory"],
            )

    def test_two_bound_nodes_with_the_same_workspace_id_poll_only_their_own_action(self) -> None:
        bravo = self.store.enroll_node(
            owner_id="owner_default",
            device_id="device-bravo",
            endpoint_id="endpoint-bravo",
            display_name="Bravo node",
        )
        self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-shared-path",
            workspace_generation="generation-shared-0001",
            display_name="Alpha shared path",
        )
        self._register_workspace(
            device_id=bravo["device_id"],
            workspace_id="workspace-shared-path",
            workspace_generation="generation-shared-0001",
            display_name="Bravo shared path",
        )
        alpha_binding = self.store.create_binding(
            owner_id="owner_default",
            device_id="device-alpha",
            workspace_id="workspace-shared-path",
            workspace_generation="generation-shared-0001",
            display_name="Alpha shared path",
        )
        bravo_binding = self.store.create_binding(
            owner_id="owner_default",
            device_id=bravo["device_id"],
            workspace_id="workspace-shared-path",
            workspace_generation="generation-shared-0001",
            display_name="Bravo shared path",
        )
        alpha_context = self.store.create_context(
            owner_id="owner_default",
            binding_id=alpha_binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )
        bravo_context = self.store.create_context(
            owner_id="owner_default",
            binding_id=bravo_binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )
        alpha_request = self.store.create_work_request(
            owner_id="owner_default",
            context_id=alpha_context["context_id"],
            objective="Inspect alpha binding",
            criteria={"kind": "read_only"},
            scope={"root": "shared"},
            expires_at_ms=self.now + 30_000,
        )
        bravo_request = self.store.create_work_request(
            owner_id="owner_default",
            context_id=bravo_context["context_id"],
            objective="Inspect bravo binding",
            criteria={"kind": "read_only"},
            scope={"root": "shared"},
            expires_at_ms=self.now + 30_000,
        )
        alpha_action = self.store.seal_action(
            owner_id="owner_default",
            request_id=alpha_request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-shared-path-alpha-0001",
            admission_reference="admission-shared-path-alpha-0001",
            expires_at_ms=self.now + 20_000,
        )
        bravo_action = self.store.seal_action(
            owner_id="owner_default",
            request_id=bravo_request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-shared-path-bravo-0001",
            admission_reference="admission-shared-path-bravo-0001",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        self.store.heartbeat(
            device_id=bravo["device_id"],
            endpoint_id="endpoint-bravo",
            runtime_instance_id="runtime-bravo",
            mcp_server_instance_id="server-bravo",
            activation_epoch="epoch-bravo",
            contract_version="smart-v3",
            readiness="ready",
        )

        alpha_delivered = self.store.poll_actions(device_id="device-alpha")
        bravo_delivered = self.store.poll_actions(device_id=bravo["device_id"])
        self.assertEqual([item["action_id"] for item in alpha_delivered], [alpha_action["action_id"]])
        self.assertEqual([item["action_id"] for item in bravo_delivered], [bravo_action["action_id"]])
        self.assertEqual(alpha_delivered[0]["device_id"], "device-alpha")
        self.assertEqual(bravo_delivered[0]["device_id"], bravo["device_id"])
        self.assertEqual(alpha_delivered[0]["workspace_id"], bravo_delivered[0]["workspace_id"])
        self.assertEqual(alpha_delivered[0]["workspace_generation"], bravo_delivered[0]["workspace_generation"])
        self.assertNotEqual(alpha_delivered[0]["binding_id"], bravo_delivered[0]["binding_id"])
        self.assertNotEqual(alpha_delivered[0]["context_id"], bravo_delivered[0]["context_id"])

    def test_observation_inventory_is_owner_scoped_and_omits_node_credentials(self) -> None:
        context, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-0020",
            admission_reference="admission-0020",
            expires_at_ms=self.now + 20_000,
        )
        node = self.store.node_observation(owner_id="owner_default", device_id="device-alpha")
        self.assertEqual(node["device_id"], "device-alpha")
        self.assertNotIn("credential_hash", node)
        self.assertNotIn("node_secret", node)
        self.assertEqual([item["device_id"] for item in self.store.list_nodes(owner_id="owner_default")], ["device-alpha"])
        self.assertEqual(self.store.list_nodes(owner_id="another_owner"), [])
        self.assertEqual([item["context_id"] for item in self.store.list_contexts(owner_id="owner_default")], [context["context_id"]])
        self.assertEqual([item["request_id"] for item in self.store.list_work_requests(owner_id="owner_default")], [request["request_id"]])
        observed_request = self.store.work_request_observation(owner_id="owner_default", request_id=request["request_id"])
        self.assertEqual([item["action_id"] for item in observed_request["actions"]], [action["action_id"]])
        self.assertNotIn("arguments_json", observed_request["actions"][0])
        self.assertNotIn("admission_reference", observed_request["actions"][0])
        lifecycle = self.store.list_action_lifecycle(owner_id="owner_default")
        self.assertEqual([item["action_id"] for item in lifecycle], [action["action_id"]])
        self.assertEqual(lifecycle[0]["delivery_state"], "queued")
        self.assertFalse(lifecycle[0]["approved_patch_candidate"])
        self.assertEqual(lifecycle[0]["receipt_count"], 0)
        self.assertIsNone(lifecycle[0]["latest_receipt_state"])
        self.assertNotIn("arguments_json", lifecycle[0])
        self.assertNotIn("admission_reference", lifecycle[0])
        self.assertNotIn("local_handle", lifecycle[0])
        self.assertEqual(self.store.list_action_lifecycle(owner_id="another_owner"), [])
        with self.assertRaises(PermissionError):
            self.store.node_observation(owner_id="another_owner", device_id="device-alpha")
        with self.assertRaises(PermissionError):
            self.store.work_request_observation(owner_id="another_owner", request_id=request["request_id"])

    def test_sealed_action_replays_only_when_immutable_payload_matches(self) -> None:
        _, request = self._request()
        first = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)
        replay = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)
        self.assertEqual(first["action_id"], replay["action_id"])
        with self.assertRaises(ConflictError):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "other"}, idempotency_key="action-key-0001", admission_reference="admission-0001", expires_at_ms=self.now + 20_000)

    def test_mcp_read_only_intent_is_atomic_fixed_and_replays_only_exactly(self) -> None:
        context, _ = self._request()
        request = self.store.create_work_request(
            owner_id="owner_default",
            context_id=context["context_id"],
            objective="A generic action must not impersonate the fixed read-only lane.",
            criteria={"kind": "read_only"},
            scope={"kind": "workspace_context"},
            expires_at_ms=self.now + 30_000,
        )
        with self.assertRaisesRegex(ValidationError, "reserved for the MCP facade"):
            self.store.seal_action(
                owner_id="owner_default",
                request_id=request["request_id"],
                tool_name="workspace_context",
                arguments={"detail": "compact", "max_entries": 1},
                idempotency_key="generic-impersonation-0001",
                admission_reference="mcp_facade:" + "f" * 64,
                expires_at_ms=self.now + 20_000,
            )
        first = self.store.request_mcp_read_only_workspace_context(
            owner_id="owner_default",
            context_id=context["context_id"],
            idempotency_key="mcp-read-only-intent-0001",
            expires_at_ms=self.now + 20_000,
            facade_contract=FACADE_CONTRACT,
        )
        self.assertFalse(first["replayed"])
        action = self.store.action(owner_id="owner_default", action_id=first["action_id"])
        self.assertEqual(action["tool_name"], "workspace_context")
        self.assertEqual(json.loads(action["arguments_json"]), {"detail": "compact", "max_entries": 1})
        self.assertEqual(action["admission_reference"], f"mcp_facade:{first['intent_digest']}")
        self.assertEqual(self.store.health()["counts"]["mcp_read_only_intents"], 1)
        self.assertEqual(self.store.health()["counts"]["work_requests"], 3)
        self.assertEqual(self.store.health()["counts"]["actions"], 1)

        replay = self.store.request_mcp_read_only_workspace_context(
            owner_id="owner_default",
            context_id=context["context_id"],
            idempotency_key="mcp-read-only-intent-0001",
            expires_at_ms=self.now + 20_000,
            facade_contract=FACADE_CONTRACT,
        )
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["request_id"], first["request_id"])
        self.assertEqual(replay["action_id"], first["action_id"])
        with self.assertRaisesRegex(ConflictError, "idempotency key"):
            self.store.request_mcp_read_only_workspace_context(
                owner_id="owner_default",
                context_id=context["context_id"],
                idempotency_key="mcp-read-only-intent-0001",
                expires_at_ms=self.now + 20_001,
                facade_contract=FACADE_CONTRACT,
            )
        self.assertEqual(self.store.health()["counts"]["mcp_read_only_intents"], 1)
        self.assertEqual(self.store.health()["counts"]["actions"], 1)

        self._ready_node()
        delivered = self.store.poll_actions(device_id="device-alpha")
        self.assertEqual([item["action_id"] for item in delivered], [first["action_id"]])
        self.assertEqual(delivered[0]["mcp_read_only_intent_digest"], first["intent_digest"])
        self.assertEqual(delivered[0]["admission_reference"], f"mcp_facade:{first['intent_digest']}")
        self.assertEqual(delivered[0]["mcp_facade_schema_version"], FACADE_CONTRACT["schema_version"])
        self.assertEqual(delivered[0]["mcp_facade_profile"], FACADE_CONTRACT["profile"])
        self.assertEqual(delivered[0]["mcp_facade_contract_sha256"], FACADE_CONTRACT["sha256"])

        self.store.set_admission_mode(mode="recovery")
        with self.assertRaisesRegex(ConflictError, "recovery"):
            self.store.request_mcp_read_only_workspace_context(
                owner_id="owner_default",
                context_id=context["context_id"],
                idempotency_key="mcp-read-only-intent-0002",
                expires_at_ms=self.now + 20_000,
                facade_contract=FACADE_CONTRACT,
            )
        self.assertEqual(self.store.health()["counts"]["mcp_read_only_intents"], 1)
        self.assertEqual(self.store.health()["counts"]["actions"], 1)

    def test_commit_failure_does_not_ack_or_persist_the_fixed_read_only_intent(self) -> None:
        context, _ = self._request()
        original_connection = self.store._connection

        @contextmanager
        def commit_failure_connection():
            with original_connection() as connection:
                yield _CommitFailingConnection(connection)

        with mock.patch.object(self.store, "_connection", commit_failure_connection):
            with self.assertRaisesRegex(sqlite3.OperationalError, "simulated durable commit failure"):
                self.store.request_mcp_read_only_workspace_context(
                    owner_id="owner_default",
                    context_id=context["context_id"],
                    idempotency_key="action-key-commit-failure-0001",
                    expires_at_ms=self.now + 20_000,
                    facade_contract=FACADE_CONTRACT,
                )

        with self.store._connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM mcp_read_only_intents").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM actions").fetchone()[0], 0)
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM events WHERE event_type = 'mcp_read_only_intent_created'"
                ).fetchone()[0],
                0,
            )
        self._ready_node()
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])

    def test_poll_requires_fresh_attributable_ready_node_and_receipt_replays(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0002", admission_reference="admission-0002", expires_at_ms=self.now + 20_000)
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        self._ready_node()
        polled = self.store.poll_actions(device_id="device-alpha")
        self.assertEqual([item["action_id"] for item in polled], [action["action_id"]])
        self.assertEqual(polled[0]["delivery_state"], "dispatch_unconfirmed")
        self.assertTrue(polled[0]["attempt_id"].startswith("try_"))
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        receipt = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=polled[0]["attempt_id"], receipt_state="completed", local_handle="cmd-1", payload={"proof": "ok"})
        self.assertEqual(receipt["delivery_state"], "settled")
        self.assertFalse(receipt["replayed"])
        replay = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=polled[0]["attempt_id"], receipt_state="completed", local_handle="cmd-1", payload={"proof": "ok"})
        self.assertEqual(replay["receipt_id"], receipt["receipt_id"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        observation = self.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(len(observation["attempts"]), 1)
        self.assertEqual(len(observation["receipts"]), 1)

    def test_ordinary_poll_does_not_dequeue_an_action_without_a_receipt_lane(self) -> None:
        config_path = Path(self.tempdir.name) / "ordinary-poll-node.json"
        config_path.write_text(json.dumps({
            "server_url": "http://127.0.0.1:8765",
            "device_id": "device-alpha",
            "node_secret": "node-secret-ordinary-poll-0001",
        }), encoding="utf-8")
        output = io.StringIO()
        with mock.patch("control_plane.node_agent._request") as request, redirect_stdout(output):
            self.assertEqual(poll(SimpleNamespace(config=str(config_path), limit=10)), 0)
        request.assert_not_called()
        self.assertEqual(json.loads(output.getvalue()), {
            "received_action_ids": [],
            "execution": "not_implemented",
            "code": "POLL_EXECUTION_DISABLED",
        })

    def test_cross_node_receipt_is_refused(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0003", admission_reference="admission-0003", expires_at_ms=self.now + 20_000)
        with self.assertRaises(PermissionError):
            self.store.record_receipt(device_id="device-other", action_id=action["action_id"], attempt_id="try-other-0001", receipt_state="accepted", local_handle="handle-other", payload={})

    def test_unknown_tool_and_receipt_before_poll_are_refused(self) -> None:
        _, request = self._request()
        with self.assertRaisesRegex(Exception, "smart-v3"):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="arbitrary_shell", arguments={}, idempotency_key="action-key-0004", admission_reference="admission-0004", expires_at_ms=self.now + 20_000)
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0005", admission_reference="admission-0005", expires_at_ms=self.now + 20_000)
        with self.assertRaises(ConflictError):
            self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id="try-alpha-0001", receipt_state="accepted", local_handle="handle-alpha", payload={})

    def test_unknown_receipt_requires_terminal_reconciliation_and_never_redelivers(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0006", admission_reference="admission-0006", expires_at_ms=self.now + 20_000)
        self._ready_node()
        attempt = self.store.poll_actions(device_id="device-alpha")[0]["attempt_id"]
        unknown = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=attempt, receipt_state="unknown", local_handle="", payload={"reason": "network_lost_after_admission"})
        self.assertEqual(unknown["delivery_state"], "reconcile_required")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        with self.assertRaises(ConflictError):
            self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=attempt, receipt_state="accepted", local_handle="handle-alpha", payload={})
        terminal = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=attempt, receipt_state="failed", local_handle="", payload={"reason": "confirmed_not_executed"})
        self.assertEqual(terminal["delivery_state"], "settled")

    def test_operator_can_quarantine_exact_historical_unknown_without_settling_or_retrying(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-quarantine-unknown-0001",
            admission_reference="admission-quarantine-unknown-0001",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        attempt = self.store.poll_actions(device_id="device-alpha")[0]["attempt_id"]
        self.store.record_receipt(
            device_id="device-alpha",
            action_id=action["action_id"],
            attempt_id=attempt,
            receipt_state="unknown",
            local_handle="",
            payload={"reason": "historic_read_effect_unknown"},
        )

        quarantined = self.store.quarantine_historical_unknown_actions(
            owner_id="owner_default",
            device_id="device-alpha",
            action_ids=[action["action_id"]],
            declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT",
        )
        self.assertEqual(quarantined["actions"], [{
            "action_id": action["action_id"],
            "disposition": "quarantined_unknown",
            "reconciled_at_ms": self.now,
        }])
        observation = self.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "reconcile_required")
        self.assertEqual([receipt["receipt_state"] for receipt in observation["receipts"]], ["unknown"])
        self.assertEqual(observation["reconciliation"]["disposition"], "quarantined_unknown")
        self.assertEqual(observation["reconciliation"]["declaration"], "HISTORICAL_READ_ONLY_UNKNOWN_EFFECT")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        lifecycle = self.store.list_action_lifecycle(owner_id="owner_default")
        self.assertEqual(lifecycle[0]["reconciliation_disposition"], "quarantined_unknown")
        health = self.store.health()
        self.assertEqual(health["unresolved_action_count"], 1)
        self.assertEqual(health["quarantined_unknown_action_count"], 1)
        self.assertEqual(health["unquarantined_unresolved_action_count"], 0)
        service_principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=service_principal["principal_id"],
                binding_id=self.store.action(owner_id="owner_default", action_id=action["action_id"])["binding_id"],
                expires_at_ms=self.now + 120_000,
                reason="Generic workspace context unknown must remain blocking",
            )

        snapshot_path = Path(self.tempdir.name) / "quarantined-unknown.sqlite3"
        snapshot = self.store.backup_to(snapshot_path)
        inspected = inspect_verified_snapshot(snapshot_path, expected_sha256=str(snapshot["snapshot_sha256"]))
        self.assertEqual(inspected["unresolved_action_count"], 1)
        self.assertEqual(inspected["quarantined_unknown_action_count"], 1)
        self.assertEqual(inspected["unquarantined_unresolved_action_count"], 0)

        with self.assertRaises(ConflictError):
            self.store.quarantine_historical_unknown_actions(
                owner_id="owner_default",
                device_id="device-alpha",
                action_ids=[action["action_id"]],
                declaration="HISTORICAL_READ_ONLY_UNKNOWN_EFFECT",
            )
        with self.assertRaises(ValidationError):
            self.store.quarantine_historical_unknown_actions(
                owner_id="owner_default",
                device_id="device-alpha",
                action_ids=[action["action_id"]],
                declaration="a different declaration",
            )

    def test_operator_can_quarantine_expired_unobserved_dispatch_without_receipt(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-unobserved-dispatch-0001",
            admission_reference="admission-unobserved-dispatch-0001",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        attempt = self.store.poll_actions(device_id="device-alpha")[0]
        self.now += 30_000
        disposition = self.store.quarantine_historical_unobserved_dispatches(
            owner_id="owner_default",
            device_id="device-alpha",
            action_ids=[action["action_id"]],
            declaration="HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH",
            rationale="expired legacy read-only dispatch; node policy/runtime unavailable for observation",
        )
        self.assertEqual(disposition["actions"][0]["attempt_id"], attempt["attempt_id"])
        observation = self.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "dispatch_unconfirmed")
        self.assertEqual(observation["receipts"], [])
        self.assertEqual(observation["dispatch_disposition"]["disposition"], "historical_read_only_unobserved_dispatch")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        health = self.store.health()
        self.assertEqual(health["unresolved_action_count"], 1)
        self.assertEqual(health["historical_unobserved_dispatch_count"], 1)
        self.assertEqual(health["quarantined_unresolved_action_count"], 1)
        self.assertEqual(health["unquarantined_unresolved_action_count"], 0)

        with self.assertRaises(ConflictError):
            self.store.quarantine_historical_unobserved_dispatches(
                owner_id="owner_default",
                device_id="device-alpha",
                action_ids=[action["action_id"]],
                declaration="HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH",
                rationale="duplicate",
            )

    def test_unobserved_dispatch_requires_expiry_and_unavailable_node(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-unobserved-dispatch-0002",
            admission_reference="admission-unobserved-dispatch-0002",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        self.store.poll_actions(device_id="device-alpha")
        with self.assertRaises(ConflictError):
            self.store.quarantine_historical_unobserved_dispatches(
                owner_id="owner_default",
                device_id="device-alpha",
                action_ids=[action["action_id"]],
                declaration="HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH",
                rationale="not expired and node still dispatchable",
            )

    def test_legacy_rotate_credential_path_fails_closed(self) -> None:
        with self.assertRaises(ConflictError):
            self.store.rotate_node_credential(owner_id="owner_default", device_id="device-alpha")

    def test_cancel_or_revoke_refuses_never_sent_action_without_settling_sent_action(self) -> None:
        _, request = self._request()
        queued = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0010", admission_reference="admission-0010", expires_at_ms=self.now + 20_000)
        canceled = self.store.cancel_work_request(owner_id="owner_default", request_id=request["request_id"])
        self.assertEqual(canceled["canceled_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=queued["action_id"])["delivery_state"], "settled")
        with self.assertRaises(ConflictError):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "identity"}, idempotency_key="action-key-0011", admission_reference="admission-0011", expires_at_ms=self.now + 20_000)

        _, second_request = self._request()
        sent = self.store.seal_action(owner_id="owner_default", request_id=second_request["request_id"], tool_name="workspace_context", arguments={"mode": "identity"}, idempotency_key="action-key-0012", admission_reference="admission-0012", expires_at_ms=self.now + 20_000)
        self._ready_node()
        self.assertEqual(self.store.poll_actions(device_id="device-alpha")[0]["action_id"], sent["action_id"])
        revoked = self.store.revoke_node(owner_id="owner_default", device_id="device-alpha")
        self.assertEqual(revoked["revoked_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=sent["action_id"])["delivery_state"], "dispatch_unconfirmed")
        with self.assertRaises(ConflictError):
            self.store.seal_action(owner_id="owner_default", request_id=second_request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0014", admission_reference="admission-0014", expires_at_ms=self.now + 20_000)

    def test_revoked_binding_blocks_new_work_and_refuses_queued_actions(self) -> None:
        context, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0013", admission_reference="admission-0013", expires_at_ms=self.now + 20_000)
        revoked = self.store.revoke_binding(owner_id="owner_default", binding_id=context["binding_id"])
        self.assertEqual(revoked["revoked_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=action["action_id"])["delivery_state"], "settled")
        with self.assertRaises(ConflictError):
            self.store.create_work_request(owner_id="owner_default", context_id=context["context_id"], objective="must not be accepted", criteria={}, scope={}, expires_at_ms=self.now + 10_000)

    def test_closed_context_refuses_queued_actions(self) -> None:
        context, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0015", admission_reference="admission-0015", expires_at_ms=self.now + 20_000)
        closed = self.store.close_context(owner_id="owner_default", context_id=context["context_id"])
        self.assertEqual(closed["closed_at_ms"], self.now)
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=action["action_id"])["delivery_state"], "settled")

    def test_revoked_node_blocks_fresh_context_and_work_request_admission(self) -> None:
        self._register_workspace(
            device_id="device-alpha",
            workspace_id="workspace-revoked-node",
            workspace_generation="generation-revoked-node",
            display_name="Revoked-node workspace",
        )
        binding = self.store.create_binding(
            owner_id="owner_default",
            device_id="device-alpha",
            workspace_id="workspace-revoked-node",
            workspace_generation="generation-revoked-node",
            display_name="Revoked-node workspace",
        )
        context = self.store.create_context(
            owner_id="owner_default",
            binding_id=binding["binding_id"],
            expires_at_ms=self.now + 60_000,
        )
        self.store.revoke_node(owner_id="owner_default", device_id="device-alpha")
        with self.assertRaisesRegex(ConflictError, "node is revoked"):
            self.store.create_context(
                owner_id="owner_default",
                binding_id=binding["binding_id"],
                expires_at_ms=self.now + 60_000,
            )
        with self.assertRaisesRegex(ConflictError, "node is revoked"):
            self.store.create_work_request(
                owner_id="owner_default",
                context_id=context["context_id"],
                objective="Must not attach new work to a revoked node",
                criteria={"kind": "read_only"},
                scope={"root": "canary"},
                expires_at_ms=self.now + 30_000,
            )

    def test_recovery_mode_blocks_new_admission_but_keeps_late_receipts_reconcilable(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0017", admission_reference="admission-0017", expires_at_ms=self.now + 20_000)
        self._ready_node()
        self.assertEqual(self.store.set_admission_mode(mode="recovery")["admission_mode"], "recovery")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=action["action_id"])["delivery_state"], "queued")
        with self.assertRaises(ConflictError):
            self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "identity"}, idempotency_key="action-key-0018", admission_reference="admission-0018", expires_at_ms=self.now + 20_000)
        self.assertEqual(self.store.set_admission_mode(mode="open")["admission_mode"], "open")
        attempt = self.store.poll_actions(device_id="device-alpha")[0]["attempt_id"]
        self.store.set_admission_mode(mode="recovery")
        receipt = self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=attempt, receipt_state="completed", local_handle="cmd-recovery-1", payload={"proof": "late"})
        self.assertEqual(receipt["delivery_state"], "settled")

    def test_recovery_mode_and_unresolved_receipt_survive_store_reopen(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0019", admission_reference="admission-0019", expires_at_ms=self.now + 20_000)
        self._ready_node()
        attempt = self.store.poll_actions(device_id="device-alpha")[0]["attempt_id"]
        self.store.record_receipt(device_id="device-alpha", action_id=action["action_id"], attempt_id=attempt, receipt_state="unknown", local_handle="", payload={"reason": "awaiting_reconcile"})
        self.store.set_admission_mode(mode="recovery")
        reopened = ControlPlaneStore(self.store.path, clock=lambda: self.now)
        self.assertEqual(reopened.admission_status()["admission_mode"], "recovery")
        self.assertEqual(reopened.poll_actions(device_id="device-alpha"), [])
        observation = reopened.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "reconcile_required")
        self.assertEqual(len(observation["attempts"]), 1)
        self.assertEqual(len(observation["receipts"]), 1)

    def test_expired_queued_action_is_refused_without_delivery(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0007", admission_reference="admission-0007", expires_at_ms=self.now + 10_000)
        self._ready_node()
        self.now += 10_001
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=action["action_id"])["delivery_state"], "settled")

    def test_unverified_or_stale_ready_heartbeat_does_not_admit_delivery(self) -> None:
        _, request = self._request()
        first = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0008", admission_reference="admission-0008", expires_at_ms=self.now + 20_000)
        self._ready_node(runtime_instance_id="unreported")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=first["action_id"])["delivery_state"], "queued")

        self._ready_node(mcp_server_instance_id="unreported")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])

        self._ready_node()
        second = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "identity"}, idempotency_key="action-key-0009", admission_reference="admission-0009", expires_at_ms=self.now + 20_000)
        self.store.heartbeat_max_age_ms = 10
        self.now += 11
        self.assertEqual(self.store.poll_actions(device_id="device-alpha"), [])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=second["action_id"])["delivery_state"], "queued")

    def test_legacy_receipts_table_is_migrated_without_claiming_new_provenance(self) -> None:
        legacy_path = Path(self.tempdir.name) / "legacy.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                "CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY, action_id TEXT NOT NULL, device_id TEXT NOT NULL, local_handle TEXT, receipt_state TEXT NOT NULL, payload_json TEXT NOT NULL, received_at_ms INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT INTO receipts VALUES ('rcpt-legacy-001', 'act-legacy-001', 'device-legacy-001', 'handle-legacy', 'completed', '{}', 1700000000000)"
            )
            connection.commit()
        finally:
            connection.close()
        ControlPlaneStore(legacy_path, clock=lambda: self.now)
        connection = sqlite3.connect(legacy_path)
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(receipts)")}
            self.assertIn("receipt_digest", columns)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertIn("mcp_server_instance_id", {row[1] for row in connection.execute("PRAGMA table_info(nodes)")})
            self.assertEqual(
                connection.execute("SELECT receipt_digest FROM receipts WHERE receipt_id = 'rcpt-legacy-001'").fetchone()[0],
                "legacy:rcpt-legacy-001",
            )
        finally:
            connection.close()

    def test_v4_node_observations_gain_the_exact_mcp_server_identity_column(self) -> None:
        legacy_path = Path(self.tempdir.name) / "v4-nodes.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                "CREATE TABLE nodes (device_id TEXT PRIMARY KEY, endpoint_id TEXT NOT NULL, owner_id TEXT NOT NULL, display_name TEXT NOT NULL, credential_hash TEXT NOT NULL, credential_created_at_ms INTEGER NOT NULL, credential_generation INTEGER NOT NULL DEFAULT 1, revoked_at_ms INTEGER, last_seen_at_ms INTEGER, runtime_instance_id TEXT, activation_epoch TEXT, contract_version TEXT, readiness TEXT NOT NULL DEFAULT 'unknown')"
            )
            connection.execute("PRAGMA user_version = 4")
            connection.commit()
        finally:
            connection.close()
        ControlPlaneStore(legacy_path, clock=lambda: self.now)
        connection = sqlite3.connect(legacy_path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertIn("mcp_server_instance_id", {row[1] for row in connection.execute("PRAGMA table_info(nodes)")})
            self.assertIn("policy_state", {row[1] for row in connection.execute("PRAGMA table_info(nodes)")})
        finally:
            connection.close()

    def test_v6_mcp_read_only_intents_gain_an_empty_fail_closed_facade_pin_and_legacy_principal(self) -> None:
        legacy_path = Path(self.tempdir.name) / "v6-mcp-intents.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                """
                CREATE TABLE mcp_read_only_intents (
                    owner_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    intent_digest TEXT NOT NULL,
                    request_id TEXT NOT NULL REFERENCES work_requests(request_id),
                    action_id TEXT NOT NULL REFERENCES actions(action_id),
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(owner_id, idempotency_key),
                    UNIQUE(request_id),
                    UNIQUE(action_id)
                )
                """
            )
            connection.execute("PRAGMA user_version = 6")
            connection.commit()
        finally:
            connection.close()

        ControlPlaneStore(legacy_path)

        connection = sqlite3.connect(legacy_path)
        try:
            columns = {
                row[1]: row[4]
                for row in connection.execute("PRAGMA table_info(mcp_read_only_intents)")
            }
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(columns["facade_schema_version"], "0")
            self.assertEqual(columns["facade_profile"], "''")
            self.assertEqual(columns["facade_contract_sha256"], "''")
            self.assertEqual(columns["principal_id"], "'legacy_unscoped'")
            self.assertIn(
                "mcp_access_grants",
                {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")},
            )
        finally:
            connection.close()

    def test_v25_oauth_rows_migrate_to_v27_without_becoming_service_principals(self) -> None:
        legacy_path = Path(self.tempdir.name) / "v25-oauth.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                """
                CREATE TABLE oauth_principals (
                    principal_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    subject_digest TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER,
                    UNIQUE(issuer, subject_digest)
                )
                """
            )
            connection.execute(
                "INSERT INTO oauth_principals VALUES (?, ?, ?, ?, ?, NULL)",
                ("oauthprn_legacy", "owner_default", "https://accounts.example.com", "f" * 64, self.now),
            )
            connection.execute("PRAGMA user_version = 25")
            connection.commit()
        finally:
            connection.close()
        upgraded = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        self.assertEqual(
            [item["principal_id"] for item in upgraded.list_oauth_principals(owner_id="owner_default")],
            ["oauthprn_legacy"],
        )
        self.assertEqual(upgraded.list_private_tunnel_service_principals(owner_id="owner_default"), [])
        ControlPlaneStore(legacy_path, clock=lambda: self.now)
        connection = sqlite3.connect(legacy_path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(
                connection.execute(
                    "SELECT principal_kind FROM oauth_principals WHERE principal_id = 'oauthprn_legacy'"
                ).fetchone()[0],
                "oauth",
            )
            self.assertIn(
                "mcp_service_grants",
                {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")},
            )
        finally:
            connection.close()

    def test_v26_service_grants_migrate_to_inventory_only(self) -> None:
        legacy_path = Path(self.tempdir.name) / "v26-service-grants.sqlite3"
        token = "mcpsvc_" + "A" * 43
        digest = hashlib.sha256(
            b"coding-tools-control-plane:mcp-service-grant:v1\0" + token.encode("ascii")
        ).hexdigest()
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                """
                CREATE TABLE oauth_principals (
                    principal_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    subject_digest TEXT NOT NULL,
                    principal_kind TEXT NOT NULL DEFAULT 'oauth',
                    created_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER,
                    UNIQUE(issuer, subject_digest)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE mcp_service_grants (
                    grant_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES oauth_principals(principal_id),
                    token_digest TEXT NOT NULL UNIQUE,
                    created_at_ms INTEGER NOT NULL,
                    expires_at_ms INTEGER NOT NULL,
                    revoked_at_ms INTEGER,
                    CHECK(expires_at_ms > created_at_ms)
                )
                """
            )
            connection.execute(
                "INSERT INTO oauth_principals VALUES (?, ?, ?, ?, ?, ?, NULL)",
                ("svcprn_legacy", "owner_default", "private_tunnel_service", "f" * 64,
                 "private_tunnel_service", self.now),
            )
            connection.execute(
                "INSERT INTO mcp_service_grants VALUES (?, ?, ?, ?, ?, ?, NULL)",
                ("mcpsvcgrant_legacy", "owner_default", "svcprn_legacy", digest,
                 self.now, self.now + 60_000),
            )
            connection.execute("PRAGMA user_version = 26")
            connection.commit()
        finally:
            connection.close()
        upgraded = ControlPlaneStore(legacy_path, clock=lambda: self.now)
        self.assertEqual(
            upgraded.authenticate_mcp_service_token(access_token=token)["scopes"],
            frozenset({"control-plane.inventory"}),
        )
        self.assertEqual(
            upgraded.list_mcp_service_grants(owner_id="owner_default")[0]["scopes"],
            ["control-plane.inventory"],
        )
        with upgraded._connection() as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(
                connection.execute("SELECT scopes_json FROM mcp_service_grants").fetchone()[0],
                '["control-plane.inventory"]',
            )

    def test_failed_schema_initialization_rolls_back_new_tables_and_version(self) -> None:
        broken_path = Path(self.tempdir.name) / "broken.sqlite3"
        connection = sqlite3.connect(broken_path)
        try:
            connection.execute("CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY)")
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(sqlite3.OperationalError):
            ControlPlaneStore(broken_path, clock=lambda: self.now)
        connection = sqlite3.connect(broken_path)
        try:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            self.assertEqual(tables, {"receipts"})
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
        finally:
            connection.close()

    def test_backup_api_snapshot_is_verified_and_never_overwrites_destination(self) -> None:
        backup_path = Path(self.tempdir.name) / "control.backup.sqlite3"
        snapshot = self.store.backup_to(backup_path)
        self.assertEqual(snapshot["sqlite_integrity"], "ok")
        self.assertEqual(snapshot["schema_version"], SCHEMA_VERSION)
        self.assertGreater(snapshot["bytes"], 0)
        self.assertEqual(snapshot["snapshot_sha256"], hashlib.sha256(backup_path.read_bytes()).hexdigest())
        connection = sqlite3.connect(backup_path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0], 1)
        finally:
            connection.close()
        with self.assertRaises(ConflictError):
            self.store.backup_to(backup_path)

    def test_explicit_snapshot_of_an_existing_database_never_initializes_or_migrates_source(self) -> None:
        source_path = Path(self.tempdir.name) / "legacy-before-migration.sqlite3"
        destination_path = Path(self.tempdir.name) / "snapshots" / "legacy.sqlite3"
        connection = sqlite3.connect(source_path)
        try:
            connection.execute("CREATE TABLE preserved_marker (value TEXT NOT NULL)")
            connection.execute("INSERT INTO preserved_marker(value) VALUES ('before-migration')")
            connection.execute("PRAGMA user_version = 3")
            connection.commit()
        finally:
            connection.close()

        snapshot = create_verified_backup(source_path, destination_path)
        self.assertEqual(snapshot["sqlite_integrity"], "ok")
        self.assertEqual(snapshot["schema_version"], 3)
        self.assertTrue(destination_path.is_file())
        self.assertEqual(snapshot["snapshot_sha256"], hashlib.sha256(destination_path.read_bytes()).hexdigest())
        connection = sqlite3.connect(source_path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(connection.execute("SELECT value FROM preserved_marker").fetchone()[0], "before-migration")
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name = 'control_plane_state'").fetchone())
        finally:
            connection.close()

        missing_source = Path(self.tempdir.name) / "does-not-exist.sqlite3"
        with self.assertRaises(NotFoundError):
            create_verified_backup(missing_source, Path(self.tempdir.name) / "missing.sqlite3")
        self.assertFalse(missing_source.exists())

    def test_maintenance_snapshot_cli_returns_content_free_receipts_and_typed_failure(self) -> None:
        destination_path = Path(self.tempdir.name) / "cli-snapshot.sqlite3"
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(
                maintenance_main(["snapshot", "--source", str(self.store.path), "--destination", str(destination_path)]),
                0,
            )
        receipt = json.loads(stdout.getvalue())
        self.assertEqual(receipt["operation"], "verified_sqlite_snapshot")
        self.assertEqual(receipt["sqlite_integrity"], "ok")
        self.assertRegex(receipt["snapshot_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn(str(self.store.path), stdout.getvalue())
        self.assertNotIn(str(destination_path), stdout.getvalue())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(
                maintenance_main([
                    "snapshot",
                    "--source",
                    str(Path(self.tempdir.name) / "missing.sqlite3"),
                    "--destination",
                    str(Path(self.tempdir.name) / "unused.sqlite3"),
                ]),
                2,
            )
        self.assertEqual(json.loads(stderr.getvalue()), {"error": {"code": "NOT_FOUND"}})

    def test_maintenance_package_fingerprint_is_source_only_and_content_free(self) -> None:
        before = self.store.health()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(maintenance_main(["package-fingerprint"]), 0)
        receipt = json.loads(stdout.getvalue())
        self.assertEqual(receipt["operation"], "control_plane_package_source_fingerprint")
        self.assertRegex(receipt["package_source_sha256"], r"^sha256:[a-f0-9]{64}$")
        self.assertNotIn(str(self.store.path), stdout.getvalue())
        self.assertEqual(self.store.health(), before)

    def test_recovery_restore_candidate_is_non_overwriting_and_keeps_dispatch_locked(self) -> None:
        context, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-restore-candidate-0001",
            admission_reference="admission-restore-candidate-0001",
            expires_at_ms=self.now + 20_000,
        )
        source_snapshot = Path(self.tempdir.name) / "restore-candidate-source.sqlite3"
        source_receipt = self.store.backup_to(source_snapshot)
        candidate_path = Path(self.tempdir.name) / "restore-candidate.sqlite3"

        candidate = create_recovery_restore_candidate(
            source_snapshot,
            candidate_path,
            expected_sha256=str(source_receipt["snapshot_sha256"]),
        )
        self.assertTrue(candidate_path.is_file())
        self.assertEqual(candidate["admission_mode"], "recovery")
        self.assertEqual(candidate["source_snapshot_sha256"], source_receipt["snapshot_sha256"])
        self.assertEqual(candidate["candidate_sha256"], hashlib.sha256(candidate_path.read_bytes()).hexdigest())
        self.assertEqual(inspect_verified_snapshot(source_snapshot)["admission_mode"], "open")
        self.assertEqual(inspect_verified_snapshot(candidate_path)["admission_mode"], "recovery")
        restored = ControlPlaneStore(candidate_path, clock=lambda: self.now)
        restored.heartbeat(
            device_id="device-alpha",
            endpoint_id="endpoint-alpha",
            runtime_instance_id="runtime-alpha",
            mcp_server_instance_id="server-alpha",
            activation_epoch="epoch-alpha",
            contract_version="smart-v3",
            readiness="ready",
        )
        self.assertEqual(restored.poll_actions(device_id="device-alpha"), [])
        self.assertEqual(restored.action(owner_id="owner_default", action_id=action["action_id"])["delivery_state"], "queued")
        with self.assertRaises(ConflictError):
            create_recovery_restore_candidate(source_snapshot, candidate_path)

        stdout = io.StringIO()
        cli_path = Path(self.tempdir.name) / "restore-candidate-cli.sqlite3"
        with redirect_stdout(stdout):
            self.assertEqual(
                maintenance_main([
                    "prepare-recovery-restore",
                    "--source",
                    str(source_snapshot),
                    "--destination",
                    str(cli_path),
                    "--expected-sha256",
                    str(source_receipt["snapshot_sha256"]),
                ]),
                0,
            )
        cli_receipt = json.loads(stdout.getvalue())
        self.assertEqual(cli_receipt["operation"], "recovery_restore_candidate")
        self.assertEqual(cli_receipt["admission_mode"], "recovery")
        self.assertNotIn(str(source_snapshot), stdout.getvalue())
        self.assertNotIn(str(cli_path), stdout.getvalue())

    def test_snapshot_inspection_binds_exact_artifact_and_reports_only_reconciliation_preflight(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-snapshot-preflight-0001",
            admission_reference="admission-snapshot-preflight-0001",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        attempt = self.store.poll_actions(device_id="device-alpha")[0]["attempt_id"]
        self.store.record_receipt(
            device_id="device-alpha",
            action_id=action["action_id"],
            attempt_id=attempt,
            receipt_state="unknown",
            local_handle="",
            payload={"reason": "requires_reconciliation"},
        )
        snapshot_path = Path(self.tempdir.name) / "restore-preflight.sqlite3"
        snapshot = self.store.backup_to(snapshot_path)
        inspected = inspect_verified_snapshot(snapshot_path, expected_sha256=str(snapshot["snapshot_sha256"]))
        self.assertEqual(inspected["sqlite_integrity"], "ok")
        self.assertEqual(inspected["snapshot_sha256"], snapshot["snapshot_sha256"])
        self.assertEqual(inspected["admission_mode"], "open")
        self.assertEqual(inspected["delivery_state_counts"], {"reconcile_required": 1})
        self.assertEqual(inspected["unresolved_action_count"], 1)
        with self.assertRaises(ConflictError):
            inspect_verified_snapshot(snapshot_path, expected_sha256="f" * 64)
        with self.assertRaises(ValidationError):
            inspect_verified_snapshot(snapshot_path, expected_sha256="not-a-sha256")
        wal_path = Path(f"{snapshot_path}-wal")
        wal_path.write_bytes(b"not-a-database")
        try:
            with self.assertRaises(ConflictError):
                inspect_verified_snapshot(snapshot_path)
        finally:
            wal_path.unlink()

    def test_maintenance_snapshot_inspection_cli_is_read_only_and_returns_typed_digest_conflict(self) -> None:
        snapshot_path = Path(self.tempdir.name) / "inspection-cli.sqlite3"
        snapshot = self.store.backup_to(snapshot_path)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(
                maintenance_main([
                    "inspect-snapshot",
                    "--source",
                    str(snapshot_path),
                    "--expected-sha256",
                    str(snapshot["snapshot_sha256"]),
                ]),
                0,
            )
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["operation"], "verified_snapshot_inspection")
        self.assertEqual(result["snapshot_sha256"], snapshot["snapshot_sha256"])
        self.assertNotIn(str(snapshot_path), stdout.getvalue())
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(
                maintenance_main([
                    "inspect-snapshot",
                    "--source",
                    str(snapshot_path),
                    "--expected-sha256",
                    "f" * 64,
                ]),
                2,
            )
        self.assertEqual(json.loads(stderr.getvalue()), {"error": {"code": "CONFLICT"}})

    def test_concurrent_poll_delivers_one_attempt_and_concurrent_receipt_replays(self) -> None:
        _, request = self._request()
        action = self.store.seal_action(owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context", arguments={"mode": "status"}, idempotency_key="action-key-0016", admission_reference="admission-0016", expires_at_ms=self.now + 20_000)
        self._ready_node()

        def concurrent_call(callback):
            barrier = threading.Barrier(2)
            results: list[dict | list] = []
            errors: list[BaseException] = []
            lock = threading.Lock()

            def worker() -> None:
                try:
                    barrier.wait(timeout=2)
                    result = callback()
                    with lock:
                        results.append(result)
                except BaseException as error:  # test fixture captures thread failure for assertion below
                    with lock:
                        errors.append(error)

            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=6)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            return results

        polls = concurrent_call(lambda: self.store.poll_actions(device_id="device-alpha"))
        delivered = [item for result in polls for item in result]
        self.assertEqual([item["action_id"] for item in delivered], [action["action_id"]])
        attempt_id = delivered[0]["attempt_id"]
        receipts = concurrent_call(
            lambda: self.store.record_receipt(
                device_id="device-alpha",
                action_id=action["action_id"],
                attempt_id=attempt_id,
                receipt_state="completed",
                local_handle="cmd-concurrent-1",
                payload={"proof": "ok"},
            )
        )
        self.assertEqual(sorted(result["replayed"] for result in receipts), [False, True])
        observation = self.store.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(len(observation["attempts"]), 1)
        self.assertEqual(len(observation["receipts"]), 1)

    def test_process_exit_after_dispatch_commit_leaves_action_reconcilable_not_redeliverable(self) -> None:
        """A real central-process exit after polling cannot create a safe retry.

        The subprocess exits immediately after SQLite commits the attempt and
        returns it. Reopening in this process must see the durable
        `dispatch_unconfirmed` state and preserve the exact attempt for a
        truthful late receipt rather than returning the action again.
        """
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-0021",
            admission_reference="admission-0021",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        package_root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(package_root)}
        program = (
            "import json, sys\n"
            "from control_plane.store import ControlPlaneStore\n"
            "store = ControlPlaneStore(sys.argv[1], clock=lambda: int(sys.argv[2]))\n"
            "print(json.dumps(store.poll_actions(device_id=sys.argv[3]), separators=(',', ':')))\n"
        )
        completed = subprocess.run(
            [sys.executable, "-W", "error", "-B", "-c", program, str(self.store.path), str(self.now), "device-alpha"],
            cwd=package_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        delivered = json.loads(completed.stdout)
        self.assertEqual([item["action_id"] for item in delivered], [action["action_id"]])
        attempt_id = delivered[0]["attempt_id"]

        reopened = ControlPlaneStore(self.store.path, clock=lambda: self.now)
        self.assertEqual(reopened.poll_actions(device_id="device-alpha"), [])
        observation = reopened.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "dispatch_unconfirmed")
        self.assertEqual([item["attempt_id"] for item in observation["attempts"]], [attempt_id])
        receipt = reopened.record_receipt(
            device_id="device-alpha",
            action_id=action["action_id"],
            attempt_id=attempt_id,
            receipt_state="unknown",
            local_handle="",
            payload={"reason": "node_effect_unconfirmed_after_process_exit"},
        )
        self.assertEqual(receipt["delivery_state"], "reconcile_required")

    def test_process_exit_before_dispatch_commit_rolls_back_without_a_phantom_attempt(self) -> None:
        """A central-process exit before COMMIT must leave no partial delivery.

        The child replaces only the event append immediately after the poll has
        written the action/attempt rows and then exits the process before the
        surrounding transaction can commit. SQLite must roll back both writes;
        a later healthy poll may issue the first and only durable attempt.
        """
        _, request = self._request()
        action = self.store.seal_action(
            owner_id="owner_default",
            request_id=request["request_id"],
            tool_name="workspace_context",
            arguments={"mode": "status"},
            idempotency_key="action-key-0022",
            admission_reference="admission-0022",
            expires_at_ms=self.now + 20_000,
        )
        self._ready_node()
        package_root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONPATH": str(package_root)}
        program = (
            "import os, sys\n"
            "from control_plane.store import ControlPlaneStore\n"
            "store = ControlPlaneStore(sys.argv[1], clock=lambda: int(sys.argv[2]))\n"
            "def crash_before_commit(*_args):\n"
            "    os._exit(73)\n"
            "store._event = crash_before_commit\n"
            "store.poll_actions(device_id=sys.argv[3])\n"
        )
        completed = subprocess.run(
            [sys.executable, "-W", "error", "-B", "-c", program, str(self.store.path), str(self.now), "device-alpha"],
            cwd=package_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 73, completed.stderr)

        reopened = ControlPlaneStore(self.store.path, clock=lambda: self.now)
        observation = reopened.action_observation(owner_id="owner_default", action_id=action["action_id"])
        self.assertEqual(observation["delivery_state"], "queued")
        self.assertEqual(observation["attempts"], [])
        delivered = reopened.poll_actions(device_id="device-alpha")
        self.assertEqual([item["action_id"] for item in delivered], [action["action_id"]])
        self.assertEqual(delivered[0]["delivery_state"], "dispatch_unconfirmed")
        self.assertEqual(delivered[0]["attempt_id"], reopened.action_observation(owner_id="owner_default", action_id=action["action_id"])["attempts"][0]["attempt_id"])

    def test_node_generated_enrollment_requires_explicit_approval(self) -> None:
        request = self.store.request_enrollment(device_id="device-beta", endpoint_id="endpoint-beta", display_name="Second node", credential_hash="a" * 64)
        self.assertIsNone(request["approved_at_ms"])
        approved = self.store.approve_enrollment(owner_id="owner_default", enrollment_id=request["enrollment_id"])
        self.assertEqual(approved["device_id"], "device-beta")
        with self.assertRaises(PermissionError):
            self.store.authenticate_node(device_id="device-beta", node_secret="not-the-requested-secret")

    def test_node_enrollment_status_is_authenticated_and_request_retry_replays_after_approval(self) -> None:
        node_secret = "s" * 40
        credential_hash = hashlib.sha256(
            json.dumps({"node_secret": node_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        request = self.store.request_enrollment(
            device_id="device-status-0001",
            endpoint_id="endpoint-status-0001",
            display_name="Status node",
            credential_hash=credential_hash,
        )
        pending = self.store.node_enrollment_status(device_id="device-status-0001", node_secret=node_secret)
        self.assertEqual(pending["state"], "pending_operator_approval")
        self.assertEqual(pending["enrollment_id"], request["enrollment_id"])
        with self.assertRaises(PermissionError):
            self.store.node_enrollment_status(device_id="device-status-0001", node_secret="wrong-secret-000000")

        approved = self.store.approve_enrollment(owner_id="owner_default", enrollment_id=request["enrollment_id"])
        self.assertEqual(approved["device_id"], "device-status-0001")
        replayed = self.store.request_enrollment(
            device_id="device-status-0001",
            endpoint_id="endpoint-status-0001",
            display_name="Status node",
            credential_hash=credential_hash,
        )
        self.assertEqual(replayed["enrollment_id"], request["enrollment_id"])
        self.assertIsNotNone(replayed["approved_at_ms"])
        status = self.store.node_enrollment_status(device_id="device-status-0001", node_secret=node_secret)
        self.assertEqual(status["state"], "approved")
        self.assertEqual(status["credential_generation"], 1)
        self.store.revoke_node(owner_id="owner_default", device_id="device-status-0001")
        revoked = self.store.node_enrollment_status(device_id="device-status-0001", node_secret=node_secret)
        self.assertEqual(revoked["state"], "revoked")

    def test_node_authority_status_is_path_free_and_distinguishes_binding_lifecycle(self) -> None:
        pending_secret = "authority-pending-secret-0001"
        pending_hash = hashlib.sha256(
            json.dumps({"node_secret": pending_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        request = self.store.request_enrollment(
            device_id="device-authority-pending-0001",
            endpoint_id="endpoint-authority-pending-0001",
            display_name="Pending authority node",
            credential_hash=pending_hash,
        )
        pending = self.store.node_authority_status(
            device_id="device-authority-pending-0001",
            node_secret=pending_secret,
        )
        self.assertEqual(pending["state"], "pending_operator_approval")
        self.assertEqual(pending["targets"], [])
        self.assertNotIn("owner_id", json.dumps(pending))
        self.assertNotIn("workspace_id", json.dumps(pending))
        self.assertEqual(request["device_id"], "device-authority-pending-0001")

        target = self.store.create_binding(
            owner_id="owner_default",
            device_id="device-alpha",
            workspace_id="workspace-alpha",
            workspace_generation="generation-1",
            display_name="Canary workspace",
        )
        active = self.store.node_authority_status(device_id="device-alpha", node_secret=self.node_secret)
        self.assertEqual(active["state"], "active")
        self.assertEqual(active["target_count"], 1)
        self.assertEqual(active["dispatchable_target_count"], 1)
        self.assertEqual(active["targets"][0]["workspace_display_name"], "Canary workspace")
        self.assertEqual(active["targets"][0]["workspace_id"], "workspace-alpha")
        self.assertEqual(active["targets"][0]["workspace_generation"], "generation-1")
        self.assertNotIn(target["binding_id"], json.dumps(active))
        self.assertNotIn("owner_default", json.dumps(active))

        self.store.revoke_binding(owner_id="owner_default", binding_id=target["binding_id"])
        revoked = self.store.node_authority_status(device_id="device-alpha", node_secret=self.node_secret)
        self.assertEqual(revoked["state"], "binding_revoked")
        self.assertEqual(revoked["targets"][0]["binding_state"], "revoked")

        with self.assertRaises(PermissionError):
            self.store.node_authority_status(device_id="device-alpha", node_secret="wrong-authority-secret")

    def test_node_enrollment_persists_one_https_target_and_requires_explicit_replacement(self) -> None:
        config_path = Path(self.tempdir.name) / "node.json"
        calls: list[tuple[str, str, dict]] = []

        def request(server_url: str, route: str, payload: dict, _authorization: str | None = None) -> dict:
            calls.append((server_url, route, payload))
            return {"enrollment_id": "enroll-node-target-0001"}

        output = io.StringIO()
        errors = io.StringIO()
        secret_field = "node_secret_dpapi" if os.name == "nt" else "node_secret"
        with mock.patch("control_plane.node_agent._request", side_effect=request), redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "https://CONTROL.example.test/",
                "--device-id", "device-target-0001", "--endpoint-id", "endpoint-target-0001", "--display-name", "Office executor",
            ]), 0)
            original = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(original["schema_version"], 1)
            self.assertEqual(original["server_url"], "https://control.example.test")
            self.assertEqual(original["enrollment_id"], "enroll-node-target-0001")
            self.assertEqual(original["enrollment_state"], "pending_operator_approval")
            original_secret = _config(config_path)["node_secret"]
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "https://other.example.test",
                "--device-id", "device-target-0001", "--endpoint-id", "endpoint-target-0001", "--display-name", "Office executor",
            ]), 1)
            unchanged = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(unchanged[secret_field], original[secret_field])
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "https://other.example.test",
                "--device-id", "device-target-0001", "--endpoint-id", "endpoint-target-0001", "--display-name", "Office executor",
                "--replace-existing-config",
            ]), 0)

        replaced = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "https://control.example.test")
        self.assertEqual(calls[1][0], "https://other.example.test")
        self.assertNotEqual(replaced[secret_field], original[secret_field])
        if os.name == "nt":
            self.assertNotIn("node_secret", replaced)
        self.assertIn("CONTROL_PLANE_ENROLLMENT_CONFIG_REPLACEMENT_REQUIRED", errors.getvalue())
        self.assertNotIn(original_secret, output.getvalue())
        self.assertNotIn(_config(config_path)["node_secret"], output.getvalue())

    def test_node_enrollment_reconcile_persists_approved_state_and_keeps_stale_state_on_transport_loss(self) -> None:
        config_path = Path(self.tempdir.name) / "reconcile-node.json"
        request_calls: list[tuple[str, str, dict, str | None]] = []
        pending_response = {
            "enrollment_id": "enroll-reconcile-0001",
            "device_id": "device-reconcile-0001",
            "approved_at_ms": None,
        }

        def request(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            request_calls.append((server_url, route, payload, authorization))
            if route == "/v1/enrollment-requests":
                return pending_response
            return {
                "enrollment_id": "enroll-reconcile-0001",
                "device_id": "device-reconcile-0001",
                "state": "approved",
                "credential_generation": 2,
                "requested_at_ms": 1_700_000_000_000,
                "approved_at_ms": 1_700_000_000_100,
                "observed_at_ms": 1_700_000_000_200,
            }

        with mock.patch("control_plane.node_agent._request", side_effect=request), redirect_stdout(io.StringIO()):
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "https://control.example.test",
                "--device-id", "device-reconcile-0001", "--endpoint-id", "endpoint-reconcile-0001", "--display-name", "Reconcile executor",
            ]), 0)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(node_agent_main(["reconcile-enrollment", "--config", str(config_path), "--device-id", "device-reconcile-0001"]), 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["state"], "approved")
            self.assertTrue(receipt["fresh"])
            self.assertEqual(receipt["server_origin"], "https://control.example.test")
            persisted = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["enrollment_state"], "approved")
            self.assertEqual(persisted["credential_generation"], 2)

        def unavailable(*_args: object, **_kwargs: object) -> dict:
            raise RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE")

        with mock.patch("control_plane.node_agent._request", side_effect=unavailable):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(node_agent_main(["reconcile-enrollment", "--config", str(config_path), "--device-id", "device-reconcile-0001"]), 0)
            stale = json.loads(output.getvalue())
            self.assertEqual(stale["state"], "approved")
            self.assertFalse(stale["fresh"])
            self.assertEqual(stale["error_code"], "CONTROL_PLANE_TRANSPORT_UNAVAILABLE")
            self.assertEqual(stale["server_origin"], "https://control.example.test")
        self.assertGreaterEqual(len(request_calls), 2)

    def test_node_enrollment_refuses_non_loopback_http_before_writing_a_config(self) -> None:
        config_path = Path(self.tempdir.name) / "node-invalid.json"
        errors = io.StringIO()
        with redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "http://100.116.112.22:8765",
                "--device-id", "device-target-0001", "--endpoint-id", "endpoint-target-0001", "--display-name", "Office executor",
            ]), 1)
        self.assertFalse(config_path.exists())
        self.assertIn("CONTROL_PLANE_SERVER_HTTPS_REQUIRED", errors.getvalue())

    def test_node_workspace_registration_persists_opaque_identity_before_network_retry(self) -> None:
        config_path = Path(self.tempdir.name) / "workspace-node.json"
        registry_path = Path(self.tempdir.name) / "workspace-registry.json"
        workspace_path = Path(self.tempdir.name) / "selected-root"
        workspace_path.mkdir()
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "server_url": "https://control.example.test",
            "device_id": "device-workspace-0001",
            "endpoint_id": "endpoint-workspace-0001",
            "display_name": "Workspace executor",
            "node_secret": "n" * 40,
        }), encoding="utf-8")
        command = [
            "register-workspace", "--config", str(config_path),
            "--workspace-registry", str(registry_path),
            "--workspace-path", str(workspace_path),
            "--display-name", "selected-root", "--capability-read",
        ]
        output = io.StringIO()
        errors = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=RuntimeError("CONTROL_PLANE_NETWORK_UNAVAILABLE")) as request, \
             redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(node_agent_main(command), 1)
        self.assertEqual(request.call_count, 1)
        self.assertTrue(registry_path.exists())
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["schema_version"], 1)
        self.assertEqual(len(registry["entries"]), 1)
        entry = registry["entries"][0]
        self.assertEqual(entry["canonical_path"], str(workspace_path.resolve()))
        self.assertTrue(entry["capabilities"]["read"])
        self.assertFalse(entry["capabilities"]["write"])
        self.assertFalse(entry["capabilities"]["exec"])
        self.assertNotIn(str(workspace_path), output.getvalue())
        self.assertNotIn("n" * 40, output.getvalue())

        calls: list[tuple[str, str, dict, str | None]] = []

        def retry(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((server_url, route, payload, authorization))
            return {
                "device_id": "device-workspace-0001",
                "workspace_id": entry["workspace_id"],
                "workspace_generation": entry["workspace_generation"],
                "display_name": "selected-root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "registered_at_ms": 1,
                "retired_at_ms": None,
                "replayed": True,
            }

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=retry), redirect_stdout(output):
            self.assertEqual(node_agent_main(command), 0)
        self.assertEqual(calls, [(
            "https://control.example.test",
            "/v1/nodes/device-workspace-0001/workspace-registrations",
            {
                "workspace_id": entry["workspace_id"],
                "workspace_generation": entry["workspace_generation"],
                "display_name": "selected-root",
                "capabilities": {"read": True, "write": False, "exec": False},
            },
            "Node " + "n" * 40,
        )])
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["workspace_id"], entry["workspace_id"])
        self.assertTrue(receipt["replayed"])
        self.assertNotIn("canonical_path", receipt)
        self.assertNotIn(str(workspace_path), output.getvalue())

        invalid = Path(self.tempdir.name) / "does-not-exist"
        with mock.patch("control_plane.node_agent._request") as request, redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                "register-workspace", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
                "--workspace-path", str(invalid),
                "--display-name", "does-not-exist", "--capability-read",
            ]), 1)
        request.assert_not_called()

    def test_node_workspace_retirement_keeps_local_entry_until_exact_central_receipt(self) -> None:
        config_path = Path(self.tempdir.name) / "workspace-retire-node.json"
        registry_path = Path(self.tempdir.name) / "workspace-retire-registry.json"
        workspace_path = Path(self.tempdir.name) / "workspace-retire-root"
        workspace_path.mkdir()
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "server_url": "https://control.example.test",
            "device_id": "device-retire-0001",
            "endpoint_id": "endpoint-retire-0001",
            "display_name": "Retire executor",
            "node_secret": "n" * 40,
        }), encoding="utf-8")
        register_command = [
            "register-workspace", "--config", str(config_path),
            "--workspace-registry", str(registry_path),
            "--workspace-path", str(workspace_path),
            "--display-name", "workspace-retire-root", "--capability-read",
        ]

        def register_request(_server_url: str, route: str, payload: dict, _authorization: str | None = None) -> dict:
            self.assertEqual(route, "/v1/nodes/device-retire-0001/workspace-registrations")
            return {
                "device_id": "device-retire-0001",
                "workspace_id": payload["workspace_id"],
                "workspace_generation": payload["workspace_generation"],
                "display_name": "workspace-retire-root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "registered_at_ms": 1,
                "retired_at_ms": None,
                "replayed": False,
            }

        with mock.patch("control_plane.node_agent._request", side_effect=register_request):
            self.assertEqual(node_agent_main(register_command), 0)
        entry = json.loads(registry_path.read_text(encoding="utf-8"))["entries"][0]
        data_root = Path(self.tempdir.name) / "workspace-retire-data"
        data_root.mkdir()
        policy_path = data_root / "control-plane-read-only-policy.json"
        policy_path.write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "server_origin": "https://control.example.test",
            "owner_id": "owner_default",
            "device_id": "device-retire-0001",
            "endpoint_id": "endpoint-retire-0001",
            "workspace_id": entry["workspace_id"],
            "workspace_generation": entry["workspace_generation"],
            "expires_at_ms": int(time.time() * 1000) + 60_000,
            "facade_contract": {
                "schema_version": 6,
                "profile": "control-plane-scoped-read-only-relay-v5",
                "sha256": "a" * 64,
            },
        }), encoding="utf-8")
        retire_command = [
            "retire-workspace", "--config", str(config_path),
            "--workspace-registry", str(registry_path),
            "--workspace-id", entry["workspace_id"],
            "--workspace-generation", entry["workspace_generation"],
            "--data-root", str(data_root),
        ]

        errors = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE")) as request, redirect_stderr(errors):
            self.assertEqual(node_agent_main(retire_command), 1)
        request.assert_called_once()
        self.assertEqual(len(json.loads(registry_path.read_text(encoding="utf-8"))["entries"]), 1)
        self.assertTrue(json.loads(policy_path.read_text(encoding="utf-8"))["enabled"])
        self.assertIn("CONTROL_PLANE_TRANSPORT_UNAVAILABLE", errors.getvalue())

        calls: list[tuple[str, str, dict, str | None]] = []

        def replay_retirement(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((server_url, route, payload, authorization))
            return {
                "device_id": "device-retire-0001",
                "workspace_id": entry["workspace_id"],
                "workspace_generation": entry["workspace_generation"],
                "display_name": "workspace-retire-root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "registered_at_ms": 1,
                "retired_at_ms": 2,
                "replayed": True,
            }

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=replay_retirement), redirect_stdout(output):
            self.assertEqual(node_agent_main(retire_command), 0)
        self.assertEqual(calls, [(
            "https://control.example.test",
            "/v1/nodes/device-retire-0001/workspace-registrations/retire",
            {"workspace_id": entry["workspace_id"], "workspace_generation": entry["workspace_generation"]},
            "Node " + "n" * 40,
        )])
        self.assertEqual(json.loads(registry_path.read_text(encoding="utf-8"))["entries"], [])
        self.assertFalse(json.loads(policy_path.read_text(encoding="utf-8"))["enabled"])
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["state"], "retired")
        self.assertTrue(receipt["replayed"])
        self.assertNotIn(str(workspace_path), output.getvalue())
        self.assertNotIn("n" * 40, output.getvalue())

        list_output = io.StringIO()
        with redirect_stdout(list_output):
            self.assertEqual(node_agent_main([
                "list-workspaces", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
            ]), 0)
        self.assertEqual(json.loads(list_output.getvalue()), {"workspaces": []})

    def test_node_installs_only_its_authenticated_context_policy_template(self) -> None:
        config_path = Path(self.tempdir.name) / "node-template.json"
        registry_path = Path(self.tempdir.name) / "node-template-workspaces.json"
        data_root = Path(self.tempdir.name) / "node-template-data"
        workspace_path = Path(self.tempdir.name) / "node-template-root"
        workspace_path.mkdir()
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "server_url": "https://control.example.test",
            "device_id": "device-template-0001",
            "endpoint_id": "endpoint-template-0001",
            "display_name": "Template executor",
            "node_secret": "n" * 40,
        }), encoding="utf-8")
        registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-template-0001",
                "workspace_generation": "generation-template-0001",
                "canonical_path": str(workspace_path.resolve()),
                "display_name": "Template root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "created_at_ms": 1,
            }],
        }), encoding="utf-8")
        calls: list[tuple[str, str, dict, str | None]] = []

        def request(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((server_url, route, payload, authorization))
            return {
                "policy_template": {
                    "owner_id": "owner_default",
                    "device_id": "device-template-0001",
                    "endpoint_id": "endpoint-template-0001",
                    "workspace_id": "workspace-template-0001",
                    "workspace_generation": "generation-template-0001",
                    "expires_at_ms": int(time.time() * 1000) + 60_000,
                    "facade_contract": {"schema_version": 6, "profile": "control-plane-scoped-read-only-relay-v5", "sha256": "a" * 64},
                }
            }

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            self.assertEqual(node_agent_main([
                "install-read-only-policy-from-context", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
                "--context-id", "ctx-template-0001", "--confirm-install", "--data-root", str(data_root),
            ]), 0)
        policy = json.loads((data_root / "control-plane-read-only-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["device_id"], "device-template-0001")
        self.assertEqual(policy["workspace_id"], "workspace-template-0001")
        self.assertEqual(calls, [
            ("https://control.example.test", "/v1/nodes/device-template-0001/read-only-policy-template", {"context_id": "ctx-template-0001"}, "Node " + "n" * 40),
        ])

        registry_path.write_text(json.dumps({"schema_version": 1, "entries": []}), encoding="utf-8")
        rejected_data_root = Path(self.tempdir.name) / "node-template-rejected"
        errors = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=request), redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                "install-read-only-policy-from-context", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
                "--context-id", "ctx-template-0001", "--confirm-install", "--data-root", str(rejected_data_root),
            ]), 1)
        self.assertIn("CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT", errors.getvalue())
        self.assertFalse((rejected_data_root / "control-plane-read-only-policy.json").exists())

    def test_node_installs_only_the_assigned_policy_for_its_selected_registered_root(self) -> None:
        config_path = Path(self.tempdir.name) / "node-assignment.json"
        registry_path = Path(self.tempdir.name) / "node-assignment-workspaces.json"
        data_root = Path(self.tempdir.name) / "node-assignment-data"
        workspace_path = Path(self.tempdir.name) / "node-assignment-root"
        workspace_path.mkdir()
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "server_url": "https://control.example.test",
            "device_id": "device-assignment-0001",
            "endpoint_id": "endpoint-assignment-0001",
            "display_name": "Assignment executor",
            "node_secret": "n" * 40,
        }), encoding="utf-8")
        registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-assignment-0001",
                "workspace_generation": "generation-assignment-0001",
                "canonical_path": str(workspace_path.resolve()),
                "display_name": "Assignment root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "created_at_ms": 1,
            }],
        }), encoding="utf-8")
        calls: list[tuple[str, str, dict, str | None]] = []

        def request(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            calls.append((server_url, route, payload, authorization))
            return {
                "policy_template": {
                    "owner_id": "owner_default",
                    "device_id": "device-assignment-0001",
                    "endpoint_id": "endpoint-assignment-0001",
                    "workspace_id": "workspace-assignment-0001",
                    "workspace_generation": "generation-assignment-0001",
                    "expires_at_ms": int(time.time() * 1000) + 60_000,
                    "facade_contract": {"schema_version": 6, "profile": "control-plane-scoped-read-only-relay-v5", "sha256": "a" * 64},
                }
            }

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            self.assertEqual(node_agent_main([
                "install-read-only-policy-from-assignment", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
                "--workspace-id", "workspace-assignment-0001",
                "--workspace-generation", "generation-assignment-0001",
                "--confirm-install", "--data-root", str(data_root),
            ]), 0)
        policy = json.loads((data_root / "control-plane-read-only-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["workspace_id"], "workspace-assignment-0001")
        self.assertEqual(calls, [(
            "https://control.example.test",
            "/v1/nodes/device-assignment-0001/read-only-policy-assignment",
            {"workspace_id": "workspace-assignment-0001", "workspace_generation": "generation-assignment-0001"},
            "Node " + "n" * 40,
        )])
        self.assertNotIn("ctx_", json.dumps(calls))

        wrong_template_root = Path(self.tempdir.name) / "node-assignment-wrong-template"

        def wrong_template(server_url: str, route: str, payload: dict, authorization: str | None = None) -> dict:
            response = request(server_url, route, payload, authorization)
            response["policy_template"]["workspace_generation"] = "generation-assignment-other"
            return response

        errors = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=wrong_template), redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                "install-read-only-policy-from-assignment", "--config", str(config_path),
                "--workspace-registry", str(registry_path),
                "--workspace-id", "workspace-assignment-0001",
                "--workspace-generation", "generation-assignment-0001",
                "--confirm-install", "--data-root", str(wrong_template_root),
            ]), 1)
        self.assertIn("CONTROL_PLANE_POLICY_TEMPLATE_TARGET_MISMATCH", errors.getvalue())
        self.assertFalse((wrong_template_root / "control-plane-read-only-policy.json").exists())

    def test_read_only_loop_admission_requires_current_local_workspace_generation(self) -> None:
        config_path = Path(self.tempdir.name) / "loop-workspace-node.json"
        registry_path = Path(self.tempdir.name) / "loop-workspace-registry.json"
        data_root = Path(self.tempdir.name) / "loop-workspace-data"
        workspace_path = Path(self.tempdir.name) / "loop-workspace-root"
        workspace_path.mkdir()
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "server_url": "https://control.example.test",
            "device_id": "device-loop-workspace-0001",
            "endpoint_id": "endpoint-loop-workspace-0001",
            "display_name": "Loop executor",
            "node_secret": "n" * 40,
        }), encoding="utf-8")
        registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-loop-workspace-0001",
                "workspace_generation": "generation-loop-workspace-0001",
                "canonical_path": str(workspace_path.resolve()),
                "display_name": "Loop root",
                "capabilities": {"read": True, "write": False, "exec": False},
                "created_at_ms": 1,
            }],
        }), encoding="utf-8")
        data_root.mkdir()
        (data_root / "control-plane-read-only-policy.json").write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "server_origin": "https://control.example.test",
            "owner_id": "owner_default",
            "device_id": "device-loop-workspace-0001",
            "endpoint_id": "endpoint-loop-workspace-0001",
            "workspace_id": "workspace-loop-workspace-0001",
            "workspace_generation": "generation-loop-workspace-0001",
            "expires_at_ms": int(time.time() * 1000) + 60_000,
            "facade_contract": {
                "schema_version": 6,
                "profile": "control-plane-scoped-read-only-relay-v5",
                "sha256": "a" * 64,
            },
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path),
            workspace_registry=str(registry_path),
            data_root=str(data_root),
            runtime_mode="development",
        )
        _read_only_loop_policy_admission(args)
        workspace_path.rmdir()
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT"):
            _read_only_loop_policy_admission(args)

    def test_installed_launcher_arguments_are_accepted_for_enrollment_heartbeat_and_safe_poll(self) -> None:
        """All commands must accept the fixed packaged ``node-agent.cmd`` tail."""

        config_path = Path(self.tempdir.name) / "installed-node.json"
        fixed_runtime_args = [
            "--project-root", "C:/Program Files/Coding Tools MCP",
            "--node", "C:/Program Files/Coding Tools MCP/Coding Tools MCP.exe",
            "--runtime-mode", "packaged",
        ]
        calls: list[tuple[str, str]] = []

        def request(server_url: str, path: str, _payload: dict, _authorization: str | None = None) -> dict:
            calls.append((server_url, path))
            if path == "/v1/enrollment-requests":
                return {"enrollment_id": "enroll-installed-launcher-0001"}
            if path.endswith("/heartbeat"):
                return {"device_id": "device-installer", "readiness": "unknown", "last_seen_at_ms": 1}
            raise AssertionError(path)

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch.dict(os.environ, {"APPDATA": str(Path(self.tempdir.name) / "appdata")}, clear=False), \
             redirect_stdout(output):
            self.assertEqual(node_agent_main([
                "request-enrollment", "--config", str(config_path), "--server-url", "https://control.example.test",
                "--device-id", "device-installer", "--endpoint-id", "endpoint-installer", "--display-name", "Installed node",
                *fixed_runtime_args,
            ]), 0)
            self.assertEqual(node_agent_main([
                "heartbeat", "--config", str(config_path), *fixed_runtime_args,
            ]), 0)
            self.assertEqual(node_agent_main([
                "poll", "--config", str(config_path), *fixed_runtime_args,
            ]), 0)
            self.assertEqual(node_agent_main([
                "run-read-only-loop", "--config", str(config_path), "--interval-seconds", "15", "--max-iterations", "1",
                "--workspace-registry", str(config_path.with_name("control-plane-workspaces.json")),
                *fixed_runtime_args,
            ]), 0)
        self.assertEqual(calls, [
            ("https://control.example.test", "/v1/enrollment-requests"),
            ("https://control.example.test", "/v1/nodes/device-installer/heartbeat"),
        ])
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[-2]["code"], "POLL_EXECUTION_DISABLED")
        self.assertEqual(records[-1]["reason"], "CONTROL_PLANE_BRIDGE_POLICY_MISSING")

    def test_bounded_read_only_loop_rechecks_heartbeat_before_each_poll(self) -> None:
        args = SimpleNamespace(interval_seconds=15, max_iterations=2)
        calls: list[str] = []
        output = io.StringIO()
        with mock.patch("control_plane.node_agent._read_only_loop_policy_admission"), \
             mock.patch("control_plane.node_agent.runtime_heartbeat", side_effect=lambda _args: calls.append("heartbeat")), \
             mock.patch("control_plane.node_agent.poll_read_only_once", side_effect=lambda _args: calls.append("poll")), \
             mock.patch("control_plane.node_agent.time.sleep") as sleep, \
             redirect_stdout(output):
            self.assertEqual(run_read_only_loop(args), 0)
        self.assertEqual(calls, ["heartbeat", "poll", "heartbeat", "poll"])
        sleep.assert_called_once_with(15)
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([(record["iteration"], record["state"]) for record in records], [(1, "completed"), (2, "completed")])

    def test_read_only_agent_retries_transient_failures_with_bounded_backoff_and_releases_lock(self) -> None:
        config_path = Path(self.tempdir.name) / "agent-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-agent-0001",
            "endpoint_id": "endpoint-agent-0001",
            "node_secret": "agent-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=3,
        )
        output = io.StringIO()
        with mock.patch(
            "control_plane.node_agent._read_only_iteration",
            side_effect=[
                RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE"),
                RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE"),
                None,
            ],
        ) as iterate, mock.patch("control_plane.node_agent.time.sleep") as sleep, redirect_stdout(output):
            self.assertEqual(run_read_only_agent(args), 0)
        self.assertEqual(iterate.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(15), mock.call(30)])
        self.assertFalse((Path(self.tempdir.name) / "agent-node.json.read-only-agent.lock").exists())
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[0]["execution"], "read_only_agent_started")
        self.assertEqual(
            [(record["state"], record["next_delay_seconds"]) for record in records[1:4]],
            [("degraded", 15), ("degraded", 30), ("completed", 15)],
        )
        self.assertEqual(records[-1], {
            "execution": "read_only_agent_stopped",
            "reason": "MAX_ITERATIONS_REACHED",
            "completed_iterations": 3,
        })

    def test_connected_agent_sends_heartbeat_without_read_only_policy(self) -> None:
        config_path = Path(self.tempdir.name) / "connected-agent-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-connected-agent-0001",
            "endpoint_id": "endpoint-connected-agent-0001",
            "node_secret": "connected-agent-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), workspace_registry=str(Path(self.tempdir.name) / "registry.json"),
            project_root=str(Path.cwd()), node="node", runtime_mode="development", timeout_seconds=20,
            data_root=self.tempdir.name, interval_seconds=15, max_backoff_seconds=60, max_iterations=1,
        )
        stop_codes = {
            "file_read": "CONTROL_PLANE_FILE_READ_POLICY_MISSING",
            "artifact": "CONTROL_PLANE_FILE_READ_POLICY_MISSING",
            "approved_patch": "CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING",
            "document_write": "CONTROL_PLANE_DOCUMENT_WRITE_POLICY_MISSING",
            "exec": "CONTROL_PLANE_EXEC_POLICY_MISSING",
        }

        def skip_lane(_args: argparse.Namespace, lane: str) -> None:
            raise RuntimeError(stop_codes[lane])

        output = io.StringIO()
        with mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat_call, \
             mock.patch("control_plane.node_agent._connected_agent_lane_admission", side_effect=skip_lane), \
             mock.patch("control_plane.node_agent.poll_file_read_once") as file_read, \
             mock.patch("control_plane.node_agent.poll_artifact_once") as artifact, \
             mock.patch("control_plane.node_agent.poll_approved_patch_once") as patch_once, \
             mock.patch("control_plane.node_agent.poll_document_write_once") as document_write, \
             mock.patch("control_plane.node_agent.poll_exec_once") as exec_once, \
             redirect_stdout(output):
            self.assertEqual(run_connected_agent(args), 0)
        heartbeat_call.assert_called_once_with(args)
        file_read.assert_not_called()
        artifact.assert_not_called()
        patch_once.assert_not_called()
        document_write.assert_not_called()
        exec_once.assert_not_called()
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[0]["execution"], "connected_agent_started")
        self.assertEqual(records[1]["state"], "completed")
        self.assertEqual([lane["state"] for lane in records[1]["lanes"]], ["disabled"] * 5)
        self.assertEqual(records[-1]["execution"], "connected_agent_stopped")
        self.assertFalse((Path(self.tempdir.name) / "connected-agent-node.json.connected-agent.lock").exists())

    def test_connected_agent_polls_each_enabled_standing_lane_after_heartbeat(self) -> None:
        config_path = Path(self.tempdir.name) / "connected-agent-enabled-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-connected-agent-0002",
            "endpoint_id": "endpoint-connected-agent-0002",
            "node_secret": "connected-agent-enabled-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), workspace_registry=str(Path(self.tempdir.name) / "registry.json"),
            project_root=str(Path.cwd()), node="node", runtime_mode="development", timeout_seconds=20,
            data_root=self.tempdir.name, interval_seconds=15, max_backoff_seconds=60, max_iterations=1,
        )
        output = io.StringIO()
        with mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat_call, \
             mock.patch("control_plane.node_agent._connected_agent_lane_admission"), \
             mock.patch("control_plane.node_agent.poll_file_read_once") as file_read, \
             mock.patch("control_plane.node_agent.poll_artifact_once") as artifact, \
             mock.patch("control_plane.node_agent.poll_approved_patch_once") as patch_once, \
             mock.patch("control_plane.node_agent.poll_document_write_once") as document_write, \
             mock.patch("control_plane.node_agent.poll_exec_once") as exec_once, \
             redirect_stdout(output):
            self.assertEqual(run_connected_agent(args), 0)
        heartbeat_call.assert_called_once_with(args)
        file_read.assert_called_once_with(args)
        artifact.assert_called_once_with(args)
        patch_once.assert_called_once_with(args)
        document_write.assert_called_once_with(args)
        exec_once.assert_called_once_with(args)
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([lane["state"] for lane in records[1]["lanes"]], ["polled"] * 5)

    def test_connected_agent_reconnects_with_bounded_backoff(self) -> None:
        config_path = Path(self.tempdir.name) / "connected-agent-reconnect-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-connected-agent-0003",
            "endpoint_id": "endpoint-connected-agent-0003",
            "node_secret": "connected-agent-reconnect-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=3,
        )
        output = io.StringIO()
        with mock.patch(
            "control_plane.node_agent._connected_agent_iteration",
            side_effect=[
                RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE"),
                RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE"),
                [],
            ],
        ) as iterate, mock.patch("control_plane.node_agent.time.sleep") as sleep, redirect_stdout(output):
            self.assertEqual(run_connected_agent(args), 0)
        self.assertEqual(iterate.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(15), mock.call(30)])
        self.assertFalse((Path(self.tempdir.name) / "connected-agent-reconnect-node.json.connected-agent.lock").exists())
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(
            [(record["state"], record["next_delay_seconds"]) for record in records[1:4]],
            [("degraded", 15), ("degraded", 30), ("completed", 15)],
        )

    def test_read_only_agent_stops_before_heartbeat_or_poll_when_local_policy_is_disabled(self) -> None:
        config_path = Path(self.tempdir.name) / "agent-policy-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-agent-policy-0001",
            "endpoint_id": "endpoint-agent-policy-0001",
            "node_secret": "agent-policy-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=0,
        )
        output = io.StringIO()
        with mock.patch(
            "control_plane.node_agent._read_only_iteration",
            side_effect=RuntimeError("CONTROL_PLANE_BRIDGE_DISABLED"),
        ) as iterate, mock.patch("control_plane.node_agent.time.sleep") as sleep, redirect_stdout(output):
            self.assertEqual(run_read_only_agent(args), 0)
        self.assertEqual(iterate.call_count, 1)
        sleep.assert_not_called()
        self.assertFalse((Path(self.tempdir.name) / "agent-policy-node.json.read-only-agent.lock").exists())
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[-1], {
            "execution": "read_only_agent_stopped",
            "reason": "CONTROL_PLANE_BRIDGE_DISABLED",
            "completed_iterations": 0,
        })

    def test_read_only_agent_refuses_a_live_same_profile_lock(self) -> None:
        config_path = Path(self.tempdir.name) / "agent-lock-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-agent-lock-0001",
            "endpoint_id": "endpoint-agent-lock-0001",
            "node_secret": "agent-lock-secret-not-reported",
        }), encoding="utf-8")
        lock_path = Path(self.tempdir.name) / "agent-lock-node.json.read-only-agent.lock"
        lock_path.write_text(json.dumps({
            "schema_version": 1,
            "instance_id": "another-local-agent-instance",
            "pid": os.getpid(),
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=1,
        )
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_READ_ONLY_AGENT_ALREADY_RUNNING"):
            run_read_only_agent(args)
        self.assertTrue(lock_path.exists())

    def test_read_only_poll_refuses_a_live_queue_drain_lock_before_journal_access(self) -> None:
        config_path = Path(self.tempdir.name) / "poll-lock-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-poll-lock-0001",
            "endpoint_id": "endpoint-poll-lock-0001",
            "node_secret": "poll-lock-secret-not-reported",
        }), encoding="utf-8")
        lock_path = _read_only_poll_lock_path(config_path)
        lock_path.write_text(json.dumps({
            "schema_version": 1,
            "instance_id": "another-local-poll-instance",
            "pid": os.getpid(),
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1,
        )
        with mock.patch("control_plane.node_agent._request") as request:
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_READ_ONLY_POLL_ALREADY_RUNNING"):
                poll_read_only_once(args)
        request.assert_not_called()
        self.assertTrue(lock_path.exists())

    def test_windows_invalid_parameter_process_probe_is_confirmed_dead(self) -> None:
        missing_process = OSError(errno.EINVAL, "The parameter is incorrect")
        missing_process.winerror = 87
        with mock.patch("control_plane.node_agent.os.name", "nt"), \
             mock.patch("control_plane.node_agent.os.kill", side_effect=missing_process):
            self.assertFalse(_pid_is_live(71_001))

    def test_windows_exited_process_is_not_reported_live_after_child_exit(self) -> None:
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child_pid = child.pid
        self.assertEqual(child.wait(timeout=10), 0)
        self.assertFalse(_pid_is_live(child_pid))

    def test_read_only_agent_reclaims_only_a_confirmed_dead_lock_owner(self) -> None:
        config_path = Path(self.tempdir.name) / "agent-stale-lock-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-agent-stale-0001",
            "endpoint_id": "endpoint-agent-stale-0001",
            "node_secret": "agent-stale-secret-not-reported",
        }), encoding="utf-8")
        lock_path = Path(self.tempdir.name) / "agent-stale-lock-node.json.read-only-agent.lock"
        lock_path.write_text(json.dumps({
            "schema_version": 1,
            "instance_id": "crashed-agent-instance",
            "pid": 71_001,
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=1,
        )
        with mock.patch("control_plane.node_agent._pid_is_live", return_value=False), \
             mock.patch("control_plane.node_agent._read_only_iteration"), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(run_read_only_agent(args), 0)
        self.assertFalse(lock_path.exists())

    def test_read_only_agent_policy_revalidation_stops_before_heartbeat_or_dequeue(self) -> None:
        config_path = Path(self.tempdir.name) / "agent-revalidation-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-agent-revalidation-0001",
            "endpoint_id": "endpoint-agent-revalidation-0001",
            "node_secret": "agent-revalidation-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), interval_seconds=15, max_backoff_seconds=60, max_iterations=0,
        )
        output = io.StringIO()
        with mock.patch(
            "control_plane.node_agent._read_only_loop_policy_admission",
            side_effect=RuntimeError("CONTROL_PLANE_BRIDGE_POLICY_EXPIRED"),
        ), mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat_call, \
             mock.patch("control_plane.node_agent.poll_read_only_once") as poll_call, \
             redirect_stdout(output):
            self.assertEqual(run_read_only_agent(args), 0)
        heartbeat_call.assert_not_called()
        poll_call.assert_not_called()
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[-1], {
            "execution": "read_only_agent_stopped",
            "reason": "CONTROL_PLANE_BRIDGE_POLICY_EXPIRED",
            "completed_iterations": 0,
        })

    def test_read_only_loop_refuses_missing_policy_without_heartbeat_or_dequeue(self) -> None:
        config_path = Path(self.tempdir.name) / "loop-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-loop-policy-0001",
            "endpoint_id": "endpoint-loop-policy-0001",
            "node_secret": "loop-policy-secret-not-reported",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path),
            data_root=self.tempdir.name,
            runtime_mode="development",
            interval_seconds=15,
            max_iterations=1,
        )
        output = io.StringIO()
        with mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat_call, \
             mock.patch("control_plane.node_agent.poll_read_only_once") as poll_call, \
             redirect_stdout(output):
            self.assertEqual(run_read_only_loop(args), 0)
        heartbeat_call.assert_not_called()
        poll_call.assert_not_called()
        record = json.loads(output.getvalue())
        self.assertEqual(record, {
            "execution": "read_only_loop_not_started",
            "reason": "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
            "completed_iterations": 0,
        })

    def test_read_only_loop_refuses_policy_bound_to_another_endpoint_before_dequeue(self) -> None:
        config_path = Path(self.tempdir.name) / "loop-mismatch-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-loop-policy-0002",
            "endpoint_id": "endpoint-loop-policy-0002",
            "node_secret": "loop-policy-secret-not-reported",
        }), encoding="utf-8")
        data_root = Path(self.tempdir.name) / "loop-policy-data"
        data_root.mkdir()
        (data_root / "control-plane-read-only-policy.json").write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "server_origin": "https://control.example.test",
            "owner_id": "owner_default",
            "device_id": "device-loop-policy-0002",
            "endpoint_id": "endpoint-some-other-node",
            "workspace_id": "workspace-loop-policy-0002",
            "workspace_generation": "generation-loop-policy-0002",
            "expires_at_ms": int(time.time() * 1000) + 60_000,
            "facade_contract": FACADE_CONTRACT,
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path),
            data_root=str(data_root),
            runtime_mode="development",
            interval_seconds=15,
            max_iterations=1,
        )
        output = io.StringIO()
        with mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat_call, \
             mock.patch("control_plane.node_agent.poll_read_only_once") as poll_call, \
             redirect_stdout(output):
            self.assertEqual(run_read_only_loop(args), 0)
        heartbeat_call.assert_not_called()
        poll_call.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["reason"], "CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH")

    def test_packaged_read_only_policy_is_explicit_cross_language_and_locally_disableable(self) -> None:
        config_path = Path(self.tempdir.name) / "packaged-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-packaged-policy-0001",
            "endpoint_id": "endpoint-packaged-policy-0001",
            "display_name": "Packaged policy node",
            "node_secret": "node-secret-must-not-enter-policy-0001",
        }), encoding="utf-8")
        appdata = Path(self.tempdir.name) / "appdata"
        expiry = int(time.time() * 1000) + 60_000
        installed_args = [
            "--project-root", "C:/Program Files/Coding Tools MCP",
            "--node", "C:/Program Files/Coding Tools MCP/Coding Tools MCP.exe",
            "--runtime-mode", "packaged",
        ]
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False), redirect_stdout(output):
            self.assertEqual(node_agent_main([
                "install-read-only-policy", "--config", str(config_path), "--owner-id", "owner_default",
                "--workspace-id", "workspace-policy-canary", "--workspace-generation", "generation-policy-0001",
                "--facade-schema-version", str(FACADE_CONTRACT["schema_version"]),
                "--facade-profile", str(FACADE_CONTRACT["profile"]),
                "--facade-sha256", str(FACADE_CONTRACT["sha256"]), "--expires-at-ms", str(expiry),
                "--confirm-install", *installed_args,
            ]), 0)
            self.assertEqual(node_agent_main(["inspect-read-only-policy", *installed_args]), 0)
            self.assertEqual(node_agent_main(["disable-read-only-policy", "--confirm-disable", *installed_args]), 0)
            self.assertEqual(node_agent_main(["inspect-read-only-policy", *installed_args]), 0)

        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(records[0]["operation"], "control_plane_read_only_policy_installed")
        self.assertTrue(records[0]["enabled"])
        self.assertFalse(records[0]["windows_acl_verified"])
        self.assertEqual(records[1]["state"], "enabled")
        self.assertEqual(records[2]["operation"], "control_plane_read_only_policy_disabled")
        self.assertEqual(records[3]["state"], "expired_or_disabled")

        policy_path = appdata / "web-mcp-assistant" / "control-plane-read-only-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertFalse(policy["enabled"])
        self.assertNotIn("node_secret", json.dumps(policy))
        self.assertNotIn("node-secret-must-not-enter-policy", json.dumps(policy))

        # The enabled policy shape emitted by Python must be accepted and
        # fingerprinted identically by the actual Recovery Host CJS policy gate.
        policy["enabled"] = True
        bridge = Path(__file__).resolve().parents[2] / "electron" / "services" / "controlPlaneReadOnlyBridge.js"
        program = (
            "const fs=require('node:fs');"
            "const bridge=require(process.argv[1]);"
            "const policy=bridge.normalisePolicy(JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{now:Date.now()-1});"
            "process.stdout.write(JSON.stringify({sha256:bridge.digest(policy)}));"
        )
        enabled_path = Path(self.tempdir.name) / "enabled-policy.json"
        enabled_path.write_text(json.dumps(policy), encoding="utf-8")
        checked = subprocess.run(
            ["node", "-e", program, str(bridge), str(enabled_path)],
            cwd=bridge.parents[2],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["sha256"], records[0]["policy_sha256"])

    def test_packaged_policy_writer_fails_closed_without_confirmation_or_with_a_redirected_data_root(self) -> None:
        config_path = Path(self.tempdir.name) / "policy-fail-closed-node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-policy-fail-closed",
            "endpoint_id": "endpoint-policy-fail-closed",
            "node_secret": "never-printed-policy-secret",
        }), encoding="utf-8")
        appdata = Path(self.tempdir.name) / "appdata"
        shared = [
            "install-read-only-policy", "--config", str(config_path), "--owner-id", "owner_default",
            "--workspace-id", "workspace-policy-fail-closed", "--workspace-generation", "generation-policy-fail-closed",
            "--facade-schema-version", str(FACADE_CONTRACT["schema_version"]),
            "--facade-profile", str(FACADE_CONTRACT["profile"]),
            "--facade-sha256", str(FACADE_CONTRACT["sha256"]),
            "--expires-at-ms", str(int(time.time() * 1000) + 60_000),
            "--runtime-mode", "packaged",
        ]
        errors = io.StringIO()
        with mock.patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False), redirect_stderr(errors):
            self.assertEqual(node_agent_main(shared), 1)
        self.assertEqual(json.loads(errors.getvalue())["error"], "CONTROL_PLANE_POLICY_CONFIRMATION_REQUIRED")
        self.assertFalse((appdata / "web-mcp-assistant" / "control-plane-read-only-policy.json").exists())

        errors = io.StringIO()
        with mock.patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False), redirect_stderr(errors):
            self.assertEqual(node_agent_main([
                *shared, "--confirm-install", "--data-root", str(Path(self.tempdir.name) / "wrong-profile"),
            ]), 1)
        self.assertEqual(json.loads(errors.getvalue())["error"], "CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN")
        self.assertFalse((appdata / "web-mcp-assistant" / "control-plane-read-only-policy.json").exists())

    def test_runtime_policy_observation_is_redacted_and_rejects_wrong_local_target(self) -> None:
        data_root = Path(self.tempdir.name) / "policy-observation-data"
        data_root.mkdir()
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-policy-observation-0001",
            "endpoint_id": "endpoint-policy-observation-0001",
            "node_secret": "not-part-of-observation",
        }
        args = SimpleNamespace(data_root=str(data_root), runtime_mode="development")
        missing = read_only_policy_observation(args, config)
        self.assertEqual(missing, {
            "state": "unavailable",
            "expires_at_ms": None,
            "policy_sha256": None,
            "reason": "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
        })
        (data_root / "control-plane-read-only-policy.json").write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "server_origin": "https://control.example.test",
            "owner_id": "owner_default",
            "device_id": config["device_id"],
            "endpoint_id": config["endpoint_id"],
            "workspace_id": "workspace-policy-observation-0001",
            "workspace_generation": "generation-policy-observation-0001",
            "expires_at_ms": int(time.time() * 1000) + 60_000,
            "facade_contract": FACADE_CONTRACT,
        }), encoding="utf-8")
        enabled = read_only_policy_observation(args, config)
        self.assertEqual(enabled["state"], "enabled")
        self.assertRegex(enabled["policy_sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(enabled["reason"], "")
        self.assertNotIn("workspace-policy-observation", json.dumps({
            "state": enabled["state"], "expires_at_ms": enabled["expires_at_ms"],
            "policy_sha256": enabled["policy_sha256"], "reason": enabled["reason"],
        }))

        config["endpoint_id"] = "endpoint-policy-observation-other"
        mismatch = read_only_policy_observation(args, config)
        self.assertEqual(mismatch, {
            "state": "unavailable",
            "expires_at_ms": None,
            "policy_sha256": None,
            "reason": "CONTROL_PLANE_BRIDGE_POLICY_CONFIG_MISMATCH",
        })

    def test_runtime_heartbeat_submits_only_compact_policy_observation(self) -> None:
        config_path = Path(self.tempdir.name) / "runtime-policy-heartbeat.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-runtime-policy-0001",
            "endpoint_id": "endpoint-runtime-policy-0001",
            "node_secret": "node-secret-never-in-policy-observation",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), project_root=self.tempdir.name, data_root=self.tempdir.name,
            runtime_mode="development", node="node", timeout_seconds=20,
        )
        submitted: list[dict] = []

        def request(_server_url: str, path: str, payload: dict, authorization: str | None = None) -> dict:
            self.assertEqual(path, "/v1/nodes/device-runtime-policy-0001/heartbeat")
            self.assertEqual(authorization, "Node node-secret-never-in-policy-observation")
            submitted.append(payload)
            return {
                "device_id": "device-runtime-policy-0001",
                "endpoint_id": "endpoint-runtime-policy-0001",
                "revoked_at_ms": None,
                "credential_generation": 1,
                "last_seen_at_ms": 1_700_000_000_000,
                "readiness": "blocked",
                "policy_state": "unavailable",
                "policy_expires_at_ms": None,
                "policy_sha256": None,
            }

        output = io.StringIO()
        with mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent._request", side_effect=request), \
             redirect_stdout(output):
            self.assertEqual(runtime_heartbeat(args), 0)
        self.assertEqual(submitted[0]["policy_observation"], {
            "state": "unavailable",
            "expires_at_ms": None,
            "policy_sha256": None,
            "reason": "CONTROL_PLANE_BRIDGE_POLICY_MISSING",
        })
        self.assertNotIn("node-secret-never-in-policy-observation", json.dumps(submitted[0]["policy_observation"]))
        result = json.loads(output.getvalue())
        self.assertEqual(result["policy_state"], "unavailable")
        self.assertEqual(result["route_evidence"], "fresh")
        evidence = json.loads((Path(self.tempdir.name) / "control-plane-route-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["kind"], "control_plane_authenticated_heartbeat")
        self.assertEqual(evidence["device_id"], "device-runtime-policy-0001")
        self.assertEqual(evidence["endpoint_id"], "endpoint-runtime-policy-0001")
        self.assertEqual(evidence["policy_state"], "unavailable")
        self.assertNotIn("node-secret-never-in-policy-observation", json.dumps(evidence))

    def test_standing_policy_observation_bootstraps_route_without_legacy_ttl_policy(self) -> None:
        data_root = Path(self.tempdir.name) / "standing-only-data"
        data_root.mkdir()
        config_path = data_root / "node.json"
        workspace_root = data_root / "workspace"
        workspace_root.mkdir()
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-standing-only-0001",
            "endpoint_id": "endpoint-standing-only-0001",
            "node_secret": "standing-only-secret-not-reported",
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        registry_path = data_root / "control-plane-workspaces.json"
        registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-standing-only-0001",
                "workspace_generation": "generation-standing-only-0001",
                "canonical_path": str(workspace_root.resolve()),
                "display_name": "standing-only",
                "capabilities": {"read": True, "write": True, "exec": True},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")
        (data_root / "control-plane-file-read-policy.json").write_text(json.dumps({
            "schema_version": 2,
            "enabled": True,
            "authority_mode": "standing",
            "server_origin": config["server_url"],
            "owner_id": "owner-standing-only-0001",
            "device_id": config["device_id"],
            "endpoint_id": config["endpoint_id"],
            "workspace_id": "workspace-standing-only-0001",
            "workspace_generation": "generation-standing-only-0001",
            "expires_at_ms": None,
            "facade_contract": FACADE_CONTRACT,
            "allowed_relative_paths": ["README.md"],
            "max_bytes": 1024,
            "max_lines": 20,
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), workspace_registry=str(registry_path),
            data_root=str(data_root), project_root=str(data_root), runtime_mode="development", node="node", timeout_seconds=20,
        )

        observation = read_only_policy_observation(args, config)
        self.assertEqual(observation["state"], "enabled")
        self.assertEqual(observation["reason"], "")
        self.assertIsInstance(observation["expires_at_ms"], int)
        self.assertGreaterEqual(observation["expires_at_ms"], int(time.time() * 1000))
        self.assertLessEqual(observation["expires_at_ms"], int(time.time() * 1000) + STANDING_POLICY_OBSERVATION_TTL_MS + 1_000)
        self.assertRegex(observation["policy_sha256"], r"^[a-f0-9]{64}$")

        submitted: list[dict] = []

        def request(_url: str, path: str, payload: dict, _authorization: str | None = None) -> dict:
            self.assertEqual(path, "/v1/nodes/device-standing-only-0001/heartbeat")
            submitted.append(payload)
            observed_policy = payload["policy_observation"]
            return {
                "device_id": config["device_id"],
                "endpoint_id": config["endpoint_id"],
                "revoked_at_ms": None,
                "credential_generation": 1,
                "last_seen_at_ms": int(time.time() * 1000),
                "readiness": "blocked",
                "policy_state": "enabled",
                "policy_expires_at_ms": observed_policy["expires_at_ms"],
                "policy_sha256": observed_policy["policy_sha256"],
            }

        with mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent._request", side_effect=request), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(runtime_heartbeat(args), 0)
        submitted_observation = submitted[0]["policy_observation"]
        self.assertEqual(submitted_observation["state"], observation["state"])
        self.assertEqual(submitted_observation["policy_sha256"], observation["policy_sha256"])
        self.assertIsInstance(submitted_observation["expires_at_ms"], int)
        evidence = json.loads((data_root / "control-plane-route-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["policy_state"], "enabled")
        self.assertEqual(evidence["policy_sha256"], observation["policy_sha256"])
        self.assertNotIn("standing-only-secret-not-reported", json.dumps(evidence))

    def test_runtime_heartbeat_refuses_an_incomplete_authenticated_echo_before_writing_route_evidence(self) -> None:
        config_path = Path(self.tempdir.name) / "runtime-route-invalid.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-runtime-route-0001",
            "endpoint_id": "endpoint-runtime-route-0001",
            "node_secret": "node-secret-never-in-route-evidence",
        }), encoding="utf-8")
        args = SimpleNamespace(
            config=str(config_path), project_root=self.tempdir.name, data_root=self.tempdir.name,
            runtime_mode="development", node="node", timeout_seconds=20,
        )
        with mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent._request", return_value={"device_id": "device-runtime-route-0001"}):
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_ROUTE_RESPONSE_INVALID"):
                runtime_heartbeat(args)
        self.assertFalse((Path(self.tempdir.name) / "control-plane-route-evidence.json").exists())

    def test_runtime_heartbeat_is_fail_closed_for_incomplete_hub(self) -> None:
        pending = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available instance=runtime-1 components_ready=false fully_ready=false "
            "runtime_telemetry_available=true error_code=none"
        )
        self.assertEqual(runtime_readiness(pending), ("degraded", "runtime_identity_unproven"))
        compatible = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available installation=current instance=runtime-2 "
            "mcp_update_pending=false mcp_running_revision=sha-a mcp_disk_revision=sha-a "
            "components_ready=true fully_ready=true runtime_update_incomplete=false "
            "runtime_telemetry_available=true runtime_signal_stale=false "
            "connector_state=CURRENT_COMPATIBLE_ACKNOWLEDGED connector_rediscovered=false "
            "connector_rediscovered_at=none connector_freshness_mode=compatible_activation_bootstrap "
            "connector_refresh_required=false connector_ack_pending=false connector_current_sha=sha-a connector_ack_sha=sha-a "
            "error_code=none"
        )
        self.assertEqual(runtime_readiness(compatible), ("degraded", "strict_connector_rediscovery_required"))
        stale_mcp = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available installation=current instance=runtime-3 "
            "mcp_update_pending=true mcp_running_revision=sha-old mcp_disk_revision=sha-new "
            "components_ready=true fully_ready=true runtime_update_incomplete=true "
            "runtime_telemetry_available=true runtime_signal_stale=false "
            "connector_state=CURRENT_ACKNOWLEDGED connector_rediscovered=true connector_rediscovered_at=2026-09-15T00:00:00Z "
            "connector_freshness_mode=current_process_discovery connector_refresh_required=false connector_ack_pending=false "
            "connector_current_sha=sha-a connector_ack_sha=sha-a error_code=none"
        )
        self.assertEqual(runtime_readiness(stale_mcp), ("degraded", "mcp_revision_unproven"))
        strict = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available installation=current instance=runtime-4 "
            "mcp_update_pending=false mcp_running_revision=sha-a mcp_disk_revision=sha-a "
            "components_ready=true fully_ready=true runtime_update_incomplete=false "
            "runtime_telemetry_available=true runtime_signal_stale=false "
            "connector_state=CURRENT_ACKNOWLEDGED connector_rediscovered=true connector_rediscovered_at=2026-09-15T00:00:00Z "
            "connector_freshness_mode=current_process_discovery connector_refresh_required=false connector_ack_pending=false "
            "connector_current_sha=sha-a connector_ack_sha=sha-a error_code=none"
        )
        self.assertEqual(runtime_readiness(strict), ("ready", "strict_current_process_discovery"))
        central_executor = parse_dev_ui_status(
            "DEV_UI STATUS state=CURRENT host=available installation=current instance=runtime-central "
            "execution_role=central_executor central_connected=true authority_ready=true central_status_reason=none "
            "mcp_update_pending=false mcp_running_revision=sha-central mcp_disk_revision=sha-central "
            "components_ready=true fully_ready=true runtime_update_incomplete=false "
            "runtime_telemetry_available=true runtime_signal_stale=false "
            "connector_state=CHANGED_NEEDS_DISCOVERY connector_rediscovered=false connector_rediscovered_at=none "
            "connector_freshness_mode=none connector_refresh_required=true connector_ack_pending=false "
            "connector_current_sha=sha-current connector_ack_sha=none error_code=none"
        )
        self.assertEqual(runtime_readiness(central_executor), ("ready", "strict_central_route"))
        central_projection = runtime_heartbeat_projection(central_executor, {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "coding-mcp-process-central-0001",
            "mcp_server_instance_id": "coding-mcp-server-central-0001",
            "activation_epoch_id": "activation-epoch-central-0001",
            "current_activation_epoch_id": "activation-epoch-central-0001",
            "tool_contract_sha256": "c" * 64,
        })
        self.assertEqual(central_projection["readiness"], "ready")
        self.assertEqual(central_projection["runtime_instance_id"], "coding-mcp-process-central-0001")
        self.assertEqual(central_projection["contract_version"], "sha256:" + "c" * 64)
        central_unavailable = dict(central_executor, central_connected="false")
        self.assertEqual(runtime_readiness(central_unavailable), ("degraded", "central_route_unproven"))
        central_policy_pending = dict(central_executor, authority_ready="false")
        self.assertEqual(runtime_readiness(central_policy_pending), ("degraded", "central_route_unproven"))
        central_error = dict(central_executor, central_status_reason="CENTRAL_AUTHORITY_STALE")
        self.assertEqual(runtime_readiness(central_error), ("degraded", "central_route_unproven"))
        projection = runtime_heartbeat_projection(strict)
        self.assertEqual(projection["readiness"], "degraded")
        self.assertEqual(projection["reason"], "runtime_identity_unproven")
        self.assertEqual(projection["runtime_instance_id"], "unreported")
        self.assertEqual(projection["mcp_server_instance_id"], "unreported")
        self.assertEqual(projection["activation_epoch"], "unreported")
        self.assertEqual(projection["contract_version"], "unreported")
        observed = runtime_heartbeat_projection(strict, {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "coding-mcp-process-0001",
            "mcp_server_instance_id": "coding-mcp-server-0001",
            "activation_epoch_id": "activation-epoch-0001",
            "current_activation_epoch_id": "activation-epoch-0001",
            "tool_contract_sha256": "f" * 64,
        })
        self.assertEqual(observed["readiness"], "ready")
        self.assertEqual(observed["runtime_instance_id"], "coding-mcp-process-0001")
        self.assertEqual(observed["mcp_server_instance_id"], "coding-mcp-server-0001")
        self.assertEqual(observed["activation_epoch"], "activation-epoch-0001")
        self.assertEqual(observed["contract_version"], "sha256:" + "f" * 64)
        unbound = runtime_heartbeat_projection(strict, {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "coding-mcp-process-0001",
            "mcp_server_instance_id": "coding-mcp-server-0001",
            "activation_epoch_id": "old-epoch",
            "current_activation_epoch_id": "new-epoch",
            "tool_contract_sha256": "f" * 64,
        })
        self.assertEqual(unbound["readiness"], "degraded")
        self.assertEqual(unbound["reason"], "runtime_identity_unproven")
        self.assertEqual(runtime_readiness({"state": "MISSING", "host": "unavailable"}), ("blocked", "runtime_unavailable"))
        self.assertEqual(
            runtime_readiness({"state": "MISSING", "host": "available", "components_ready": "true", "fully_ready": "true", "runtime_telemetry_available": "true", "error_code": "none"}),
            ("blocked", "runtime_unavailable"),
        )

    def test_recovery_identity_observation_accepts_only_structured_read_only_output(self) -> None:
        args = SimpleNamespace(node="node", timeout_seconds=20)
        expected = {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "identity_current": True,
        }
        with mock.patch("control_plane.node_agent.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps({"ok": True, "observation": expected}))) as run:
            self.assertEqual(recovery_identity_observation(args, Path.cwd()), expected)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "node")
        self.assertEqual(command[-2:], ["--project-root", str(Path.cwd())])
        with mock.patch("control_plane.node_agent.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps({"ok": False, "error": {"code": "MCP_IDENTITY_OBSERVATION_UNBOUND"}}))):
            self.assertIsNone(recovery_identity_observation(args, Path.cwd()))

    def test_packaged_runtime_status_uses_installed_electron_adapter_only(self) -> None:
        args = SimpleNamespace(
            node=r"C:\\Program Files\\Coding Tools MCP\\Coding Tools MCP.exe",
            timeout_seconds=20,
            runtime_mode="packaged",
        )
        payload = {
            "ok": True,
            "status": {
                "observation_schema_version": 1,
                "observation_kind": "recovery_runtime_read_only",
                "runtime_mode": "packaged",
                "strict_ready": True,
            },
        }
        with mock.patch("control_plane.node_agent.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload))) as run:
            status = recovery_runtime_status(args, Path(r"C:\\Program Files\\Coding Tools MCP"))
        self.assertEqual(status, {"adapter_mode": "packaged", "strict_ready": "true"})
        self.assertEqual(runtime_readiness(status), ("ready", "strict_packaged_recovery_observation"))
        command = run.call_args.args[0]
        self.assertEqual(command[0], args.node)
        self.assertEqual(command[-3:], ["--runtime-mode", "packaged", "--runtime-status"])
        self.assertNotIn("--project-root", command)
        self.assertEqual(run.call_args.kwargs["env"]["ELECTRON_RUN_AS_NODE"], "1")

    def test_serialized_cjs_identity_observation_is_accepted_by_python_parser(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is required for the Electron identity contract")
        observer = Path(__file__).resolve().parents[1] / "control_plane" / "recovery_identity_observer.cjs"
        program = """
const { normalizedObservation } = require(process.argv[1]);
const descriptor = {
  installation_id: 'a'.repeat(64),
  runtime_mode: 'development',
  instance_id: 'recovery-host-contract-0001'
};
const observation = normalizedObservation(descriptor, {
  observation_schema_version: 1,
  observation_kind: 'mcp_identity_read_only',
  recovery_host_instance_id: descriptor.instance_id,
  observed_at: '2026-09-16T00:00:00.000Z',
  mcp_process_instance_id: 'mcp-process-contract-0001',
  mcp_server_instance_id: 'mcp-server-contract-0001',
  activation_epoch_id: 'activation-contract-0001',
  current_activation_epoch_id: 'activation-contract-0001',
  tool_contract_sha256: 'b'.repeat(64),
  mcp_ready: true,
  identity_current: true
});
process.stdout.write(JSON.stringify(observation));
"""
        completed = subprocess.run(
            [node, "-e", program, str(observer)],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        serialized = json.loads(completed.stdout)
        self.assertEqual(serialized["observation_kind"], "mcp_identity_read_only")
        self.assertEqual(observed_runtime_identity(serialized), {
            "runtime_instance_id": "mcp-process-contract-0001",
            "mcp_server_instance_id": "mcp-server-contract-0001",
            "activation_epoch": "activation-contract-0001",
            "contract_version": "sha256:" + "b" * 64,
        })

    @staticmethod
    def _strict_runtime_status() -> dict[str, str]:
        return {
            "state": "CURRENT",
            "host": "available",
            "installation": "current",
            "mcp_update_pending": "false",
            "mcp_running_revision": "sha-current",
            "mcp_disk_revision": "sha-current",
            "components_ready": "true",
            "fully_ready": "true",
            "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true",
            "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED",
            "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-09-15T00:00:00Z",
            "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false",
            "connector_ack_pending": "false",
            "connector_current_sha": "sha-current",
            "connector_ack_sha": "sha-current",
            "error_code": "none",
        }

    @staticmethod
    def _strict_identity_observation() -> dict[str, object]:
        return {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "mcp-process-node-bridge-0001",
            "mcp_server_instance_id": "mcp-server-node-bridge-0001",
            "activation_epoch_id": "activation-node-bridge-0001",
            "current_activation_epoch_id": "activation-node-bridge-0001",
            "tool_contract_sha256": "a" * 64,
        }

    def test_read_only_node_lane_persists_a_safe_completed_receipt_before_submitting_it(self) -> None:
        config_path = Path(self.tempdir.name) / "node.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }), encoding="utf-8")
        action = {
            "action_id": "act-node-bridge-0001",
            "attempt_id": "try-node-bridge-0001",
            "owner_id": "owner-node-bridge-0001",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "workspace_id": "workspace-node-bridge-0001",
            "workspace_generation": "generation-node-bridge-0001",
            "context_id": "ctx-node-bridge-0001",
            "binding_id": "bind-node-bridge-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "mcp_read_only_intent_digest": "f" * 64,
            "admission_reference": "mcp_facade:" + "f" * 64,
            "mcp_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": 2_000_000_000_000,
        }
        local_result = {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "action_id": action["action_id"],
            "attempt_id": action["attempt_id"],
            "local_handle": "cp_ro_" + "b" * 48,
            "workspace_accessed": True,
            "policy_sha256": "c" * 64,
            "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
            "runtime_identity": {
                "activation_epoch_id": "activation-node-bridge-0001",
                "process_instance_id": "mcp-process-node-bridge-0001",
                "server_instance_id": "mcp-server-node-bridge-0001",
                "tool_contract_sha256": "d" * 64,
            },
            "facade_contract": dict(FACADE_CONTRACT),
            "workspace_summary": {
                "schema_version": 1,
                "project": {"type": "node", "name": "office-fixture", "version": "1.0.0"},
                "entries": [{"name": "office-marker.txt", "type": "file", "size_bytes": 17, "is_hidden": False, "is_ignored": False}],
                "entries_truncated": False,
                "git": {"is_repo": True, "branch": "main", "changed_count": 0, "truncated": False},
            },
            "workspace_summary_sha256": "f" * 64,
            "response_sha256": "e" * 64,
            "workspace": "E:/must-never-reach-central",
        }
        requests: list[tuple[str, dict[str, object]]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            requests.append((path, payload))
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            self.assertEqual(payload["receipt_state"], "completed")
            self.assertEqual(payload["local_handle"], local_result["local_handle"])
            self.assertNotIn("must-never-reach-central", json.dumps(payload))
            return {"receipt_id": "receipt-node-bridge-0001"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self._strict_runtime_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self._strict_identity_observation()), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge", return_value=(local_result, None)):
            self.assertEqual(poll_read_only_once(args), 0)

        self.assertEqual([path for path, _ in requests], [
            "/v1/nodes/device-node-bridge-0001/poll",
            "/v1/nodes/device-node-bridge-0001/receipts",
        ])
        journal = _read_journal(_journal_path(config_path))
        entry = journal["entries"]["act-node-bridge-0001|try-node-bridge-0001"]
        self.assertEqual(entry["state"], "completed")
        self.assertTrue(entry["receipt"]["receipt_submitted"])
        self.assertNotIn("must-never-reach-central", json.dumps(entry))

    def test_scoped_pilot_dispatches_only_decision_bound_file_read(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Selected workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        context = self.store.create_context(
            owner_id="owner_default", binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000,
        )
        request = self.store.create_work_request(
            owner_id="owner_default", context_id=context["context_id"], objective="Old queued read",
            criteria={}, scope={}, expires_at_ms=self.now + 60_000,
        )
        old = self.store.seal_action(
            owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context",
            arguments={"detail": "compact"}, idempotency_key="old-generic-action-001",
            admission_reference="test", expires_at_ms=self.now + 60_000,
        )
        self._ready_node()
        self.store.set_admission_mode(mode="recovery")
        with self.assertRaises(ConflictError):
            self.store.set_admission_mode(mode="scoped_pilot")
        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="Pilot for the selected Windows workspace",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="generic"), [])
        intent = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], path="README.md", start_line=1,
            max_lines=10, max_bytes=1024, idempotency_key="pilot-file-read-001",
            facade_contract=FACADE_CONTRACT,
        )
        action = self.store.action(owner_id="owner_default", action_id=intent["action_id"])
        self.assertEqual(action["scoped_pilot_decision_id"], decision["decision_id"])
        delivered = self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read")
        self.assertEqual([row["action_id"] for row in delivered], [intent["action_id"]])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=old["action_id"])["delivery_state"], "queued")

    def test_scoped_pilot_renewal_rechecks_target_and_preserves_decision(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Selected workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self._ready_node()
        self.store.set_admission_mode(mode="recovery")
        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000,
            reason="Renewal test for selected workspace",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        renewed = self.store.renew_scoped_pilot_decision(
            owner_id="owner_default", decision_id=decision["decision_id"], expires_at_ms=self.now + 120_000,
        )
        self.assertEqual(renewed["expires_at_ms"], self.now + 120_000)
        self.assertEqual(renewed["binding_id"], binding["binding_id"])
        self.assertEqual(self.store.admission_status()["admission_mode"], "scoped_pilot")
        with self.assertRaises(ValidationError):
            self.store.renew_scoped_pilot_decision(
                owner_id="owner_default", decision_id=decision["decision_id"], expires_at_ms=self.now + 30_000,
            )
        self.now += 120_000
        with self.assertRaises(ConflictError):
            self.store.renew_scoped_pilot_decision(
                owner_id="owner_default", decision_id=decision["decision_id"], expires_at_ms=self.now + 60_000,
            )

    def test_scoped_pilot_revocation_fences_queued_action_even_after_global_open(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Selected workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self._ready_node()
        self.store.set_admission_mode(mode="recovery")
        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="Short trial for selected workspace",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        intent = self.store.request_mcp_bounded_file_read(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], path="README.md", start_line=1,
            max_lines=10, max_bytes=1024, idempotency_key="pilot-file-read-002",
            facade_contract=FACADE_CONTRACT,
        )
        self.store.revoke_scoped_pilot_decision(owner_id="owner_default", decision_id=decision["decision_id"])
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        self.store.set_admission_mode(mode="open")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        # Simulate an old untagged service action surviving a schema upgrade.
        with self.store._connection() as connection:
            connection.execute(
                "UPDATE actions SET scoped_pilot_decision_id = NULL WHERE action_id = ?",
                (intent["action_id"],),
            )
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        self.assertEqual(self.store.action(owner_id="owner_default", action_id=intent["action_id"])["delivery_state"], "queued")

    def test_shared_service_never_inherits_global_open_and_old_pilot_task_cannot_rebind(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Selected workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        with self.assertRaises(ConflictError):
            self.store.create_mcp_task_session(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], label="Not authorized by global open",
            )
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], path="README.md", start_line=1,
                max_lines=10, max_bytes=1024, idempotency_key="service-open-read-001",
                facade_contract=FACADE_CONTRACT,
            )
        self.store.set_admission_mode(mode="recovery")
        first = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="First task scope",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        task = self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], label="Task pinned to first decision",
        )
        self.assertEqual(task["scoped_pilot_decision_id"], first["decision_id"])
        self.store.set_admission_mode(mode="recovery")
        second = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="Second task scope",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], path="README.md", start_line=1,
                max_lines=10, max_bytes=1024, idempotency_key="old-pilot-task-read-001",
                facade_contract=FACADE_CONTRACT, task_id=task["task_id"],
            )
        self.assertNotEqual(second["decision_id"], first["decision_id"])

    def test_scoped_pilot_decision_rejects_unknown_effect_on_selected_node(self) -> None:
        context, request = self._request()
        self.store.seal_action(
            owner_id="owner_default", request_id=request["request_id"], tool_name="workspace_context",
            arguments={"detail": "compact"}, idempotency_key="unknown-before-pilot-001",
            admission_reference="test", expires_at_ms=self.now + 30_000,
        )
        self._ready_node()
        self.assertEqual(len(self.store.poll_actions(device_id="device-alpha")), 1)
        self.store.set_admission_mode(mode="recovery")
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=context["binding_id"], expires_at_ms=self.now + 120_000,
                reason="Unknown old effect must block selected node",
            )

    def test_scoped_pilot_resumes_after_exact_quarantined_file_read_without_settling_history(self) -> None:
        binding, principal, old_action = self._quarantine_service_file_read_unknown()
        self.store.set_admission_mode(mode="recovery")
        other_principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=other_principal["principal_id"],
                binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000,
                reason="A quarantined file read cannot authorize another service principal",
            )

        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 60_000,
            reason="Resume exact selected binding after audited bounded-read unknown",
        )

        old_observation = self.store.action_observation(
            owner_id="owner_default", action_id=old_action["action_id"],
        )
        self.assertEqual(decision["binding_id"], binding["binding_id"])
        self.assertEqual(old_observation["delivery_state"], "reconcile_required")
        self.assertEqual(old_observation["receipts"][-1]["receipt_state"], "unknown")
        self.assertEqual(old_observation["reconciliation"]["disposition"], "quarantined_unknown")
        self.assertEqual(self.store.poll_actions(device_id="device-alpha", lane="bounded_file_read"), [])
        health = self.store.health()
        self.assertEqual(health["unresolved_action_count"], 1)
        self.assertEqual(health["quarantined_unknown_action_count"], 1)
        self.assertEqual(health["unquarantined_unresolved_action_count"], 0)

        self.store.set_admission_mode(mode="scoped_pilot")
        renewed = self.store.renew_scoped_pilot_decision(
            owner_id="owner_default", decision_id=decision["decision_id"],
            expires_at_ms=self.now + 120_000,
        )
        self.assertEqual(renewed["binding_id"], binding["binding_id"])

    def test_scoped_pilot_stays_blocked_for_quarantined_file_read_with_local_handle(self) -> None:
        binding, principal, _action = self._quarantine_service_file_read_unknown(
            local_handle="local-handle-must-remain-blocking",
        )
        self.store.set_admission_mode(mode="recovery")

        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
                reason="A quarantined file read with a local handle remains blocking",
            )

    def test_scoped_pilot_stays_blocked_when_quarantined_file_read_evidence_digest_drifts(self) -> None:
        binding, principal, action = self._quarantine_service_file_read_unknown()
        self.store.set_admission_mode(mode="recovery")
        with self.store._connection() as connection:
            connection.execute(
                "UPDATE action_reconciliations SET evidence_digest = ? WHERE action_id = ?",
                ("0" * 64, action["action_id"]),
            )

        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
                reason="Tampered quarantine evidence cannot clear the pilot gate",
            )

    def test_scoped_pilot_stays_blocked_when_quarantined_file_read_action_digest_drifts(self) -> None:
        binding, principal, action = self._quarantine_service_file_read_unknown()
        self.store.set_admission_mode(mode="recovery")
        with self.store._connection() as connection:
            connection.execute(
                "UPDATE actions SET action_digest = ? WHERE action_id = ?",
                ("0" * 64, action["action_id"]),
            )

        with self.assertRaises(ConflictError):
            self.store.create_scoped_pilot_decision(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
                reason="Drifted immutable action cannot clear the pilot gate",
            )

    def test_scoped_pilot_exec_is_pinned_to_task_and_exact_target(self) -> None:
        self.store.register_node_workspace(
            device_id="device-alpha", workspace_id="workspace-code", workspace_generation="generation-code-1",
            display_name="Code workspace", capabilities={"read": True, "write": True, "exec": True},
        )
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-code",
            workspace_generation="generation-code-1", display_name="Code workspace",
        )
        other = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Other workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self._ready_node()
        self.store.set_admission_mode(mode="recovery")
        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="Structured command pilot in one code workspace",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        with self.assertRaises(ConflictError):
            self.store.create_mcp_task_session(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=other["binding_id"], label="Wrong workspace",
            )
        task = self.store.create_mcp_task_session(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], label="Selected workspace task",
        )
        with self.assertRaises(ConflictError):
            self.store.request_mcp_exec(
                owner_id="owner_default", principal_id=principal["principal_id"],
                binding_id=binding["binding_id"], argv=["npm", "test"],
                idempotency_key="pilot-exec-no-task-001", facade_contract=FACADE_CONTRACT,
            )
        intent = self.store.request_mcp_exec(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], task_id=task["task_id"], argv=["npm", "test"],
            idempotency_key="pilot-exec-task-001", facade_contract=FACADE_CONTRACT,
        )
        action = self.store.action(owner_id="owner_default", action_id=intent["action_id"])
        self.assertEqual(action["scoped_pilot_decision_id"], decision["decision_id"])
        self.assertEqual(
            [row["action_id"] for row in self.store.poll_actions(device_id="device-alpha", lane="bounded_exec")],
            [intent["action_id"]],
        )

    def test_restore_candidate_closes_scoped_pilot_and_revokes_decision(self) -> None:
        binding = self.store.create_binding(
            owner_id="owner_default", device_id="device-alpha", workspace_id="workspace-alpha",
            workspace_generation="generation-1", display_name="Selected workspace",
        )
        principal = self.store.create_private_tunnel_service_principal(owner_id="owner_default")
        self.store.set_admission_mode(mode="recovery")
        decision = self.store.create_scoped_pilot_decision(
            owner_id="owner_default", principal_id=principal["principal_id"],
            binding_id=binding["binding_id"], expires_at_ms=self.now + 120_000,
            reason="Before recovery snapshot",
        )
        self.store.set_admission_mode(mode="scoped_pilot")
        source = Path(self.tempdir.name) / "scoped-pilot-source.sqlite3"
        receipt = self.store.backup_to(source)
        candidate = Path(self.tempdir.name) / "scoped-pilot-recovery.sqlite3"
        create_recovery_restore_candidate(source, candidate, expected_sha256=str(receipt["snapshot_sha256"]))
        restored = ControlPlaneStore(candidate, clock=lambda: self.now)
        self.assertEqual(restored.admission_status()["admission_mode"], "recovery")
        self.assertIsNotNone(restored.scoped_pilot_decision(
            owner_id="owner_default", decision_id=decision["decision_id"],
        )["revoked_at_ms"])
        with self.assertRaises(ConflictError):
            restored.set_admission_mode(mode="scoped_pilot")

    def test_read_only_bridge_defers_projection_until_request_binding(self) -> None:
        """The bridge must preserve IDs until the only final Python verifier."""
        request = {
            "action_id": "act-node-bridge-0001",
            "attempt_id": "try-node-bridge-0001",
            "facade_contract": dict(FACADE_CONTRACT),
        }
        raw_result = {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "local_handle": "cp_ro_" + "b" * 48,
            "workspace_accessed": True,
            "policy_sha256": "c" * 64,
            "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
            "runtime_identity": {
                "activation_epoch_id": "activation-node-bridge-0001",
                "process_instance_id": "mcp-process-node-bridge-0001",
                "server_instance_id": "mcp-server-node-bridge-0001",
                "tool_contract_sha256": "d" * 64,
            },
            "facade_contract": dict(FACADE_CONTRACT),
            "workspace_summary": {
                "schema_version": 1,
                "project": {"type": "node", "name": "office-fixture", "version": "1.0.0"},
                "entries": [],
                "entries_truncated": False,
                "git": {"is_repo": True, "branch": "main", "changed_count": 0, "truncated": False},
            },
            "workspace_summary_sha256": "f" * 64,
            "response_sha256": "e" * 64,
        }
        args = SimpleNamespace(timeout_seconds=20)
        completed = SimpleNamespace(returncode=0, stdout=json.dumps({"ok": True, "result": raw_result}))
        with mock.patch("control_plane.node_agent._adapter_command", return_value=(["node"], {})), \
             mock.patch("control_plane.node_agent.subprocess.run", return_value=completed):
            result, error = recovery_read_only_bridge(args, Path.cwd(), request)

        self.assertIsNone(error)
        self.assertEqual(result, raw_result)
        self.assertEqual(_safe_bridge_result(result, request)["workspace_accessed"], True)

    def test_read_only_bridge_result_emits_typed_safe_diagnostic_categories(self) -> None:
        request = {
            "action_id": "act-node-bridge-0001",
            "attempt_id": "try-node-bridge-0001",
            "facade_contract": dict(FACADE_CONTRACT),
        }
        result = {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "local_handle": "cp_ro_" + "b" * 48,
            "workspace_accessed": True,
            "policy_sha256": "c" * 64,
            "actor": {"client_id": "electron-control-plane-bridge", "client_type": "electron"},
            "runtime_identity": {
                "activation_epoch_id": "activation-node-bridge-0001",
                "process_instance_id": "mcp-process-node-bridge-0001",
                "server_instance_id": "mcp-server-node-bridge-0001",
                "tool_contract_sha256": "d" * 64,
            },
            "facade_contract": dict(FACADE_CONTRACT),
            "workspace_summary": {
                "schema_version": 1,
                "project": {"type": "node", "name": "office-fixture", "version": "1.0.0"},
                "entries": [],
                "entries_truncated": False,
                "git": {"is_repo": True, "branch": "main", "changed_count": 0, "truncated": False},
            },
            "workspace_summary_sha256": "f" * 64,
            "response_sha256": "e" * 64,
        }
        mutations = {
            "CONTROL_PLANE_BRIDGE_RESULT_ACTION_INVALID": lambda value: value.__setitem__("action_id", "wrong-action-id"),
            "CONTROL_PLANE_BRIDGE_RESULT_SUMMARY_INVALID": lambda value: value.__setitem__("workspace_summary", {"schema_version": 1}),
            "CONTROL_PLANE_BRIDGE_RESULT_IDENTITY_INVALID": lambda value: value.__setitem__("runtime_identity", {}),
            "CONTROL_PLANE_BRIDGE_RESULT_CONTRACT_INVALID": lambda value: value.__setitem__("facade_contract", {}),
            "CONTROL_PLANE_BRIDGE_RESULT_SUMMARY_DIGEST_INVALID": lambda value: value.__setitem__("workspace_summary_sha256", "not-a-digest"),
            "CONTROL_PLANE_BRIDGE_RESULT_DIGEST_INVALID": lambda value: value.__setitem__("response_sha256", "not-a-digest"),
        }
        for code, mutate in mutations.items():
            with self.subTest(code=code):
                invalid = json.loads(json.dumps(result))
                mutate(invalid)
                with self.assertRaisesRegex(RuntimeError, f"^{code}$"):
                    _safe_bridge_result(invalid, request)

    def test_read_only_bridge_requires_canonical_facade_intent_provenance(self) -> None:
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }
        action = {
            "action_id": "act-node-bridge-provenance-0001",
            "attempt_id": "try-node-bridge-provenance-0001",
            "owner_id": "owner-node-bridge-0001",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "workspace_id": "workspace-node-bridge-0001",
            "workspace_generation": "generation-node-bridge-0001",
            "context_id": "ctx-node-bridge-0001",
            "binding_id": "bind-node-bridge-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "mcp_read_only_intent_digest": "f" * 64,
            "admission_reference": "mcp_facade:" + "f" * 64,
            "mcp_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": 2_000_000_000_000,
        }
        request = _read_only_bridge_request(action, config)
        self.assertNotIn("intent_digest", request)
        self.assertEqual(request["facade_contract"], FACADE_CONTRACT)
        for field, value in (
            ("mcp_read_only_intent_digest", None),
            ("mcp_read_only_intent_digest", "not-a-digest"),
            ("admission_reference", "mcp_facade:" + "e" * 64),
            ("mcp_facade_schema_version", 0),
            ("mcp_facade_profile", "bad profile"),
            ("mcp_facade_contract_sha256", "not-a-digest"),
        ):
            rejected = dict(action)
            rejected[field] = value
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_BRIDGE_ACTION_DENIED"):
                _read_only_bridge_request(rejected, config)

    def test_read_only_node_lane_rejects_missing_provenance_before_bridge_effect(self) -> None:
        config_path = Path(self.tempdir.name) / "node-missing-provenance.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }), encoding="utf-8")
        action = {
            "action_id": "act-node-bridge-missing-provenance-0001",
            "attempt_id": "try-node-bridge-missing-provenance-0001",
            "owner_id": "owner-node-bridge-0001",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "workspace_id": "workspace-node-bridge-0001",
            "workspace_generation": "generation-node-bridge-0001",
            "context_id": "ctx-node-bridge-0001",
            "binding_id": "bind-node-bridge-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "expires_at_ms": 2_000_000_000_000,
        }
        requests: list[tuple[str, dict[str, object]]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            requests.append((path, payload))
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            return {"receipt_id": "receipt-node-bridge-missing-provenance-0001"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self._strict_runtime_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self._strict_identity_observation()), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge") as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        bridge.assert_not_called()
        self.assertEqual([path for path, _ in requests], [
            "/v1/nodes/device-node-bridge-0001/poll",
            "/v1/nodes/device-node-bridge-0001/receipts",
        ])
        receipt = requests[-1][1]
        self.assertEqual(receipt["receipt_state"], "rejected")
        self.assertEqual(receipt["payload"], {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "code": "CONTROL_PLANE_BRIDGE_ACTION_DENIED",
        })

    def test_read_only_node_lane_reconciles_a_prepared_effect_as_unknown_without_reexecution(self) -> None:
        config_path = Path(self.tempdir.name) / "node.json"
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        journal_path = _journal_path(config_path)
        _write_json_atomic(journal_path, {
            "schema_version": READ_ONLY_JOURNAL_SCHEMA_VERSION,
            "entries": {
                "act-node-bridge-0002|try-node-bridge-0002": {
                    "state": "prepared",
                    "action_id": "act-node-bridge-0002",
                    "attempt_id": "try-node-bridge-0002",
                }
            },
        })
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertTrue(path.endswith("/receipts"), "prepared recovery must settle before any new poll")
            receipts.append(payload)
            return {"receipt_id": "receipt-node-bridge-0002"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge") as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        bridge.assert_not_called()
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["local_handle"], "")
        self.assertEqual(receipts[0]["payload"], {
            "schema_version": 1,
            "operation_kind": "control_plane_read_only_workspace_context",
            "code": "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
            "diagnostic_code": "CONTROL_PLANE_BRIDGE_PREPARED_RECOVERED",
        })
        journal = _read_journal(journal_path)
        entry = journal["entries"]["act-node-bridge-0002|try-node-bridge-0002"]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

    def test_read_only_node_lane_terminalizes_an_unexpected_post_prepare_failure(self) -> None:
        config_path = Path(self.tempdir.name) / "node-post-prepare-failure.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }), encoding="utf-8")
        action = {
            "action_id": "act-node-bridge-post-prepare-0001",
            "attempt_id": "try-node-bridge-post-prepare-0001",
            "owner_id": "owner-node-bridge-0001",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "workspace_id": "workspace-node-bridge-0001",
            "workspace_generation": "generation-node-bridge-0001",
            "context_id": "ctx-node-bridge-0001",
            "binding_id": "bind-node-bridge-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "mcp_read_only_intent_digest": "f" * 64,
            "admission_reference": "mcp_facade:" + "f" * 64,
            "mcp_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": 2_000_000_000_000,
        }
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-node-bridge-post-prepare-0001"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self._strict_runtime_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self._strict_identity_observation()), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge", return_value=(None, "CONTROL_PLANE_BRIDGE_RESULT_INVALID")) as bridge, \
             mock.patch("control_plane.node_agent._record_local_receipt", side_effect=RuntimeError("CONTROL_PLANE_BRIDGE_RESULT_INVALID")):
            self.assertEqual(poll_read_only_once(args), 0)

        bridge.assert_called_once()
        self.assertEqual(receipts, [{
            "action_id": action["action_id"],
            "attempt_id": action["attempt_id"],
            "receipt_state": "unknown",
            "local_handle": "",
            "payload": {
                "schema_version": 1,
                "operation_kind": "control_plane_read_only_workspace_context",
                "code": "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_BRIDGE_RESULT_INVALID",
            },
        }])
        journal = _read_journal(_journal_path(config_path))
        entry = journal["entries"][f"{action['action_id']}|{action['attempt_id']}"]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

    def test_node_agent_subprocess_crash_after_prepared_marker_recovers_unknown_without_bridge_reexecution(self) -> None:
        config_path = Path(self.tempdir.name) / "node-subprocess-crash.json"
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        action = {
            "action_id": "act-node-bridge-subprocess-crash-0001",
            "attempt_id": "try-node-bridge-subprocess-crash-0001",
            "owner_id": "owner-node-bridge-0001",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "workspace_id": "workspace-node-bridge-0001",
            "workspace_generation": "generation-node-bridge-0001",
            "context_id": "ctx-node-bridge-0001",
            "binding_id": "bind-node-bridge-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "mcp_read_only_intent_digest": "f" * 64,
            "admission_reference": "mcp_facade:" + "f" * 64,
            "mcp_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": 2_000_000_000_000,
        }
        crash_script = """
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from control_plane import node_agent

config_path = Path(sys.argv[1])
project_root = Path(sys.argv[2])
action = json.loads(sys.argv[3])
strict_status = {
    'state': 'CURRENT', 'host': 'available', 'installation': 'current',
    'mcp_update_pending': 'false', 'mcp_running_revision': 'sha-current',
    'mcp_disk_revision': 'sha-current', 'components_ready': 'true',
    'fully_ready': 'true', 'runtime_update_incomplete': 'false',
    'runtime_telemetry_available': 'true', 'runtime_signal_stale': 'false',
    'connector_state': 'CURRENT_ACKNOWLEDGED', 'connector_rediscovered': 'true',
    'connector_rediscovered_at': '2026-09-15T00:00:00Z',
    'connector_freshness_mode': 'current_process_discovery',
    'connector_refresh_required': 'false', 'connector_ack_pending': 'false',
    'connector_current_sha': 'sha-current', 'connector_ack_sha': 'sha-current',
    'error_code': 'none',
}
identity = {
    'observation_schema_version': 1, 'observation_kind': 'mcp_identity_read_only',
    'mcp_ready': True, 'identity_current': True,
    'mcp_process_instance_id': 'mcp-process-node-bridge-0001',
    'mcp_server_instance_id': 'mcp-server-node-bridge-0001',
    'activation_epoch_id': 'activation-node-bridge-0001',
    'current_activation_epoch_id': 'activation-node-bridge-0001',
    'tool_contract_sha256': 'a' * 64,
}
def request(_url, path, _payload, _authorization=None):
    if path.endswith('/poll'):
        return {'actions': [action]}
    raise AssertionError('node process must exit before submitting a receipt')
def crash_bridge(*_args):
    os._exit(73)
args = SimpleNamespace(config=str(config_path), project_root=str(project_root), node='node', timeout_seconds=20, limit=1)
with mock.patch('control_plane.node_agent._request', side_effect=request), \
     mock.patch('control_plane.node_agent._runtime_status', return_value=strict_status), \
     mock.patch('control_plane.node_agent.recovery_identity_observation', return_value=identity), \
     mock.patch('control_plane.node_agent.recovery_read_only_bridge', side_effect=crash_bridge):
    node_agent.poll_read_only_once(args)
"""
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        crashed = subprocess.run(
            [sys.executable, "-c", crash_script, str(config_path), str(Path.cwd()), json.dumps(action)],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertEqual(crashed.returncode, 73, crashed.stderr)
        journal_path = _journal_path(config_path)
        journal = _read_journal(journal_path)
        entry = journal["entries"]["act-node-bridge-subprocess-crash-0001|try-node-bridge-subprocess-crash-0001"]
        self.assertEqual(entry, {
            "state": "prepared",
            "action_id": action["action_id"],
            "attempt_id": action["attempt_id"],
        })
        receipts: list[dict[str, object]] = []

        def recovery_request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertTrue(path.endswith("/receipts"), "prepared crash recovery must settle before any poll")
            receipts.append(payload)
            return {"receipt_id": "receipt-node-bridge-subprocess-crash-0001"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=recovery_request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge") as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        bridge.assert_not_called()
        self.assertEqual(receipts, [{
            "action_id": action["action_id"],
            "attempt_id": action["attempt_id"],
            "receipt_state": "unknown",
            "local_handle": "",
            "payload": {
                "schema_version": 1,
                "operation_kind": "control_plane_read_only_workspace_context",
                "code": "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
                "diagnostic_code": "CONTROL_PLANE_BRIDGE_PREPARED_RECOVERED",
            },
        }])
        journal = _read_journal(journal_path)
        entry = journal["entries"]["act-node-bridge-subprocess-crash-0001|try-node-bridge-subprocess-crash-0001"]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

    def test_read_only_bridge_timeout_is_unknown_and_never_reexecuted_for_a_duplicate_action(self) -> None:
        config_path = Path(self.tempdir.name) / "node-bridge-timeout.json"
        config_path.write_text(json.dumps({
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-timeout-0001",
            "endpoint_id": "endpoint-node-bridge-timeout-0001",
            "node_secret": "node-secret-not-printed",
        }), encoding="utf-8")
        action = {
            "action_id": "act-node-bridge-timeout-0001",
            "attempt_id": "try-node-bridge-timeout-0001",
            "owner_id": "owner-node-bridge-timeout-0001",
            "device_id": "device-node-bridge-timeout-0001",
            "endpoint_id": "endpoint-node-bridge-timeout-0001",
            "workspace_id": "workspace-node-bridge-timeout-0001",
            "workspace_generation": "generation-node-bridge-timeout-0001",
            "context_id": "ctx-node-bridge-timeout-0001",
            "binding_id": "bind-node-bridge-timeout-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({"detail": "compact", "max_entries": 1}),
            "mcp_read_only_intent_digest": "f" * 64,
            "admission_reference": "mcp_facade:" + "f" * 64,
            "mcp_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": 2_000_000_000_000,
        }
        requests: list[tuple[str, dict[str, object]]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            requests.append((path, payload))
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            self.assertEqual(payload, {
                "action_id": action["action_id"],
                "attempt_id": action["attempt_id"],
                "receipt_state": "unknown",
                "local_handle": "",
                "payload": {
                    "schema_version": 1,
                    "operation_kind": "control_plane_read_only_workspace_context",
                    "code": "CONTROL_PLANE_BRIDGE_EFFECT_UNKNOWN",
                    "diagnostic_code": "CONTROL_PLANE_BRIDGE_TIMEOUT",
                },
            })
            return {"receipt_id": "receipt-node-bridge-timeout-0001"}

        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self._strict_runtime_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self._strict_identity_observation()), \
             mock.patch("control_plane.node_agent._harden_windows_private_file"), \
             mock.patch(
                 "control_plane.node_agent.subprocess.run",
                 side_effect=subprocess.TimeoutExpired(cmd=["node"], timeout=args.timeout_seconds),
             ) as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        self.assertEqual(bridge.call_count, 1)
        journal = _read_journal(_journal_path(config_path))
        entry = journal["entries"]["act-node-bridge-timeout-0001|try-node-bridge-timeout-0001"]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

        # If a transport delivered the same sealed action again, the durable
        # unknown record wins over any bridge retry.
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self._strict_runtime_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self._strict_identity_observation()), \
             mock.patch("control_plane.node_agent._harden_windows_private_file"), \
             mock.patch("control_plane.node_agent.subprocess.run") as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        bridge.assert_not_called()
        self.assertEqual([path for path, _ in requests], [
            "/v1/nodes/device-node-bridge-timeout-0001/poll",
            "/v1/nodes/device-node-bridge-timeout-0001/receipts",
            "/v1/nodes/device-node-bridge-timeout-0001/poll",
        ])

    def test_node_transport_failure_is_a_typed_safe_error(self) -> None:
        with mock.patch(
            "control_plane.node_agent.urllib.request.urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_TRANSPORT_UNAVAILABLE$"):
                _request("https://control.example.test", "/healthz", {})

    def test_read_only_node_lane_replays_durable_receipt_after_transport_failure_without_reexecution(self) -> None:
        config_path = Path(self.tempdir.name) / "node-receipt-replay.json"
        config = {
            "server_url": "https://control.example.test",
            "device_id": "device-node-bridge-0001",
            "endpoint_id": "endpoint-node-bridge-0001",
            "node_secret": "node-secret-not-printed",
        }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        journal_path = _journal_path(config_path)
        _write_json_atomic(journal_path, {
            "schema_version": READ_ONLY_JOURNAL_SCHEMA_VERSION,
            "entries": {
                "act-node-bridge-replay-0001|try-node-bridge-replay-0001": {
                    "state": "completed",
                    "action_id": "act-node-bridge-replay-0001",
                    "attempt_id": "try-node-bridge-replay-0001",
                    "receipt": {
                        "action_id": "act-node-bridge-replay-0001",
                        "attempt_id": "try-node-bridge-replay-0001",
                        "receipt_state": "completed",
                        "local_handle": "cp_ro_" + "b" * 48,
                        "payload": {
                            "schema_version": 1,
                            "operation_kind": "control_plane_read_only_workspace_context",
                            "workspace_accessed": True,
                            "response_sha256": "e" * 64,
                        },
                        "receipt_submitted": False,
                    },
                },
            },
        })
        args = SimpleNamespace(config=str(config_path), project_root=str(Path.cwd()), node="node", timeout_seconds=20, limit=1)
        receipt_calls: list[dict[str, object]] = []

        def unavailable_request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertTrue(path.endswith("/receipts"), "pending receipt must flush before a new poll")
            receipt_calls.append(payload)
            raise RuntimeError("CONTROL_PLANE_TRANSPORT_UNAVAILABLE")

        with mock.patch("control_plane.node_agent._request", side_effect=unavailable_request), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge") as bridge:
            with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_TRANSPORT_UNAVAILABLE$"):
                poll_read_only_once(args)
        bridge.assert_not_called()
        journal = _read_journal(journal_path)
        entry = journal["entries"]["act-node-bridge-replay-0001|try-node-bridge-replay-0001"]
        self.assertEqual(entry["state"], "completed")
        self.assertFalse(entry["receipt"]["receipt_submitted"])

        def recovered_request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertTrue(path.endswith("/receipts"), "receipt recovery must not fetch new work")
            receipt_calls.append(payload)
            return {"receipt_id": "receipt-node-bridge-replay-0001", "replayed": True}

        with mock.patch("control_plane.node_agent._request", side_effect=recovered_request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent.recovery_read_only_bridge") as bridge:
            self.assertEqual(poll_read_only_once(args), 0)
        bridge.assert_not_called()
        self.assertEqual(len(receipt_calls), 2)
        self.assertEqual(receipt_calls[0], receipt_calls[1])
        journal = _read_journal(journal_path)
        entry = journal["entries"]["act-node-bridge-replay-0001|try-node-bridge-replay-0001"]
        self.assertEqual(entry["state"], "completed")
        self.assertTrue(entry["receipt"]["receipt_submitted"])
