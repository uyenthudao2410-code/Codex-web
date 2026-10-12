# Local helper preparation checkpoint

Observed repository: `E:\Github\Tools-Codex-web`, branch `main`, HEAD
`2c554f59cb7b8ffc86ce5e0e28076c792777642f`. Existing product/runtime evidence
changes were preserved. Ownership of this wave is only this new `live-canary`
directory. No product source, fixture baseline, frozen packet, old RUN or old WAVE
was changed by this wave.

Prepared a compact fixed-common helper, exact no-newline patch envelope, protected
pin template, root binary SSH staging/invocation, root credential-only retained
output reader, operation instructions, offline tests and artifact manifest.

Validation completed locally:

- `r11_mcp_canary.py stage`: PASS; target still exact preimage, checker unchanged,
  one-condition postimage, patch/plan/checker digests match the immutable packet.
- `test_r11_mcp_canary.py`: **16/16 PASS** in 0.023 seconds. Tests use the actual
  standing façade schema and offline mocked transport only. They cover contract
  mismatch, extra target, internal expiry rejection, immutable no-replay marker,
  first-effect response loss, epoch/window drift, receipt/digest/proof validation,
  failed proof without invented Job, raw secret redaction and unknown-effect gate.
  Standing policy telemetry is verified as a fresh typed TTL of at most 60s;
  the exact 60m context/pilot authority is independently enforced. Expired TTL,
  expired exact context and wrong epoch are negative cases.
- `test_root_canary_ssh.py`: **6/6 PASS**, with all SSH subprocesses mocked;
  verifies binary transport, fixed source pin, local exclusive intent before
  uncertainty, no replay and fixed-pins read-only observation.
- `node --test native-output-read.test.cjs`: **4/4 PASS**, pure reader validators;
  exact command/stream, full retention, secret rejection and exact fixture TAP.

No SSH, live API/MCP call, grant, renewal, runtime/service start/stop, native
acceptance, central verdict, live patch, live Job, commit, push or release occurred
in this wave. All local validation commands exited; no background Job was started.

Remaining: root completes Windows r11 activation and exact authority renewal,
fills/stages fresh pins, runs read-only preflight, executes one dispatch, observes
the same action, verifies native Job/TAP4/4/ProofLedger source binding locally, then
cleans up the settled central task/writer. Genuine native semantic acceptance is
still separately pending: `NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE`.

Next action is root-controlled staging/preflight; these offline results do not
claim live central/native end-to-end acceptance.
