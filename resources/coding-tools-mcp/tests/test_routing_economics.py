from __future__ import annotations

import unittest

from benchmarks.routing_economics import simulate


class RoutingEconomicsBenchmarkTests(unittest.TestCase):
    def test_scenario_invokes_production_router_and_labels_assumptions(self) -> None:
        payload = simulate()
        self.assertTrue(payload["production_router_invoked"])
        self.assertEqual(payload["evidence_class"], "scenario_simulation_not_production_ab")
        self.assertEqual(payload["task_count"], 100)
        self.assertEqual(
            payload["route_distribution"],
            {"deterministic": 30, "mini": 35, "luna": 20, "sol_xhigh": 15},
        )
        self.assertGreater(payload["strategies"]["all_sol_for_model_tasks"]["credits"], payload["strategies"]["adaptive_router"]["credits"])
        self.assertIn("success_probability", payload["assumptions"])


if __name__ == "__main__":
    unittest.main()
