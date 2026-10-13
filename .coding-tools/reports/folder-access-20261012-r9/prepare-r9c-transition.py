from pathlib import Path
import json

root = Path(r'E:\DEV\Codex-web\.coding-tools\reports\folder-access-20261012-r9')
previous = root / 'r9b-transition'
target = root / 'r9c-transition'
target.mkdir(exist_ok=True)
proof = json.loads((root / 'r9c-candidate-verification.json').read_text())
assert proof['ok'] is True
assert proof['candidate'] == r'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9c\win-unpacked'

def create(name, value):
    with (target / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)

def changed(value, replacements):
    for before, after in replacements:
        if before not in value:
            raise ValueError('Missing expected source fragment: ' + before)
        value = value.replace(before, after)
    return value

identity = [
    ('46092', '43176'),
    ('46784d8ace11d21e87705a6ad93b1411', '21106c0b1376ec5a6142d074c619575f'),
    ('99dce9d41278ebd61f3fb6701fb60e166092b57c9a10784c994da4bcdd66ecab', '588b9782f4c3a2577a003894c95668543d81eb69311a77cb288b0cafa13a6148'),
    ('activation-mv4zd4vb-152a334b42a5ef82b6feff9498747bb6', 'activation-mv4ztgwa-41d4eace008278b49931d1b727068507')
]
ops = changed((previous / 'packaged-operations.cjs').read_text(), [
    ("'r9-candidate-verification.json' : 'r9b-candidate-verification.json'", "'r9b-candidate-verification.json' : 'r9c-candidate-verification.json'"),
    *identity,
    ('LIVE_SANDBOX_PREVENTS_R7_RETIREMENT', 'LIVE_SANDBOX_PREVENTS_R9B_RETIREMENT'),
    ('EXACT_R7_OWNER_REQUIRED', 'EXACT_R9B_OWNER_REQUIRED')
])
old_activation = "    receipt = await service.activateWorkspace({ workspaceId, workspaceGeneration: currentGeneration, confirmActivate: true });"
new_activation = """    const workspaceRoot = service.registeredWorkspaceRoot({ workspaceId, workspaceGeneration: currentGeneration });
    requireState(workspaceRoot.toLowerCase() === 'e:\\\\dev\\\\autocad', 'EXACT_AUTOCAD_ROOT_REQUIRED');
    const { SettingsStore } = load('settingsStore');
    const settings = new SettingsStore(paths);
    const beforeSettings = settings.load();
    const beforeEpoch = await exactCall('runtime.activation_epoch_status');
    const roots = Array.isArray(beforeSettings.authorizedRoots) ? beforeSettings.authorizedRoots : [];
    const key = value => path.normalize(value).toLowerCase();
    let added = false;
    if (key(workspaceRoot) !== key(beforeSettings.workspace) && !roots.some(root => key(root) === key(workspaceRoot))) {
      requireState(roots.length < 32, 'CONTROL_PLANE_WORKSPACE_ROOT_LIMIT');
      await exactCall('runtime.update_authorized_roots', [[...roots, workspaceRoot]]);
      added = true;
    }
    const afterSettings = settings.load();
    const afterEpoch = await exactCall('runtime.activation_epoch_status');
    requireState(key(afterSettings.workspace) === key(beforeSettings.workspace)
      && afterEpoch.activation_epoch_id === beforeEpoch.activation_epoch_id
      && afterEpoch.state === 'READY' && afterEpoch.admission_open === true
      && (key(workspaceRoot) === key(afterSettings.workspace)
        || afterSettings.authorizedRoots.some(root => key(root) === key(workspaceRoot))), 'NATIVE_ROOT_AUTHORIZATION_NOT_VERIFIED');
    const activation = await service.activateWorkspace({ workspaceId, workspaceGeneration: currentGeneration, confirmActivate: true });
    receipt = { ...activation, local_root_authorization: { verified: true, added,
      authorized_root: workspaceRoot, native_default_workspace: afterSettings.workspace,
      activation_epoch_unchanged: true, activation_epoch_id: afterEpoch.activation_epoch_id } };"""
ops = changed(ops, [(old_activation, new_activation)])
create('packaged-operations.cjs', ops)

tags = [
    ('machine-folder-access-1012-r9b', 'machine-folder-access-1012-r9c'),
    ('machine-folder-access-1012-r9\\', 'machine-folder-access-1012-r9b\\')
]
invoke = changed((previous / 'invoke-packaged.ps1').read_text(), [*tags, ('observe-r9b-machine.cjs', 'observe-r9c-machine.cjs')])
create('invoke-packaged.ps1', invoke)
observer = changed((previous / 'observe-r9b-machine.cjs').read_text(), [
    ('r9b-candidate-verification.json', 'r9c-candidate-verification.json'),
    identity[-1],
    ('NEW_EXACT_R8_ACTIVATION_EPOCH_REQUIRED', 'NEW_EXACT_R9C_ACTIVATION_EPOCH_REQUIRED'),
    ('EXACT_VERIFIED_R8_PACKAGE_REQUIRED', 'EXACT_VERIFIED_R9C_PACKAGE_REQUIRED')
])
create('observe-r9c-machine.cjs', observer)

hashes = [
    ('d99de2dbbcf6bedc7db957b487db73c7eb6bf63f1458fd3bd337e0396e5a7d10', proof['executable_sha256']),
    ('a9a8c2007c12ecf7654f3eb38ae44a82df0a7c69888189090b517be361bc16fe', proof['app_asar_sha256'])
]
launch = changed((previous / 'launch-r9b.ps1').read_text(), [
    *tags, *hashes, *identity[:-1], ('134362667290535710', '134362674908503410'),
    ('install_r9b_supervisor', 'install_r9c_supervisor'),
    ('launch_r9b_ui', 'launch_r9c_ui')
])
launch = launch.replace('prior-r8', 'prior-r9b').replace('prior-r9 supervisor', 'prior-r9b supervisor').replace('prior r8 owner', 'prior r9b owner')
launch = launch.replace('The r9 package', 'The r9c package').replace('r9 supervisor', 'r9c supervisor').replace('exact r9.', 'exact r9c.')
create('launch-r9c.ps1', launch)

shortcut = changed((previous / 'update-coding-tools-shortcuts-r9b.ps1').read_text(), [
    (tags[0][0], tags[0][1]), *hashes, identity[-1]
])
shortcut = shortcut.replace('before-r9.json', 'before-r9c.json').replace('after-r9.json', 'after-r9c.json')
shortcut = shortcut.replace('r9 package', 'r9c package').replace('r9 EXE', 'r9c EXE').replace('r9 activation', 'r9c activation').replace('An r9 observer', 'An r9c observer').replace('The r9 READY', 'The r9c READY')
create('update-coding-tools-shortcuts-r9c.ps1', shortcut)
print('Prepared additive r9c transition; no runtime effects')
