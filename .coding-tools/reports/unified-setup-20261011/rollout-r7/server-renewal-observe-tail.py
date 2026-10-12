"""Read-only post-renewal exact scope and state verification."""
try:
    values = parse_environment(protected_file(ENV_FILE))
    token = values['CONTROL_PLANE_OPERATOR_TOKEN']
    bind = values.get('CONTROL_PLANE_BIND', '127.0.0.1')
    if bind in {'0.0.0.0', '::'}:
        bind = '127.0.0.1'
    origin = 'http://' + bind + ':' + values.get('CONTROL_PLANE_PORT', '8765')
    verify_release(CURRENT.resolve(strict=True), REVISION, PACKAGE)
    health = verify_health(origin, token, REVISION, PACKAGE)
    state = require_quiescent(Path(values['CONTROL_PLANE_DB']))
    require(state['actions'] == 32 and state['tasks'] == 6 and state['acceptances'] == 1
            and state['open_tasks'] == 0
            and state['historical_action_families_sha256'] == '825c437a6f420df0221f01bf74685c4fe3caf46268a62506497942aff9d52aed',
            'ACTION_TASK_OR_HISTORICAL_STATE_CHANGED')
    overview = json_request(origin, token, '/v1/ui/overview')
    now = overview['observed_at_ms']
    contexts = [r for r in overview['contexts'] if r['binding_id'] == 'bind_3e05bf64cb3e4bab93d930ae1692bebb' and r['closed_at_ms'] is None and r['expires_at_ms'] > now]
    pilots = [r for r in overview['scoped_pilot_decisions'] if r['revoked_at_ms'] is None and r['expires_at_ms'] > now]
    require(len(contexts) == 1 and contexts[0]['context_id'] == 'ctx_01ca575dd5fa46cc95432e8f5aa56848'
            and contexts[0]['expires_at_ms'] == 1791717633341, 'EXACT_CONTEXT_CHANGED')
    require(len(pilots) == 1 and pilots[0]['decision_id'] == 'pilot_39a7fb99d6f7475db1e553383c3f3e2e'
            and pilots[0]['binding_id'] == contexts[0]['binding_id'] and pilots[0]['expires_at_ms'] == 1791717633341,
            'EXACT_PILOT_CHANGED')
    require(health['admission_mode'] == 'scoped_pilot', 'ADMISSION_CHANGED')
    emit('renewal_fresh_observation', ok=True, observed_at_ms=now, health=health, state=state,
         binding_id=contexts[0]['binding_id'], context_id=contexts[0]['context_id'],
         pilot_id=pilots[0]['decision_id'], expires_at_ms=1791717633341, remote_mutation=False)
except Exception as error:
    emit('renewal_fresh_observation_failed', ok=False, code=error.code if isinstance(error, GuardFailure) else 'OBSERVATION_FAILED')
    raise SystemExit(2) from None
