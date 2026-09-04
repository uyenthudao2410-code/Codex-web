from __future__ import annotations

import base64
import hashlib
import tempfile
import unittest
import zlib
from pathlib import Path

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.patching import MAX_EXACT_FILE_BYTES, parse_patch
from coding_tools_mcp.server import Runtime


def exact_write_section(path: str, before: bytes | None, after: bytes) -> str:
    preimage = "absent" if before is None else hashlib.sha256(before).hexdigest()
    postimage = hashlib.sha256(after).hexdigest()
    payload = base64.b64encode(zlib.compress(after, level=9)).decode("ascii")
    return (
        f"*** Write Exact File: {path}\n"
        f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}\n"
        f"+{payload}\n"
    )


def exact_write_patch(*sections: str) -> str:
    return "*** Begin Patch\n" + "".join(sections) + "*** End Patch\n"


class ExactPatchParserTests(unittest.TestCase):
    def test_parser_preserves_mixed_line_endings_exactly(self) -> None:
        content = b"alpha\r\nbeta\ngamma\r\n"
        operation = parse_patch(exact_write_patch(exact_write_section("mixed.txt", None, content)))[0]
        self.assertEqual(operation.kind, "write_exact")
        self.assertEqual(operation.preimage_sha256, "absent")
        self.assertEqual(operation.add_content.encode("utf-8"), content)
        self.assertEqual(operation.postimage_sha256, hashlib.sha256(content).hexdigest())

    def test_parser_rejects_postimage_mismatch_and_non_utf8(self) -> None:
        bad_digest = "0" * 64
        mismatch = (
            "*** Begin Patch\n"
            "*** Write Exact File: bad.txt\n"
            f"@@ encoding=zlib-base64 preimage_sha256=absent postimage_sha256={bad_digest}\n"
            f"+{base64.b64encode(zlib.compress(b'content')).decode('ascii')}\n"
            "*** End Patch\n"
        )
        with self.assertRaises(ToolFailure) as caught:
            parse_patch(mismatch)
        self.assertEqual(caught.exception.code, "PATCH_EXACT_POSTIMAGE_MISMATCH")

        binary = b"\xff\xfe"
        with self.assertRaises(ToolFailure) as caught:
            parse_patch(exact_write_patch(exact_write_section("binary.bin", None, binary)))
        self.assertEqual(caught.exception.code, "UNSUPPORTED_ENCODING")

    def test_parser_rejects_decompression_beyond_exact_file_limit(self) -> None:
        oversized = b"x" * (MAX_EXACT_FILE_BYTES + 1)
        with self.assertRaises(ToolFailure) as caught:
            parse_patch(exact_write_patch(exact_write_section("oversized.txt", None, oversized)))
        self.assertEqual(caught.exception.code, "PATCH_EXACT_PAYLOAD_TOO_LARGE")


class ExactPatchRuntimeTests(unittest.TestCase):
    def test_exact_update_and_add_commit_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = b"alpha\r\nbeta\n"
            after = b"alpha\r\nBETA\nomega\r\n"
            added = b"new\r\nfile\r\n"
            (root / "mixed.txt").write_bytes(before)
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.apply_patch(
                    {
                        "patch": exact_write_patch(
                            exact_write_section("mixed.txt", before, after),
                            exact_write_section("added.txt", None, added),
                        )
                    }
                )
                self.assertTrue(result["clean"])
                self.assertEqual(
                    result["affected_files"],
                    [
                        {"path": "mixed.txt", "operation": "update"},
                        {"path": "added.txt", "operation": "add"},
                    ],
                )
                self.assertEqual((root / "mixed.txt").read_bytes(), after)
                self.assertEqual((root / "added.txt").read_bytes(), added)
            finally:
                runtime.close()

    def test_preimage_mismatch_stages_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first_before = b"first-before\r\n"
            second_before = b"second-before\n"
            (root / "first.txt").write_bytes(first_before)
            (root / "second.txt").write_bytes(second_before)
            first_section = exact_write_section("first.txt", first_before, b"first-after\n")
            wrong_second_section = exact_write_section("second.txt", b"wrong", b"second-after\n")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                with self.assertRaises(ToolFailure) as caught:
                    runtime.apply_patch({"patch": exact_write_patch(first_section, wrong_second_section)})
                self.assertEqual(caught.exception.code, "PATCH_EXACT_PREIMAGE_MISMATCH")
                self.assertEqual((root / "first.txt").read_bytes(), first_before)
                self.assertEqual((root / "second.txt").read_bytes(), second_before)
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
