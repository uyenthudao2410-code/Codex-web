"""Stage only the owner-approved immutable r10 Store archive; no service/API operation."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import sys

ROOT = Path('/home/svhome/.local/lib/codex-control-plane/incoming')
NAME = 'codex-control-plane-395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5.tar.gz'
SHA = 'bf76625554e32478202191c29ccdea0790448a47971db30af54a7aa5959d9061'
STAGING = ROOT / 'r10-approved-20261011T123342Z'

def require(ok):
    if not ok:
        raise RuntimeError('STAGE_GUARD_REFUSED')

def private(directory):
    require(directory.is_dir() and not directory.is_symlink())
    info = directory.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700)

def file_hash(file):
    require(file.is_file() and not file.is_symlink() and file.stat().st_uid == os.getuid())
    return hashlib.sha256(file.read_bytes()).hexdigest()

try:
    require(pwd.getpwuid(os.getuid()).pw_name == 'svhome')
    private(ROOT)
    target = ROOT / NAME
    action = sys.argv[1]
    if action == 'prepare':
        require(not STAGING.exists() and not STAGING.is_symlink())
        require(not target.exists() or file_hash(target) == SHA)
        STAGING.mkdir(mode=0o700)
        print(json.dumps({'phase': 'approved_archive_staging_prepared', 'ok': True,
                          'staging': str(STAGING), 'target_preexists': target.exists(), 'service_changed': False}))
    elif action == 'publish':
        private(STAGING)
        source = STAGING / NAME
        require(file_hash(source) == SHA)
        os.chmod(source, 0o600)
        if target.exists():
            require(file_hash(target) == SHA)
        else:
            os.link(source, target)
        require(file_hash(target) == SHA and stat.S_IMODE(target.stat().st_mode) == 0o600)
        print(json.dumps({'phase': 'approved_archive_staged', 'ok': True, 'archive': str(target),
                          'archive_sha256': SHA, 'service_changed': False}))
    else:
        require(False)
except Exception:
    print(json.dumps({'phase': 'approved_archive_staging_refused', 'ok': False,
                      'code': 'STAGE_GUARD_REFUSED', 'service_changed': False}))
    raise SystemExit(2) from None
