"""Audit frozen r4 node-loop delta against actual serving Ubuntu evidence locally."""
import ast
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = PARENT.parents[2]
BASE = PARENT / "codex-control-plane-parallel-native-1012-f7acd9ec4ba1"
READINESS = PARENT / "server-readiness-before-r4.json"
NODE_PATH = "control-plane/control_plane/node_agent.py"
EXPECTED_NEW = "fca440c9fc9faa32e4beea9085b2828a85b1c27247a17217aef7230698ce2537"
CHANGED_FUNCTIONS = {"_connected_agent_iteration", "run_connected_agent"}


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def direct_branch(tree):
    branches = [node for node in tree.body if isinstance(node, ast.If)
                and isinstance(node.test, ast.Name) and node.test.id == "__package__"]
    require(len(branches) == 1, "EXACT_PACKAGE_DIRECT_BRANCH_REQUIRED")
    return branches[0]


def validate_delta(old, new):
    old_tree, new_tree = ast.parse(old), ast.parse(new)
    old_branch, new_branch = direct_branch(old_tree), direct_branch(new_tree)
    require(ast.dump(ast.Module(body=old_branch.body, type_ignores=[]))
            == ast.dump(ast.Module(body=new_branch.body, type_ignores=[])), "PACKAGE_IMPORT_BRANCH_CHANGED")
    old_functions = {node.name: node for node in old_tree.body if isinstance(node, ast.FunctionDef)}
    new_functions = {node.name: node for node in new_tree.body if isinstance(node, ast.FunctionDef)}
    require(set(old_functions) == set(new_functions), "NODE_FUNCTION_SURFACE_CHANGED")
    actual = {name for name in old_functions if ast.dump(old_functions[name]) != ast.dump(new_functions[name])}
    require(actual == CHANGED_FUNCTIONS, "DELTA_FUNCTIONS_NOT_EXACT")
    function_hashes = {}
    for name in sorted(CHANGED_FUNCTIONS):
        before, after = old_functions[name], new_functions[name]
        function_hashes[name] = {"serving_ast_sha256": sha(ast.dump(before).encode()), "r4_ast_sha256": sha(ast.dump(after).encode())}
        before.body, after.body = [], []
        require(ast.dump(before) == ast.dump(after), "CHANGED_NODE_FUNCTION_INTERFACE_CHANGED")
    old_branch.orelse, new_branch.orelse = [], []
    require(ast.dump(old_tree) == ast.dump(new_tree), "DELTA_EXCEEDS_DIRECT_LOADER_AND_TWO_LOOP_FUNCTIONS")
    return function_hashes


def import_dependencies(source, local_names):
    dependencies = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                if node.module:
                    dependencies.add(node.module.split(".")[0])
                else:
                    dependencies.update(alias.name.split(".")[0] for alias in node.names)
            elif node.module == "control_plane":
                dependencies.update(alias.name.split(".")[0] for alias in node.names)
            elif str(node.module or "").startswith("control_plane."):
                dependencies.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("control_plane."):
                    dependencies.add(alias.name.split(".")[1])
        elif isinstance(node, ast.Call):
            call_name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if call_name in {"__import__", "import_module"}:
                require(node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str),
                        "OPAQUE_DYNAMIC_IMPORT_REQUIRES_REVIEW")
                name = node.args[0].value
                if name.startswith("control_plane."):
                    dependencies.add(name.split(".")[1])
                elif name == "control_plane":
                    dependencies.add("__init__")
            require(call_name not in {"exec", "eval", "exec_module", "run_module", "run_path"}, "OPAQUE_EXECUTION_REQUIRES_REVIEW")
    return sorted(dependencies & local_names)


def serving_entrypoint_graph(package, renewal):
    modules = {file.stem: file.read_text(encoding="utf-8") for file in package.glob("*.py")}
    pending = ["__init__", "__main__"]
    graph = {}
    while pending:
        name = pending.pop()
        if name in graph:
            continue
        dependencies = import_dependencies(modules[name], set(modules))
        require(name == "node_agent" or not any(isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id in CHANGED_FUNCTIONS)
                    or (isinstance(node.func, ast.Attribute) and node.func.attr in CHANGED_FUNCTIONS))
                    for node in ast.walk(ast.parse(modules[name]))), "SERVING_ENTRYPOINT_EXECUTES_CHANGED_NODE_LOOP")
        graph[name] = dependencies
        pending.extend(dependencies)
    renewal_dependencies = import_dependencies(renewal, set(modules))
    require(renewal_dependencies == [], "RENEWAL_IMPORTS_CONTROL_PLANE_PACKAGE")
    require(not any(isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id in CHANGED_FUNCTIONS)
                or (isinstance(node.func, ast.Attribute) and node.func.attr in CHANGED_FUNCTIONS))
                for node in ast.walk(ast.parse(renewal))), "RENEWAL_EXECUTES_CHANGED_NODE_LOOP")
    return {"http_transitive_local_import_graph": graph, "renewal_local_import_dependencies": renewal_dependencies,
            "node_agent_reachable_from_http_or_renewal": "node_agent" in graph.get("mcp_facade", []),
            "changed_connected_agent_loop_executed_by_http_or_renewal": False}


def main():
    readiness_raw = READINESS.read_bytes()
    readiness = json.loads(readiness_raw.decode("utf-8-sig"))
    require(readiness.get("ok") is True and readiness.get("service_stable") is True
            and readiness.get("source_startup_disk_attestation_matches") is True
            and readiness.get("serving_source", {}).get("release_file_integrity_verified") is True
            and 0 <= int(time.time() * 1000) - readiness.get("capture_completed_at_ms", 0) <= 10 * 60 * 1000,
            "FRESH_SANITIZED_SERVING_OBSERVATION_REQUIRED")
    observed = readiness["serving_source"]
    package = BASE / "control-plane/control_plane"
    for name, expected in observed["python_files_sha256"].items():
        require(sha((package / name).read_bytes()) == expected, "EXACT_SERVING_PACKAGE_BASELINE_DRIFT")
    old, new = (BASE / NODE_PATH).read_bytes(), (ROOT / NODE_PATH).read_bytes()
    require(sha(new) == EXPECTED_NEW, "FROZEN_R4_NODE_LOOP_SOURCE_REQUIRED")
    function_hashes = validate_delta(old, new)
    launcher = (BASE / "deploy/control-plane-launcher.sh").read_text(encoding="utf-8")
    entry = (package / "__main__.py").read_text(encoding="utf-8")
    renewal_file = BASE / "deploy/control-plane-authority-renewal.py"
    renewal = renewal_file.read_text(encoding="utf-8")
    manifest = {item["path"]: item["sha256"] for item in observed["release_manifest_files"]}
    for relative in ("deploy/control-plane-launcher.sh", "deploy/control-plane-authority-renewal.py"):
        require(sha((BASE / relative).read_bytes()) == manifest[relative], "EXACT_SERVING_DEPLOY_ENTRYPOINT_DRIFT")
    require("exec /usr/bin/python3 -B -m control_plane" in launcher
            and "from .http_api import serve_from_environment" in entry, "SERVING_PACKAGE_ENTRYPOINT_CHANGED")
    graph = serving_entrypoint_graph(package, renewal)
    receipt = {"schema_version": 1, "operation": "windows_r4_loader_and_heartbeat_loop_delta_against_serving_ubuntu", "ok": True,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "observed_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "readiness_sha256": sha(readiness_raw), "readiness_captured_at_ms": readiness["capture_completed_at_ms"],
        "serving_service_pid": readiness["service_pid"], "serving_release_root": observed["serving_release_root"],
        "serving_package_source_sha256": observed["package_source_sha256"], "serving_node_agent_sha256": sha(old),
        "windows_r4_node_agent_raw_sha256": sha(new), "changed_function_ast_sha256": function_hashes,
        "package_import_branch_unchanged": True, "all_ast_except_direct_else_and_two_named_function_bodies_unchanged": True,
        "changed_functions": sorted(CHANGED_FUNCTIONS), "changed_functions_public_signatures_unchanged": True,
        "serving_http_entrypoint": "python3 -B -m control_plane -> .http_api.serve_from_environment",
        "serving_entrypoint_dependency_proof": graph,
        "serving_http_may_import_node_agent_for_facade_relay": True,
        "serving_http_and_renewal_do_not_execute_changed_connected_agent_loop": True,
        "serving_entrypoint_hashes": {"launcher": sha((BASE / "deploy/control-plane-launcher.sh").read_bytes()),
            "package_main": sha((package / "__main__.py").read_bytes()), "renewal": sha(renewal_file.read_bytes())},
        "contract": readiness["tool_contract"], "ubuntu_alignment_deployment_required_for_current_http_and_renewal": False,
        "ubuntu_alignment_deployment_performed": False, "external_mutations_performed": False,
        "source_or_package_parity_claimed": False,
        "proof_limit": "Current immutable HTTP entrypoint transitively imports node_agent for facade relay, but neither HTTP nor renewal executes the corrected connected-agent loop. This does not prove a future Linux node-agent client uses the corrected loop or that r4 has been packaged/activated.",
        "canary_pin_rule": "Pin actual serving Ubuntu node_agent and Windows r4 node_agent separately; do not claim byte parity."}
    output = HERE / "windows-r4-source-delta-receipt-corrected.json"
    require(not output.exists(), "NEW_ADDITIVE_R4_RECEIPT_REQUIRED")
    with (HERE / "windows-r4-loader-and-heartbeat-loop-corrected.diff").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
            fromfile="ubuntu-serving/" + NODE_PATH, tofile="windows-r4/" + NODE_PATH)))
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": True, "report_path": str(output), "serving_service_pid": readiness["service_pid"],
        "changed_functions": sorted(CHANGED_FUNCTIONS), "ubuntu_restart_required_for_current_entrypoints": False}))


if __name__ == "__main__":
    main()
