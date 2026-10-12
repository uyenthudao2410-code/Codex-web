# r14 context guard correction

This root-only packet corrects the local rollout guard after the first close stopped before remote effects. The original packet, failed receipt and consumed local close intent remain unchanged in `activation-server-same-window`.

The actual read-only inspection at `1791762929114` proved two unclosed target contexts: the approved standing context is live, and `ctx_b7d6fe51fc7c4aaaaba2947ad8c98e43` expired at `1791759840282`. Admission remained `scoped_pilot`; the exact prior pilot was the only unrevoked pilot. All remote r14 phase intents and marker were absent. Task/writer/queued/target-unsettled counts were zero.

The server helper changes only `window()`: select unclosed contexts whose expiry is in the future, then require exactly one original context with the original expiry and exact device/workspace/generation. All historical context rows remain unchanged and included in preservation checks. The driver pins the original typed failure, original local intent and actual read-only inspection before a fresh guarded close. New exclusive local intents live in this sibling packet; the original intent is never removed or reused.

Human approval `call_VVCZ5vN5tTi8XytTvFyQyHY0` authorizes the same r14 sequence. The expiry remains `1791776571067` (2026-10-12 10:42:51.067 Asia/Saigon). No authority extension, Ubuntu deploy/restart, Windows reboot or semantic acceptance is included.

## Root execution

Obtain a fresh Windows pre-close receipt first. Then run exactly once:

```powershell
python -B "E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r14\activation-server-same-window-context-guard\root-server-transition-r14-ssh.py" close --execute --approval-id "call_VVCZ5vN5tTi8XytTvFyQyHY0" --approval $r14ApprovalFile --approval-sha256 $r14ApprovalSha --windows $r14PrecloseFile --windows-sha256 $r14PrecloseSha
```

Use this corrected driver for later `observe --read-only`, `replace --execute` and `reopen --execute` phases, with the same arguments and sequential Windows preparation described in the original packet README. Marker/public receipt contracts are unchanged. `replace` and `reopen` still require the fresh final Windows proof and exact previous server receipt hash.

An uncertain result requires read-only inspection and reconciliation. Never rerun a consumed mutation. The first failure was a pre-effect guard defect; this is a distinct guarded attempt backed by the read-only census.

## Proof

The focused test loads the actual census and verifies that the approved context is selected while all historical rows remain identical. It rejects an extra live context, wrong device, closed/expired standing context, and wrong approval ID. The original frozen Windows consumer compatibility proof remains applicable because public output and mutation-phase contracts were not changed.
