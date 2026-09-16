from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tarfile
import tempfile
import time
import unittest
import urllib.request


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
            self.assertFalse(any(path.endswith(".sqlite3") for path in files))
            self.assertFalse(any(path.endswith("control-plane.env") for path in files))
            for relative, entry in files.items():
                target = release / relative
                self.assertTrue(target.is_file())
                self.assertEqual(entry["size_bytes"], target.stat().st_size)
                self.assertEqual(entry["sha256"], sha256_file(target))

            for launcher in (
                "deploy/control-plane-launcher.sh",
                "deploy/control-plane-backup.sh",
                "deploy/control-plane-healthcheck.sh",
            ):
                self.assertNotEqual((release / launcher).stat().st_mode & 0o111, 0)

            service_templates = {
                "codex-control-plane.service.example": "control-plane-launcher.sh",
                "codex-control-plane-backup.service.example": "control-plane-backup.sh",
                "codex-control-plane-healthcheck.service.example": "control-plane-healthcheck.sh",
            }
            for template, launcher in service_templates.items():
                content = (release / "deploy" / template).read_text(encoding="utf-8")
                self.assertIn(f"current/deploy/{launcher}", content)
                self.assertNotIn("/DEV/Codex-web", content)

            with tarfile.open(archive, "r:gz") as bundle:
                names = set(bundle.getnames())
            prefix = f"{receipt['release_name']}/"
            self.assertIn(f"{prefix}release-manifest.json", names)
            self.assertIn(f"{prefix}control-plane/control_plane/http_api.py", names)
            self.assertFalse(any(".coding-tools" in name or name.endswith(".sqlite3") for name in names))

    def test_refuses_to_overwrite_a_previously_built_release(self) -> None:
        revision = "b" * 40
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            BUILDER.build_release(ROOT, output, revision, require_clean_source=False)
            with self.assertRaises(BUILDER.ReleaseBuildError):
                BUILDER.build_release(ROOT, output, revision, require_clean_source=False)

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
            port = free_port()
            environment = {
                **os.environ,
                "CONTROL_PLANE_DB": str(database),
                "CONTROL_PLANE_BIND": "127.0.0.1",
                "CONTROL_PLANE_PORT": str(port),
                "CONTROL_PLANE_OPERATOR_TOKEN": "x" * 32,
                "CONTROL_PLANE_DECLARED_SOURCE_REVISION": revision,
                "CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256": receipt["package_source_sha256"],
            }
            process = subprocess.Popen(
                [str(release_root / "deploy" / "control-plane-launcher.sh")],
                cwd=release_root,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                health = wait_health(f"http://127.0.0.1:{port}/healthz", receipt["package_source_sha256"])
                self.assertEqual(health["schema_version"], receipt["control_plane_schema_version"])
                self.assertEqual(health["declared_source_revision"], revision)
                self.assertTrue(database.is_file())
                self.assertFalse(str(database).startswith(str(release_root)))
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
