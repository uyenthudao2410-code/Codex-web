from pathlib import Path
import base64
import hashlib
import json

root = Path(__file__).resolve().parent
source = (root / 'run-autocad-folder-access-canary-r9c.py').read_text(encoding='utf-8')
old_final = 'AUTOCAD_SHARED_MCP_WRITE_EXEC_20261012_R9C_OK\nstage=exact_patch'
new_final = old_final.replace('_R9C_', '_R9D_')
source = source.replace('mcp-access-smoke-20261012-r9c.txt', 'mcp-access-smoke-20261012-r9d.txt')
source = source.replace('_R9C_', '_R9D_').replace('autocad-folder-access-r9c-20261012:', 'autocad-folder-access-r9d-20261012:')
source = source.replace(base64.b64encode(old_final.encode()).decode(), base64.b64encode(new_final.encode()).decode())
source = source.replace(hashlib.sha256(old_final.encode()).hexdigest(), hashlib.sha256(new_final.encode()).hexdigest())
compile(source, 'run-autocad-folder-access-canary-r9d.py', 'exec')
digest = hashlib.sha256(source.encode()).hexdigest()
with (root / 'run-autocad-folder-access-canary-r9d.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source)
wrapper = (root / 'invoke-autocad-folder-access-canary-r9c.ps1').read_text(encoding='utf-8')
wrapper = wrapper.replace('run-autocad-folder-access-canary-r9c.py', 'run-autocad-folder-access-canary-r9d.py')
wrapper = wrapper.replace('mcp-access-smoke-20261012-r9c.txt', 'mcp-access-smoke-20261012-r9d.txt')
wrapper = wrapper.replace('autocad-folder-access-receipt-r9c-', 'autocad-folder-access-receipt-r9d-')
wrapper = wrapper.replace('8cf3c2244cf9dfb8f06c2abb59468c14153c199f2d15af987240873eff45e2bd', digest)
with (root / 'invoke-autocad-folder-access-canary-r9d.ps1').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(wrapper)
print(json.dumps({'prepared_only': True, 'target': 'mcp-access-smoke-20261012-r9d.txt',
                  'script_sha256': digest,
                  'expected_bytes': len(new_final.encode()), 'expected_sha256': hashlib.sha256(new_final.encode()).hexdigest()}))
