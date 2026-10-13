from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
old = here / 'run-autocad-exec-only-canary-r9d.py'
source = old.read_text(encoding='utf-8')
assert hashlib.sha256(old.read_bytes()).hexdigest() == '9d1903d588fddcd6c979c4c4f3e868c7156219c924717d8e6d502a1778ceb4d6'
source = source.replace('    ("node_version", ["node", "--version"]),\n', '')
source = source.replace('autocad-exec-only-r9d-20261012:', 'autocad-exec-remaining-r9d-20261012:')
source = source.replace('"operation": "autocad_exec_only_canary"', '"operation": "autocad_exec_remaining_canary"')
anchor = '        validate_commands(pid, contract)\n'
prior = r'''
        original_version_action = 'act_c4b96e42976c47b9a69d1275dd2487e4'
        original_version = client.call('exec_command', {'operation':'exec_status','action_id':original_version_action})
        require(original_version.get('execution') == 'completed_exec_relay' and original_version.get('exit_code') == 0 and original_version.get('process_state') == 'completed', 'ORIGINAL_NODE_VERSION_JOB_NOT_COMPLETED')
        version_payload, version_proof = verified_receipt(connection, original_version, 'exec', args, contract, 'task_ce160f4b2026492685a363e3fa93918b', 1, 'electron-control-plane-exec-bridge', 'control_plane_exec')
        version_page = client.call('command_control', {'operation':'exec_output','action_id':original_version_action,'cursor':0,'max_bytes':65536})
        require(version_page.get('has_output') is True and version_page.get('truncated') is False and version_page.get('exit_code') == 0 and version_page.get('output') == '[stdout]\n'+version_payload['stdout']+'\n[stderr]\n'+version_payload['stderr'], 'ORIGINAL_NODE_VERSION_OUTPUT_NOT_VERIFIED')
        require(version_payload['stderr'].strip() == '', 'ORIGINAL_NODE_VERSION_STDERR')
        match = re.fullmatch(r'v([0-9]+)\.[0-9]+\.[0-9]+', version_payload['stdout'].strip())
        require(match is not None and int(match.group(1)) >= 22, 'ORIGINAL_NODE_VERSION_NOT_VERIFIED')
        outcome['proofs']['node_version'] = {'status':original_version,'receipt':version_proof,'stdout':version_payload['stdout'].strip(),'reused_original_job':True}
        outcome['prior_action_ids'] = {'node_version':original_version_action}
        emit('original_job_reobserved_verified', lane='node_version', stdout=version_payload['stdout'].strip(), action_reexecuted=False, **version_proof)
'''
assert source.count(anchor) == 1
source = source.replace(anchor, anchor + prior)
start = source.index('            output = page.get("output", "")')
end = source.index('            payload, proof = verified_receipt', start)
source = source[:start] + '''            output = page.get("output", "")
            payload, proof = verified_receipt(connection, executed, "exec", args, contract, task_id, lease_generation,
                                             "electron-control-plane-exec-bridge", "control_plane_exec")
            require(output == "[stdout]\\n"+payload["stdout"]+"\\n[stderr]\\n"+payload["stderr"] and payload["stderr"].strip() == "", "ORIGINAL_OUTPUT_STREAMS_NOT_VERIFIED")
            clean_output = payload["stdout"].strip()
            if lane == "node_cwd":
                require(clean_output == GUEST_CWD, "GUEST_WORKSPACE_NOT_VERIFIED")
            elif lane == "node_hash":
                require(clean_output == POSTIMAGE, "EXISTING_FINAL_FILE_HASH_NOT_VERIFIED")
            else:
                require(clean_output == DOTNET_VERSION, "DIRECT_DOTNET_VERSION_NOT_VERIFIED")
''' + source[end:]
# The second call is read-only and retains the existing lineage assertions.
source = source.replace('            proof["output_bytes"] = page["total_bytes"]\n', '            proof["output_bytes"] = page["total_bytes"]\n            proof["stdout"] = clean_output\n')
source = source.replace("version_payload['stdout']+'\\\\n[stderr]\\\\n'", "version_payload['stdout']+'\\n[stderr]\\n'")
source = source.replace("'[stdout]\\\\n'", "'[stdout]\\n'")
source = source.replace("r'v([0-9]+)\\\\.[0-9]+\\\\.[0-9]+'", "r'v([0-9]+)\\.[0-9]+\\.[0-9]+'");
compile(source, 'run-autocad-exec-remaining-canary-r9d.py', 'exec')
target = here / 'run-autocad-exec-remaining-canary-r9d.py'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
wrapper = (here / 'invoke-autocad-exec-only-canary-r9d.ps1').read_text(encoding='utf-8')
wrapper = wrapper.replace(old.name,target.name).replace('9d1903d588fddcd6c979c4c4f3e868c7156219c924717d8e6d502a1778ceb4d6',digest)
wrapper = wrapper.replace('autocad-exec-only-receipt-r9d-', 'autocad-exec-remaining-receipt-r9d-')
wrapper = wrapper.replace('autocad_exec_only_canary_ssh','autocad_exec_remaining_canary_ssh')
with (here / 'invoke-autocad-exec-remaining-canary-r9d.ps1').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(wrapper)
print(json.dumps({'script_sha256':digest,'prepared_only':True,'prior_node_version_not_reexecuted':True,'new_command_count':3}))
