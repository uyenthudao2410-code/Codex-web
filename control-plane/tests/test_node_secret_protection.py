from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane import node_agent


class NodeSecretProtectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="node-secret-protection-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "control-plane-node.json"
        self.secret = "node-secret-protection-test-0001"

    def test_windows_write_persists_only_dpapi_envelope(self) -> None:
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_protect_node_secret", return_value="dpapi-v1:protected-value"
        ) as protect:
            node_agent._write_config(self.path, {"schema_version": 1, "node_secret": self.secret, "device_id": "device-test"})

        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("node_secret", persisted)
        self.assertEqual(persisted["node_secret_dpapi"], "dpapi-v1:protected-value")
        protect.assert_called_once_with(self.secret)
        self.assertNotIn(self.secret, self.path.read_text(encoding="utf-8"))

    def test_protected_config_is_unwrapped_only_in_memory_and_reprotected_on_write(self) -> None:
        self.path.write_text(
            json.dumps({"schema_version": 1, "node_secret_dpapi": "dpapi-v1:protected-value", "device_id": "device-test"}),
            encoding="utf-8",
        )
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_unprotect_node_secret", return_value=self.secret
        ) as unprotect, mock.patch.object(
            node_agent, "_protect_node_secret", return_value="dpapi-v1:reprotected-value"
        ) as protect:
            config = node_agent._config(self.path)
            self.assertEqual(config["node_secret"], self.secret)
            self.assertTrue(config["_node_secret_protected"])
            config["enrollment_state"] = "approved"
            node_agent._write_config(self.path, config)

        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("node_secret", persisted)
        self.assertNotIn("_node_secret_protected", persisted)
        self.assertEqual(persisted["node_secret_dpapi"], "dpapi-v1:reprotected-value")
        unprotect.assert_called_once_with("dpapi-v1:protected-value")
        protect.assert_called_once_with(self.secret)

    def test_plaintext_and_protected_credentials_are_ambiguous(self) -> None:
        self.path.write_text(
            json.dumps({
                "schema_version": 1,
                "node_secret": self.secret,
                "node_secret_dpapi": "dpapi-v1:protected-value",
            }),
            encoding="utf-8",
        )
        with mock.patch.object(node_agent.os, "name", "nt"):
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_NODE_SECRET_AMBIGUOUS"):
                node_agent._config(self.path)

    def test_windows_refuses_plaintext_fallback_when_protection_unavailable(self) -> None:
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent,
            "_protect_node_secret",
            side_effect=RuntimeError("CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE"),
        ):
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_NODE_SECRET_PROTECTION_UNAVAILABLE"):
                node_agent._write_config(self.path, {"schema_version": 1, "node_secret": self.secret})
        self.assertFalse(self.path.exists())

    def test_windows_legacy_plaintext_config_is_migrated_on_first_read(self) -> None:
        self.path.write_text(
            json.dumps({"schema_version": 1, "node_secret": self.secret, "device_id": "device-test"}),
            encoding="utf-8",
        )
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_protect_node_secret", return_value="dpapi-v1:migrated-value"
        ) as protect:
            config = node_agent._config(self.path)

        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(config["node_secret"], self.secret)
        self.assertTrue(config["_node_secret_protected"])
        self.assertNotIn("node_secret", persisted)
        self.assertEqual(persisted["node_secret_dpapi"], "dpapi-v1:migrated-value")
        self.assertNotIn(self.secret, self.path.read_text(encoding="utf-8"))
        protect.assert_called_once_with(self.secret)

    def test_windows_pending_rotation_secret_is_protected_and_unwrapped_in_memory(self) -> None:
        pending = "pending-node-secret-protection-0001"
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_protect_node_secret", side_effect=["dpapi-v1:active", "dpapi-v1:pending"]
        ) as protect:
            node_agent._write_config(
                self.path,
                {
                    "schema_version": 1,
                    "node_secret": self.secret,
                    "node_secret_pending": pending,
                    "device_id": "device-test",
                },
            )
        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("node_secret", persisted)
        self.assertNotIn("node_secret_pending", persisted)
        self.assertEqual(persisted["node_secret_dpapi"], "dpapi-v1:active")
        self.assertEqual(persisted["node_secret_pending_dpapi"], "dpapi-v1:pending")
        protect.assert_has_calls([mock.call(self.secret), mock.call(pending)])

        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_unprotect_node_secret", side_effect=[self.secret, pending]
        ) as unprotect:
            config = node_agent._config(self.path)
        self.assertEqual(config["node_secret"], self.secret)
        self.assertEqual(config["node_secret_pending"], pending)
        self.assertTrue(config["_node_secret_protected"])
        self.assertTrue(config["_node_secret_pending_protected"])
        self.assertEqual(unprotect.call_count, 2)

    def test_windows_completed_rotation_removes_pending_protected_copy(self) -> None:
        self.path.write_text(
            json.dumps({
                "schema_version": 1,
                "node_secret_dpapi": "dpapi-v1:active",
                "node_secret_pending_dpapi": "dpapi-v1:pending",
            }),
            encoding="utf-8",
        )
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent, "_unprotect_node_secret", side_effect=[self.secret, "pending-node-secret-0001"]
        ), mock.patch.object(
            node_agent, "_protect_node_secret", return_value="dpapi-v1:active-rewritten"
        ):
            config = node_agent._config(self.path)
            config.pop("node_secret_pending", None)
            node_agent._write_config(self.path, config)
        persisted = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("node_secret_pending_dpapi", persisted)
        self.assertEqual(persisted["node_secret_dpapi"], "dpapi-v1:active-rewritten")

    def test_non_windows_legacy_config_remains_readable_for_source_fixtures(self) -> None:
        self.path.write_text(
            json.dumps({"schema_version": 1, "node_secret": self.secret}),
            encoding="utf-8",
        )
        with mock.patch.object(node_agent.os, "name", "posix"):
            config = node_agent._config(self.path)
        self.assertEqual(config["node_secret"], self.secret)

    def test_windows_acl_hardening_uses_sid_allowlist_without_shell(self) -> None:
        identity = SimpleNamespace(returncode=0, stdout='"Admin","S-1-5-21-111-222-333-1001"\r\n')
        applied = SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent.sys, "platform", "win32"
        ), mock.patch.object(node_agent.subprocess, "run", side_effect=[identity, applied]) as run:
            node_agent._harden_windows_private_file(self.path)

        self.assertEqual(run.call_count, 2)
        identity_call = run.call_args_list[0]
        acl_call = run.call_args_list[1]
        self.assertEqual(identity_call.args[0], ["whoami.exe", "/user", "/fo", "csv", "/nh"])
        self.assertNotIn("shell", identity_call.kwargs)
        self.assertEqual(
            acl_call.args[0],
            [
                "icacls.exe",
                str(self.path),
                "/inheritance:r",
                "/grant:r",
                "*S-1-5-21-111-222-333-1001:F",
                "*S-1-5-18:F",
                "*S-1-5-32-544:F",
            ],
        )

    def test_windows_acl_hardening_fails_closed_on_command_failure(self) -> None:
        failed = SimpleNamespace(returncode=1, stdout="", stderr="denied")
        with mock.patch.object(node_agent.os, "name", "nt"), mock.patch.object(
            node_agent.sys, "platform", "win32"
        ), mock.patch.object(node_agent.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_NODE_CONFIG_ACL_UNAVAILABLE"):
                node_agent._harden_windows_private_file(self.path)


if __name__ == "__main__":
    unittest.main()
