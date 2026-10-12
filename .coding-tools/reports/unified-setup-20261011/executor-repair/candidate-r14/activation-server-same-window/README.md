# r14 server phases in the existing authority window

Prepared for the root controller only. No external effect has been performed by this packet. The execution driver requires a future explicit human approval for r14; prior r13/window approval IDs are refused.

## Scope and preserved evidence

- Target: `svhome@100.116.112.22`, unchanged service instance `cp_339c7a19bc2443eeab35583addfef543` and source revision `9cae1044…`.
- Context: `ctx_1e7e2fec6f0e43018db7a51c6980e5c2`, original requested time `1791758571067`, unchanged expiry `1791776571067` (2026-10-12 10:42:51.067 Asia/Saigon).
- Close revokes the sole unrevoked pilot, exactly `pilot_b1cb26c319fb489aae24d3b746318447`. Replace creates one pilot for the same principal, binding and expiry. Reopen admits that pilot.
- Context and service grant rows must remain byte-for-byte equal; existing pilot and task/action history is preserved except the exact prior-pilot revocation. No renewal, deployment, service restart, reboot, patch replay, or semantic acceptance.
- The r13 marker is read and preserved. The new marker is `/home/svhome/.local/state/codex-control-plane/owner-operations/r14-same-window-activation/authority-transition-public.json`.

## Root command sequence

All variables below denote absolute paths or SHA-256 values obtained from the actual files. Do not reuse the historical Windows observation. Before any mutation, record the new approval response in a pinned JSON file. Its fields must exactly match `approval()` in the frozen server helper, including the unchanged context/expiry/target, the three approved operation booleans, and the four prohibited-effect booleans. Use the actual response call ID and current approval timestamp. This packet contains no approval.

1. Obtain a fresh Windows pre-close receipt using `activation-windows-same-window/observe-r14.cjs observe`. It must be less than 60 seconds old when closing.
2. Close intake once:

```powershell
python -B "E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r14\activation-server-same-window\root-server-transition-r14-ssh.py" close --execute --approval-id $r14ApprovalId --approval $r14ApprovalFile --approval-sha256 $r14ApprovalSha --windows $r14PrecloseFile --windows-sha256 $r14PrecloseSha
```

3. Follow the frozen Windows packet: supported r13 owned executor cleanup/full-clean refresh; READY with zero Jobs/VM; fresh observe/freeze; activate r14; validate policy; start bounded agent; refresh/finalize.
4. Refresh server observation while intake stays closed, to capture the actual new node echo:

```powershell
python -B "E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r14\activation-server-same-window\root-server-transition-r14-ssh.py" observe --read-only
```

5. Run Windows final proof with the fresh server observation. Replace the pilot once, using the real final Windows proof and latest matching closed-phase server receipt:

```powershell
python -B "E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r14\activation-server-same-window\root-server-transition-r14-ssh.py" replace --execute --approval-id $r14ApprovalId --approval $r14ApprovalFile --approval-sha256 $r14ApprovalSha --windows $r14FinalProofFile --windows-sha256 $r14FinalProofSha --server $r14ClosedServerFile --server-sha256 $r14ClosedServerSha
```

6. Refresh Windows final proof if the receipt has reached 60 seconds. Reopen once, using the pilot-replaced receipt as the previous marker reference:

```powershell
python -B "E:\Github\Tools-Codex-web\.coding-tools\reports\unified-setup-20261011\executor-repair\candidate-r14\activation-server-same-window\root-server-transition-r14-ssh.py" reopen --execute --approval-id $r14ApprovalId --approval $r14ApprovalFile --approval-sha256 $r14ApprovalSha --windows $r14FinalProofFile --windows-sha256 $r14FinalProofSha --server $r14ReplacedServerFile --server-sha256 $r14ReplacedServerSha
```

7. Take one read-only `observe` receipt. Then run the separately frozen new verification canary. Never replay the r13 patch/proof or accept its pending native wave through this packet.

Each mutation creates exclusive local and remote phase intents. If a process fails, times out, or reports an uncertain result, inspect read-only and reconcile the observed state. Do not rerun the mutation. The helper requires at least 12 minutes left in the original authority window and fresh matching Windows receipts.

## Offline evidence

Five focused projection/preservation tests passed during packet preparation. After the final TARGET marker fix, the real exported Windows `guardServer` consumer check passed again. This proves local projection compatibility; r14 has not been activated and live executor/canary acceptance is not yet proven. See `offline-proof.json` for exact frozen hashes.
