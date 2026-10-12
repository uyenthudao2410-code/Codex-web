# r11 native correlation — root-owned live execution

This lane only prepares local observation helpers. It never runs the checker,
replays the patch, changes authority, calls SSH, or accepts a native RUN/WAVE.

## Before one new canary

Root runs `native-preflight.cjs` on the active packaged r11 profile. Supported
Recovery Host IPC identity observation and the canonical query-only census verify
the current native epoch/process/server/contract, baseline target/checker, zero
active canonical work, and unchanged old pending run/wave rows. Native runtime
lifecycle processes are allowed. Only an exclusive public evidence file is saved.

The public result supplies `native_preflight` fields and actual identity pins.
Root adds its emitted `receipt_sha256` to the canary pins and dispatches within
the canary helper's 60 second freshness gate. Preflight itself grants no authority.

## After terminal canary receipt

```powershell
python -B .coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r11\native-live-correlation\correlate_r11.py --receipt ABSOLUTE_PUBLIC_OBSERVE_JSON --pins ABSOLUTE_CANARY_PINS_JSON --output-receipt ABSOLUTE_NATIVE_STDOUT_READ_JSON
```

The receipt may be the exact helper public result or the root SSH transport
wrapper containing one `public_receipts` observe/cleanup result. The output
receipt is the `live-canary/native-output-read.cjs` authenticated query-only
capture wrapper. Its exact action/task/command/Job/RUN/WAVE/proof/runtime identity,
observation digest and completion time are compared with the correlated receipt
and ledger. Its stdout/stderr pages must use offset 0 and complete bounded
retained streams; stderr must be empty. It must be captured promptly:
ExecSession output retention is 300 seconds, unlike the durable Job and proof.
No captured stdout is emitted by this correlator, only digest/bytes/TAP counts.

The correlator opens only the real ledger through SQLite URI `mode=ro`, enables
`query_only`, holds one explicit read transaction, and closes the connection.
It never imports a Runtime/ledger constructor. It checks the exact fresh nonempty
32-hex RUN/WAVE, submitted node journal receipt, plan, postimage and checker,
durable Job terminal exit 0, initial-verification ProofLedger execution/cache
status, source binding, input/aggregate fingerprints, quiescence and preservation
of the historical pending row hashes. Source fingerprints ignore `.coding-tools`
as the product does. An exclusive allowlisted result is written in this directory.

`--output-receipt` may be omitted to preserve useful partial correlation before
the stdout capture arrives. That result explicitly lists
`NATIVE_TAP_OUTPUT_NOT_CAPTURED`; it never claims 4/4 from exit 0 alone.

Native semantic acceptance remains pending with
`NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE`. These helpers cannot close
that boundary or call the central Console verdict. A central MCP service trial
is not a genuine ChatWeb call.

## Offline checks

`python -B test_correlate_r11.py` uses only in-memory SQLite fixtures and a
temporary source fixture. Seven checks cover successful correlation/query-only
protection, wrong Job WAVE, old pending mutation, source fingerprint drift,
aggregate mismatch, exact TAP output/wrong command, and the public settled/native
journal boundary including rejection of unexpected raw fields. No live operation occurs.
