'use strict';
// Root-only operational helper. Uses supported packaged node-agent installers;
// never edits a policy JSON, starts a VM, dispatches work or accepts a RUN/WAVE.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {spawnSync, execFileSync} = require('node:child_process');
const asar = require('@electron/asar');
const repo = 'E:\\Github\\Tools-Codex-web', services = path.join(repo, 'electron/services');
const transition = require('../activation-windows/transition-r11.cjs');
const {ControlPlaneEnrollmentService, parsePolicyAuthorityObservation} = require(path.join(services, 'controlPlaneEnrollment'));
const {RecoveryIpcClient, loadRecoveryDescriptor} = require(path.join(services, 'recoveryIpc'));
const {descriptorRequestOptions, descriptorMatchesInstallation} = require(path.join(services, 'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity: identity, sameProcessIdentity: same} = require(path.join(services, 'processIdentity'));
const {canonicalLedgerCensus} = require(path.join(services, 'fullCleanActivation'));
const paths = transition.pathsFor('r11');
const target = {binding_id:'bind_3e05bf64cb3e4bab93d930ae1692bebb',device_id:'72ceec2d-e3f2-472f-8e3c-99fffe053035',workspace_id:'workspace_dda1d78e9a21402aa6213f72af64f788',workspace_generation:'generation_c2f13e8d02344cf6a38a3f42ecfa59b6',owner_id:'owner_default',endpoint_id:'executor-72ceec2d-e3f2-472f-8e3c-99fffe053035',server_origin:'https://svhome.tail0e4032.ts.net'};
const facade = {schema_version:32,profile:'control-plane-private-tunnel-service-v1',sha256:'3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66'};
const expiry = 1791739329910, requested = 1791735729910;
const contextId = 'ctx_71ae5c01e2de4df6874d401263a310c0', pilotId = 'pilot_b294f82a6cf64b098268322b9106d8c7';
const serverRevision = '9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c';
const nativePin = {activation_epoch_id:'activation-mv41dwd7-2d04fcff5a63f38940d0e99aea872251',mcp_process_instance_id:'JSKtd-MweBjIMZ0p',mcp_server_instance_id:'Vx0DhMwsMsmnY7E1',tool_contract_sha256:'0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4'};
const oldPending = {run_id:'95e909f0040a448faa9f1f3257e2ee2c',wave_id:'c101beadfc6d4f2fbc13845052c84693',runs:'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590',waves:'59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce'};
const policyHashes = {ReadOnly:'734f7de680b9213d021041c06788027340816aaf72629b778cd38dd649feb793',FileRead:'284bd75cc62669c42a7a8bbb9d0531d6da7afd344442f457727fdecfde5404db',ApprovedPatch:'63cd7bf31e8db3fed7f99cc3bfdbf5cd522b3accd5d91cbaff2ed2ae0ab71ab8',Exec:'5e38d0067e7d8e7a38ce1dba8378616202d6192ed01b22ffbd1ee8105e257040'};
const dependencyHashes = {'electron/services/controlPlaneEnrollment.js':'c72766572150b5f2ce1e7ed7f976eb408ff3a75a7191951fddf0ccb7a28c6405','electron/services/fullCleanActivation.js':'881ffbdc57d4332ec1d6316199d2876d58821447b30cc861eade4c2c3d31baf1','electron/services/processIdentity.js':'a0ee2b08cbe4108c352ba14b9532ceaf581497f745a2adda7924c819a972809f','electron/services/recoveryIpc.js':'57e0154c4d9f80bcfc5fa95ec5c4643de436d8fe945e9b3ab884afd9b8faebc2','electron/services/recoveryHostLauncher.js':'92cb2478ae940c737a8e8a007181a9fa410b1eeb1e26a06b5bb07e1043ebf60a'};
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha = file => digest(fs.readFileSync(file));
const read = file => JSON.parse(fs.readFileSync(file,'utf8'));
const fail = code => {throw Object.assign(new Error(),{code});};
const need = (ok,code) => {if (!ok) fail(code);};
function canonical(v) {if (Array.isArray(v)) return '['+v.map(canonical).join(',')+']'; if (v && typeof v==='object') return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}'; return JSON.stringify(v);}
const equal = (a,b) => canonical(a)===canonical(b);
const withoutFacade = v => Object.fromEntries(Object.entries(v).filter(([k])=>k!=='facade_contract'));
const admittedDigest = v => digest(Buffer.from(canonical(Object.fromEntries(Object.entries(v).filter(([k])=>k!=='enabled'))),'utf8'));
function guardReplacement(before,after) {need(equal(after.facade_contract,facade),'POST_FACADE_MISMATCH');need(equal(withoutFacade(before),withoutFacade(after)),'NONCONTRACT_POLICY_FIELD_CHANGED');return true;}
function emit(v) {const row={observed_at_ms:Date.now(),helper_sha256:sha(__filename),...v};fs.appendFileSync(path.join(__dirname,'reconciliation.jsonl'),JSON.stringify(row)+'\n');process.stdout.write(JSON.stringify(row)+'\n');return row;}
function arg(name) {const a=process.argv.filter(v=>v.startsWith('--'+name+'='));need(a.length===1,'EXPLICIT_RECEIPT_REQUIRED');return a[0].slice(name.length+3);}
function pinned(name) {const file=arg(name);need(path.isAbsolute(file)&&/^[a-f0-9]{64}$/.test(arg(name+'-sha256'))&&sha(file)===arg(name+'-sha256'),'RECEIPT_CHANGED');const v=read(file);return Array.isArray(v.public_receipts)&&v.public_receipts.length===1?v.public_receipts[0]:v;}
function guardServer(s,now=Date.now()) {
  need(s.ok===true && s.remote_mutation===false && s.source_revision===serverRevision && s.service_instance_id==='cp_339c7a19bc2443eeab35583addfef543'
    && s.binding_id===target.binding_id && s.admission==='scoped_pilot' && (!s.host||s.host==='100.116.112.22') && (!s.service||s.service==='codex-control-plane.service')
    && Number.isSafeInteger(s.observed_at_ms) && now-s.observed_at_ms>=0 && now-s.observed_at_ms<60000,'FRESH_SCOPED_PILOT_RECEIPT_REQUIRED');
  need(s.next_requested_at_ms===requested && s.next_expires_at_ms===expiry && s.next_context_id===contextId && s.next_pilot_id===pilotId && expiry-requested===3600000 && requested<=now && expiry>now,'EXACT_UNCHANGED_60M_AUTHORITY_REQUIRED');
  need(s.state && ['queued_actions','accepted_actions','open_writers','open_tasks','target_unsettled_actions'].every(k=>s.state[k]===0),'CENTRAL_TASKS_NOT_QUIESCENT');
  return true;
}
function verifyCandidate() {
  need(execFileSync('git',['--no-optional-locks','rev-parse','HEAD'],{cwd:repo,encoding:'utf8',windowsHide:true}).trim()==='2c554f59cb7b8ffc86ce5e0e28076c792777642f','HEAD_CHANGED');
  const pf=path.join(__dirname,'../candidate-parity-20261011T142316263Z.json'),sf=path.join(__dirname,'../source-freeze.json'),p=read(pf);
  need(sha(pf)==='cefbb4daaeda869629594ed311e685de10049ef07445766b73ae4a5113bc0666'&&sha(sf)==='3bd561909abf56126ae2a15cc65932181251a48a1a9d47779b506e1b6c359c63'&&p.ok&&p.source_files.length===12,'FROZEN_PARITY_CHANGED');
  need(sha(paths.appRoot())==='2071c0c242bc4b24ebfc22ea21b5c4d066e018505061ebe299cd666c6d2e8a91'&&sha(paths.executablePath())==='d556d6040ced8fd0d6ed52b05cbdbb15a398344d1995402ad3bfcd8efbce94bc','R11_PACKAGE_CHANGED');
  const rf=path.join(__dirname,'../authority-renewal-next/remote-receipts/renew-20261011T162210220806Z.json');need(sha(rf)==='67fbeee14cc5f687470943d3a1ffbaf56abb71139bcdacc2b57d879daba95f85','APPROVED_RENEWAL_RECEIPT_CHANGED');const renewal=read(rf).public_receipts[0];need(renewal.ok===true&&renewal.requested_at_ms===requested&&renewal.expires_at_ms===expiry&&renewal.context_id===contextId&&renewal.pilot_id===pilotId&&renewal.binding_id===target.binding_id,'APPROVED_RENEWAL_WINDOW_CHANGED');
  for(const i of p.source_files) {const b=i.payload.startsWith('app.asar/')?asar.extractFile(paths.appRoot(),path.join(...i.payload.slice(9).split('/'))):fs.readFileSync(path.join(path.dirname(paths.executablePath()),i.payload));need(sha(path.join(repo,i.source))===i.sha256&&digest(b)===i.sha256,'R11_SOURCE_OR_PAYLOAD_DRIFT');}
  for(const [rel,hash] of Object.entries(dependencyHashes))need(sha(path.join(repo,rel))===hash&&digest(asar.extractFile(paths.appRoot(),path.join(...rel.split('/'))))===hash,'HELPER_DEPENDENCY_DRIFT');
}
function policySnapshot(requireOld=false) {
  const all={};
  const registry=read(paths.controlPlaneWorkspaceRegistryFile()),entries=registry.entries?.filter(v=>v.workspace_id===target.workspace_id&&v.workspace_generation===target.workspace_generation);need(registry.schema_version===1&&Array.isArray(entries)&&entries.length===1&&path.resolve(entries[0].canonical_path).toLowerCase()===repo.toLowerCase()&&fs.realpathSync.native(entries[0].canonical_path).toLowerCase()===repo.toLowerCase()&&['read','write','exec'].every(k=>entries[0].capabilities[k]===true),'REGISTERED_WORKSPACE_SCOPE_CHANGED');
  for(const kind of Object.keys(policyHashes)) {const file=paths['controlPlane'+kind+'PolicyFile'](),v=read(file);need(Object.keys(v).every(k=>!/secret|token|credential|password|private_key/i.test(k)),'UNEXPECTED_POLICY_SECRET_FIELD');need(v.enabled===true&&['device_id','workspace_id','workspace_generation','owner_id','endpoint_id','server_origin'].every(k=>v[k]===target[k]),'POLICY_TARGET_CHANGED');if(requireOld)need(sha(file)===policyHashes[kind],'BEFORE_POLICY_HASH_CHANGED');all[kind]={file_sha256:sha(file),value:v};}
  need(all.ReadOnly.value.expires_at_ms===expiry&&equal(all.ReadOnly.value.facade_contract,facade),'METADATA_POLICY_NOT_CURRENT');
  for(const kind of ['FileRead','ApprovedPatch','Exec'])need(all[kind].value.authority_mode==='standing'&&all[kind].value.expires_at_ms===null,'STANDING_POLICY_LIFETIME_CHANGED');
  return all;
}
const pendingCode=`import hashlib,json,sqlite3,sys\nfrom pathlib import Path\nfrom contextlib import closing\nwith closing(sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True,timeout=10)) as d:\n d.row_factory=sqlite3.Row;d.execute("PRAGMA query_only=ON");d.execute("BEGIN");r={}\n for t,c,v in (("runs","run_id",sys.argv[2]),("waves","wave_id",sys.argv[3])):\n  rows=d.execute(f"SELECT * FROM {t} WHERE {c}=?",(v,)).fetchall()\n  if len(rows)!=1:raise SystemExit(2)\n  r[t]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\n d.rollback()\nprint(json.dumps(r))`;
function pending() {const r=spawnSync(paths.portablePython(),['-B','-I','-c',pendingCode,path.join(repo,'.coding-tools/orchestration/ledger.sqlite3'),oldPending.run_id,oldPending.wave_id],{windowsHide:true,shell:false,timeout:15000,encoding:'utf8',maxBuffer:8192});need(!r.error&&r.status===0,'PENDING_READ_FAILED');const v=JSON.parse(r.stdout);need(v.runs===oldPending.runs&&v.waves===oldPending.waves,'OLD_PENDING_CHANGED');return v;}
function zeroVm() {const script="$ErrorActionPreference='Stop'; $names=@('WindowsSandbox','WindowsSandboxClient','WindowsSandboxServer','WindowsSandboxRemoteSession','vmmemWindowsSandbox'); $a=@(Get-Process | Where-Object { $names -contains $_.ProcessName }).Count; $b=@(Get-CimInstance Win32_Process -Filter \"Name='wxc-windows-sandbox-daemon.exe' OR Name='wxc-exec.exe' OR Name='wxc-windows-sandbox-guest.exe'\").Count; @{host_count=$a;backend_count=$b;content_free=$true} | ConvertTo-Json -Compress";const r=spawnSync('C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',['-NoProfile','-NonInteractive','-Command',script],{windowsHide:true,shell:false,timeout:10000,encoding:'utf8',maxBuffer:8192});need(!r.error&&r.status===0,'VM_CENSUS_UNAVAILABLE');const v=JSON.parse(r.stdout.replace(/^\uFEFF/,''));need(v.content_free===true&&v.host_count===0&&v.backend_count===0,'VM_OR_BACKEND_STILL_PRESENT');return v;}
async function localGuard() {
  verifyCandidate();const d=loadRecoveryDescriptor(paths),owner=await identity(d.owner_pid);need(descriptorMatchesInstallation(d,paths.runtimeIdentity())&&d.instance_id==='079fecd6cdf5a0ecd178685eb8db1e88'&&owner.state==='live'&&same(owner,{pid:25548,process_start_token:'134362096578839110'}),'HOST_PROVENANCE_CHANGED');
  const client=new RecoveryIpcClient({paths}),options=descriptorRequestOptions(d),n=await client.call('runtime.identity_observation',[],options);
  need(n.observation_kind==='mcp_identity_read_only'&&n.mcp_ready===true&&n.identity_current===true&&n.current_activation_epoch_id===nativePin.activation_epoch_id&&Object.entries(nativePin).every(([k,v])=>n[k]===v),'NATIVE_PROVENANCE_CHANGED');
  const status=await client.status({...options,fresh:true});need(status.activation_epoch?.state==='READY'&&status.activation_epoch.admission_open===true&&status.activation_epoch.update_incomplete===false,'LOCAL_RUNTIME_NOT_READY');
  const c=await canonicalLedgerCensus({paths,workspace:repo,allowAcceptancePending:true,pythonStatusFn:async()=>({installed:true,command:paths.portablePython(),prefixArgs:['-B']})});
  const keys=['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes'];
  need(c.mutated_canonical_ledger===false&&c.content_free===true&&keys.every(k=>c.counts[k]===0)&&c.snapshot?.query_only===true&&c.snapshot?.immutable===true&&equal(c.snapshot.integrity_check,['ok'])&&c.snapshot.foreign_key_check_rows===0&&c.lifecycle.unexplained_active_runs===0&&c.lifecycle.unbound_live_resource_residues===0&&c.lifecycle.projection_drift===false&&c.lifecycle.live_owned_runs.length===0&&equal(c.lifecycle.awaiting_acceptance_runs,[oldPending.run_id])&&c.lifecycle.blockers.every(k=>k==='live_runtime_state_process'),'LOCAL_JOBS_NOT_QUIESCENT');
  return {host:{pid:owner.pid,process_start_token:owner.process_start_token,instance_id:d.instance_id},native:nativePin,canonical_counts:c.counts,pending:pending(),vm:zeroVm(),ledger_mutated:false};
}
function installArgs(kind,v) {
  const a=['--config',paths.controlPlaneNodeConfigFile(),'--workspace-registry',paths.controlPlaneWorkspaceRegistryFile(),'--workspace-id',target.workspace_id,'--workspace-generation',target.workspace_generation,'--owner-id',target.owner_id,'--facade-schema-version',String(facade.schema_version),'--facade-profile',facade.profile,'--facade-sha256',facade.sha256,'--confirm-install','--replace'];
  if(kind==='Exec')a.push(...v.allowed_argv_prefixes.flatMap(p=>['--allowed-argv-prefix',JSON.stringify(p)]),'--max-timeout-ms',String(v.max_timeout_ms),'--max-output-bytes',String(v.max_output_bytes));
  else {a.push(...v.allowed_relative_prefixes.flatMap(p=>['--allowed-relative-prefix',p]));if(kind==='FileRead')a.push('--max-bytes',String(v.max_bytes),'--max-lines',String(v.max_lines));else a.push('--max-patch-bytes',String(v.max_patch_bytes),'--max-file-bytes',String(v.max_file_bytes));}
  return a;
}
async function authority(service) {const r=await service.runPackagedNodeAgent('inspect-policy-authority',['--config',paths.controlPlaneNodeConfigFile(),'--workspace-registry',paths.controlPlaneWorkspaceRegistryFile(),'--workspace-id',target.workspace_id,'--workspace-generation',target.workspace_generation]);const a=parsePolicyAuthorityObservation(r.stdout,target.workspace_id,target.workspace_generation);need(a.owner_id===target.owner_id&&a.standing_write_enabled===true&&a.exec_enabled===true&&a.exec_binding_count>=1&&equal(a.facade_contract,facade)&&Date.now()-a.observed_at_ms>=0&&Date.now()-a.observed_at_ms<60000,'LIVE_FACADE_AUTHORITY_MISMATCH');return a;}
async function synchronize() {
  need(process.argv.includes('--operator-approved-same-scope-r11'),'OPERATOR_APPROVAL_REQUIRED');guardServer(pinned('server'));const beforeLocal=await localGuard(),before=policySnapshot(true);emit({phase:'before_contract_reconciliation',local:beforeLocal,before_policies:before,authority_expires_at_ms:expiry,no_new_sandbox_probe:true});
  const attempt=path.join(__dirname,'sync-attempt.json');fs.writeFileSync(attempt,JSON.stringify({at_ms:Date.now(),helper_sha256:sha(__filename),no_automatic_retry:true})+'\n',{flag:'wx'});
  const service=new ControlPlaneEnrollmentService({paths,experimentalWindowsSandbox:true}),commands={FileRead:'install-file-read-policy',ApprovedPatch:'install-approved-patch-policy',Exec:'install-exec-policy'};
  for(const [kind,operation] of Object.entries(commands)) {
    guardServer(pinned('server'));await localGuard();const a=await authority(service);const current=policySnapshot();need(current[kind].file_sha256===before[kind].file_sha256,'POLICY_CHANGED_DURING_SYNC');
    const r=await service.runPackagedNodeAgent(operation,installArgs(kind,before[kind].value));
    const installed=JSON.parse(String(r.stdout).trim());need(installed.enabled===true&&installed.runtime_mode==='packaged'&&/^[a-f0-9]{64}$/.test(installed.policy_sha256||''),'INSTALL_RECEIPT_INVALID');
    const after=policySnapshot();guardReplacement(before[kind].value,after[kind].value);need(admittedDigest(after[kind].value)===installed.policy_sha256,'INSTALLED_POLICY_DIGEST_MISMATCH');emit({phase:'contract_policy_reconciled',kind,file_sha256:after[kind].file_sha256,installed_policy_sha256:installed.policy_sha256,facade_contract:a.facade_contract,noncontract_fields_unchanged:true,sandbox_probe_performed:false});
  }
  guardServer(pinned('server'));const afterLocal=await localGuard(),after=policySnapshot();need(after.ReadOnly.file_sha256===before.ReadOnly.file_sha256,'METADATA_POLICY_CHANGED');for(const kind of Object.keys(commands))guardReplacement(before[kind].value,after[kind].value);
  emit({phase:'contract_reconciliation_complete',ok:true,after_policies:after,local:afterLocal,authority_expires_at_ms:expiry,metadata_policy_unchanged:true,noncontract_fields_unchanged:true,sandbox_probe_performed:false,runtime_restarted:false,server_mutated:false,acceptance_performed:false});
}
async function main(){if(process.argv[2]==='observe')emit({phase:'policy_contract_observation',ok:true,policies:policySnapshot(true),local:await localGuard(),runtime_mutated:false,server_mutated:false});else if(process.argv[2]==='sync')await synchronize();else fail('PHASE_INVALID');}
module.exports={guardReplacement,guardServer,installArgs,canonical,admittedDigest,facade,target,expiry,requested,nativePin,contextId,pilotId,serverRevision};
if(require.main===module)main().catch(e=>{emit({ok:false,code:String(e.code||'RECONCILIATION_REFUSED').replace(/[^A-Za-z0-9_.:-]/g,'').slice(0,128),partial_state_possible:fs.existsSync(path.join(__dirname,'sync-attempt.json')),no_automatic_retry:true,no_further_dispatch_until_reconciled:true,acceptance_performed:false,secret_values_emitted:false});process.exitCode=2;});
