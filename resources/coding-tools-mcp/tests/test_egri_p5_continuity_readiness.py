from __future__ import annotations

import unittest

from coding_tools_mcp.egri_p5_continuity_readiness import (
    egri_p5_continuity_readiness,
)
from coding_tools_mcp.rotation_advisory_study import (
    ROTATION_ADVISORY_STUDY_SCHEMA_VERSION,
)
from coding_tools_mcp.semantic_localization import (
    DEFAULT_UNAVAILABLE_REASON,
    SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
)


BASELINE_FINGERPRINT = "a" * 64
STRATA = [
    "problem_task_class",
    "execution_route",
    "quality_oracle",
    "source_identity",
    "session_boundary_condition",
    "continuity_baseline_version",
    "semantic_localization_condition",
]


def rotation_readiness(*, ready: bool = True) -> dict[str, object]:
    return {
        "schema_version": ROTATION_ADVISORY_STUDY_SCHEMA_VERSION,
        "status": (
            "READY_FOR_EXPLICIT_OPERATOR_STUDY_OPEN"
            if ready
            else "HOLD_MANUAL_CONTINUITY_NOT_PROVEN"
        ),
        "manual_continuity_safety": {"proven_safe": ready},
        "preregistration": {"valid": ready},
        "authority": {
            "study_epoch_opened": False,
            "assignment_created": False,
            "rotation_recommendation_emitted": False,
            "production_behavior_changed": False,
        },
    }


def baseline_acceptance() -> dict[str, object]:
    return {
        "schema_version": 1,
        "acceptance_id": "common-continuity-baseline-v1",
        "accepted": True,
        "common_baseline_fingerprint": BASELINE_FINGERPRINT,
        "accepted_components": [
            "goal_pursuit_projector",
            "controller_knowledge_checkpoint_and_recovery",
            "continuity_core",
            "same_role_resume",
            "ui_independent_execution",
            "same_usage_and_economics_instrumentation",
        ],
        "continuity_contract_version": "continuity-core-v1",
        "controller_knowledge_checkpoint_version": "knowledge-checkpoint-v1",
        "same_role_resume_verified": True,
        "ui_independent_execution_verified": True,
        "same_usage_and_economics_instrumentation_verified": True,
        "counterevidence_safety_floor_status": "NOT_APPLICABLE",
        "public_tool_count": 8,
    }


def preregistration() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "egri-continuity-ab-v1",
        "treatment_id": "egri-enrichment",
        "treatment_version": "1",
        "treatment_fingerprint": "b" * 64,
        "common_baseline_fingerprint": BASELINE_FINGERPRINT,
        "treatment_only_components": [
            "workspace_evidence_index",
            "case_memory",
            "enriched_frame_and_discriminator_packet",
        ],
        "strata": list(STRATA),
        "outcomes": [
            "trusted_problem_resolution",
            "ttpr",
            "accepted_result_economics",
            "accepted_result_quality",
            "resume_success",
            "state_loss",
            "duplicate_work",
            "wrong_frame_or_reopen",
            "rework",
        ],
        "minimum_qualifying_rows_per_arm": 5,
        "assignment_before_arm_action": True,
        "same_common_baseline_both_arms": True,
        "same_continuity_semantics_both_arms": True,
        "treatment_requires_semantic_localization": False,
        "deterministic_text_search_fallback_required": True,
        "source_identity_and_freshness_required": True,
        "max_definition_depth": 3,
        "max_reference_edges": 100,
        "max_call_hierarchy_depth": 3,
        "max_evidence_files": 24,
        "max_evidence_bytes": 262_144,
        "workspace_evidence_index_is_authority": False,
        "case_memory_is_authority": False,
        "automatic_activation": False,
        "automatic_promotion": False,
        "public_tool_count": 8,
    }


def aa_health() -> dict[str, object]:
    return {
        "schema_version": 1,
        "receipt_id": "egri-aa-health-v1",
        "study_id": "egri-continuity-ab-v1",
        "status": "PASS",
        "common_baseline_fingerprint": BASELINE_FINGERPRINT,
        "manifest_fingerprint": "c" * 64,
        "instrumentation_fingerprint": "d" * 64,
        "observed_strata": list(STRATA),
        "assignment_before_arm_action_verified": True,
        "arms_content_equivalent": True,
        "same_continuity_semantics_verified": True,
        "outcome_instrumentation_complete": True,
        "state_loss_count": 0,
        "duplicate_work_count": 0,
        "qualifying_observations_per_arm": 1,
        "synthetic_or_fixture_evidence": False,
        "automatic_activation": False,
        "automatic_promotion": False,
    }


def unavailable_semantic_status() -> dict[str, object]:
    return {
        "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
        "available": False,
        "provider": None,
        "reason": DEFAULT_UNAVAILABLE_REASON,
        "read_only": True,
    }


class EgriP5ContinuityReadinessTests(unittest.TestCase):
    def evaluate(self, **overrides: object) -> dict[str, object]:
        arguments: dict[str, object] = {
            "common_baseline_acceptance": baseline_acceptance(),
            "preregistration": preregistration(),
            "aa_health_receipt": aa_health(),
            "semantic_status": unavailable_semantic_status(),
        }
        arguments.update(overrides)
        return egri_p5_continuity_readiness(
            rotation_readiness(),
            **arguments,
        )

    def test_tg10_hold_cannot_be_bypassed_by_downstream_receipts(self) -> None:
        result = egri_p5_continuity_readiness(
            rotation_readiness(ready=False),
            common_baseline_acceptance=baseline_acceptance(),
            preregistration=preregistration(),
            aa_health_receipt=aa_health(),
            semantic_status=unavailable_semantic_status(),
        )
        self.assertEqual(result["status"], "HOLD_TG10_MANUAL_CONTINUITY_NOT_READY")
        self.assertFalse(result["authority"]["p5_epoch_opened"])
        self.assertFalse(result["authority"]["assignment_created"])

    def test_common_baseline_acceptance_is_required_before_preregistration(self) -> None:
        result = self.evaluate(common_baseline_acceptance=None)
        self.assertEqual(result["status"], "AWAITING_COMMON_BASELINE_ACCEPTANCE")
        self.assertEqual(result["common_baseline_acceptance"]["status"], "MISSING")

    def test_typed_semantic_unavailability_uses_fallback_and_can_reach_readiness(self) -> None:
        result = self.evaluate()
        self.assertEqual(result["status"], "READY_FOR_EXPLICIT_EGRI_AB_STUDY_OPEN")
        self.assertEqual(
            result["semantic_condition"]["status"],
            "UNAVAILABLE_TYPED_FALLBACK_REQUIRED",
        )
        self.assertTrue(result["semantic_condition"]["semantic_dependency_forbidden"])
        self.assertFalse(result["authority"]["egri_treatment_activated"])
        self.assertFalse(result["authority"]["policy_promoted"])
        self.assertEqual(result["study_contract"]["public_tool_count"], 8)

    def test_preregistration_cannot_require_semantic_or_create_authority(self) -> None:
        invalid = preregistration()
        invalid["treatment_requires_semantic_localization"] = True
        invalid["workspace_evidence_index_is_authority"] = True
        invalid["public_tool_count"] = 9
        result = self.evaluate(preregistration=invalid)
        self.assertEqual(result["status"], "INVALID_PROSPECTIVE_EGRI_PREREGISTRATION")
        reasons = result["preregistration"]["reason_codes"]
        self.assertIn("treatment_requires_semantic_localization_must_be_false", reasons)
        self.assertIn("workspace_evidence_index_is_authority_must_be_false", reasons)
        self.assertIn("public_tool_count_must_remain_8", reasons)

    def test_available_semantic_provider_needs_exact_current_source_fence(self) -> None:
        semantic = {
            "schema_version": SEMANTIC_LOCALIZATION_SCHEMA_VERSION,
            "available": True,
            "provider": "fixture-provider",
            "read_only": True,
        }
        result = self.evaluate(semantic_status=semantic)
        self.assertEqual(result["status"], "HOLD_SEMANTIC_CAPABILITY_CONTRACT_NOT_PROVEN")
        self.assertEqual(result["semantic_condition"]["status"], "AVAILABLE_BUT_UNPROVEN")

    def test_synthetic_or_mismatched_aa_receipt_does_not_enable_ab(self) -> None:
        invalid = aa_health()
        invalid["synthetic_or_fixture_evidence"] = True
        invalid["common_baseline_fingerprint"] = "e" * 64
        result = self.evaluate(aa_health_receipt=invalid)
        self.assertEqual(result["status"], "HOLD_AA_INSTRUMENTATION_HEALTH_NOT_PROVEN")
        self.assertFalse(result["aa_instrumentation_health"]["baseline_fingerprint_matches"])
        self.assertIn(
            "aa_synthetic_or_fixture_evidence_must_be_false",
            result["aa_instrumentation_health"]["reason_codes"],
        )


if __name__ == "__main__":
    unittest.main()
