"""Create additive r9 scripts; never operate runtime, supervisor or shortcuts."""
from pathlib import Path
import hashlib
import json

root = Path(r"E:\DEV\Codex-web")
prior = root / ".coding-tools/reports/sandbox-not-started-20261012/r8-transition"
out = Path(__file__).resolve().parent
proof_path = out.parent / "r9-candidate-verification.json"
proof = json.loads(proof_path.read_text(encoding="utf-8"))
expected_candidate = str(root / "dist/windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9/win-unpacked")
if not (proof["ok"] is True and proof["candidate"] == expected_candidate
        and proof["resources"]["exact_source"] is True and proof["adapters"]["exact_source"] is True
        and proof["sanitation"]["sanitized"] is True):
    raise RuntimeError("Exact r9 package proof required")
for name, expected in (("Coding Tools MCP.exe", proof["executable_sha256"]),
                       ("resources/app.asar", proof["app_asar_sha256"]),
                       ("resources/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_state_aware.py", proof["packaged_adapter_sha256"])):
    if hashlib.sha256((Path(expected_candidate) / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError("r9 package changed since proof")

def source(name, expected):
    raw = (prior / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise RuntimeError("Reviewed r8 script changed")
    return raw.decode("utf-8")

def create(name, text):
    with (out / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)

launch = source("launch-r8.ps1", "cb96bbd02471602708c715047ffa8019e6f157979ee8996b5a707ba06ea24ded")
launch = launch.replace("machine-exec-lifecycle-1012-r8", "machine-folder-access-1012-r9")
launch = launch.replace("machine-exec-lifecycle-1012-r7", "machine-exec-lifecycle-1012-r8")
launch = launch.replace("$R7", "$PriorCandidate").replace("$R8", "$NewCandidate")
launch = launch.replace("7d9e2b2460a70b227fcfb66776bba2955aab8b034094bb88354f99ccb8ddca47", proof["executable_sha256"])
launch = launch.replace("3312c166840d97ffefd50b609c5c9736ebdcd1201cd3346bfc3b0a112b71eb62", proof["app_asar_sha256"])
launch = launch.replace("42692", "11364")
launch = launch.replace("r7", "prior-r8").replace("r8 supervisor", "r9 supervisor").replace("r8 package", "r9 package")
launch = launch.replace("install_r8_supervisor", "install_r9_supervisor").replace("launch_r8_ui", "launch_r9_ui")
launch = launch.replace("The installed supervisor does not target exact r8", "The installed supervisor does not target exact r9")
launch = launch.replace("The exact r8 supervisor installation receipt", "The exact r9 supervisor installation receipt")
launch = launch.replace("    $Retired.receipt.host_pid -ne 11364 -or", "    $Retired.receipt.host_pid -ne 11364 -or\n    $Retired.receipt.retirement.identity.pid -ne 11364 -or\n    $Retired.receipt.retirement.identity.process_start_token -ne '134362637018564480' -or")
launch = launch.replace("    if (Test-Path -LiteralPath $DescriptorPath) {\n        $Descriptor = Get-Content -LiteralPath $DescriptorPath -Raw | ConvertFrom-Json\n        if (Get-Process", "    if (Test-Path -LiteralPath $DescriptorPath) {\n        $Descriptor = Get-Content -LiteralPath $DescriptorPath -Raw | ConvertFrom-Json\n        if ($Descriptor.owner_pid -ne 11364 -or $Descriptor.instance_id -ne '83634bc8f513cc453f74f94751efb819' -or\n            $Descriptor.installation_id -ne '6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228' -or\n            $Descriptor.owner_process_start_token -ne '134362637018564480') { throw 'The preserved retired descriptor is not the exact prior r8 owner.' }\n        if (Get-Process")
create("launch-r9.ps1", launch)

shortcuts = source("update-coding-tools-shortcuts-r8.ps1", "b950a2a21b5e80525928ac230712c3085180ae01ebd792e8d20d72e6c4136589")
shortcuts = shortcuts.replace("machine-exec-lifecycle-1012-r8", "machine-folder-access-1012-r9")
shortcuts = shortcuts.replace("machine-exec-lifecycle-1012-r7", "machine-exec-lifecycle-1012-r8")
shortcuts = shortcuts.replace("7d9e2b2460a70b227fcfb66776bba2955aab8b034094bb88354f99ccb8ddca47", proof["executable_sha256"])
shortcuts = shortcuts.replace("3312c166840d97ffefd50b609c5c9736ebdcd1201cd3346bfc3b0a112b71eb62", proof["app_asar_sha256"])
shortcuts = shortcuts.replace("2cc6d473dab47ba4701ef4653847dcb6c7b0b609c0b90d6dd0f789ecd032b1b1", "982304384ba8a66df884e440c2e0f4ed27f5516ddc1377accd92d7450208c329")
shortcuts = shortcuts.replace("df55a27e4b0dfb693a01d44998a975fe360879b469198ca9f2cc895b3485a9c4", "84f5444f2360de1e8e01d32a3bd892784b93ca3d5b5bf3fc938ce50dba0cc0b9")
shortcuts = shortcuts.replace("r7-original", "r8-original").replace("before-r8.json", "before-r9.json").replace("after-r8.json", "after-r9.json")
shortcuts = shortcuts.replace("activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4", "activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a")
shortcuts = shortcuts.replace("r8", "r9")
# Preserve backup labels as r8: they are the previous exact link bytes.
shortcuts = shortcuts.replace("r9-original", "r8-original")
# The previous target remains the exact existing r8 package.
shortcuts = shortcuts.replace("$ExpectedOldTarget = '" + expected_candidate + "\\Coding Tools MCP.exe'",
    "$ExpectedOldTarget = 'E:\\DEV\\Codex-web\\dist\\windows-candidate-mxc-wsb-cbe1774-machine-exec-lifecycle-1012-r8\\win-unpacked\\Coding Tools MCP.exe'")
shortcuts = shortcuts.replace("machine-exec-lifecycle-1012-r9", "machine-exec-lifecycle-1012-r8")
create("update-coding-tools-shortcuts-r9.ps1", shortcuts)

receipt = {"operation": "prepare_r9_launch_and_shortcut_scripts", "runtime_effects": 0,
    "supervisor_mutated": False, "shortcuts_mutated": False, "candidate": expected_candidate,
    "source_r9_proof_sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest(),
    "exact_prior_host": {"pid": 11364, "instance_id": "83634bc8f513cc453f74f94751efb819",
        "installation_id": "6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228",
        "process_start_token": "134362637018564480"},
    "prepared_files": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                       for name in ("launch-r9.ps1", "update-coding-tools-shortcuts-r9.ps1")}}
create("launch-and-shortcuts-preparation.json", json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
