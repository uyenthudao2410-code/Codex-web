from __future__ import annotations

import unittest

from coding_tools_mcp.connector_attestation import (
    build_connector_attestation,
    verify_connector_attestation,
)


class ConnectorAttestationTests(unittest.TestCase):
    secret = "connector-attestation-test-secret"
    binding = {
        "client_id": "chatweb",
        "client_type": "chatweb",
        "activation_epoch_id": "activation-test-001",
        "process_instance_id": "mcp-process-test",
        "server_instance_id": "mcp-server-test",
        "contract_sha256": "a" * 64,
        "issued_at_unix_ms": 1_700_000_000_000,
        "nonce": "0123456789abcdef0123456789abcdef",
    }

    def test_round_trip_binds_exact_runtime_tuple(self) -> None:
        value = build_connector_attestation(self.secret, **self.binding)
        verified, reason = verify_connector_attestation(
            value,
            self.secret,
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
        )
        self.assertTrue(verified)
        self.assertEqual(reason, "verified")

    def test_replay_against_replacement_process_is_rejected(self) -> None:
        value = build_connector_attestation(self.secret, **self.binding)
        verified, reason = verify_connector_attestation(
            value,
            self.secret,
            **{key: value for key, value in {**self.binding, "process_instance_id": "replacement-process"}.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "binding_mismatch")

    def test_tampering_and_expiry_are_rejected(self) -> None:
        value = build_connector_attestation(self.secret, **self.binding)
        tampered = value.replace("chatweb|chatweb|", "chatweb|opencode|", 1)
        verified, reason = verify_connector_attestation(
            tampered,
            self.secret,
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "binding_mismatch")

        verified, reason = verify_connector_attestation(
            value,
            self.secret,
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 15 * 60 * 1000 + 1,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "timestamp_expired")


if __name__ == "__main__":
    unittest.main()
