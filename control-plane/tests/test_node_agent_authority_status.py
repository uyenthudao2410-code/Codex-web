from __future__ import annotations

import unittest

from control_plane.node_agent import _authority_status_projection


class NodeAgentAuthorityStatusTests(unittest.TestCase):
    def test_projection_accepts_enriched_target_identity(self) -> None:
        device_id = "4c4b7a5b-7744-49ae-a490-78a528a00471"
        response = {
            "device_id": device_id,
            "state": "active",
            "node_display_name": "DESKTOP-63643J4",
            "workspace_count": 1,
            "target_count": 1,
            "dispatchable_target_count": 1,
            "targets": [{
                "node_display_name": "DESKTOP-63643J4",
                "workspace_display_name": "Codex-web",
                "workspace_id": "workspace_f93b5bac9dc74fae9cea66f44c4ebc94",
                "workspace_generation": "generation_a91d1829c5bf4c7093a30cec14105c76",
                "capabilities": {"read": True, "write": False, "exec": False},
                "binding_state": "active",
                "workspace_state": "active",
                "presence_state": "online",
                "readiness": "degraded",
                "policy_state": "enabled",
                "dispatch_state": "dispatchable",
                "dispatch_blockers": [],
            }],
            "observed_at_ms": 1_790_079_200_424,
        }

        projection = _authority_status_projection(response, config={"device_id": device_id})

        self.assertEqual(projection["state"], "active")
        self.assertEqual(projection["target_count"], 1)
        self.assertEqual(
            projection["targets"][0]["workspace_generation"],
            "generation_a91d1829c5bf4c7093a30cec14105c76",
        )


if __name__ == "__main__":
    unittest.main()
