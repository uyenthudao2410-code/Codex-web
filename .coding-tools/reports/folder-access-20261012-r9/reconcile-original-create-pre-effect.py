"""Guarded additive reconciliation of one original attempt; no effect replay.

Default is local preflight only. --confirm-reconcile permits one authenticated
receipt POST, backed by explicitly labelled offline/operator inference rather
than a retained native rejection response. It never edits a node journal.
"""
from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9b/win-unpacked/resources"
PACKAGE = BASE / "resources/coding-tools-mcp"
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_ed8982433bf347ef8c32aebc17b23d43"
ATTEMPT = "try_79756ada1f5c45c389f4c133ecb55c95"
DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
SERVER = "https://svhome.tail0e4032.ts.net"
AUTOCAD = Path("E:/DEV/Autocad").resolve(strict=True)
PRIMARY = ROOT.resolve(strict=True)
REPORT = Path(__file__).with_name("original-create-scope-diagnosis-r9b-1791794423244.json")
CAUSAL_REPORT = Path(__file__).with_name("original-create-causal-corroboration-r9b-1791795026355.json")
CONTEXT_METADATA = Path(__file__).with_name("canary") / "original-create-context-metadata-read-only-2.json"
APPROVED_POLICY = PROFILE / "control-plane-approved-patch-policy.json"
EXPECTED_CONTEXT = "cpdw_0aa500396f46f2b950b6006ac62bf136f065dd7f4be90bd38e0f95e5"
JOURNAL = PROFILE / "control-plane-node.json.document-write-bridge-journal.json"
SETTINGS = PROFILE / "settings.json"
PINNED = {
    REPORT: "71e0279ac77797ee18b5172fa43469cefc6990e909bfc9211396de62bd195d48",
    CAUSAL_REPORT: "d3a89464cc5a9affdd2789d3366022870dd60acf56baf13ba288be77461c1bfe",
    CONTEXT_METADATA: "f4758b1ca2ea7b9578af7ed737650fa5a1109a89cfd211a9523e0fc70b6b2b65",
    APPROVED_POLICY: "f5dd13bcc2689e490bce54c7c071605d8393a1ff3daafb2c990c25748c7184e9",
    JOURNAL: "61a1af71b949a03aa0e77cb9eae1be2cd942fbaeebffaa57a1d47bc8dfcc3ae1",
    SETTINGS: "c4d7e203953f69ab41c4039d6d611dd331f919f272ca25cbfbeedfe49cfe4011",
    BASE / "app.asar": "a9a8c2007c12ecf7654f3eb38ae44a82df0a7c69888189090b517be361bc16fe",
    PACKAGE / "coding_tools_mcp/server.py": "808a6dc888f6812cf30ae805e29d7f0abdd340d0ef9c91c534e05e451acf7aa9",
    PACKAGE / "coding_tools_mcp/workspace_scope.py": "40b8f32ff1d961735b0b6d3d04f623871b12bea0ef354d84c9407077a2dd2f1b",
    PACKAGE / "coding_tools_mcp/workspace_context_registry.py": "e9d34f604ed17b39dea657bc8a1ee40ed88b24f80da6c95fc8101ca36527c4b5",
    BASE / "resources/control-plane/node_agent.py": "b2cf0f1c141cd19043965aa0a111715a4142e09719c13b4e540b8f4c4c597bc0",
}


def require(condition: object, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), "RECONCILE_JSON_SCHEMA_MISMATCH")
    return value


def validate() -> dict:
    for path, expected in PINNED.items():
        require(sha(path) == expected, "RECONCILE_PINNED_EVIDENCE_CHANGED")
    settings = load(SETTINGS)
    require(Path(settings.get("workspace", "")).resolve(strict=True) == PRIMARY
            and settings.get("authorizedRoots") == [], "RECONCILE_NATIVE_ROOTS_CHANGED")
    require(SETTINGS.stat().st_mtime_ns == 1790160650015643800,
            "RECONCILE_SETTINGS_WRITE_HISTORY_CHANGED")
    causal = load(CAUSAL_REPORT)
    require(causal.get("action_id") == ACTION and causal.get("attempt_id") == ATTEMPT
            and causal.get("expected_local_task_context_id") == EXPECTED_CONTEXT
            and causal.get("expected_context_present") is False
            and causal.get("autocad_context_count") == 0
            and causal.get("settings_predates_original_runtime_start") is True
            and causal.get("registry_context_delete_or_eviction_method_present") is False
            and causal.get("authorized_roots_update_replaces_registry") is False
            and causal.get("limits", {}).get("retained_original_native_error") is False
            and causal.get("limits", {}).get("retrospective_corroboration") is True,
            "RECONCILE_CAUSAL_EVIDENCE_SCHEMA_MISMATCH")
    metadata = load(CONTEXT_METADATA)
    require(metadata.get("read_only") is True and metadata.get("action_id") == ACTION,
            "RECONCILE_ORIGINAL_CONTEXT_METADATA_MISMATCH")
    projection = {"action_id": ACTION, "attempt_id": ATTEMPT, "policy_sha256": causal["policy_sha256"],
                  "workspace_id": "workspace_bc86004be2684b958ab7a9a6f9530cd7",
                  "workspace_generation": "generation_03f9c04f1b14414fa4bfa7d91cc8ea7a",
                  **metadata["metadata"]}
    derived_context = "cpdw_" + hashlib.sha256(json.dumps(projection, ensure_ascii=False, sort_keys=True,
                                                          separators=(",", ":")).encode()).hexdigest()[:56]
    require(derived_context == EXPECTED_CONTEXT, "RECONCILE_DERIVED_ORIGINAL_CONTEXT_MISMATCH")
    state = load(PROFILE / "runtime-state.json")
    require(state.get("nativePid") == 2404
            and state.get("nativeProcessStartToken") == "134362674928684990"
            and state.get("nativeInstanceId") == "90d9550789c680f110bf4ea8"
            and state.get("nativeActivationEpochId") == "activation-mv4ztgwa-41d4eace008278b49931d1b727068507"
            and Path(state.get("nativeWorkspace", "")).resolve(strict=True) == PRIMARY
            and Path(state.get("nativeModuleRoot", "")).resolve(strict=True) == PACKAGE.resolve(strict=True),
            "RECONCILE_ORIGINAL_RUNTIME_CHANGED")
    # Check the live Windows PID start token without commands or credentials.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, 0, 2404)
    require(bool(handle), "RECONCILE_ORIGINAL_RUNTIME_NOT_ALIVE")
    values = [ctypes.c_ulonglong() for _ in range(4)]
    try:
        require(kernel.GetProcessTimes(handle, *[ctypes.byref(value) for value in values]), "RECONCILE_RUNTIME_START_UNAVAILABLE")
        # Runtime state uses the WMI timestamp's microsecond precision; the
        # direct kernel value retains the final 100 ns digit. Pin both.
        require(str(values[0].value) == "134362674928684995", "RECONCILE_RUNTIME_PID_REUSED")
    finally:
        kernel.CloseHandle(handle)
    journal = load(JOURNAL)
    entry = journal.get("entries", {}).get(f"{ACTION}|{ATTEMPT}")
    require(isinstance(entry, dict), "RECONCILE_ORIGINAL_JOURNAL_ENTRY_MISSING")
    receipt = entry.get("receipt", {})
    payload = receipt.get("payload", {})
    require(entry.get("action_id") == ACTION and entry.get("attempt_id") == ATTEMPT
            and entry.get("state") == "unknown" and receipt.get("receipt_state") == "unknown"
            and receipt.get("receipt_submitted") is True and receipt.get("local_handle") == ""
            and payload.get("code") == "CONTROL_PLANE_DOCUMENT_WRITE_EFFECT_UNKNOWN"
            and payload.get("diagnostic_code") == "CONTROL_PLANE_DOCUMENT_WRITE_MCP_REJECTED"
            and payload.get("reconciliation_required") is True, "RECONCILE_ORIGINAL_UNKNOWN_MISMATCH")
    require(not (AUTOCAD / "mcp-access-smoke-20261012-r9.txt").exists()
            and not (AUTOCAD / ".coding-tools").exists(), "RECONCILE_EFFECT_EVIDENCE_PRESENT")
    registry = load(PRIMARY / ".coding-tools/orchestration/task-context-workspaces.json")
    contexts = registry.get("contexts", {})
    require(registry.get("schema_version") == 1 and isinstance(contexts, dict)
            and EXPECTED_CONTEXT not in contexts and EXPECTED_CONTEXT not in registry.get("legacy_contexts", {})
            and not any(isinstance(value, dict)
            and Path(str(value.get("canonical_root", "."))).resolve(strict=False) == AUTOCAD
            for value in contexts.values()), "RECONCILE_AUTOCAD_CONTEXT_ALREADY_BOUND")
    # Exact packaged bridge ordering: bootstrap must complete before workflow.
    archive = (BASE / "app.asar").read_bytes()
    begin = archive.index(b"async controlPlaneDocumentWrite(admission = {})")
    end = archive.index(b"async controlPlaneExec(admission = {})", begin)
    lane = archive[begin:end]
    require(lane.index(b"const bootstrap = await callLocalTool('workspace_context'")
            < lane.index(b"const structured = await callLocalTool(DOCUMENT_WRITE_LOCAL_TOOL_NAME"),
            "RECONCILE_PACKAGED_BRIDGE_ORDER_CHANGED")
    server_text = (PACKAGE / "coding_tools_mcp/server.py").read_text(encoding="utf-8")
    registry_text = (PACKAGE / "coding_tools_mcp/workspace_context_registry.py").read_text(encoding="utf-8")
    identity = server_text[server_text.index("    def _workspace_identity_for_request("):
                           server_text.index("    @staticmethod", server_text.index("    def _workspace_identity_for_request("))]
    bind = server_text[server_text.index("    def _bind_task_context_workspace("):
                       server_text.index("    def _bound_task_context_workspace(")]
    registry_bind = registry_text[registry_text.index("    def bind("):registry_text.index("    def _load(")]
    roots_update = server_text[server_text.index("    def set_authorized_roots("):server_text.index("    def switch_workspace(")]
    require(identity.index("self._bind_task_context_workspace(") < identity.index("return resolved, scope_root, identity")
            and bind.index("self.workspace_context_registry.bind(") < bind.index("self._task_context_workspace_ids[scope] = target")
            and registry_bind.index("self._write_locked()") < registry_bind.index("return dict(entry)")
            and "os.fsync(handle.fileno())" in registry_text and "os.replace(temporary, self.path)" in registry_text
            and not any(marker in registry_text for marker in ["self._contexts.clear(", "self._contexts.pop(", "del self._contexts["])
            and "workspace_context_registry" not in roots_update, "RECONCILE_DURABLE_BIND_ORDER_MISMATCH")
    sys.path.insert(0, str(PACKAGE))
    from coding_tools_mcp.errors import ToolFailure
    from coding_tools_mcp.workspace_scope import Workspace
    workspace = Workspace(PRIMARY, authorized_roots=[])
    source = ast.parse((PACKAGE / "coding_tools_mcp/server.py").read_text(encoding="utf-8"))
    runtime = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "Runtime")
    method = next(node for node in runtime.body if isinstance(node, ast.FunctionDef) and node.name == "_resolve_authorized_execution_scope")
    namespace = {"ToolFailure": ToolFailure, "ResolvedPath": object}
    exec(compile(ast.Module(body=[method], type_ignores=[]), "pinned-packaged-scope-guard", "exec"), namespace)
    refusal = ""
    try:
        namespace[method.name](SimpleNamespace(workspace=workspace, resolve_existing=workspace.resolve_existing), str(AUTOCAD), field="path")
    except ToolFailure as error:
        refusal = error.code
    require(refusal == "STALE_WORKSPACE_CONTEXT", "RECONCILE_EXPECTED_PRE_EFFECT_SCOPE_REFUSAL_MISSING")
    config = load(PROFILE / "control-plane-node.json")
    require(config.get("device_id") == DEVICE and config.get("server_url") == SERVER
            and config.get("credential_generation") == 1 and config.get("enrollment_state") == "approved"
            and isinstance(config.get("node_secret_dpapi"), str)
            and config["node_secret_dpapi"].startswith("dpapi-v1:")
            and not config.get("node_secret"), "RECONCILE_NODE_CREDENTIAL_METADATA_MISMATCH")
    return {"schema_version": 1, "operation_kind": "control_plane_document_write",
            "code": "PRE_EFFECT_WORKSPACE_BIND_REJECTED", "evidence_sha256": PINNED[CAUSAL_REPORT],
            "offline_scope_evidence_sha256": PINNED[REPORT],
            "original_local_journal_sha256": PINNED[JOURNAL], "packaged_app_sha256": PINNED[BASE / "app.asar"],
            "offline_native_refusal_code": refusal, "original_native_error_retained": False,
            "expected_local_context_id_sha256": hashlib.sha256(EXPECTED_CONTEXT.encode()).hexdigest(),
            "exact_durable_context_absent": True, "registry_has_no_context_delete_or_eviction": True,
            "reconciliation_basis": "operator_inference_from_exact_package_durable_binding_order_and_absent_context_and_effect_evidence",
            "original_unknown_receipt_preserved": True, "local_effect_replayed": False,
            "reconciliation_required": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-reconcile", action="store_true")
    args = parser.parse_args()
    payload = validate()
    output = {"operation": "original_create_pre_effect_reconciliation", "observed_at_ms": int(time.time() * 1000),
              "mode": "submit_original_receipt" if args.confirm_reconcile else "local_preflight_only",
              "action_id": ACTION, "attempt_id": ATTEMPT, "payload": payload,
              "node_journal_modified": False, "action_redispatched": False}
    if args.confirm_reconcile:
        spec = importlib.util.spec_from_file_location("pinned_node_agent", BASE / "resources/control-plane/node_agent.py")
        agent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent)
        # Protected credential is decrypted in memory. _config is not used:
        # its legacy migration path can write node configuration.
        config = load(PROFILE / "control-plane-node.json")
        secret = agent._unprotect_node_secret(config["node_secret_dpapi"])
        validate()  # Recheck all guards immediately before the one POST.
        response = agent._request(SERVER, f"/v1/nodes/{DEVICE}/receipts",
                                  {"action_id": ACTION, "attempt_id": ATTEMPT, "receipt_state": "rejected",
                                   "local_handle": "", "payload": payload}, f"Node {secret}")
        secret = None
        require(set(response) == {"receipt_id", "action_id", "attempt_id", "receipt_state", "delivery_state", "replayed"}
                and isinstance(response.get("receipt_id"), str) and re.fullmatch(r"rcpt_[a-f0-9]{32}", response["receipt_id"])
                and response.get("action_id") == ACTION and response.get("attempt_id") == ATTEMPT
                and response.get("receipt_state") == "rejected" and response.get("delivery_state") == "settled"
                and isinstance(response.get("replayed"), bool), "RECONCILE_RESPONSE_METADATA_MISMATCH")
        require(sha(JOURNAL) == PINNED[JOURNAL], "RECONCILE_LOCAL_JOURNAL_CHANGED_DURING_SUBMISSION")
        output["server_receipt"] = response
    report = Path(__file__).with_name(f"original-create-reconcile-preflight-{output['observed_at_ms']}.json")
    report.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(report), **output}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error)
        if re.fullmatch(r"[A-Z][A-Z0-9_]{2,100}", code) is None:
            code = "RECONCILE_PREFLIGHT_OR_TRANSPORT_FAILED"
        print(json.dumps({"operation": "original_create_pre_effect_reconciliation", "ok": False, "error_code": code}))
        raise SystemExit(1)
