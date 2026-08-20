# P4-MX External Evaluation Closeout

- Candidate model: `gpt-5.4-mini`
- Evaluation date: `2026-08-20`
- Runner: `p4-mx-model-extreme-v1`
- Evidence class: benchmark, non-promoting, non-mutating.
- Effort interpretation: 24 Extreme at `medium` + 6 Ultra at `low` (requested `medium`, fallback: `medium_no_terminal_answer_within_budget`).
- A response filename containing `medium` is not evidence that all cases ran at medium effort; the evaluator-owned manifest is authoritative for effort provenance.

## Held-out outcome

- Total / attempted: 30 / 30
- FIRST_PASS: 4
- REPAIRED: 0
- FAIL: 25
- HARD_FAIL: 1
- UNKNOWN: 0
- First-pass rate: 0.133333
- Repair recovery rate: 0.0
- Final pass rate: 0.133333
- Weighted score: 0.113994
- Hard-fail IDs: MX-AG-001

## Canonical dimension scores

| Dimension | Pass | Fail | Observed | Score | Weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| anti_gaming | 2 | 14 | 16 | 0.125 | 8.0 |
| causal_repair | 1 | 9 | 10 | 0.1 | 10.0 |
| correctness | 4 | 26 | 30 | 0.133333 | 20.0 |
| electron_ui_reasoning | 0 | 5 | 5 | 0.0 | 5.0 |
| hidden_oracle | 3 | 14 | 17 | 0.176471 | 15.0 |
| repo_reasoning | 1 | 14 | 15 | 0.066667 | 12.0 |
| security | 0 | 5 | 5 | 0.0 | 12.0 |
| state_consistency | 4 | 17 | 21 | 0.190476 | 12.0 |
| terminal_reasoning | 1 | 5 | 6 | 0.166667 | 6.0 |

## Integrity and governance

- Canonical before/after identical: `True`
- Non-terminal medium timeout policy: `transport_failure_not_model_fail`.
- Ultra fallback preserves candidate model and public/private challenge-oracle identity.
- P4-MX cannot open P5 and cannot activate routing policy.

### Artifact hashes

- `final_report`: `2b42f2b3ef082eba6f0bfc5301178c7b9804d90146add3298a7d4e9d4a468a47` | `tmp/p4mx-closeout-snapshot/tests/model_eval_pack/results/p4mx_gpt54mini_20260820_final_report.json`
- `private_oracle`: `ad07bf2d50f59cdcefbc36d7b5ddb583444636ca7996bd72e92f22cb7b5a6bdd` | `tests/model_eval_pack/private/model_extreme_oracles_v1.json`
- `public_catalog`: `f13b69161b0c03d1bcf96111169539ec8706bb6d6015b9dec8607d12e8aa73ad` | `tests/model_eval_pack/public/model_extreme_challenges_v1.json`
- `public_feedback`: `cec53b620e183cc1b50d172e8d9d7803333bf57cb24d0ee7cb02a3a02b0b5e8c` | `tests/model_eval_pack/public/model_extreme_feedback_v1.json`
- `responses`: `22f7bd3a2bf706d860f4a97403662479302f9b666e186c8cab8cf0ef746031a1` | `tmp/p4mx-closeout-snapshot/tests/model_eval_pack/results/p4mx_gpt54mini_medium_20260820_responses.json`
