from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "deploy" / "prepare-control-plane-activation.py"
SPEC = importlib.util.spec_from_file_location("prepare_control_plane_activation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ActivationConfigTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path]:
        release = root / "release"
        release.mkdir()
        (release / "release-manifest.json").write_text(
            json.dumps(
                {
                    "release_name": "codex-control-plane-" + "a" * 40,
                    "source_revision": "a" * 40,
                    "package_source_sha256": "sha256:" + "b" * 64,
                }
            ),
            encoding="utf-8",
        )
        env = root / "control-plane.env"
        env.write_text(
            "# keep the operator secret and unrelated settings\n"
            "CONTROL_PLANE_OPERATOR_TOKEN=do-not-print\n"
            "CONTROL_PLANE_DECLARED_SOURCE_REVISION=old\n"
            "CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=sha256:" + "c" * 64 + "\n",
            encoding="utf-8",
        )
        drop_in = root / "10-immutable-release.conf"
        drop_in.write_text(
            "[Service]\n"
            "Environment=CONTROL_PLANE_DECLARED_SOURCE_REVISION=old\n"
            "Environment=CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=sha256:" + "c" * 64 + "\n",
            encoding="utf-8",
        )
        return release, env, drop_in

    def test_prepare_updates_both_identity_files_without_touching_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release, env, drop_in = self._fixture(Path(temporary))
            receipt = MODULE.prepare_activation_config(release_dir=release, env_file=env, drop_in=drop_in)
            self.assertTrue(receipt["changed"])
            env_text = env.read_text(encoding="utf-8")
            drop_in_text = drop_in.read_text(encoding="utf-8")
            self.assertIn("CONTROL_PLANE_OPERATOR_TOKEN=do-not-print", env_text)
            self.assertIn("CONTROL_PLANE_DECLARED_SOURCE_REVISION=" + "a" * 40, env_text)
            self.assertIn("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=sha256:" + "b" * 64, env_text)
            self.assertIn("Environment=CONTROL_PLANE_DECLARED_SOURCE_REVISION=" + "a" * 40, drop_in_text)
            self.assertIn("Environment=CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=sha256:" + "b" * 64, drop_in_text)
            self.assertNotIn("do-not-print", json.dumps(receipt))

    def test_check_only_is_idempotent_and_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release, env, drop_in = self._fixture(Path(temporary))
            before_env = env.read_bytes()
            receipt = MODULE.prepare_activation_config(
                release_dir=release, env_file=env, drop_in=drop_in, check_only=True
            )
            self.assertFalse(receipt["environment_matches"])
            self.assertFalse(receipt["drop_in_matches"])
            self.assertEqual(env.read_bytes(), before_env)
            MODULE.prepare_activation_config(release_dir=release, env_file=env, drop_in=drop_in)
            receipt = MODULE.prepare_activation_config(
                release_dir=release, env_file=env, drop_in=drop_in, check_only=True
            )
            self.assertTrue(receipt["environment_matches"])
            self.assertTrue(receipt["drop_in_matches"])
            self.assertFalse(receipt["changed"])

    def test_duplicate_identity_key_is_rejected_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            release, env, drop_in = self._fixture(Path(temporary))
            env.write_text(env.read_text(encoding="utf-8") + "CONTROL_PLANE_DECLARED_SOURCE_REVISION=duplicate\n", encoding="utf-8")
            before_env = env.read_bytes()
            before_drop_in = drop_in.read_bytes()
            with self.assertRaises(MODULE.ActivationConfigError):
                MODULE.prepare_activation_config(release_dir=release, env_file=env, drop_in=drop_in)
            self.assertEqual(env.read_bytes(), before_env)
            self.assertEqual(drop_in.read_bytes(), before_drop_in)


if __name__ == "__main__":
    unittest.main()
