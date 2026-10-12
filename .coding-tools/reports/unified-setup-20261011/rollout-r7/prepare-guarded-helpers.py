"""Freeze existing guarded driver with exact Console-only rollout constants."""
from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
prior = here.parents[1] / 'mcp-web-contract-20261011'
provenance = json.loads((here / 'snapshot-provenance.json').read_text())
original = (prior / 'ubuntu-rollout-driver.py').read_text()
def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)
driver = original
for old, new in [
    ('BASE_REVISION = "70de202d93c9a759befe5d38491ce54e9ef4b3cd"', 'BASE_REVISION = "beaa9d5ade4926ef231e3ec9d0a517fe93830e90"'),
    ('BASE_PACKAGE = "sha256:fd5132676f1a68e875348fe790c6803c591f65a73311d793194c20a4e70b7d81"', 'BASE_PACKAGE = "sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835"'),
    ('REVISION = "beaa9d5ade4926ef231e3ec9d0a517fe93830e90"\nPACKAGE', 'REVISION = "' + provenance['source_revision'] + '"\nPACKAGE'),
    ('PACKAGE = "sha256:acb5ae4713844015e32ee5005001583ae4c04e650c68fb599b22309c65dd2835"\nARCHIVE_SHA256', 'PACKAGE = "' + provenance['package_source_sha256'] + '"\nARCHIVE_SHA256'),
    ('ARCHIVE_SHA256 = "e31132a545da55cad564a373c138bb644917c8cbce73e87b724c88dfee6f3b36"', 'ARCHIVE_SHA256 = "' + provenance['archive_sha256'] + '"'),
    ('("mcp-web-contract-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))', '"unified-setup-r7-' + provenance['source_revision'][:16] + '"'),
    ('require(delta == ["DEPLOYMENT.md", "control-plane/control_plane/mcp_facade.py", "control-plane/control_plane/mcp_status.py", "control-plane/control_plane/node_agent.py"], "UNRELATED_RELEASE_DELTA")', 'require(delta == ["control-plane/control_plane/web_ui.py"], "UNRELATED_RELEASE_DELTA")\n        require(file_hash(candidate / delta[0]) == "' + provenance['frozen_web_ui_sha256'] + '", "FROZEN_CONSOLE_DELTA_MISMATCH")\n        require(canonical_digest(new_manifest["files"]) == REVISION, "SOURCE_SNAPSHOT_IDENTITY_MISMATCH")'),
    ('require_quiescent(database, expected=initial_counts)\n        private_directory(BACKUP_ROOT, create=True)', 'require_quiescent(database, expected=initial_counts)\n        emit("intake_closed", ok=True, admission="recovery", host=HOST, service=SERVICE, observed_at_ms=int(time.time() * 1000))\n        private_directory(BACKUP_ROOT, create=True)'),
    ('if not reopen_pending:\n            json_request(origin, token, "/v1/maintenance/admission", {"mode": original_admission})', 'require(reopen_pending, "UNEXPECTED_LIVE_DECISION_AFTER_CLOSURE")'),
    ('require(final_admission == ("recovery" if reopen_pending else original_admission), "FINAL_ADMISSION_MISMATCH")', 'require(final_admission == "recovery", "FINAL_ADMISSION_MISMATCH")\n        ui_environment = dict(os.environ, PYTHONPATH=str(candidate / "control-plane"), PYTHONDONTWRITEBYTECODE="1")\n        expected_ui = run_json(["/usr/bin/python3", "-B", "-c", "import hashlib,json; from control_plane.web_ui import WEB_UI_HTML,WEB_UI_JAVASCRIPT; print(json.dumps({k:hashlib.sha256(v.encode()).hexdigest() for k,v in [(\'/\',WEB_UI_HTML),(\'/assets/control-plane-ui.js\',WEB_UI_JAVASCRIPT)]}))"], code="CONSOLE_EXPECTED_HASH_FAILED", environment=ui_environment)\n        for ui_route, expected_hash in expected_ui.items():\n            try:\n                with urllib.request.urlopen(origin + ui_route, timeout=10) as response:\n                    actual_ui = response.read(1024 * 1024)\n            except OSError:\n                raise GuardFailure("CONSOLE_HTTP_VERIFY_FAILED") from None\n            require(hashlib.sha256(actual_ui).hexdigest() == expected_hash, "CONSOLE_SERVED_BYTES_MISMATCH")\n        emit("console_served_bytes_verified", ok=True, sha256=expected_ui)'),
]:
    driver = replace_once(driver, old, new)
compile(driver, 'ubuntu-console-rollout.py', 'exec')
(here / 'ubuntu-console-rollout.py').write_text(driver, encoding='utf-8', newline='\n')
definitions = driver.split('\ndef main() -> int:', 1)[0]
renewal = (prior / 'ubuntu-renew-tail.py').read_text()
renewal = replace_once(renewal, 'BACKUP = BACKUP_ROOT / "mcp-web-contract-20261011T082438Z"', 'BACKUP = BACKUP_ROOT / "unified-setup-r7-' + provenance['source_revision'][:16] + '"')
renewal = replace_once(renewal, 'Owner-approved beaa9d5a rollout:', 'Owner-approved frozen Console r7 rollout:')
renewal = replace_once(renewal, 'INSTALL_SAME_SCOPE_WINDOWS_POLICY_AND_ACTIVATE_R4', 'INSTALL_SAME_SCOPE_WINDOWS_POLICY_AFTER_R7_ACTIVATION')
helper = definitions + '\n' + renewal
compile(helper, 'ubuntu-same-scope-renewal.py', 'exec')
(here / 'ubuntu-same-scope-renewal.py').write_text(helper, encoding='utf-8', newline='\n')
print(json.dumps({
    'operation': 'guarded_helpers_frozen',
    'rollout_driver_sha256': hashlib.sha256(driver.encode()).hexdigest(),
    'renewal_helper_sha256': hashlib.sha256(helper.encode()).hexdigest(),
    'renewal_executed': False,
    'python_syntax': 'pass',
}, sort_keys=True))
