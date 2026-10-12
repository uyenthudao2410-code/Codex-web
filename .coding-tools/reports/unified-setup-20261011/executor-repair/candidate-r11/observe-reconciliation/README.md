# Exact rejected-action reconciliation

This is a local-only prepared packet. Root owns remote execution. Original source/runtime/service/authority markers are unchanged.

`observe-r11.py` loads the original staged canary by exact hash at `incoming/r11-approved-20261011T163335163457Z`. It proves the additional context through the fixed action `act_a0b6b348fd944ea7b9e1eccf0b4c816f`, task `task_d06d0dcedee9447ca8dca049137295aa`, standing intent, work request, task-action link, owner, complete target and exact 600000ms lifespan. It removes only that internal context from a copied overview, then runs the frozen authority guards. Read-only SQLite uses `mode=ro`, `query_only` and explicit connection closing.

`cleanup-r11.py` requires root `--execute`, exactly one settled rejected receipt with `CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH`, and exactly one attempt. Its exclusive cleanup intent precedes release/close. It releases the exact writer and closes the exact task, then checks closed task/no open writer. It has no patch, test, task-open, renewal, rollout or restart path. A transport uncertainty must be reconciled; never repeat an effect.

Root commands use `root-observe-ssh.py stage --execute`, `observe --execute`, then `cleanup --execute`. The transport stages exactly the two pinned helpers in `incoming/r11-approved-20261011T164200000001Z` with the existing frozen binary STAGE/INVOKE. Stage and cleanup are once-only. Public receipts are retained locally, while SSH stderr and protected fields remain undisclosed.

15 offline tests passed: 9 observer, 3 cleanup, 3 transport. Independent bounded review found no concrete defect in observer/cleanup. An initial fixture cleanup failure on Windows was resolved by closing temporary SQLite connections; live observer connections already closed correctly. This lane made no external effects, commit, push or release.
