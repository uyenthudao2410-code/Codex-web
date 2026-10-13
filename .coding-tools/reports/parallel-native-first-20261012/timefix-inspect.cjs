console.log('begin');
try {
const path=require('node:path'); const root='E:/DEV/Codex-web'; const appRoot=path.join(root,'dist/windows-candidate-mxc-wsb-cbe1774-parallel-native-1012-r4/win-unpacked'); const exe=path.join(appRoot,'Coding Tools MCP.exe');
console.log('app',appRoot);
const {RuntimePaths}=require(path.join(appRoot,'resources/app.asar/electron/services/runtimePaths')); console.log('rp');
const {RecoveryIpcClient,loadRecoveryDescriptor}=require(path.join(appRoot,'resources/app.asar/electron/services/recoveryIpc')); console.log('ipc');
const {descriptorRequestOptions,readVerifiedReadyHost}=require(path.join(appRoot,'resources/app.asar/electron/services/recoveryHostLauncher')); console.log('launcher');
const paths=new RuntimePaths({dataRoot:path.join(process.env.APPDATA,'web-mcp-assistant'),appRoot,resourcesRoot:path.join(appRoot,'resources/resources'),executablePath:exe,runtimeMode:'packaged'}); console.log('paths');
const hold=setInterval(()=>{},1000);
(async()=>{ console.log('async'); const client=new RecoveryIpcClient({paths}); const verified=await readVerifiedReadyHost(client,paths,loadRecoveryDescriptor,2,{allowAdmissionBlocked:true}); console.log('verified'); const expected=descriptorRequestOptions(verified.descriptor); const call=(a,args=[])=>client.call(a,args,expected); const out={descriptor:verified.descriptor,activation:await call('runtime.activation_epoch_status'),runtime:await call('runtime.lightweight_snapshot'),status:await call('recovery.status',[{fresh:true}])}; console.log(JSON.stringify(out)); clearInterval(hold);})().catch(e=>{console.error('ERR',e.stack||e);clearInterval(hold);process.exitCode=1});
} catch(e){console.error('TOP',e.stack||e);}
process.stdin.resume();
