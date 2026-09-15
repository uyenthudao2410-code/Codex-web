from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from control_plane.http_api import ControlPlaneHttpServer
from control_plane.store import ControlPlaneStore


class ControlPlaneHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.operator_token = "o" * 40
        self.server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3"),
            self.operator_token,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tempdir.cleanup()

    def _post(self, path: str, payload: dict, authorization: str | None = None) -> tuple[int, dict]:
        headers = {"Content-Type": "application/json"}
        if authorization:
            headers["Authorization"] = authorization
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=2) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def test_two_step_enrollment_never_exposes_node_secret_to_operator(self) -> None:
        node_secret = "n" * 40
        credential_hash = hashlib.sha256(
            json.dumps({"node_secret": node_secret}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        status, enrollment = self._post(
            "/v1/enrollment-requests",
            {
                "device_id": "device-http-canary",
                "endpoint_id": "endpoint-http-canary",
                "display_name": "HTTP Canary",
                "credential_hash": credential_hash,
            },
        )
        self.assertEqual(status, 201)
        self.assertNotIn("node_secret", enrollment)

        status, forbidden = self._post(
            f"/v1/enrollment-requests/{enrollment['enrollment_id']}/approve",
            {},
        )
        self.assertEqual(status, 403)
        self.assertEqual(forbidden["error"]["code"], "FORBIDDEN")

        status, approved = self._post(
            f"/v1/enrollment-requests/{enrollment['enrollment_id']}/approve",
            {},
            f"Bearer {self.operator_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["device_id"], "device-http-canary")
        self.assertNotIn("node_secret", approved)

        status, heartbeat = self._post(
            "/v1/nodes/device-http-canary/heartbeat",
            {"endpoint_id": "endpoint-http-canary", "readiness": "unknown"},
            f"Node {node_secret}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(heartbeat["readiness"], "unknown")
