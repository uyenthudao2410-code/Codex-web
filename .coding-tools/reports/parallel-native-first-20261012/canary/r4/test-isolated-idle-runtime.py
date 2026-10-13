"""Offline launcher identity boundaries; no process, profile or network access."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("isolated_idle_sampler", Path(__file__).with_name("observe-isolated-idle.py"))
sampler = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"psutil": SimpleNamespace()}):
    spec.loader.exec_module(sampler)


class RuntimeIdentityTests(unittest.TestCase):
    def fixture(self):
        candidate = Path(r"E:\DEV\Codex-web\dist\reviewed-candidate\win-unpacked")
        pins = {"activation_epoch": "activation-reviewed", "supervisor_instance_id": "a" * 24,
                "process_instance_id": "independent-mcp-id", "native_pid": 50724,
                "native_process_start_token": "134362825928499830"}
        state = {"nativeActivationEpochId": pins["activation_epoch"], "nativeInstanceId": pins["supervisor_instance_id"],
                 "nativePid": pins["native_pid"], "nativeProcessStartToken": pins["native_process_start_token"],
                 "nativeModuleRoot": str(candidate / "resources/resources/coding-tools-mcp"),
                 "nativeCommand": str(candidate / "resources/resources/native-python/pythonw.exe")}
        epoch = {"current": {"activation_epoch_id": pins["activation_epoch"], "state": "READY", "admission_state": "OPEN"}}
        live = {"pid": pins["native_pid"], "creation_time": pins["native_process_start_token"],
                "executable_path": state["nativeCommand"]}
        return candidate, pins, state, epoch, live

    def observe(self, candidate, pins, state, epoch, live):
        with patch.object(sampler, "read", side_effect=[state, epoch]), patch.object(sampler, "identity", return_value=live):
            return sampler.runtime(pins, candidate)

    def test_distinct_launcher_and_mcp_identities_remain_distinct(self):
        candidate, pins, state, epoch, live = self.fixture()
        result = self.observe(candidate, pins, state, epoch, live)
        self.assertEqual(result["supervisor_instance_id"], pins["supervisor_instance_id"])
        self.assertEqual(result["reviewed_mcp_process_instance_id"], pins["process_instance_id"])
        self.assertNotEqual(result["supervisor_instance_id"], result["reviewed_mcp_process_instance_id"])

    def test_changed_launcher_nonce_cannot_pass(self):
        candidate, pins, state, epoch, live = self.fixture()
        state["nativeInstanceId"] = "b" * 24
        with self.assertRaisesRegex(RuntimeError, "EXACT_NATIVE_MODULE_CHANGED"):
            self.observe(candidate, pins, state, epoch, live)

    def test_changed_pid_or_start_token_cannot_pass(self):
        candidate, pins, state, epoch, live = self.fixture()
        for field, value in (("nativePid", 50725), ("nativeProcessStartToken", "134362825928499840")):
            changed = copy.deepcopy(state)
            changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, "EXACT_NATIVE_MODULE_CHANGED"):
                self.observe(candidate, pins, changed, epoch, live)

    def test_os_creation_token_must_match_original_launcher_token(self):
        candidate, pins, state, epoch, live = self.fixture()
        live["creation_time"] = "134362825928499840"
        with self.assertRaisesRegex(RuntimeError, "EXACT_NATIVE_PROCESS_CHANGED"):
            self.observe(candidate, pins, state, epoch, live)


if __name__ == "__main__":
    unittest.main()
