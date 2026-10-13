"""Pure facade/store input validation; never instantiate store or send requests."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
root = here.parents[3]
validator_package = root / ".coding-tools/reports/folder-access-20261012-r9/server-overlay/codex-control-plane-local-folder-activation-1012-r9-626768b49f4b/control-plane"
sys.path.insert(0, str(validator_package))
from control_plane.mcp_facade import ControlPlaneMcpFacade
from control_plane.store import _mcp_exec_argv, _mcp_exec_cwd, _mcp_exec_limits, ValidationError

script = here / "run-autocad-exec-only-canary-r9d.py"
spec = importlib.util.spec_from_file_location("prepared_exec_only", script)
prepared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepared)
facade = object.__new__(ControlPlaneMcpFacade)
facade.oauth_enabled = facade.oauth_file_read_enabled = facade.oauth_exec_enabled = True
facade.oauth_permission_requests_enabled = facade.oauth_approved_patch_enabled = False
contract = {"schema_version":32,"profile":"control-plane-private-tunnel-service-v1",
            "sha256":"3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66"}


def validate(argv):
    arguments = {"operation":"exec_run", "binding_id":"bind_offline_validation", "task_id":"task_"+"a"*32,
                 "argv":argv,"cwd":"","timeout_ms":300000,"max_output_bytes":32768,
                 "idempotency_key":"offline-validation:prepared-command","expected_facade_contract":contract}
    name, normalized = facade._arguments({"name":"exec_command","arguments":arguments})
    assert name == "exec_command" and normalized["argv"] == argv
    assert _mcp_exec_argv(argv) == argv and _mcp_exec_cwd("") == ""
    assert _mcp_exec_limits(timeout_ms=300000,max_output_bytes=32768) == (300000,32768)


commands = []
for lane, argv in prepared.COMMANDS:
    validate(argv)
    commands.append({"lane":lane,"argv_item_bytes":[len(item.encode()) for item in argv],"facade":"pass","store":"pass"})
old_tree = ast.parse((here / "run-autocad-folder-access-canary-r9d.py").read_text(encoding="utf-8"))
old_code = next(ast.literal_eval(node.value) for node in old_tree.body if isinstance(node,ast.Assign)
                and any(isinstance(target,ast.Name) and target.id == "NODE_CODE" for target in node.targets))
try:
    validate(["node","-e",old_code])
    raise AssertionError("Original invalid inline code was unexpectedly admitted")
except ValidationError as error:
    original_failure = {"type":type(error).__name__,"message":str(error),"inline_bytes":len(old_code.encode()),
                        "contains_forbidden_semicolons":";" in old_code,"cwd_empty_is_valid":True}
report = {"operation":"r9d_exec_only_offline_validation", "live_execution_performed":False,
          "production_authority_modified":False,"original_canary_file_preserved":True,"commands":commands,
          "original_pre_admission_failure":original_failure,"python_sha256":hashlib.sha256(script.read_bytes()).hexdigest(),
          "expected_guest_cwd":prepared.GUEST_CWD,"expected_existing_file_sha256":prepared.POSTIMAGE,
          "validator_sha256":{name:hashlib.sha256((validator_package / f"control_plane/{name}.py").read_bytes()).hexdigest()
                              for name in ("mcp_facade","store")}}
report_path = here / "r9d-exec-only-offline-validation.json"
report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"report_path":str(report_path),**report}))
