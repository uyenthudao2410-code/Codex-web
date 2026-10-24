"""Origin-gated default provenance stamp (P2 effectiveness).

The default "representative" stamp fires only when a server-owned
host-turn claim positively establishes an organic origin. It never fires
from the workflow label alone, never overwrites an explicit provenance,
and never fires for known system callers (CP approved-patch bridge).
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from coding_tools_mcp.server import Runtime
from coding_tools_mcp.workflow_tools import AgentWorkflowMixin


def _stage_pending_host_turn(root: Path, *, staged_at_ms: int | None = None) -> None:
    directory = root / ".coding-tools" / "evaluation"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "chatweb-host-turn-pending.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "turn_id": "turn-test-1",
                "trace_id": "a" * 32,
                "staged_at_unix_ms": (
                    int(time.time() * 1000) if staged_at_ms is None else staged_at_ms
                ),
            }
        ),
        encoding="utf-8",
    )


def _run_metadata(runtime: Runtime, run_id: str) -> dict:
    record = runtime.orchestration_ledger.get_run(run_id)
    assert record is not None
    return record["metadata"]


class ProvenanceOriginStampTests(unittest.TestCase):
    def _prepare(self, root: Path, args: dict) -> dict:
        runtime = Runtime(root, permission_mode="dangerous")
        try:
            out = runtime.agent_workflow(args)
            return _run_metadata(runtime, out["orchestration"]["run_id"])
        finally:
            runtime.close()

    def test_host_turn_claim_stamps_custom_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            _stage_pending_host_turn(root)
            metadata = self._prepare(
                root,
                {
                    "workflow": "custom",
                    "phase": "prepare",
                    "objective": "do a small thing",
                    "queries": ["x"],
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertEqual(evaluation.get("provenance"), "representative")
        self.assertEqual(metadata.get("provenance_source"), "runtime_default_organic_v1")
        self.assertEqual(evaluation.get("task_class"), "custom")

    def test_no_claim_no_stamp_even_for_feature_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            metadata = self._prepare(
                root,
                {
                    "workflow": "feature",
                    "phase": "prepare",
                    "objective": "do a small thing",
                    "queries": ["x"],
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertIsNone(evaluation.get("provenance"))
        self.assertIsNone(metadata.get("provenance_source"))

    def test_explicit_provenance_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            _stage_pending_host_turn(root)
            metadata = self._prepare(
                root,
                {
                    "workflow": "custom",
                    "phase": "prepare",
                    "objective": "do a small thing",
                    "queries": ["x"],
                    "evaluation": {"provenance": "synthetic"},
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertEqual(evaluation.get("provenance"), "synthetic")
        self.assertIsNone(metadata.get("provenance_source"))

    def test_bridge_signature_never_stamped_even_with_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            _stage_pending_host_turn(root)
            metadata = self._prepare(
                root,
                {
                    "workflow": "custom",
                    "phase": "prepare",
                    "objective": "Apply one owner-approved exact local patch.",
                    "queries": ["x"],
                    "execution_mode": "mcp_only",
                    "execution_route": "deterministic",
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertIsNone(evaluation.get("provenance"))
        self.assertIsNone(metadata.get("provenance_source"))

    def test_expired_pending_turn_no_stamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            root = Path(temp)
            _stage_pending_host_turn(root, staged_at_ms=1)
            metadata = self._prepare(
                root,
                {
                    "workflow": "custom",
                    "phase": "prepare",
                    "objective": "do a small thing",
                    "queries": ["x"],
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertIsNone(evaluation.get("provenance"))
        self.assertIsNone(metadata.get("provenance_source"))

    def test_attested_transport_turn_stamps(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ), patch.object(
            AgentWorkflowMixin,
            "_attested_chatweb_transport_turn",
            return_value={"trace_id": "b" * 32, "turn_id": "chatweb-trace:" + "b" * 32},
        ):
            root = Path(temp)
            metadata = self._prepare(
                root,
                {
                    "workflow": "custom",
                    "phase": "prepare",
                    "objective": "do a small thing",
                    "queries": ["x"],
                },
            )
        evaluation = metadata.get("evaluation", {})
        self.assertEqual(evaluation.get("provenance"), "representative")
        self.assertEqual(metadata.get("provenance_source"), "runtime_default_organic_v1")


if __name__ == "__main__":
    unittest.main()
