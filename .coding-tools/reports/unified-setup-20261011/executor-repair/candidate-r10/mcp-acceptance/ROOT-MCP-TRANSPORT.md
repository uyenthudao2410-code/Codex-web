# Reviewed root MCP transport

Prepared/static only. No live SSH, MCP, runtime, task/Job, service or authority operation was performed by the preparing agent.

Helper `root-mcp-transport.py` SHA-256:
`a081b293cd1e33fbc4c53f86ed52fe2c9c2ce53cb6b6797c4fee1b615eaf5d19`.

Frozen canary v2 SHA-256:
`54f8ee88889e60437c7831410aae7845b2481401ce3f73bf7daa33a77e3ea047`.

## Root use

Run with Python and argv. The pin JSON must reside in this `mcp-acceptance` directory and contain only the public reviewed schema documented in `README-v2.md`.

```powershell
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/root-mcp-transport.py stage
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/root-mcp-transport.py discover
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/root-mcp-transport.py preflight --pins-file <ABSOLUTE_PUBLIC_PIN_FILE> --mode cold
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/root-mcp-transport.py execute --pins-file <SAME_PUBLIC_PIN_FILE> --mode cold --root-execute --expected-state-sha256 <JUST_REVIEWED_PREFLIGHT_HASH>
```

Warm uses a fresh public pin/native observation and its own reviewed preflight hash. The underlying canary requires the exact successful cold attempt before warm. Continue observing the existing local command when execution takes time; never reinvoke execute as polling or recovery.

Stage writes exact binary bytes only to the already existing private directory:
`/home/svhome/.local/lib/codex-control-plane/incoming/r10-approved-20261011T123342Z/r10-mcp-canary-v2.py`.
The directory must be the current owner's real path with mode 0700; staged file must be owned by the same user with mode 0600. A present file must match exact bytes; there is no replacement. Every discovery/preflight/execution rechecks staged file SHA before loading it.

Discovery reuses frozen canary `mcp_credentials` and `call` with inventory only. The retained public projection contains facade tool contract and exactly the target binding/presence/readiness/policy state. Authorization/header material stays in protected server files and process memory. Neither discovery nor the local wrapper emits configuration, credentials, raw MCP response or stderr.

## Fixed authorization and evidence

The helper is specific to the approved Store395 service instance, exact binding, standing context/pilot and **19:48:18.491–20:48:18.491 +07:00** window. It refuses a different context/pilot/window or old r9 epoch. The frozen canary performs actual service/source/grant/authority/ready-node/task/exec admission; transport does not replace those checks or renew authority.

Each invocation creates a new `transport-<action>-<mode-if-present>-<UTC timestamp>.jsonl` with exclusive creation. Verified public remote stdout is streamed as exact bytes; transport metadata is added as public JSON lines. The sealed evidence path/hash is emitted at completion. SSH stderr goes to DEVNULL. Unknown/nonpublic output is withheld and classified for root reconciliation. There is no automatic retry or raw exception output.

Before execute, an exclusive `transport-execution-once-<epoch/context/pilot/mode digest>.json` marker records the attempt. A response loss or interrupted transport cannot lead to another invocation of that mode through this helper. Root must reconcile the original task/action without replay, stop or automatic cleanup. Preflight/stage/discovery are separate explicit actions.

`check-root-mcp-transport.py` compiles both local and remote wrapper syntax and checks two positive/seven negative pure cases (old epoch, changed context/window, extra private pin field, private stdout/header and nonpublic phase). `root-mcp-transport-static-proof.json` records their pass; helper main and SSH were not invoked. Existing canary, source, package, runtime and other workers' changes remain untouched.

Native Job correlation remains a required separate acceptance gate using the existing `verify-r10-native-job.py`. A successful transport or central canary receipt alone is not native Job acceptance or acceptance of an old pending RUN/WAVE.
