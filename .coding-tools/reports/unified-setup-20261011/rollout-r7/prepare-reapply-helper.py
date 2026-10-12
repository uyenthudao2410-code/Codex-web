"""Repair postflight byte oracle and reuse protected prior attempt artifacts."""
from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
original = (here / 'ubuntu-console-rollout.py').read_text()
def once(text, old, new):
    assert text.count(old) == 1
    return text.replace(old, new, 1)
reapply = once(original, 'require(original_admission == "scoped_pilot", "ORIGINAL_ADMISSION_NOT_SCOPED_PILOT")', 'require(original_admission == "recovery", "REAPPLY_REQUIRES_CLOSED_INTAKE")')
start = reapply.index('        backup_directory.mkdir(mode=0o700)')
end = reapply.index('        candidate_receipt = verify_release(candidate, REVISION, PACKAGE)', start)
replacement = '''        private_directory(backup_directory)
        require(protected_file(backup_directory / "control-plane.env.before") == old_env
                and protected_file(backup_directory / "10-immutable-release.conf.before") == old_drop_in,
                "RETAINED_BACKUP_BASELINE_MISMATCH")
        snapshot = json.loads(protected_file(backup_directory / "snapshot-receipt.json"))
        snapshot_path = backup_directory / "control-plane-before-hotfix.sqlite3"
        require(file_hash(snapshot_path) == snapshot["snapshot_sha256"], "RETAINED_SNAPSHOT_HASH_MISMATCH")
        require_quiescent(snapshot_path, expected=initial_counts)
        require_quiescent(database, expected=initial_counts)
        emit("retained_backup_verified", ok=True, protected_backup_directory=str(backup_directory),
             snapshot_sha256=snapshot["snapshot_sha256"], schema_version=SCHEMA, overwritten=False)
        candidate = (RELEASES / RELEASE_NAME).resolve(strict=True)
'''
reapply = reapply[:start] + replacement + reapply[end:]
reapply = once(reapply, 'hashlib.sha256(v.encode()).hexdigest()', 'hashlib.sha256(v).hexdigest()')
compile(reapply, 'ubuntu-console-reapply.py', 'exec')
path = here / 'ubuntu-console-reapply.py'
assert not path.exists()
path.write_text(reapply, encoding='utf-8', newline='\n')
print(json.dumps({'operation':'console_reapply_helper_prepared','python_syntax':'pass','sha256':hashlib.sha256(reapply.encode()).hexdigest(),'source_package_modified':False,'retained_artifacts_overwritten':False}))
