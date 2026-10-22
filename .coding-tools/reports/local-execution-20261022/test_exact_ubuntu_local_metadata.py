"""Offline transition tests; never contact systemd, a network or Ubuntu."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / '.coding-tools/reports/parallel-native-first-20261012/codex-control-plane-parallel-native-1012-f7acd9ec4ba1'
SCRIPT = HERE / 'activate-exact-ubuntu-local-metadata.py'


class Current:
    def __init__(self, path, target):
        self.path, self.target = path, target
    def is_symlink(self):
        return True
    def resolve(self):
        return self.target
    def __truediv__(self, other):
        return self.path / other
    def __fspath__(self):
        return str(self.path)


class TransitionTests(unittest.TestCase):
    def setUp(self):
        fake_fcntl = types.SimpleNamespace(LOCK_EX=1, LOCK_NB=2, LOCK_UN=4, flock=lambda *args: None)
        fake_pwd = types.SimpleNamespace(getpwuid=lambda uid: types.SimpleNamespace(pw_name='svhome'))
        with patch.dict(sys.modules, {'fcntl': fake_fcntl, 'pwd': fake_pwd}):
            spec = importlib.util.spec_from_file_location('exact_update_fixture', SCRIPT)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix='ubuntu-metadata-fixture-')
        self.addCleanup(self.temp.cleanup)
        m = self.module
        m.HOME = Path(self.temp.name)
        m.INSTALL = m.HOME / '.local/lib/codex-control-plane'
        m.RELEASES = m.INSTALL / 'releases'
        m.RELEASES.mkdir(parents=True)
        m.BASELINE = m.RELEASES / BASE.name
        shutil.copytree(BASE, m.BASELINE)
        m.CURRENT = Current(m.INSTALL / 'current', m.BASELINE)
        m.ENV = m.HOME / '.config/codex-control-plane/control-plane.env'
        m.DROP = m.HOME / '.config/systemd/user/codex-control-plane.service.d/10-immutable-release.conf'
        m.ENV.parent.mkdir(parents=True)
        m.DROP.parent.mkdir(parents=True)
        m.ENV.write_text('CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=' + m.BASE_PACKAGE + '\nUNRELATED=preserved\n')
        m.DROP.write_text('[Service]\nEnvironment=CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256=' + m.BASE_PACKAGE + '\n')
        self.original_configs = {p: p.read_bytes() for p in (m.ENV, m.DROP)}
        authorization = m.HOME / '.config/codex-control-plane/ubuntu-root-mcp-authorization'
        authorization.write_text('mcpsvc_' + 'x' * 32)
        self.database = m.HOME / 'control-plane.sqlite3'
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            connection.executescript('''
                PRAGMA user_version=29;
                CREATE TABLE nodes(device_id,endpoint_id,owner_id,display_name,credential_hash,credential_created_at_ms,credential_generation,revoked_at_ms);
                CREATE TABLE events(event_id,event_type);
                CREATE TABLE actions(action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,expires_at_ms,settled_at_ms);
                CREATE TABLE action_reconciliations(action_id,disposition);
                CREATE TABLE mcp_exec_intents(action_id);
                CREATE TABLE mcp_task_sessions(task_id,expires_at_ms,closed_at_ms);
                CREATE TABLE mcp_task_writer_leases(lease_id,expires_at_ms,released_at_ms);
                CREATE TABLE control_plane_state(state_key,state_value);
                INSERT INTO control_plane_state VALUES('admission_mode','scoped_pilot');
                CREATE TABLE scoped_pilot_decisions(decision_id,owner_id,revoked_at_ms,expires_at_ms);
                INSERT INTO scoped_pilot_decisions VALUES('pilot1','owner1',NULL,9999999999999);
                CREATE TABLE mcp_service_grants(grant_id,revoked_at_ms);
                INSERT INTO mcp_service_grants VALUES('grant1',NULL);
                CREATE TABLE mcp_access_grants(grant_id);
                CREATE TABLE oauth_principals(principal_id);
                INSERT INTO oauth_principals VALUES('principal1');
                CREATE TABLE bindings(binding_id);
                INSERT INTO bindings VALUES('binding1');
                CREATE TABLE node_workspaces(workspace_id);
                INSERT INTO node_workspaces VALUES('workspace1');
            ''')
        self.active, self.pid, self.started = True, m.EXPECTED_PID, False
        self.commands = []
        self.timer_state = {name + '.timer': 'active' for name in m.AUX}
        self.fail_poststart = False
        self.race = False
        self.restore_failure = None
        self.stop_timer_failure = None
        self.new_settings_drift = False
        self.actual_observe = m.observe

        def properties(unit):
            if unit == m.SERVICE:
                return {'ActiveState': 'active' if self.active else 'inactive',
                        'MainPID': str(self.pid), 'ControlGroup': '/fixture/service',
                        'ExecStart': str(m.CURRENT / 'deploy/control-plane-launcher.sh')}
            return {'ActiveState': self.timer_state.get(unit, 'inactive'), 'MainPID': '0'}

        def run(*arguments):
            self.commands.append(arguments)
            verb, unit = arguments[0], arguments[1] if len(arguments) > 1 else None
            if unit in self.timer_state:
                self.timer_state[unit] = 'inactive' if verb == 'stop' else 'active'
                if verb == 'stop' and unit == self.stop_timer_failure:
                    raise RuntimeError('FIXTURE_TIMER_STOP_FAILED_AFTER_STOP')
                if verb == 'start' and unit == self.restore_failure:
                    raise RuntimeError('FIXTURE_TIMER_RESTORE_FAILED')
            elif unit == m.SERVICE:
                if verb == 'stop':
                    self.active, self.pid = False, 0
                    if self.race:
                        with contextlib.closing(sqlite3.connect(self.database)) as connection:
                            connection.execute("INSERT INTO events VALUES('race','action_sealed')")
                            connection.commit()
                elif verb == 'start':
                    self.active, self.pid, self.started = True, m.EXPECTED_PID + 1, True
            return ''

        def observe(environment, package, authorization):
            if self.started and self.fail_poststart:
                raise RuntimeError('FIXTURE_POSTSTART_FAILED')
            return {'service_instance_id': 'new' if self.started else 'old', 'binding_ids': ['binding1']}, []

        def stopped(cgroup, listeners):
            m.require(not self.active and self.pid == 0, 'FIXTURE_SERVICE_NOT_STOPPED')

        m.properties, m.run, m.observe, m.stopped = properties, run, observe, stopped
        m.private = lambda path: (path.read_bytes(), 0o600)
        m.switch = lambda target: setattr(m.CURRENT, 'target', Path(target))
        # Linux's process environment is represented explicitly in this Windows fixture.
        real_read = Path.read_text
        def read_text(path, *args, **kwargs):
            if path.as_posix().startswith('/proc/') and path.name == 'environ':
                new = str(self.pid) in str(path) and self.started
                target = m.CURRENT.resolve() if new else m.BASELINE
                fields = {'PYTHONPATH': str(target / 'control-plane'),
                          'CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256': m.NEW_PACKAGE if new else m.BASE_PACKAGE,
                          'CONTROL_PLANE_DB': str(self.database)}
                if new:
                    fields['CONTROL_PLANE_DECLARED_SOURCE_REVISION'] = json.loads((target / 'release-manifest.json').read_bytes())['source_revision']
                    if self.new_settings_drift:
                        fields['CONTROL_PLANE_UNRELATED_SETTING'] = 'changed'
                return '\0'.join(key + '=' + value for key, value in fields.items())
            return real_read(path, *args, **kwargs)
        self.patches = [patch.object(Path, 'home', return_value=m.HOME), patch.object(Path, 'read_text', read_text),
                        patch.object(os, 'readlink', lambda path: str(m.BASELINE)),
                        patch.object(os, 'getuid', lambda: 1000, create=True)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def invoke(self, execute=True):
        output = io.StringIO()
        with patch.object(sys, 'argv', [str(SCRIPT)] + (['--execute'] if execute else [])), contextlib.redirect_stdout(output):
            self.module.main()
        return json.loads(output.getvalue())

    def test_readonly_preflight_does_not_mutate(self):
        result = self.invoke(False)
        self.assertTrue(result['ok'])
        self.assertFalse(result['external_mutations_performed'])
        self.assertEqual(self.commands, [])
        self.assertEqual(len(list(self.module.RELEASES.iterdir())), 1)

    def test_success_exact_overlay_preserves_authority_and_timers(self):
        result = self.invoke()
        self.assertTrue(result['pilots_and_admission_unchanged'])
        self.assertTrue(result['existing_causal_rows_preserved'])
        self.assertEqual(result['admission_mode'], 'scoped_pilot')
        self.assertEqual(self.module.sha((self.module.CURRENT.resolve() / self.module.NODE).read_bytes()), self.module.NEW_NODE)
        self.assertEqual(sum(command == ('stop', self.module.SERVICE) for command in self.commands), 1)
        self.assertEqual(sum(command == ('start', self.module.SERVICE) for command in self.commands), 1)
        self.assertTrue(all(state == 'active' for state in self.timer_state.values()))
        self.assertIn(b'UNRELATED=preserved', self.module.ENV.read_bytes())

    def test_completed_action_race_aborts_and_restarts_original(self):
        self.race = True
        with self.assertRaisesRegex(RuntimeError, 'CAUSAL_STATE_CHANGED_DURING_STOP'):
            self.invoke()
        self.assertEqual(self.module.CURRENT.resolve(), self.module.BASELINE)
        self.assertTrue(self.active)
        self.assertEqual({p: p.read_bytes() for p in self.original_configs}, self.original_configs)
        self.assertTrue(all(state == 'active' for state in self.timer_state.values()))

    def test_poststart_failure_never_stops_or_rolls_back_candidate(self):
        self.fail_poststart = True
        # Make the bounded retry deadline immediate without waiting in the fixture.
        with patch.object(self.module.time, 'monotonic', side_effect=[0, 100]):
            with self.assertRaisesRegex(RuntimeError, 'POSTSTART_SOURCE_OR_MCP_NOT_PROVEN'):
                self.invoke()
        self.assertNotEqual(self.module.CURRENT.resolve(), self.module.BASELINE)
        self.assertEqual(sum(command == ('stop', self.module.SERVICE) for command in self.commands), 1)
        self.assertTrue(self.active)

    def test_timer_stop_partial_failure_restores_timer(self):
        self.stop_timer_failure = next(iter(self.timer_state))
        with self.assertRaisesRegex(RuntimeError, 'FIXTURE_TIMER_STOP_FAILED_AFTER_STOP'):
            self.invoke()
        self.assertEqual(self.timer_state[self.stop_timer_failure], 'active')
        self.assertNotIn(('stop', self.module.SERVICE), self.commands)

    def test_restore_failure_still_attempts_every_timer(self):
        self.race = True
        self.restore_failure = next(iter(self.timer_state))
        with self.assertRaisesRegex(RuntimeError, 'TIMER_RESTORATION_FAILED'):
            self.invoke()
        for timer in self.timer_state:
            self.assertIn(('start', timer), self.commands)

    def test_unrelated_new_process_settings_are_rejected_without_rollback(self):
        self.new_settings_drift = True
        with self.assertRaisesRegex(RuntimeError, 'UNRELATED_SERVICE_SETTINGS_CHANGED'):
            self.invoke()
        self.assertNotEqual(self.module.CURRENT.resolve(), self.module.BASELINE)
        self.assertEqual(sum(command == ('stop', self.module.SERVICE) for command in self.commands), 1)

    def test_unquarantined_unknown_blocks_before_any_service_change(self):
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            connection.execute("INSERT INTO actions VALUES('uncertain','node','workspace','generation','exec_command','reconcile_required',1,NULL)")
            connection.commit()
        with self.assertRaisesRegex(RuntimeError, 'UNRESOLVED_WORK_BLOCKS_UPDATE'):
            self.invoke()
        self.assertEqual(self.commands, [])

    def test_extra_release_file_is_diagnosed_before_mutation(self):
        path = self.module.BASELINE / '__pycache__/fixture.pyc'
        path.parent.mkdir()
        path.write_bytes(b'fixture extra file')
        with self.assertRaises(self.module.ReleaseCheckFailure) as failure:
            self.invoke()
        self.assertEqual(str(failure.exception), 'RELEASE_VERIFY_RELEASE_FILE_SET_DOES_NOT_MATCH_MANIFEST')
        self.assertEqual(failure.exception.issues, [{'issue': 'EXTRA_FILE', 'path': '__pycache__/fixture.pyc'}])
        self.assertEqual(self.commands, [])

    def test_changed_verifier_is_not_imported(self):
        path = self.module.BASELINE / 'deploy/control-plane-verify-release.py'
        path.write_text("raise AssertionError('this verifier must not run')")
        with self.assertRaisesRegex(RuntimeError, 'BASELINE_VERIFIER_CHANGED'):
            self.invoke()
        self.assertEqual(self.commands, [])

    def test_exact_confirmed_cache_pair_is_preserved_and_excluded_only_from_candidate(self):
        m = self.module
        for relative in m.CONFIRMED_GENERATED_CACHES:
            path = m.BASELINE / relative
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'observed generated bytecode fixture')
        readonly = self.invoke(False)
        self.assertEqual(readonly['confirmed_baseline_caches_preserved_and_excluded_from_candidate'], sorted(m.CONFIRMED_GENERATED_CACHES))
        self.assertEqual(self.commands, [])
        self.assertEqual(len(list(m.RELEASES.iterdir())), 1)
        result = self.invoke()
        self.assertTrue(result['ok'])
        for relative in m.CONFIRMED_GENERATED_CACHES:
            self.assertEqual((m.BASELINE / relative).read_bytes(), b'observed generated bytecode fixture')
            self.assertFalse((m.CURRENT.resolve() / relative).exists())

    def test_third_extra_cache_is_denied_without_mutation(self):
        m = self.module
        for relative in m.CONFIRMED_GENERATED_CACHES | {'control-plane/control_plane/__pycache__/node_agent.cpython-314.pyc'}:
            path = m.BASELINE / relative
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'generated bytecode fixture')
        with self.assertRaises(m.ReleaseCheckFailure) as failure:
            self.invoke()
        self.assertEqual(str(failure.exception), 'RELEASE_VERIFY_RELEASE_FILE_SET_DOES_NOT_MATCH_MANIFEST')
        self.assertEqual(self.commands, [])
        self.assertEqual(len(list(m.RELEASES.iterdir())), 1)

    def test_listening_socket_inodes_prove_exact_systemd_process(self):
        m = self.module
        listing = 'header\n 0: 0100007F:223D 00000000:0000 0A 0 0 0 0 0 111\n 1: 0100007F:223E 00000000:0000 0A 0 0 0 0 0 222\n'
        with patch.object(Path, 'iterdir', return_value=[Path('fd3'), Path('fd4')]), patch.object(Path, 'read_text', return_value=listing), patch.object(os, 'readlink', side_effect=['socket:[111]', 'socket:[222]']):
            m.prove_listener_ownership(970133, [('127.0.0.1', 8765), ('127.0.0.1', 8766)])

    def test_other_process_listener_is_rejected(self):
        m = self.module
        listing = 'header\n 0: 0100007F:223D 00000000:0000 0A 0 0 0 0 0 111\n 1: 0100007F:223E 00000000:0000 0A 0 0 0 0 0 222\n'
        with patch.object(Path, 'iterdir', return_value=[Path('fd3')]), patch.object(Path, 'read_text', return_value=listing), patch.object(os, 'readlink', return_value='socket:[111]'):
            with self.assertRaisesRegex(RuntimeError, 'SYSTEMD_PID_DOES_NOT_OWN_LISTENER'):
                m.prove_listener_ownership(970133, [('127.0.0.1', 8765), ('127.0.0.1', 8766)])

    def test_actual_baseline_health_without_pid_uses_os_listener_proof(self):
        m = self.module
        health = {'ok': True, 'schema_version': 29, 'package_source_sha256': m.BASE_PACKAGE,
                  'expected_package_source_sha256': m.BASE_PACKAGE, 'service_instance_id': 'cp_fixture'}
        inventory = {'result': {'structuredContent': {'tool_contract': m.CONTRACT,
                     'workspace_accessed': False, 'targets': [{'binding_id': 'binding1'}]}}}
        with patch.object(m, 'json_http', side_effect=[health, inventory]), patch.object(m, 'prove_listener_ownership') as proof:
            result, addresses = self.actual_observe({}, m.BASE_PACKAGE, b'mcpsvc_' + b'x' * 32)
        self.assertEqual(result['service_instance_id'], 'cp_fixture')
        self.assertEqual(addresses, [('127.0.0.1', 8765), ('127.0.0.1', 8766)])
        proof.assert_called_once_with(m.EXPECTED_PID, addresses)


if __name__ == '__main__':
    unittest.main()
