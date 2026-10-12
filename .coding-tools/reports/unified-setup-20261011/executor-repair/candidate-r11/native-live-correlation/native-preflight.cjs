'use strict';
// Root executes this query-only preflight. Only an exclusive public receipt is saved.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {spawnSync, execFileSync} = require('node:child_process');
const repo = 'E:\\Github\\Tools-Codex-web';
const services = path.join(repo, 'electron/services');
const {createRuntimePaths} = require(path.join(services, 'runtimePaths'));
const {RecoveryIpcClient} = require(path.join(services, 'recoveryIpc'));
const {descriptorRequestOptions, descriptorMatchesInstallation} = require(path.join(services, 'recoveryHostLauncher'));
const {observeLifecycleProcessIdentity, sameProcessIdentity} = require(path.join(services, 'processIdentity'));
const {canonicalLedgerCensus} = require(path.join(services, 'fullCleanActivation'));
const dataRoot = 'C:\\Users\\daoth\\AppData\\Roaming\\web-mcp-assistant';
const candidate = path.join(repo, 'dist/windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11/win-unpacked');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const oldRun = '95e909f0040a448faa9f1f3257e2ee2c', oldWave = 'c101beadfc6d4f2fbc13845052c84693';
const oldHashes = {runs: 'a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590', waves: '59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce'};
const expectedPre = '90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650';
const expectedChecker = '059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230';
const fail = code => {throw Object.assign(new Error(), {code});};
const need = (test, code) => {if (!test) fail(code);};
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const pendingCode = `import hashlib,json,sqlite3,sys\nfrom pathlib import Path\nfrom contextlib import closing\nwith closing(sqlite3.connect(Path(sys.argv[1]).resolve(strict=True).as_uri()+"?mode=ro",uri=True,timeout=10)) as db:\n db.row_factory=sqlite3.Row;db.execute("PRAGMA query_only=ON");db.execute("BEGIN");result={}\n for table,column,value in (("runs","run_id",sys.argv[2]),("waves","wave_id",sys.argv[3])):\n  rows=db.execute(f"SELECT * FROM {table} WHERE {column}=?",(value,)).fetchall()\n  if len(rows)!=1:raise SystemExit(2)\n  result[table]=hashlib.sha256(json.dumps(dict(rows[0]),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()\n db.rollback()\nprint(json.dumps(result))`;
async function main() {
  const paths = createRuntimePaths({dataRoot, appRoot:path.join(candidate,'resources/app.asar'), resourcesRoot:path.join(candidate,'resources/resources'), runtimeMode:'packaged', executablePath:path.join(candidate,'Coding Tools MCP.exe')});
  const descriptor = read(paths.recoveryHostDescriptorFile());
  need(descriptorMatchesInstallation(descriptor, paths.runtimeIdentity()), 'R11_INSTALLATION_REQUIRED');
  const owner = await observeLifecycleProcessIdentity(descriptor.owner_pid);
  need(owner.state === 'live' && sameProcessIdentity({pid:descriptor.owner_pid,process_start_token:descriptor.owner_process_start_token}, owner), 'HOST_IDENTITY_CHANGED');
  const client = new RecoveryIpcClient({paths}), options = descriptorRequestOptions(descriptor);
  const identity = await client.call('runtime.identity_observation', [], options);
  need(identity.observation_kind === 'mcp_identity_read_only' && identity.mcp_ready === true && identity.identity_current === true
    && identity.activation_epoch_id === identity.current_activation_epoch_id, 'NATIVE_IDENTITY_NOT_CURRENT_READY');
  need(['mcp_process_instance_id','mcp_server_instance_id','activation_epoch_id'].every(key => /^[A-Za-z0-9_-]{1,256}$/.test(identity[key] || ''))
    && /^[a-f0-9]{64}$/.test(identity.tool_contract_sha256 || ''), 'NATIVE_IDENTITY_INVALID');
  const sourceHead = execFileSync('git', ['--no-optional-locks','rev-parse','HEAD'], {cwd:repo,encoding:'utf8',windowsHide:true}).trim();
  need(sourceHead === '2c554f59cb7b8ffc86ce5e0e28076c792777642f', 'HEAD_CHANGED');
  const preimage = sha(fs.readFileSync(path.join(repo,'tests/fixtures/initial-proof-canary-target.cjs')));
  const checker = sha(fs.readFileSync(path.join(repo,'tests/fixtures/initial-proof-canary-check.cjs')));
  need(preimage === expectedPre && checker === expectedChecker, 'CANARY_SOURCE_CHANGED');
  const pending = spawnSync(paths.portablePython(), ['-B','-I','-c',pendingCode,path.join(repo,'.coding-tools/orchestration/ledger.sqlite3'),oldRun,oldWave], {shell:false,windowsHide:true,encoding:'utf8',timeout:15000,maxBuffer:8192});
  need(!pending.error && pending.status === 0, 'PENDING_READ_FAILED');
  const hashes = JSON.parse(pending.stdout);
  need(hashes.runs === oldHashes.runs && hashes.waves === oldHashes.waves, 'OLD_PENDING_CHANGED');
  const census = await canonicalLedgerCensus({paths,workspace:repo,allowAcceptancePending:true,pythonStatusFn:async()=>({installed:true,command:paths.portablePython(),prefixArgs:['-B']})});
  const keys = ['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes'];
  need(census.mutated_canonical_ledger === false && keys.every(key => census.counts[key] === 0)
    && census.snapshot?.query_only === true && census.snapshot?.immutable === true
    && census.snapshot?.integrity_check?.length === 1 && census.snapshot.integrity_check[0] === 'ok'
    && census.snapshot?.foreign_key_check_rows === 0
    && census.lifecycle?.unexplained_active_runs === 0 && census.lifecycle?.unbound_live_resource_residues === 0
    && census.lifecycle?.projection_drift === false
    && (census.lifecycle?.blockers || []).every(code => code === 'live_runtime_state_process'), 'CANONICAL_CENSUS_NOT_QUIESCENT');
  const observed = Date.now();
  const nativePreflight = {observed_at_ms:observed,source_head:sourceHead,preimage_sha256:preimage,checker_sha256:checker,
    old_run_sha256:hashes.runs,old_wave_sha256:hashes.waves,no_active_jobs:true};
  const result = {ok:true,kind:'r11_query_only_native_preflight',observed_at_ms:observed,native_preflight:nativePreflight,
    activation_epoch:identity.activation_epoch_id,runtime_instance_id:identity.mcp_process_instance_id,
    mcp_server_instance_id:identity.mcp_server_instance_id,native_tool_contract_sha256:identity.tool_contract_sha256,
    contract_version:'sha256:'+identity.tool_contract_sha256,
    census:{counts:Object.fromEntries(keys.map(key=>[key,census.counts[key]])),snapshot:census.snapshot,
      blockers:census.lifecycle.blockers,mutated_canonical_ledger:false},source_unchanged:true,external_mutation:false};
  const after = sha(fs.readFileSync(path.join(repo,'tests/fixtures/initial-proof-canary-target.cjs')));
  need(after === preimage && sha(fs.readFileSync(path.join(repo,'tests/fixtures/initial-proof-canary-check.cjs'))) === checker, 'SOURCE_CHANGED_DURING_PREFLIGHT');
  const afterIdentity = await client.call('runtime.identity_observation', [], options);
  need(afterIdentity.identity_current === true && afterIdentity.mcp_ready === true
    && ['mcp_process_instance_id','mcp_server_instance_id','activation_epoch_id','tool_contract_sha256'].every(key=>afterIdentity[key]===identity[key]), 'NATIVE_IDENTITY_CHANGED_DURING_PREFLIGHT');
  const file = path.join(__dirname, 'native-preflight-'+observed+'.json');
  fs.writeFileSync(file,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({...result,receipt_path:file,receipt_sha256:sha(fs.readFileSync(file))})+'\n');
}
main().catch(error=>{process.stdout.write(JSON.stringify({ok:false,code:error.code||'QUERY_ONLY_PREFLIGHT_FAILED',external_mutation:false})+'\n');process.exitCode=2;});
