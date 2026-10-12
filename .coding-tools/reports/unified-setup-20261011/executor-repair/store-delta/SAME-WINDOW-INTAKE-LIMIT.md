# Same-window intake recovery: current authority limit

Prepared source analysis; no SSH/API/runtime/service/authority operation was performed.

The requested `recovery -> scoped_pilot` transition cannot retain the exact current pilot ID. `ControlPlaneStore.set_admission_mode` in `control-plane/control_plane/store.py:1616` revokes **every** currently unrevoked pilot on recovery entry. Lines1617–1618 explain that later reopening requires a fresh decision, to prevent old queued actions becoming dispatchable. `renew_scoped_pilot_decision` at line2011 also forbids resurrecting a revoked decision.

Consequently preserving grant/context/window is possible, but preserving the same **live** pilot through these owner APIs is not. Creating a replacement at the exact original expiry requires a separately reviewed authority action. No SQL edits, pilot resurrection or bypass of the admission API is an acceptable substitute.

`ubuntu-r10-same-window-intake.py` SHA256 `770853b1f6df78550961a04e0a8d01e19c368247d6384acbf6aa6b0bf98358d0` is retained as an **observe-only prepared draft**. Default observation reuses frozen v3 inspect/state/target/authority definitions, validates the exact current grant/context/pilot/window and post-cold 38/10/1 counts, original quarantine/acceptance digests and exact settled cold/cleanup family. `--execute` fails before any owner mutation with `SAME_PILOT_RECOVERY_UNSUPPORTED_PREPARED_OBSERVE_ONLY`. It must not be presented as a functioning close/reopen packet.

Original frozen v3 helper and marker remain untouched. Root reported cold action `act_9482be2aef814d82b3ff4722b5979a25` and task `task_80e2fb1ba3e449edbfb05d5a53055642` settled and cleaned, while runtime processes are currently absent. No new Job, deployment, restart, commit or push by this preparing agent. Root's next decision is whether to leave scoped pilot during recovery or approve a same-expiry replacement pilot; this report grants neither action.
