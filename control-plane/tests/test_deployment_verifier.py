from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from control_plane.deployment_verifier import main as verifier_main
from control_plane.http_api import ControlPlaneHttpServer, _package_source_sha256
from control_plane.store import ControlPlaneStore, SCHEMA_VERSION


class _IncompleteHealthHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        payload = {
            "service": "coding-tools-control-plane",
            "ok": True,
            "sqlite_integrity": "ok",
            "schema_version": None,
            "diagnostic": "private remote detail must not reach a receipt",
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _RedirectHealthHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(302)
        self.send_header("Location", "https://untrusted.example.invalid/healthz")
        self.send_header("Content-Length", "0")
        self.end_headers()


class DeploymentHealthVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.fingerprint = _package_source_sha256()
        self.server = ControlPlaneHttpServer(
            ("127.0.0.1", 0),
            ControlPlaneStore(Path(self.tempdir.name) / "control.sqlite3"),
            "o" * 40,
            expected_package_source_sha256=self.fingerprint,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tempdir.cleanup()

    def _run(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = verifier_main(list(arguments))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_exact_selected_package_health_receipt_passes(self) -> None:
        exit_code, stdout, stderr = self._run(
            "--health-url",
            f"{self.base_url}/healthz",
            "--expected-package-source-sha256",
            self.fingerprint,
            "--expected-admission",
            "open",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        receipt = json.loads(stdout)
        self.assertEqual(receipt["operation"], "control_plane_deployment_health_verification")
        self.assertEqual(receipt["service_instance_id"], self.server.service_instance_id)
        self.assertEqual(receipt["schema_version"], SCHEMA_VERSION)
        self.assertEqual(receipt["admission_mode"], "open")
        self.assertEqual(receipt["package_source_sha256"], self.fingerprint)
        self.assertNotIn(self.base_url, stdout)

    def test_incomplete_remote_health_fails_without_echoing_endpoint_or_body(self) -> None:
        incomplete_server = ThreadingHTTPServer(("127.0.0.1", 0), _IncompleteHealthHandler)
        incomplete_thread = threading.Thread(target=incomplete_server.serve_forever, daemon=True)
        incomplete_thread.start()
        incomplete_url = f"http://127.0.0.1:{incomplete_server.server_port}/healthz"
        try:
            exit_code, stdout, stderr = self._run(
                "--health-url",
                incomplete_url,
                "--expected-package-source-sha256",
                self.fingerprint,
                "--expected-admission",
                "open",
            )
        finally:
            incomplete_server.shutdown()
            incomplete_server.server_close()
            incomplete_thread.join(timeout=2)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE")
        self.assertNotIn(incomplete_url, stderr)
        self.assertNotIn("private remote detail", stderr)

    def test_credential_or_non_health_url_is_rejected_before_network(self) -> None:
        exit_code, stdout, stderr = self._run(
            "--health-url",
            "https://operator:secret@example.invalid/not-healthz",
            "--expected-package-source-sha256",
            self.fingerprint,
            "--expected-admission",
            "open",
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "CONTROL_PLANE_DEPLOYMENT_HEALTH_URL_INVALID")
        self.assertNotIn("secret", stderr)

    def test_redirect_is_unavailable_without_following_or_echoing_location(self) -> None:
        redirect_server = ThreadingHTTPServer(("127.0.0.1", 0), _RedirectHealthHandler)
        redirect_thread = threading.Thread(target=redirect_server.serve_forever, daemon=True)
        redirect_thread.start()
        redirect_url = f"http://127.0.0.1:{redirect_server.server_port}/healthz"
        try:
            exit_code, stdout, stderr = self._run(
                "--health-url",
                redirect_url,
                "--expected-package-source-sha256",
                self.fingerprint,
                "--expected-admission",
                "open",
            )
        finally:
            redirect_server.shutdown()
            redirect_server.server_close()
            redirect_thread.join(timeout=2)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "CONTROL_PLANE_DEPLOYMENT_HEALTH_UNAVAILABLE")
        self.assertNotIn(redirect_url, stderr)
        self.assertNotIn("untrusted.example.invalid", stderr)
