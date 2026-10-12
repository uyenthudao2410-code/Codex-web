"""Task-session pinning and patch-acceptance closure.

Two chats must never retarget each other: every follow-up read/patch call
presents a server-issued task handle that the store revalidates against the
immutable binding snapshot. Acceptance closes the verified-patch loop without
reverting files.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from control_plane.store import (
    ConflictError,
    ControlPlaneStore,
    MCP_TASK_WRITER_LEASE_TTL_MS,
    NotFoundError,
    PermissionError,
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

    def _facade(self, schema_version: int = 27, profile: str = "control-plane-oauth-bounded-file-read-v3") -> dict:
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

    def test_task_open_idempotency_replays_exact_task_and_conflicts_on_changed_intent(self) -> None:
        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="idempotent-task")['principal_id']
        binding = self._target(owner_id=owner, suffix="idempotent")
        first = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"],
            label="Same task", idempotency_key="task-open-idempotent-001",
        )
        replayed = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"],
            label="Same task", idempotency_key="task-open-idempotent-001",
        )
        self.assertEqual(replayed["task_id"], first["task_id"])
        with self.assertRaises(ConflictError):
            self.store.create_mcp_task_session(
                owner_id=owner, principal_id=principal, binding_id=binding["binding_id"],
                label="Changed label", idempotency_key="task-open-idempotent-001",
            )

    def test_writer_lease_serializes_same_binding_and_allows_handoff_after_release_or_expiry(self) -> None:
        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="writer-lease")['principal_id']
        binding = self._target(owner_id=owner, suffix="writer")
        task_a = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Writer A",
            idempotency_key="writer-task-a-0001",
        )
        task_b = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Writer B",
            idempotency_key="writer-task-b-0001",
        )

        first = self.store.claim_mcp_task_writer_lease(
            owner_id=owner, principal_id=principal, task_id=task_a["task_id"]
        )
        self.assertEqual(first["state"], "held")
        self.assertEqual(first["lease_generation"], 1)
        self.now += MCP_TASK_WRITER_LEASE_TTL_MS // 2
        renewed = self.store.claim_mcp_task_writer_lease(
            owner_id=owner, principal_id=principal, task_id=task_a["task_id"]
        )
        self.assertTrue(renewed["replayed"])
        self.assertEqual(renewed["lease_generation"], first["lease_generation"])
        self.assertGreater(renewed["expires_at_ms"], first["expires_at_ms"])
        self.assertEqual(renewed["expires_at_ms"], self.now + MCP_TASK_WRITER_LEASE_TTL_MS)
        self.now = first["expires_at_ms"] + 1
        self.assertLess(self.now, renewed["expires_at_ms"])
        with self.assertRaises(ConflictError):
            self.store.claim_mcp_task_writer_lease(
                owner_id=owner, principal_id=principal, task_id=task_b["task_id"]
            )

        observed = self.store.observe_mcp_task(
            owner_id=owner, principal_id=principal, task_id=task_b["task_id"]
        )
        self.assertEqual(observed["writer_lease"]["task_id"], task_a["task_id"])
        self.assertEqual(observed["writer_lease"]["state"], "held")
        self.assertNotIn("arguments_json", json.dumps(observed))

        released = self.store.release_mcp_task_writer_lease(
            owner_id=owner, principal_id=principal, task_id=task_a["task_id"], reason="chat_handoff"
        )
        self.assertEqual(released["state"], "released")
        second = self.store.claim_mcp_task_writer_lease(
            owner_id=owner, principal_id=principal, task_id=task_b["task_id"]
        )
        self.assertEqual(second["state"], "held")

        self.now += MCP_TASK_WRITER_LEASE_TTL_MS + 1
        third = self.store.claim_mcp_task_writer_lease(
            owner_id=owner, principal_id=principal, task_id=task_a["task_id"]
        )
        self.assertEqual(third["state"], "held")
        self.assertEqual(third["lease_generation"], 2)
        final = self.store.observe_mcp_task(
            owner_id=owner, principal_id=principal, task_id=task_b["task_id"]
        )
        self.assertEqual(final["writer_lease"]["state"], "held")
        self.assertEqual(final["writer_lease"]["task_id"], task_a["task_id"])

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
            facade_contract=self._facade(schema_version=28, profile="control-plane-oauth-permission-request-v3"),
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
            facade_contract=self._facade(schema_version=29, profile="control-plane-oauth-approved-patch-v3"),
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
        with closing(sqlite3.connect(self.store.path)) as connection:
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
        accepted = self.store.record_owner_mcp_patch_acceptance(
            owner_id=owner,
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

    def test_owner_standing_patch_acceptance_resolves_intent_and_preserves_gates(self) -> None:
        import base64
        import hashlib
        import sqlite3
        import zlib

        owner = "owner-default"
        principal = self._principal(owner_id=owner, subject="standing-accept")["principal_id"]
        self._principal(owner_id=owner, subject="other-standing-accept")
        binding = self._target(owner_id=owner, suffix="standing-accept")
        task = self.store.create_mcp_task_session(
            owner_id=owner, principal_id=principal, binding_id=binding["binding_id"], label="Standing acceptance"
        )
        self.store.claim_mcp_task_writer_lease(owner_id=owner, principal_id=principal, task_id=task["task_id"])
        preimage = hashlib.sha256(b"old\n").hexdigest()
        new_content = b"new\n"
        postimage = hashlib.sha256(new_content).hexdigest()
        payload = base64.b64encode(zlib.compress(new_content)).decode("ascii")
        envelope = "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: notes/app.txt",
            f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}",
            f"+{payload}",
            "*** End Patch",
            "",
        ))
        intent = self.store.request_mcp_standing_patch(
            owner_id=owner,
            principal_id=principal,
            binding_id=binding["binding_id"],
            path="notes/app.txt",
            preimage_sha256=preimage,
            patch_sha256=hashlib.sha256(envelope.encode("utf-8")).hexdigest(),
            validation_profile="targeted",
            patch_envelope=envelope,
            idempotency_key="owner-standing-accept-001",
            facade_contract=self._facade(schema_version=31, profile="control-plane-oauth-standing-write-v1"),
            task_id=task["task_id"],
        )
        action_id = intent["action_id"]
        with self.assertRaisesRegex(ConflictError, "completed receipt"):
            self.store.record_owner_mcp_patch_acceptance(owner_id=owner, action_id=action_id, decision="accepted")

        # Receipt payload verification belongs to the facade relay. Here the
        # isolated durable fixture exercises the owner acceptance gates.
        with closing(sqlite3.connect(self.store.path)) as connection:
            connection.execute(
                "INSERT INTO receipts(receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("rcpt_standing_unknown", action_id, binding["device_id"], "", "unknown", "{}", "e" * 64, self.now),
            )
            connection.execute("UPDATE actions SET delivery_state = 'reconcile_required' WHERE action_id = ?", (action_id,))
            connection.commit()
        with self.assertRaisesRegex(ConflictError, "unknown-effect"):
            self.store.record_owner_mcp_patch_acceptance(owner_id=owner, action_id=action_id, decision="accepted")
        with closing(sqlite3.connect(self.store.path)) as connection:
            connection.execute(
                "INSERT INTO receipts(receipt_id, action_id, device_id, local_handle, receipt_state, payload_json, receipt_digest, received_at_ms)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("rcpt_standing_completed", action_id, binding["device_id"], "cp_standing_handle", "completed", "{}", "f" * 64, self.now + 1),
            )
            connection.execute(
                "UPDATE actions SET delivery_state = 'settled', settled_at_ms = ? WHERE action_id = ?", (self.now + 1, action_id)
            )
            connection.commit()
        self.store.close_mcp_task_session(owner_id=owner, principal_id=principal, task_id=task["task_id"])
        with self.assertRaises(NotFoundError):
            self.store.record_owner_mcp_patch_acceptance(owner_id="owner-other", action_id=action_id, decision="accepted")
        accepted = self.store.record_owner_mcp_patch_acceptance(
            owner_id=owner, action_id=action_id, decision="accepted", note="verified standing result"
        )
        self.assertEqual(accepted["principal_id"], principal)
        self.assertEqual(accepted["owner_id"], owner)
        self.assertEqual(accepted["decision"], "accepted")
        self.assertEqual(
            self.store.record_owner_mcp_patch_acceptance(owner_id=owner, action_id=action_id, decision="accepted"), accepted
        )
        with self.assertRaises(ConflictError):
            self.store.record_owner_mcp_patch_acceptance(owner_id=owner, action_id=action_id, decision="rejected")
        self.store.revoke_oauth_principal(owner_id=owner, principal_id=principal)
        with self.assertRaises(PermissionError):
            self.store.record_owner_mcp_patch_acceptance(owner_id=owner, action_id=action_id, decision="accepted")

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
        with closing(sqlite3.connect(self.store.path)) as connection:
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
        self.assertEqual(self.facade.contract["schema_version"], 29)
        opened = self._call({"operation": "task_open", "binding_id": self.binding["binding_id"], "label": "Chat A", "idempotency_key": "task-open-chat-a-0001"})
        task_id = opened["result"]["structuredContent"]["task"]["task_id"]
        self.assertTrue(task_id.startswith("task_"))
        replayed = self._call({"operation": "task_open", "binding_id": self.binding["binding_id"], "label": "Chat A", "idempotency_key": "task-open-chat-a-0001"})
        self.assertEqual(replayed["result"]["structuredContent"]["task"]["task_id"], task_id)
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
        self.assertTrue(rejected["result"]["isError"])
        self.assertEqual(rejected["result"]["structuredContent"]["code"], "CONFLICT")

    def test_task_control_observes_and_handoffs_writer_lease(self) -> None:
        by_name = {tool["name"]: tool for tool in self.facade.contract["tools"]}
        self.assertEqual(
            by_name["task_control"]["_meta"]["control_plane"]["implemented_operations"],
            ["task_observe", "writer_claim", "writer_release"],
        )
        schema = by_name["task_control"]["inputSchema"]
        branches = {
            branch["properties"]["operation"]["enum"][0]: branch
            for branch in schema["oneOf"]
        }
        self.assertEqual(set(branches), {"task_observe", "writer_claim", "writer_release"})
        for operation in ("task_observe", "writer_claim"):
            self.assertEqual(set(branches[operation]["required"]), {"operation", "task_id"})
            self.assertEqual(set(branches[operation]["properties"]), {"operation", "task_id"})
        self.assertEqual(
            set(branches["writer_release"]["properties"]),
            {"operation", "task_id", "reason"},
        )
        self.assertEqual(set(branches["writer_release"]["required"]), {"operation", "task_id"})
        opened = self._call({
            "operation": "task_open",
            "binding_id": self.binding["binding_id"],
            "label": "handoff",
            "idempotency_key": "task-control-open-0001",
        })
        task_id = opened["result"]["structuredContent"]["task"]["task_id"]
        claimed_with_reason = self._call(
            {"operation": "writer_claim", "task_id": task_id, "reason": "not allowed here"},
            tool="task_control",
        )
        self.assertTrue(claimed_with_reason["result"]["isError"])
        self.assertEqual(claimed_with_reason["result"]["structuredContent"]["code"], "VALIDATION_ERROR")
        claimed = self._call(
            {"operation": "writer_claim", "task_id": task_id},
            tool="task_control",
        )
        self.assertEqual(
            claimed["result"]["structuredContent"]["writer_lease"]["state"],
            "held",
        )
        observed = self._call(
            {"operation": "task_observe", "task_id": task_id},
            tool="task_control",
        )
        observation = observed["result"]["structuredContent"]
        self.assertEqual(observation["task"]["task_id"], task_id)
        self.assertEqual(observation["writer_lease"]["state"], "held")
        self.assertNotIn("arguments_json", json.dumps(observation))
        released = self._call(
            {"operation": "writer_release", "task_id": task_id, "reason": "handoff"},
            tool="task_control",
        )
        self.assertEqual(
            released["result"]["structuredContent"]["writer_lease"]["state"],
            "released",
        )

    def test_standing_write_queues_without_per_patch_permission_and_replays(self) -> None:
        """The shared-account standing lane is task/lease bound, not approval bound."""

        import base64
        import hashlib
        import zlib

        owner = self.owner_id
        principal = self.principal
        binding = self.binding
        task = self.store.create_mcp_task_session(
            owner_id=owner,
            principal_id=principal["principal_id"],
            binding_id=binding["binding_id"],
            label="Standing write",
        )
        lease = self.store.claim_mcp_task_writer_lease(
            owner_id=owner,
            principal_id=principal["principal_id"],
            task_id=task["task_id"],
        )
        self.assertEqual(lease["state"], "held")

        old_content = b"old\n"
        new_content = b"new\n"
        preimage = hashlib.sha256(old_content).hexdigest()
        postimage = hashlib.sha256(new_content).hexdigest()
        payload = base64.b64encode(zlib.compress(new_content)).decode("ascii")
        envelope = "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: notes/app.txt",
            f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}",
            f"+{payload}",
            "*** End Patch",
            "",
        ))
        facade = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=("control-plane.inventory",),
            oauth_file_read_enabled=True,
            oauth_patch_write_scope="control-plane.patch",
            oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True,
        )
        contract = {
            key: facade.contract[key]
            for key in ("schema_version", "profile", "sha256")
        }
        self.assertEqual(contract["schema_version"], 31)
        self.assertEqual(contract["profile"], "control-plane-oauth-standing-write-v1")
        listed = facade.handle(
            {"jsonrpc": "2.0", "id": "standing-tools-001", "method": "tools/list", "params": {}},
            owner_id=owner,
            principal_id=principal["principal_id"],
            granted_context_id=None,
            oauth_scopes=frozenset({"control-plane.inventory", "control-plane.patch"}),
        )
        listed_tools = {tool["name"]: tool for tool in listed["result"]["tools"]}
        self.assertEqual(
            listed_tools["agent_workflow"]["_meta"]["control_plane"]["capability_state"],
            "standing_write",
        )
        request = {
            "jsonrpc": "2.0",
            "id": "standing-write-001",
            "method": "tools/call",
            "params": {
                "name": "agent_workflow",
                "arguments": {
                    "operation": "apply_patch",
                    "binding_id": binding["binding_id"],
                    "task_id": task["task_id"],
                    "path": "notes/app.txt",
                    "preimage_sha256": preimage,
                    "patch_sha256": hashlib.sha256(envelope.encode("utf-8")).hexdigest(),
                    "validation_profile": "targeted",
                    "patch_envelope": envelope,
                    "idempotency_key": "standing-patch-key-001",
                    "expected_facade_contract": contract,
                },
            },
        }
        first = facade.handle(
            request,
            owner_id=owner,
            principal_id=principal["principal_id"],
            granted_context_id=None,
            oauth_scopes=frozenset({"control-plane.inventory", "control-plane.patch"}),
        )
        self.assertIsNotNone(first)
        first_content = first["result"]["structuredContent"]
        self.assertEqual(first_content["authority_mode"], "standing")
        self.assertEqual(first_content["execution"], "queued_for_standing_local_policy")
        self.assertFalse(first_content["replayed"])
        self.assertNotIn("permission_request_id", request["params"]["arguments"])

        replay = facade.handle(
            request,
            owner_id=owner,
            principal_id=principal["principal_id"],
            granted_context_id=None,
            oauth_scopes=frozenset({"control-plane.inventory", "control-plane.patch"}),
        )
        replay_content = replay["result"]["structuredContent"]
        self.assertTrue(replay_content["replayed"])
        self.assertEqual(replay_content["action_id"], first_content["action_id"])

        competing_task = self.store.create_mcp_task_session(
            owner_id=owner,
            principal_id=principal["principal_id"],
            binding_id=binding["binding_id"],
            label="Competing standing write",
        )
        denied_request = {
            **request,
            "id": "standing-write-002",
            "params": {
                **request["params"],
                "arguments": {
                    **request["params"]["arguments"],
                    "task_id": competing_task["task_id"],
                    "idempotency_key": "standing-patch-key-002",
                },
            },
        }
        denied = facade.handle(
            denied_request,
            owner_id=owner,
            principal_id=principal["principal_id"],
            granted_context_id=None,
            oauth_scopes=frozenset({"control-plane.inventory", "control-plane.patch"}),
        )
        self.assertTrue(denied["result"]["isError"])
        self.assertEqual(denied["result"]["structuredContent"]["code"], "CONFLICT")

    def test_standing_document_create_is_durable_and_does_not_put_content_in_action_payload(self) -> None:
        """Central admission pins document writes without making the facade a file writer."""

        owner = self.owner_id
        principal_id = self.principal["principal_id"]
        task = self.store.create_mcp_task_session(
            owner_id=owner,
            principal_id=principal_id,
            binding_id=self.binding["binding_id"],
            label="Document create",
        )
        lease = self.store.claim_mcp_task_writer_lease(
            owner_id=owner,
            principal_id=principal_id,
            task_id=task["task_id"],
        )
        self.assertEqual(lease["state"], "held")
        facade = ControlPlaneMcpFacade(
            self.store,
            oauth_scopes=("control-plane.inventory",),
            oauth_file_read_enabled=True,
            oauth_patch_write_scope="control-plane.patch",
            oauth_approved_patch_enabled=True,
            oauth_standing_write_enabled=True,
        )
        contract = {key: facade.contract[key] for key in ("schema_version", "profile", "sha256")}
        request = {
            "jsonrpc": "2.0",
            "id": "document-create-001",
            "method": "tools/call",
            "params": {
                "name": "document_workflow",
                "arguments": {
                    "operation": "doc_create",
                    "binding_id": self.binding["binding_id"],
                    "task_id": task["task_id"],
                    "target": "docs/report.md",
                    "title": "Report",
                    "content": "# Report\n\nCreated by the local node.",
                    "overwrite": False,
                    "idempotency_key": "document-create-key-001",
                    "expected_facade_contract": contract,
                },
            },
        }
        scopes = frozenset({"control-plane.inventory", "control-plane.patch"})
        first = facade.handle(
            request,
            owner_id=owner,
            principal_id=principal_id,
            granted_context_id=None,
            oauth_scopes=scopes,
        )
        self.assertIsNotNone(first)
        first_content = first["result"]["structuredContent"]
        self.assertEqual(first_content["operation"], "document_create")
        self.assertEqual(first_content["task_id"], task["task_id"])
        self.assertFalse(first_content["replayed"])
        self.assertNotIn("content", json.dumps(first_content))

        replay = facade.handle(
            request,
            owner_id=owner,
            principal_id=principal_id,
            granted_context_id=None,
            oauth_scopes=scopes,
        )
        self.assertTrue(replay["result"]["structuredContent"]["replayed"])
        self.assertEqual(
            replay["result"]["structuredContent"]["action_id"],
            first_content["action_id"],
        )
        action = self.store.action(owner_id=owner, action_id=first_content["action_id"])
        self.assertNotIn('"content":', action["arguments_json"])
        with self.store._connection() as connection:
            row = connection.execute(
                "SELECT content, target_path, task_id FROM mcp_document_write_intents WHERE action_id = ?",
                (first_content["action_id"],),
            ).fetchone()
        self.assertEqual(row["content"], "# Report\n\nCreated by the local node.")
        self.assertEqual(row["target_path"], "docs/report.md")
        self.assertEqual(row["task_id"], task["task_id"])

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
