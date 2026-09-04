from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas


class CommittedReviewTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout.strip()

    def _repository(self, root: Path) -> tuple[str, str]:
        self._git(root, "init")
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        self._git(root, "add", "app.py")
        self._git(root, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "base")
        base = self._git(root, "rev-parse", "HEAD")
        changed = [
            "VALUE = 2\n",
            "API_KEY=actual-secret-value\n",
            'CLIENT_SECRET = "quoted-secret-value"\n',
            "Authorization: Bearer another-secret\n",
            "-----BEGIN PRIVATE KEY-----\n",
            "private-key-body\n",
            "-----END PRIVATE KEY-----\n",
        ]
        changed.extend(f"LINE_{index:04d} = {index}\n" for index in range(500))
        (root / "app.py").write_text("".join(changed), encoding="utf-8")
        self._git(root, "add", "app.py")
        self._git(root, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "review target")
        return base, self._git(root, "rev-parse", "HEAD")

    def test_agent_workflow_committed_review_is_immutable_bounded_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, head = self._repository(root)
            (root / "uncommitted.txt").write_text("current-only-change\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                review_args = {
                    "base_commit": base,
                    "head_commit": head,
                    "paths": ["app.py"],
                    "max_bytes": 1024,
                    "max_lines": 1000,
                }
                first = runtime.agent_workflow({"workflow": "diagnose", "phase": "prepare", "committed_review": review_args})
                result = first["committed_review"]
                self.assertTrue(result["deterministic"])
                self.assertFalse(result["llm_summary"])
                self.assertEqual(result["range"]["base_commit"], base)
                self.assertEqual(result["range"]["head_commit"], head)
                self.assertEqual(result["range"]["effective_base_commit"], base)
                self.assertTrue(result["result_tail"]["truncated"])
                handoff = result["large_result_handoff"]
                self.assertEqual(handoff["kind"], "DIFF_PAGE")
                self.assertEqual(
                    handoff["source_identity"]["source_sha256"],
                    result["integrity"]["source_diff_sha256"],
                )
                self.assertEqual(handoff["continuation"], result["continuation"])
                self.assertTrue(handoff["has_more"])
                self.assertTrue(
                    handoff["recoverability"][
                        "continuation_recovers_all_omitted_data"
                    ]
                )
                next_operation = handoff["next_operation"]
                self.assertEqual(next_operation["tool"], "agent_workflow")
                self.assertEqual(
                    next_operation["arguments"]["committed_review"]["continuation"],
                    result["continuation"],
                )
                self.assertIn("sensitive values redacted from diff output", result["warnings"])
                self.assertNotIn("actual-secret-value", result["diff"])
                self.assertNotIn("quoted-secret-value", result["diff"])
                self.assertNotIn("another-secret", result["diff"])
                self.assertNotIn("private-key-body", result["diff"])
                self.assertNotIn("current-only-change", result["diff"])
                self.assertGreater(result["integrity"]["redaction_count"], 0)
                self.assertNotEqual(
                    result["integrity"]["source_diff_sha256"], result["integrity"]["presented_diff_sha256"]
                )

                pages = [result["diff"]]
                token = result["continuation"]
                while token:
                    next_args = {**review_args, "continuation": token}
                    page = runtime.agent_workflow({"workflow": "diagnose", "phase": "prepare", "committed_review": next_args})
                    review = page["committed_review"]
                    pages.append(review["diff"])
                    token = review["continuation"]
                full = runtime.agent_workflow({
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "committed_review": {**review_args, "max_bytes": 262144},
                })["committed_review"]
                self.assertEqual("".join(pages), full["diff"])
                self.assertEqual(full["summary"]["file_count"], 1)
                self.assertEqual(full["files"][0]["path"], "app.py")
                self.assertNotIn("large_result_handoff", full)
            finally:
                runtime.close()

    def test_committed_review_rejects_aliases_missing_history_and_mutation_phases(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, head = self._repository(root)
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                with self.assertRaises(ToolFailure) as alias_error:
                    runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "committed_review": {"base_commit": "HEAD", "head_commit": head},
                    })
                self.assertEqual(alias_error.exception.code, "COMMITTED_REVIEW_COMMIT_INVALID")
                with self.assertRaises(ToolFailure) as missing_error:
                    runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "committed_review": {"base_commit": "0" * 40, "head_commit": head},
                    })
                self.assertEqual(missing_error.exception.code, "COMMITTED_REVIEW_COMMIT_MISSING")
                with self.assertRaises(ToolFailure) as phase_error:
                    runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "run",
                        "committed_review": {"base_commit": base, "head_commit": head},
                    })
                self.assertEqual(phase_error.exception.code, "COMMITTED_REVIEW_PHASE_INVALID")
            finally:
                runtime.close()

    def test_committed_review_stays_inside_agent_workflow_schema(self) -> None:
        schemas = input_schemas()
        self.assertIn("committed_review", schemas["agent_workflow"]["properties"])
        self.assertNotIn("committed_review", schemas)
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                self.assertNotIn(
                    "committed_review",
                    {tool["name"] for tool in runtime._tools_list_payload["tools"]},
                )
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
