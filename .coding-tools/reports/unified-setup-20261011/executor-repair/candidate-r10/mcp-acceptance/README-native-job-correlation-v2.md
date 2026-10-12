# Exact cold native Job correlation v2

Prepared 2026-10-11; dirty `main @ 2c554f59`. Root owns execution. This lane created only this README and `verify-r10-native-job-v2.py`; original verifier, source/package, runtime, authority, journal, ledger and cold action remain untouched.

## Actual schema and evidence locations

The original verifier (`b620253eb7cd1851fd38c862cfaa3be2abc407c2ddd3ad8534af96739048baf5`) looked for `entry.request`. Actual exec-journal schema 1 stores exactly `action_id`, `attempt_id`, `receipt`, `state`; `_record_exec_receipt` in `node_agent.py` confirms this. The missing field is a verifier schema error, not evidence that the command needs replaying.

The immutable public cold transport contains the canary request preflight, queued action/task, terminal receipt and completed cleanup. V2 pins that complete artifact and reviewed pins, then correlates its exact action/task/attempt/command/job/runtime/digests to the submitted local journal receipt and one query-only canonical ledger Job.

| Immutable input | SHA-256 |
| --- | --- |
| `verify-r10-native-job.py` | `b620253eb7cd1851fd38c862cfaa3be2abc407c2ddd3ad8534af96739048baf5` |
| `pins.root-reviewed.cold.json` | `28e8dff65226c5001184ad7dbd34fd6e65b2e05af106c10bdb0d73d01aae7b67` |
| `transport-execute-cold-20261011T130654124612Z.jsonl` | `c3ab3f3cb0d80c5023f32efc20a964586fdd3dcfdd7bea361f2e91120eba4e6a` |
| `verify-r10-native-job-v2.py` | `693f5783cff04fc2130b9d1085fcdbaf8d60dbcd578d2e763bacaaf5ea02709f` |

## Root CLI

```text
python -B .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/verify-r10-native-job-v2.py .coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/pins.root-reviewed.cold.json act_9482be2aef814d82b3ff4722b5979a25 task_80e2fb1ba3e449edbfb05d5a53055642 dd7a305f5be0ec9383bbf1119e655002345c6a2e685a544879b50b4679ee0b39 32214fedb8fb33cebf30bf69a4c16347819a5899c3da7e730fa8a92fc2d03af4
```

The helper recomputes the bridge response projection SHA and combined stdout/stderr SHA internally. Output is bounded safe correlation metadata only. It never emits stdout/stderr, protected configuration, full journal or full Job metadata. SQLite opens with `mode=ro`, `query_only=ON`, and one read transaction. No IPC, SSH, subprocess, action or runtime operation is present.

Strict Job pins include root PID 20952 and its actual OS start token, command/Job ids, exited state, timestamps, owner, native process/server identity, checkout and metadata command hash. It requires RUN/WAVE equality between journal payload and Job. Both are empty for this standalone exec; successful correlation therefore proves a real durable terminal Job and exact public output, and does **not** prove a patch ProofLedger/wave or semantic acceptance. It reports that limitation explicitly instead of inventing a RUN/WAVE.

## Validation and next action

Static `compile(...)` syntax check passed without executing the verifier or writing bytecode. Read-only schema/field inspection confirmed the exact journal and Job locations without printing raw content. Root must run the new helper once, retain its safe result, and continue remaining runtime/cleanup proof. No command replay is needed or authorized by this packet.
