"""Prepare or close the exact reviewed idle broker once; never claim VM ownership."""
import argparse
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(r"E:\DEV\Codex-web")
HERE = Path(__file__).resolve().parent
HELPER = HERE / "observe-original-owned-stop-readonly.py"
HELPER_SHA = "8ab29b114c2184e1a4696647e477c502ee91b3ee6b38469a85ff615e15f07168"
ATTRIBUTION = HERE / "diagnostic-wsb-cli-server-attribution-evidence.json"
ATTRIBUTION_SHA = "c662f981239698bdc8516910018fe4498a7135542b45fdf789f2475bd3afa1af"
CATALOG_POWERSHELL = Path(r"C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe")
TERMINATE_ATTEMPTED = False
UNKNOWN_PATH = None


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_helpers():
    require(sha(HELPER) == HELPER_SHA, "EXACT_REVIEWED_READONLY_HELPER_CHANGED")
    spec = importlib.util.spec_from_file_location("reviewed_idle_broker_observation", HELPER)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    require(observer.m.file_sha(observer.SOURCE) == observer.REVIEWED_SOURCE_SHA,
            "EXACT_ORIGINAL_STOP_HELPER_CHANGED")
    return observer


def attributed_broker(expected_image):
    require(sha(ATTRIBUTION) == ATTRIBUTION_SHA, "REVIEWED_DIAGNOSTIC_ATTRIBUTION_CHANGED")
    report = json.loads(ATTRIBUTION.read_text(encoding="utf-8-sig"))
    process = report["subsequent_live_process"]
    require(report["operation"] == "diagnostic_wsb_list_parent_attribution_readonly_evidence"
            and process["pid"] == 27568 and process["parent_pid"] == 3724
            and os.path.normcase(process["executable_path"]) == os.path.normcase(str(expected_image))
            and report["known_diagnostic_invocation"]["reported_environment_count"] == 0
            and report["known_diagnostic_invocation"]["count_by_local_checks"] == 1,
            "EXACT_IDENTIFIED_DIAGNOSTIC_BROKER_REQUIRED")
    captured = datetime.fromisoformat(process["created_at_utc"]).replace(tzinfo=timezone.utc)
    delta = captured - datetime(1601, 1, 1, tzinfo=timezone.utc)
    token = (delta.days * 86400 + delta.seconds) * 10000000 + delta.microseconds * 10
    return {"evidence_sha256": ATTRIBUTION_SHA, "prior_microsecond_creation_filetime": str(token),
            "parent_cli_pid": 3724, "per_tool_call_child_pid_capture": False,
            "strongest_claim": "exact live server matches reviewed AppCli parent correlation"}


def win32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    a = ctypes.WinDLL("advapi32", use_last_error=True)
    k.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k.OpenProcess.restype = wintypes.HANDLE
    k.GetCurrentProcess.restype = wintypes.HANDLE
    k.GetCurrentProcessId.restype = wintypes.DWORD
    k.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
                                 ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                 ctypes.POINTER(wintypes.FILETIME))
    k.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                          ctypes.POINTER(wintypes.DWORD))
    k.ProcessIdToSessionId.argtypes = (wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    k.CloseHandle.argtypes = (wintypes.HANDLE,)
    k.LocalFree.argtypes = (ctypes.c_void_p,)
    k.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
    k.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k.WaitForSingleObject.restype = wintypes.DWORD
    a.OpenProcessToken.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE))
    a.GetTokenInformation.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                     wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    a.ConvertSidToStringSidW.argtypes = (ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR))
    return k, a


def sid(k, a, process):
    token = wintypes.HANDLE()
    require(a.OpenProcessToken(process, 0x8, ctypes.byref(token)), "PROCESS_OWNER_TOKEN_UNAVAILABLE")
    try:
        size = wintypes.DWORD()
        a.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        require(0 < size.value <= 65536, "PROCESS_OWNER_TOKEN_INVALID")
        buffer = ctypes.create_string_buffer(size.value)
        require(a.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)),
                "PROCESS_OWNER_TOKEN_UNAVAILABLE")
        sid_pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p)).contents.value
        rendered = wintypes.LPWSTR()
        require(a.ConvertSidToStringSidW(sid_pointer, ctypes.byref(rendered)), "PROCESS_OWNER_SID_UNAVAILABLE")
        try:
            return rendered.value
        finally:
            k.LocalFree(ctypes.cast(rendered, ctypes.c_void_p))
    finally:
        k.CloseHandle(token)


def live_identity(k, a, handle, pid, expected_image):
    code = wintypes.DWORD()
    require(k.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value == 259,
            "EXACT_IDLE_BROKER_NOT_LIVE")
    created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
    require(k.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                              ctypes.byref(kernel), ctypes.byref(user)), "BROKER_CREATION_TIME_UNAVAILABLE")
    size = wintypes.DWORD(32768)
    image = ctypes.create_unicode_buffer(size.value)
    require(k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)), "BROKER_IMAGE_UNAVAILABLE")
    actual = Path(image.value).resolve(strict=True)
    require(os.path.normcase(str(actual)) == os.path.normcase(str(expected_image))
            and actual.name.lower() == "windowssandboxserver.exe", "EXACT_IDLE_BROKER_IMAGE_CHANGED")
    owner, current = sid(k, a, handle), sid(k, a, k.GetCurrentProcess())
    require(owner == current, "BROKER_NOT_OWNED_BY_CURRENT_USER")
    session, current_session = wintypes.DWORD(), wintypes.DWORD()
    require(k.ProcessIdToSessionId(pid, ctypes.byref(session))
            and k.ProcessIdToSessionId(k.GetCurrentProcessId(), ctypes.byref(current_session))
            and session.value == current_session.value, "BROKER_NOT_IN_CURRENT_USER_SESSION")
    return {"pid": pid, "exact_creation_filetime": str((created.dwHighDateTime << 32) | created.dwLowDateTime),
            "executable_path": str(actual), "owner_sid": owner, "current_user_sid": current,
            "session_id": session.value, "same_current_user_and_session": True,
            "termination_handle_identity_verified": True}


def powershell_json(script, code, *, executable=None):
    chosen = str(executable) if executable is not None else "powershell.exe"
    result = subprocess.run([chosen, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=15,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(result.returncode == 0 and len(result.stdout) <= 8192, code)
    return json.loads(result.stdout)


def catalog_membership(catalog, image):
    """Observe exact SHA256 SIP membership in the installed catalog, read-only."""
    trust = ctypes.WinDLL("wintrust", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    trust.CryptCATOpen.argtypes = (wintypes.LPWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD)
    trust.CryptCATOpen.restype = wintypes.HANDLE
    trust.CryptCATClose.argtypes = (wintypes.HANDLE,)
    trust.CryptCATGetMemberInfo.argtypes = (wintypes.HANDLE, wintypes.LPWSTR)
    trust.CryptCATGetMemberInfo.restype = ctypes.c_void_p
    trust.CryptCATAdminAcquireContext2.argtypes = (ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p,
                                                  wintypes.LPCWSTR, ctypes.c_void_p, wintypes.DWORD)
    trust.CryptCATAdminReleaseContext.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    trust.CryptCATAdminCalcHashFromFileHandle2.argtypes = (wintypes.HANDLE, wintypes.HANDLE,
                                                        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p, wintypes.DWORD)
    kernel.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                   wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    invalid = ctypes.c_void_p(-1).value
    cat = trust.CryptCATOpen(str(catalog), 0, None, 0, 0)
    require(cat and cat != invalid, "INSTALLED_CODE_INTEGRITY_CATALOG_UNREADABLE")
    context, file_handle = wintypes.HANDLE(), None
    try:
        require(trust.CryptCATAdminAcquireContext2(ctypes.byref(context), None, "SHA256", None, 0),
                "CODE_INTEGRITY_HASH_CONTEXT_UNAVAILABLE")
        file_handle = kernel.CreateFileW(str(image), 0x80000000, 0x7, None, 3, 0, None)
        require(file_handle and file_handle != invalid, "EXACT_BROKER_FILE_HANDLE_UNAVAILABLE")
        size = wintypes.DWORD()
        require(trust.CryptCATAdminCalcHashFromFileHandle2(context, file_handle, ctypes.byref(size), None, 0)
                and 0 < size.value <= 128, "CODE_INTEGRITY_MEMBER_HASH_UNAVAILABLE")
        buffer = ctypes.create_string_buffer(size.value)
        require(trust.CryptCATAdminCalcHashFromFileHandle2(context, file_handle, ctypes.byref(size), buffer, 0),
                "CODE_INTEGRITY_MEMBER_HASH_UNAVAILABLE")
        digest = buffer.raw[:size.value].hex().upper()
        require(trust.CryptCATGetMemberInfo(cat, digest) or trust.CryptCATGetMemberInfo(cat, digest.lower()),
                "EXACT_BROKER_NOT_IN_INSTALLED_CODE_INTEGRITY_CATALOG")
        return {"checked": True, "algorithm": "SHA256 SIP", "member_digest": digest,
                "catalog_sha256": sha(catalog), "member_present": True}
    finally:
        if file_handle and file_handle != invalid:
            kernel.CloseHandle(file_handle)
        if context:
            trust.CryptCATAdminReleaseContext(context, 0)
        trust.CryptCATClose(cat)


def signature(path):
    # Store-deployed AppX files may have no individual Authenticode signature.
    # Bind deployment trust and the installed package block map honestly.
    script = "$ErrorActionPreference='Stop'; @(Get-AppxPackage -Name MicrosoftWindows.WindowsSandbox | ForEach-Object { @{name=[string]$_.Name;package_full_name=[string]$_.PackageFullName;install_location=[string]$_.InstallLocation;status=[string]$_.Status;signature_kind=[string]$_.SignatureKind;publisher=[string]$_.Publisher} })|ConvertTo-Json -Compress"
    packages = powershell_json(script, "BROKER_PACKAGE_TRUST_OBSERVATION_FAILED")
    if isinstance(packages, dict):
        packages = [packages]
    require(isinstance(packages, list), "INSTALLED_BROKER_PACKAGE_INVALID")
    matches = [row for row in packages if os.path.normcase(row["install_location"]) == os.path.normcase(str(path.parent))]
    require(len(matches) == 1, "EXACT_INSTALLED_BROKER_PACKAGE_REQUIRED")
    package = matches[0]
    require(package["name"] == "MicrosoftWindows.WindowsSandbox"
            and package["package_full_name"] == path.parent.name
            and package["status"] == "Ok" and package["signature_kind"] == "Store"
            and "O=Microsoft Corporation" in package["publisher"], "MICROSOFT_STORE_DEPLOYMENT_TRUST_REQUIRED")
    blockmap, manifest = path.parent / "AppxBlockMap.xml", path.parent / "AppxManifest.xml"
    tree = ET.parse(blockmap).getroot()
    require(tree.attrib.get("HashMethod") == "http://www.w3.org/2001/04/xmlenc#sha256",
            "INSTALLED_APPX_BLOCKMAP_HASH_ALGORITHM_UNSUPPORTED")
    files = [item for item in tree if item.tag.rsplit("}", 1)[-1] == "File"
             and item.attrib.get("Name", "").casefold() == path.name.casefold()]
    require(len(files) == 1 and int(files[0].attrib["Size"]) == path.stat().st_size,
            "EXACT_BROKER_BLOCKMAP_SIZE_OR_MEMBER_INVALID")
    blocks = [item for item in files[0] if item.tag.rsplit("}", 1)[-1] == "Block"]
    require(len(blocks) == (path.stat().st_size + 65535) // 65536, "EXACT_BROKER_BLOCKMAP_BLOCK_COUNT_INVALID")
    with path.open("rb") as source:
        for block in blocks:
            payload = source.read(65536)
            require(base64.b64decode(block.attrib["Hash"], validate=True) == hashlib.sha256(payload).digest(),
                    "EXACT_BROKER_INSTALLED_BLOCKMAP_HASH_MISMATCH")
        require(source.read(1) == b"", "BROKER_FILE_CHANGED_DURING_BLOCKMAP_VERIFICATION")
    identity = ET.parse(manifest).getroot().find("{*}Identity")
    require(identity is not None and identity.attrib["Name"] == package["name"]
            and identity.attrib["Publisher"] == package["publisher"], "EXACT_DEPLOYED_MANIFEST_IDENTITY_CHANGED")
    catalog = path.parent / "AppxMetadata/CodeIntegrity.cat"
    catalog_proof = {"present": False, "membership_checked": False}
    if catalog.exists():
        escaped = str(catalog).replace("'", "''")
        # This host's WindowsPowerShell5 Security module fails to autoload with
        # FormatXmlUpdateException. Use the existing exact Codex runtime pwsh7
        # where the same read-only certificate command was verified to succeed.
        require(CATALOG_POWERSHELL.is_file(), "EXACT_CATALOG_OBSERVER_RUNTIME_UNAVAILABLE")
        cat_signature = powershell_json("$ErrorActionPreference='Stop'; $s=Get-AuthenticodeSignature -FilePath '" + escaped + "'; @{status=[string]$s.Status;subject=[string]$s.SignerCertificate.Subject;thumbprint=[string]$s.SignerCertificate.Thumbprint}|ConvertTo-Json -Compress", "INSTALLED_CATALOG_SIGNATURE_OBSERVATION_FAILED", executable=CATALOG_POWERSHELL)
        require(cat_signature["status"] == "Valid" and "O=Microsoft Corporation" in cat_signature["subject"],
                "MICROSOFT_INSTALLED_CATALOG_SIGNATURE_REQUIRED")
        catalog_proof = {"present": True, "signature": cat_signature,
                         "signature_observer_path": str(CATALOG_POWERSHELL),
                         "signature_observer_sha256": sha(CATALOG_POWERSHELL),
                         **catalog_membership(catalog, path)}
    return {"trust_kind": "Microsoft Store installed AppX deployment plus exact installed block map",
            "individual_executable_authenticode_claimed": False, "package": package,
            "blockmap_sha256": sha(blockmap), "manifest_sha256": sha(manifest),
            "broker_blocks_verified": len(blocks), "executable_sha256": sha(path),
            "code_integrity_catalog": catalog_proof}


def original_binding(observer, cli):
    m = observer.m
    dispatch = observer.evidence(cli.dispatch, cli.dispatch_sha256)
    plan = observer.evidence(cli.plan, cli.plan_sha256)
    unknown = observer.evidence(cli.unknown, cli.unknown_sha256)
    require(dispatch["operation"] == "dispatch_owned_sandbox_supported_stop"
            and dispatch["producer_sha256"] == observer.REVIEWED_SOURCE_SHA
            and dispatch["reviewed_plan_sha256"] == cli.plan_sha256 and dispatch["effect_state"] == "dispatching"
            and plan["operation"] == "prepare_owned_sandbox_supported_stop"
            and plan["producer_sha256"] == observer.REVIEWED_SOURCE_SHA and plan["stop_dispatched"] is False
            and dispatch["binding"] == plan["binding"]
            and dispatch["binding_sha256"] == plan["binding_sha256"] == m.digest(plan["binding"]),
            "EXACT_ORIGINAL_SUPPORTED_STOP_DISPATCH_REQUIRED")
    bound = plan["binding"]
    attempt = bound["stop_attempt_id"]
    require(cli.dispatch.name == "owned-stop-dispatch-" + attempt + ".json"
            and cli.plan.name == "owned-stop-plan-" + attempt + ".json"
            and cli.unknown.name == "owned-stop-unknown-" + attempt + ".json"
            and unknown == {"operation": "owned_sandbox_supported_stop", "ok": False,
                "code": "SUPPORTED_STOP_VM_SHUTDOWN_NOT_CONFIRMED", "stop_invocation_attempted": True,
                "effect_state": "unknown_requires_original_observation", "automatic_retry_permitted": False,
                "nonce_saved": False}, "EXACT_ORIGINAL_STOP_UNKNOWN_REQUIRED")
    return bound


def boundary(observer, cli, bound):
    m = observer.m
    package, runtime, warm = (bound[key] for key in ("package", "runtime", "warm_receipt"))
    args = SimpleNamespace(candidate=Path(package["candidate"]), package_proof=cli.package_proof,
        package_proof_sha256=package["package_manifest_sha256"], activation_epoch=runtime["activation_epoch"],
        process_instance_id=runtime["process_instance_id"], server_instance_id=runtime["server_instance_id"],
        native_pid=runtime["native_process"]["pid"],
        native_process_start_token=runtime["native_process"]["supported_native_process_start_token"],
        warm_receipt=Path(warm["path"]), warm_receipt_sha256=warm["sha256"], canary_task_id=warm["task_id"],
        warm_job_id=warm["job_id"], warm_action_id=warm["action_id"], service_pid=bound["central"]["service_pid"])
    require(m.package_facts(args) == package and m.runtime_facts(args, package) == runtime
            and m.warm_receipt_facts(args) == warm
            and m.native_job_facts(args, warm) == bound["native_warm_job"], "ORIGINAL_R6_RUNTIME_OR_JOB_CHANGED")
    authority = observer.central_authority(args, bound["central"], 2)
    authority["current_writer"].pop("expires_at_ms")
    backend = bound["backend"]
    base = Path(os.environ["TEMP"]).resolve() / "wxc-wsb/state-aware"
    record_path = Path(backend["record_path"])
    require(record_path.resolve() == base / backend["sandbox_id"][4:] / "record.json",
            "ORIGINAL_STOPPED_RECORD_PATH_CHANGED")
    record = m.read_json(record_path)
    require(record["sandbox_id"] == backend["sandbox_id"] and record["state"] == "stopped"
            and m.digest(record["mapped_folders"]) == backend["mapped_folders_sha256"]
            and not (base / "daemon.json").exists(), "ORIGINAL_STOPPED_MAPPING_OR_DAEMON_CHANGED")
    hosts = observer.host_inventory()
    require(hosts == {"user_mode_hosts": [{"name": "WindowsSandboxServer.exe", "pid": cli.broker_pid}],
                      "kernel_memory_observations": []}, "BROKER_NOT_EXCLUSIVE_IDLE_USER_MODE_HOST")
    # Global native quiescence and stopped records are rechecked after the
    # central/network observation, immediately before accepting this boundary.
    require(m.native_job_facts(args, warm) == bound["native_warm_job"]
            and m.runtime_facts(args, package) == runtime and m.read_json(record_path) == record
            and not (base / "daemon.json").exists(), "NATIVE_OR_STOPPED_BOUNDARY_CHANGED")
    return {"package_manifest_sha256": package["package_manifest_sha256"], "runtime": runtime,
            "native_job_count": 0, "authority": authority, "original_stop_attempt_id": bound["stop_attempt_id"],
            "original_stop_result_preserved": "UNKNOWN", "stopped_record_sha256": sha(record_path),
            "mapped_folders_sha256": backend["mapped_folders_sha256"], "daemon_record_absent": True,
            "hosts": hosts, "owned_vm_claimed": False}


def main():
    global TERMINATE_ATTEMPTED, UNKNOWN_PATH
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("dispatch", "plan", "unknown", "package-proof", "expected-image-path"):
        p.add_argument("--" + name, type=Path, required=True)
    for name in ("dispatch-sha256", "plan-sha256", "unknown-sha256", "closure-attempt-id"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--broker-pid", type=int, required=True)
    p.add_argument("--execute-reviewed-plan", type=Path)
    p.add_argument("--reviewed-plan-sha256")
    cli = p.parse_args()
    require(Path.cwd().resolve() == ROOT and os.name == "nt", "EXACT_WINDOWS_REPOSITORY_REQUIRED")
    require(cli.broker_pid == 27568 and re.fullmatch(r"[a-f0-9]{32}", cli.closure_attempt_id),
            "EXACT_IDENTIFIED_BROKER_AND_FRESH_UUID_REQUIRED")
    require(bool(cli.execute_reviewed_plan) == bool(cli.reviewed_plan_sha256), "EXACT_REVIEWED_PLAN_PAIR_REQUIRED")
    dispatch_path = HERE / ("idle-broker-closure-dispatch-" + cli.closure_attempt_id + ".json")
    UNKNOWN_PATH = HERE / ("idle-broker-closure-unknown-" + cli.closure_attempt_id + ".json")
    require(not dispatch_path.exists() and not UNKNOWN_PATH.exists(), "CLOSURE_ATTEMPT_ALREADY_USED_NO_RETRY")
    expected_image = cli.expected_image_path.resolve(strict=True)
    observer = load_helpers()
    m = observer.m
    bound = original_binding(observer, cli)
    reviewed = None
    if cli.execute_reviewed_plan:
        reviewed = observer.evidence(cli.execute_reviewed_plan, cli.reviewed_plan_sha256)
        require(reviewed["operation"] == "prepare_exact_idle_broker_closure"
                and reviewed["producer_sha256"] == sha(Path(__file__)) and reviewed["closure_dispatched"] is False
                and 0 <= int(time.time() * 1000) - reviewed["observed_at_ms"] <= 300000,
                "EXACT_FRESH_REVIEWED_CLOSURE_PLAN_REQUIRED")
    k, a = win32()
    # Keep this exact handle through identity checks and the one termination.
    # Holding the handle prevents a recycled PID from becoming the target.
    rights = 0x1000 | 0x100000 | (0x1 if reviewed else 0)
    handle = k.OpenProcess(rights, False, cli.broker_pid)
    require(bool(handle), "EXACT_BROKER_HANDLE_UNAVAILABLE")
    try:
        identity = live_identity(k, a, handle, cli.broker_pid, expected_image)
        attribution = attributed_broker(expected_image)
        captured_creation = int(identity["exact_creation_filetime"])
        require(str(captured_creation - captured_creation % 10) == attribution["prior_microsecond_creation_filetime"],
                "IDENTIFIED_DIAGNOSTIC_BROKER_CREATION_CHANGED")
        signed = signature(expected_image)
        current = boundary(observer, cli, bound)
        binding = {"closure_attempt_id": cli.closure_attempt_id, "broker": identity, "attribution": attribution,
                   "signed_image": signed, "boundary": current, "original_dispatch_sha256": cli.dispatch_sha256,
                   "original_plan_sha256": cli.plan_sha256, "original_unknown_sha256": cli.unknown_sha256}
        report = {"schema_version": 1, "operation": "prepare_exact_idle_broker_closure",
                  "observed_at_ms": int(time.time() * 1000), "producer_sha256": sha(Path(__file__)),
                  "reviewed_readonly_helper_sha256": HELPER_SHA, "closure_dispatched": False,
                  "automatic_retry_permitted": False, "owned_vm_claimed": False,
                  "authorization_scope": "user_requested_reversible_local_repair",
                  "binding": binding, "binding_sha256": m.digest(binding)}
        if reviewed is None:
            saved = m.write_new(HERE / ("idle-broker-closure-plan-" + cli.closure_attempt_id + ".json"), report)
            print(json.dumps({"operation": report["operation"], "ok": True, "closure_dispatched": False, **saved}))
            return
        require(reviewed["binding"] == binding and reviewed["binding_sha256"] == m.digest(binding),
                "EXACT_REVIEWED_IDLE_BROKER_BOUNDARY_CHANGED")
        require(signature(expected_image) == signed and boundary(observer, cli, bound) == current
                and live_identity(k, a, handle, cli.broker_pid, expected_image) == identity,
                "IDLE_BROKER_BOUNDARY_CHANGED_BEFORE_CLOSURE")
        m.write_new(dispatch_path, {**report, "operation": "dispatch_exact_idle_broker_closure",
            "reviewed_plan_sha256": cli.reviewed_plan_sha256, "effect_state": "dispatching"})
        TERMINATE_ATTEMPTED = True
        require(k.TerminateProcess(handle, 0), "EXACT_BROKER_TERMINATION_UNCONFIRMED")
        require(k.WaitForSingleObject(handle, 10000) == 0, "EXACT_BROKER_EXIT_UNCONFIRMED")
        require(observer.host_inventory() == {"user_mode_hosts": [], "kernel_memory_observations": []},
                "POST_CLOSURE_HOST_INVENTORY_CHANGED")
        report.update(operation="exact_idle_broker_closure_observed", observed_at_ms=int(time.time() * 1000),
            closure_dispatched=True, terminate_invocation_count=1, exact_handle_exit_confirmed=True,
            reviewed_plan_sha256=cli.reviewed_plan_sha256, user_mode_host_count=0, kernel_memory_count=0,
            original_stop_result_preserved="UNKNOWN", next_action="Read-only original stop supplement before next cached command")
        saved = m.write_new(HERE / ("idle-broker-closure-receipt-" + cli.closure_attempt_id + ".json"), report)
        print(json.dumps({"operation": report["operation"], "ok": True, "closure_dispatched": True, **saved}))
    finally:
        k.CloseHandle(handle)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        code = code if re.fullmatch(r"[A-Za-z0-9_]{1,128}", code) else "IDLE_BROKER_OBSERVATION_FAILED"
        failure = {"operation": "exact_idle_broker_closure", "ok": False, "code": code,
                   "terminate_invocation_attempted": TERMINATE_ATTEMPTED,
                   "effect_state": "unknown_requires_original_observation" if TERMINATE_ATTEMPTED else "not_dispatched",
                   "automatic_retry_permitted": False, "owned_vm_claimed": False}
        if TERMINATE_ATTEMPTED and UNKNOWN_PATH is not None and not UNKNOWN_PATH.exists():
            with UNKNOWN_PATH.open("x", encoding="utf-8") as output:
                json.dump(failure, output, indent=2)
                output.write("\n")
        print(json.dumps(failure))
        raise SystemExit(1)
