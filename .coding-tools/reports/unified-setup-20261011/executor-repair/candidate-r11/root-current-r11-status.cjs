'use strict';
const fs=require('node:fs'),path=require('node:path');
const repo='E:\\Github\\Tools-Codex-web',services=path.join(repo,'electron/services');
const {pathsFor}=require('./activation-windows/transition-r11.cjs');
const {RecoveryIpcClient,loadRecoveryDescriptor}=require(path.join(services,'recoveryIpc'));
const {descriptorRequestOptions,descriptorMatchesInstallation}=require(path.join(services,'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity,sameProcessIdentity}=require(path.join(services,'processIdentity'));
async function main(){
 const paths=pathsFor('r11'),d=loadRecoveryDescriptor(paths),o=await observeLifecycleProcessIdentity(d.owner_pid);
 if(!descriptorMatchesInstallation(d,paths.runtimeIdentity())||o.state!=='live'||!sameProcessIdentity(o,{pid:d.owner_pid,process_start_token:d.owner_process_start_token}))throw Object.assign(new Error(),{code:'CURRENT_R11_HOST_UNPROVEN'});
 const client=new RecoveryIpcClient({paths}),options=descriptorRequestOptions(d),s=await client.status({...options,fresh:true}),l=await client.call('runtime.lightweight_snapshot',[],options),n=await client.call('runtime.identity_observation',[],options);
 const v={ok:true,observed_at_ms:Date.now(),runtime_mutated:false,host:{pid:o.pid,process_start_token:o.process_start_token,instance_id:d.instance_id},readiness:Object.fromEntries(['fullyReady','localReady','centralConnected','authorityReady','updateIncomplete'].map(k=>[k,l[k]??null])),epoch:{id:s.activation_epoch?.activation_epoch_id,state:s.activation_epoch?.state,admission_open:s.activation_epoch?.admission_open,update_incomplete:s.activation_epoch?.update_incomplete},native:n};
 fs.appendFileSync(path.join(__dirname,'current-r11-status.jsonl'),JSON.stringify(v)+'\n');process.stdout.write(JSON.stringify(v)+'\n');
}
main().catch(e=>{process.stdout.write(JSON.stringify({ok:false,code:e.code||'CURRENT_R11_STATUS_UNAVAILABLE',runtime_mutated:false})+'\n');process.exitCode=2;});
