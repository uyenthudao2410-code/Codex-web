'use strict';
const fs = require('node:fs'), path = require('node:path');
let s = fs.readFileSync(path.join(__dirname, '../../candidate-r13/canary-5h/root-canary-ssh.py'), 'utf8')
  .replaceAll('\r\n', '\n').replaceAll('r13_5h', 'r14_same_window').replaceAll('R13_5H', 'R14_SAME_WINDOW');
s = s.replace('COMMON_SOURCE = HERE.parent / "authority-5h/r11_common.py"', 'COMMON_SOURCE = HERE.parent.parent / "candidate-r13/authority-5h/r11_common.py"')
  .replace('2bd2bed8d9389a9381b49c92eeca6864cd6230db16d3dcff1822742f062888b1', 'f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324')
  .replace('e9351a360eaa7c016514015a27ea06c762604e12c2a5ca436a550abbf09f29ff', 'a618711528b418db77a901a5b83537bde2d511618ef630ab22670a2e6579625d');
const start = s.indexOf('    reopened = [row for row in rows'), end = s.indexOf('    _, _, frozen =', start);
if (start < 0 || end < 0) throw new Error('TRANSPORT_REOPEN_ANCHOR_MISSING');
s = s.slice(0, start) + `    reopened = [row for row in rows if isinstance(row, dict) and row.get("ok") is True
                and row.get("phase") == "r14_same_window_read_only_observation" and row.get("next_phase") == "intake_reopened"]
    require(len(reopened) == 1, "EXACT_R14_REOPEN_RECEIPT_REQUIRED")
    receipt = reopened[0]
    target = {"host": "100.116.112.22", "service": "codex-control-plane.service", "admission": "scoped_pilot",
        "source_revision": "9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c",
        "binding_id": "bind_3e05bf64cb3e4bab93d930ae1692bebb", "device_id": "72ceec2d-e3f2-472f-8e3c-99fffe053035",
        "workspace_id": "workspace_dda1d78e9a21402aa6213f72af64f788", "workspace_generation": "generation_c2f13e8d02344cf6a38a3f42ecfa59b6",
        "root": r"E:\\Github\\Tools-Codex-web", "profile": "web-mcp-assistant", "prior_pilot_revoked": True,
        "replacement_pilot_same_principal": True, "replacement_pilot_same_binding": True,
        "replacement_pilot_expires_at_ms": 1791776571067, "prior_pilot_id": "pilot_b1cb26c319fb489aae24d3b746318447"}
    require(all(receipt.get(field) == value for field, value in target.items())
            and re.fullmatch(r"call_[A-Za-z0-9_-]+", str(pins.get("approval_id")))
            and pins["approval_id"] not in {"call_a60e931056bd402b997c6c10b0796d81", "call_1KzUkF0gMn6uVpHd3QisTzXF"}
            and pins.get("context_id") == "ctx_1e7e2fec6f0e43018db7a51c6980e5c2"
            and pins.get("requested_at_ms") == 1791758571067 and pins.get("expires_at_ms") == 1791776571067
            and pins.get("pilot_id") != "pilot_b1cb26c319fb489aae24d3b746318447"
            and all(receipt.get(field) == pins.get(field) for field in
                    ("requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id", "approval_id",
                     "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"))
            and re.fullmatch(r"[a-f0-9]{64}", str(pins.get("authority_marker_sha256")))
            and receipt.get("next_marker_sha256") == pins["authority_marker_sha256"], "EXACT_R14_SAME_WINDOW_PINS_REQUIRED")
` + s.slice(end);
fs.writeFileSync(path.join(__dirname, 'root-canary-ssh.py'), s, { flag: 'wx' });
process.stdout.write(JSON.stringify({ generated: 'root-canary-ssh.py', remote_mutated: false }) + '\n');
