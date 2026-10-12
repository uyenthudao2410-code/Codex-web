"""Guarded r11 schema28->29 rollout. Root runs it; no DB restore or automatic old-code fallback."""
from r11_common import *

def stage_release(revision):
    name = "codex-control-plane-" + revision
    require(ARTIFACT_DIR.is_relative_to(INCOMING.resolve()) and re.fullmatch(r"r11-approved-[0-9TZ]+", ARTIFACT_DIR.name), "APPROVED_ARTIFACT_DIRECTORY_REQUIRED")
    private_directory(ARTIFACT_DIR)
    archive_path = ARTIFACT_DIR / (name + ".tar.gz")
    protected_file(archive_path)
    require(file_hash(archive_path) == IDENTITIES[revision]["archive"], "ARCHIVE_HASH_CHANGED")
    with tarfile.open(archive_path, "r:gz") as archive:
        seen = set()
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            require(parts and parts[0] == name and not PurePosixPath(member.name).is_absolute() and ".." not in parts
                    and member.name not in seen and (member.isdir() or member.isfile()) and member.mode & 0o7000 == 0
                    and member.size <= 16*1024*1024, "ARCHIVE_PATH_TYPE_MODE_OR_SIZE_INVALID")
            seen.add(member.name)
        target = RELEASES / name
        if target.exists():
            require(not target.is_symlink(), "EXISTING_RELEASE_SYMLINK_DENIED")
            verify_release(target.resolve(), revision)
            return target.resolve()
        for member in archive.getmembers():
            destination = RELEASES / member.name
            if member.isdir():
                destination.mkdir(parents=True, mode=0o700, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
                with archive.extractfile(member) as source, destination.open("xb") as output:
                    while block := source.read(1024*1024):
                        output.write(block)
                os.chmod(destination, 0o755 if member.mode & 0o111 else 0o600)
        verify_release(target.resolve(), revision)
        return target.resolve()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    arguments(parser)
    args = parser.parse_args()
    origin, token, database, health, snapshot, overview, grant = inspect()
    require(health["declared_source_revision"] == BASE_REVISION and snapshot["schema_version"] == 28, "ORIGINAL_STORE395_SCHEMA28_REQUIRED")
    if not args.execute:
        emit("r11_deployment_read_only_preflight", ok=True, remote_mutation=False, **public_observation(health, snapshot, overview, grant))
        return
    guard_arguments(args, health, snapshot, grant)
    require(overview["admission"]["admission_mode"] == "recovery" and MARKER.exists(), "EXACT_R11_INTAKE_CLOSE_REQUIRED")
    marker = json.loads(protected_file(MARKER))
    require(marker.get("operation") == "owner_approved_r11_initial_verification_60m" and marker.get("phase") == "intake_closed"
            and marker.get("initial_state") == snapshot and marker.get("service_grant_sha256") == digest(grant), "R11_CLOSE_MARKER_CHANGED")
    old_link, old_env, old_drop = os.readlink(CURRENT), protected_file(ENV_FILE), protected_file(DROP_IN)
    baseline, old_pid = CURRENT.resolve(strict=True), service_pid()
    require(str(CURRENT / "deploy/control-plane-launcher.sh").encode() in run(["systemctl", "--user", "show", SERVICE, "--property=ExecStart", "--value"], code="SERVICE_COMMAND_UNAVAILABLE"), "SERVICE_LAUNCHER_MISMATCH")
    descriptor = operation_lock()
    phase = "preflight"
    try:
        require(state(database) == snapshot and os.readlink(CURRENT) == old_link and protected_file(ENV_FILE) == old_env
                and protected_file(DROP_IN) == old_drop, "PREDEPLOYMENT_CONCURRENT_CHANGE")
        require(api(origin, token, "/healthz")["admission_mode"] == "recovery", "INTAKE_REOPENED_BEFORE_DEPLOYMENT")
        private_directory(RELEASES); private_directory(INCOMING); private_directory(BACKUP_ROOT, create=True)
        backup = BACKUP_ROOT / ("r11-initial-verification-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        backup.mkdir(mode=0o700)
        atomic_bytes(backup / "control-plane.env.before", old_env)
        atomic_bytes(backup / "10-immutable-release.conf.before", old_drop)
        backup_env = dict(os.environ, PYTHONPATH=str(baseline / "control-plane"), PYTHONDONTWRITEBYTECODE="1")
        destination = backup / "control-plane-before-schema29.sqlite3"
        receipt = run_json(["/usr/bin/python3", "-B", "-m", "control_plane.maintenance", "snapshot", "--source", str(database), "--destination", str(destination)], code="VERIFIED_BACKUP_FAILED", environment=backup_env)
        os.chmod(destination, 0o600)
        inspection = run_json(["/usr/bin/python3", "-B", "-m", "control_plane.maintenance", "inspect-snapshot", "--source", str(destination), "--expected-sha256", receipt["snapshot_sha256"]], code="BACKUP_INSPECTION_FAILED", environment=backup_env)
        require(inspection.get("sqlite_integrity") == "ok" and inspection.get("schema_version") == 28, "BACKUP_INTEGRITY_FAILED")
        compare_history(snapshot, state(destination)); compare_history(snapshot, state(database))
        atomic_bytes(backup / "snapshot-receipt.json", json.dumps(receipt).encode())
        atomic_bytes(backup / "inspection-receipt.json", json.dumps(inspection).encode())
        phase = "backup_verified"
        emit(phase, ok=True, protected_backup_directory=str(backup), snapshot_sha256=receipt["snapshot_sha256"], database_restored=False)
        candidate = stage_release(REVISION)
        recovery = stage_release(RECOVERY_REVISION)
        old_files = {r["path"]: r for r in json.loads((baseline / "release-manifest.json").read_bytes())["files"]}
        new_files = {r["path"]: r for r in json.loads((candidate / "release-manifest.json").read_bytes())["files"]}
        delta = [p for p in sorted(set(old_files)|set(new_files)) if old_files.get(p) != new_files.get(p)]
        require(delta == ["control-plane/control_plane/" + p for p in ("mcp_facade.py", "node_agent.py", "recovery_approved_patch_bridge.cjs", "store.py")], "R11_RELEASE_DELTA_CHANGED")
        helper = candidate / "deploy/prepare-control-plane-activation.py"
        helper_args = ["/usr/bin/python3", "-B", str(helper), "--release-dir", str(candidate), "--env-file", str(ENV_FILE), "--drop-in", str(DROP_IN)]
        run_json(helper_args + ["--check-only"], code="ACTIVATION_CHECK_FAILED")
        require(state(database) == snapshot and os.readlink(CURRENT) == old_link and protected_file(ENV_FILE) == old_env
                and protected_file(DROP_IN) == old_drop, "CONFIGURATION_CONCURRENT_CHANGE")
        prepared = run_json(helper_args, code="ACTIVATION_PREPARATION_FAILED")
        require(prepared.get("environment_matches") is True and prepared.get("drop_in_matches") is True, "ACTIVATION_PREPARATION_MISMATCH")
        phase = "configuration_prepared"
        atomic_current(str(candidate))
        phase = "current_switched"
        run(["systemctl", "--user", "daemon-reload"], code="SYSTEMD_RELOAD_FAILED")
        phase = "restart_requested"
        run(["systemctl", "--user", "restart", SERVICE], code="SERVICE_RESTART_FAILED")
        deadline, new_health = time.monotonic()+40, None
        while time.monotonic() < deadline:
            try:
                observed = api(origin, token, "/healthz")
                if observed.get("ok") is True and observed.get("declared_source_revision") == REVISION and observed.get("schema_version") == 29:
                    new_health = observed
                    break
            except GuardFailure:
                pass
            time.sleep(.5)
        require(new_health is not None and new_health.get("package_source_sha256") == PACKAGE and new_health.get("expected_package_source_sha256") == PACKAGE
                and new_health.get("service_instance_id") != health["service_instance_id"] and new_health.get("started_at_ms", 0) > health["started_at_ms"]
                and new_health.get("admission_mode") == "recovery" and service_pid() != old_pid and CURRENT.resolve() == candidate, "NEW_R11_SERVICE_INSTANCE_NOT_PROVEN")
        verify_release(candidate, REVISION)
        final_state = state(database)
        compare_history(snapshot, final_state, migration=True)
        require(final_state["schema_version"] == 29, "DATABASE_SCHEMA29_NOT_PROVEN")
        final_overview = api(origin, token, "/v1/ui/overview")
        require(digest(target(final_overview)) == digest(grant), "SERVICE_GRANT_MUTATED")
        emit("deployment_complete", ok=True, host=HOST, service=SERVICE, source_revision=REVISION, package_source_sha256=PACKAGE,
             binding_id=BINDING, admission="recovery", observed_at_ms=final_overview["observed_at_ms"], service_instance_id=new_health["service_instance_id"],
             state=final_state, state_sha256=digest(final_state), service_grant_sha256=digest(grant), file_count=38,
             release_delta=delta, snapshot_sha256=receipt["snapshot_sha256"], protected_backup_directory=str(backup),
             staged_recovery_release=str(recovery), recovery_source_revision=RECOVERY_REVISION, recovery_activated=False,
             database_restored=False, authority_renewed=False, remote_mutation=True, next_action="FRESH_R11_OBSERVE_THEN_EXACT60M_RENEWAL_AND_WINDOWS_POLICY_ACTIVATION")
    except Exception as error:
        emit("deployment_failed", ok=False, phase_reached=phase, code=error.code if isinstance(error, GuardFailure) else "R11_DEPLOYMENT_FAILED",
             database_restored=False, automatic_schema28_fallback=False, next_action="KEEP_INTAKE_CLOSED_INSPECT_CONFIG_CURRENT_SCHEMA_AND_SERVICE_USE_SCHEMA29_RECOVERY_ONLY_IF_EXPLICITLY_DIRECTED")
        raise SystemExit(2) from None
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        emit("r11_deployment_preflight_failed", ok=False, code=error.code if isinstance(error, GuardFailure) else "R11_DEPLOYMENT_PREFLIGHT_FAILED", remote_mutation=False)
        raise SystemExit(2) from None
