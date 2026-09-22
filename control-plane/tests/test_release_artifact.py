from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import urllib.request
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts" / "build-control-plane-release.py"
SPEC = importlib.util.spec_from_file_location("control_plane_release_builder", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_health(url: str, expected_fingerprint: str, timeout_seconds: float = 10) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("package_source_sha256") == expected_fingerprint:
                return payload
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
        time.sleep(0.05)
    raise AssertionError(f"release launcher did not publish expected health: {last_error}")


def post_json(url: str, payload: dict, *, authorization: str = "") -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode("utf-8"))
        finally:
            error.close()


class ControlPlaneReleaseArtifactTests(unittest.TestCase):
    def test_builds_secret_free_versioned_release_and_archive(self) -> None:
        revision = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            receipt = BUILDER.build_release(
                ROOT,
                output,
                revision,
                require_clean_source=False,
            )

            release = Path(receipt["release_directory"])
            archive = Path(receipt["archive"])
            self.assertEqual(release.parent, output)
            self.assertTrue(release.is_dir())
            self.assertTrue(archive.is_file())
            self.assertEqual(receipt["archive_sha256"], sha256_file(archive))
            self.assertEqual(receipt["source_revision"], revision)

            manifest = json.loads((release / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["source_revision"], revision)
            self.assertEqual(manifest["package_source_sha256"], receipt["package_source_sha256"])
            self.assertGreater(manifest["control_plane_schema_version"], 0)
            self.assertEqual(set(manifest["component_sha256"]), {"control_plane", "deployment", "documentation"})

            files = {entry["path"]: entry for entry in manifest["files"]}
            self.assertTrue(BUILDER.REQUIRED_RELEASE_FILES.issubset(files))
            self.assertFalse(any(path.startswith(".coding-tools/") for path in files))
            self.assertFalse(any("/__pycache__/" in f"/{path}" for path in files))
            self.assertFalse(any(path.endswith((".pyc", ".pyo")) for path in files))
            self.assertFalse(any(path.endswith(".sqlite3") for path in files))
            self.assertFalse(any(path.endswith("control-plane.env") for path in files))
            for relative, entry in files.items():
                target = release / relative
                self.assertTrue(target.is_file())
                self.assertEqual(entry["size_bytes"], target.stat().st_size)
                self.assertEqual(entry["sha256"], sha256_file(target))

            for launcher in (
                "deploy/control-plane-launcher.sh",
                "deploy/control-plane-mcp-tunnel-launcher.sh",
                "deploy/control-plane-backup.sh",
                "deploy/control-plane-healthcheck.sh",
            ):
                if os.name != "nt":
                    self.assertNotEqual((release / launcher).stat().st_mode & 0o111, 0)
                self.assertNotIn(b"\r\n", (release / launcher).read_bytes())

            service_templates = {
                "codex-control-plane.service.example": "control-plane-launcher.sh",
                "codex-control-plane-mcp-tunnel.service.example": "control-plane-mcp-tunnel-launcher.sh",
                "codex-control-plane-backup.service.example": "control-plane-backup.sh",
                "codex-control-plane-healthcheck.service.example": "control-plane-healthcheck.sh",
            }
            for template, launcher in service_templates.items():
                content = (release / "deploy" / template).read_text(encoding="utf-8")
                self.assertIn(f"current/deploy/{launcher}", content)
                self.assertNotIn("/DEV/Codex-web", content)

            verifier = release / "deploy" / "control-plane-verify-release.py"
            verification = subprocess.run(
                [sys.executable, str(verifier), "--release-dir", str(release)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            self.assertEqual(verification.returncode, 0)
            verified_receipt = json.loads(verification.stdout)
            self.assertEqual(verified_receipt["file_count"], len(files))
            self.assertEqual(verified_receipt["source_revision"], revision)

            with (release / "control-plane" / "control_plane" / "web_ui.py").open("ab") as tampered:
                tampered.write(b"\n")
            tampered_result = subprocess.run(
                [sys.executable, str(verifier), "--release-dir", str(release)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            self.assertEqual(tampered_result.returncode, 2)

            prefix = f"{receipt['release_name']}/"
            with tarfile.open(archive, "r:gz") as bundle:
                members = {member.name: member for member in bundle.getmembers()}
            names = set(members)
            self.assertIn(f"{prefix}release-manifest.json", names)
            self.assertIn(f"{prefix}control-plane/control_plane/http_api.py", names)
            for launcher in (
                "deploy/control-plane-launcher.sh",
                "deploy/control-plane-mcp-tunnel-launcher.sh",
                "deploy/control-plane-backup.sh",
                "deploy/control-plane-healthcheck.sh",
            ):
                member = members[f"{prefix}{launcher}"]
                self.assertEqual(member.mode & 0o111, 0o111)
            self.assertFalse(any(
                ".coding-tools" in name
                or "/__pycache__/" in name
                or name.endswith((".pyc", ".pyo", ".sqlite3"))
                for name in names
            ))

    def test_refuses_to_overwrite_a_previously_built_release(self) -> None:
        revision = "b" * 40
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            BUILDER.build_release(ROOT, output, revision, require_clean_source=False)
            with self.assertRaises(BUILDER.ReleaseBuildError):
                BUILDER.build_release(ROOT, output, revision, require_clean_source=False)

    @unittest.skipIf(os.name == "nt", "direct POSIX launcher execution requires a Unix shell")
    def test_archive_launcher_runs_from_extracted_release_with_external_state(self) -> None:
        revision = "c" * 40
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            output = temporary_root / "outputs"
            output.mkdir()
            receipt = BUILDER.build_release(ROOT, output, revision, require_clean_source=False)
            extracted = temporary_root / "extracted"
            with tarfile.open(receipt["archive"], "r:gz") as bundle:
                bundle.extractall(extracted)
            release_root = extracted / receipt["release_name"]
            database = temporary_root / "state" / "control-plane.sqlite3"
            database.parent.mkdir()
            backup_directory = temporary_root / "state" / "backups"
            port = free_port()
            mcp_port = free_port()
            environment = {
                **os.environ,
                "CONTROL_PLANE_DB": str(database),
                "CONTROL_PLANE_BACKUP_DIR": str(backup_directory),
                "CONTROL_PLANE_BIND": "127.0.0.1",
                "CONTROL_PLANE_PORT": str(port),
                "CONTROL_PLANE_MCP_BIND": "127.0.0.1",
                "CONTROL_PLANE_MCP_PORT": str(mcp_port),
                "CONTROL_PLANE_OPERATOR_TOKEN": "x" * 32,
                "CONTROL_PLANE_DECLARED_SOURCE_REVISION": revision,
                "CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256": receipt["package_source_sha256"],
                "CONTROL_PLANE_HEALTH_URL": f"http://127.0.0.1:{port}/healthz",
                "CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION": "open",
            }
            process = subprocess.Popen(
                [str(release_root / "deploy" / "control-plane-launcher.sh")],
                cwd=release_root,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                verification = subprocess.run(
                    [sys.executable, str(release_root / "deploy" / "control-plane-verify-release.py"), "--release-dir", str(release_root)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(verification.returncode, 0)
                health = wait_health(f"http://127.0.0.1:{port}/healthz", receipt["package_source_sha256"])
                self.assertEqual(health["schema_version"], receipt["control_plane_schema_version"])
                self.assertEqual(health["declared_source_revision"], revision)
                self.assertTrue(database.is_file())
                self.assertFalse(str(database).startswith(str(release_root)))

                primary_url = f"http://127.0.0.1:{port}"
                mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
                operator = "x" * 32
                status, node = post_json(
                    f"{primary_url}/v1/nodes/enroll",
                    {
                        "device_id": "device-release-ingress-001",
                        "endpoint_id": "endpoint-release-ingress-001",
                        "display_name": "Release ingress fixture",
                    },
                    authorization=f"Bearer {operator}",
                )
                self.assertEqual(status, 201)
                status, workspace_registration = post_json(
                    f"{primary_url}/v1/nodes/{node['device_id']}/workspace-registrations",
                    {
                        "workspace_id": "workspace-release-ingress-001",
                        "workspace_generation": "generation-release-ingress-001",
                        "display_name": "Release ingress workspace",
                        "capabilities": {"read": True, "write": True, "exec": True},
                    },
                    authorization=f"Node {node['node_secret']}",
                )
                self.assertEqual(status, 201)
                self.assertEqual(workspace_registration["workspace_id"], "workspace-release-ingress-001")
                status, binding = post_json(
                    f"{primary_url}/v1/bindings",
                    {
                        "device_id": node["device_id"],
                        "workspace_id": "workspace-release-ingress-001",
                        "workspace_generation": "generation-release-ingress-001",
                        "display_name": "Release ingress workspace",
                    },
                    authorization=f"Bearer {operator}",
                )
                self.assertEqual(status, 201)
                status, context = post_json(
                    f"{primary_url}/v1/contexts",
                    {"binding_id": binding["binding_id"], "expires_at_ms": int(time.time() * 1000) + 60_000},
                    authorization=f"Bearer {operator}",
                )
                self.assertEqual(status, 201)
                status, grant = post_json(
                    f"{primary_url}/v1/mcp-access-grants",
                    {
                        "context_id": context["context_id"],
                        "principal_id": "openai-ubuntu-root-release-fixture",
                        "expires_at_ms": int(time.time() * 1000) + 30_000,
                    },
                    authorization=f"Bearer {operator}",
                )
                self.assertEqual(status, 201)
                initialize = {"jsonrpc": "2.0", "id": "release-ingress-001", "method": "initialize", "params": {}}
                status, primary_rejected = post_json(
                    f"{primary_url}/mcp",
                    initialize,
                    authorization=f"Bearer {grant['access_token']}",
                )
                self.assertEqual(status, 404)
                self.assertEqual(primary_rejected["error"]["code"], "NOT_FOUND")
                status, initialized = post_json(
                    mcp_url,
                    initialize,
                    authorization=f"Bearer {grant['access_token']}",
                )
                self.assertEqual(status, 200)
                self.assertEqual(initialized["result"]["_meta"]["control_plane"]["access_scope"], "server_issued_context_grant")

                backup = subprocess.run(
                    [str(release_root / "deploy" / "control-plane-backup.sh")],
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(backup.returncode, 0)
                backup_status = json.loads((backup_directory / "last-automatic-backup.json").read_text(encoding="utf-8"))
                self.assertEqual(backup_status["inspection"]["sqlite_integrity"], "ok")
                self.assertEqual(backup_status["inspection"]["unresolved_action_count"], 0)

                healthcheck = subprocess.run(
                    [str(release_root / "deploy" / "control-plane-healthcheck.sh")],
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(healthcheck.returncode, 0)
                health_status = json.loads((backup_directory / "last-healthcheck.json").read_text(encoding="utf-8"))
                self.assertEqual(health_status["deployment"]["package_source_sha256"], receipt["package_source_sha256"])

                status, recovery = post_json(
                    f"{primary_url}/v1/maintenance/admission",
                    {"mode": "recovery"},
                    authorization=f"Bearer {operator}",
                )
                self.assertEqual(status, 200)
                self.assertEqual(recovery["admission_mode"], "recovery")
                recovery_environment = {**environment, "CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION": "recovery"}
                recovery_healthcheck = subprocess.run(
                    [str(release_root / "deploy" / "control-plane-healthcheck.sh")],
                    env=recovery_environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(recovery_healthcheck.returncode, 0)
                recovery_status = json.loads((backup_directory / "last-healthcheck.json").read_text(encoding="utf-8"))
                self.assertEqual(recovery_status["deployment"]["admission_mode"], "recovery")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
