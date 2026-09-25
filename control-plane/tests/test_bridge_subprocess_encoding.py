"""Exercise real child pipes without Recovery credentials or a live node."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane import node_agent


BRIDGES = (
    (node_agent.recovery_read_only_bridge, "CONTROL_PLANE_BRIDGE"),
    (node_agent.recovery_file_read_bridge, "CONTROL_PLANE_FILE_READ"),
    (node_agent.recovery_approved_patch_bridge, "CONTROL_PLANE_APPROVED_PATCH"),
    (node_agent.recovery_exec_bridge, "CONTROL_PLANE_EXEC"),
    (node_agent.recovery_document_write_bridge, "CONTROL_PLANE_DOCUMENT_WRITE"),
)


class BridgeSubprocessEncodingTests(unittest.TestCase):
    def invoke(self, bridge, script: str, request=None):
        command = [sys.executable, "-c", script]
        args = SimpleNamespace(timeout_seconds=5)
        # Windows ACP must not be the JSON wire encoding. Force it on other
        # hosts too so this regression cannot hide behind UTF-8 Linux defaults.
        with mock.patch.object(node_agent, "_adapter_command", return_value=(command, dict(os.environ))), \
             mock.patch("subprocess._text_encoding", return_value="cp1252"):
            return bridge(args, Path(__file__).resolve().parent, request or {})

    def test_unicode_request_and_result_survive_non_utf8_system_locale(self):
        script = (
            "import json,sys; "
            "value=json.loads(sys.stdin.buffer.read()); "
            "sys.stdout.buffer.write(json.dumps({'ok':True,'result':value}, "
            "ensure_ascii=False).encode('utf-8'))"
        )
        request = {"path": "hồ-sơ.md", "content": "Tiếng Việt: chờ xử lý ✓"}
        for bridge, _prefix in BRIDGES:
            with self.subTest(bridge=bridge.__name__):
                self.assertEqual(self.invoke(bridge, script, request), (request, None))

    def test_non_utf8_stderr_does_not_mask_structured_rejection(self):
        script = (
            "import sys; sys.stderr.buffer.write(bytes([0x81,0xff])); "
            "sys.stdout.buffer.write(b'{\"ok\":false,\"error\":{\"code\":\"REQUEST_REJECTED\"}}'); "
            "sys.exit(1)"
        )
        for bridge, _prefix in BRIDGES:
            with self.subTest(bridge=bridge.__name__):
                self.assertEqual(self.invoke(bridge, script), (None, "REQUEST_REJECTED"))

    def test_malformed_stdout_is_typed_invalid_never_repaired_or_completed(self):
        script = "import sys; sys.stdout.buffer.write(bytes([0xff,0xfe,0xfd]))"
        for bridge, prefix in BRIDGES:
            with self.subTest(bridge=bridge.__name__):
                self.assertEqual(self.invoke(bridge, script), (None, prefix + "_RESULT_INVALID"))


if __name__ == "__main__":
    unittest.main()
