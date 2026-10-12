const fs = require('node:fs');
const path = require('node:path');
const repo = path.resolve(__dirname, '../../..');
const { createRuntimePaths } = require(path.join(repo, 'electron/services/runtimePaths'));
const { ControlPlaneEnrollmentService } = require(path.join(repo, 'electron/services/controlPlaneEnrollment'));
const { loadRecoveryDescriptor } = require(path.join(repo, 'electron/services/recoveryIpc'));
const { descriptorMatchesInstallation } = require(path.join(repo, 'electron/services/recoveryHostLauncher'));
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-folders-unified-1011-r3/win-unpacked');
const paths = createRuntimePaths({
  dataRoot: path.join(process.env.APPDATA, 'web-mcp-assistant'),
  appRoot: path.join(candidate, 'resources/app.asar'),
  resourcesRoot: path.join(candidate, 'resources/resources'),
  runtimeMode: 'packaged', executablePath: path.join(candidate, 'Coding Tools MCP.exe')
});
const service = new ControlPlaneEnrollmentService({paths, experimentalWindowsSandbox:true});
const target = {workspaceId:'workspace_dda1d78e9a21402aa6213f72af64f788',
  workspaceGeneration:'generation_c2f13e8d02344cf6a38a3f42ecfa59b6', replaceExisting:true};
function emit(value) { process.stdout.write(JSON.stringify(value)+'\n'); }
(async () => {
  const phase = process.argv[2];
  if (!descriptorMatchesInstallation(loadRecoveryDescriptor(paths), paths.runtimeIdentity())) {
    throw Object.assign(new Error('Candidate installation changed'), {code:'R3_INSTALLATION_MISMATCH'});
  }
  if (phase === 'install') {
    const metadata = await service.installReadOnlyPolicyAssignment(target);
    emit({phase:'metadata_installed',result:metadata});
    const files = await service.installStandingWorkspaceFilePolicies({...target,allowWrite:true});
    emit({phase:'files_installed',result:files});
    if (files.state !== 'read_and_patch') throw Object.assign(new Error('File install partial'), {code:files.error_code || 'FILE_INSTALL_PARTIAL'});
    const observed = await service.inspectStandingWorkspaceFilePolicies();
    emit({phase:'files_observed',result:observed});
    const exec = await service.inspectStandingWorkspaceExecPolicy(target);
    emit({phase:'exec_observed',result:exec});
    fs.writeFileSync(path.join(__dirname,'local-policy-result.json'),JSON.stringify({metadata,files,observed,exec},null,2));
    if (exec.sandbox.state === 'available') {
      const installed = await service.installStandingWorkspaceExecPolicy(target);
      emit({phase:'exec_installed',result:installed});
      fs.writeFileSync(path.join(__dirname,'exec-policy-result.json'),JSON.stringify(installed,null,2));
    }
  } else if (phase === 'metadata') {
    const metadata = await service.installReadOnlyPolicyAssignment(target);
    emit({phase:'metadata_installed',result:metadata});
    fs.writeFileSync(path.join(__dirname,'metadata-renewal-result.json'),JSON.stringify(metadata,null,2));
  } else if (phase === 'exec') {
    const files = await service.inspectStandingWorkspaceFilePolicies();
    if (![files.file_read, files.approved_patch].every(policy => policy?.enabled === true
      && policy.workspace_id === target.workspaceId
      && policy.workspace_generation === target.workspaceGeneration)) {
      throw Object.assign(new Error('File policy incomplete'), {code:'FILE_POLICY_NOT_READY'});
    }
    const observed = await service.inspectStandingWorkspaceExecPolicy(target);
    emit({phase:'exec_observed',result:observed});
    if (observed.sandbox.state !== 'available') {
      throw Object.assign(new Error('Sandbox unavailable'), {code:'WINDOWS_SANDBOX_NOT_READY'});
    }
    const installed = await service.installStandingWorkspaceExecPolicy(target);
    emit({phase:'exec_installed',result:installed});
    fs.writeFileSync(path.join(__dirname,'exec-policy-result.json'),JSON.stringify(installed,null,2));
  } else if (phase === 'status') {
    emit({phase,files:await service.inspectStandingWorkspaceFilePolicies(),
      exec:await service.inspectStandingWorkspaceExecPolicy(target)});
  } else if (phase === 'authority') {
    const result = await service.runPackagedNodeAgent('inspect-policy-authority',[
      '--config',paths.controlPlaneNodeConfigFile(),'--workspace-registry',paths.controlPlaneWorkspaceRegistryFile(),
      '--workspace-id',target.workspaceId,'--workspace-generation',target.workspaceGeneration
    ]);
    emit({phase,result:JSON.parse(result.stdout)});
  } else throw new Error('Unknown phase');
})().catch(error=>{emit({ok:false,error:String(error.code || 'LOCAL_POLICY_OPERATION_FAILED')});process.exitCode=1;});
