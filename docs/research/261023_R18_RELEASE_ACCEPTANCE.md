# Exact Release Acceptance — packaged r18 (2026-10-23)

One record binding source, package, runtime and test evidence for the
release that is live on DESKTOP-63643J4. Produced for the P0 "exact release
acceptance" item of the 23/10 progress review. Facts only; every value below
was read from the named source at the stated time.

## Source

| Item | Value |
| --- | --- |
| GitHub `main` | `15bdbbc6b97677b4926da5b66e0d24497d6c187f` |
| Windows local HEAD | `15bdbbc6b97677b4926da5b66e0d24497d6c187f` (identical) |
| Source commit | `c7adddfd` feat(work-hub,mcp): atomic git delivery guard + durable destructive approval receipt |
| Delivery snapshot | `15bdbbc6` chore(coding-tools): delivery snapshot for atomic git guard + approval receipt |

## Package

| Item | Value |
| --- | --- |
| Build tag | `r18` |
| Build directory | `dist/windows-candidate-mxc-wsb-cbe1774-r18/win-unpacked` |
| Executable SHA-256 | `7F961CA9BE04B1BB24CC536368F1FF74404EAC2F191730A73EF206D4A00B95E3` |
| Installation ID | `0b4cdecbe3ad66b8a17a85a51d4c98668fc2684fec01c4eb1d814f84f5f0c271` |
| Runtime mode | `packaged` |

## Runtime (single snapshots, packaged descriptor)

| Item | 2026-10-23T06:08:35Z | 2026-10-23T06:35:14Z |
| --- | --- | --- |
| Activation epoch | `activation-mvkkj43q-0531d891ee5be965a6817d028b3769bd` | same |
| Epoch state / admission | READY / OPEN | READY / OPEN |
| Recovery Host PID | 41892 | 41892 |
| Supervisor | healthy | healthy |
| MCP running / central connected / authority ready / fully ready | true / true / true / true | true / true / true / true |
| Recovery Host revision (running == disk) | `31b88e4d0bbb15b704c73153452b72b020ca90648c13719894a0ed9f15abe8b8` | same |
| Electron UI revision (running == disk) | `4931cd7d702e2848051d5ebb16936c54357beb16a38c7d1cc02c774d2ade0fdb` | same |
| update_pending | false | false |

## Test evidence (local runs with preserved logs — NOT CI)

GitHub reports 0 check runs for this HEAD; the runs below are local,
operator-preserved logs and are not represented as CI acceptance.

| Suite | Result | Log SHA-256 |
| --- | --- | --- |
| Node work-hub-files, VM | 19/19, exit 0 | `a20578cf206e5164a9ed4a16f0aa380c2fde2f82b36f08b540e7c02b1afa0718` |
| Node work-hub-files, Windows | 19/19, exit 0 | `665f1f393913b27b2c4e5f6b428b746dd4eeef08c6009edfc9e63ec61adba9ad` |
| Node work-hub-files, svhome | 19/19, exit 0 | `6ff8f2e74373aa0ecc424aee226586977131678f308d7cce6617df211095ebe0` |
| Python local-mode, Windows | 8 passed, exit 0 | `6b0e176f768d95e735d329a16abce7452e3cacc62e3068154b34266815e5e259` |

## Acceptance events

- Work Hub GUI acceptance by the operator: 2026-10-23 (chat confirmation).
- GUI E2E acceptance on this package (r18) by the operator: 2026-10-23
  13:34 +07 ("nghiệm thu GUI E2E trên r18 ok"), with the 06:35:14Z runtime
  snapshot above taken at the same time.
- Control Plane action `act_81e2ae42400f456bad538e98366ce02c` settled
  centrally (`settled / rejected`); receipts retain the original `unknown`
  and the terminal `rejected`.

## Addendum — epoch rotation during the acceptance commit (2026-10-23 07:16Z)

Committing this record required a brief full stop of the packaged stack so
the delivery check could stage a stable snapshot (the live app rewrites
`.coding-tools/performance.json` continuously). On restart, the host first
resumed epoch `activation-mvkkj43q` in an update-incomplete state (MCP
running but unbound; full-clean census could not acquire its exclusive
ledger gate while that MCP held the ledger). Terminating the MCP process
let the restart's stop phase free the gate, and a new full-clean epoch
`activation-mvkmy4ps-60f9bb927bf7784e10967bd94cbb6ab8` reached READY / OPEN
with `fully_ready=true` (snapshot 2026-10-23T07:16:46Z). Package,
installation and source are unchanged; only the activation epoch rotated,
which is an activation instance, not part of the release identity above.

## Addendum 2 — rollback drill executed (2026-10-23)

The rollback position below was exercised end to end on 2026-10-23 under
the operator's full-authority grant:

- Pre-drill: r18 live, epoch `activation-mvkmy4ps` READY (snapshot
  2026-10-23T07:36:16Z).
- Rollback leg: r18 supervisor uninstalled, r17 supervisor installed,
  full-clean activation → r17 installation `2e91538e…`, epoch
  `activation-mvknropv-c8a06abf4fcf4b229186e0726cc36a5f` READY / OPEN,
  supervisor healthy, `fully_ready=true` (snapshot 2026-10-23T07:40:01Z).
- Roll-forward leg: r17 supervisor uninstalled, r18 supervisor installed,
  full-clean activation → r18 installation `0b4cdecb…`, epoch
  `activation-mvknwh0u-af5988c4f6f68ab7b37a58df8346d8e7` READY / OPEN,
  `fully_ready=true` (snapshot 2026-10-23T07:43:16Z).

Both directions used the proven Recovery Host IPC path; no census-gate
intervention was needed on cross-installation switches. The live release
after the drill is again r18 (current epoch `activation-mvknwh0u`).

## Rollback position

- Previous packaged builds retained on the Windows machine: r17, r16, r15k.
- The full-clean activation path (packaged Recovery Host IPC
  `runtime.restart` with `full_clean_refresh` + `allowAcceptancePending`)
  has been executed successfully for r15k, r16, r17 and r18.
