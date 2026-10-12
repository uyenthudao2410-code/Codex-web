"""Artifact reads remain bounded by current local authority and file identity."""

from __future__ import annotations

import io
import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane import node_agent


CONTRACT = {"schema_version": 8, "profile": "control-plane-oauth-bounded-file-read-v1", "sha256": "f" * 64}


class ArtifactNodeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="control-plane-artifact-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "workspace"
        self.root.mkdir()
        self.config_path = self.directory / "node.json"
        self.registry = self.directory / "workspaces.json"
        self.config = {
            "server_url": "https://control.example.test", "device_id": "artifact-device-0001",
            "endpoint_id": "artifact-endpoint-0001", "node_secret": "fixture-secret-not-printed",
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry.write_text(json.dumps({"schema_version": 1, "entries": [{
            "workspace_id": "artifact-workspace-0001", "workspace_generation": "artifact-generation-0001",
            "canonical_path": str(self.root.resolve()), "display_name": "Artifact fixture",
            "capabilities": {"read": True, "write": False, "exec": False}, "created_at_ms": 1,
        }]}), encoding="utf-8")
        self.args = SimpleNamespace(
            config=str(self.config_path), workspace_registry=str(self.registry),
            data_root=str(self.directory / "data"), project_root=str(self.directory),
            node="node", runtime_mode="development", timeout_seconds=20, replace=True,
        )
        self.sequence = 0
        self.policy = self.install_policy()

    def install_policy(self, *, max_bytes: int = 1024, max_lines: int = 20,
                       expires_at_ms: int | None = None) -> dict[str, object]:
        return node_agent._install_file_read_policy_values(
            self.args, config_path=self.config_path, config=self.config,
            owner_id="artifact-owner-0001", workspace_id="artifact-workspace-0001",
            workspace_generation="artifact-generation-0001", expires_at_ms=expires_at_ms,
            facade_contract=CONTRACT,
            allowed_relative_paths=None if expires_at_ms is None else ["fixture.txt", "image.bin"],
            allowed_relative_prefixes=["."] if expires_at_ms is None else None,
            max_bytes=max_bytes, max_lines=max_lines,
        )

    def action(self, *, kind: str = "document", path: str = "fixture.txt", **overrides: object) -> dict[str, object]:
        self.sequence += 1
        return {
            "action_id": f"action-artifact-{self.sequence:04d}", "attempt_id": f"attempt-artifact-{self.sequence:04d}",
            "owner_id": "artifact-owner-0001", "device_id": self.config["device_id"],
            "endpoint_id": self.config["endpoint_id"], "workspace_id": "artifact-workspace-0001",
            "workspace_generation": "artifact-generation-0001", "binding_id": "artifact-binding-0001",
            "tool_name": "document_workflow" if kind == "document" else "view_image",
            "arguments_json": json.dumps({"operation": f"{kind}_read", "path": path}),
            "mcp_artifact_kind": kind, "mcp_artifact_path": path,
            "mcp_artifact_facade_schema_version": CONTRACT["schema_version"],
            "mcp_artifact_facade_profile": CONTRACT["profile"],
            "mcp_artifact_facade_contract_sha256": CONTRACT["sha256"],
            "expires_at_ms": int(time.time() * 1000) + 30_000, **overrides,
        }

    def poll(self, action: dict[str, object]) -> dict[str, object]:
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/poll"):
                self.assertEqual(payload, {"limit": 1, "lane": "bounded_artifact"})
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-fixture-0001"}

        with mock.patch.object(node_agent, "_request", side_effect=request), \
             mock.patch.object(node_agent, "_runtime_status", return_value={}), \
             mock.patch.object(node_agent, "runtime_readiness", return_value=("ready", "fixture")), \
             mock.patch.object(node_agent, "recovery_identity_observation", return_value={}), \
             mock.patch.object(node_agent, "observed_runtime_identity", return_value={
                 "activation_epoch_id": "fixture-epoch", "process_instance_id": "fixture-process",
                 "server_instance_id": "fixture-server", "tool_contract_sha256": "a" * 64,
             }), redirect_stdout(io.StringIO()):
            self.assertEqual(node_agent.poll_artifact_once(self.args), 0)
        self.assertEqual(len(receipts), 1)
        return receipts[0]

    def assert_rejected(self, receipt: dict[str, object], code: str) -> None:
        self.assertEqual(receipt["receipt_state"], "rejected")
        self.assertEqual(receipt["payload"]["code"], code)
        self.assertNotIn("content", receipt["payload"])
        self.assertNotIn("data_base64", receipt["payload"])

    def test_expired_or_invalid_action_never_touches_target(self) -> None:
        for expiry, code in ((int(time.time() * 1000) - 1, "CONTROL_PLANE_ARTIFACT_REQUEST_EXPIRED"),
                             (True, "CONTROL_PLANE_ARTIFACT_ACTION_DENIED"),
                             (None, "CONTROL_PLANE_ARTIFACT_ACTION_DENIED")):
            with self.subTest(expiry=expiry), mock.patch.object(node_agent, "_read_artifact_bytes") as read:
                self.assert_rejected(self.poll(self.action(expires_at_ms=expiry)), code)
                read.assert_not_called()

    def test_expired_policy_never_touches_target(self) -> None:
        policy = self.install_policy(expires_at_ms=int(time.time() * 1000) + 60_000)
        policy["expires_at_ms"] = int(time.time() * 1000) - 1
        node_agent._write_json_atomic(node_agent._file_read_policy_path(self.args), policy)
        with mock.patch.object(node_agent, "_read_artifact_bytes") as read:
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_FILE_READ_POLICY_EXPIRED")
            read.assert_not_called()

    def test_policy_bytes_and_lines_reject_oversized_document(self) -> None:
        self.install_policy(max_bytes=8, max_lines=2)
        target = self.root / "fixture.txt"
        target.write_bytes(b"123456789")
        self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_TOO_LARGE")
        target.write_bytes(b"a\nb\nc")
        self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_FILE_READ_LIMIT_DENIED")
        target.write_bytes(b"abc\ndef\n")
        receipt = self.poll(self.action())
        self.assertEqual(receipt["receipt_state"], "completed")
        self.assertEqual(receipt["payload"]["content"], "abc\ndef\n")

    def test_oversized_file_is_rejected_without_reading_its_bytes(self) -> None:
        target = self.root / "fixture.txt"
        target.write_bytes(b"x" * 100_000)
        original_read = Path.read_bytes

        def read_bytes(path: Path) -> bytes:
            if path == target:
                raise AssertionError("unbounded artifact read")
            return original_read(path)

        with self.spy_reader() as readers, mock.patch.object(Path, "read_bytes", new=read_bytes):
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_TOO_LARGE")
        self.assertEqual(readers[0].requests, [])

    def test_handle_read_is_bounded_and_target_mutation_is_not_relayed(self) -> None:
        target = self.root / "fixture.txt"
        target.write_bytes(b"original")

        def mutate() -> None:
            target.write_bytes(b"modified")
            changed = target.stat()
            os.utime(target, ns=(changed.st_atime_ns, changed.st_mtime_ns + 1_000_000_000))

        with self.spy_reader(on_read=mutate) as readers:
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_TARGET_CHANGED")
        self.assertTrue(readers[0].requests)
        self.assertLessEqual(sum(readers[0].returned_bytes), 1025)
        self.assertTrue(all(0 < size <= 1025 for size in readers[0].requests))

    def test_file_growth_cannot_expand_the_bounded_read(self) -> None:
        target = self.root / "fixture.txt"
        target.write_bytes(b"original")
        with self.spy_reader(on_read=lambda: target.write_bytes(b"x" * 100_000)) as readers:
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_TOO_LARGE")
        self.assertEqual(sum(readers[0].returned_bytes), 1025)
        self.assertTrue(all(0 < size <= 1025 for size in readers[0].requests))

    def test_replacement_between_validation_and_open_never_reads_new_file(self) -> None:
        target = self.root / "fixture.txt"
        target.write_bytes(b"allowed")
        original_open = os.open

        def replace_then_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            if Path(path) == target:
                target.rename(self.root / "previous.txt")
                target.write_bytes(b"replacement")
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(node_agent.os, "open", side_effect=replace_then_open), self.spy_reader() as readers:
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_TARGET_CHANGED")
        self.assertEqual(readers[0].requests, [])

    def test_expiry_or_policy_change_during_read_withholds_content(self) -> None:
        action = self.action()

        def expire(_root: Path, _relative: str, _max_bytes: int) -> bytes:
            action["expires_at_ms"] = int(time.time() * 1000) - 1
            return b"do not relay"

        with mock.patch.object(node_agent, "_read_artifact_bytes", side_effect=expire):
            self.assert_rejected(self.poll(action), "CONTROL_PLANE_ARTIFACT_REQUEST_EXPIRED")

        def change_policy(_root: Path, _relative: str, _max_bytes: int) -> bytes:
            self.install_policy(max_bytes=512)
            return b"do not relay"

        with mock.patch.object(node_agent, "_read_artifact_bytes", side_effect=change_policy):
            self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_FILE_READ_TARGET_MISMATCH")

    def test_image_magic_and_policy_size_are_enforced(self) -> None:
        target = self.root / "image.bin"
        for raw, mime in ((b"\x89PNG\r\n\x1a\nfixture", "image/png"),
                          (b"\xff\xd8\xfffixture", "image/jpeg"),
                          (b"RIFF\x04\x00\x00\x00WEBPfixture", "image/webp")):
            with self.subTest(mime=mime):
                target.write_bytes(raw)
                receipt = self.poll(self.action(kind="image", path="image.bin"))
                self.assertEqual(receipt["receipt_state"], "completed")
                self.assertEqual(receipt["payload"]["mime"], mime)
        for raw in (b"not an image", b"RIFFWEBPxxxx", b"RIFFxxxxnoWEBP"):
            with self.subTest(raw=raw):
                target.write_bytes(raw)
                self.assert_rejected(self.poll(self.action(kind="image", path="image.bin")),
                                     "CONTROL_PLANE_ARTIFACT_MIME_DENIED")
        self.install_policy(max_bytes=8)
        target.write_bytes(b"\x89PNG\r\n\x1a\nmore")
        self.assert_rejected(self.poll(self.action(kind="image", path="image.bin")), "CONTROL_PLANE_ARTIFACT_TOO_LARGE")

    def test_artifact_absolute_cap_remains_even_with_larger_policy(self) -> None:
        policy = {**self.policy, "max_bytes": 2 * 1024 * 1024}
        entry = json.loads(self.registry.read_text(encoding="utf-8"))["entries"][0]
        for kind, cap in (("document", 256 * 1024), ("image", 1024 * 1024)):
            with self.subTest(kind=kind), \
                 mock.patch.object(node_agent, "_file_read_policy_admission", return_value=(policy, entry)), \
                 mock.patch.object(node_agent, "_read_artifact_bytes", side_effect=RuntimeError("CONTROL_PLANE_ARTIFACT_TOO_LARGE")) as read:
                self.assert_rejected(self.poll(self.action(kind=kind)), "CONTROL_PLANE_ARTIFACT_TOO_LARGE")
                self.assertEqual(read.call_args.args[2], cap)

    def test_symlink_and_path_escape_are_rejected(self) -> None:
        outside = self.directory / "outside.txt"
        outside.write_bytes(b"outside secret fixture")
        self.assert_rejected(self.poll(self.action(path="../outside.txt")), "CONTROL_PLANE_ARTIFACT_ACTION_DENIED")
        try:
            (self.root / "fixture.txt").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable on fixture host: {type(error).__name__}")
        self.assert_rejected(self.poll(self.action()), "CONTROL_PLANE_ARTIFACT_REPARSE_DENIED")

    def test_windows_reparse_attribute_prevents_opening_the_target(self) -> None:
        target = self.root / "fixture.txt"
        target.write_bytes(b"fixture")
        original_lstat = Path.lstat

        def lstat(path: Path):
            metadata = original_lstat(path)
            if path == target:
                return SimpleNamespace(st_mode=metadata.st_mode, st_file_attributes=0x400)
            return metadata

        with mock.patch.object(Path, "lstat", new=lstat), \
             mock.patch.object(node_agent.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, create=True), \
             mock.patch.object(node_agent.os, "open") as opened:
            with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_ARTIFACT_REPARSE_DENIED$"):
                node_agent._read_artifact_bytes(self.root, "fixture.txt", 1024)
            opened.assert_not_called()

    @staticmethod
    def spy_reader(*, on_read: object = None):
        original_fdopen = os.fdopen
        readers = []

        class Reader:
            def __init__(self, handle):
                self.handle = handle
                self.requests = []
                self.returned_bytes = []
                self.changed = False

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def fileno(self):
                return self.handle.fileno()

            def read(self, size):
                self.requests.append(size)
                raw = self.handle.read(size)
                self.returned_bytes.append(len(raw))
                if on_read is not None and not self.changed:
                    self.changed = True
                    on_read()
                return raw

        def wrap(descriptor, mode="r", *args, **kwargs):
            handle = original_fdopen(descriptor, mode, *args, **kwargs)
            if mode != "rb":
                return handle
            reader = Reader(handle)
            readers.append(reader)
            return reader

        class Spy:
            def __enter__(self):
                self.patch = mock.patch.object(node_agent.os, "fdopen", side_effect=wrap)
                self.patch.start()
                return readers

            def __exit__(self, *args):
                self.patch.stop()

        return Spy()


if __name__ == "__main__":
    unittest.main()
