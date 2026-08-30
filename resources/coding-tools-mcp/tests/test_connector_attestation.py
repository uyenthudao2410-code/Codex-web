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

    def test_replay_against_replacement_runtime_binding_is_rejected(self) -> None:
        value = build_connector_attestation(self.secret, **self.binding)
        replacements = {
            "activation_epoch_id": "activation-replacement-002",
            "process_instance_id": "replacement-process",
            "server_instance_id": "replacement-server",
            "contract_sha256": "b" * 64,
        }
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                expected = {**self.binding, field: replacement}
                verified, reason = verify_connector_attestation(
                    value,
                    self.secret,
                    **{
                        key: item
                        for key, item in expected.items()
                        if key not in {"issued_at_unix_ms", "nonce"}
                    },
                    now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
                )
                self.assertFalse(verified)
                self.assertEqual(reason, "binding_mismatch")

    def test_tampering_is_rejected(self) -> None:
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

        replacement_nibble = "0" if value[-1] != "0" else "1"
        signature_tampered = f"{value[:-1]}{replacement_nibble}"
        verified, reason = verify_connector_attestation(
            signature_tampered,
            self.secret,
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "signature_invalid")

        verified, reason = verify_connector_attestation(
            value,
            "rotated-connector-attestation-secret",
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 1000,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "signature_invalid")

    def test_static_attestation_remains_valid_for_long_lived_exact_runtime(self) -> None:
        value = build_connector_attestation(self.secret, **self.binding)
        verified, reason = verify_connector_attestation(
            value,
            self.secret,
            **{key: value for key, value in self.binding.items() if key not in {"issued_at_unix_ms", "nonce"}},
            now_unix_ms=self.binding["issued_at_unix_ms"] + 24 * 60 * 60 * 1000,
        )
        self.assertTrue(verified)
        self.assertEqual(reason, "verified")

    def test_future_issued_attestation_is_rejected(self) -> None:
        now_unix_ms = self.binding["issued_at_unix_ms"]
        future_binding = {
            **self.binding,
            "issued_at_unix_ms": now_unix_ms + 5001,
        }
        value = build_connector_attestation(self.secret, **future_binding)
        verified, reason = verify_connector_attestation(
            value,
            self.secret,
            **{
                key: item
                for key, item in future_binding.items()
                if key not in {"issued_at_unix_ms", "nonce"}
            },
            now_unix_ms=now_unix_ms,
        )
        self.assertFalse(verified)
        self.assertEqual(reason, "timestamp_invalid")


if __name__ == "__main__":
    unittest.main()
