from __future__ import annotations

import base64
import unittest

from coding_tools_mcp.errors import JsonRpcError
from coding_tools_mcp.resolution_contract import (
    ResolutionContractError,
    contract_sha256,
    counterevidence_frame_update_advisory,
    normalize_problem_frame,
    normalize_resolution_envelope,
)
from coding_tools_mcp.tool_schema import validate_arguments


FRAME = {
    "schema_version": 1,
    "frame_id": "frame-1",
    "frame_revision": 1,
    "observation": "The bounded projection is stale",
    "a_star": {"domains": ["source", "runtime"], "phenomena": ["stale projection"], "ownership_boundaries": [], "relations": []},
    "governing_invariants": [{"invariant_id": "invariant-1", "summary": "Consumers use the canonical identity"}],
    "ownership": [],
    "hypotheses": [{"hypothesis_id": "hypothesis-1", "mechanism": "Runtime generation is stale", "prediction": "Restart exposes the current projection", "falsifier": "A fresh generation remains stale"}],
    "counterevidence": [],
    "decision_delta": {"tested_observation": "Fresh runtime read", "changed_decision": True, "next_action": "Rebind the runtime", "rationale": "The loaded generation differs from source"},
    "closure_falsifier": "A fresh runtime read still disagrees",
}

ENVELOPE = {
    "schema_version": 1,
    "direct_outcomes": [{"outcome_id": "outcome-1", "summary": "The projection matches the canonical state"}],
    "relevant_invariants": ["Consumers use the canonical identity"],
    "truth_domains": ["source", "runtime", "data"],
    "adjacent_risks": [{"risk_id": "risk-1", "summary": "A sibling consumer remains stale", "basis": "It shares the same identity boundary"}],
    "excluded_scope": ["Unrelated screens"],
    "required_evidence": [{"evidence_id": "evidence-1", "kind": "fresh runtime read", "provenance": "target runtime receipt", "status": "observed"}],
    "closure_falsification_probe": {"probe_id": "probe-1", "method": "Reload and compare the projection", "expected_failure_signal": "The projection remains stale", "executed": True, "result": "passed"},
}


class ResolutionContractTests(unittest.TestCase):
    def test_frame_is_canonical_and_shadow_only(self) -> None:
        normalized = normalize_problem_frame(FRAME)
        self.assertEqual(normalized["frame_id"], "frame-1")
        self.assertFalse(normalized["authority_side_effects"])
        self.assertEqual(contract_sha256(normalized), contract_sha256(dict(normalized)))

    def test_frame_rejects_authority_or_private_data(self) -> None:
        with self.assertRaises(ResolutionContractError):
            normalize_problem_frame({**FRAME, "authority_side_effects": True})
        with self.assertRaises(ResolutionContractError):
            normalize_problem_frame({**FRAME, "observation": "contact admin@example.com"})
        with self.assertRaises(ResolutionContractError):
            normalize_problem_frame({**FRAME, "observation": ["not", "text"]})

    def test_frame_rejects_bounded_encoded_credential_variants(self) -> None:
        private_value = "token=durable-secret-material"
        encoded_values = {
            "percent": "token%3Ddurable-secret-material",
            "escaped_ascii": r"token\x3ddurable-secret-material",
            "base64": base64.b64encode(private_value.encode("utf-8")).decode("ascii"),
            "hex": private_value.encode("utf-8").hex(),
        }
        for encoding, value in encoded_values.items():
            with self.subTest(encoding=encoding):
                with self.assertRaises(ResolutionContractError):
                    normalize_problem_frame({**FRAME, "observation": value})

    def test_counterevidence_advisory_is_content_free_and_never_authority(self) -> None:
        empty = counterevidence_frame_update_advisory(normalize_problem_frame(FRAME))
        self.assertEqual(empty["status"], "NO_COUNTEREVIDENCE_RECORDED")
        self.assertFalse(empty["frame_update_or_explanation_recommended"])
        self.assertFalse(empty["automatic_mutation_gate"])

        normalized = normalize_problem_frame({
            **FRAME,
            "counterevidence": [{
                "observation_id": "observation-2",
                "summary": "A fresh runtime remains stale",
                "impact": "The current causal frame may not explain the observation",
            }],
            "decision_delta": {
                **FRAME["decision_delta"],
                "changed_decision": False,
                "next_action": "Review whether the frame must change",
            },
        })
        advisory = counterevidence_frame_update_advisory(normalized)
        self.assertEqual(advisory["status"], "COUNTEREVIDENCE_REQUIRES_FRAME_REVIEW")
        self.assertEqual(advisory["counterevidence_count"], 1)
        self.assertTrue(advisory["frame_update_or_explanation_recommended"])
        self.assertTrue(advisory["same_family_retry_materiality_review_recommended"])
        self.assertFalse(advisory["decision_changed_attested"])
        self.assertFalse(advisory["materiality_inferred"])
        self.assertEqual(advisory["authority"], "ADVISORY_ONLY")
        self.assertFalse(advisory["automatic_mutation_gate"])

    def test_envelope_requires_passed_closure_falsifier(self) -> None:
        normalized = normalize_resolution_envelope(ENVELOPE)
        self.assertEqual(normalized["closure_falsification_probe"]["result"], "passed")
        with self.assertRaises(ResolutionContractError):
            normalize_resolution_envelope({**ENVELOPE, "closure_falsification_probe": {**ENVELOPE["closure_falsification_probe"], "executed": False}})
        with self.assertRaises(ResolutionContractError):
            normalize_resolution_envelope({
                **ENVELOPE,
                "required_evidence": [{
                    **ENVELOPE["required_evidence"][0],
                    "provenance": {"not": "text"},
                }],
            })

    def test_public_envelope_schema_matches_runtime_structure(self) -> None:
        normalized = normalize_resolution_envelope(ENVELOPE)
        validate_arguments("task_control", {"action": "accept", "problem_resolution_envelope": normalized})

        invalid_envelopes = {
            "top_level_extra": {**ENVELOPE, "unexpected": True},
            "direct_outcome_extra": {
                **ENVELOPE,
                "direct_outcomes": [{**ENVELOPE["direct_outcomes"][0], "unexpected": True}],
            },
            "risk_missing_basis": {
                **ENVELOPE,
                "adjacent_risks": [{"risk_id": "risk-1", "summary": "missing basis"}],
            },
            "evidence_bad_status": {
                **ENVELOPE,
                "required_evidence": [{**ENVELOPE["required_evidence"][0], "status": "guessed"}],
            },
            "probe_extra": {
                **ENVELOPE,
                "closure_falsification_probe": {**ENVELOPE["closure_falsification_probe"], "unexpected": True},
            },
            "probe_failed_result": {
                **ENVELOPE,
                "closure_falsification_probe": {**ENVELOPE["closure_falsification_probe"], "result": "failed"},
            },
        }
        for name, envelope in invalid_envelopes.items():
            with self.subTest(name=name):
                with self.assertRaises(JsonRpcError):
                    validate_arguments("task_control", {"action": "accept", "problem_resolution_envelope": envelope})
                with self.assertRaises(ResolutionContractError):
                    normalize_resolution_envelope(envelope)


if __name__ == "__main__":
    unittest.main()
