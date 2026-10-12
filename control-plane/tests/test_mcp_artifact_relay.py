"""Scoped image relay validates actual bytes, MIME and receipt digests."""
from __future__ import annotations

import base64
import hashlib
import json
import unittest

from control_plane.mcp_facade import _completed_artifact_relay


class McpArtifactRelayTests(unittest.TestCase):
    contract = {"schema_version": 32, "profile": "control-plane-private-tunnel-service-v1", "sha256": "a" * 64}

    def action(self, raw: bytes, mime: str = "image/webp", *, wrong_digest: bool = False, path: str = "assets/fixture.webp") -> dict:
        data = base64.b64encode(raw).decode("ascii")
        response = {"path": path, "mime": mime, "data_base64": data}
        digest = hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        payload = {
            "schema_version": 1, "operation_kind": "control_plane_artifact_image",
            "facade_contract": self.contract,
            "actor": {"client_id": "electron-control-plane-artifact-bridge", "client_type": "electron"},
            "local_handle": "cp_artifact_" + "b" * 48,
            "response_sha256": "c" * 64 if wrong_digest else digest, **response,
        }
        return {"tool_name": "view_image", "receipts": [{"receipt_state": "completed",
                "receipt_id": "receipt-001", "received_at_ms": 1, "payload_json": json.dumps(payload)}]}

    def test_matching_png_jpeg_and_webp_signatures_are_relayed(self) -> None:
        for mime, raw in (("image/png", b"\x89PNG\r\n\x1a\nfixture"),
                          ("image/jpeg", b"\xff\xd8\xfffixture"),
                          ("image/webp", b"RIFF\x08\x00\x00\x00WEBPfixture")):
            with self.subTest(mime=mime):
                relay = _completed_artifact_relay(self.action(raw, mime), self.contract, kind="image")
                self.assertIsNotNone(relay)
                self.assertEqual(relay["mime"], mime)
                self.assertEqual(relay["bytes"], len(raw))

    def test_forged_webp_mime_is_rejected_even_when_digest_is_correct(self) -> None:
        for raw in (b"not an image", b"RIFF", b"RIFF1234WAVEdata", b"\x89PNG\r\n\x1a\nfixture"):
            with self.subTest(signature=raw[:4]):
                self.assertIsNone(_completed_artifact_relay(self.action(raw), self.contract, kind="image"))

    def test_wrong_digest_over_limit_or_parent_path_are_not_relayed(self) -> None:
        raw = b"RIFF1234WEBPfixture"
        for action in (self.action(raw, wrong_digest=True), self.action(raw, path="../private.webp"),
                       self.action(raw + b"x" * (1024 * 1024))):
            self.assertIsNone(_completed_artifact_relay(action, self.contract, kind="image"))


if __name__ == "__main__":
    unittest.main()
