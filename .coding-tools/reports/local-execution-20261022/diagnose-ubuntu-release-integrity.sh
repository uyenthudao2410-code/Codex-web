python3 - <<'PY_RELEASE_DIAGNOSTIC'
"""Read only: report relative release paths and hashes, never file contents."""
import hashlib
import json
from pathlib import Path
import stat

root = Path('/home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-parallel-native-1012-f7acd9ec4ba1')
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = (root / 'release-manifest.json').read_bytes()
if sha(manifest) != 'c65439e1de52b741483debfd0600b52e7d969a8641818c554071990d4b3b1a3d':
    raise SystemExit('BASELINE_MANIFEST_CHANGED; no files changed')
expected = {record['path']: record for record in json.loads(manifest)['files']}
actual, issues = {}, []
for path in root.rglob('*'):
    relative = path.relative_to(root).as_posix()
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        issues.append({'issue': 'SYMLINK', 'path': relative})
    elif stat.S_ISREG(mode):
        actual[relative] = path
    elif not stat.S_ISDIR(mode):
        issues.append({'issue': 'UNSUPPORTED_ENTRY', 'path': relative})
for relative in sorted(set(actual) - set(expected) - {'release-manifest.json'}):
    issues.append({'issue': 'EXTRA_FILE', 'path': relative})
for relative, record in expected.items():
    if relative not in actual:
        issues.append({'issue': 'MISSING_REGULAR_FILE', 'path': relative})
    else:
        content = actual[relative].read_bytes()
        digest = sha(content)
        if len(content) != record['size_bytes'] or digest != record['sha256']:
            issues.append({'issue': 'FILE_BYTES_CHANGED', 'path': relative,
                           'expected_sha256': record['sha256'], 'actual_sha256': digest})
print(json.dumps({'read_only': True, 'issue_count': len(issues), 'issues': issues[:100],
                  'truncated': len(issues) > 100}, indent=2))

PY_RELEASE_DIAGNOSTIC
