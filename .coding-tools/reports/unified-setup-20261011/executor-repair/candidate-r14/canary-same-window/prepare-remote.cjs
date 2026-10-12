'use strict';
// Derive one explicit same-window canary from retained r13 helper. Static files only.
const fs = require('node:fs'), path = require('node:path');
const preparation = JSON.parse(fs.readFileSync(path.join(__dirname, 'static-preparation.json')));
let s = fs.readFileSync(path.join(__dirname, '../../candidate-r13/canary-5h/r13_5h_mcp_canary.py'), 'utf8')
  .replaceAll('\r\n', '\n').replaceAll('r13_5h', 'r14_same_window');
s = s.replace('PRE = "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650"', 'PRE = "' + preparation.existing_preimage_sha256 + '"')
  .replace('POST = "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e"', 'POST = "' + preparation.proposed_postimage_sha256 + '"')
  .replace('PATCH = "77f2c282c91f3627e721d0d68bf1fa821bad21575ec136204353894b18ce5e4a"', 'PATCH = "' + preparation.patch_sha256 + '"')
  .replaceAll('len(post) == 414', 'len(post) == 406').replaceAll('"bytes_written": 414', '"bytes_written": 406')
  .replace('NEXT_OPERATION_DIR = Path("/home/svhome/.local/state/codex-control-plane/owner-operations/r13-initial-verification-5h")', 'NEXT_OPERATION_DIR = Path("/home/svhome/.local/state/codex-control-plane/owner-operations/r14-same-window-activation")')
  .replace('NEXT_AUTHORITY_MARKER = NEXT_OPERATION_DIR / "authority-renewal-public.json"', 'NEXT_AUTHORITY_MARKER = NEXT_OPERATION_DIR / "authority-transition-public.json"')
  .replace('NEXT_OPERATION = "owner_approved_r13_initial_verification_5h"', 'NEXT_OPERATION = "owner_approved_r14_same_window_activation"');
const start = s.indexOf('def pins_input(common):'), end = s.indexOf('\ndef authority_guard(', start);
if (start < 0 || end < 0) throw new Error('EXACT_CANARY_GUARD_ANCHOR_MISSING');
s = s.slice(0, start) + `def pins_input(common):
    global _prior_marker_path, _prior_marker_sha256
    pins = private_json(HERE / "pins.json")
    expected = {"requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id",
                "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version",
                "native_tool_contract_sha256", "native_preflight", "approval_id", "authority_receipt_sha256", "authority_marker_sha256"}
    require(set(pins) == expected, "PINS_FIELDS_INVALID")
    require(all(isinstance(pins[field], str) and 1 <= len(pins[field]) <= 128 for field in
                ("context_id", "pilot_id", "service_instance_id", "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version")), "PINS_IDENTITY_INVALID")
    require(re.fullmatch(r"call_[A-Za-z0-9_-]+", str(pins["approval_id"]))
            and pins["approval_id"] not in {"call_a60e931056bd402b997c6c10b0796d81", "call_1KzUkF0gMn6uVpHd3QisTzXF"}, "SEPARATE_R14_APPROVAL_REQUIRED")
    require(pins["context_id"] == "ctx_1e7e2fec6f0e43018db7a51c6980e5c2"
            and pins["requested_at_ms"] == 1791758571067 and pins["expires_at_ms"] == 1791776571067
            and re.fullmatch(r"pilot_[a-f0-9]{32}", str(pins["pilot_id"]))
            and pins["pilot_id"] != "pilot_b1cb26c319fb489aae24d3b746318447", "EXACT_EXISTING_WINDOW_REPLACEMENT_REQUIRED")
    require(all(re.fullmatch(r"[a-f0-9]{64}", str(pins[field])) for field in ("authority_receipt_sha256", "authority_marker_sha256")), "AUTHORITY_DIGEST_INVALID")
    receipt_path = HERE / "authority-receipt.json"
    require(sha(common.protected_file(receipt_path)) == pins["authority_receipt_sha256"], "AUTHORITY_RECEIPT_HASH_CHANGED")
    wrapper = private_json(receipt_path)
    rows = wrapper.get("public_receipts", [wrapper])
    receipt_rows = [row for row in rows if isinstance(row, dict) and row.get("ok") is True
                    and row.get("phase") == "r14_same_window_read_only_observation" and row.get("next_phase") == "intake_reopened"]
    require(len(receipt_rows) == 1, "EXACT_R14_REOPEN_OBSERVATION_REQUIRED")
    receipt = receipt_rows[0]
    authority_bytes = common.protected_file(NEXT_AUTHORITY_MARKER)
    require(sha(authority_bytes) == pins["authority_marker_sha256"], "R14_MARKER_HASH_CHANGED")
    authority = private_json(NEXT_AUTHORITY_MARKER)
    require(authority.get("phase") == "intake_reopened" and authority.get("operation") == NEXT_OPERATION
            and authority.get("approval_id") == pins["approval_id"] and authority.get("authority_approval_id") == "call_a60e931056bd402b997c6c10b0796d81", "R14_MARKER_APPROVAL_OR_PHASE_CHANGED")
    target = {"binding_id": common.BINDING, "principal_id": common.PRINCIPAL, "device_id": common.DEVICE,
              "workspace_id": common.WORKSPACE, "workspace_generation": common.GENERATION,
              "root": common.LOCAL_ROOT, "profile": common.LOCAL_PROFILE, "source_revision": common.REVISION}
    require(all(authority.get(k) == v for k,v in target.items()) and all(receipt.get(k) == v for k,v in target.items()), "R14_AUTHORITY_TARGET_CHANGED")
    require(receipt.get("admission") == "scoped_pilot" and receipt.get("prior_pilot_revoked") is True
            and receipt.get("prior_pilot_id") == "pilot_b1cb26c319fb489aae24d3b746318447"
            and receipt.get("replacement_pilot_same_principal") is True and receipt.get("replacement_pilot_same_binding") is True
            and receipt.get("replacement_pilot_expires_at_ms") == 1791776571067
            and receipt.get("approved_window_covered") is True and receipt.get("grant_expires_at_ms", 0) >= 1791776571067,
            "EXACT_REOPENED_SAME_WINDOW_SCOPE_REQUIRED")
    for field in ("requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id",
                  "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"):
        require(authority.get(field) == pins[field] == receipt.get(field), "R14_AUTHORITY_NATIVE_PIN_MISMATCH")
    require(pins["native_tool_contract_sha256"] == NATIVE_TOOL_SHA256 and pins["contract_version"] == "sha256:" + NATIVE_TOOL_SHA256, "R14_NATIVE_CONTRACT_NOT_PINNED")
    _prior_marker_path, _prior_marker_sha256 = NEXT_AUTHORITY_MARKER, pins["authority_marker_sha256"]
    return pins

` + s.slice(end);
s = s.replace('"old_run_sha256", "old_wave_sha256", "no_active_jobs", "receipt_sha256"}', '"old_run_sha256", "old_wave_sha256", "second_old_run_sha256", "second_old_wave_sha256", "cold_sandbox", "no_active_jobs", "receipt_sha256"}')
  .replace('and native["old_wave_sha256"] == OLD_WAVE_SHA and native["no_active_jobs"] is True', 'and native["old_wave_sha256"] == OLD_WAVE_SHA and native["second_old_run_sha256"] == "6a66aac3bf8d389938a0b4284b487378c180ce7bfca9cf1d5f754fc20077a2ca"\n                and native["second_old_wave_sha256"] == "3d2c5310ba6e9d91d32ba09c3d2b191c722cc0fe550b25cba371650e360a2b4d" and native["cold_sandbox"] is True and native["no_active_jobs"] is True')
  .replace('and payload["run_id"] != OLD_RUN and payload["wave_id"] != OLD_WAVE', 'and payload["run_id"] not in {OLD_RUN, "fbaf4b0700d04794af4062671c1bcd2b"} and payload["wave_id"] not in {OLD_WAVE, "e712eca9463e465fb1905264c998f50c"}');
fs.writeFileSync(path.join(__dirname, 'r14_same_window_mcp_canary.py'), s, { flag: 'wx' });
process.stdout.write(JSON.stringify({ generated: 'r14_same_window_mcp_canary.py', runtime_contacted: false, fixture_mutated: false }) + '\n');
