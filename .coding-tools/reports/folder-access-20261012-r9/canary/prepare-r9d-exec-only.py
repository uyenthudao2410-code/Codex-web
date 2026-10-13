"""Prepare additive exec-only canary; never dispatch or modify production authority."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
prior_path = here / "run-autocad-folder-access-canary-r9d.py"
source = prior_path.read_text(encoding="utf-8")
assert hashlib.sha256(source.encode()).hexdigest() == "dfe1fda063f4ebd7d55d164d6470456ec00d5c4623ac4914e4d35f4f99eb6fe5"
source = source.replace("Run one reviewed shared MCP create, exact patch and exec proof", "Run four fresh structured exec proofs against the already verified Autocad file")
start = source.index("MARKER = ")
end = source.index("PROTOCOL = ", start)
constants = '''TARGET = "mcp-access-smoke-20261012-r9d.txt"
POSTIMAGE = "3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023"
DOTNET_VERSION = "10.0.102"
GUEST_CWD = r"C:\\CodexWorkspace\\share-0"
COMMANDS = (
    ("node_version", ["node", "--version"]),
    ("node_cwd", ["node", "-p", "process.cwd()"]),
    ("node_hash", ["node", "-p", "require('node:crypto').createHash('sha256').update(require('node:fs').readFileSync('mcp-access-smoke-20261012-r9d.txt')).digest('hex')"]),
    ("dotnet", ["dotnet", "--version"]),
)
'''
source = source[:start] + constants + source[end:]
start = source.index("LANES = {")
end = source.index("\n\n\ndef recover_handles", start)
source = source[:start] + 'LANES = {lane: ("mcp_exec_intents", "exec_command", "exec_status") for lane, _argv in COMMANDS}' + source[end:]
start = source.index("def patch_envelope():")
end = source.index("def main():", start)
validation = '''def validate_commands(pid, contract):
    # Load the actual serving implementation only for its pure validators.
    serving_package = Path(f"/proc/{pid}/cwd").resolve() / "control-plane"
    require((serving_package / "control_plane/mcp_facade.py").is_file(), "SERVING_VALIDATOR_SOURCE_MISSING")
    sys.path.insert(0, str(serving_package))
    from control_plane.mcp_facade import ControlPlaneMcpFacade
    from control_plane.store import _mcp_exec_argv, _mcp_exec_cwd, _mcp_exec_limits
    facade = object.__new__(ControlPlaneMcpFacade)
    facade.oauth_enabled = facade.oauth_file_read_enabled = facade.oauth_exec_enabled = True
    facade.oauth_permission_requests_enabled = facade.oauth_approved_patch_enabled = False
    for lane, argv in COMMANDS:
        parameters = {"operation":"exec_run", "binding_id":"bind_offline_validation",
                      "task_id":"task_"+"a"*32, "argv":argv, "cwd":"", "timeout_ms":300000,
                      "max_output_bytes":32768, "idempotency_key":"offline-validation:"+lane,
                      "expected_facade_contract":contract}
        name, normalized = facade._arguments({"name":"exec_command", "arguments":parameters})
        require(name == "exec_command" and normalized["argv"] == argv, "OFFLINE_FACADE_ARGUMENT_MISMATCH")
        require(_mcp_exec_argv(argv) == argv and _mcp_exec_cwd("") == ""
                and _mcp_exec_limits(timeout_ms=300000,max_output_bytes=32768) == (300000,32768),
                "OFFLINE_STORE_ARGUMENT_MISMATCH")
    emit("offline_exec_arguments_validated", command_count=len(COMMANDS),
         argv_item_bytes={lane:[len(item.encode()) for item in argv] for lane,argv in COMMANDS},
         serving_source_sha256={name:hashlib.sha256((serving_package / ("control_plane/"+name+".py")).read_bytes()).hexdigest()
                                for name in ("mcp_facade","store")})


'''
source = source[:start] + validation + source[end:]
source = source.replace('attempt = "autocad-folder-access-r9d-20261012:"', 'attempt = "autocad-exec-only-r9d-20261012:"')
source = source.replace('"label": "Autocad shared folder read write patch Node and dotnet proof"', '"label": "Autocad fresh Node version cwd file hash and dotnet exec proof"')
source = source.replace('contract = check_target(args, connection, client)\n', 'contract = check_target(args, connection, client)\n        validate_commands(pid, contract)\n', 1)
start = source.index('        created = queue("create"')
end = source.index('            executed = queue(lane, "exec_command"', start)
source = source[:start] + '        for lane, argv in COMMANDS:\n' + source[end:]
start = source.index('            if lane == "exec":')
end = source.index('            payload, proof = verified_receipt', start)
expectations = '''            clean_output = output.strip()
            if lane == "node_version":
                match = re.fullmatch(r"v([0-9]+)\\.[0-9]+\\.[0-9]+", clean_output)
                require(match is not None and int(match.group(1)) >= 22, "NODE_VERSION_NOT_VERIFIED")
            elif lane == "node_cwd":
                require(clean_output == GUEST_CWD, "GUEST_WORKSPACE_NOT_VERIFIED")
            elif lane == "node_hash":
                require(clean_output == POSTIMAGE, "EXISTING_FINAL_FILE_HASH_NOT_VERIFIED")
            else:
                require(clean_output == DOTNET_VERSION, "DIRECT_DOTNET_VERSION_NOT_VERIFIED")
'''
source = source[:start] + expectations + source[end:]
source = source.replace('"final_sha256": postimage, "marker_verified": True,', '"final_sha256": POSTIMAGE, "existing_file_hash_verified": True,')
source = source.replace('"semantic_acceptance_performed": False}', '"semantic_acceptance_performed": False, "file_write_or_patch_dispatched": False}')
source = source.replace('"operation": "autocad_folder_access_canary"', '"operation": "autocad_exec_only_canary"')
compile(source, "run-autocad-exec-only-canary-r9d.py", "exec")
assert 'queue("create"' not in source and 'queue("patch"' not in source and 'INITIAL' not in source
python_path = here / "run-autocad-exec-only-canary-r9d.py"
assert not python_path.exists()
python_path.write_text(source, encoding="utf-8")
python_hash = hashlib.sha256(python_path.read_bytes()).hexdigest()
wrapper_source = (here / "invoke-autocad-folder-access-canary-r9d.ps1").read_text(encoding="utf-8")
wrapper_source = wrapper_source.replace("run-autocad-folder-access-canary-r9d.py", python_path.name)
wrapper_source = wrapper_source.replace("dfe1fda063f4ebd7d55d164d6470456ec00d5c4623ac4914e4d35f4f99eb6fe5", python_hash)
wrapper_source = wrapper_source.replace("autocad-folder-access-receipt-r9d-", "autocad-exec-only-receipt-r9d-")
wrapper_source = wrapper_source.replace("if (Test-Path -LiteralPath $targetPath) { throw 'SCRATCH_TARGET_ALREADY_EXISTS_DO_NOT_OVERWRITE' }",
    "if (-not (Test-Path -LiteralPath $targetPath)) { throw 'EXISTING_VERIFIED_R9D_FILE_REQUIRED' }\n"
    "if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023') { throw 'EXISTING_VERIFIED_R9D_FILE_CHANGED' }")
wrapper_source = wrapper_source.replace("autocad_folder_access_canary_ssh", "autocad_exec_only_canary_ssh")
wrapper_path = here / "invoke-autocad-exec-only-canary-r9d.ps1"
assert not wrapper_path.exists()
wrapper_path.write_text(wrapper_source, encoding="utf-8")
print(json.dumps({"python_path":str(python_path), "python_sha256":python_hash,
                  "wrapper_path":str(wrapper_path), "wrapper_sha256":hashlib.sha256(wrapper_path.read_bytes()).hexdigest(),
                  "live_execution_performed":False}))
