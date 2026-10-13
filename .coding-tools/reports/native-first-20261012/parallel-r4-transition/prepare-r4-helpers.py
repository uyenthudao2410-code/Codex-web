"""Prepare dated r3 -> r4 helpers and immutable retirement evidence; no runtime calls."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREVIOUS = HERE.with_name("parallel-r3-transition")
OLD = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r3/win-unpacked"
NEW = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked"
OWNER = {"owner_pid": 12604, "owner_process_start_token": "134362825905927480",
         "instance_id": "c05d5a902dc55835b2cdc9263799dea7",
         "installation_id": "1db86beab972872a3361551fcae3d06bf8065f37027effa20b030a8cb921a606"}
EPOCH = "activation-mv58t4he-c162dd8a1c513c77581c5adee2ae6762"


def sha(file):
    digest = hashlib.sha256()
    with file.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(file):
    return json.loads(file.read_text(encoding="utf-8-sig"))


def exclusive(file, value):
    with file.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def version_map(text):
    return text.replace("r2", "__OLD_VERSION__").replace("r3", "__NEW_VERSION__") \
        .replace("R2", "__OLD_CAPS__").replace("R3", "__NEW_CAPS__") \
        .replace("__OLD_VERSION__", "r3").replace("__NEW_VERSION__", "r4") \
        .replace("__OLD_CAPS__", "R3").replace("__NEW_CAPS__", "R4")


def main():
    status_path = PREVIOUS / "status-1791811659906-a73e943e.json"
    status = read(status_path)
    assert status["ok"] and status["candidate"].lower() == str(OLD).lower()
    assert status["receipt"]["owner"] == OWNER
    assert status["receipt"]["activation"]["activation_epoch_id"] == EPOCH
    old_parity_path = HERE.parent / "parallel-r3-candidate-parity.json"
    old_smoke_path = HERE.parent / "parallel-r3-packaged-smoke.json"
    parity, smoke = read(old_parity_path), read(old_smoke_path)
    assert parity["ok"] and smoke["ok"] and parity["candidate"].lower() == str(OLD).lower()
    assert parity["executable_sha256"] == sha(OLD / "Coding Tools MCP.exe")
    assert parity["app_asar_sha256"] == sha(OLD / "resources/app.asar")
    assert smoke["sha256"]["source_package_parity_receipt"] == sha(old_parity_path)
    resources_root = OLD / "resources/resources"
    files = {}
    for file in sorted(resources_root.rglob("*")):
        assert not file.is_symlink(), "OLD_PACKAGE_LINK_UNSUPPORTED"
        assert file.name not in {"__pycache__", ".pytest_cache", ".coding-tools"}, "OLD_PACKAGE_CACHE_DETECTED"
        if file.is_dir():
            continue
        assert file.is_file() and file.suffix.lower() not in {".pyc", ".pyo"}
        files[file.relative_to(resources_root).as_posix()] = {"size_bytes": file.stat().st_size, "sha256": sha(file)}
    manifest = Path(os.environ["APPDATA"]) / "web-mcp-assistant/recovery-supervisor/manifest.json"
    snapshot = {"schema_version": 1, "kind": "retiring_immutable_package_resource_snapshot", "ok": True,
        "observed_at": datetime.now(timezone.utc).isoformat(), "candidate": str(OLD),
        "executable_sha256": parity["executable_sha256"], "app_asar_sha256": parity["app_asar_sha256"],
        "old_parity_proof_sha256": sha(old_parity_path), "old_smoke_proof_sha256": sha(old_smoke_path),
        "installed_manifest_sha256": sha(manifest),
        "installed_node_agent_sha256": sha(resources_root / "control-plane/node_agent.py"),
        "resources": files, "file_count": len(files), "retirement_only": True, "current_source_claim": False,
        "owner_status_receipt": str(status_path.relative_to(ROOT)), "owner_status_receipt_sha256": sha(status_path),
        "expected_owner": OWNER, "expected_epoch": EPOCH}
    snapshot_path = HERE / "retiring-r3-resource-snapshot.json"
    exclusive(snapshot_path, json.dumps(snapshot, indent=2) + "\n")

    source = (PREVIOUS / "packaged-operations.cjs").read_text(encoding="utf-8-sig")
    header = source[:source.index("  let result;")]
    status_branch = source[source.index("  let result;"):source.index("    const confirmReadRejection")]
    body = source[source.index("    } else if (mode === 'stop') {"):source.index("    } else if (mode === 'poll-once' || mode === 'assist-canary') {")]
    tail = source[source.index("  const report = receiptFile(mode, result,"):]
    header = version_map(header)
    status_branch = version_map(status_branch)
    body = version_map(body).replace("    } else if (mode === 'stop') {", "    if (mode === 'stop') {", 1)
    tail = version_map(tail)
    header = header.replace("owner_pid: 35428, owner_process_start_token: '134362815903498960'", "owner_pid: 12604, owner_process_start_token: '134362825905927480'")
    header = header.replace("a233b450199c09cd3118fb4ca2d7068b", OWNER["instance_id"])
    header = header.replace("1f61bc22f8a5b5c999710b319733ce8983f2ab6ab90ee6f7ab447f615b3facbb", OWNER["installation_id"])
    header = header.replace("// r3 remains admission-closed; one supported stop precedes fresh stopped observation.",
                            "// r3 is the exact READY owner; one supported stop precedes fresh stopped observation.")
    header = header.replace("  requireState(['stop', 'stopped-observation', 'retire', 'refresh', 'complete', 'status', 'policies',\n    'canary-build', 'canary-overlap', 'final-policy', 'poll-once', 'assist-canary', 'reconcile-read067'].includes(mode), 'UNSUPPORTED_OPERATION');",
                            "  requireState(['stop', 'stopped-observation', 'retire', 'refresh', 'complete', 'status', 'policies'].includes(mode), 'UNSUPPORTED_OPERATION');")
    header = header.replace("139a3e8f37afb0a67d60eb35abd66b50b1a9598d035734db1108b488bfa093db", sha(snapshot_path))
    start = header.index("  const serverFence = () => {")
    header = header[:start] + '''  const serverFence = () => {
    const file = option('--server-fence');
    const fence = read(file);
    const age = Date.now() - fence.capture_completed_at_ms;
    const work = fence.whole_device_census || {};
    const global = fence.global_live_work_by_scope || {};
    const historic = fence.historical_unknown_actions_preserved || [];
    const autocad = historic.filter(item => item.workspace_id === targets[1].workspace_id
      && item.workspace_generation === targets[1].workspace_generation);
    const expectedQuarantines = ['act_9db9b985a3d648b5b941f2e13a30ee47',
      'act_52409c69f1b84e08bb3fdd86747f79c3', 'act_3849e259d55546639794cec40f63fea8'].sort();
    requireState(fence.ok === true && fence.service_stable === true && fence.sqlite_integrity_ok === true
      && fence.source_startup_disk_attestation_matches === true && Number.isFinite(age) && age >= 0 && age <= 120_000
      && ['live_open_tasks', 'live_writers', 'queued_actions', 'active_dispatch_actions'].every(key => work[key] === 0)
      && ['live_open_tasks', 'live_writers', 'active_actions', 'blocking_action_identities'].every(key => Array.isArray(global[key]) && global[key].length === 0)
      && targets.every(target => Object.values(fence.expected_current_scopes || {}).some(item => item.workspace_id === target.workspace_id
        && item.workspace_generation === target.workspace_generation))
      && autocad.length === 3 && JSON.stringify(autocad.map(item => item.action_id).sort()) === JSON.stringify(expectedQuarantines)
      && historic.every(item => item.delivery_state === 'reconcile_required' && item.disposition === 'quarantined_unknown'
        && item.expired === true && Number.isInteger(item.reconciled_at_ms) && item.reconciled_at_ms > 0)
      && work.unsettled_actions === historic.length && work.reconciliation_required_actions === historic.length,
      'FRESH_EXACT_IDLE_SERVER_CENSUS_REQUIRED');
    return { receipt_path: file, sha256: digest(file), capture_completed_at_ms: fence.capture_completed_at_ms,
      admission_fence_claimed: false, preserved_autocad_quarantines: expectedQuarantines };
  };
'''
    status_branch = status_branch.replace("  if (mode === 'status' || mode === 'stopped-observation') {",
        "  if (mode === 'status' || mode === 'stopped-observation') {\n    if (mode === 'stopped-observation') requireState(fs.existsSync(path.join(__dirname, 'ordinary-r3-stop-intent.json')), 'ORIGINAL_STOP_INTENT_REQUIRED');")
    status_branch += "    requireState(apply, 'EXPLICIT_APPLY_REQUIRED');\n    const server = serverFence();\n"
    body = body.replace("activation-mv587m4p-0c2b59f01b1d25ba52938db8923db9da", EPOCH)
    body = body.replace("epoch.admission_open === false && beforeRuntime.mcpRunning === true", "epoch.state === 'READY' && epoch.admission_open === true && beforeRuntime.mcpRunning === true")
    body = body.replace("EXACT_INCOMPLETE_R3_EPOCH_REQUIRED", "EXACT_READY_R3_EPOCH_REQUIRED")
    body = body.replace("observed_at_ms: Date.now(), owner: expectedOwner, epoch, before_census: before,", "observed_at_ms: Date.now(), owner: expectedOwner, epoch, server, before_census: before,")
    body = body.replace("const stopped = await client.stop({ manual: true }, expected);", "serverFence();\n      const stopped = await client.stop({ manual: true }, expected);")
    body = body.replace("stage = 'supervisor_suppression'; mutationStarted = true;", "const retirementIntentPath = path.join(__dirname, 'ordinary-r3-retirement-intent.json');\n      requireState(!fs.existsSync(retirementIntentPath), 'ORIGINAL_R3_RETIREMENT_ALREADY_ATTEMPTED_OBSERVE_ONLY');\n      serverFence();\n      fs.writeFileSync(retirementIntentPath, JSON.stringify({ schema_version: 1, operation: 'exact-retirement-intent',\n        observed_at_ms: Date.now(), owner: expectedOwner, stopped_observation: observationPath, server, no_replay: true }, null, 2) + '\\n', { flag: 'wx' });\n      stage = 'supervisor_suppression'; mutationStarted = true;")
    body = body.replace("stage = 'exact_host_retirement';", "serverFence();\n      stage = 'exact_host_retirement';")
    body = body.replace("durable_state_deleted: false,", "durable_state_deleted: false, server_census: server, retirement_intent_receipt: retirementIntentPath,")
    body = body.replace("stage = 'full_clean_refresh'; mutationStarted = true;", "const refreshIntent = path.join(__dirname, 'ordinary-r4-refresh-intent.json');\n      requireState(!fs.existsSync(refreshIntent), 'ORIGINAL_R4_REFRESH_ALREADY_ATTEMPTED_OBSERVE_ONLY');\n      fs.writeFileSync(refreshIntent, JSON.stringify({ schema_version: 1, operation: 'full-clean-refresh-intent',\n        observed_at_ms: Date.now(), owner: pick(verified.descriptor, ['owner_pid','owner_process_start_token','instance_id','installation_id']),\n        server, no_replay: true }, null, 2) + '\\n', { flag: 'wx' });\n      stage = 'full_clean_refresh'; mutationStarted = true;")
    body = body.replace("reason: 'operator_parallel_native_first_preserve_history'", "reason: 'operator_parallel_native_first_r4_preserve_history'")
    body = body.replace("    } else if (mode === 'policies') {", "    } else if (mode === 'policies') {\n      const currentEpoch = await exact('runtime.activation_epoch_status');\n      requireState(currentEpoch.state === 'READY' && currentEpoch.admission_open === true && currentEpoch.activation_epoch_id === option('--epoch'), 'EXACT_READY_R4_EPOCH_REQUIRED');\n      requireState(idle(await census()), 'ACTIVE_LOCAL_WORK_PREVENTS_POLICY_UPDATE');")
    code = header + status_branch + body + "    }\n  }\n" + tail
    exclusive(HERE / "packaged-operations.cjs", code)
    install = version_map((PREVIOUS / "install-launch.ps1").read_text(encoding="utf-8-sig"))
    for old, new in (("35428", "12604"), ("134362815903498960", OWNER["owner_process_start_token"]),
                     ("a233b450199c09cd3118fb4ca2d7068b", OWNER["instance_id"]),
                     ("1f61bc22f8a5b5c999710b319733ce8983f2ab6ab90ee6f7ab447f615b3facbb", OWNER["installation_id"])):
        install = install.replace(old, new)
    install = install.replace("if (-not $Apply) {", "foreach ($SourceEntry in $Parity.code_sha256.PSObject.Properties) {\n    $SourceFile = Join-Path 'E:\\DEV\\Codex-web' $SourceEntry.Name\n    if ((Get-FileHash -LiteralPath $SourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $SourceEntry.Value) { throw 'Source changed after final package proof.' }\n}\nif ($Smoke.production_descriptor_stable -ne $true -or @($Smoke.fixture_generations_alive_after).Count -ne 0 -or\n    @($Smoke.candidate_process_census_after).Count -ne 0 -or @($Smoke.profiles_remaining_after).Count -ne 0) { throw 'Isolated smoke cleanup and stable production descriptor are required.' }\nif (-not $Apply) {")
    exclusive(HERE / "install-launch.ps1", install)
    report = {"schema_version": 1, "operation": "r3_to_r4_helpers_prepared", "ok": True,
        "observed_at": datetime.now(timezone.utc).isoformat(), "old_candidate": str(OLD), "new_candidate": str(NEW),
        "expected_old_owner": OWNER, "expected_old_epoch": EPOCH,
        "helper_sha256": {name: sha(HERE / name) for name in ("packaged-operations.cjs", "install-launch.ps1", snapshot_path.name)},
        "source_modified": False, "runtime_modified": False, "new_package_proof_pending": True,
        "old_stop_failures_preserved": True, "ready_inferred": False, "production_mutations_performed": False}
    exclusive(HERE / "helper-preparation.json", json.dumps(report, indent=2) + "\n")
    print(json.dumps({"ok": True, "directory": str(HERE), "resource_file_count": len(files), "helper_sha256": report["helper_sha256"]}))


if __name__ == "__main__":
    main()
