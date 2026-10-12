"""Read-only, content-free timings for the packaged Gate 0 census."""
import faulthandler
import json
from pathlib import Path
import sys
import time

repo = Path(__file__).resolve().parents[3]
module_root = repo / 'dist/windows-candidate-mxc-wsb-cbe1774-mcp-feedback-1011-r4/win-unpacked/resources/resources/coding-tools-mcp'
sys.path.insert(0, str(module_root))
sys.path.insert(1, str(module_root / 'python_vendor'))
started = time.monotonic()

def emit(phase, **fields):
    print(json.dumps({'phase': phase, 'elapsed_seconds': round(time.monotonic() - started, 3), **fields}), flush=True)

faulthandler.dump_traceback_later(20, repeat=True)
emit('imports_begin')
from coding_tools_mcp import lifecycle_census as census_module
emit('imports_complete')
original_observer = census_module.observe_process_identity

def observed_process(pid, token):
    emit('process_probe_begin', pid=int(pid))
    result = original_observer(pid, token)
    emit('process_probe_complete', pid=int(pid), exists=result.exists, identity=result.identity)
    return result

census_module.observe_process_identity = observed_process
emit('snapshot_begin')
with census_module.open_lifecycle_census_snapshot(repo) as snapshot:
    emit('snapshot_complete', size_bytes=snapshot.snapshot_metadata['size_bytes'], logical_sha256=snapshot.snapshot_metadata['logical_sha256'])
    projection = census_module.read_task_projection(repo)
    emit('projection_complete', context_count=projection.get('context_count'))
    result = census_module.lifecycle_census(snapshot, workspace=repo, observed_at=time.time(), grace_seconds=15*60, stale_after_seconds=24*60*60, projection=projection)
    emit('classification_complete', summary=result['summary'], content_free=result['content_free'], mutated_canonical_ledger=result['mutated_canonical_ledger'])
faulthandler.cancel_dump_traceback_later()
emit('complete')
