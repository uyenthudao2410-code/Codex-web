from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "deploy" / "control-plane-authority-renewal.py"
SPEC = importlib.util.spec_from_file_location("control_plane_authority_renewal", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class AuthorityRenewalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_700_000_000_000
        self.grant_id = "mcpsvcgrant_test"
        self.decision_id = "pilot_test"
        self.calls: list[tuple[str, str, dict | None]] = []
        self.environment = {
            "CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED": "true",
            "CONTROL_PLANE_OPERATOR_URL": "https://control-plane.example",
            "CONTROL_PLANE_OPERATOR_TOKEN": "operator-never-printed",
            "CONTROL_PLANE_MCP_SERVICE_GRANT_ID": self.grant_id,
            "CONTROL_PLANE_SCOPED_PILOT_DECISION_ID": self.decision_id,
            "CONTROL_PLANE_AUTHORITY_GRANT_TTL_SECONDS": "3600",
            "CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS": "1800",
            "CONTROL_PLANE_AUTHORITY_GRANT_WINDOW_SECONDS": "7200",
            "CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS": "7200",
        }

    def opener(self, request, timeout=0):
        path = urlparse(request.full_url).path
        method = request.method
        payload = None if request.data is None else json.loads(request.data.decode("utf-8"))
        self.calls.append((method, path, payload))
        if path == "/v1/mcp-service-grants":
            return _Response({"mcp_service_grants": [{
                "grant_id": self.grant_id, "expires_at_ms": self.now + 1_000, "revoked_at_ms": None,
            }]})
        if path == "/v1/scoped-pilot-decisions":
            return _Response({"scoped_pilot_decisions": [{
                "decision_id": self.decision_id, "expires_at_ms": self.now + 1_000, "revoked_at_ms": None,
            }]})
        if path == "/v1/maintenance/admission":
            return _Response({"admission_mode": "scoped_pilot"})
        if path.endswith("/renew"):
            assert payload is not None
            return _Response({"expires_at_ms": payload["expires_at_ms"]})
        raise AssertionError(path)

    def test_renews_live_grant_and_exact_pilot_without_opening_admission(self) -> None:
        result = MODULE.renew_authority(
            environment=self.environment, opener=self.opener, now_ms=self.now,
        )
        self.assertTrue(result["grant"]["renewed"])
        self.assertTrue(result["decision"]["renewed"])
        self.assertEqual(
            [path for _method, path, _payload in self.calls],
            [
                "/v1/mcp-service-grants", "/v1/scoped-pilot-decisions",
                "/v1/maintenance/admission",
                f"/v1/mcp-service-grants/{self.grant_id}/renew",
                f"/v1/scoped-pilot-decisions/{self.decision_id}/renew",
            ],
        )
        self.assertNotIn(self.environment["CONTROL_PLANE_OPERATOR_TOKEN"], json.dumps(result))

    def test_recovery_does_not_reopen_or_renew_pilot(self) -> None:
        def recovery_opener(request, timeout=0):
            if urlparse(request.full_url).path == "/v1/maintenance/admission":
                return _Response({"admission_mode": "recovery"})
            return self.opener(request, timeout)

        result = MODULE.renew_authority(
            environment=self.environment, opener=recovery_opener, now_ms=self.now,
        )
        self.assertTrue(result["grant"]["renewed"])
        self.assertFalse(result["decision"]["renewed"])
        self.assertNotIn(f"/v1/scoped-pilot-decisions/{self.decision_id}/renew", [path for _method, path, _payload in self.calls])

    def test_disabled_timer_is_a_noop(self) -> None:
        self.assertEqual(
            MODULE.renew_authority(environment={"CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED": "false"}),
            {"enabled": False, "state": "disabled"},
        )


if __name__ == "__main__":
    unittest.main()
