"""Prepare exact r9 source overlay; no upload, deployment or authority changes.

The entire facade is identical to serving baseline except reviewed metadata
support. node_agent receives only the pure validator and one attested pre-effect
error code. Every other serving-release byte remains unchanged.
"""
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT / ".coding-tools/reports/folder-access-20261012-r9/server-overlay/codex-control-plane-local-folder-activation-1012-r9-626768b49f4b"
SHA = lambda content: hashlib.sha256(content).hexdigest()


def require(value, code):
    if not value:
        raise RuntimeError(code)


def function(source, name):
    tree = ast.parse(source)
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return "".join(source.splitlines(True)[node.lineno - 1:node.end_lineno]) + "\n"


def component(records, prefix):
    digest = hashlib.sha256()
    for record in records:
        if record["path"].startswith(prefix):
            digest.update(record["path"].encode() + b"\0" + record["sha256"].encode() + b"\0")
    return digest.hexdigest()


def main():
    readiness = json.loads((OUT / "server-readiness.json").read_text(encoding="utf-8"))
    observed = readiness["serving_source"]
    manifest_bytes = (BASE / "release-manifest.json").read_bytes()
    require(SHA(manifest_bytes) == observed["release_manifest_sha256"], "LOCAL_SERVING_BASELINE_MANIFEST_DRIFT")
    manifest = json.loads(manifest_bytes)
    require(manifest["files"] == observed["release_manifest_files"], "LOCAL_SERVING_BASELINE_FILES_DRIFT")
    facade_path = "control-plane/control_plane/mcp_facade.py"
    node_path = "control-plane/control_plane/node_agent.py"
    facade_before = (BASE / facade_path).read_text(encoding="utf-8")
    facade_head = subprocess.run(["git", "show", "HEAD:" + facade_path], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    require(facade_before.replace("\r\n", "\n") == facade_head.replace("\r\n", "\n"), "SERVING_FACADE_NOT_EXACT_HEAD")
    facade_after = (ROOT / facade_path).read_text(encoding="utf-8").replace("\r\n", "\n")
    # Existing source proof: only the approved metadata diff is permitted.
    allowed_functions = {"_completed_exec_relay"}
    allowed_methods = {"_exec_status", "_exec_output", "_exec_stop"}
    trees = [ast.parse(facade_before), ast.parse(facade_after)]
    for tree in trees:
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "node_agent":
                node.names = [item for item in node.names if item.name != "_safe_exec_metadata"]
            if isinstance(node, ast.ClassDef) and node.name == "ControlPlaneMcpFacade":
                node.body = [item for item in node.body if not isinstance(item, ast.FunctionDef) or item.name not in allowed_methods]
        tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name not in allowed_functions]
    require(ast.dump(trees[0]) == ast.dump(trees[1]), "UNAPPROVED_FACADE_CHANGE")
    node_before = (BASE / node_path).read_text(encoding="utf-8").replace("\r\n", "\n")
    local_node = (ROOT / node_path).read_text(encoding="utf-8").replace("\r\n", "\n")
    metadata = function(local_node, "_safe_exec_metadata")
    anchor = "def _safe_exec_bridge_result("
    require(node_before.count(anchor) == 1 and "def _safe_exec_metadata(" not in node_before, "NODE_METADATA_ANCHOR_DRIFT")
    node_after = node_before.replace(anchor, metadata + "\n\n" + anchor, 1)
    old_code = '    "CONTROL_PLANE_FILE_READ_TARGET_MISMATCH",\n'
    new_code = old_code + '    # Only the Recovery Host pre-dispatch phase can emit this attestation.\n    "CONTROL_PLANE_FILE_READ_TARGET_MISSING_BEFORE_DISPATCH",\n'
    left = node_after.index("FILE_READ_PRE_EFFECT_REJECTION_CODES = ")
    right = node_after.index("\nREAD_ONLY_POLICY_STOP_CODES", left)
    section = node_after[left:right]
    require(section.count(old_code) == 1, "FILE_READ_PRE_EFFECT_ANCHOR_DRIFT")
    node_after = node_after[:left] + section.replace(old_code, new_code, 1) + node_after[right:]
    before_tree, after_tree = ast.parse(node_before), ast.parse(node_after)
    after_tree.body = [node for node in after_tree.body if not isinstance(node, ast.FunctionDef) or node.name != "_safe_exec_metadata"]
    for tree in (before_tree, after_tree):
        tree.body = [node for node in tree.body if not isinstance(node, ast.Assign) or not any(isinstance(target, ast.Name) and target.id == "FILE_READ_PRE_EFFECT_REJECTION_CODES" for target in node.targets)]
    require(ast.dump(before_tree) == ast.dump(after_tree), "UNAPPROVED_NODE_CHANGE")
    modified = {facade_path: facade_after.encode(), node_path: node_after.encode()}
    digest = SHA(b"".join(modified[name] for name in sorted(modified)))
    name = "codex-control-plane-native-first-1012-" + digest[:12]
    candidate = OUT / name
    require(not candidate.exists(), "CANDIDATE_ALREADY_EXISTS")
    candidate.mkdir()
    records = []
    for record in manifest["files"]:
        path, expected = record["path"], record["sha256"]
        before = (BASE / path).read_bytes()
        require(len(before) == record["size_bytes"] and SHA(before) == expected, "BASELINE_FILE_DRIFT")
        content = modified.get(path, before)
        target = candidate / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
        records.append({"path": path, "sha256": SHA(content), "size_bytes": len(content)})
    changed = [record["path"] for old, record in zip(manifest["files"], records) if old != record]
    require(changed == sorted(modified), "OVERLAY_CHANGED_FILE_SET_DRIFT")
    aggregate = hashlib.sha256()
    for path in sorted((candidate / "control-plane/control_plane").glob("*.py")):
        aggregate.update(path.name.encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest() + b"\0")
    candidate_manifest = {**manifest, "release_name": name, "package_source_sha256": "sha256:" + aggregate.hexdigest(),
        "component_sha256": {key: component(records, prefix) for key, prefix in {"control_plane": "control-plane/control_plane/", "deployment": "deploy/", "documentation": "DEPLOYMENT.md"}.items()}, "files": records}
    (candidate / "release-manifest.json").write_text(json.dumps(candidate_manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("native_overlay_release_verifier", candidate / "deploy/control-plane-verify-release.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verification = verifier.verify_release(candidate)
    contract_code = "from control_plane.mcp_facade import tool_contract; import json; c=tool_contract(auth_kind='private_tunnel_service',oauth_scopes=('control-plane.inventory',),oauth_file_read_enabled=True,oauth_patch_write_scope='control-plane.patch',oauth_approved_patch_enabled=True,oauth_standing_write_enabled=True,oauth_exec_enabled=True); print(json.dumps(c))"
    contract_proc = subprocess.run([sys.executable, "-B", "-c", contract_code], cwd=candidate / "control-plane", capture_output=True, check=True)
    contract = json.loads(contract_proc.stdout)
    require({key: contract[key] for key in ("schema_version", "profile", "sha256")} == readiness["tool_contract"], "OVERLAY_PUBLIC_CONTRACT_DRIFT")
    for path in changed:
        (OUT / (Path(path).stem + "-metadata-overlay.diff")).write_text("".join(difflib.unified_diff((BASE / path).read_text(encoding="utf-8").splitlines(True), (candidate / path).read_text(encoding="utf-8").splitlines(True), fromfile="serving/" + path, tofile="candidate/" + path)), encoding="utf-8")
    archive = OUT / (name + ".tar.gz")
    with tarfile.open(archive, "w:gz", compresslevel=9) as bundle:
        def modes(member):
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            member.mode = 0o755 if member.isdir() or member.name.endswith(".sh") else 0o644
            return member
        bundle.add(candidate, arcname=name, filter=modes)
    receipt = {"operation": "native_first_metadata_overlay_preparation", "ok": True,
        "candidate_release": str(candidate), "candidate_archive": str(archive), "candidate_archive_sha256": SHA(archive.read_bytes()),
        "candidate_manifest_sha256": SHA((candidate / "release-manifest.json").read_bytes()), "verification": verification,
        "changed_runtime_files": changed, "unchanged_release_files": len(records) - len(changed),
        "baseline_service_pid": readiness["service_pid"], "baseline_release_root": observed["serving_release_root"],
        "baseline_manifest_sha256": observed["release_manifest_sha256"], "baseline_package_source_sha256": observed["package_source_sha256"],
        "protected_config_hashes": readiness["protected_activation_config_hashes"], "expected_contract": readiness["tool_contract"],
        "expected_unknown_actions": [{key: action[key] for key in ("action_id", "workspace_id", "workspace_generation", "delivery_state", "expires_at_ms", "disposition")} for action in readiness["historical_unknown_actions_preserved"]],
        "source_revision_is_original_base_lineage": manifest.get("source_revision"),
        "overlay_is_locally_prepared_not_committed_revision": True, "remote_mutations_performed": False,
        "rollback": {"source_only": True, "restore_release_root": observed["serving_release_root"], "restore_package_source_sha256": observed["package_source_sha256"],
                     "database_restore_allowed": False, "authority_restore_allowed": False, "procedure": "Guard current candidate and idle census; restore protected pre-switch env/drop-in; atomically restore current release link; daemon-reload and restart exact service; verify previous serving package and schema32 contract; preserve all task/action/history rows."}}
    with (OUT / "server-overlay-preparation.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": True, "release": name, "changed_files": changed, "package_source_sha256": verification["package_source_sha256"], "contract": readiness["tool_contract"], "remote_mutations": False}, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import re
        code = str(error) if isinstance(error, RuntimeError) and re.fullmatch(r"[A-Z_]{3,100}", str(error)) else type(error).__name__
        print(json.dumps({"ok": False, "error_code": code, "remote_mutations": False}, separators=(",", ":")))
        sys.exit(1)
