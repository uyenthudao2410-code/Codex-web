"""Create a focused multi-target revision of the prepared single-use canary."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'native-first-20261012/canary'
OUT = HERE / 'canary'
OUT.mkdir(exist_ok=True)

def change(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('CANARY_SOURCE_ANCHOR_DRIFT')
    return source.replace(old, new)

source = (BASE / 'run-native-first-canary.py').read_text(encoding='utf-8')
source = change(source,
    'rows = connection.execute("SELECT * FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?", (now,)).fetchall()',
    'rows = connection.execute("SELECT * FROM scoped_pilot_decisions WHERE principal_id=? AND binding_id=? AND device_id=? AND workspace_id=? AND workspace_generation=? AND revoked_at_ms IS NULL AND expires_at_ms>?", (args.principal_id, args.binding_id, args.device_id, args.workspace_id, args.workspace_generation, now)).fetchall()')
source = change(source,
    'require(inventory.get("principal_id") == args.principal_id and len(inventory.get("targets", [])) == 1, "SHARED_MCP_INVENTORY_NOT_EXACT")\n    target = inventory["targets"][0]',
    'require(inventory.get("principal_id") == args.principal_id, "SHARED_MCP_PRINCIPAL_CHANGED")\n    matches = [item for item in inventory.get("targets", []) if item.get("binding_id") == args.binding_id]\n    require(len(matches) == 1, "SHARED_MCP_INVENTORY_NOT_EXACT")\n    target = matches[0]')
source = change(source, 'attempt = "native-first-20261012:" + args.attempt_id', 'attempt = "parallel-native-first-20261012:" + args.attempt_id')
files = {'run-native-first-canary.py': source.encode()}
for name in ('test-native-first-canary.py', 'prepare-native-first-fixtures.py', 'invoke-native-first-canary.ps1'):
    files[name] = (BASE / name).read_bytes()
for name, content in files.items():
    with (OUT / name).open('xb') as target:
        target.write(content)
receipt = {'operation': 'multiworkspace_canary_preparation', 'live_dispatch': False,
    'changes': ['exact target pilot query', 'exact binding selection from multi-target inventory', 'fresh idempotency namespace'],
    'files': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}
with (OUT / 'harness-preparation.json').open('x', encoding='utf-8') as target:
    json.dump(receipt, target, indent=2)
    target.write('\n')
print(json.dumps(receipt))
