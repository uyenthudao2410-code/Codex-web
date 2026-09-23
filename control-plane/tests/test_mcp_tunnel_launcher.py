from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "deploy" / "control-plane-mcp-tunnel-launcher.sh"
HEADER_SENTINEL = "Bearer fixture-scoped-header-never-put-in-argv"
OPERATOR_SENTINEL = "fixture-operator-token-never-pass-to-tunnel"


@unittest.skipUnless(os.name == "posix", "the Ubuntu launcher requires a POSIX host")
class McpTunnelLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mcp-tunnel-launcher-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.client = self.directory / "fake tunnel client"
        self.client.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "print(json.dumps({'argv': sys.argv[1:], "
            "'operator_token_present': 'CONTROL_PLANE_OPERATOR_TOKEN' in os.environ}))\n",
            encoding="utf-8",
        )
        self.client.chmod(0o700)
        self.header = self.directory / "scoped MCP header"
        self.header.write_text(HEADER_SENTINEL, encoding="utf-8")
        self.header.chmod(0o600)
        # Do not inherit the developer's live service configuration or keys.
        self.environment = {
            "PATH": os.defpath,
            "LC_ALL": "C",
            "CONTROL_PLANE_TUNNEL_CLIENT": str(self.client),
            "CONTROL_PLANE_TUNNEL_PROFILE": "ubuntu-root-mcp-fixture",
            "CONTROL_PLANE_TUNNEL_ID": "tunnel_fixture_12345",
            "CONTROL_PLANE_MCP_AUTH_HEADER_FILE": str(self.header),
        }

    def run_launcher(self, **overrides: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["bash", str(LAUNCHER)],
            env={**self.environment, **overrides},
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertNotIn(HEADER_SENTINEL, result.stdout + result.stderr)
        self.assertNotIn(OPERATOR_SENTINEL, result.stdout + result.stderr)
        return result

    def test_pins_tunnel_identity_main_loopback_url_and_file_references(self) -> None:
        result = self.run_launcher(CONTROL_PLANE_OPERATOR_TOKEN=OPERATOR_SENTINEL)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "argv": [
                    "run",
                    "--profile", "ubuntu-root-mcp-fixture",
                    "--control-plane.tunnel-id", "tunnel_fixture_12345",
                    "--mcp.server-url", "url=http://127.0.0.1:8766/mcp,channel=main",
                    "--mcp.extra-headers", f"Authorization: file:{self.header}",
                    "--mcp.discovery-extra-headers", f"Authorization: file:{self.header}",
                ],
                "operator_token_present": False,
            },
        )
        self.assertEqual(result.stderr, "")

    def test_uses_validated_configured_port_with_read_only_header_file(self) -> None:
        self.header.chmod(0o400)
        result = self.run_launcher(CONTROL_PLANE_MCP_PORT="18866")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "url=http://127.0.0.1:18866/mcp,channel=main",
            json.loads(result.stdout)["argv"],
        )

    def test_private_service_mode_uses_protected_header_for_discovery_and_calls(self) -> None:
        result = self.run_launcher(CONTROL_PLANE_MCP_AUTH_MODE="private_tunnel_service")
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(result.stdout)["argv"]
        self.assertIn("--mcp.discovery-extra-headers", argv)
        self.assertIn("--mcp.extra-headers", argv)
        self.assertEqual(argv.count(f"Authorization: file:{self.header}"), 2)

    def test_oauth_mode_never_injects_the_legacy_authorization_header(self) -> None:
        self.environment.pop("CONTROL_PLANE_MCP_AUTH_HEADER_FILE")
        result = self.run_launcher(CONTROL_PLANE_MCP_AUTH_MODE="oauth_introspection")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "argv": [
                    "run",
                    "--profile", "ubuntu-root-mcp-fixture",
                    "--control-plane.tunnel-id", "tunnel_fixture_12345",
                    "--mcp.server-url", "url=http://127.0.0.1:8766/mcp,channel=main",
                ],
                "operator_token_present": False,
            },
        )

    def test_oauth_mode_refuses_an_accidental_static_header_or_unknown_auth_mode(self) -> None:
        result = self.run_launcher(CONTROL_PLANE_MCP_AUTH_MODE="oauth_introspection")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("must be unset", result.stderr)

        result = self.run_launcher(CONTROL_PLANE_MCP_AUTH_MODE="not-a-mode")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("CONTROL_PLANE_MCP_AUTH_MODE", result.stderr)

    def test_refuses_invalid_routing_before_starting_client(self) -> None:
        for name, value in (
            ("CONTROL_PLANE_MCP_BIND", "0.0.0.0"),
            ("CONTROL_PLANE_MCP_BIND", "100.116.112.22"),
            ("CONTROL_PLANE_MCP_PORT", "22"),
            ("CONTROL_PLANE_MCP_PORT", "65536"),
            ("CONTROL_PLANE_MCP_PORT", "08766"),
            ("CONTROL_PLANE_MCP_PORT", "8766/mcp,channel=other"),
            ("CONTROL_PLANE_MCP_PORT", "999999999999999999999999999"),
            ("CONTROL_PLANE_TUNNEL_ID", "wrong-identity"),
            ("CONTROL_PLANE_TUNNEL_ID", "tunnel_fixture\nother"),
        ):
            with self.subTest(name=name, value=value):
                result = self.run_launcher(**{name: value})
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_refuses_missing_header_reference(self) -> None:
        self.environment.pop("CONTROL_PLANE_MCP_AUTH_HEADER_FILE")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_refuses_nonregular_empty_relative_and_symlink_header_files(self) -> None:
        symlink = self.directory / "header-link"
        symlink.symlink_to(self.header)
        empty = self.directory / "empty"
        empty.touch(mode=0o600)
        fifo = self.directory / "fifo"
        os.mkfifo(fifo, mode=0o600)
        unsafe_name = self.directory / "unsafe\nheader"
        unsafe_name.write_text(HEADER_SENTINEL, encoding="utf-8")
        unsafe_name.chmod(0o600)
        for reference in (
            self.directory / "missing", self.directory, symlink, empty, fifo,
            unsafe_name, "relative-header",
        ):
            with self.subTest(reference=str(reference)):
                result = self.run_launcher(CONTROL_PLANE_MCP_AUTH_HEADER_FILE=str(reference))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_refuses_nonprivate_or_executable_header_files(self) -> None:
        for mode in (0o644, 0o640, 0o660, 0o700, 0o777):
            with self.subTest(mode=oct(mode)):
                self.header.chmod(mode)
                result = self.run_launcher()
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("mode 0400 or 0600", result.stderr)

    def test_refuses_nonregular_or_nonexecutable_client(self) -> None:
        self.client.chmod(0o600)
        for client in (self.client, self.directory, self.directory / "missing", "relative-client"):
            with self.subTest(client=str(client)):
                result = self.run_launcher(CONTROL_PLANE_TUNNEL_CLIENT=str(client))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")


class McpTunnelDeploymentTemplateTests(unittest.TestCase):
    def test_tunnel_unit_loads_only_separate_tunnel_environment(self) -> None:
        unit = (ROOT / "deploy" / "codex-control-plane-mcp-tunnel.service.example").read_text(encoding="utf-8")
        self.assertEqual(
            [line for line in unit.splitlines() if line.startswith("EnvironmentFile=")],
            ["EnvironmentFile=%h/.config/codex-control-plane/mcp-tunnel.env"],
        )
        template = (ROOT / "deploy" / "control-plane-mcp-tunnel.env.example").read_text(encoding="utf-8")
        self.assertEqual(
            {line.split("=", 1)[0] for line in template.splitlines() if line and not line.startswith("#")},
            {
                "CONTROL_PLANE_TUNNEL_CLIENT", "CONTROL_PLANE_TUNNEL_PROFILE",
                "CONTROL_PLANE_TUNNEL_ID", "CONTROL_PLANE_MCP_BIND", "CONTROL_PLANE_MCP_PORT",
                "CONTROL_PLANE_MCP_AUTH_MODE", "CONTROL_PLANE_MCP_AUTH_HEADER_FILE",
            },
        )

    def test_release_allowlist_requires_the_separate_tunnel_environment_template(self) -> None:
        spec = importlib.util.spec_from_file_location("mcp_tunnel_release_builder", ROOT / "scripts" / "build-control-plane-release.py")
        assert spec is not None and spec.loader is not None
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        self.assertIn("control-plane-mcp-tunnel.env.example", builder.DEPLOY_FILES)
        self.assertIn("deploy/control-plane-mcp-tunnel.env.example", builder.REQUIRED_RELEASE_FILES)


if __name__ == "__main__":
    unittest.main()
