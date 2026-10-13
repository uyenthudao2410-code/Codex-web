"""Exact policy selection and independent workspace admission regressions."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

from control_plane import node_agent as agent
from control_plane import workspace_policy_store as store
from tests import test_exec_node_agent as exec_fixtures


class WorkspacePolicyStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workspace-policy-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "control-plane-exec-policy.json"

    def policy(self, index):
        return {"workspace_id": f"workspace-policy-{index:04}",
                "workspace_generation": f"generation-policy-{index:04}",
                "enabled": True, "native_argv_prefixes": [["node", f"trusted-{index}.js"]]}

    def write(self, policy, replace=False):
        store.write_policy(self.path, policy, replace=replace, atomic_writer=agent._write_json_atomic)

    def test_concurrent_install_preserves_both_scopes_and_exact_replacement(self):
        barrier = threading.Barrier(2)
        policies = [self.policy(1), self.policy(2)]

        def install(policy):
            barrier.wait(timeout=3)
            self.write(policy)

        with ThreadPoolExecutor(max_workers=2) as workers:
            list(workers.map(install, policies))
        self.assertEqual(len(store.read_entries(self.path)), 2)
        for policy in policies:
            self.assertEqual(store.read_selected(self.path, policy), policy)
        changed = {**policies[0], "enabled": False}
        self.write(changed, replace=True)
        self.assertEqual(store.read_selected(self.path, policies[0]), changed)
        self.assertEqual(store.read_selected(self.path, policies[1]), policies[1])
        self.assertFalse(self.path.with_name(self.path.name + ".install.lock").exists())

    def test_singleton_compatibility_and_no_implicit_selection_or_stale_generation(self):
        first = self.policy(1)
        self.write(first)
        self.assertEqual(json.loads(self.path.read_text()), first)
        self.assertEqual(store.read_selected(self.path), first)
        self.write(self.policy(2))
        with self.assertRaisesRegex(RuntimeError, "TARGET_REQUIRED"):
            store.read_selected(self.path)
        with self.assertRaisesRegex(RuntimeError, "TARGET_NOT_FOUND"):
            store.read_selected(self.path, {**first, "workspace_generation": "generation-retired-0001"})
        with self.assertRaisesRegex(RuntimeError, "COLLECTION_INVALID"):
            store.select({"schema_version": 1, "policies": [first, first]}, first)

    def test_connected_loop_polls_both_scopes_without_mutating_original_args(self):
        for policy in (self.policy(1), self.policy(2)):
            self.write(policy)
        args = argparse.Namespace(data_root=self.temp.name, runtime_mode="development")
        visited = []
        with mock.patch.object(agent, "runtime_heartbeat"), mock.patch.object(agent, "_connected_agent_lane_admission"), \
                mock.patch.object(agent, "poll_file_read_once"), mock.patch.object(agent, "poll_artifact_once"), \
                mock.patch.object(agent, "poll_approved_patch_once"), mock.patch.object(agent, "poll_document_write_once"), \
                mock.patch.object(agent, "poll_exec_once", side_effect=lambda current: visited.append(agent._targeted_poll(current, {"lane": "bounded_exec", "limit": 1}))):
            agent._connected_agent_iteration(args)
        self.assertEqual(len(visited), 2)
        self.assertEqual({item["workspace_id"] for item in visited}, {"workspace-policy-0001", "workspace-policy-0002"})
        self.assertFalse(hasattr(args, "workspace_id"))

    def test_resume_running_job_uses_only_its_exact_scope(self):
        first, second = self.policy(1), self.policy(2)
        args = argparse.Namespace(**first)
        journal = {"entries": {"first": {"state": "running", "action_id": "action-first", "request": first},
                               "second": {"state": "running", "action_id": "action-second", "request": second}}}
        with mock.patch.object(agent, "_control_bridge_observation", return_value=("running", 0)) as observe:
            result, count = agent._resume_running_exec_entries(args, config_path=self.path, config={},
                journal_path=self.path, journal=journal, project_root=self.path.parent)
        self.assertEqual(count, 0)
        self.assertEqual(result["running"], ["action-first"])
        self.assertEqual(observe.call_args.kwargs["entry"]["action_id"], "action-first")


class IsolatedNodeAgentCliTests(unittest.TestCase):
    def test_direct_isolated_launcher_loads_owned_sibling_without_adapter_mutation(self):
        with tempfile.TemporaryDirectory(prefix="isolated-node-agent-") as temporary:
            root = Path(temporary)
            adapter = root / "adapter"
            adapter.mkdir()
            for source in (Path(agent.__file__), Path(store.__file__)):
                shutil.copyfile(source, adapter / source.name)
            # An unrelated working-directory module must never be imported.
            (root / "workspace_policy_store.py").write_text("raise RuntimeError('wrong module')\n", encoding="utf-8")
            data = root / "data"
            data.mkdir()
            first = exec_fixtures._policy()
            second = {**first, "workspace_id": "workspace-exec-0002", "workspace_generation": "generation-exec-0002"}
            (data / "control-plane-exec-policy.json").write_text(
                json.dumps({"schema_version": 1, "policies": [first, second]}), encoding="utf-8")

            def adapter_tree():
                return {str(path.relative_to(adapter)): path.read_bytes() if path.is_file() else None
                        for path in adapter.rglob("*")}

            before = adapter_tree()
            environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            command = [sys.executable, "-I", str(adapter / "node_agent.py")]
            help_result = subprocess.run([*command, "--help"], cwd=root, env=environment,
                                         capture_output=True, text=True, timeout=15)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("inspect-exec-policy", help_result.stdout)
            for policy in (first, second):
                result = subprocess.run([*command, "inspect-exec-policy", "--data-root", str(data),
                    "--workspace-id", policy["workspace_id"], "--workspace-generation", policy["workspace_generation"]],
                    cwd=root, env=environment, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt["workspace_id"], policy["workspace_id"])
                self.assertEqual(receipt["state"], "enabled")
                self.assertEqual(receipt["policy_sha256"], agent._policy_digest(policy))
            self.assertEqual(adapter_tree(), before, "isolated CLI must not write bytecode or mutate adapter files")


class WorkspaceExecAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = exec_fixtures.ExecNodeReceiptTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_native_script_approval_and_disabling_do_not_cross_workspaces(self):
        item = self.fixture
        first = item.policy(allowed_argv_prefixes=[["node", "--version"], ["node", "trusted.js"]],
                            native_argv_prefixes=[["node", "trusted.js"]], execution_mode="native_only")
        second = {**first, "workspace_id": "workspace-exec-0002", "workspace_generation": "generation-exec-0002",
                  "allowed_argv_prefixes": [["node", "--version"]], "native_argv_prefixes": []}
        registry = json.loads(item.registry_path.read_text())
        next_root = item.root / "second-workspace"
        next_root.mkdir()
        registry["entries"].append({**registry["entries"][0], "workspace_id": second["workspace_id"],
                                   "workspace_generation": second["workspace_generation"], "canonical_path": str(next_root)})
        agent._write_json_atomic(item.registry_path, registry)
        path = item.data_root / "control-plane-exec-policy.json"
        agent._write_local_policy(path, first, replace=False)
        agent._write_local_policy(path, second, replace=False)
        observation = agent._standing_policy_observation(item.args(), item.config)
        admitted = [{"lane": "exec", "policy_sha256": agent._policy_digest(agent._read_exec_policy(path, target=policy)),
                     "workspace_id": policy["workspace_id"], "workspace_generation": policy["workspace_generation"]}
                    for policy in (first, second)]
        expected = agent.hashlib.sha256(json.dumps(sorted(admitted, key=lambda entry: (entry["lane"], entry["workspace_id"],
                     entry["workspace_generation"])), separators=(",", ":"), sort_keys=True).encode()).hexdigest()
        self.assertEqual(observation["state"], "enabled")
        self.assertEqual(observation["policy_sha256"], expected, "heartbeat must attest both current workspace policies")
        request = agent._exec_bridge_request(item.action(), item.config)
        request.update({"argv": ["node", "trusted.js"], "cwd": ""})
        admitted = agent._admit_exec_policy_request(item.args(), config_path=item.config_path, config=item.config, request=request)
        self.assertEqual(admitted["native_argv_prefixes"], [["node", "trusted.js"]])
        with self.assertRaisesRegex(RuntimeError, "ALLOWLIST_DENIED"):
            agent._admit_exec_policy_request(item.args(), config_path=item.config_path, config=item.config,
                request={**request, "workspace_id": second["workspace_id"], "workspace_generation": second["workspace_generation"]})
        agent._write_local_policy(path, {**first, "enabled": False}, replace=True)
        with self.assertRaisesRegex(RuntimeError, "EXEC_DISABLED"):
            agent._admit_exec_policy_request(item.args(), config_path=item.config_path, config=item.config, request=request)
        version_request = {**request, "argv": ["node", "--version"], "workspace_id": second["workspace_id"], "workspace_generation": second["workspace_generation"]}
        self.assertEqual(agent._admit_exec_policy_request(item.args(), config_path=item.config_path, config=item.config,
                                                        request=version_request)["native_argv_prefixes"], [])
        with self.assertRaisesRegex(RuntimeError, "POLICY_CONFIG_MISMATCH"):
            agent._admit_exec_policy_request(item.args(), config_path=item.config_path, config=item.config,
                                            request={**version_request, "workspace_generation": "generation-exec-retired"})


if __name__ == "__main__":
    unittest.main()
