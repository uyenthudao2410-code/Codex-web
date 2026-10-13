from pathlib import Path
import base64
import hashlib
import json

root = Path(__file__).resolve().parent
source = (root / 'run-autocad-folder-access-canary-r9.py').read_text(encoding='utf-8')
old_final = 'AUTOCAD_SHARED_MCP_WRITE_EXEC_20261012_R9_OK\nstage=exact_patch'
new_final = old_final.replace('_R9_', '_R9C_')
source = source.replace('mcp-access-smoke-20261012-r9.txt', 'mcp-access-smoke-20261012-r9c.txt')
source = source.replace('_R9_', '_R9C_').replace('autocad-folder-access-r9-20261012:', 'autocad-folder-access-r9c-20261012:')
source = source.replace(base64.b64encode(old_final.encode()).decode(), base64.b64encode(new_final.encode()).decode())
source = source.replace(hashlib.sha256(old_final.encode()).hexdigest(), hashlib.sha256(new_final.encode()).hexdigest())
compile(source, 'run-autocad-folder-access-canary-r9c.py', 'exec')
with (root / 'run-autocad-folder-access-canary-r9c.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source)
wrapper = (root / 'invoke-autocad-folder-access-canary-r9.ps1').read_text(encoding='utf-8')
wrapper = wrapper.replace('run-autocad-folder-access-canary-r9.py', 'run-autocad-folder-access-canary-r9c.py')
wrapper = wrapper.replace('mcp-access-smoke-20261012-r9.txt', 'mcp-access-smoke-20261012-r9c.txt')
wrapper = wrapper.replace('autocad-folder-access-receipt-r9-', 'autocad-folder-access-receipt-r9c-')
with (root / 'invoke-autocad-folder-access-canary-r9c.ps1').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(wrapper)
print(json.dumps({'prepared_only': True, 'target': 'mcp-access-smoke-20261012-r9c.txt',
                  'script_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'expected_bytes': len(new_final.encode()), 'expected_sha256': hashlib.sha256(new_final.encode()).hexdigest()}))
