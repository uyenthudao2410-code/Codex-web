"""Final read-only inventory/action/authority census after exact failure cleanup."""
import re
ACTION = 'act_2673b93c5bb3483889742dfe3055fd3d'
TASK = 'task_8982097843784d44bcc4bb0440c35141'
BINDING = 'bind_3e05bf64cb3e4bab93d930ae1692bebb'
DEVICE = '72ceec2d-e3f2-472f-8e3c-99fffe053035'
CONTEXT = 'ctx_01ca575dd5fa46cc95432e8f5aa56848'
PILOT = 'pilot_39a7fb99d6f7475db1e553383c3f3e2e'
EXPIRY = 1791717633341
SAFE_CODE = re.compile(r'[A-Z][A-Z0-9_]{2,95}')
SAFE_STATE = re.compile(r'[a-z][a-z0-9_]{0,63}')
try:
    require(pwd.getpwuid(os.getuid()).pw_name == USER, 'EXECUTION_USER_MISMATCH')
    values = parse_environment(protected_file(ENV_FILE))
    bind = values.get('CONTROL_PLANE_BIND', '127.0.0.1')
    if bind in {'0.0.0.0', '::'}:
        bind = '127.0.0.1'
    origin = 'http://' + bind + ':' + values.get('CONTROL_PLANE_PORT', '8765')
    token = values['CONTROL_PLANE_OPERATOR_TOKEN']
    health = verify_health(origin, token, REVISION, PACKAGE)
    verification = verify_release(CURRENT.resolve(strict=True), REVISION, PACKAGE)
    overview = json_request(origin, token, '/v1/ui/overview')
    observed = overview['observed_at_ms']
    state = require_quiescent(Path(values['CONTROL_PLANE_DB']))
    require(state['open_tasks'] == 0, 'OPEN_TASKS_REMAIN')
    require(state['historical_action_families_sha256'] == '825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed', 'HISTORICAL_EVIDENCE_CHANGED')
    action = json_request(origin, token, '/v1/actions/' + ACTION)
    require(action.get('action_id') == ACTION and action.get('task_id') == TASK and action.get('binding_id') == BINDING and action.get('delivery_state') == 'settled', 'FINAL_ACTION_STATE_MISMATCH')
    require(len(action.get('attempts', [])) == 1, 'ACTION_REPLAY_DETECTED')
    receipts = []
    for receipt in action.get('receipts', []):
        payload = json.loads(receipt.get('payload_json') or '{}')
        require(isinstance(payload, dict), 'RECEIPT_PAYLOAD_INVALID')
        safe = {k:receipt.get(k) for k in ('receipt_id','receipt_state','received_at_ms','receipt_digest')}
        safe['local_handle_present'] = bool(receipt.get('local_handle'))
        for key in ('code','diagnostic_code'):
            if isinstance(payload.get(key), str) and SAFE_CODE.fullmatch(payload[key]):
                safe[key] = payload[key]
        for key in ('operation_kind','process_state','phase','category'):
            if isinstance(payload.get(key),str) and SAFE_STATE.fullmatch(payload[key]):
                safe[key] = payload[key]
        safe['exit_code_present'] = isinstance(payload.get('exit_code'),int) and not isinstance(payload.get('exit_code'),bool)
        receipts.append(safe)
    unknown = [r for r in receipts if r['receipt_id'] == 'rcpt_420d659f8dac4aa1941b4c126acf7784']
    terminal = [r for r in receipts if r['receipt_id'] == 'rcpt_97a6b0ffb80149fd8f87c5d6b70e3182']
    require(len(unknown)==1 and unknown[0]['receipt_state']=='unknown' and unknown[0]['receipt_digest']=='8d3914e1391aa13728c3a483e7e8b3a327f1221e5bc691115c312ae7caf99dd5', 'ORIGINAL_UNKNOWN_CHANGED')
    require(len(terminal)==1 and terminal[0]['receipt_state']=='failed' and not terminal[0]['exit_code_present'], 'TERMINAL_FAILURE_RECEIPT_MISMATCH')
    contexts = [r for r in overview['contexts'] if r.get('context_id')==CONTEXT]
    pilots = [r for r in overview['scoped_pilot_decisions'] if r.get('decision_id')==PILOT]
    require(len(contexts)==1 and contexts[0]['binding_id']==BINDING and contexts[0]['closed_at_ms'] is None and contexts[0]['expires_at_ms']==EXPIRY, 'APPROVED_CONTEXT_CHANGED')
    require(len(pilots)==1 and pilots[0]['binding_id']==BINDING and pilots[0]['revoked_at_ms'] is None and pilots[0]['expires_at_ms']==EXPIRY, 'APPROVED_PILOT_CHANGED')
    require(health['admission_mode']=='scoped_pilot' and observed<EXPIRY,'AUTHORITY_WINDOW_CHANGED_OR_EXPIRED')
    tunnel = parse_environment(protected_file(HOME / '.config/codex-control-plane/mcp-tunnel.env'))
    header_path = Path(tunnel['CONTROL_PLANE_MCP_AUTH_HEADER_FILE'])
    require(header_path.is_file() and not header_path.is_symlink(), 'HEADER_TARGET_UNSAFE')
    metadata = header_path.stat()
    require(metadata.st_uid==os.getuid() and stat.S_IMODE(metadata.st_mode) in {0o400,0o600}, 'HEADER_ACL_INVALID')
    authorization = header_path.read_text().strip()
    require(authorization.startswith('Bearer '),'HEADER_FORMAT_INVALID')
    mcp_origin = 'http://127.0.0.1:' + values.get('CONTROL_PLANE_MCP_PORT','8766')
    def metadata_call(operation, number):
        request = urllib.request.Request(mcp_origin+'/mcp',data=json.dumps({'jsonrpc':'2.0','id':number,'method':'tools/call','params':{'name':'workspace_context','arguments':{'operation':operation}}}).encode(),headers={'Authorization':authorization,'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(request,timeout=15) as response:
                result = json.load(response)
        except (OSError,ValueError,urllib.error.URLError):
            raise GuardFailure('MCP_METADATA_READ_FAILED') from None
        require('error' not in result and result.get('result',{}).get('isError') is not True,'MCP_METADATA_TOOL_FAILED')
        return result['result']['structuredContent']
    inventory = metadata_call('inventory',1)
    tasks = metadata_call('task_list',2)
    require(len(inventory['targets'])==1 and inventory['targets'][0]['binding_id']==BINDING,'INVENTORY_TARGET_CHANGED')
    target = inventory['targets'][0]
    fields = lambda row,keys:{k:row.get(k) for k in keys}
    nodes = [r for r in overview['nodes'] if r['device_id']==DEVICE]
    require(len(nodes)==1,'NODE_NOT_UNIQUE')
    node = nodes[0]
    age = observed-node['last_seen_at_ms']
    require(0<=age<60000 and node['readiness']=='ready' and target['presence_state']=='online','FINAL_NODE_NOT_ONLINE_READY')
    with sqlite3.connect(Path(values['CONTROL_PLANE_DB']).as_uri()+'?mode=ro',uri=True,timeout=5) as connection:
        connection.row_factory=sqlite3.Row
        task = connection.execute('SELECT task_id,binding_id,created_at_ms,expires_at_ms,closed_at_ms,close_reason FROM mcp_task_sessions WHERE task_id=?',(TASK,)).fetchone()
        require(task is not None and task['closed_at_ms'] is not None,'TASK_NOT_CLOSED')
        writer = [dict(r) for r in connection.execute('SELECT task_id,lease_generation,expires_at_ms,released_at_ms,release_reason FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_generation',(TASK,))]
        require(all(r['released_at_ms'] is not None for r in writer),'WRITER_LEASE_NOT_RELEASED')
    emit('final_server_read_only_census',ok=True,observed_at_ms=observed,remote_mutation=False,
         metadata_operations=['inventory','task_list'],health=health,service_pid=service_pid(),release_verification=verification,
         state=state,binding_id=BINDING,context_id=CONTEXT,pilot_id=PILOT,authority_expires_at_ms=EXPIRY,
         authority_remaining_ms=EXPIRY-observed,inventory_contract=inventory['tool_contract'],
         inventory_target=fields(target,('binding_id','presence_state','readiness','dispatch_state','policy_state','capabilities')),
         node=fields(node,('device_id','readiness','policy_state','policy_reason','policy_expires_at_ms','last_seen_at_ms','activation_epoch')),
         heartbeat_age_ms=age,task=dict(task),writer_leases=writer,
         action={**fields(action,('action_id','task_id','tool_name','delivery_state','settled_at_ms')),'attempt_count':len(action['attempts']),'receipts':receipts},
         exec_canary_passed=False,exec_failure_classification='SANDBOX_STATE_PHASE_FAILED_NATIVE_SPAWN_FAILED_NO_EXIT_CODE',
         original_unknown_preserved=True,historical_family_preserved=True)
except Exception as error:
    emit('final_server_census_failed',ok=False,code=error.code if isinstance(error,GuardFailure) else 'FINAL_SERVER_CENSUS_FAILED',remote_mutation=False)
    raise SystemExit(2) from None
