const fs = require('node:fs');
const path = require('node:path');
const candidate = path.resolve(process.argv[2]);
if (process.execPath.toLowerCase() !== path.join(candidate, 'Coding Tools MCP.exe').toLowerCase()) throw new Error('EXACT_ELECTRON_REQUIRED');
const load = name => require(path.join(candidate, 'resources', 'app.asar', 'electron', 'services', name));
const { RuntimePaths } = load('runtimePaths');
const { ControlPlaneEnrollmentService, parsePolicyAuthorityObservation } = load('controlPlaneEnrollment');
const paths = new RuntimePaths({ dataRoot:path.join(process.env.APPDATA,'web-mcp-assistant'),
  appRoot:path.join(candidate,'resources','app.asar'), resourcesRoot:path.join(candidate,'resources','resources'),
  executablePath:process.execPath, runtimeMode:'packaged' });
const service = new ControlPlaneEnrollmentService({ paths, experimentalWindowsSandbox:true });
(async () => {
  const id='workspace_bc86004be2684b958ab7a9a6f9530cd7';
  const gen='generation_03f9c04f1b14414fa4bfa7d91cc8ea7a';
  const start=Date.now();
  const result=await service.runPackagedNodeAgent('inspect-policy-authority',[
    '--config',paths.controlPlaneNodeConfigFile(),'--workspace-registry',paths.controlPlaneWorkspaceRegistryFile(),
    '--workspace-id',id,'--workspace-generation',gen,'--project-root',candidate,'--node',process.execPath,'--runtime-mode','packaged']);
  const now=Date.now(); const observation=parsePolicyAuthorityObservation(result.stdout,id,gen);
  const output={operation:'authority_clock_readonly', started_at_ms:start,local_received_at_ms:now,
    server_observed_at_ms:observation.observed_at_ms,age_ms:now-observation.observed_at_ms,
    request_duration_ms:now-start,mutation:false};
  fs.writeFileSync(path.join(__dirname,`authority-clock-${now}.json`),JSON.stringify(output,null,2));
  console.log(JSON.stringify(output));
})().catch(error=>{console.error(JSON.stringify({ok:false,code:error.code||error.name}));process.exitCode=1;});
