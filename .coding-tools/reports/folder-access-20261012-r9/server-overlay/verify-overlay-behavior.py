"""Exercise reviewed activation and historical negative cases against the exact overlay."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
receipt = json.loads((OUT / 'overlay-preparation-receipt.json').read_text())
candidate = Path(receipt['candidate_release'])
sys.path.insert(0, str(candidate / 'control-plane'))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'control-plane/tests' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


activation = load('test_node_workspace_activation')
store = load('test_store')
suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(activation),
    store.ControlPlaneStoreTests('test_scoped_pilot_retired_read_continuity_rejects_missing_fences_and_evidence'),
    store.ControlPlaneStoreTests('test_scoped_pilot_retired_read_continuity_rejects_target_scope_changes'),
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
proof = {'operation': 'exact_overlay_activation_behavior_validation', 'candidate_release': str(candidate),
    'package_source_sha256': receipt['verification']['package_source_sha256'],
    'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
    'passed': result.wasSuccessful(), 'remote_mutations': False}
(OUT / 'overlay-behavior-validation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof, separators=(',', ':')))
sys.exit(0 if result.wasSuccessful() else 1)
