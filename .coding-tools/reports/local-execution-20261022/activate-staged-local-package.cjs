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
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const assert = (value, code) => {if (!value) throw Object.assign(new Error(code), {code});};
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const save = (name, value) => fs.writeFileSync(path.join(__dirname, name), JSON.stringify(value,null,2)+'\n');
const plan = readJson(path.join(__dirname, 'package-update-plan.json'));
const revisions = readJson(path.join(__dirname, 'candidate-component-revisions.json'));
const checkpoint = readJson(path.join(__dirname, '../direct-local-mode-20261022-refresh/checkpoint.json'));
const previous = readJson(path.join(__dirname, 'activation-preflight.json'));
const operationId = 'full-clean-cli-direct-local-20261022-04';
const paths = createRuntimePaths({dataRoot:path.join(process.env.APPDATA,'web-mcp-assistant'),
  resourcesRoot:path.join(plan.target,'resources/resources'),appRoot:path.join(plan.target,'resources/app.asar'),
  runtimeMode:'packaged',executablePath:path.join(plan.target,'Coding Tools MCP.exe')});
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
  const request = activation.buildRequest({component:'recovery_host',expectedDiskRevision:oldRevision},checkpoint,Date.now(),{operationId});
  phase('preflight');
  const preflight = await context.client.call('code.activation_preflight',[request],context.requestOptions);
  assert(preflight.safe === true && preflight.runtime?.source_checkpoint?.ok === true,'ACTIVATION_PREFLIGHT_REFUSED');
  const authority = {expected_disk_revision:oldRevision,recovery_host:{pid:Number(context.descriptor.owner_pid),instance_id:context.descriptor.instance_id}};
  save('activation-preflight.json',{ok:true,verified_at_unix_ms:Date.now(),request,preflight,authority});
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
      stagePackage({paths,descriptor:context.descriptor});
      for(const item of plan.changes) assert(sha(fs.readFileSync(path.join(plan.target,item.path))) === item.after_sha256,'STAGED_PACKAGE_DRIFT');
      staged = true;
      phase('launch_replacement_through_supported_bootstrap');
      return spawn(executable,args,options);
    }});
  save('activation-bootstrap.json',{ok:true,operation_id:operationId,required:result.required,staged,
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
  save('supervisor-refresh.json',{ok:true,observed_at:new Date().toISOString(),action:'Install',
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
  save('activation-final.json',receipt);
  console.log(JSON.stringify(receipt));
  assert(receipt.ok && receipt.state === 'READY' && receipt.admission_open && receipt.fully_ready,'ACTIVATION_NOT_READY');
}
main().catch(error=>{const receipt={ok:false,code:error.code||error.message,stage_receipt:error.stage_receipt||null,
  operation_id:operationId,next_action:'Inspect durable bootstrap and exact activation status before retrying.'};
  save('activation-adapter-failure.json',receipt);console.log(JSON.stringify(receipt));process.exitCode=1;});
