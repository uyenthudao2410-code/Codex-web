'use strict';
// Recover the approved r10 trial after its exact process set disappeared.
// One current authority window; no grant changes, command replay or acceptance.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), Module = require('node:module');
const { spawn } = require('node:child_process');
const helper = path.join(__dirname, 'activate-r10-v2.cjs');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const fail = code => { throw Object.assign(new Error(), { code }); };
const oldJournal = path.join(__dirname, 'windows-activation-v2.jsonl');
const handoffJournal = path.join(__dirname, 'windows-handoff-continuation.jsonl');
const journal = path.join(__dirname, 'windows-trial-recovery.jsonl');
const closureFile = path.join(__dirname, 'server-recovery-closed.json');
const expectedInstallation = '36cd3af6fe1da4607cfe3035d48becd97dc12265901b480401bf44389ff1d1dc';
const retired = [{pid:14516,process_start_token:'134361966532424140'}, {pid:15660,process_start_token:'134361966677348870'},
  {pid:6064,process_start_token:'134361966557949550'}, {pid:3584,process_start_token:'134361969912419610'}];
const repo = path.resolve(__dirname, '../../../../../..');
const candidate = path.join(repo,'dist/windows-candidate-mxc-wsb-cbe1774-setup-exec-contract-1011-r10/win-unpacked');
const executable = path.join(candidate,'Coding Tools MCP.exe');
const rows = file => fs.existsSync(file) ? fs.readFileSync(file,'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse) : [];
const safe = value => /^[A-Z0-9_]{1,128}$/.test(value || '') ? value : 'R10_RECOVERY_REFUSED';
function emit(value) { const row={observed_at:new Date().toISOString(), helper_sha256:sha(__filename),...value}; fs.appendFileSync(journal,JSON.stringify(row)+'\n'); process.stdout.write(JSON.stringify(row)+'\n'); return row; }
if (sha(helper)!=='4b689f8533f1de77130257543b408aec43b3f91e79579015a7a10a054db06b05' || sha(oldJournal)!=='4213950067cc15136df9dfd4da95978c5d216f47754ac37464367da7ab2a24b3') fail('FROZEN_HELPER_CHANGED');
let code=fs.readFileSync(helper,'utf8');
const terminal="main().catch(error => { emit({ ok: false, code: safeText(error.code || 'R10_ACTIVATION_FAILED'), cause_code: safeText(error.cause?.code), no_automatic_retry: true }); process.exitCode = 1; });";
if(code.split(terminal).length!==2) fail('FROZEN_ENTRYPOINT_CHANGED');
code=code.replace(terminal,`module.exports={ verifyFiles, authorizationGuard, renewalGuard, observedDescriptor, authenticated, inspectRuntime, descriptorIdentity, observeLifecycleProcessIdentity, sameProcessIdentity,
 censusFor, assertCensus, inspectPoliciesNoProbe, assertPoliciesUnchanged, assertPendingRecords, zeroVmProof, refresh, startAgent, proof,
 installHooks(hooks){ emit=hooks.emit;lastReceipt=hooks.lastReceipt;currentR10=hooks.currentR10;mutationGuard=hooks.mutationGuard;} };`);
const loaded=new Module(helper,module); loaded.filename=helper;loaded.paths=Module._nodeModulePaths(path.dirname(helper));loaded._compile(code,helper); const v2=loaded.exports;
function last(phase){return rows(journal).findLast(row=>row.phase===phase);}
function mutationGuard(){
  const auth=v2.authorizationGuard();v2.verifyFiles();const renewal=v2.renewalGuard();
  const value=process.argv.find(x=>x.startsWith('--recovery-closure-sha256='));
  if(!value || value.slice(26)!==sha(closureFile)) fail('EXACT_RECOVERY_CLOSURE_REQUIRED');
  const closure=JSON.parse(fs.readFileSync(closureFile,'utf8'));
  if(closure.ok!==true || closure.phase!=='r10_same_window_intake_closed' || closure.admission!=='recovery'
    || closure.service_instance_id!==renewal.service_instance_id || closure.context_id!==renewal.context_id || closure.pilot_id!==renewal.pilot_id
    || closure.expires_at_ms!==renewal.expires_at_ms || closure.source_revision!==renewal.source_revision
    || closure.observed_at_ms>Date.now() || Date.now()-closure.observed_at_ms>=600000) fail('FRESH_SAME_WINDOW_RECOVERY_CLOSURE_REQUIRED');
  return {...auth,...renewal};
}
async function descriptor(){
  v2.verifyFiles();const observed=await v2.observedDescriptor();
  if(observed.tag!=='r10' || observed.owner.state!=='live' || observed.descriptor.installation_id!==expectedInstallation) fail('EXACT_R10_INSTALLATION_REQUIRED');
  return observed;
}
async function currentR10(){
  const observed=await descriptor(), started=last('recovery_candidate_started');
  if(!started) fail('RECOVERY_SPAWN_RECEIPT_REQUIRED');
  const epochFile=JSON.parse(fs.readFileSync(observed.paths.activationEpochFile(),'utf8')).current;
  if(JSON.stringify(v2.descriptorIdentity(observed.descriptor))===JSON.stringify(started.descriptor)) return observed;
  const refresh=last('refresh');
  if(!refresh || refresh.state!=='HANDOFF' || epochFile.activation_epoch_id!==refresh.epoch
    || epochFile.owner_pid!==started.owner.pid || epochFile.owner_instance_id!==started.descriptor.instance_id
    || epochFile.operation_id!==epochFile.verification?.operation_id && epochFile.verification?.operation_id
    || !['VERIFYING','READY'].includes(epochFile.state) || epochFile.error) fail('EXACT_RECOVERY_HANDOFF_REQUIRED');
  const proof=epochFile.state==='READY'?epochFile.verification?.final_census:epochFile.verification;
  if(!proof || proof.host_pid!==observed.owner.pid || proof.host_instance_id!==observed.descriptor.instance_id
    || proof.expected_old_host_pid!==started.owner.pid || proof.expected_old_host_instance_id!==started.descriptor.instance_id
    || ['workspace_matches','device_matches','revision_matches','process_identity_verified','epoch_matches'].some(key=>proof[key]!==true)) fail('RECOVERY_HANDOFF_CURRENT_PROOF_REQUIRED');
  return observed;
}
v2.installHooks({emit,currentR10,mutationGuard,lastReceipt:(phase,tag)=>[...rows(oldJournal),...rows(handoffJournal),...rows(journal)].findLast(row=>row.phase===phase&&(!tag||row.tag===tag))||null});
async function spawnCandidate(){
  mutationGuard();if(last('recovery_candidate_spawned'))fail('RECOVERY_SPAWN_ALREADY_ATTEMPTED');
  for(const identity of retired){if((await v2.observeLifecycleProcessIdentity(identity.pid)).state!=='absent')fail('PREVIOUS_RUNTIME_NOT_ABSENT');}
  const observed=await v2.observedDescriptor();if(observed.owner.state!=='absent')fail('UNEXPECTED_LIVE_HOST');
  v2.assertCensus(await v2.censusFor(observed,'recovery_absent_census'));v2.assertPendingRecords(observed.paths);
  v2.assertPoliciesUnchanged(await v2.inspectPoliciesNoProbe(observed));v2.zeroVmProof('before_recovery_spawn');mutationGuard();
  const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
  const child=spawn(executable,[],{env,windowsHide:true,detached:true,stdio:'ignore'});
  await new Promise((resolve,reject)=>{child.once('spawn',resolve);child.once('error',reject);});child.unref();emit({phase:'recovery_candidate_spawned',tag:'r10',pid:child.pid});
  const deadline=Date.now()+45000;while(Date.now()<deadline){try{const live=await descriptor();await v2.inspectRuntime(live,'recovery_candidate_started');return;}
    catch(error){if(!['RECOVERY_DESCRIPTOR_STALE','RECOVERY_DESCRIPTOR_MISSING','RECOVERY_HOST_UNAVAILABLE','EXACT_R10_INSTALLATION_REQUIRED'].includes(error.code))throw error;}
    await new Promise(resolve=>setTimeout(resolve,500));}fail('RECOVERY_SPAWN_NOT_OBSERVED');
}
async function main(){const phase=process.argv[2];if(phase==='spawn')await spawnCandidate();else if(phase==='status'){await v2.inspectRuntime(await currentR10());}
 else if(phase==='refresh')await v2.refresh();else if(phase==='agent')await v2.startAgent();else if(phase==='proof')await v2.proof();else fail('RECOVERY_PHASE_INVALID');}
main().catch(error=>{emit({ok:false,code:safe(error.code),no_automatic_retry:true});process.exitCode=1;});
