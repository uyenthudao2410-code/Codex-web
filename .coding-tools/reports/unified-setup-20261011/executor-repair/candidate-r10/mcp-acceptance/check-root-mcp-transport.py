"""Static and pure transport guards only: never invoke helper main or SSH."""
import copy
import hashlib
import json
from pathlib import Path
import runpy

BASE = Path(__file__).resolve().parent
path = BASE / "root-mcp-transport.py"
raw = path.read_bytes()
compile(raw, str(path), "exec")
scope = runpy.run_path(str(path), run_name="root_mcp_transport_static_checks")
compile(scope["REMOTE_CODE"], "root_mcp_remote_wrapper", "exec")
assert hashlib.sha256(scope["CANARY"].read_bytes()).hexdigest() == scope["CANARY_SHA"]
pins = {"service_instance_id": scope["SERVICE"], "context_id": scope["CONTEXT"], "pilot_id": scope["PILOT"],
    "requested_at_ms": scope["REQUESTED"], "expires_at_ms": scope["EXPIRES"], "activation_epoch_id": "activation-fixture-r10-current",
    "process_instance_id": "fixture-process", "server_instance_id": "fixture-server", "native_contract_sha256": "a" * 64,
    "rollout_receipt_sha256": "b" * 64, "native_observation_sha256": "c" * 64,
    "facade_contract": {"schema_version": 1, "profile": "workspace_context", "sha256": "d" * 64}}

class PublicPinFixture:
    parent = BASE
    def __init__(self, value):
        self.material = json.dumps(value).encode()
    def resolve(self, strict=True): return self
    def is_file(self): return True
    def is_symlink(self): return False
    def read_bytes(self): return self.material

scope["pins_bytes"](PublicPinFixture(pins))
cases = []
for name, mutation in (
    ("old_epoch", lambda row: row.update(activation_epoch_id="activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7")),
    ("different_context", lambda row: row.update(context_id="ctx_" + "f" * 32)),
    ("extended_window", lambda row: row.update(expires_at_ms=scope["EXPIRES"] + 1)),
    ("private_pin_field", lambda row: row.update(authorization="not-a-credential-fixture")),
):
    sample = copy.deepcopy(pins)
    mutation(sample)
    try: scope["pins_bytes"](PublicPinFixture(sample))
    except RuntimeError: cases.append({"case": name, "rejected": True})
    else: raise AssertionError(name)

scope["public_record"](b'{"phase":"root_mcp_transport_discovery","ok":true}')
for name, material in (
    ("private_stdout", b'{"phase":"r10_mcp_canary_terminal","stdout":"fixture"}'),
    ("nested_header", b'{"phase":"r10_mcp_canary_preflight","preflight":{"headers":{}}}'),
    ("nonpublic_phase", b'{"phase":"debug","token":"fixture"}'),
):
    try: scope["public_record"](material)
    except RuntimeError: cases.append({"case": name, "rejected": True})
    else: raise AssertionError(name)

result = {"kind": "root_mcp_transport_static_guard_proof", "helper_sha256": hashlib.sha256(raw).hexdigest(),
    "canary_sha256": scope["CANARY_SHA"], "local_and_remote_syntax": "passed", "positive_cases": 2,
    "negative_cases": cases, "helper_main_invoked": False, "ssh_invoked": False, "live_operations": False}
with (BASE / "root-mcp-transport-static-proof.json").open("x", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
print(json.dumps(result, separators=(",", ":")))
