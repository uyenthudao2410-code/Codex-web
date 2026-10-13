"""Retrospective, read-only causal corroboration; no native action or receipt POST."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9b/win-unpacked/resources/resources/coding-tools-mcp"
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


spec = importlib.util.spec_from_file_location("guarded_reconcile_helper", HERE / "reconcile-original-create-pre-effect.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
helper.validate()  # Only local preflight; no credential decryption or POST.
metadata_path = HERE / "canary/original-create-context-metadata-read-only-2.json"
assert sha(metadata_path) == "f4758b1ca2ea7b9578af7ed737650fa5a1109a89cfd211a9523e0fc70b6b2b65"
metadata = load(metadata_path)["metadata"]
assert metadata["task_id"] == "task_09461f4e2d3b4992811812e816a6edbc" and metadata["writer_lease_generation"] == 1
policy_path = PROFILE / "control-plane-approved-patch-policy.json"
assert sha(policy_path) == "f5dd13bcc2689e490bce54c7c071605d8393a1ff3daafb2c990c25748c7184e9"
policy = load(policy_path)
policy_projection = {key: value for key, value in policy.items() if key != "enabled"}
policy_sha256 = hashlib.sha256(json.dumps(policy_projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
assert policy_sha256 == "b86758a26dc93540d9f13211d0f244df9fc51f6798eb8d25d0d937154c0882b6"
context_projection = {"action_id": helper.ACTION, "attempt_id": helper.ATTEMPT,
                      "policy_sha256": policy_sha256,
                      "workspace_id": policy["workspace_id"], "workspace_generation": policy["workspace_generation"],
                      **metadata}
context_id = "cpdw_" + hashlib.sha256(json.dumps(context_projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:56]
registry_path = ROOT / ".coding-tools/orchestration/task-context-workspaces.json"
registry = load(registry_path)
contexts = registry["contexts"]
assert context_id not in contexts and context_id not in registry.get("legacy_contexts", {})
autocad = Path("E:/DEV/Autocad").resolve(strict=True)
assert not any(Path(value["canonical_root"]).resolve(strict=False) == autocad for value in contexts.values())
registry_source = PACKAGE / "coding_tools_mcp/workspace_context_registry.py"
server_source = PACKAGE / "coding_tools_mcp/server.py"
server_text = server_source.read_text(encoding="utf-8")
registry_text = registry_source.read_text(encoding="utf-8")
identity = server_text[server_text.index("    def _workspace_identity_for_request("):server_text.index("    @staticmethod", server_text.index("    def _workspace_identity_for_request("))]
assert identity.index("self._bind_task_context_workspace(") < identity.index("return resolved, scope_root, identity")
bind = server_text[server_text.index("    def _bind_task_context_workspace("):server_text.index("    def _bound_task_context_workspace(")]
assert bind.index("self.workspace_context_registry.bind(") < bind.index("self._task_context_workspace_ids[scope] = target")
registry_bind = registry_text[registry_text.index("    def bind("):registry_text.index("    def _load(")]
assert registry_bind.index("self._write_locked()") < registry_bind.index("return dict(entry)")
assert "os.fsync(handle.fileno())" in registry_text and "os.replace(temporary, self.path)" in registry_text
assert not any(marker in registry_text for marker in ["self._contexts.clear(", "self._contexts.pop(", "del self._contexts["])
set_roots = server_text[server_text.index("    def set_authorized_roots("):server_text.index("    def switch_workspace(")]
assert "workspace_context_registry" not in set_roots
settings_time = (PROFILE / "settings.json").stat().st_mtime_ns
assert settings_time < 1791793892868499500
report = {
    "schema_version": 1, "operation": "original_create_causal_corroboration", "observed_at_ms": int(time.time() * 1000),
    "action_id": helper.ACTION, "attempt_id": helper.ATTEMPT,
    "source_sha256": {"server": sha(server_source), "registry": sha(registry_source), "packaged_app": helper.PINNED[helper.BASE / "app.asar"]},
    "metadata_receipt_sha256": sha(metadata_path), "policy_sha256": policy_sha256,
    "expected_local_task_context_id": context_id,
    "registry_snapshot_sha256": sha(registry_path), "registry_schema_version": registry["schema_version"],
    "expected_context_present": False, "autocad_context_count": 0, "registry_context_count": len(contexts),
    "settings_last_write_unix_ns": settings_time, "settings_predates_original_runtime_start": True,
    "packaged_persistence_order": ["workspace_context scope resolution", "bind exact opaque task context",
                                  "registry write, flush, fsync, atomic replace", "bootstrap returns exact workspace",
                                  "bridge checks returned workspace", "bridge dispatches document_workflow"],
    "registry_context_delete_or_eviction_method_present": False,
    "authorized_roots_update_replaces_registry": False,
    "autocad_evidence_tree_exists": False, "original_target_exists": False,
    "inference": "Successful ordinary Autocad bootstrap would leave the exact durable context. Its absence corroborates that the bridge did not dispatch document_workflow.",
    "limits": {"retained_original_native_error": False, "retrospective_corroboration": True,
               "assumes_no_external_registry_or_target_deletion": True, "proves_original_error_code": False,
               "reconciliation_posted": False, "original_action_replayed": False},
}
report_path = HERE / f"original-create-causal-corroboration-r9b-{report['observed_at_ms']}.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report_path": str(report_path), "report_sha256": sha(report_path), **report}, separators=(",", ":")))
