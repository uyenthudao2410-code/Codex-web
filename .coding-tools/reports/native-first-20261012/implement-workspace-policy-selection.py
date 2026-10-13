"""Guarded source transformation for the scoped policy change (not runtime data)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / "control-plane/control_plane/node_agent.py"
source = path.read_text(encoding="utf-8")


def replace(old, new, count=1):
    global source
    if source.count(old) != count:
        raise RuntimeError("SOURCE_EDIT_PREIMAGE_CHANGED")
    source = source.replace(old, new)


def block(name):
    match = re.search(r"^def " + re.escape(name) + r"\(.*?(?=^def |\Z)", source, re.M | re.S)
    if not match:
        raise RuntimeError("SOURCE_FUNCTION_MISSING")
    return match.group()


def edit_block(name, transform):
    old = block(name)
    replace(old, transform(old))


replace("from typing import Any, Callable, Iterator\n", "from typing import Any, Callable, Iterator\n\nfrom .workspace_policy_store import (\n    read_entries as _workspace_policy_entries, read_selected as _workspace_policy_selected,\n    write_policy as _workspace_policy_write, scope as _workspace_policy_scope,\n)\n")
readers = (
    ("_read_local_policy", "READ_ONLY_POLICY_MAX_BYTES", "CONTROL_PLANE_BRIDGE", "_normalise_read_only_policy"),
    ("_read_file_read_policy", "FILE_READ_POLICY_MAX_BYTES", "CONTROL_PLANE_FILE_READ", "_normalise_file_read_policy"),
    ("_read_approved_patch_policy", "APPROVED_PATCH_POLICY_MAX_BYTES", "CONTROL_PLANE_APPROVED_PATCH", "_normalise_approved_patch_policy"),
    ("_read_exec_policy", "EXEC_POLICY_MAX_BYTES", "CONTROL_PLANE_EXEC", "_normalise_exec_policy"),
)
for name, maximum, code, normalise in readers:
    replacement = f'''def {name}(policy_path: Path, *, target: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        policy_path.stat()
        value = _workspace_policy_selected(policy_path, target)
        if len(json.dumps(value).encode("utf-8")) > {maximum}:
            raise RuntimeError("{code}_POLICY_INVALID")
    except FileNotFoundError as error:
        raise RuntimeError("{code}_POLICY_MISSING") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("{code}_POLICY_INVALID") from error
    except RuntimeError as error:
        if str(error).startswith("CONTROL_PLANE_POLICY_"):
            suffix = "MISSING" if str(error) == "CONTROL_PLANE_POLICY_TARGET_NOT_FOUND" else "INVALID"
            raise RuntimeError("{code}_POLICY_" + suffix) from error
        raise
    return {normalise}(value)


'''
    replace(block(name), replacement)

replace(block("_write_local_policy"), '''def _write_local_policy(policy_path: Path, policy: dict[str, Any], *, replace: bool) -> None:
    _workspace_policy_write(policy_path, policy, replace=replace, atomic_writer=_write_json_atomic)


def _policy_target(args: argparse.Namespace) -> dict[str, str] | None:
    workspace_id = getattr(args, "workspace_id", None)
    generation = getattr(args, "workspace_generation", None)
    if not workspace_id and not generation:
        return None
    target = {"workspace_id": workspace_id, "workspace_generation": generation}
    _workspace_policy_scope(target)
    return target


def _targeted_poll(args: argparse.Namespace, payload: dict[str, Any]) -> dict[str, Any]:
    target = _policy_target(args)
    return {**payload, **target} if target is not None else payload


''')
# Existing CLI/loop consumers select their explicit target, preserving singleton
# behavior when no target was historically supplied.
for reader, _maximum, _code, _normalise in readers:
    for path_factory in ("_read_only_policy_path", "_file_read_policy_path", "_approved_patch_policy_path", "_exec_policy_path"):
        old = f"{reader}({path_factory}(args))"
        source = source.replace(old, f"{reader}({path_factory}(args), target=_policy_target(args))")
    source = source.replace(f"{reader}(policy_path)", f"{reader}(policy_path, target=_policy_target(args))")
source = source.replace("_read_exec_policy(path)", "_read_exec_policy(path, target=_policy_target(args))")

for name in ("_file_read_policy_admission", "_approved_patch_policy_admission", "_document_write_policy_admission"):
    def change(text):
        text = text.replace("    config: dict[str, Any],\n)", "    config: dict[str, Any],\n    target: dict[str, Any] | None = None,\n)", 1)
        text = text.replace("target=_policy_target(args)", "target=target or _policy_target(args)")
        if name == "_document_write_policy_admission":
            text = text.replace("config=config)", "config=config, target=target)")
        return text
    edit_block(name, change)
for name in ("_admit_file_read_policy_request", "_admit_approved_patch_policy_request", "_admit_document_write_policy_request"):
    edit_block(name, lambda text: text.replace("config_path=config_path, config=config)", "config_path=config_path, config=config, target=request)", 1))
edit_block("_admit_exec_policy_request", lambda text: text.replace("target=_policy_target(args)", "target=request"))

for name in ("_disable_matching_retired_workspace_policy", "_disable_matching_retired_workspace_file_read_policy", "_disable_matching_retired_workspace_approved_patch_policy", "_disable_matching_retired_workspace_exec_policy"):
    # The compact metadata helper has a historical name in this source.
    if not re.search(r"^def " + re.escape(name) + r"\(", source, re.M):
        if name == "_disable_matching_retired_workspace_policy":
            name = "_disable_matching_retired_workspace_read_only_policy"
    edit_block(name, lambda text: text.replace("target=_policy_target(args)", "target=entry"))

for lane in ("bounded_file_read", "approved_patch", "document_write", "bounded_exec", "bounded_artifact"):
    old = '{"limit": 1, "lane": "' + lane + '"}'
    replace(old, "_targeted_poll(args, " + old + ")")
edit_block("_poll_artifact_once", lambda text: text.replace("                config=config,\n            )", "                config=config,\n                target=action,\n            )", 1).replace("config_path=config_path, config=config)", "config_path=config_path, config=config, target=action)"))

# Inspection/revocation selectors are explicit and never mutable global state.
for parser in ("inspect_policy", "disable_policy", "inspect_file_read_policy_parser", "disable_file_read_policy_parser", "inspect_approved_patch_policy_parser", "disable_approved_patch_policy_parser", "inspect_exec_policy_parser", "disable_exec_policy_parser"):
    marker = f'    {parser}.add_argument("--data-root", default="")\n'
    replace(marker, marker + f'    {parser}.add_argument("--workspace-id")\n    {parser}.add_argument("--workspace-generation")\n')
path.write_text(source, encoding="utf-8", newline="")

# Bridge loaders keep existing normalisers/fingerprints and accept a target.
for filename, function, code in (
    ("controlPlaneReadOnlyBridge.js", "loadReadOnlyBridgePolicy", "CONTROL_PLANE_BRIDGE_POLICY_INVALID"),
    ("controlPlaneFileReadBridge.js", "loadFileReadBridgePolicy", "CONTROL_PLANE_FILE_READ_POLICY_INVALID"),
    ("controlPlaneApprovedPatchBridge.js", "loadApprovedPatchBridgePolicy", "CONTROL_PLANE_APPROVED_PATCH_POLICY_INVALID"),
    ("controlPlaneExecBridge.js", "loadExecBridgePolicy", "CONTROL_PLANE_EXEC_POLICY_INVALID"),
):
    path = ROOT / "electron/services" / filename
    content = path.read_text(encoding="utf-8")
    content = content.replace("const fs = require('node:fs');", "const fs = require('node:fs');\nconst { MAX_COLLECTION_BYTES, selectWorkspacePolicy } = require('./controlPlanePolicyStore');", 1)
    match = re.search(r"function " + function + r"\(.*?(?=\nfunction |\nmodule.exports)", content, re.S)
    old = match.group()
    new = old.replace("{ now = Date.now()", "{ target = null, now = Date.now()", 1)
    new = new.replace("stat.size > MAX_POLICY_BYTES", "stat.size > MAX_COLLECTION_BYTES")
    new = new.replace("normalisePolicy(raw,", f"normalisePolicy(selectWorkspacePolicy(raw, target, {{ code: '{code}', maxPolicyBytes: MAX_POLICY_BYTES }}),")
    content = content.replace(old, new, 1)
    path.write_text(content, encoding="utf-8", newline="")
print("SCOPED_POLICY_SOURCE_TRANSFORMATION_COMPLETE")
