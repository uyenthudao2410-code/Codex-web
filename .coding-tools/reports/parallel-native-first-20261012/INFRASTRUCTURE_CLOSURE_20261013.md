# Infrastructure Closure — Codex-web, 13-10-2026

> **Draft for operator review.** This report carries forward verified runtime
> evidence and records the three closure phases requested in the user assessment.
> The final verdict must be updated from the phase A/B/C receipts before this
> report is used to declare closure. No runtime operation, commit, push, tag,
> release, or service restart was performed by the report author.

## Objective and scope

Close the Native-First infrastructure work at the smallest evidenced scope so
product work can return to Problem Resolution, Knowledge Reuse and Outcome
Confirmation. The operational scope is ordinary File API, approved native
Git/Node and explicitly approved build commands on the two existing workspace
bindings. This closure adds no runner architecture and does not require a public
installer or an AutoCAD build.

The assessment is the user-supplied **“Đánh giá hoàn thiện hạ tầng Codex-web để
quay lại mục tiêu sản phẩm”**, attached on 13-10-2026. Its proposed durations are
planning estimates, not measured elapsed time or delivery commitments.

Observed repository identity: `main @
7999c4151cb501db86f2e4d0a2275d33fc248324`, matching `origin/main`. The worktree
contains the implementation, tests, documentation, package resources and runtime
evidence from the preceding authorized waves. This report does not treat a dirty
worktree as permission to discard evidence or rewrite history.

## Closure criteria

| Criterion | Strongest carried evidence | Closure status in this draft |
|---|---|---|
| File API/Git/Node Native-First runtime | 100 reads, 20 exact patches, 20 readbacks, 10 distinct Node Jobs, 3 Git Jobs and one approved build/readback on the retained r4/r5 receipt chain | Proven at the existing runtime scope |
| Independent workspaces and reconnect without replay | Two native Jobs overlap for 2,078 ms; client transport is recreated and the original Jobs are observed without a second exec; tasks/writers terminal | Proven for client transport reconnect |
| Packaged restricted native execution or locked unproven scope | Exact packaged launcher probe completed; corrected restore and independent readback show empty prefixes on both scopes; network/path/Job-limit dimensions remain locked | Phase A closed at bounded scope |
| One real Coding Problem resolved and confirmed | `AUTO_ACTIVATION_GIT_TOO_LARGE` reproduced, source patch applied, behavior confirmed, focused test 38/38; source-only | Phase B closed at source scope |
| Controlled Git baseline and delivery evidence | Classified review, secret scan, consistent ledger snapshot and delivery guards passed; changes remain staged for review with no commit | Phase C prepared and verified |

The first two criteria must not be rerun merely to replace their existing proof.
Their reuse remains conditional on unchanged relevant source/runtime conditions.
The other three criteria are not inferred from fixture counts or documentation.

## Runtime and evidence carried into closure

The retained current checkpoint identifies:

- Windows candidate:
  `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-parallel-r4-timefix\win-unpacked`.
- Activation epoch:
  `activation-mv5gbzeq-7ac98611bf3a96aa444fcf8e14d3ea1c`, state `READY`, admission `OPEN`.
- Windows MCP process instance: `-s21-KH6ldxHjCSO`.
- Ubuntu MCP instance: `7GYqt3ZdkU47_HIr`; service
  `codex-control-plane.service`, PID `970133`, target `svhome@100.116.112.22`.
- Recovery Host PID `44012`, instance
  `ecae23c8a75f4b28b3bc182104f3ed49`; packaged code revision current at the
  Windows status observation.
- Execution role `central_executor`, with native/MCP/authority/central connected.
  `CHANGED_NEEDS_DISCOVERY` is not applicable to this executor role; a separate
  direct connector still needs its own discovery evidence.
- Desktop and Start Menu shortcuts and Recovery Supervisor manifest target the
  r4-timefix candidate. Named Sandbox process census is zero at the post-shortcut
  observation.

The base policy for each workspace is `native_first` with empty native prefixes.
Phase A temporarily introduces only the exact probe launcher on Codex-web. Its
installation receipt is evidence of a narrow policy change, not proof of the
child's restrictions or a completed roundtrip. Restoration and terminal action/
task/writer evidence must precede the final closure verdict.

### Retained receipts and locally verified hashes

| Receipt | SHA-256 |
|---|---|
| [Runtime aggregate](canary/r5/production-completion-evidence-20261013.json) | `9efb4c93edf9b77467549b86ec1aafe70e4d90b2434c13a25fde6b510f889f4c` |
| [Strict continuation join](canary/r5/native-first-continuation-evidence-join-20261013-v3.json) | `2e3cf43e24865c6e7a8cd39e7f847c799866b1e9e221c30eae0ad926cbdfaa05` |
| [Production evidence checkpoint](canary/r5/production-final-evidence-20261013-v3.json) | `646ba458e490f0386cb2367c625c2b0161f9817baaab49805ff82e52c11f12d9` |
| [Post-shortcut verification](production-post-shortcut-verification-20261013.json) | `de37d246088a66ac5250e08675142d9d9a5a1a0e723a02c0dc50e0741b2d8d84` |
| [Source token fixture](canary/r5/token-child-native-fixture-20261013.json) | `b5fa290522ab6ad59bbd782162b691716e2ebc73351645faed42298cd33996dd` |
| [Windows read-only status](canary/r5/windows-status-live-20261013.json) | `555f167483e709c2beb08b08979b8cd1178e4a31aa747898bd224f387c6942b2` |
| [Exact packaged probe approval](canary/r5/packaged-token-packaged-token-install-1791848440172-42315e65.json) | `7978440a02bb9fb60dc70c5b289e2a544147f8d3c85d3dd2a7b8b2f68bdb6ce0` |
| [Packaged token canary](canary/r5/packaged-token-canary-694a79bfeef446559b3897cc052e723a.ndjson) | `5ba4d7118a20069e5267ce5699cfb0a2ce86ec7a23531769c56e3099fac22cb6` |
| [Packaged restore failure 1](canary/r5/packaged-token-packaged-token-restore-failure-1791849843525-3129da00.json) | `b305a68953e3180e26521d793c8606e1eca082718d9e3cffeb33096774ec1ed8` |
| [Packaged restore failure 2](canary/r5/packaged-token-packaged-token-restore-failure-1791849861589-149cda72.json) | `719e483e5a5d02b5b47fc6a79af4f726479c7af11c07afbc4a6c5c229b3d2a47` |
| [Corrected packaged restore](canary/r5/packaged-token-packaged-token-restore-1791850043345-d884cf29.json) | `d40d8ad7b179c47e8e107191cd4bdf20ad2d833595fea96f0563087b582a9322` |
| [Independent policy readback](canary/r5/packaged-token-restore-verify-20261013.json) | `69b32732939fca92c128958e99053dd41ef00841619bece8c69459488652495e` |
| [Phase B real Problem](phase-b-real-problem-git-evidence-20261013.json) | `03bf7ac56a145fdc7be2617c230c785785941ee4dba097ea765781c0607b114c` |

These are observation-window claims. No static readiness receipt proves later
process liveness. The final operator checkpoint needs a fresh read-only status
and job census after phases A/B/C.

## Phase A — Security boundary

### Proven source behavior

The bounded source Runtime token fixture launches a compiled WinAPI child through
the native Node path, with exit 0, `execution_backend=native`,
`isolation_level=process_container`, `policy_decision=native_explicit_approval`,
and zero VM-adapter calls. It observes AppContainer, low integrity RID `4096`,
non-elevated token, Administrator deny-only and disabled, zero enabled sensitive
privileges, and zero token query errors. Its explicit
`production_native_claim=false` is preserved.

### Packaged proof and restoration

Use the existing packaged r4-timefix runtime and the single exact approved argv:

```text
node .coding-tools/reports/parallel-native-first-20261012/canary/r5/token-child-launcher.js
```

The completed canary bound the actual Job, receipt, action, task, workspace,
generation and activation epoch. Its terminal receipt records exit 0,
`native/process_container/native_explicit_approval`, no elevated fallback, and
the restricted child token facts listed above. The canary elapsed time was
38.772 seconds. This is one approved read-only probe; it does not authorize
broader prefixes or toolchains. Record the actual network/path boundary and
required Job limits separately when those restrictions are directly exercised;
the token probe alone does not prove them.

After the original Job/action was terminal and its task/writer closed, the
corrected helper restored the exact empty native-prefix policy. Independent
readback confirms Codex-web hash `f10114...de2d58`, AutoCAD hash
`0d4230...10782`, and empty prefixes on both scopes. The earlier restore failures
remain chronology: the helper compared policy SHA with a raw scope hash, and no
duplicate Job was dispatched. No broader Node/Git/script approval follows from
this probe.

If a required restriction cannot be verified, closure may use the assessment's
locked-scope alternative: explicitly name that restriction and deny or isolate
the commands it affects. A token-only pass is not blanket approval for toolchains.

## Phase B — One actual Coding Problem

Record one small Codex-web bug or product problem with an observable before/after
outcome. Required trace: source read → guarded patch → Git diff review → smallest
relevant validation → behavior confirmation. Ordinary reads and metadata do not
need a VM; executable validation retains the existing approval/isolation policy.

Completed receipt: `phase-b-real-problem-git-evidence-20261013.json`. The
retained `.coding-tools` tree reproduced `AUTO_ACTIVATION_GIT_TOO_LARGE` before
source identity evaluation. `electron/services/recoveryActionStore.js` now
applies rooted `.coding-tools` exclusions before bounded output/source-entry
checks; `node --test tests/accepted-code-activation.test.js` passed 38/38, with
behavior confirmation accepting the repository and returning a source
fingerprint. The recorded reproduction-to-behavior interval was 84,343 ms and
focused validation 77,540 ms. One test assertion initially called an unfiltered
Python helper and was corrected without weakening the guard. The source-only
patch is not rebuilt or loaded into the serving package. A separate
`scripts/check-sensitive-tracked.js` `maxBuffer` fix has focused 4/4 evidence.
Do not call the independent 20/20 fixture wave 20 user Problems.

## Phase C — Controlled baseline

Review existing changes by source, tests, maintained docs, runtime evidence and
package resources. Preserve unrelated work. Before the baseline is committed or
pushed, retain a secret scan and diff review; create the canonical ledger snapshot
with the repository delivery staging command and record the guard result:

```powershell
npm run stage:coding-tools-delivery
npm run check:coding-tools-delivery
```

The stage operation preserves every `.coding-tools/**` file except the two
approved transient SQLite sidecars, snapshots the canonical ledger consistently
and binds it to the staged delivery receipt. `check:coding-tools-history` must
continue to reject other ignored evidence, nested repositories and gitlinks in
that tree. New runtime evidence appearing after a snapshot requires the relevant
delivery guard/re-snapshot handling, not omission.

Any actual credential found in retained evidence is a delivery conflict requiring
remediation. It must not be silently excluded. The baseline is reviewable only
after the scan, staged ledger, index verification, diff and final job state agree.
The assessment requires approval before the commit; preparation of this draft is
not that approval. No public release is part of this closure.

## Remaining debt after bounded closure

| Item | Classification and next trigger |
|---|---|
| Three AutoCAD `UNKNOWN` actions; five historic actions across the device | Separate reconciliation debt. Preserve quarantine and original evidence. Resolve only from trustworthy original-action evidence; no replay, blind settlement or deletion. |
| CPython native loader exit 126 | Tool compatibility limitation. Keep affected commands isolated/denied until a real use case justifies compatibility work and validation. |
| .NET/AutoCAD build | Not executed or accepted. Requires separate toolchain/use-case validation and authority; not a general Native-First closure requirement. |
| Direct connector discovery | Required only if operating the direct connector. Current `central_executor` proof does not attest that connector. |
| Sandbox idle teardown | Safe automatic teardown observed with final aggregate RAM zero, 390,240 ms after Job terminal. Fast memory release and a 30-second end-to-end SLA are not proven. Reopen on a reproducible user impact. |
| Original parent canary failure | Retain `ORIGINAL_JOB_IDENTITY_NOT_VERIFIED` as history. Linked continuation proof covers its successful lanes; reopen only for a new failure or invalidated evidence. |
| Public packaging/release | Deferred. Operational candidate activation is separate from published artifact/release acceptance. |

The separate activation closure projection's `NO_ACCEPTED_CHECKPOINT`,
`NOT_RELEASED` and `NOT_CLAIMED` labels must not be upgraded by this report.
Operational candidate readiness is evidenced independently. Every claim keeps
its original scope: source, focused test, package, controlled live runtime or
published release.

## Final operator checkpoint to fill from receipts

### Production activation gate — 13-10-2026

#### Successor receipt after accepted checkpoint — 03:42 UTC

The accepted current-HEAD checkpoint is now available. Trusted Recovery Host
preflight returned `READY`, selected checkpoint
`4e9e9eb6bb494ca5ae04c49c7092c126`, one receipt, and
`mutable_operation_started=false`. This closes the earlier
`TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE` condition. The generated official
run report for `e8cdbc78f12043559003ff65c4f6c883` records accepted status,
same-wave proof, exact file adoption, and a valid audit chain.

Development full-clean preflight still returned
`RECOVERY_HOST_INSTALLATION_MISMATCH`, before any lifecycle mutation. The
serving host belongs to packaged r4-timefix; the bfix unpacked candidate has
a different installation identity. No restart, installation switch, policy
change or source activation was performed. The successor receipt is
`bfix-production-activation-gate-20261013-v2.json`; earlier failed receipts
below remain chronology.

Fresh SSH to `svhome@100.116.112.22` timed out. The retained historical Ubuntu
readiness proof is carried forward without asserting a fresh server state.
The supported boundary audit passed 42/42 recovery bootstrap tests; packaged
to packaged live replacement is unsupported, while unsigned MXC Sandbox
binaries cannot be published as a customer NSIS installer.

The remaining action is a legitimate packaged release/install transition and
fresh authenticated postflight. Source acceptance and package proof alone do
not establish that bfix is loaded. No commit, push or public release occurred.

The bfix candidate was rechecked without mutating the serving installation:

- packaged parity recheck: PASS (`90` application files, `299` resource files,
  `10` Control Plane adapter files);
- isolated packaged recovery smoke: PASS;
- Ubuntu read-only readiness: PASS, service PID `970133` stable;
- serving Windows r4-timefix: `READY/OPEN`, `fullyReady=true`, Recovery Host
  PID `44012`;
- trusted bootstrap preflight: `TRUSTED_BOOTSTRAP_SOURCE_UNAVAILABLE`;
- full-clean preflight from the development checkout:
  `RECOVERY_HOST_INSTALLATION_MISMATCH`.

The exact gate receipt is
[`bfix-production-activation-gate-20261013.json`](bfix-production-activation-gate-20261013.json).
No supervisor manifest, shortcut, process, activation epoch, policy, Ubuntu
service, or AutoCAD action was changed in this wave. The decision is
`BLOCKED_PRESERVE_CURRENT_PRODUCTION`: bfix has package proof but no current
HEAD accepted `recovery_host` checkpoint, and the unpacked candidate has no
supported in-place packaged release/install handoff. The existing r4-timefix
runtime remains the only production-loaded candidate.

- **Phase A result:** bounded packaged token proof and exact empty-prefix restore
  passed. Network/path and Job-limit dimensions not directly exercised remain
  locked to isolated/deny; no broad native approval is granted.
- **Phase B result:** one real source Problem completed and behavior confirmed;
  source-only patch is not packaged.
- **Phase C result:** classified source/test/docs/evidence/package review completed;
  repository secret check passed; ledger snapshot and coding-tools delivery check
  passed on 10,728 files. The baseline is staged for review and intentionally not
  committed or pushed because the user has not named a commit/push target.
- **Runtime state:** carry-forward r4-timefix `READY/OPEN`; no post-phase live
  assertion is now refreshed by [server-readiness-closure-final-20261013.json](server-readiness-closure-final-20261013.json)
  (`5d8685dcdd94f0f3f55310e3caa83784c6a99e7c6835881c6a403e136791e1c8`) and
  [windows-status-live-final-20261013.json](canary/r5/windows-status-live-final-20261013.json)
  (`a35cbfebeb8a617198011473b88f3730a08a6e9e6190c15a5cf1d7aff1a0cf3f`).
  Ubuntu PID `970133` is stable; Codex-web exact scope has no open task, writer
  or unsettled action; AutoCAD retains three quarantined `reconcile_required`
  actions. Windows remains `READY/OPEN`, `fullyReady=true`, central executor,
  native/MCP/authority connected.
- **Git state:** `main @ 7999c4151cb501db86f2e4d0a2275d33fc248324`, dirty;
  staged evidence baseline present; no baseline commit created by this report
  author.
- **Next action:** return to concrete product Problems and knowledge reuse. Reopen
  infrastructure only for a demonstrated operational boundary failure. A future
  packaging/activation wave is required before the Phase B source fix is claimed
  as loaded into the currently serving packaged candidate.
