"""Explicit emergency schema29 recovery activation; no automatic fallback or DB restore."""
from r11_common import *

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    arguments(parser)
    parser.add_argument("--expected-current-link")
    args = parser.parse_args()
    require(os.name == "posix" and pwd.getpwuid(os.getuid()).pw_name == USER, "EXECUTION_USER_MISMATCH")
    require(HOST in run(["tailscale", "ip", "-4"], code="TAILSCALE_IDENTITY_UNAVAILABLE").decode().split(), "SERVER_ADDRESS_MISMATCH")
    values = environment()
    database = Path(values["CONTROL_PLANE_DB"])
    snapshot = state(database)
    require(snapshot["schema_version"] == 29 and CURRENT.is_symlink(), "RECOVERY_REQUIRES_CURRENT_SCHEMA29")
    candidate = (RELEASES / ("codex-control-plane-" + REVISION)).resolve(strict=True)
    recovery = (RELEASES / ("codex-control-plane-" + RECOVERY_REVISION)).resolve(strict=True)
    require(CURRENT.resolve(strict=True) == candidate and values.get("CONTROL_PLANE_DECLARED_SOURCE_REVISION") == REVISION
            and values.get("CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256") == PACKAGE, "RECOVERY_REQUIRES_EXACT_R11_CURRENT_AND_CONFIG")
    verify_release(candidate, REVISION); verify_release(recovery, RECOVERY_REVISION)
    with closing(sqlite3.connect(database.as_uri()+"?mode=ro", uri=True)) as con:
        row = con.execute("SELECT state_value FROM control_plane_state WHERE state_key='admission_mode'").fetchone()
        require(row is not None and row[0] == "recovery", "RECOVERY_REQUIRES_PERSISTED_CLOSED_INTAKE")
    old_link = os.readlink(CURRENT)
    if not args.execute:
        emit("r11_recovery_read_only_preflight", ok=True, host=HOST, service=SERVICE, observed_at_ms=int(time.time()*1000),
             current_link=old_link, state=snapshot, state_sha256=digest(snapshot), admission="recovery", remote_mutation=False,
             recovery_source_revision=RECOVERY_REVISION)
        return
    require(args.operator_approved and args.confirm_target == HOST and args.expected_current_link == old_link
            and args.expected_state_sha256 == digest(snapshot) and type(args.observed_at_ms) is int
            and 0 <= int(time.time()*1000)-args.observed_at_ms < 60000, "EXPLICIT_RECOVERY_TARGET_AND_FRESH_PINS_REQUIRED")
    descriptor = operation_lock()
    try:
        compare_history(snapshot,state(database))
        require(os.readlink(CURRENT)==old_link,"CURRENT_CHANGED_BEFORE_RECOVERY")
        private_directory(BACKUP_ROOT,create=True)
        backup=BACKUP_ROOT/("r11-schema29-recovery-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        backup.mkdir(mode=0o700)
        atomic_bytes(backup/"control-plane.env.before",protected_file(ENV_FILE))
        atomic_bytes(backup/"10-immutable-release.conf.before",protected_file(DROP_IN))
        backup_env=dict(os.environ,PYTHONPATH=str(candidate/"control-plane"),PYTHONDONTWRITEBYTECODE="1")
        destination=backup/"control-plane-current-schema29.sqlite3"
        receipt=run_json(["/usr/bin/python3","-B","-m","control_plane.maintenance","snapshot","--source",str(database),"--destination",str(destination)],code="RECOVERY_BACKUP_FAILED",environment=backup_env)
        os.chmod(destination,0o600)
        inspection=run_json(["/usr/bin/python3","-B","-m","control_plane.maintenance","inspect-snapshot","--source",str(destination),"--expected-sha256",receipt["snapshot_sha256"]],code="RECOVERY_BACKUP_INSPECTION_FAILED",environment=backup_env)
        require(inspection.get("sqlite_integrity")=="ok" and inspection.get("schema_version")==29,"RECOVERY_BACKUP_INVALID")
        compare_history(snapshot,state(destination));compare_history(snapshot,state(database))
        atomic_bytes(backup/"snapshot-receipt.json",json.dumps(receipt).encode())
        atomic_bytes(backup/"inspection-receipt.json",json.dumps(inspection).encode())
        prepared=run_json(["/usr/bin/python3","-B",str(recovery/"deploy/prepare-control-plane-activation.py"),"--release-dir",str(recovery),"--env-file",str(ENV_FILE),"--drop-in",str(DROP_IN)],code="RECOVERY_ACTIVATION_PREPARATION_FAILED")
        require(prepared.get("environment_matches") is True and prepared.get("drop_in_matches") is True,"RECOVERY_CONFIG_MISMATCH")
        require(os.readlink(CURRENT)==old_link,"CURRENT_CHANGED_DURING_RECOVERY_PREPARATION")
        atomic_current(str(recovery))
        run(["systemctl","--user","daemon-reload"],code="RECOVERY_SYSTEMD_RELOAD_FAILED")
        run(["systemctl","--user","restart",SERVICE],code="RECOVERY_SERVICE_RESTART_FAILED")
        origin="http://127.0.0.1:"+values.get("CONTROL_PLANE_PORT","8765")
        health=None;deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            try:
                row=api(origin,values["CONTROL_PLANE_OPERATOR_TOKEN"],"/healthz")
                if row.get("ok") is True and row.get("declared_source_revision")==RECOVERY_REVISION:health=row;break
            except GuardFailure:pass
            time.sleep(.5)
        require(health is not None and health.get("schema_version")==29 and health.get("package_source_sha256")==RECOVERY_PACKAGE
                and health.get("expected_package_source_sha256")==RECOVERY_PACKAGE and health.get("admission_mode")=="recovery","RECOVERY_SERVICE_NOT_PROVEN")
        compare_history(snapshot,state(database))
        emit("schema29_recovery_activated",ok=True,host=HOST,service=SERVICE,source_revision=RECOVERY_REVISION,
             admission="recovery",observed_at_ms=int(time.time()*1000),state=snapshot,state_sha256=digest(snapshot),
             service_instance_id=health["service_instance_id"],database_restored=False,authority_renewed=False,
             new_intake_or_dispatch_enabled=False,protected_backup_directory=str(backup),snapshot_sha256=receipt["snapshot_sha256"],remote_mutation=True)
    finally:
        fcntl.flock(descriptor,fcntl.LOCK_UN);os.close(descriptor)

if __name__=="__main__":
    try:main()
    except Exception as error:
        emit("r11_explicit_recovery_failed",ok=False,code=error.code if isinstance(error,GuardFailure) else "R11_RECOVERY_FAILED",database_restored=False,
             next_action="KEEP_INTAKE_CLOSED_RECONCILE_EXACT_CONFIG_CURRENT_SERVICE_AND_SCHEMA29_NO_OLD_SNAPSHOT_RESTORE")
        raise SystemExit(2) from None
