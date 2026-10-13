"""Offline checks for the deployment's exact historical exception and fence."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
TREE = ast.parse((HERE / 'deploy-server-candidate.py').read_text(encoding='utf-8'))
NAMES = {'require', 'sha', 'connect', 'digest_rows', 'census', 'same_state'}
NAMESPACE = dict(hashlib=hashlib, json=json, Path=Path, re=re, sqlite3=sqlite3, time=time, DEVICE='device')
exec(compile(ast.Module(body=[node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in NAMES], type_ignores=[]), 'deployment-boundary-functions', 'exec'), NAMESPACE)

class DeploymentBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / 'state.sqlite3'
        connection = sqlite3.connect(self.database)
        connection.executescript('''
            PRAGMA user_version=29;
            CREATE TABLE control_plane_state(state_key,state_value,changed_at_ms);
            INSERT INTO control_plane_state VALUES('admission_mode','scoped_pilot',1);
            CREATE TABLE mcp_task_sessions(task_id,closed_at_ms,expires_at_ms);
            CREATE TABLE mcp_task_writer_leases(task_id,released_at_ms,expires_at_ms);
            CREATE TABLE actions(action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,expires_at_ms,settled_at_ms,created_at_ms);
            INSERT INTO actions VALUES('unknown','device','workspace','generation','workspace_context','reconcile_required',1,NULL,1);
            INSERT INTO actions VALUES('history','other','old','generation','workspace_context','dispatch_unconfirmed',1,NULL,2);
            CREATE TABLE action_reconciliations(action_id,disposition);
            INSERT INTO action_reconciliations VALUES('unknown','quarantined_unknown');
            CREATE TABLE action_dispatch_dispositions(action_id,disposition);
            CREATE TABLE delivery_attempts(action_id,attempt_id);
            CREATE TABLE receipts(action_id,receipt_id);
            CREATE TABLE bindings(binding_id);
            CREATE TABLE node_workspaces(workspace_id);
            CREATE TABLE scoped_pilot_decisions(decision_id,owner_id,principal_id,binding_id,device_id,endpoint_id,workspace_id,workspace_generation,created_at_ms,revoked_at_ms);
            CREATE TABLE mcp_service_grants(grant_id,expires_at_ms);
            CREATE TABLE oauth_principals(principal_id);
        ''')
        for table in ('mcp_read_only_intents', 'mcp_file_read_intents', 'mcp_approved_patch_intents', 'mcp_standing_patch_intents', 'mcp_exec_intents', 'mcp_artifact_intents', 'mcp_document_write_intents'):
            connection.execute('CREATE TABLE ' + table + '(action_id)')
        connection.execute("INSERT INTO mcp_read_only_intents VALUES('history')")
        connection.commit()
        connection.row_factory = sqlite3.Row
        self.approved = {'expected_unknown_actions': [dict(connection.execute("SELECT a.action_id,a.workspace_id,a.workspace_generation,a.delivery_state,a.expires_at_ms,r.disposition FROM actions a LEFT JOIN action_reconciliations r ON r.action_id=a.action_id WHERE a.action_id='unknown'").fetchone())],
            'expected_historical_dispatch_actions': [dict(connection.execute("SELECT action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,expires_at_ms,settled_at_ms FROM actions WHERE action_id='history'").fetchone())]}
        connection.close()

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, sql):
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(sql)
            connection.commit()
        finally:
            connection.close()

    def census(self, **kw):
        return NAMESPACE['census'](self.database, self.approved, **kw)

    def test_only_exact_expired_compact_metadata_is_history(self):
        before = self.database.read_bytes()
        result = self.census()
        self.assertEqual(result['active_actions'], 0)
        self.assertEqual(result['historical_unknown_count'], 1)
        self.assertEqual(self.database.read_bytes(), before)
        self.mutate("INSERT INTO actions VALUES('new','other','old','generation','workspace_context','dispatch_unconfirmed',1,NULL,3)")
        with self.assertRaisesRegex(RuntimeError, 'LIVE_WORK_BLOCKS_SERVICE_TRANSITION'):
            self.census()

    def test_exec_intent_never_qualifies_as_compact_metadata(self):
        self.mutate("INSERT INTO mcp_exec_intents VALUES('history')")
        with self.assertRaisesRegex(RuntimeError, 'HISTORICAL_DISPATCH_HAS_EFFECTFUL_INTENT'):
            self.census()

    def test_fenced_census_requires_recovery_and_preserves_history(self):
        before = self.census()
        self.mutate("UPDATE control_plane_state SET state_value='recovery',changed_at_ms=2")
        with self.assertRaisesRegex(RuntimeError, 'ADMISSION_CHANGED'):
            self.census()
        after = self.census(admission_mode='recovery')
        self.assertTrue(NAMESPACE['same_state'](before, after, fence_change=True))
        self.mutate("UPDATE actions SET expires_at_ms=2 WHERE action_id='unknown'")
        with self.assertRaisesRegex(RuntimeError, 'UNRESOLVED_HISTORY_SET_CHANGED'):
            self.census(admission_mode='recovery')

if __name__ == '__main__':
    unittest.main()
