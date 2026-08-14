from __future__ import annotations

import unittest

from coding_tools_mcp.provider_routing import recommend_shadow_route


class ProviderRoutingTests(unittest.TestCase):
    def test_broad_read_only_prefers_flash_and_hard_reasoning_prefers_pro(self) -> None:
        flash = recommend_shadow_route({
            "side_effect_class": "read_only", "scope": "broad", "risk": "low", "hard_reasoning": False,
        })
        self.assertEqual(flash["recommendation"]["model"], "opencode-go/deepseek-v4-flash")
        self.assertFalse(flash["automatic_dispatch"])
        self.assertFalse(flash["mutation_allowed"])
        pro = recommend_shadow_route({
            "side_effect_class": "read_only", "scope": "broad", "risk": "medium", "hard_reasoning": True,
        })
        self.assertEqual(pro["recommendation"]["model"], "opencode-go/deepseek-v4-pro")

    def test_mutation_and_risk_gates_never_auto_route_opencode(self) -> None:
        deterministic = recommend_shadow_route({
            "side_effect_class": "deterministic_mutation", "scope": "localized", "risk": "low",
        })
        self.assertEqual(deterministic["recommendation"]["route"], "mcp_deterministic")
        risky = recommend_shadow_route({
            "side_effect_class": "read_only", "scope": "broad", "risk": "high",
        })
        self.assertEqual(risky["recommendation"]["route"], "controller_manual")
        consequential = recommend_shadow_route({
            "side_effect_class": "consequential_mutation", "scope": "bounded", "risk": "medium",
        })
        self.assertEqual(consequential["recommendation"]["route"], "controller_manual")

    def test_codex_current_policy_recommendations_are_deterministic(self) -> None:
        mini = recommend_shadow_route({
            "side_effect_class": "proposed_change", "scope": "localized", "ambiguity": "low",
            "evidence_quality": "localized", "risk": "low", "strong_oracle": True,
        })
        self.assertEqual(mini["recommendation"]["route"], "codex_mini")
        luna = recommend_shadow_route({
            "side_effect_class": "proposed_change", "scope": "bounded", "ambiguity": "medium",
            "evidence_quality": "partial", "risk": "medium", "hard_reasoning": False,
        })
        self.assertEqual(luna["recommendation"]["route"], "codex_luna")
        manual = recommend_shadow_route({
            "side_effect_class": "proposed_change", "scope": "broad", "ambiguity": "high",
            "evidence_quality": "sparse", "risk": "medium", "hard_reasoning": True,
        })
        self.assertEqual(manual["recommendation"]["route"], "controller_manual")

    def test_unknown_fields_and_non_boolean_flags_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            recommend_shadow_route({"scope": "broad", "prompt": "must not enter routing evidence"})
        with self.assertRaises(ValueError):
            recommend_shadow_route({"hard_reasoning": "yes"})


if __name__ == "__main__":
    unittest.main()
