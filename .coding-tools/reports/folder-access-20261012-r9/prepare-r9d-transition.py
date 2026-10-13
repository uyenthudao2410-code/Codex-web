from pathlib import Path
import json

root = Path(r'E:\DEV\Codex-web\.coding-tools\reports\folder-access-20261012-r9')
previous = root / 'r9c-transition'
target = root / 'r9d-transition'
proof = json.loads((root / 'r9d-candidate-verification.json').read_text())
assert proof['ok'] is True
assert proof['candidate'] == r'E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-folder-access-1012-r9d\win-unpacked'
target.mkdir(exist_ok=True)

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
    ('43176', '35288'),
    ('21106c0b1376ec5a6142d074c619575f', 'd01ae3e08fb3e06fe2fda5da65c61285'),
    ('588b9782f4c3a2577a003894c95668543d81eb69311a77cb288b0cafa13a6148', '0f533411b2fdd0939b42db27ac9b4ad65361228f50489107338bf00e5826b740'),
    ('activation-mv4ztgwa-41d4eace008278b49931d1b727068507', 'activation-mv50m446-6a132615d256208450967af03c450d00')
]
ops = changed((previous / 'packaged-operations.cjs').read_text(), [
    ("'r9b-candidate-verification.json' : 'r9c-candidate-verification.json'", "'r9c-candidate-verification.json' : 'r9d-candidate-verification.json'"),
    *identity,
    ('LIVE_SANDBOX_PREVENTS_R9B_RETIREMENT', 'LIVE_SANDBOX_PREVENTS_R9C_RETIREMENT'),
    ('EXACT_R9B_OWNER_REQUIRED', 'EXACT_R9C_OWNER_REQUIRED')
])
create('packaged-operations.cjs', ops)

tags = [
    ('machine-folder-access-1012-r9c', 'machine-folder-access-1012-r9d'),
    ('machine-folder-access-1012-r9b', 'machine-folder-access-1012-r9c')
]
invoke = changed((previous / 'invoke-packaged.ps1').read_text(), [*tags, ('observe-r9c-machine.cjs', 'observe-r9d-machine.cjs')])
create('invoke-packaged.ps1', invoke)
observer = changed((previous / 'observe-r9c-machine.cjs').read_text(), [
    ('r9c-candidate-verification.json', 'r9d-candidate-verification.json'),
    identity[-1],
    ('NEW_EXACT_R9C_ACTIVATION_EPOCH_REQUIRED', 'NEW_EXACT_R9D_ACTIVATION_EPOCH_REQUIRED'),
    ('EXACT_VERIFIED_R9C_PACKAGE_REQUIRED', 'EXACT_VERIFIED_R9D_PACKAGE_REQUIRED')
])
create('observe-r9d-machine.cjs', observer)

hashes = [
    ('88a36a0c15cc5eb97657c8e68554f07aa7704cfaab9fd0ab2078ea4423f19bf2', proof['executable_sha256']),
    ('45903d28f4c7e0415ca30857992e5b34c66e1f7f597822c35036874df7dd78cd', proof['app_asar_sha256'])
]
launch = changed((previous / 'launch-r9c.ps1').read_text(), [
    *tags, *hashes, *identity[:-1], ('134362674908503410', '134362688272046960'),
    ('install_r9c_supervisor', 'install_r9d_supervisor'),
    ('launch_r9c_ui', 'launch_r9d_ui')
])
launch = launch.replace('prior-r9b', 'prior-r9c').replace('prior r9b owner', 'prior r9c owner')
launch = launch.replace('The r9c package', 'The r9d package').replace('r9c supervisor', 'r9d supervisor').replace('exact r9c.', 'exact r9d.')
create('launch-r9d.ps1', launch)

shortcut = changed((previous / 'update-coding-tools-shortcuts-r9c.ps1').read_text(), [
    (tags[0][0], tags[0][1]), *hashes, identity[-1]
])
shortcut = shortcut.replace('before-r9c.json', 'before-r9d.json').replace('after-r9c.json', 'after-r9d.json')
shortcut = shortcut.replace('r9c package', 'r9d package').replace('r9c EXE', 'r9d EXE').replace('r9c activation', 'r9d activation').replace('An r9c observer', 'An r9d observer').replace('The r9c READY', 'The r9d READY')
create('update-coding-tools-shortcuts-r9d.ps1', shortcut)
print('Prepared additive r9d transition; no runtime effects')
