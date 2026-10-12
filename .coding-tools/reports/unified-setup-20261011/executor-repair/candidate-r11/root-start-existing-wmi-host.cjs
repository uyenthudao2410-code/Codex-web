'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const repo='E:\\Github\\Tools-Codex-web',base=__dirname,services=path.join(repo,'electron/services');
const host=require('./lifecycle-wmi-resume/resume-native-modules.cjs');
const {pathsFor}=require('./activation-windows/transition-r11.cjs');
const {RecoveryIpcClient,loadRecoveryDescriptor}=require(path.join(services,'recoveryIpc'));
const {descriptorRequestOptions,descriptorMatchesInstallation}=require(path.join(services,'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity,sameProcessIdentity}=require(path.join(services,'processIdentity'));
const guard=require('./policy-contract-reconciliation/reconcile.cjs');
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
function need(v,c){if(!v)throw Object.assign(new Error(),{code:c});}
function emit(v){fs.appendFileSync(path.join(base,'existing-wmi-host-start.jsonl'),JSON.stringify({...v,at_ms:Date.now()})+'\n');process.stdout.write(JSON.stringify(v)+'\n');}
async function main(){
 const server=process.argv.find(a=>a.startsWith('--server=')).slice(9),expected=process.argv.find(a=>a.startsWith('--server-sha256=')).slice(16);
 need(sha(server)===expected,'SERVER_RECEIPT_CHANGED');guard.guardServer(JSON.parse(fs.readFileSync(server,'utf8')).public_receipts[0]);
 host.verify();await host.census();
 const paths=pathsFor('r11'),d=loadRecoveryDescriptor(paths),owner=await observeLifecycleProcessIdentity(17272);
 need(d.owner_pid===17272&&owner.state==='live'&&sameProcessIdentity(owner,{pid:d.owner_pid,process_start_token:d.owner_process_start_token})&&descriptorMatchesInstallation(d,paths.runtimeIdentity()),'EXACT_WMI_HOST_IDENTITY_REQUIRED');
 const client=new RecoveryIpcClient({paths}),options=descriptorRequestOptions(d),ping=await client.ping(options);
 need(ping.pid===17272&&ping.instance_id===d.instance_id&&ping.process_start_token===owner.process_start_token,'AUTHENTICATED_HOST_PING_REQUIRED');
 fs.writeFileSync(path.join(base,'existing-wmi-host-start-intent.json'),JSON.stringify({pid:17272,process_start_token:owner.process_start_token,instance_id:d.instance_id,at_ms:Date.now(),no_automatic_retry:true})+'\n',{flag:'wx'});
 emit({phase:'existing_wmi_host_start_reserved',pid:17272,process_start_token:owner.process_start_token,instance_id:d.instance_id,job_association:true,job_identity_unproven:true,new_host_spawned:false});
 const result=await client.start({}, {...options,timeout:60000});
 emit({phase:'existing_wmi_host_runtime_started',ok:true,pid:17272,state:result.state||null,new_host_spawned:false,refresh_performed:false,acceptance_performed:false});
}
main().catch(e=>{emit({ok:false,code:e.code||'EXISTING_WMI_HOST_START_REFUSED',no_automatic_retry:true,raw_error_emitted:false});process.exitCode=2;});
