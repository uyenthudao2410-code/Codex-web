'use strict';
// Operator deployment adapter around the maintained exact-owner bootstrap.
// Plain Node never loads the target ASAR, so it can replace it after host exit.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {spawn, execFileSync} = require('node:child_process');
const {createRuntimePaths} = require('../../../electron/services/runtimePaths');
const ipc = require('../../../electron/services/recoveryIpc');
const launcher = require('../../../electron/services/recoveryHostLauncher');
const bootstrap = require('../../../electron/services/recoveryBootstrap');
const activation = require('../../../scripts/full-clean-activation');
const {stagePackage} = require('./stage-local-package.cjs');
const {canonicalLedgerCensus} = require('../../../electron/services/fullCleanActivation');
const {SettingsStore} = require('../../../electron/services/settingsStore');
const acceptedSource = require('../../../electron/services/recoveryActionStore');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const assert = (value, code) => {if (!value) throw Object.assign(new Error(code), {code});};
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const save = (name, value) => fs.writeFileSync(path.join(__dirname, name), JSON.stringify(value,null,2)+'\n');
const plan = readJson(path.join(__dirname, 'package-update-plan.json'));
const revisions = readJson(path.join(__dirname, 'candidate-component-revisions.json'));
const checkpoint = readJson(path.join(__dirname, '../direct-local-mode-20261022-refresh/checkpoint.json'));
const previous = readJson(path.join(__dirname, 'activation-preflight.json'));
const operationId = 'full-clean-cli-direct-local-20261022-05';
const paths = createRuntimePaths({dataRoot:path.join(process.env.APPDATA,'web-mcp-assistant'),
  resourcesRoot:path.join(plan.target,'resources/resources'),appRoot:path.join(plan.target,'resources/app.asar'),
  runtimeMode:'packaged',executablePath:path.join(plan.target,'Coding Tools MCP.exe')});
const expectedWorkspace = path.resolve('E:/DEV/Codex-web');
const expectedWorktreeFp = '8c6cd24145bde5b549d468cd5d9ea17d8af62f714d98c04ecb7b905a92ab5d4e';
const samePath = (left,right) => path.resolve(String(left || '')).toLowerCase() === path.resolve(String(right || '')).toLowerCase();
async function verifyAcceptedSource(workspace) {
  const identity = await acceptedSource.workspaceIdentity(workspace);
  const row = acceptedSource.readAcceptedCheckpoint(workspace,checkpoint.run_id,checkpoint.wave_id);
  assert(row?.status === 'accepted' && ['checkpoint_id','run_id','wave_id','proof_fingerprint','git_head']
    .every(field => row[field] === checkpoint[field]),'ACCEPTED_CHECKPOINT_CHANGED');
  assert(identity.head === checkpoint.git_head && identity.worktree_fp === row.metadata?.worktree_fp
    && identity.worktree_fp === expectedWorktreeFp,'ACCEPTED_SOURCE_IDENTITY_DRIFT');
  const receipts = acceptedSource.acceptedReceipts(row);
  assert(Array.isArray(receipts) && receipts.length === 26,'CANONICAL_ACCEPTED_RECEIPTS_REQUIRED');
  for (const receipt of receipts) {
    const file = path.resolve(workspace,...receipt.path.split('/'));
    const relative = path.relative(workspace,file);
    assert(relative && !relative.startsWith('..') && !path.isAbsolute(relative),'ACCEPTED_RECEIPT_PATH_INVALID');
    const info = fs.lstatSync(file);
    assert(!info.isSymbolicLink() && info.isFile() && receipt.state === 'file','ACCEPTED_RECEIPT_FILE_INVALID');
    const bytes = fs.readFileSync(file);
    assert(bytes.length === receipt.size_bytes && sha(bytes) === receipt.sha256,'ACCEPTED_RECEIPT_BYTES_CHANGED');
  }
  const diagnostic = acceptedSource.evaluateActivationEligibility(row,{workspace,currentHead:identity.head});
  // Auto component ownership is a separate route. This adapter deploys the
  // explicit exact-six-file package plan and retains that diagnostic honestly.
  assert(['ACTIVATABLE','COMPONENT_MAPPING_UNMAPPED'].includes(diagnostic.code),'ACCEPTED_SOURCE_DIAGNOSTIC_REFUSED');
  return {verified:true,checkpoint_id:row.checkpoint_id,run_id:row.run_id,wave_id:row.wave_id,
    proof_fingerprint:row.proof_fingerprint,current_git_head:identity.head,
    current_worktree_fp:identity.worktree_fp,accepted_worktree_fp:row.metadata.worktree_fp,
    whole_worktree_fp_verified:true,accepted_receipts_checked:true,receipt_count:receipts.length,
    receipts:receipts.map(({path,state,sha256,size_bytes})=>({path,state,sha256,size_bytes})),
    automatic_component_eligibility:{eligible:diagnostic.eligible,code:diagnostic.code,details:diagnostic.details || null}};
}
function requireStoppedRuntime(snapshot,workspace) {
  const state = snapshot?.status;
  assert(state?.busy === false && state.recovering === false && state.runtimeRunning === false
    && state.tunnelRunning === false && state.manuallyStopped === false
    && snapshot.device?.coding?.native_alive === false,'FRESH_RUNTIME_NOT_QUIESCENT_AND_STOPPED');
  assert(snapshot.settings?.executionRole === 'central_executor' && samePath(snapshot.settings.workspace,workspace),
    'FRESH_STOPPED_WORKSPACE_MISMATCH');
  return {stopped:true,busy:false,recovering:false,manually_stopped:false,runtime_running:false,
    tunnel_running:false,native_alive:false,workspace,observed_at:new Date().toISOString()};
}
function requireCensus(census,workspace) {
  const snapshot = census?.snapshot;
  assert(census?.safe === true && census.source_checkpoint_verified === true && census.content_free === true
    && census.mutated_canonical_ledger === false && samePath(census.workspace,workspace)
    && snapshot?.backup_api_copy === true && snapshot.immutable === true && snapshot.query_only === true
    && JSON.stringify(snapshot.integrity_check) === '["ok"]' && snapshot.foreign_key_check_rows === 0
    && /^[a-f0-9]{64}$/.test(census.census_fingerprint || ''),'CANONICAL_STOPPED_CENSUS_REFUSED');
}
const phase = name => console.log(JSON.stringify({phase:name,observed_at:new Date().toISOString()}));
async function main() {
  assert(!process.versions.electron, 'PLAIN_NODE_REQUIRED');
  assert(process.argv.includes('--execute'), 'EXECUTE_FLAG_REQUIRED');
  assert(sha(fs.readFileSync(path.join(plan.candidate,'resources/app.asar'))) === revisions.candidate_app_asar_sha256
    && revisions.candidate_app_asar_sha256 === plan.changes.find(x=>x.path==='resources/app.asar').after_sha256,
    'CANDIDATE_ASAR_CHANGED');
  assert(sha(fs.readFileSync(path.resolve(__dirname,'../../../electron/services/componentRevision.js')))
    === revisions.component_revision_implementation_sha256,'REVISION_IMPLEMENTATION_CHANGED');
  for (const item of plan.changes) {
    assert(sha(fs.readFileSync(path.join(plan.target,item.path))) === item.before_sha256
      && sha(fs.readFileSync(path.join(plan.candidate,item.path))) === item.after_sha256,'PACKAGE_PLAN_DRIFT');
  }
  const context = activation.createCommandContext({paths});
  context.requestOptions.timeout = 55000;
  const status = await context.client.status(context.requestOptions);
  const oldRevision = previous.authority.expected_disk_revision;
  assert(bootstrap.assessRecoveryHostFreshness({paths,descriptor:context.descriptor,status,expectedDiskRevision:oldRevision}).current,
    'OLD_RECOVERY_HOST_NOT_CURRENT');
  const workspace = new SettingsStore(paths).load().workspace;
  assert(samePath(workspace,expectedWorkspace),'CONFIGURED_WORKSPACE_CHANGED');
  phase('fresh_stopped_runtime_snapshot');
  const snapshot = await context.client.call('runtime.snapshot',[{force:true,reason:'resume-stopped-local-deployment'}],context.requestOptions);
  const runtimeObservation = requireStoppedRuntime(snapshot,workspace);
  phase('canonical_stopped_runtime_ledger_census');
  const census = await canonicalLedgerCensus({paths,workspace,sourceCheckpoint:checkpoint,allowAcceptancePending:true});
  requireCensus(census,workspace);
  const sourceVerification = await verifyAcceptedSource(workspace);
  const request = {requested_at_unix_ms:Date.now()};
  const authority = {expected_disk_revision:oldRevision,recovery_host:{pid:Number(context.descriptor.owner_pid),instance_id:context.descriptor.instance_id}};
  save('resume-05-stopped-census.json',{ok:true,evidence_kind:'stopped_runtime_canonical_ledger_census',operation_id:operationId,
    verified_at_unix_ms:Date.now(),checkpoint,authority,runtime_observation:runtimeObservation,
    canonical_ledger_census:census,source_verification:sourceVerification});
  // Keep the maintained stop handler and every refusal. Only its transport
  // wait changes: the old handler can finish a costly post-stop snapshot.
  const originalStop = context.client.stop.bind(context.client);
  context.client.stop = (options,callOptions={}) => originalStop(options,{...callOptions,timeout:90000});
  phase('supported_bootstrap_stop_and_handoff');
  let staged = false;
  const newRevision = revisions.components.recovery_host.revision;
  const result = await bootstrap.bootstrapCurrentRecoveryHost({paths,app:{isPackaged:true,getAppPath:()=>paths.appRoot()},
    client:context.client,descriptor:context.descriptor,status,operationId,sourceCheckpoint:checkpoint,
    expectedDiskRevision:newRevision,requestedAtUnixMs:Date.now(),expiresAtUnixMs:Date.now()+300000,timeoutMs:55000,
    spawnProcess:(executable,args,options)=>{
      assert(!staged && path.resolve(executable) === path.resolve(paths.executablePath())
        && args.includes('--recovery-host') && args.includes('--recovery-bootstrap='+operationId),'UNEXPECTED_BOOTSTRAP_LAUNCH');
      const observation = execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',
        'Get-CimInstance Win32_Process -Filter "Name = \'Coding Tools MCP.exe\'" | Select-Object ProcessId,ExecutablePath | ConvertTo-Json -Compress'],
        {encoding:'utf8',windowsHide:true,timeout:15000}).trim();
      const processRows = observation ? JSON.parse(observation) : [];
      assert([].concat(processRows).every(row=>row.ExecutablePath
        && path.resolve(row.ExecutablePath).toLowerCase() !== path.resolve(executable).toLowerCase()),'INSTALLED_PROCESS_STILL_LIVE');
      phase('stage_code_with_old_processes_absent');
      stagePackage({paths,descriptor:context.descriptor,evidenceFile:'resume-05-stopped-census.json',operationId});
      for(const item of plan.changes) assert(sha(fs.readFileSync(path.join(plan.target,item.path))) === item.after_sha256,'STAGED_PACKAGE_DRIFT');
      staged = true;
      phase('launch_replacement_through_supported_bootstrap');
      return spawn(executable,args,options);
    }});
  save('resume-05-bootstrap.json',{ok:true,operation_id:operationId,required:result.required,staged,
    replacement_pid:result.pid,expected_recovery_revision:newRevision});
  phase('wait_for_canonical_activation_epoch');
  const operation = await activation.waitForReplacementOperation(paths,context.descriptor,operationId,300000);
  const epoch = operation.activationEpochId;
  assert(epoch,'ACTIVATION_EPOCH_UNAVAILABLE');
  const replacement = ipc.loadRecoveryDescriptor(paths);
  assert(launcher.descriptorMatchesInstallation(replacement,paths.runtimeIdentity())
    && Number(replacement.owner_pid) !== Number(context.descriptor.owner_pid),'REPLACEMENT_IDENTITY_UNPROVEN');
  const replacementClient = new ipc.RecoveryIpcClient({paths});
  const replacementStatus = await replacementClient.status({...launcher.descriptorRequestOptions(replacement),timeout:55000});
  assert(replacementStatus.activation_epoch?.activation_epoch_id === epoch
    && replacementStatus.activation_epoch?.admission_open === false,'SUPERVISOR_REFRESH_REQUIRES_CLOSED_NEW_EPOCH');
  phase('refresh_maintained_supervisor_for_new_node_bytes');
  const supervisorOutput = execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass',
    '-File',path.join(plan.target,'resources/resources/recovery-supervisor/recovery-supervisor.ps1'),
    '-Action','Install','-Packaged','-Executable',paths.executablePath(),'-AppRoot',plan.target],
    {encoding:'utf8',windowsHide:true,timeout:60000,maxBuffer:2*1024*1024});
  const supervisorResult = JSON.parse(supervisorOutput.trim());
  assert(supervisorResult.ok !== false,'SUPERVISOR_REFRESH_FAILED');
  save('resume-05-supervisor-refresh.json',{ok:true,observed_at:new Date().toISOString(),action:'Install',
    executable:paths.executablePath(),status:supervisorResult.status || null,
    expected_node_agent_sha256:plan.changes.find(x=>x.path.endsWith('/node_agent.py')).after_sha256});
  phase('wait_for_ready');
  const ready = await activation.waitForReplacementReady(paths,context.descriptor,epoch,300000,
    {operationId,notBeforeUnixMs:request.requested_at_unix_ms});
  const finalStatus = ready.status || ready.last?.status;
  const receipt = {ok:ready.ready === true,operation_id:operationId,checkpoint,activation_epoch_id:epoch,staged,
    expected_recovery_revision:newRevision,replacement_pid:ready.descriptor?.owner_pid || ready.last?.descriptor?.owner_pid,
    state:finalStatus?.activation_epoch?.state,admission_open:finalStatus?.activation_epoch?.admission_open,
    fully_ready:finalStatus?.runtime?.fully_ready,connector_acknowledged:ready.connectorAckAttempted === true};
  save('resume-05-final.json',receipt);
  console.log(JSON.stringify(receipt));
  assert(receipt.ok && receipt.state === 'READY' && receipt.admission_open && receipt.fully_ready,'ACTIVATION_NOT_READY');
}
main().catch(error=>{const receipt={ok:false,code:error.code||error.message,stage_receipt:error.stage_receipt||null,
  operation_id:operationId,next_action:'Inspect durable bootstrap and exact activation status before retrying.'};
  save('resume-05-failure.json',receipt);console.log(JSON.stringify(receipt));process.exitCode=1;});
