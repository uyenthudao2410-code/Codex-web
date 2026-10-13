"""Read-only diagnosis; does not call MCP or settle/replay the original action."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace


REPOSITORY = Path(__file__).resolve().parents[3]
PACKAGE = REPOSITORY / "dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9b/win-unpacked/resources/resources/coding-tools-mcp"
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_ed8982433bf347ef8c32aebc17b23d43"
ATTEMPT = "try_79756ada1f5c45c389f4c133ecb55c95"
AUTOCAD = Path("E:/DEV/Autocad")
TARGET = AUTOCAD / "mcp-access-smoke-20261012-r9.txt"

sys.dont_write_bytecode = True
sys.path.insert(0, str(PACKAGE))
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.workspace_scope import Workspace


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


settings = json.loads((PROFILE / "settings.json").read_text(encoding="utf-8-sig"))
primary = Path(settings["workspace"])
roots = [Path(item) for item in settings.get("authorizedRoots", [])]
workspace = Workspace(primary, authorized_roots=roots)

# Compile only the exact packaged Runtime scope guard. Runtime.__init__ and
# tool dispatch are deliberately excluded: they may create task/ledger state.
server_path = PACKAGE / "coding_tools_mcp/server.py"
tree = ast.parse(server_path.read_text(encoding="utf-8"))
runtime_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Runtime")
scope_method = next(node for node in runtime_class.body if isinstance(node, ast.FunctionDef) and node.name == "_resolve_authorized_execution_scope")
namespace = {"ToolFailure": ToolFailure, "ResolvedPath": object}
exec(compile(ast.Module(body=[scope_method], type_ignores=[]), str(server_path), "exec"), namespace)
offline = SimpleNamespace(workspace=workspace, resolve_existing=workspace.resolve_existing)
try:
    namespace["_resolve_authorized_execution_scope"](offline, str(AUTOCAD), field="path")
    scope_result = {"allowed": True}
except ToolFailure as error:
    scope_result = {"allowed": False, "code": error.code, "category": error.category,
                    "retryable": error.retryable, "details": error.details}

journal_path = PROFILE / "control-plane-node.json.document-write-bridge-journal.json"
journal = json.loads(journal_path.read_text(encoding="utf-8-sig"))
entries = [entry for entry in journal.get("entries", {}).values()
           if isinstance(entry, dict) and entry.get("action_id") == ACTION and entry.get("attempt_id") == ATTEMPT]
assert len(entries) == 1
entry = entries[0]
receipt = entry.get("receipt", {})
payload = receipt.get("payload", {})
registry_path = primary / ".coding-tools/orchestration/task-context-workspaces.json"
registry = json.loads(registry_path.read_text(encoding="utf-8-sig")) if registry_path.exists() else {}
contexts = registry.get("contexts", {})
autocad_contexts = [context for context, value in contexts.items()
                   if isinstance(value, dict) and Path(str(value.get("canonical_root", "."))).resolve(strict=False) == AUTOCAD.resolve(strict=False)]
result = {
    "schema_version": 1,
    "operation": "offline_original_create_scope_diagnosis",
    "observed_at_ms": int(time.time() * 1000),
    "action_id": ACTION, "attempt_id": ATTEMPT,
    "runtime_config": {"primary_workspace": str(workspace.root), "authorized_roots": [str(root) for root in roots]},
    "packaged_scope_guard": {"server_sha256": sha(server_path), "workspace_scope_sha256": sha(PACKAGE / "coding_tools_mcp/workspace_scope.py"), "result": scope_result},
    "original_local_journal": {"state": entry.get("state"), "receipt_state": receipt.get("receipt_state"),
                               "receipt_submitted": receipt.get("receipt_submitted"), "local_handle_present": bool(receipt.get("local_handle")),
                               "code": payload.get("code"), "diagnostic_code": payload.get("diagnostic_code"),
                               "reconciliation_required": payload.get("reconciliation_required"),
                               "native_original_error_retained": False},
    "filesystem_observation": {"target_exists": TARGET.exists(), "autocad_evidence_tree_exists": (AUTOCAD / ".coding-tools").exists()},
    "task_context_registry": {"context_count": len(contexts), "autocad_context_count": len(autocad_contexts)},
    "proof_limits": {"is_original_native_receipt": False, "proves_original_no_effect": False,
                     "supports_current_root_authorization_mismatch": scope_result.get("allowed") is False,
                     "native_tool_not_dispatched_by_this_observer": True,
                     "action_replayed_or_settled": False,
                     "runtime_or_journal_modified": False},
}
report = Path(__file__).with_name(f"original-create-scope-diagnosis-r9b-{result['observed_at_ms']}.json")
report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report_path": str(report), **result}, separators=(",", ":")))
