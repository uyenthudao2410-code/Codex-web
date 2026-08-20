# P4-MX Closeout Provenance

- Evaluation date: `2026-08-20`
- Candidate: `gpt-5.4-mini`
- External evaluation worktree branch: `p4mx-eval-20260820`
- Result-source commit: `522dede8f1b995a1ff3ec4c40b933c75c0c43dda`
- Final-report SHA256: `2b42f2b3ef082eba6f0bfc5301178c7b9804d90146add3298a7d4e9d4a468a47`
- Responses SHA256: `22f7bd3a2bf706d860f4a97403662479302f9b666e186c8cab8cf0ef746031a1`

## Evaluator-input authority

The evaluator pack used for closeout is the Sol-accepted P4-MX pack recorded by run `6852041e20904481a077e86dea866cba`, wave `26e4a403db214be491d31af8746b6960`. Its accepted checkpoint receipts bind the evaluator inputs to:

- public catalog SHA256: `f13b69161b0c03d1bcf96111169539ec8706bb6d6015b9dec8607d12e8aa73ad`
- public feedback SHA256: `cec53b620e183cc1b50d172e8d9d7803333bf57cb24d0ee7cb02a3a02b0b5e8c`
- private oracle SHA256: `ad07bf2d50f59cdcefbc36d7b5ddb583444636ca7996bd72e92f22cb7b5a6bdd`

The current main-workspace evaluator files matched all three accepted receipts exactly at closeout time.

## Eval-commit mismatch and resolution

The private-oracle blob committed at result-source commit `522dede8...` materializes to SHA256 `50e181c5febf343c3f305c0855657449b42b3d37b3e894a1a72bb5bb488e9dc0`, so that committed blob is not the accepted oracle used to grade the held-out run and was rejected by the closeout verifier.

To preserve the security boundary without reading the unauthorized external-worktree filesystem, only the committed final report and response artifacts were materialized through an ephemeral detached Git worktree under the authorized main workspace. The closeout verifier used the accepted evaluator inputs from main, produced and replay-verified the immutable manifest, then the ephemeral worktree was removed. No private-oracle content is duplicated in this evidence directory.

## Closed measurement

- Outcome: `4 FIRST_PASS / 0 REPAIRED / 25 FAIL / 1 HARD_FAIL / 0 UNKNOWN`
- Weighted score: `0.113994`
- Effort provenance: `24 Extreme @ medium` plus `6 Ultra @ low` after requested-medium non-terminal transport fallback.
- Canonical before/after: identical.
- Canonical non-interference: `PASS`.
- Evidence class: benchmark, non-promoting, non-mutating.
- P5 may be opened by this evidence: `false`.
- Automatic policy activation: `false`.
