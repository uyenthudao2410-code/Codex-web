"""Record Windows direct-loader delta against actual serving Ubuntu source, locally."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = PARENT.parents[2]
BASE = PARENT / 'codex-control-plane-parallel-native-1012-f7acd9ec4ba1'
READINESS = PARENT / 'server-readiness-r2-preparation.json'
PATH = 'control-plane/control_plane/node_agent.py'
EXPECTED_NEW = 'bee27651ef1fba03f6f6c52dd1a93fe671f07d7b73b0402118ead88c97f9dffe'


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(content):
    return hashlib.sha256(content).hexdigest()


readiness = json.loads(READINESS.read_text(encoding='utf-8'))
require(readiness.get('ok') is True and readiness.get('service_stable') is True,
        'SANITIZED_SERVING_OBSERVATION_REQUIRED')
old = (BASE / PATH).read_bytes()
new = (ROOT / PATH).read_bytes()
observed = readiness['serving_source']
require(sha(old) == observed['python_files_sha256']['node_agent.py'], 'SERVING_LOCAL_BASELINE_DRIFT')
require(sha(new) == EXPECTED_NEW, 'FROZEN_DIRECT_LOADER_SOURCE_REQUIRED')
old_tree = ast.parse(old, filename='serving-node-agent')
new_tree = ast.parse(new, filename='windows-r3-node-agent')
old_branch = next(node for node in old_tree.body if isinstance(node, ast.If)
                  and isinstance(node.test, ast.Name) and node.test.id == '__package__')
new_branch = next(node for node in new_tree.body if isinstance(node, ast.If)
                  and isinstance(node.test, ast.Name) and node.test.id == '__package__')
require(ast.dump(ast.Module(body=old_branch.body, type_ignores=[]))
        == ast.dump(ast.Module(body=new_branch.body, type_ignores=[])),
        'PACKAGE_IMPORT_BRANCH_CHANGED')
# Replace only the direct-file else branch with an empty branch for AST equality;
# every other statement, public interface and package import must remain identical.
old_branch.orelse = []
new_branch.orelse = []
require(ast.dump(old_tree) == ast.dump(new_tree), 'DELTA_EXCEEDS_DIRECT_FILE_LOADER')
launcher = (BASE / 'deploy/control-plane-launcher.sh').read_text(encoding='utf-8')
entry = (BASE / 'control-plane/control_plane/__main__.py').read_text(encoding='utf-8')
http = (BASE / 'control-plane/control_plane/http_api.py').read_text(encoding='utf-8')
renewal = (BASE / 'deploy/control-plane-authority-renewal.py').read_text(encoding='utf-8')
require('exec /usr/bin/python3 -B -m control_plane' in launcher
        and 'from .http_api import serve_from_environment' in entry,
        'SERVING_PACKAGE_ENTRYPOINT_CHANGED')
require('import node_agent' not in http and 'import node_agent' not in renewal
        and 'import control_plane.node_agent' not in http
        and 'import control_plane.node_agent' not in renewal,
        'SERVING_DIRECT_LOADER_DEPENDENCY_PRESENT')
(HERE / 'windows-r3-direct-loader.diff').write_text(''.join(difflib.unified_diff(
    old.decode().splitlines(True), new.decode().splitlines(True),
    fromfile='ubuntu-serving/' + PATH, tofile='windows-r3/' + PATH)), encoding='utf-8')
receipt = {
    'schema_version': 1, 'operation': 'windows_r3_direct_loader_delta_against_serving_ubuntu',
    'ok': True, 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
    'observed_git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'readiness_sha256': sha(READINESS.read_bytes()),
    'readiness_captured_at_ms': readiness['capture_completed_at_ms'],
    'serving_service_pid': readiness['service_pid'],
    'serving_release_root': observed['serving_release_root'],
    'serving_package_source_sha256': observed['package_source_sha256'],
    'serving_node_agent_sha256': sha(old),
    'windows_r3_node_agent_raw_sha256': sha(new),
    'package_import_branch_unchanged': True,
    'all_ast_except_direct_file_else_unchanged': True,
    'serving_http_entrypoint': 'python3 -B -m control_plane -> .http_api.serve_from_environment',
    'serving_http_and_renewal_do_not_import_node_agent': True,
    'contract': readiness['tool_contract'],
    'ubuntu_alignment_deployment_required': False,
    'ubuntu_alignment_deployment_performed': False,
    'external_mutations_performed': False,
    'canary_pin_rule': 'Pin actual serving node_agent hash separately from the Windows packaged direct-loader hash; never claim byte parity between them.',
}
with (HERE / 'windows-r3-source-delta-receipt.json').open('x', encoding='utf-8', newline='\n') as target:
    json.dump(receipt, target, indent=2)
    target.write('\n')
print(json.dumps({'ok': True, 'serving_service_pid': readiness['service_pid'],
                  'direct_loader_only': True, 'ubuntu_restart_required': False}))
