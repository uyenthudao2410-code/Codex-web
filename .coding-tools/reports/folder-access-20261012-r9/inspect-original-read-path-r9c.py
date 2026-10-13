"""Offline read-only projection diagnosis; does not replay the MCP action."""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c/win-unpacked/resources/resources/coding-tools-mcp"
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_5e96e41f520d44d99a2b36bf749e658b"
ATTEMPT = "try_df0e7870613c4eee8d1e9ff90b3a4d5b"
RELATIVE = "mcp-access-smoke-20261012-r9c.txt"
AUTOCAD = Path("E:/DEV/Autocad").resolve(strict=True)
sys.path.insert(0, str(PACKAGE))
from coding_tools_mcp.workspace_scope import Workspace
from coding_tools_mcp.file_tools import FileToolsMixin


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


settings = load(PROFILE / "settings.json")
workspace = Workspace(Path(settings["workspace"]), [Path(item) for item in settings["authorizedRoots"]])


class OfflineFileReader(FileToolsMixin):
    def resolve_existing(self, raw_path):
        return workspace.resolve_existing_at(AUTOCAD, raw_path)


native = OfflineFileReader().read_file({"path": RELATIVE, "start_line": 1, "max_lines": 20, "max_bytes": 4096, "encoding": "utf-8"})
assert native["path"] == (AUTOCAD / RELATIVE).as_posix() and native["path"] != RELATIVE
policy = load(PROFILE / "control-plane-file-read-policy.json")
policy_sha256 = hashlib.sha256(json.dumps({key: value for key, value in policy.items() if key != "enabled"},
                                           ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
context_projection = {"action_id": ACTION, "attempt_id": ATTEMPT, "policy_sha256": policy_sha256,
                      "workspace_id": policy["workspace_id"], "workspace_generation": policy["workspace_generation"],
                      "facade_contract": policy["facade_contract"]}
context_id = "cpfr_" + hashlib.sha256(json.dumps(context_projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:56]
registry = load(ROOT / ".coding-tools/orchestration/task-context-workspaces.json")
context = registry["contexts"].get(context_id)
assert isinstance(context, dict) and Path(context["canonical_root"]).resolve(strict=True) == AUTOCAD
journal = load(PROFILE / "control-plane-node.json.file-read-bridge-journal.json")
entry = journal["entries"][f"{ACTION}|{ATTEMPT}"]
assert entry["state"] == "unknown" and entry["receipt"]["payload"]["diagnostic_code"] == "CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID"
report = {"schema_version": 1, "operation": "offline_original_read_path_diagnosis", "observed_at_ms": int(time.time() * 1000),
          "action_id": ACTION, "attempt_id": ATTEMPT,
          "original_diagnostic_code": entry["receipt"]["payload"]["diagnostic_code"],
          "source_sha256": {name: sha(PACKAGE / f"coding_tools_mcp/{name}.py") for name in ["workspace_scope", "file_tools", "fs_utils"]},
          "expected_local_task_context_id": context_id, "persisted_context": context,
          "scope": {"primary_workspace": str(workspace.root), "authorized_roots": [str(root) for root in workspace.authorized_roots]},
          "projection": {"native_path": native["path"], "admission_path": RELATIVE, "path_matches": False,
                         "content_sha256": hashlib.sha256(native["content"].encode()).hexdigest(),
                         "bytes_read": native["bytes_read"], "total_bytes": native["total_bytes"],
                         "start_line": native["start_line"], "end_line": native["end_line"], "total_lines": native["total_lines"]},
          "diagnosis": "read_file resolves against the bound Autocad root but returns display relative to the primary Codex root; bridge rejects its absolute path before relay.",
          "limits": {"offline_current_projection_not_retained_original_response": True,
                     "original_action_replayed": False, "receipt_posted": False, "runtime_modified": False}}
report_path = HERE / f"original-read-path-diagnosis-r9c-{report['observed_at_ms']}.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report_path": str(report_path), "report_sha256": sha(report_path), **report}, separators=(",", ":")))
