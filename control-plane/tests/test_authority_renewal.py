from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError
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
        self.grant = {
            "grant_id": self.grant_id, "owner_id": "owner_test", "principal_id": "svcprn_test",
            "expires_at_ms": self.now + 6 * 60 * 60 * 1000, "revoked_at_ms": None,
        }
        self.anchor = {
            "decision_id": self.decision_id, "owner_id": "owner_test", "principal_id": "svcprn_test",
            "device_id": "device_test", "endpoint_id": "endpoint_test", "binding_id": "bind_test",
            "workspace_id": "workspace_test", "workspace_generation": "generation_test",
            "expires_at_ms": self.now + 6 * 60 * 60 * 1000, "revoked_at_ms": None,
        }
        self.decisions = [self.anchor]
        self.admission = "scoped_pilot"
        self.environment = {
            "CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED": "true",
            "CONTROL_PLANE_OPERATOR_URL": "https://control-plane.example",
            "CONTROL_PLANE_OPERATOR_TOKEN": "operator-never-printed",
            "CONTROL_PLANE_MCP_SERVICE_GRANT_ID": self.grant_id,
            "CONTROL_PLANE_SCOPED_PILOT_DECISION_ID": self.decision_id,
            "CONTROL_PLANE_AUTHORITY_GRANT_TTL_SECONDS": "28800",
            "CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS": "43200",
            "CONTROL_PLANE_AUTHORITY_GRANT_WINDOW_SECONDS": "25200",
            "CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS": "25200",
        }

    def opener(self, request, timeout=0):
        path = urlparse(request.full_url).path
        method = request.method
        payload = None if request.data is None else json.loads(request.data.decode("utf-8"))
        self.calls.append((method, path, payload))
        if path == "/v1/mcp-service-grants":
            return _Response({"mcp_service_grants": [self.grant]})
        if path == "/v1/scoped-pilot-decisions":
            return _Response({"scoped_pilot_decisions": self.decisions})
        if path == "/v1/maintenance/admission":
            return _Response({"admission_mode": self.admission})
        if path.endswith("/renew"):
            assert payload is not None
            target = self.grant if path.startswith("/v1/mcp-service-grants/") else next(
                decision for decision in self.decisions if path == f"/v1/scoped-pilot-decisions/{decision['decision_id']}/renew"
            )
            return _Response({**target, "expires_at_ms": payload["expires_at_ms"]})
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

    def test_renewal_follows_selected_folder_on_the_approved_node_at_existing_twenty_hour_ttl(self) -> None:
        self.environment["CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS"] = "72000"
        self.environment["CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS"] = "7200"
        self.grant["expires_at_ms"] = self.now + 8 * 60 * 60 * 1000
        self.anchor["revoked_at_ms"] = self.now - 1000
        selected = {**self.anchor, "decision_id": "pilot_selected_folder", "binding_id": "bind_selected",
                    "workspace_id": "workspace_selected", "workspace_generation": "generation_selected",
                    "revoked_at_ms": None, "expires_at_ms": self.now + 60 * 60 * 1000}
        self.decisions.append(selected)
        before_anchor = dict(self.anchor)
        before_selected = dict(selected)

        result = MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)

        self.assertEqual(result["configured_decision_id"], self.decision_id)
        self.assertEqual(result["decision_id"], selected["decision_id"])
        self.assertTrue(result["followed_selected_pilot"])
        self.assertFalse(result["grant"]["renewed"])
        self.assertTrue(result["decision"]["renewed"])
        self.assertEqual(result["decision"]["expires_at_ms"], self.now + 20 * 60 * 60 * 1000)
        self.assertEqual(self.anchor, before_anchor, "the configured historical anchor remains immutable")
        self.assertEqual(selected, before_selected, "the timer does not rewrite observations or activate a folder")
        posts = [call for call in self.calls if call[0] == "POST"]
        self.assertEqual(posts, [("POST", f"/v1/scoped-pilot-decisions/{selected['decision_id']}/renew",
                                 {"expires_at_ms": self.now + 20 * 60 * 60 * 1000})])

    def test_selected_pilot_identity_or_ambiguous_scope_fails_before_any_mutation(self) -> None:
        for scenario in ["owner_id", "principal_id", "device_id", "endpoint_id", "multiple-live", "no-live", "missing-anchor"]:
            with self.subTest(scenario=scenario):
                self.calls.clear()
                anchor = {**self.anchor, "revoked_at_ms": self.now - 1000}
                selected = {**self.anchor, "decision_id": "pilot_selected", "revoked_at_ms": None}
                if scenario in {"owner_id", "principal_id", "device_id", "endpoint_id"}:
                    selected[scenario] = "different_identity"
                self.decisions = [anchor, selected]
                if scenario == "multiple-live":
                    self.decisions.append({**selected, "decision_id": "pilot_other"})
                elif scenario == "no-live":
                    selected["expires_at_ms"] = self.now
                elif scenario == "missing-anchor":
                    self.decisions = [selected]
                with self.assertRaises(MODULE.RenewalError):
                    MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)
                self.assertFalse(any(method == "POST" for method, _path, _body in self.calls))

    def test_parallel_workspace_decisions_renew_without_changing_their_scopes(self) -> None:
        other = {**self.anchor, "decision_id": "pilot_other_workspace", "binding_id": "bind_other",
                 "workspace_id": "workspace_other", "workspace_generation": "generation_other"}
        unrelated = {**other, "decision_id": "pilot_unrelated_node", "device_id": "device_other"}
        self.decisions.extend([other, unrelated])
        before = json.dumps(self.decisions, sort_keys=True)
        result = MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)
        self.assertEqual({item["decision_id"] for item in result["decisions"]}, {self.decision_id, other["decision_id"]})
        self.assertTrue(all(item["renewed"] for item in result["decisions"]))
        self.assertEqual(json.dumps(self.decisions, sort_keys=True), before)
        posts = [path for method, path, _body in self.calls if method == "POST"]
        self.assertIn(f"/v1/scoped-pilot-decisions/{other['decision_id']}/renew", posts)
        self.assertNotIn(f"/v1/scoped-pilot-decisions/{unrelated['decision_id']}/renew", posts)

    def test_configured_grant_and_anchor_must_have_matching_valid_identity(self) -> None:
        for field in ["owner_id", "principal_id", "device_id", "endpoint_id"]:
            with self.subTest(field=field):
                self.calls.clear()
                anchor = dict(self.anchor)
                anchor[field] = "" if field in {"device_id", "endpoint_id"} else "different_identity"
                self.decisions = [anchor]
                with self.assertRaises(MODULE.RenewalError):
                    MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)
                self.assertFalse(any(method == "POST" for method, _path, _body in self.calls))

    def test_recovery_allows_grant_only_renewal_with_revoked_expired_pilot_anchor(self) -> None:
        self.admission = "recovery"
        self.anchor.update(revoked_at_ms=self.now - 1000, expires_at_ms=self.now - 1000)
        result = MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)
        self.assertTrue(result["grant"]["renewed"])
        self.assertFalse(result["decision"]["renewed"])
        self.assertFalse(any(path.startswith("/v1/scoped-pilot-decisions/") for _method, path, _body in self.calls))

    def test_pending_work_or_concurrent_folder_change_blocks_server_renewal_without_retry(self) -> None:
        self.grant["expires_at_ms"] = self.now + 8 * 60 * 60 * 1000

        def blocked_opener(request, timeout=0):
            path = urlparse(request.full_url).path
            if request.method == "POST":
                self.calls.append((request.method, path, json.loads(request.data.decode("utf-8"))))
                raise HTTPError(request.full_url, 409, "Conflict", {}, None)
            return self.opener(request, timeout)

        with self.assertRaisesRegex(MODULE.RenewalError, "operator API returned HTTP 409"):
            MODULE.renew_authority(environment=self.environment, opener=blocked_opener, now_ms=self.now)
        self.assertEqual(len([call for call in self.calls if call[0] == "POST"]), 1)
        self.assertFalse(any(path == "/v1/maintenance/admission" and method == "POST" for method, path, _body in self.calls))

    def test_wrong_renewal_receipt_cannot_claim_success_for_another_target(self) -> None:
        self.grant["expires_at_ms"] = self.now + 8 * 60 * 60 * 1000

        def wrong_receipt_opener(request, timeout=0):
            receipt = self.opener(request, timeout)
            if request.method == "POST":
                payload = json.loads(receipt.payload.decode("utf-8"))
                return _Response({**payload, "workspace_generation": "generation_other"})
            return receipt

        with self.assertRaisesRegex(MODULE.RenewalError, "renewal receipt changed"):
            MODULE.renew_authority(environment=self.environment, opener=wrong_receipt_opener, now_ms=self.now)

    def test_renewal_never_shortens_authority_when_window_exceeds_ttl(self) -> None:
        self.environment["CONTROL_PLANE_AUTHORITY_GRANT_TTL_SECONDS"] = "3600"
        self.environment["CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS"] = "1800"
        result = MODULE.renew_authority(environment=self.environment, opener=self.opener, now_ms=self.now)
        self.assertFalse(result["grant"]["renewed"])
        self.assertFalse(result["decision"]["renewed"])
        self.assertFalse(any(method == "POST" for method, _path, _body in self.calls))

    def test_disabled_timer_is_a_noop(self) -> None:
        self.assertEqual(
            MODULE.renew_authority(environment={"CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED": "false"}),
            {"enabled": False, "state": "disabled"},
        )

    def test_oneshot_renewal_timer_repeats_after_service_completion(self) -> None:
        timer = (ROOT / "deploy" / "codex-control-plane-authority-renewal.timer.example").read_text(encoding="utf-8")
        self.assertIn("OnActiveSec=5min", timer)
        self.assertIn("OnUnitInactiveSec=15min", timer)
        self.assertNotIn("OnBootSec=5min", timer)
        self.assertNotIn("OnUnitActiveSec=15min", timer)

    def test_live_authority_outside_seconds_windows_is_not_renewed(self) -> None:
        def outside_window_opener(request, timeout=0):
            path = urlparse(request.full_url).path
            method = request.method
            payload = None if request.data is None else json.loads(request.data.decode("utf-8"))
            self.calls.append((method, path, payload))
            if path == "/v1/mcp-service-grants":
                return _Response({"mcp_service_grants": [{
                    **self.grant,
                    "expires_at_ms": self.now + 8 * 60 * 60 * 1000,
                    "revoked_at_ms": None,
                }]})
            if path == "/v1/scoped-pilot-decisions":
                return _Response({"scoped_pilot_decisions": [{
                    **self.anchor,
                    "expires_at_ms": self.now + 8 * 60 * 60 * 1000,
                    "revoked_at_ms": None,
                }]})
            if path == "/v1/maintenance/admission":
                return _Response({"admission_mode": "scoped_pilot"})
            raise AssertionError(path)

        result = MODULE.renew_authority(
            environment=self.environment, opener=outside_window_opener, now_ms=self.now,
        )
        self.assertFalse(result["grant"]["renewed"])
        self.assertFalse(result["decision"]["renewed"])
        self.assertFalse(any(path.endswith("/renew") for _method, path, _payload in self.calls))


if __name__ == "__main__":
    unittest.main()
