"""Reviewed exact pilot transfer using supported operator APIs only.

Default is read-only preflight. Mutation requires --confirm-transfer after the
new machine is READY and the reviewed continuity overlay is serving. The old
pilot revocation is explicitly user-authorized; expiry/principal/grants stay
pinned. Failures after entering recovery remain fail-closed for operator review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEVICE = "4c4b7a5b-7744-49ae-a490-78a528a00471"
ENDPOINT = "executor-4c4b7a5b-7744-49ae-a490-78a528a00471"
WORKSPACE = "workspace_f93b5bac9dc74fae9cea66f44c4ebc94"
GENERATION = "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"
BINDING = "bind_71661b1046884174b01c99af5f8546aa"
OLD_DEVICE = "72ceec2d-e3f2-472f-8e3c-99fffe053035"
OLD_PILOT = "pilot_7177a7cd197c4944ae77ebc1c4d433a3"
OLD_BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
PRINCIPAL = "svcprn_cd98750c7c7e45678d201066dc1b7d7a"
GRANT = "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd"
EXPIRY = 1791776571067  # User-approved 2026-10-12T10:42:51.067+07:00, never extended here.
STORE_SHA = "e5b3b8e2a63e2e4144f9f782b275b4ecc056e8c1f642c91cc9647cb6b6d6667c"
HISTORY_SHA = "724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f"
HISTORY = {"act_048df93488874a70aa97a7ee18ccbd03", "act_744496c6bd514d38a746cf8819aae9ad"}
ORIGIN = "https://svhome.tail0e4032.ts.net"
STAGE = "preflight"


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def history(con):
    families = []
    for action in sorted(HISTORY):
        family = {"action_id": action}
        for table in ("actions", "action_reconciliations", "delivery_attempts", "receipts"):
            family[table] = sorted([dict(row) for row in con.execute(
                "SELECT * FROM " + table + " WHERE action_id=?", (action,)
            )], key=lambda row: json.dumps(row, sort_keys=True))
        families.append(family)
    return digest(families)


def quiescent(con):
    for device in (DEVICE, OLD_DEVICE):
        require(con.execute("SELECT COUNT(*) FROM mcp_task_sessions WHERE device_id=? AND closed_at_ms IS NULL",
                            (device,)).fetchone()[0] == 0, "DEVICE_OPEN_TASK")
        require(con.execute("SELECT COUNT(*) FROM mcp_task_writer_leases l JOIN mcp_task_sessions t ON t.task_id=l.task_id "
                            "WHERE t.device_id=? AND l.released_at_ms IS NULL", (device,)).fetchone()[0] == 0,
                "DEVICE_UNRELEASED_WRITER")
        rows = con.execute("SELECT a.action_id,a.tool_name,a.expires_at_ms,a.delivery_state,r.disposition FROM actions a "
                           "LEFT JOIN action_reconciliations r ON r.action_id=a.action_id "
                           "WHERE a.device_id=? AND a.settled_at_ms IS NULL", (device,)).fetchall()
        require({row["action_id"] for row in rows} == (HISTORY if device == DEVICE else set()),
                "DEVICE_UNSETTLED_ACTION_SET_CHANGED")
        require(all(row["tool_name"] == "workspace_context" and row["expires_at_ms"] < int(time.time()*1000)
                    and row["delivery_state"] == "reconcile_required" and row["disposition"] == "quarantined_unknown"
                    for row in rows), "DEVICE_UNSETTLED_ACTION_NOT_HISTORICAL_QUARANTINE")
    require(history(con) == HISTORY_SHA, "HISTORICAL_FAMILY_DRIFT")


def main():
    global STAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-activation-epoch", required=True)
    parser.add_argument("--confirm-transfer", action="store_true")
    args = parser.parse_args()
    require(bool(args.expected_activation_epoch.strip()), "ACTIVATION_EPOCH_REQUIRED")
    pid = int(subprocess.check_output(["systemctl", "--user", "show", "codex-control-plane.service",
                                      "--property=MainPID", "--value"], text=True).strip())
    env = dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in item)
    token = env.get("CONTROL_PLANE_OPERATOR_TOKEN", "")
    require(bool(token), "OPERATOR_CREDENTIAL_MISSING")
    for folder in env.get("PYTHONPATH", "").split(":"):
        if folder:
            sys.path.insert(0, folder)
    from control_plane.store import ControlPlaneStore
    import control_plane.store as serving
    require(hashlib.sha256(Path(serving.__file__).read_bytes()).hexdigest() == STORE_SHA,
            "REVIEWED_CONTINUITY_OVERLAY_NOT_SERVING")
    store = object.__new__(ControlPlaneStore)
    store.clock = lambda: int(time.time()*1000)
    database = Path(env["CONTROL_PLANE_DB"])
    if not database.is_absolute():
        database = Path(f"/proc/{pid}/cwd").resolve()/database
    con = sqlite3.connect(database.resolve().as_uri()+"?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.row_factory = sqlite3.Row

    def api(path, body):
        request = urllib.request.Request(ORIGIN+path, data=json.dumps(body).encode(),
                                         headers={"Authorization": "Bearer "+token, "Content-Type": "application/json"},
                                         method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read(65536))

    def grants():
        return [dict(row) for row in con.execute("SELECT * FROM mcp_service_grants WHERE principal_id=? ORDER BY grant_id",
                                                (PRINCIPAL,))]

    try:
        now = int(time.time()*1000)
        require(now < EXPIRY <= now+24*60*60*1000, "APPROVED_EXPIRY_NOT_CURRENT")
        quiescent(con)
        mode = con.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()[0]
        require(mode == "scoped_pilot", "ADMISSION_MODE_CHANGED")
        pilots = con.execute("SELECT * FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL").fetchall()
        require(len(pilots) == 1 and pilots[0]["decision_id"] == OLD_PILOT and pilots[0]["device_id"] == OLD_DEVICE
                and pilots[0]["binding_id"] == OLD_BINDING and pilots[0]["principal_id"] == PRINCIPAL
                and pilots[0]["expires_at_ms"] == EXPIRY, "OLD_PILOT_SCOPE_OR_EXPIRY_CHANGED")
        target = con.execute("SELECT b.*,nw.capabilities_json,nw.retired_at_ms,n.readiness,n.last_seen_at_ms,"
                             "n.activation_epoch,n.policy_state,n.policy_expires_at_ms,n.revoked_at_ms AS node_revoked "
                             "FROM bindings b JOIN node_workspaces nw ON nw.device_id=b.device_id AND nw.workspace_id=b.workspace_id "
                             "AND nw.workspace_generation=b.workspace_generation JOIN nodes n ON n.device_id=b.device_id "
                             "WHERE b.binding_id=?", (BINDING,)).fetchone()
        require(target is not None and target["owner_id"] == "owner_default" and target["device_id"] == DEVICE
                and target["endpoint_id"] == ENDPOINT and target["workspace_id"] == WORKSPACE
                and target["workspace_generation"] == GENERATION and target["revoked_at_ms"] is None
                and target["retired_at_ms"] is None and target["node_revoked"] is None
                and json.loads(target["capabilities_json"]) == {"read": True,"write": True,"exec": True},
                "NEW_TARGET_NOT_EXACT_CURRENT_CODING_SCOPE")
        require(target["readiness"] == "ready" and now-target["last_seen_at_ms"] < 60_000
                and target["activation_epoch"] == args.expected_activation_epoch
                and target["policy_state"] == "enabled" and target["policy_expires_at_ms"] > now,
                "NEW_MACHINE_READY_HEARTBEAT_NOT_CURRENT")
        grant_rows = grants()
        live = [row for row in grant_rows if row["revoked_at_ms"] is None and row["expires_at_ms"] > now]
        require(len(live) == 1 and live[0]["grant_id"] == GRANT and live[0]["owner_id"] == "owner_default"
                and set(json.loads(live[0]["scopes_json"])) == {"control-plane.inventory","control-plane.read","control-plane.patch"},
                "EXISTING_PRINCIPAL_GRANT_SCOPE_CHANGED")
        blocking = store._blocking_unresolved_action_count_for_pilot(
            con, device_id=DEVICE, owner_id="owner_default", principal_id=PRINCIPAL, binding_id=BINDING,
            workspace_id=WORKSPACE, workspace_generation=GENERATION,
        )
        require(blocking == 0, "NEW_TARGET_PILOT_ELIGIBILITY_BLOCKED")
        receipt = {"operation":"exact_new_machine_pilot_transfer", "preflight":"pass", "service_pid":pid,
                   "old_pilot":OLD_PILOT,"new_binding":BINDING,"new_generation":GENERATION,
                   "principal_id":PRINCIPAL,"grant_id":GRANT,"preserved_expires_at_ms":EXPIRY,
                   "historical_family_sha256":HISTORY_SHA,"grant_is_target_bound":False,"authority_mutations":False}
        if not args.confirm_transfer:
            print(json.dumps(receipt,separators=(",",":")))
            return
        STAGE = "enter_recovery"
        quiescent(con)
        result = api("/v1/maintenance/admission", {"mode":"recovery"})
        require(result.get("admission_mode") == "recovery", "RECOVERY_RESULT_INVALID")
        require(con.execute("SELECT revoked_at_ms FROM scoped_pilot_decisions WHERE decision_id=?",(OLD_PILOT,)).fetchone()[0] is not None,
                "AUTHORIZED_OLD_PILOT_NOT_REVOKED")
        quiescent(con)
        require(grants() == grant_rows, "SERVICE_GRANTS_DRIFTED")
        STAGE = "create_new_exact_pilot"
        result = api("/v1/scoped-pilot-decisions", {
            "principal_id":PRINCIPAL,"binding_id":BINDING,"expires_at_ms":EXPIRY,
            "reason":"User-authorized transfer to DESKTOP-63643J4 exact Codex-web replacement generation; preserve original expiry and unknown read evidence.",
        })
        require(result.get("principal_id") == PRINCIPAL and result.get("binding_id") == BINDING
                and result.get("device_id") == DEVICE and result.get("workspace_id") == WORKSPACE
                and result.get("workspace_generation") == GENERATION and result.get("expires_at_ms") == EXPIRY
                and result.get("revoked_at_ms") is None, "NEW_PILOT_RESULT_NOT_EXACT")
        STAGE = "reopen_scoped_pilot"
        require(api("/v1/maintenance/admission", {"mode":"scoped_pilot"}).get("admission_mode") == "scoped_pilot",
                "SCOPED_PILOT_RESULT_INVALID")
        current = con.execute("SELECT decision_id FROM scoped_pilot_decisions WHERE revoked_at_ms IS NULL AND expires_at_ms>?",
                              (int(time.time()*1000),)).fetchall()
        require(len(current) == 1 and current[0]["decision_id"] == result["decision_id"], "FINAL_LIVE_PILOT_NOT_EXACT")
        quiescent(con)
        require(grants() == grant_rows, "SERVICE_GRANTS_DRIFTED")
        receipt.update({"authority_mutations":True,"new_pilot":result["decision_id"],"old_pilot_revoked_as_authorized":True,
                        "final_admission_mode":"scoped_pilot","service_grants_unchanged":True,
                        "historical_families_unchanged":True,"completed_at_ms":int(time.time()*1000)})
        print(json.dumps(receipt,separators=(",",":")))
    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation":"exact_new_machine_pilot_transfer","ok":False,"stage":STAGE,"error_code":code,
                          "operator_action":"Inspect admission and exact pilot metadata; do not retry an uncertain mutation blindly."},separators=(",",":")))
        sys.exit(1)
