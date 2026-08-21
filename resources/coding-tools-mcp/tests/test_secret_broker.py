from __future__ import annotations

import json
import unittest

from coding_tools_mcp.errors import JsonRpcError
from coding_tools_mcp.secret_broker import (
    AUTH_HANDLE_ENV,
    MCP_AUTH_HANDLE,
    OPENAI_API_KEY_HANDLE,
    SECRET_BROKER_ENV,
    SecretBroker,
    SecretBrokerError,
)
from coding_tools_mcp.tool_schema import validate_arguments


class SecretBrokerTests(unittest.TestCase):
    def test_envelope_is_consumed_and_status_is_content_free(self) -> None:
        fake_secret = "test-only-secret-material"
        env = {
            SECRET_BROKER_ENV: json.dumps({MCP_AUTH_HANDLE: fake_secret}),
            AUTH_HANDLE_ENV: MCP_AUTH_HANDLE,
        }
        broker = SecretBroker.from_environment(env)
        self.assertNotIn(SECRET_BROKER_ENV, env)
        self.assertEqual(broker.resolve(MCP_AUTH_HANDLE), fake_secret)
        serialized = json.dumps(broker.status(), sort_keys=True)
        self.assertNotIn(fake_secret, serialized)
        self.assertNotIn(fake_secret, repr(broker))
        self.assertEqual(broker.status()["handle_count"], 1)
        self.assertTrue(broker.status()["content_free"])

    def test_legacy_auth_and_openai_are_captured_then_removed_from_ambient_env(self) -> None:
        env = {
            "CODING_TOOLS_MCP_AUTH_TOKEN": "legacy-test-bearer",
            "OPENAI_API_KEY": "test-provider-key",
        }
        broker = SecretBroker.from_environment(env)
        self.assertEqual(env, {})
        self.assertEqual(broker.resolve(MCP_AUTH_HANDLE), "legacy-test-bearer")
        self.assertEqual(broker.resolve(OPENAI_API_KEY_HANDLE), "test-provider-key")
        child = broker.inject_env({"PATH": "safe"}, {"OPENAI_API_KEY": OPENAI_API_KEY_HANDLE})
        self.assertEqual(child["PATH"], "safe")
        self.assertEqual(child["OPENAI_API_KEY"], "test-provider-key")
        self.assertNotIn("CODING_TOOLS_MCP_AUTH_TOKEN", child)

    def test_malformed_or_conflicting_envelopes_fail_without_exposing_secret_values(self) -> None:
        raw_secret = "do-not-print-this-test-secret"
        cases = [
            {SECRET_BROKER_ENV: "{not-json"},
            {SECRET_BROKER_ENV: json.dumps({"not-a-secret-handle": raw_secret})},
            {
                SECRET_BROKER_ENV: json.dumps({MCP_AUTH_HANDLE: raw_secret}),
                "CODING_TOOLS_MCP_AUTH_TOKEN": "different-test-secret",
            },
        ]
        for env in cases:
            with self.subTest(env_keys=sorted(env)), self.assertRaises(SecretBrokerError) as raised:
                SecretBroker.from_environment(dict(env))
            rendered = str(raised.exception)
            self.assertNotIn(raw_secret, rendered)
            self.assertNotIn("different-test-secret", rendered)

    def test_model_arguments_cannot_add_network_capability_to_exec_command(self) -> None:
        with self.assertRaises(JsonRpcError):
            validate_arguments(
                "exec_command",
                {"cmd": "echo bounded", "allow_network": True},
            )


if __name__ == "__main__":
    unittest.main()
