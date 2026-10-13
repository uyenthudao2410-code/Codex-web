from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / 'run-autocad-folder-access-canary-r9.py').read_text(encoding='utf-8')
source = source.rsplit('\nif __name__ == "__main__":', 1)[0]
cleanup = r'''

def close_reconciled_original():
    args = argparse.Namespace(credential_file='/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization', credential_json_key=None)
    pid, port, connection = service_state()
    require(pid == 946413, 'ORIGINAL_CLEANUP_SERVICE_CHANGED')
    action_id = 'act_ed8982433bf347ef8c32aebc17b23d43'
    task_id = 'task_09461f4e2d3b4992811812e816a6edbc'
    action = connection.execute('SELECT settled_at_ms,delivery_state FROM actions WHERE action_id=?', (action_id,)).fetchone()
    require(action is not None and action['settled_at_ms'] is not None and action['delivery_state'] == 'settled', 'ORIGINAL_ACTION_STILL_UNRESOLVED')
    receipts = connection.execute('SELECT receipt_state FROM receipts WHERE action_id=? ORDER BY received_at_ms', (action_id,)).fetchall()
    require(len(receipts) == 2 and [row['receipt_state'] for row in receipts] == ['unknown','rejected'], 'ORIGINAL_RECEIPT_HISTORY_MISMATCH')
    task = connection.execute('SELECT * FROM mcp_task_sessions WHERE task_id=?', (task_id,)).fetchone()
    require(task is not None and task['binding_id'] == 'bind_8cd903180f3146099fea128bf55c0b4b' and task['principal_id'] == PRINCIPAL and task['workspace_id'] == WORKSPACE and task['workspace_generation'] == EXPECTED_GENERATION, 'ORIGINAL_TASK_SCOPE_CHANGED')
    client = Mcp(port, existing_credential(args, connection))
    client.call('task_control', {'operation':'writer_release','task_id':task_id,'reason':'original_create_reconciled_readonly_bootstrap_refusal'})
    client.call('workspace_context', {'operation':'task_close','task_id':task_id})
    closed = connection.execute('SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?',(task_id,)).fetchone()[0] is not None
    held = connection.execute('SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL',(task_id,)).fetchone()[0]
    require(closed and held == 0, 'ORIGINAL_CLEANUP_NOT_VERIFIED')
    emit('original_reconciled_task_closed', ok=True, service_pid=pid, task_id=task_id, original_action_id=action_id, original_unknown_preserved=True, writer_released=True, task_closed=True, database_direct_mutation=False)
    connection.close()

if __name__ == '__main__':
    try:
        close_reconciled_original()
    except Exception as error:
        emit('original_cleanup_failed', ok=False, error_code=error_code(error))
        sys.exit(1)
'''
with (root / 'close-reconciled-original-task.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(source + cleanup)
print('Prepared supported task closure; no live mutation')
