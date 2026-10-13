"""Run the affected server contract tests against the immutable overlay imports."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipt = json.loads((HERE / 'server-candidate-preparation.json').read_text(encoding='utf-8'))
candidate = Path(receipt['candidate_release'])
sys.path.insert(0, str(candidate / 'control-plane'))
import control_plane.http_api
import control_plane.store
require_path = str(candidate / 'control-plane/control_plane')
if not str(control_plane.http_api.__file__).startswith(require_path) or not str(control_plane.store.__file__).startswith(require_path):
    raise RuntimeError('IMMUTABLE_CANDIDATE_IMPORT_REQUIRED')
suite = unittest.TestSuite()
for name in ('test_node_workspace_activation', 'test_mcp_exec', 'test_mcp_private_tunnel_service_facade', 'test_store'):
    spec = importlib.util.spec_from_file_location('candidate_' + name, ROOT / 'control-plane/tests' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tests = unittest.defaultTestLoader.loadTestsFromModule(module)
    if name == 'test_store':
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(module.ControlPlaneStoreTests)
        tests = unittest.TestSuite(test for test in tests if test._testMethodName.startswith('test_scoped_pilot'))
    suite.addTests(tests)
result = unittest.TextTestRunner(verbosity=1).run(suite)
proof = {'operation': 'exact_parallel_server_candidate_validation', 'candidate': str(candidate),
    'package_source_sha256': receipt['verification']['package_source_sha256'], 'tests_run': result.testsRun,
    'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
    'actual_http_api_import': control_plane.http_api.__file__, 'actual_store_import': control_plane.store.__file__, 'remote_mutations': False}
with (HERE / 'server-candidate-validation.json').open('x', encoding='utf-8') as target:
    json.dump(proof, target, indent=2)
    target.write('\n')
print(json.dumps(proof))
sys.exit(0 if result.wasSuccessful() else 1)
