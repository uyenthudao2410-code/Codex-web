"""Read only exact canary unknown action, task and unchanged historical rows."""
import re
ACTION = 'act_2673b93c5bb3483889742dfe3055fd3d'
TASK = 'task_8982097843784d44bcc4bb0440c35141'
BINDING = 'bind_3e05bf64cb3e4bab93d930ae1692bebb'
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
    action = json_request(origin, token, '/v1/actions/' + ACTION)
    require(action.get('action_id') == ACTION and action.get('task_id') == TASK and action.get('binding_id') == BINDING and action.get('tool_name') == 'exec_command', 'EXACT_CANARY_IDENTITY_MISMATCH')
    overview = json_request(origin, token, '/v1/ui/overview')
    database = Path(values['CONTROL_PLANE_DB'])
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        families = []
        for historical_id in HISTORICAL_ACTION_IDS:
            historical = connection.execute('SELECT * FROM actions WHERE action_id=?', (historical_id,)).fetchone()
            require(historical is not None, 'HISTORICAL_ACTION_MISSING')
            family = {'action': dict(historical)}
            for table, ordering in (('delivery_attempts','attempt_number, attempt_id'),('receipts','received_at_ms, receipt_id'),('action_reconciliations','action_id'),('action_dispatch_dispositions','action_id')):
                family[table] = [dict(r) for r in connection.execute('SELECT * FROM ' + table + ' WHERE action_id=? ORDER BY ' + ordering, (historical_id,))]
            families.append(family)
        history_digest = canonical_digest(families)
        require(history_digest == '825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed', 'HISTORICAL_EVIDENCE_CHANGED')
        counts = {key:int(connection.execute(query).fetchone()[0]) for key,query in STATE_QUERIES.items()}
        task = connection.execute('SELECT * FROM mcp_task_sessions WHERE task_id=?', (TASK,)).fetchone()
        require(task is not None and task['binding_id'] == BINDING, 'TASK_IDENTITY_MISMATCH')
        writer = [dict(r) for r in connection.execute('SELECT task_id, lease_generation, acquired_at_ms,renewed_at_ms,expires_at_ms,released_at_ms,release_reason FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_generation', (TASK,))]
        nonhistorical = [{'action_id':r['action_id'],'tool_name':r['tool_name'],'delivery_state':r['delivery_state'],'settled_at_ms':r['settled_at_ms']} for r in connection.execute("SELECT action_id,tool_name,delivery_state,settled_at_ms FROM actions WHERE delivery_state!='settled' ORDER BY action_id") if r['action_id'] not in HISTORICAL_ACTION_IDS]
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
        for key in ('command_id','job_id','local_handle'):
            safe[key + '_present'] = bool(payload.get(key))
        for key in ('exit_code','duration_ms','elapsed_ms'):
            if isinstance(payload.get(key),int) and not isinstance(payload[key],bool):
                safe[key] = payload[key]
        receipts.append(safe)
    sealed = json.loads(action['arguments_json'])
    safe_sealed = {k:sealed.get(k) for k in ('schema_version','operation','operation_kind','timeout_ms','max_output_bytes','task_id','writer_lease_generation')}
    fields = lambda row, keys:{key:row.get(key) for key in keys}
    node = [r for r in overview['nodes'] if r['device_id'] == action['device_id']]
    require(len(node)==1,'NODE_NOT_UNIQUE')
    safe_action = fields(action, ('action_id','task_id','binding_id','device_id','endpoint_id','workspace_id','workspace_generation','tool_name','delivery_state','created_at_ms','expires_at_ms','settled_at_ms','writer_lease_generation'))
    safe_action.update({'sealed_arguments_sha256':hashlib.sha256(action['arguments_json'].encode()).hexdigest(),'sealed_metadata':safe_sealed,'action_ttl_ms':action['expires_at_ms']-action['created_at_ms'],'attempts':[fields(r,('attempt_id','attempt_number','dispatched_at_ms')) for r in action.get('attempts',[])],'receipts':receipts})
    emit('exact_unknown_exec_read_only_observation',ok=True,observed_at_ms=overview['observed_at_ms'],remote_mutation=False,
         health=health,release_verification=verification,state=counts,historical_action_families_sha256=history_digest,
         nonhistorical_unresolved_actions=nonhistorical,action=safe_action,
         task={k:task[k] for k in ('task_id','binding_id','created_at_ms','expires_at_ms','closed_at_ms','close_reason')},writer_leases=writer,
         node=fields(node[0],('device_id','readiness','policy_state','policy_reason','policy_expires_at_ms','last_seen_at_ms','activation_epoch')))
except Exception as error:
    emit('exact_unknown_exec_observation_failed',ok=False,code=error.code if isinstance(error,GuardFailure) else 'EXEC_UNKNOWN_OBSERVATION_FAILED',remote_mutation=False)
    raise SystemExit(2) from None
