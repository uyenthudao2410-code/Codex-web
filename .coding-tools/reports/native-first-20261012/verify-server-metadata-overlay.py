"""Focused execution relay and unchanged service-contract tests on exact overlay."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
receipt = json.loads((OUT / "server-overlay-preparation.json").read_text(encoding="utf-8"))
candidate = Path(receipt["candidate_release"])
sys.path.insert(0, str(candidate / "control-plane"))
suite = unittest.TestSuite()
for name in ("test_mcp_exec", "test_mcp_private_tunnel_service_facade"):
    spec = importlib.util.spec_from_file_location("overlay_" + name, ROOT / "control-plane/tests" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
proof = {"operation": "native_first_exact_server_overlay_validation", "candidate": str(candidate),
         "package_source_sha256": receipt["verification"]["package_source_sha256"],
         "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
         "passed": result.wasSuccessful(), "remote_mutations": False}
with (OUT / "server-overlay-validation.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(proof, handle, indent=2)
    handle.write("\n")
print(json.dumps(proof, separators=(",", ":")))
sys.exit(0 if result.wasSuccessful() else 1)
