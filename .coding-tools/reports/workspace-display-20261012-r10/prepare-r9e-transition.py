from pathlib import Path
import json

root = Path(r'E:\DEV\Codex-web')
report = root / '.coding-tools' / 'reports' / 'workspace-display-20261012-r10'
previous = root / '.coding-tools' / 'reports' / 'folder-access-20261012-r9' / 'r9d-transition'
target = report / 'r9e-transition'
proof = json.loads((report / 'r9e-candidate-verification.json').read_text())
assert proof['ok'] is True
assert proof['candidate'] == str(root / 'dist' / 'windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e' / 'win-unpacked')
target.mkdir(exist_ok=True)

def create(name, value):
    if (target / name).exists():
        assert (target / name).read_text() == value, 'Refusing concurrent helper overwrite: ' + name
        return
    with (target / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)

def changed(value, replacements):
    for before, after in replacements:
        if before not in value:
            raise ValueError('Missing expected source fragment: ' + before)
        value = value.replace(before, after)
    return value

identity = [
    ('35288', '3476'),
    ('d01ae3e08fb3e06fe2fda5da65c61285', 'dbf2536afedb8b4e554a29fc9e88cb50'),
    ('0f533411b2fdd0939b42db27ac9b4ad65361228f50489107338bf00e5826b740', 'bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba'),
    ('activation-mv50m446-6a132615d256208450967af03c450d00', 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db'),
    ('134362688272046960', '134362696871111330')
]
tags = [
    ('machine-folder-access-1012-r9d', 'machine-folder-access-1012-r9e'),
    ('machine-folder-access-1012-r9c', 'machine-folder-access-1012-r9d')
]
hashes = [
    ('337f3669f7702156fe725c61dfc530d1938eee35f463fe3f1261ddba53b14c74', proof['executable_sha256']),
    ('2fba385f52d679dc005b8a55d8d05a971bb0312e0bcbc9a3acabd69885ed7589', proof['app_asar_sha256'])
]
ops = changed((previous / 'packaged-operations.cjs').read_text(), [
    ("const sourceProofPath = path.join(__dirname, '..', mode === 'retire' ? 'r9c-candidate-verification.json' : 'r9d-candidate-verification.json');", "const oldMode = ['retire', 'stop', 'stopped-observation'].includes(mode);\nconst sourceProofPath = oldMode\n  ? path.join(root, '.coding-tools', 'reports', 'folder-access-20261012-r9', 'r9d-candidate-verification.json')\n  : path.join(__dirname, '..', 'r9e-candidate-verification.json');"),
    *identity[:4],
    ('LIVE_SANDBOX_PREVENTS_R9C_RETIREMENT', 'LIVE_SANDBOX_PREVENTS_R9D_RETIREMENT'),
    ('EXACT_R9C_OWNER_REQUIRED', 'EXACT_R9D_OWNER_REQUIRED')
])
ops = changed(ops, [
    ("  let receipt;\n  if (mode === 'retire') {", """  const assertOldOwner = async () => {
    const activation = await exactCall('runtime.activation_epoch_status');
    requireState(verified.descriptor.owner_pid === 3476
      && verified.descriptor.instance_id === 'dbf2536afedb8b4e554a29fc9e88cb50'
      && verified.descriptor.installation_id === 'bdf474c17024f7686b83920b289de5422d6129db4bbf8a93659eb744ccaaadba'
      && verified.descriptor.owner_process_start_token === '134362696871111330'
      && activation.activation_epoch_id === 'activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db'
      && activation.state === 'READY' && activation.admission_open === true, 'EXACT_R9D_OWNER_REQUIRED');
  };
  const readTransitionEvidence = filename => {
    const resolved = path.resolve(filename || '');
    requireState(resolved.toLowerCase().startsWith(path.resolve(__dirname, '..').toLowerCase() + path.sep)
      && fs.statSync(resolved).isFile() && fs.statSync(resolved).size <= 65536, 'BOUNDED_TRANSITION_EVIDENCE_REQUIRED');
    return { path: resolved, value: JSON.parse(fs.readFileSync(resolved, 'utf8')) };
  };
  const requireFreshServerIdle = () => {
    const evidence = readTransitionEvidence(process.argv[4]);
    const value = evidence.value;
    const age = Date.now() - value.observed_at_ms;
    requireState(Number.isSafeInteger(value.observed_at_ms) && age >= 0 && age <= 120000
      && value.database_mutations_performed === false && value.sqlite_integrity_ok === true
      && value.current_generation_idle === true && value.current_device_live_task_writer_idle === true
      && value.selected_target?.binding_id === 'bind_8cd903180f3146099fea128bf55c0b4b'
      && value.selected_target?.device_id === '4c4b7a5b-7744-49ae-a490-78a528a00471'
      && value.selected_target?.workspace_id === workspaceId
      && value.selected_target?.workspace_generation === currentGeneration
      && value.live_pilot?.decision_id === 'pilot_833530c73c72491ba0163037ae80e8f0'
      && value.live_pilot?.workspace_generation === currentGeneration
      && value.live_pilot?.expires_at_ms > Date.now()
      && ['unclosed_tasks', 'unreleased_writers', 'unsettled_actions', 'queued_actions', 'active_dispatch_actions']
        .every(key => value.current_generation_census?.[key] === 0)
      && ['unclosed_tasks', 'unreleased_writers', 'queued_actions', 'active_dispatch_actions']
        .every(key => value.all_current_device_census?.[key] === 0), 'FRESH_SELECTED_CENTRAL_IDLE_RECEIPT_REQUIRED');
    // The all-device historical quarantined UNKNOWN actions remain evidence.
    // They are deliberately not required to be settled or deleted.
    return { path: evidence.path, observed_at_ms: value.observed_at_ms,
      historical_unknown_actions_preserved: true };
  };
  let receipt;
  if (mode === 'retire') {
    await assertOldOwner();
    const serverIdle = requireFreshServerIdle();
    const stopEvidence = readTransitionEvidence(process.argv[5]);
    const stop = stopEvidence.value;
    const stopAge = Date.now() - Date.parse(stop.observed_at);
    requireState(stop.ok === true && stop.operation === 'stop' && stop.candidate.toLowerCase() === candidate.toLowerCase()
      && stop.receipt?.ordinary_stop === true && stop.receipt?.runtime?.mcpRunning === false
      && stop.receipt?.stopped_census?.safe === true && stopAge >= 0 && stopAge <= 900000,
    'FRESH_CONFIRMED_ORDINARY_STOP_REQUIRED');
    const stoppedSnapshot = await exactCall('runtime.lightweight_snapshot');
    requireState(stoppedSnapshot.mcpRunning === false && stoppedSnapshot.nativeAlive === false,
      'EXACT_NATIVE_NOT_STOPPED');"""),
    ("'WindowsSandbox*','wxc-windows-sandbox-daemon'", "'WindowsSandbox*','vmmemWSB','wxc-windows-sandbox-daemon','wxc-exec'"),
    ("    await client.stop({ manual: true }, expected);\n    const after = await canonicalLedgerCensus", "    // The ordinary stop was already confirmed; do not replay its operation.\n    const after = await canonicalLedgerCensus"),
    ("stopped_census: after, preserved_historical_acceptance: true, durable_state_deleted: false };", "stopped_census: after, preserved_historical_acceptance: true, durable_state_deleted: false,\n      ordinary_stop_receipt: stopEvidence.path, server_idle_receipt: serverIdle, original_stop_not_replayed: true };"),
    ("  } else if (mode === 'stop') {\n    const { canonicalLedgerCensus }", "  } else if (mode === 'stop') {\n    await assertOldOwner();\n    const serverIdle = requireFreshServerIdle();\n    const { canonicalLedgerCensus }"),
    ("    const stopped = await client.stop({ manual: true }, expected);\n    const after", """    const stopped = await client.stop({ manual: true }, expected);
    const operationResultPath = path.join(__dirname, `ordinary-stop-operation-result-${Date.now()}.json`);
    fs.writeFileSync(operationResultPath, JSON.stringify({ operation: 'ordinary_stop_operation_result',
      observed_at: new Date().toISOString(), candidate, runtime: summarize(stopped), before_census: before,
      exact_owner_verified: true, server_idle_receipt: serverIdle }, null, 2), { flag: 'wx' });
    const after"""),
    ("ordinary_stop:true, historical_acceptance_preserved:true };", "ordinary_stop:true, historical_acceptance_preserved:true, exact_owner_verified:true,\n      operation_result_path:operationResultPath, server_idle_receipt:serverIdle };"),
    ("    // Persist the real operation result before any optional diagnostic gate.\n    requireState(stopped.mcpRunning === false, 'ORDINARY_STOP_NOT_CONFIRMED');", "    // The real result is preserved above even if a diagnostic confirmation fails.\n    requireState(stopped.mcpRunning === false && after.safe === true, 'ORDINARY_STOP_NOT_CONFIRMED');"),
    ("  } else if (mode === 'stopped-observation') {\n    const { canonicalLedgerCensus }", "  } else if (mode === 'stopped-observation') {\n    await assertOldOwner();\n    const { canonicalLedgerCensus }")
])
create('packaged-operations.cjs', ops)

invoke = changed((previous / 'invoke-packaged.ps1').read_text(), [
    ("'exec','observe'", "'exec','observe','stop','stopped-observation'"),
    ("[string]$Epoch)", "[string]$Epoch,[string]$ServerCensusPath,[string]$StopReceiptPath)"),
    ("if ($Operation -eq 'retire')", "if ($Operation -in @('retire','stop','stopped-observation'))"),
    *tags,
    ('observe-r9d-machine.cjs', 'observe-r9e-machine.cjs'),
    ("elseif($Operation -in @('metadata','files','exec')){@($generation)}else{@()}", "elseif($Operation -in @('metadata','files','exec')){@($generation)}elseif($Operation -eq 'retire'){@(('\"'+$ServerCensusPath+'\"'),('\"'+$StopReceiptPath+'\"'))}elseif($Operation -eq 'stop'){@(('\"'+$ServerCensusPath+'\"'))}else{@()}")
])
create('invoke-packaged.ps1', invoke)
observer = changed((previous / 'observe-r9d-machine.cjs').read_text(), [
    ('r9d-candidate-verification.json', 'r9e-candidate-verification.json'), identity[3],
    ('NEW_EXACT_R9D_ACTIVATION_EPOCH_REQUIRED', 'NEW_EXACT_R9E_ACTIVATION_EPOCH_REQUIRED'),
    ('EXACT_VERIFIED_R9D_PACKAGE_REQUIRED', 'EXACT_VERIFIED_R9E_PACKAGE_REQUIRED')
])
create('observe-r9e-machine.cjs', observer)
launch = changed((previous / 'launch-r9d.ps1').read_text(), [
    *tags, *hashes, *identity[:3], identity[4],
    ('install_r9d_supervisor', 'install_r9e_supervisor'), ('launch_r9d_ui', 'launch_r9e_ui')
])
launch = launch.replace('prior-r9c', 'prior-r9d').replace('prior r9c owner', 'prior r9d owner')
launch = launch.replace('The r9d package', 'The r9e package').replace('r9d supervisor', 'r9e supervisor').replace('exact r9d.', 'exact r9e.')
create('launch-r9e.ps1', launch)
shortcut = changed((previous / 'update-coding-tools-shortcuts-r9d.ps1').read_text(), [
    ('machine-exec-lifecycle-1012-r8', 'machine-folder-access-1012-r9d'),
    (tags[0][0], tags[0][1]), *hashes, identity[3],
    ('982304384ba8a66df884e440c2e0f4ed27f5516ddc1377accd92d7450208c329', 'eca1a5e87d6e079f418eb3658e1610bd9b52d843dccf581cbdf6e21e6b4053de'),
    ('84f5444f2360de1e8e01d32a3bd892784b93ca3d5b5bf3fc938ce50dba0cc0b9', 'c7c6b39ce883febdc2c91300d7f26937ed1c564f898c604fa05098954496af84'),
    ('coding-tools-r8-original.lnk', 'coding-tools-r9d-original.lnk'),
    ('before-r9d.json', 'before-r9e.json'), ('after-r9d.json', 'after-r9e.json')
])
# Old and new paths were replaced sequentially; restore the expected prior target.
shortcut = changed(shortcut, [
    ("$ExpectedOldTarget = 'E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9e\\win-unpacked\\Coding Tools MCP.exe'", "$ExpectedOldTarget = 'E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9d\\win-unpacked\\Coding Tools MCP.exe'")
])
shortcut = shortcut.replace('r9d package', 'r9e package').replace('r9d EXE', 'r9e EXE').replace('r9d activation', 'r9e activation').replace('An r9d observer', 'An r9e observer').replace('The r9d READY', 'The r9e READY')
create('update-coding-tools-shortcuts-r9e.ps1', shortcut)
print('Prepared additive r9e transition; no runtime effects')
