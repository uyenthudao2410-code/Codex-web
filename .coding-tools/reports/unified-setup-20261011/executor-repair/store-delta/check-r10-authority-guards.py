"""Exercise actual helper main guards with read-only synthetic observations.

No SSH, server, service, SQLite or file read by the helper occurs. The fake
owner-operation lock rejects any attempt to reach a mutation boundary.
"""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


out = Path(__file__).resolve().parent
source = (out / "ubuntu-r10-store-authority-v2-pinned.py").read_bytes()
manifest = json.loads((out / "r10-authority-helper-v2-pinned-manifest.json").read_bytes())
assert hashlib.sha256(source).hexdigest() == manifest["helper_sha256"]
tree = ast.parse(source)
nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
         and node.name in {"GuardFailure", "require", "main"}]
assert len(nodes) == 3
namespace = {"argparse": argparse, "__doc__": "Synthetic guard exercise only", "DEVICE": manifest["device_id"],
             "PREDECESSOR_EPOCH": manifest["predecessor_epoch"]}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "frozen_authority_main", "exec"), namespace)


def forbidden(*_args, **_kwargs):
    raise AssertionError("guard failed to reject before mutation/configuration boundary")


namespace["os"] = SimpleNamespace(open=forbidden)
namespace["protected_file"] = forbidden
namespace["api"] = forbidden
observed_at = 1791720500000
fresh_node = {"device_id": manifest["device_id"], "activation_epoch": manifest["predecessor_epoch"],
              "last_seen_at_ms": observed_at - 1000}
common = ["--execute", "--expected-service-instance", "cp_new_test", "--expected-state-sha256", "unused"]
cases = [
    ("missing_operator_approval", ["close", *common], fresh_node, "EXPLICIT_R10_STORE_60M_OWNER_APPROVAL_REQUIRED"),
    ("wrong_service_instance", ["close", "--execute", "--operator-approved", "--expected-service-instance", "cp_wrong"],
     fresh_node, "EXPECTED_SERVICE_INSTANCE_REQUIRED"),
    ("wrong_predecessor_epoch", ["close", *common, "--operator-approved", "--expected-activation-epoch", "wrong-epoch"],
     fresh_node, "EXPECTED_FRESH_R9_PREDECESSOR_REQUIRED_FOR_AUTHORITY_PREPARATION"),
    ("stale_predecessor_heartbeat", ["renew", *common, "--operator-approved", "--expected-activation-epoch", manifest["predecessor_epoch"]],
     {**fresh_node, "last_seen_at_ms": observed_at - 60000}, "EXPECTED_FRESH_R9_PREDECESSOR_REQUIRED_FOR_AUTHORITY_PREPARATION"),
    ("reopen_rejects_predecessor", ["reopen", *common, "--operator-approved", "--expected-activation-epoch", manifest["predecessor_epoch"]],
     fresh_node, "NEW_R10_ACTIVATION_REQUIRED_FOR_REOPEN"),
]
results = []
original_argv = sys.argv
try:
    for name, arguments, node, expected in cases:
        namespace["inspect"] = lambda current=node: ("", "", None, {"service_instance_id": "cp_new_test"}, {},
                                                     {"observed_at_ms": observed_at, "nodes": [current]}, {})
        sys.argv = ["synthetic-helper", *arguments]
        try:
            namespace["main"]()
        except namespace["GuardFailure"] as error:
            assert error.code == expected, (name, error.code)
            results.append({"name": name, "result": "pass", "guard_code": error.code})
        else:
            raise AssertionError(name + " unexpectedly passed")
finally:
    sys.argv = original_argv
receipt = {"operation": "r10_authority_local_negative_guard_verification", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
           "helper_sha256": manifest["helper_sha256"], "passed": len(results), "failed": 0, "cases": results,
           "remote_execution": False, "real_mutation_boundary_reached": False}
with (out / "r10-authority-guard-verification.json").open("xb") as handle:
    handle.write((json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
print(json.dumps(receipt, sort_keys=True, indent=2))
