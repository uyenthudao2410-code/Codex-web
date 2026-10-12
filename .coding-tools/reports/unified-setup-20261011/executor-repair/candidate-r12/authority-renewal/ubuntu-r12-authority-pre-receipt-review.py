"""Root-only exact-scope follow-up authority; no deployment, restart or command replay."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import time

COMMON_SHA = "c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f"
common_path = Path(__file__).resolve().parent / "r11_common.py"
if hashlib.sha256(common_path.read_bytes()).hexdigest() != COMMON_SHA:
    print('{"phase":"r12_renewal_failed","ok":false,"code":"FROZEN_COMMON_CHANGED"}')
    raise SystemExit(2)
spec = importlib.util.spec_from_file_location("r12_frozen_common", common_path)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

OPERATION = "owner_approved_r12_initial_verification_60m"
NEXT_DIR = c.HOME_DIR / ".local/state/codex-control-plane/owner-operations/r12-initial-verification-60m"
NEXT_MARKER = NEXT_DIR / "authority-renewal-public.json"
CANARY_DIR = NEXT_DIR / "canary"
PRIOR_MARKER = c.HOME_DIR / ".local/state/codex-control-plane/owner-operations/r11-initial-verification-next-60m/authority-renewal-public.json"
PRIOR_MARKER_SHA = "e3d29f73b0395dd47ff46dd9bbb62831afce0a14183d23c2cd0ca88c5ceaf34c"
MIN_CANARY_REMAINING_MS = 720000
PRIOR_REQUESTED = 1791735729910
PRIOR_EXPIRES = 1791739329910
PRIOR_CONTEXT = "ctx_71ae5c01e2de4df6874d401263a310c0"
PRIOR_PILOT = "pilot_b294f82a6cf64b098268322b9106d8c7"
REASON = "Owner-approved r12 verification: exact Tools-Codex-web read/edit/sandboxed exec for one new 60-minute window"


def now_ms():
    return int(time.time() * 1000)


def prior_marker(grant):
    raw = c.protected_file(PRIOR_MARKER)
    c.require(hashlib.sha256(raw).hexdigest() == PRIOR_MARKER_SHA, "EXACT_FROZEN_R11_PRIOR_REQUIRED")
    marker = json.loads(raw)
    expected = {"operation": "owner_approved_r11_initial_verification_next_60m", "binding_id": c.BINDING,
                "device_id": c.DEVICE, "workspace_id": c.WORKSPACE, "workspace_generation": c.GENERATION,
                "root": c.LOCAL_ROOT, "profile": c.LOCAL_PROFILE, "source_revision": c.REVISION,
                "service_grant_sha256": c.digest(grant), "phase": "intake_reopened",
                "requested_at_ms": PRIOR_REQUESTED, "expires_at_ms": PRIOR_EXPIRES,
                "context_id": PRIOR_CONTEXT, "pilot_id": PRIOR_PILOT}
    c.require(all(marker.get(key) == value for key, value in expected.items()), "PREVIOUS_R11_AUTHORITY_MARKER_CHANGED")
    return marker, hashlib.sha256(raw).hexdigest()


def save(marker):
    c.private_directory(NEXT_DIR)
    descriptor, temporary = tempfile.mkstemp(prefix=".authority-next-", dir=NEXT_DIR)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json.dumps(marker, sort_keys=True, separators=(",", ":")).encode())
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, NEXT_MARKER)
    finally:
        Path(temporary).unlink(missing_ok=True)


def bootstrap_canary_directory():
    c.private_directory(NEXT_DIR)
    if CANARY_DIR.exists() or CANARY_DIR.is_symlink():
        c.private_directory(CANARY_DIR)
        c.require(not any(CANARY_DIR.iterdir()), "R12_CANARY_EVIDENCE_ALREADY_EXISTS_NO_REPLAY")
        return
    CANARY_DIR.mkdir(mode=0o700)
    c.private_directory(CANARY_DIR)


def canary_window(marker, observed_at_ms):
    c.require(type(observed_at_ms) is int and type(marker.get("requested_at_ms")) is int
        and type(marker.get("expires_at_ms")) is int
        and marker["expires_at_ms"] - marker["requested_at_ms"] == 3600000
        and marker["requested_at_ms"] <= observed_at_ms
        and marker["expires_at_ms"] - observed_at_ms >= MIN_CANARY_REMAINING_MS,
        "R12_WINDOW_TOO_SHORT_FOR_FULL_10M_ACTION_PLUS_MARGIN")


def selected_expired(overview):
    now = overview["observed_at_ms"]
    c.require(now >= PRIOR_EXPIRES, "PREVIOUS_WINDOW_NOT_EXPIRED")
    contexts = [row for row in overview["contexts"] if row.get("binding_id") == c.BINDING and row.get("closed_at_ms") is None]
    pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None]
    for row in contexts:
        c.require(row.get("device_id") == c.DEVICE and row.get("workspace_id") == c.WORKSPACE
                  and row.get("workspace_generation") == c.GENERATION and row["expires_at_ms"] <= now,
                  "UNEXPECTED_LIVE_OR_WRONG_TARGET_CONTEXT")
    for row in pilots:
        c.require(row.get("decision_id") == PRIOR_PILOT and row.get("binding_id") == c.BINDING
                  and row.get("principal_id") == c.PRINCIPAL and row.get("device_id") == c.DEVICE
                  and row.get("workspace_id") == c.WORKSPACE and row.get("workspace_generation") == c.GENERATION
                  and row["expires_at_ms"] == PRIOR_EXPIRES, "UNRELATED_UNREVOKED_PILOT_RECOVERY_WOULD_ALTER")
    prior_contexts = [row for row in overview["contexts"] if row.get("context_id") == PRIOR_CONTEXT]
    prior_pilots = [row for row in overview["scoped_pilot_decisions"] if row.get("decision_id") == PRIOR_PILOT]
    c.require(len(prior_contexts) == len(prior_pilots) == 1
              and prior_contexts[0]["expires_at_ms"] == PRIOR_EXPIRES
              and prior_pilots[0]["expires_at_ms"] == PRIOR_EXPIRES, "PREVIOUS_CONTEXT_OR_PILOT_MISSING")
    return [row["context_id"] for row in contexts], [row["decision_id"] for row in pilots]


def authority_fence(overview, close_ids, revoke_ids):
    # Only terminal timestamps may change on the exact previously-expired rows.
    def normalized(rows, key, allowed, changed):
        output = []
        for row in rows:
            item = dict(row)
            if row[key] in allowed:
                item.pop(changed, None)
            output.append(item)
        return sorted(output, key=lambda item: item[key])
    return {"contexts": c.digest(normalized(overview["contexts"], "context_id", close_ids, "closed_at_ms")),
            "pilots": c.digest(normalized(overview["scoped_pilot_decisions"], "decision_id", revoke_ids, "revoked_at_ms")),
            "context_ids": sorted(row["context_id"] for row in overview["contexts"]),
            "pilot_ids": sorted(row["decision_id"] for row in overview["scoped_pilot_decisions"])}


def preserve_authority_rows(overview, marker):
    baseline = marker["authority_initial"]
    contexts = [row for row in overview["contexts"] if row["context_id"] in baseline["context_ids"]]
    pilots = [row for row in overview["scoped_pilot_decisions"] if row["decision_id"] in baseline["pilot_ids"]]
    old = authority_fence({"contexts": contexts, "scoped_pilot_decisions": pilots}, marker["old_context_ids"], marker["old_pilot_ids"])
    c.require(old == baseline, "UNRELATED_AUTHORITY_HISTORY_CHANGED")
    added_contexts = [row for row in overview["contexts"] if row["context_id"] not in baseline["context_ids"]]
    added_pilots = [row for row in overview["scoped_pilot_decisions"] if row["decision_id"] not in baseline["pilot_ids"]]
    c.require(len(added_contexts) <= 1 and len(added_pilots) <= 1, "UNEXPECTED_ADDED_AUTHORITY_ROWS")
    for row in added_contexts:
        c.require(row.get("binding_id") == c.BINDING and row.get("device_id") == c.DEVICE
                  and row.get("workspace_id") == c.WORKSPACE and row.get("workspace_generation") == c.GENERATION
                  and row.get("closed_at_ms") is None and row["expires_at_ms"] == marker["expires_at_ms"], "NEW_CONTEXT_SCOPE_CHANGED")
    for row in added_pilots:
        c.require(row.get("binding_id") == c.BINDING and row.get("principal_id") == c.PRINCIPAL
                  and row.get("device_id") == c.DEVICE and row.get("workspace_id") == c.WORKSPACE
                  and row.get("workspace_generation") == c.GENERATION and row.get("revoked_at_ms") is None
                  and row["expires_at_ms"] == marker["expires_at_ms"] and row.get("reason") == REASON, "NEW_PILOT_SCOPE_CHANGED")
    return added_contexts, added_pilots


def marker_check(marker, snapshot, overview, grant, prior_sha, args):
    expected = {"operation": OPERATION, "binding_id": c.BINDING, "device_id": c.DEVICE, "workspace_id": c.WORKSPACE,
                "workspace_generation": c.GENERATION, "root": c.LOCAL_ROOT, "profile": c.LOCAL_PROFILE,
                "source_revision": c.REVISION, "prior_marker_sha256": prior_sha,
                "service_grant_sha256": c.digest(grant), "approval_id": args.approval_id, "approved_duration_ms": 3600000}
    c.require(all(marker.get(key) == value for key, value in expected.items()), "NEXT_MARKER_SCOPE_APPROVAL_OR_PRIOR_CHANGED")
    if "requested_at_ms" in marker:
        c.require(type(marker.get("requested_at_ms")) is int and marker.get("expires_at_ms") == marker["requested_at_ms"] + 3600000
                  and now_ms() < marker["expires_at_ms"] <= grant["expires_at_ms"], "NEXT_WINDOW_EXPIRED_NO_REANCHOR")
    else:
        c.require(marker["phase"] in {"close_prepared", "intake_closed"} and "expires_at_ms" not in marker,
                  "NEXT_UNANCHORED_PHASE_INVALID")
    c.compare_history(marker["initial_state"], snapshot, authority=True)
    return preserve_authority_rows(overview, marker)


def close_expired(origin, auth, overview, marker):
    c.require(marker["phase"] in {"close_prepared", "intake_closed"}, "NEXT_CLOSE_PHASE_CHANGED")
    c.require(overview["admission"]["admission_mode"] in {"scoped_pilot", "recovery"}, "ADMISSION_CHANGED")
    # Guard before the supported recovery API's global revocation side effect.
    current = [row for row in overview["scoped_pilot_decisions"] if row.get("revoked_at_ms") is None]
    c.require(all(row["decision_id"] in marker["old_pilot_ids"] for row in current), "UNRELATED_PILOT_BEFORE_RECOVERY")
    if overview["admission"]["admission_mode"] != "recovery":
        c.api(origin, auth, "/v1/maintenance/admission", {"mode": "recovery"})
    c.require(c.api(origin, auth, "/healthz")["admission_mode"] == "recovery", "INTAKE_NOT_RECOVERY")
    overview = c.api(origin, auth, "/v1/ui/overview")
    preserve_authority_rows(overview, marker)
    for decision_id in marker["old_pilot_ids"]:
        row = next(row for row in overview["scoped_pilot_decisions"] if row["decision_id"] == decision_id)
        if row.get("revoked_at_ms") is None:
            c.api(origin, auth, "/v1/scoped-pilot-decisions/" + decision_id + "/revoke", {})
    for context_id in marker["old_context_ids"]:
        row = next(row for row in overview["contexts"] if row["context_id"] == context_id)
        if row.get("closed_at_ms") is None:
            c.api(origin, auth, "/v1/contexts/" + context_id + "/close", {})
    overview = c.api(origin, auth, "/v1/ui/overview")
    preserve_authority_rows(overview, marker)
    c.require(not any(row.get("closed_at_ms") is None and row.get("binding_id") == c.BINDING for row in overview["contexts"])
              and not any(row.get("revoked_at_ms") is None for row in overview["scoped_pilot_decisions"]), "EXPIRED_AUTHORITY_NOT_TERMINAL")
    marker["phase"] = "intake_closed"; save(marker)


def renew(origin, auth, overview, marker, grant):
    c.require(marker["phase"] in {"intake_closed", "context_create_intended", "context_created", "pilot_create_intended", "authority_renewed"}
              and overview["admission"]["admission_mode"] == "recovery", "NEXT_RENEW_REQUIRES_RECOVERY_PHASE")
    if "requested_at_ms" not in marker:
        anchor = now_ms()
        c.require(anchor + 3600000 <= grant["expires_at_ms"], "SERVICE_GRANT_CANNOT_COVER_NEXT_WINDOW")
        marker.update(requested_at_ms=anchor, expires_at_ms=anchor + 3600000)
        save(marker)
    contexts, pilots = preserve_authority_rows(overview, marker)
    if not contexts:
        c.require(not marker.get("context_create_intended"), "CONTEXT_CREATE_OUTCOME_UNKNOWN_NO_REPLAY")
        marker.update(context_create_intended=True, phase="context_create_intended"); save(marker)
        c.api(origin, auth, "/v1/contexts", {"binding_id": c.BINDING, "expires_at_ms": marker["expires_at_ms"]})
        overview = c.api(origin, auth, "/v1/ui/overview")
        contexts, pilots = preserve_authority_rows(overview, marker)
    c.require(len(contexts) == 1, "NEW_CONTEXT_OUTCOME_NOT_UNIQUE")
    if marker.get("context_id"):
        c.require(marker["context_id"] == contexts[0]["context_id"], "NEW_CONTEXT_ID_CHANGED")
    marker.update(context_id=contexts[0]["context_id"], phase="context_created"); save(marker)
    if not pilots:
        c.require(not marker.get("pilot_create_intended"), "PILOT_CREATE_OUTCOME_UNKNOWN_NO_REPLAY")
        marker.update(pilot_create_intended=True, phase="pilot_create_intended"); save(marker)
        c.api(origin, auth, "/v1/scoped-pilot-decisions", {"principal_id": c.PRINCIPAL, "binding_id": c.BINDING,
                                                          "expires_at_ms": marker["expires_at_ms"], "reason": REASON})
        overview = c.api(origin, auth, "/v1/ui/overview")
        contexts, pilots = preserve_authority_rows(overview, marker)
    c.require(len(pilots) == 1, "NEW_PILOT_OUTCOME_NOT_UNIQUE")
    if marker.get("pilot_id"):
        c.require(marker["pilot_id"] == pilots[0]["decision_id"], "NEW_PILOT_ID_CHANGED")
    marker["pilot_id"] = pilots[0]["decision_id"]
    c.renewed_authority(overview, marker)
    marker["phase"] = "authority_renewed"; save(marker)


def reopen(origin, auth, overview, marker, args):
    c.require(marker["phase"] in {"authority_renewed", "intake_reopened"}, "NEXT_REOPEN_PHASE_CHANGED")
    c.renewed_authority(overview, marker)
    canary_window(marker, overview["observed_at_ms"])
    bootstrap_canary_directory()
    nodes = [row for row in overview["nodes"] if row.get("device_id") == c.DEVICE]
    c.require(len(nodes) == 1, "NODE_NOT_UNIQUE")
    node = nodes[0]
    for supplied, field in ((args.expected_activation_epoch, "activation_epoch"), (args.expected_runtime_instance, "runtime_instance_id"),
                            (args.expected_mcp_instance, "mcp_server_instance_id"), (args.expected_contract_version, "contract_version")):
        c.require(isinstance(supplied, str) and supplied and node.get(field) == supplied, "EXACT_CURRENT_R11_NODE_REQUIRED")
    c.require(0 <= overview["observed_at_ms"] - node.get("last_seen_at_ms", 0) < 60000
              and node.get("readiness") == "ready" and node.get("policy_state") == "enabled"
              and type(node.get("policy_expires_at_ms")) is int
              and overview["observed_at_ms"] < node["policy_expires_at_ms"] <= node["last_seen_at_ms"] + 60000,
              "NODE_NOT_FRESH_READY_CURRENT_STANDING_POLICY_TTL")
    c.require(overview["admission"]["admission_mode"] in {"recovery", "scoped_pilot"}, "NEXT_ADMISSION_CHANGED")
    if overview["admission"]["admission_mode"] == "recovery":
        c.api(origin, auth, "/v1/maintenance/admission", {"mode": "scoped_pilot"})
    c.require(c.api(origin, auth, "/healthz")["admission_mode"] == "scoped_pilot", "NEXT_SCOPED_INTAKE_NOT_REOPENED")
    marker.update(phase="intake_reopened", activation_epoch=node["activation_epoch"],
                  runtime_instance_id=node["runtime_instance_id"], mcp_server_instance_id=node["mcp_server_instance_id"],
                  contract_version=node["contract_version"], canary_directory=str(CANARY_DIR),
                  minimum_canary_remaining_ms=MIN_CANARY_REMAINING_MS)
    save(marker)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("observe", "close", "renew", "reopen"), nargs="?", default="observe")
    c.arguments(parser)
    parser.add_argument("--approval-id")
    parser.add_argument("--approved-duration-ms", type=int)
    parser.add_argument("--expected-prior-marker-sha256")
    parser.add_argument("--expected-next-marker-sha256")
    for field in ("activation-epoch", "runtime-instance", "mcp-instance", "contract-version"):
        parser.add_argument("--expected-" + field)
    args = parser.parse_args()
    origin, auth, database, health, snapshot, overview, grant = c.inspect()
    c.require(health["declared_source_revision"] == c.REVISION and health["package_source_sha256"] == c.PACKAGE, "CURRENT_MAIN_R11_REQUIRED_NO_SERVICE_CHANGE")
    prior, prior_sha = prior_marker(grant)
    next_exists = NEXT_MARKER.exists()
    next_sha = hashlib.sha256(c.protected_file(NEXT_MARKER)).hexdigest() if next_exists else "absent"
    if args.action == "observe" or not args.execute:
        marker = json.loads(c.protected_file(NEXT_MARKER)) if next_exists else {}
        c.emit("r12_read_only_observation", ok=True, remote_mutation=False,
               device_id=c.DEVICE, workspace_id=c.WORKSPACE, workspace_generation=c.GENERATION,
               root=c.LOCAL_ROOT, profile=c.LOCAL_PROFILE,
               requested_at_ms=marker.get("requested_at_ms"), expires_at_ms=marker.get("expires_at_ms"),
               context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"),
               capabilities={"read": True, "write": True, "exec": True},
               canary_directory=str(CANARY_DIR), minimum_canary_remaining_ms=MIN_CANARY_REMAINING_MS,
               prior_marker_sha256=prior_sha, prior_requested_at_ms=PRIOR_REQUESTED, prior_expires_at_ms=PRIOR_EXPIRES,
               prior_window_expired=now_ms() >= PRIOR_EXPIRES, next_marker_sha256=next_sha,
               next_operation=marker.get("operation"), next_phase=marker.get("phase"),
               next_requested_at_ms=marker.get("requested_at_ms"), next_expires_at_ms=marker.get("expires_at_ms"),
               next_context_id=marker.get("context_id"), next_pilot_id=marker.get("pilot_id"),
               **c.public_observation(health, snapshot, overview, grant))
        return
    c.guard_arguments(args, health, snapshot, grant)
    c.require(args.approved_duration_ms == 3600000 and isinstance(args.approval_id, str)
              and re.fullmatch(r"[A-Za-z0-9_-]{8,128}", args.approval_id)
              and args.approval_id != "call_flEpmLChKJPZsbnlAAXR5byS", "EXPLICIT_NEW_60M_APPROVAL_REQUIRED")
    c.require(args.expected_prior_marker_sha256 == prior_sha and args.expected_next_marker_sha256 == next_sha, "EXPECTED_IMMUTABLE_MARKER_PINS_REQUIRED")
    descriptor = c.operation_lock()
    try:
        c.require(c.state(database) == snapshot and prior_marker(grant)[1] == prior_sha, "STATE_OR_PRIOR_CHANGED_BEFORE_OWNER_LOCK")
        if next_exists:
            next_raw = c.protected_file(NEXT_MARKER)
            c.require(hashlib.sha256(next_raw).hexdigest() == next_sha, "NEXT_MARKER_CHANGED_BEFORE_OWNER_LOCK")
            marker = json.loads(next_raw)
            marker_check(marker, snapshot, overview, grant, prior_sha, args)
        else:
            c.require(args.action == "close" and not NEXT_DIR.exists() and not NEXT_DIR.is_symlink(), "NEW_NEXT_CLOSE_REQUIRED_NO_MARKER_REANCHOR")
            close_ids, revoke_ids = selected_expired(overview)
            NEXT_DIR.mkdir(parents=True, mode=0o700)
            bootstrap_canary_directory()
            marker = {"operation": OPERATION, "binding_id": c.BINDING, "device_id": c.DEVICE, "workspace_id": c.WORKSPACE,
                      "workspace_generation": c.GENERATION, "root": c.LOCAL_ROOT, "profile": c.LOCAL_PROFILE,
                      "source_revision": c.REVISION, "service_instance_id": health["service_instance_id"],
                      "prior_marker_sha256": prior_sha, "approval_id": args.approval_id, "approved_duration_ms": 3600000,
                      "service_grant_sha256": c.digest(grant), "phase": "close_prepared", "initial_state": snapshot,
                      "old_context_ids": close_ids, "old_pilot_ids": revoke_ids,
                      "authority_initial": authority_fence(overview, close_ids, revoke_ids)}
            save(marker)
        c.require(marker["service_instance_id"] == health["service_instance_id"], "SERVICE_RESTARTED_DURING_NEXT_WINDOW")
        if args.action == "close":
            close_expired(origin, auth, overview, marker)
        elif args.action == "renew":
            renew(origin, auth, overview, marker, grant)
        else:
            reopen(origin, auth, overview, marker, args)
        final_health = c.api(origin, auth, "/healthz")
        final_overview = c.api(origin, auth, "/v1/ui/overview")
        final_state = c.state(database)
        c.require(final_health["service_instance_id"] == health["service_instance_id"] and c.digest(c.target(final_overview)) == c.digest(grant)
                  and prior_marker(grant)[1] == prior_sha, "SERVICE_GRANT_OR_PRIOR_MARKER_CHANGED")
        c.compare_history(snapshot, final_state, authority=True)
        preserve_authority_rows(final_overview, marker)
        c.emit("r12_" + marker["phase"], ok=True, host=c.HOST, service=c.SERVICE, service_restarted=False, deployed=False,
               source_revision=c.REVISION, package_source_sha256=c.PACKAGE, service_instance_id=health["service_instance_id"],
               binding_id=c.BINDING, device_id=c.DEVICE, workspace_id=c.WORKSPACE, workspace_generation=c.GENERATION,
               root=c.LOCAL_ROOT, profile=c.LOCAL_PROFILE, admission=final_health["admission_mode"],
               observed_at_ms=final_overview["observed_at_ms"], state=final_state, state_sha256=c.digest(final_state),
               requested_at_ms=marker.get("requested_at_ms"), expires_at_ms=marker.get("expires_at_ms"), duration_ms=3600000,
               context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"), approval_id=marker["approval_id"],
               prior_marker_sha256=prior_sha, prior_marker_unchanged=True,
               next_marker_sha256=hashlib.sha256(c.protected_file(NEXT_MARKER)).hexdigest(),
               service_grant_sha256=c.digest(grant), service_grant_preserved=c.GRANT, service_grant_changed=False,
               action_task_history_preserved=True, remote_mutation=True,
               policy_assignment=None if not marker.get("context_id") else {"binding_id": c.BINDING, "device_id": c.DEVICE,
                 "workspace_id": c.WORKSPACE, "workspace_generation": c.GENERATION, "root": c.LOCAL_ROOT,
                 "profile": c.LOCAL_PROFILE, "context_id": marker["context_id"], "expires_at_ms": marker["expires_at_ms"]})
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN); os.close(descriptor)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        c.emit("r12_renewal_failed", ok=False, code=error.code if isinstance(error, c.GuardFailure) else "NEXT_RENEWAL_FAILED",
               next_action="READ_ONLY_INSPECT_EXACT_MARKER_STATE_NO_REANCHOR_NO_CREATION_REPLAY")
        raise SystemExit(2) from None
