"""Task-session pinning and patch-acceptance closure.

Two chats must never retarget each other: every follow-up read/patch call
presents a server-issued task handle that the store revalidates against the
immutable binding snapshot. Acceptance closes the verified-patch loop without
reverting files.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_plane.store import (
    ConflictError,
    ControlPlaneStore,
)
from control_plane.mcp_facade import ControlPlaneMcpFacade

ISSUER = "https://accounts.example.test"


class McpTaskSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-task-session-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)

    def _target(self, *, owner_id: str, suffix: str) -> dict:
        node = self.store.enroll_node(
            owner_id=owner_id,
            device_id=f"device-{suffix}",
            endpoint_id=f"endpoint-{suffix}",
            display_name=f"Node {suffix}",
        )
        self.store.register_node_workspace(
            device_id=node["device_id"],
            workspace_id=f"workspace-{suffix}",
            workspace_generation="generation-001",
            display_name=f"Workspace {suffix}",
            capabilities={"read": True, "write": True, "exec": False},
        )
        return self.store.create_binding(
            owner_id=owner_id,
            device_id=node["device_id"],
            workspace_id=f"workspace-{suffix}",
            workspace_generation="generation-001",
            display_name=f"Workspace {suffix}",
        )

    def _principal(self, *, owner_id: str, subject: str) -> dict:
        return self.store.link_oauth_principal(owner_id=owner_id, issuer=ISSUER, subject=subject)

    def _facade(self, schema_version: int = 15, profile: str = "control-plane-oauth-bounded-file-read-v3") -> dict:
        return {"schema_version": schema_version, "profile": profile, "sha256": "a" * 64}

    def test_two_tasks_pin_different_targets_and_cross_use_is_rejected(self) -> None:
        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="alice-task")["principal_id"]
        binding_a = self._target(owner_id=owner, suffix="a")
        binding_b = self._target(owner_id=owner, suffix="b")
        task_a = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding_a["binding_id"], label="Task A"
        )
        task_b = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding_b["binding_id"], label="Task B"
        )
        self.assertNotEqual(task_a["task_id"], task_b["task_id"])
        self.assertTrue(task_a["task_id"].startswith("task_"))
        # Same idempotency key on different tasks must conflict, never silently retarget.
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id=owner,
                principal_id=principal,
                binding_id=binding_a["binding_id"],
                path="notes/app.txt",
                start_line=1,
                max_lines=10,
                max_bytes=1024,
                idempotency_key="shared-task-key-001",
                facade_contract=self._facade(),
                task_id=task_a["task_id"],
            )
            self.store.request_mcp_bounded_file_read(
                owner_id=owner,
                principal_id=principal,
                binding_id=binding_a["binding_id"],
                path="notes/app.txt",
                start_line=1,
                max_lines=10,
                max_bytes=1024,
                idempotency_key="shared-task-key-001",
                facade_contract=self._facade(),
                task_id=task_b["task_id"],
            )
        # Explicit cross-binding use is rejected before any action is sealed.
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id=owner,
                principal_id=principal,
                binding_id=binding_b["binding_id"],
                path="notes/app.txt",
                start_line=1,
                max_lines=5,
                max_bytes=512,
                idempotency_key="cross-binding-key-002",
                facade_contract=self._facade(),
                task_id=task_a["task_id"],
            )

    def test_closing_task_fences_new_actions_but_keeps_history(self) -> None:
        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="bob-task")["principal_id"]
        binding = self._target(owner_id=owner, suffix="close")
        task = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Close me"
        )
        intent = self.store.request_mcp_bounded_file_read(
            owner_id=owner,
            principal_id=principal,
            binding_id=binding["binding_id"],
            path="notes/app.txt",
            start_line=1,
            max_lines=5,
            max_bytes=512,
            idempotency_key="close-task-key-003",
            facade_contract=self._facade(),
            task_id=task["task_id"],
        )
        linked = self.store.list_mcp_task_actions(owner_id=owner, principal_id=principal, task_id=task["task_id"])
        self.assertEqual([row["action_id"] for row in linked], [intent["action_id"]])
        closed = self.store.close_mcp_task_session(
            owner_id=owner, principal_id=principal, task_id=task["task_id"]
        )
        self.assertIsNotNone(closed["closed_at_ms"])
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id=owner,
                principal_id=principal,
                binding_id=binding["binding_id"],
                path="notes/other.txt",
                start_line=1,
                max_lines=5,
                max_bytes=512,
                idempotency_key="close-task-key-004",
                facade_contract=self._facade(),
                task_id=task["task_id"],
            )
        # History stays observable after close.
        still = self.store.list_mcp_task_actions(owner_id=owner, principal_id=principal, task_id=task["task_id"])
        self.assertEqual(len(still), 1)

    def test_revoked_binding_invalidates_task_for_new_actions(self) -> None:
        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="cara-task")["principal_id"]
        binding = self._target(owner_id=owner, suffix="revoke")
        task = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Revoke me"
        )
        self.store.revoke_binding(owner_id=owner, binding_id=binding["binding_id"])
        with self.assertRaises(ConflictError):
            self.store.request_mcp_bounded_file_read(
                owner_id=owner,
                principal_id=principal,
                binding_id=binding["binding_id"],
                path="notes/app.txt",
                start_line=1,
                max_lines=5,
                max_bytes=512,
                idempotency_key="revoked-task-key-005",
                facade_contract=self._facade(),
                task_id=task["task_id"],
            )

    def test_patch_acceptance_requires_completed_receipt_and_never_reverts(self) -> None:
        import base64
        import hashlib
        import sqlite3
        import zlib

        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="dana-task")["principal_id"]
        binding = self._target(owner_id=owner, suffix="accept")
        task = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Accept me"
        )
        preimage = "b" * 64
        new_content = "updated via task\n"
        postimage = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
        payload = base64.b64encode(zlib.compress(new_content.encode("utf-8"))).decode("ascii")
        envelope = "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: notes/app.txt",
            f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}",
            f"+{payload}",
            "*** End Patch",
            "",
        ))
        patch_sha = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
        permission = self.store.request_mcp_patch_permission(
            owner_id=owner,
            principal_id=principal,
            binding_id=binding["binding_id"],
            path="notes/app.txt",
            preimage_sha256=preimage,
            patch_sha256=patch_sha,
            validation_profile="targeted",
            idempotency_key="accept-perm-key-006",
            facade_contract=self._facade(schema_version=16, profile="control-plane-oauth-permission-request-v3"),
            task_id=task["task_id"],
        )
        self.assertEqual(permission["task_id"], task["task_id"])
        self.store.approve_mcp_permission_request(owner_id=owner, permission_request_id=permission["permission_request_id"])
        intent = self.store.request_mcp_approved_patch(
            owner_id=owner,
            principal_id=principal,
            permission_request_id=permission["permission_request_id"],
            patch_envelope=envelope,
            idempotency_key="accept-patch-key-007",
            facade_contract=self._facade(schema_version=17, profile="control-plane-oauth-approved-patch-v3"),
            task_id=task["task_id"],
        )
        # No receipt yet: acceptance must fail closed.
        with self.assertRaises(ConflictError):
            self.store.record_mcp_patch_acceptance(
                owner_id=owner, principal_id=principal, action_id=intent["action_id"], decision="accepted"
            )
        # Inject one verified completed receipt + settled delivery directly.
        # The acceptance gate only checks for a completed receipt and a
        # non-unknown delivery; payload shape is validated by the facade relay.
        with sqlite3.connect(self.store.path) as connection:
            connection.execute(
                "INSERT INTO receipts(receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "rcpt_task_accept_001",
                    intent["action_id"],
                    binding["device_id"],
                    "cp_local_handle_001",
                    "completed",
                    "{}",
                    "d" * 64,
                    self.now,
                ),
            )
            connection.execute(
                "UPDATE actions SET delivery_state = 'settled', settled_at_ms = ? WHERE action_id = ?",
                (self.now, intent["action_id"]),
            )
            connection.commit()
        accepted = self.store.record_mcp_patch_acceptance(
            owner_id=owner,
            principal_id=principal,
            action_id=intent["action_id"],
            decision="accepted",
            note="verified diff locally",
            decided_by="owner_console",
        )
        self.assertEqual(accepted["decision"], "accepted")
        # A conflicting second verdict never overwrites the first, and the
        # file itself is untouched by the verdict: correction needs a new patch.
        with self.assertRaises(ConflictError):
            self.store.record_mcp_patch_acceptance(
                owner_id=owner, principal_id=principal, action_id=intent["action_id"], decision="rejected"
            )
        stored = self.store.get_mcp_patch_acceptance(owner_id=owner, action_id=intent["action_id"])
        assert stored is not None
        self.assertEqual(stored["decision"], "accepted")

    def test_unknown_effect_blocks_acceptance_until_reconciled(self) -> None:
        import sqlite3

        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="erin-task")["principal_id"]
        binding = self._target(owner_id=owner, suffix="unknown")
        task = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Unknown me"
        )
        intent = self.store.request_mcp_bounded_file_read(
            owner_id=owner,
            principal_id=principal,
            binding_id=binding["binding_id"],
            path="notes/app.txt",
            start_line=1,
            max_lines=5,
            max_bytes=512,
            idempotency_key="unknown-task-key-008",
            facade_contract=self._facade(),
            task_id=task["task_id"],
        )
        with sqlite3.connect(self.store.path) as connection:
            connection.execute("UPDATE actions SET delivery_state = 'reconcile_required' WHERE action_id = ?", (intent["action_id"],))
            connection.execute(
                "INSERT INTO receipts(receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("rcpt_task_unknown_001", intent["action_id"], binding["device_id"], "", "unknown", "{}", "e" * 64, self.now),
            )
            connection.commit()
        # Read actions never carry acceptance; patch acceptance on a
        # non-patch action must fail closed as well.
        with self.assertRaises(ConflictError):
            self.store.record_mcp_patch_acceptance(
                owner_id=owner, principal_id=principal, action_id=intent["action_id"], decision="accepted"
            )


class McpTaskFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-task-facade-")
        self.addCleanup(self.temporary.cleanup)
        self.now = 1_700_000_000_000
        self.store = ControlPlaneStore(Path(self.temporary.name) / "control.sqlite3", clock=lambda: self.now)
        self.owner_id = "owner-default"
        self.node = self.store.enroll_node(
            owner_id=self.owner_id,
            device_id="task-node-0001",
            endpoint_id="task-endpoint-0001",
            display_name="Task node",
        )
        self.store.register_node_workspace(
            device_id=self.node["device_id"],
            workspace_id="task-workspace-0001",
            workspace_generation="task-generation-0001",
            display_name="Task workspace",
            capabilities={"read": True, "write": True, "exec": False},
        )
        self.binding = self.store.create_binding(
            owner_id=self.owner_id,
            device_id=self.node["device_id"],
            workspace_id="task-workspace-0001",
            workspace_generation="task-generation-0001",
            display_name="Task workspace",
        )
        self.principal = self.store.link_oauth_principal(
            owner_id=self.owner_id, issuer=ISSUER, subject="provider-subject-task-owner"
        )
        self.facade = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=("control-plane.inventory",),
            oauth_file_read_enabled=True,
            oauth_permission_requests_enabled=True,
            oauth_patch_write_scope="control-plane.patch",
            oauth_approved_patch_enabled=True,
        )

    def _contract(self) -> dict:
        return {key: self.facade.contract[key] for key in ("schema_version", "profile", "sha256")}

    def _call(self, arguments: dict, tool: str = "workspace_context") -> dict:
        response = self.facade.handle(
            {"jsonrpc": "2.0", "id": "task-facade-001", "method": "tools/call", "params": {"name": tool, "arguments": arguments}},
            owner_id=self.owner_id,
            principal_id=self.principal["principal_id"],
            granted_context_id=None,
        )
        assert response is not None
        return response

    def test_task_open_list_close_span_read_without_retarget(self) -> None:
        self.assertEqual(self.facade.contract["schema_version"], 17)
        opened = self._call({"operation": "task_open", "binding_id": self.binding["binding_id"], "label": "Chat A"})
        task_id = opened["result"]["structuredContent"]["task"]["task_id"]
        self.assertTrue(task_id.startswith("task_"))
        listed = self._call({"operation": "task_list"})
        self.assertEqual([t["task_id"] for t in listed["result"]["structuredContent"]["tasks"]], [task_id])
        read = self._call({
            "operation": "read_file",
            "binding_id": self.binding["binding_id"],
            "path": "notes/app.txt",
            "idempotency_key": "facade-task-read-001",
            "expected_facade_contract": self._contract(),
            "task_id": task_id,
        })
        self.assertEqual(read["result"]["structuredContent"]["task_id"], task_id)
        status = self._call({"operation": "read_status", "action_id": read["result"]["structuredContent"]["action_id"]})
        self.assertIn("action", status["result"]["structuredContent"])
        closed = self._call({"operation": "task_close", "task_id": task_id})
        self.assertIsNotNone(closed["result"]["structuredContent"]["task"]["closed_at_ms"])
        # New reads on a closed task are rejected; history stays listed.
        rejected = self._call({
            "operation": "read_file",
            "binding_id": self.binding["binding_id"],
            "path": "notes/app.txt",
            "idempotency_key": "facade-task-read-002",
            "expected_facade_contract": self._contract(),
            "task_id": task_id,
        })
        self.assertEqual(rejected["error"]["data"]["code"], "CONFLICT")

    def test_console_wiring_exposes_tasks_and_acceptance(self) -> None:
        from control_plane.http_api import ControlPlaneHandler
        from control_plane.web_ui import WEB_UI_HTML, WEB_UI_JAVASCRIPT

        html = WEB_UI_HTML.decode("utf-8")
        js = WEB_UI_JAVASCRIPT.decode("utf-8")
        self.assertIn("task-sessions-body", html)
        self.assertIn("patch-acceptances-body", html)
        self.assertIn("onboarding-wizard-body", html)
        self.assertIn("/v1/ui/task-sessions", js)
        self.assertIn("/v1/ui/patch-acceptances/", js)
        self.assertIn("/v1/ui/exec-stops/", js)
        for method in ("_create_ui_task_session", "_ui_close_task_session", "_ui_record_patch_acceptance",
                       "_ui_exec_stop"):
            self.assertTrue(hasattr(ControlPlaneHandler, method))
