'use strict';
// Static derivation only. Never opens the ledger, journal or live runtime.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const source = path.join(__dirname, '../../candidate-r13/canary-5h/correlate_r13_5h_source_identity.py');
const raw = fs.readFileSync(source);
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
if (sha(raw) !== '8dd49d77566f64ea846746af8b23455257cf8bf11b75fa2ab4ef176a060b4c76') throw new Error('PINNED_PRIOR_CORRELATOR_CHANGED');
let code = raw.toString('utf8');
function once(before, after) {
  if (code.split(before).length !== 2) throw new Error('EXACT_DERIVATION_NOT_UNIQUE');
  code = code.replace(before, after);
}
code = code.replaceAll('r13_5h', 'r14_same_window');
once('PRE = "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650"', 'PRE = "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e"');
once('POST = "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e"', 'POST = "0ae4bfe07e94d171e8885a464f3bf8f3e0d9b49a444b144b1aed2e4963ab4496"');
once('NAMES = [', 'SECOND_RUN = "fbaf4b0700d04794af4062671c1bcd2b"\nSECOND_WAVE = "e712eca9463e465fb1905264c998f50c"\nSECOND_HASHES = {"runs": "6a66aac3bf8d389938a0b4284b487378c180ce7bfca9cf1d5f754fc20077a2ca",\n                 "waves": "3d2c5310ba6e9d91d32ba09c3d2b191c722cc0fe550b25cba371650e360a2b4d"}\nNATIVE_SHA = "0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"\nNAMES = [');
once('    raw = path.read_bytes()\n    need(len(raw) <= 2 * 1024 * 1024, "INPUT_TOO_LARGE")', '    need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024 * 1024, "INPUT_UNSAFE_OR_TOO_LARGE")\n    raw = path.read_bytes()\n    need(len(raw) <= 2 * 1024 * 1024, "INPUT_TOO_LARGE")');
once('"bytes_written": 414', '"bytes_written": 406');
once('and run != OLD_RUN and wave != OLD_WAVE', 'and run not in {OLD_RUN, SECOND_RUN} and wave not in {OLD_WAVE, SECOND_WAVE}');
once('    run, wave, proof = summary["run_id"], summary["wave_id"], summary["initial_verification"]', '    second = {}\n    for table, column, value in (("runs", "run_id", SECOND_RUN), ("waves", "wave_id", SECOND_WAVE)):\n        rows = connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (value,)).fetchall()\n        need(len(rows) == 1, "SECOND_PENDING_RECORD_MISSING")\n        second[table] = sha(canonical(dict(rows[0]), ascii=True))\n        need(second[table] == SECOND_HASHES[table], "SECOND_PENDING_RECORD_CHANGED")\n    run, wave, proof = summary["run_id"], summary["wave_id"], summary["initial_verification"]');
once('"old_pending_record_sha256": old, "old_pending_records_unchanged": True', '"old_pending_record_sha256": old, "second_pending_record_sha256": second, "old_pending_records_unchanged": True');
once('"runtime_identity", "stdout", "stderr", "tap", "remote_mutation"}', '"runtime_identity", "proof_status", "native_command_status", "native_exit_code", "stdout", "stderr", "tap", "remote_mutation"}');
once('and value["tool"] == "command_control" and value["action"] == "read" and value["remote_mutation"] is False,', 'and value["tool"] == "command_control" and value["action"] == "read" and value["remote_mutation"] is False\n         and value["proof_status"] == "passed" and value["native_exit_code"] == 0\n         and value["native_command_status"] in {"exited", "reconciled_terminal"},');
once('    parser.add_argument("--output-receipt", type=Path)', '    parser.add_argument("--receipt-sha256", required=True)\n    parser.add_argument("--pins-sha256", required=True)\n    parser.add_argument("--output-receipt", type=Path)\n    parser.add_argument("--output-receipt-sha256")');
once('    family, summary = public_result(receipt)', '    need(receipt_sha == args.receipt_sha256 and pins_sha == args.pins_sha256, "EXACT_PUBLIC_INPUT_DIGEST_REQUIRED")\n    family, summary = public_result(receipt)');
once('and pins["expires_at_ms"] - pins["requested_at_ms"] == 18000000, "AUTHORITY_PLAN_PINS_INVALID")', 'and pins["requested_at_ms"] == 1791758571067 and pins["expires_at_ms"] == 1791776571067\n         and pins["context_id"] == "ctx_1e7e2fec6f0e43018db7a51c6980e5c2"\n         and re.fullmatch(r"pilot_[a-f0-9]{32}", str(pins["pilot_id"]))\n         and pins["pilot_id"] != "pilot_b1cb26c319fb489aae24d3b746318447"\n         and re.fullmatch(r"call_[A-Za-z0-9_-]+", str(pins["approval_id"]))\n         and pins["approval_id"] not in {"call_a60e931056bd402b997c6c10b0796d81", "call_1KzUkF0gMn6uVpHd3QisTzXF"}, "AUTHORITY_PLAN_PINS_INVALID")');
once('and re.fullmatch(r"[a-f0-9]{64}", str(pins["native_tool_contract_sha256"])), "RUNTIME_PINS_INVALID")', 'and pins["native_tool_contract_sha256"] == NATIVE_SHA\n         and pins["contract_version"] == "sha256:" + NATIVE_SHA, "RUNTIME_PINS_INVALID")');
once('(ROOT / TARGET).stat().st_size == 414', '(ROOT / TARGET).stat().st_size == 406');
once('        output_value, output_sha = load(args.output_receipt)', '        output_value, output_sha = load(args.output_receipt)\n        need(output_sha == args.output_receipt_sha256, "EXACT_OUTPUT_RECEIPT_DIGEST_REQUIRED")');
once('            "strongest_proof": result["strongest_proof"], "remaining_gaps": result["remaining_gaps"]}', '            "strongest_proof": result["strongest_proof"], "remaining_gaps": result["remaining_gaps"],\n            "command_id": evidence["command_id"], "job_id": evidence["job_id"], "completed_at_ms": evidence["completed_at_ms"]}');
const destination = path.join(__dirname, 'correlate_r14_same_window.py');
fs.writeFileSync(destination, code, { flag: 'wx' });
process.stdout.write(JSON.stringify({ ok: true, prepared_path: destination, sha256: sha(Buffer.from(code)),
  source_sha256: sha(raw), runtime_contacted: false, credentials_read: false, ledger_read: false, checker_executed: false }) + '\n');
