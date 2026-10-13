from pathlib import Path
root = Path(r'E:\DEV\Codex-web\.coding-tools\reports\folder-access-20261012-r9')
previous = root / 'transition'
target = root / 'r9b-transition'
target.mkdir(exist_ok=True)
def create(name, value):
    with (target / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)
old_r8 = 'machine-exec-lifecycle-1012-r8'
old_r9 = 'machine-folder-access-1012-r9'
new_r9b = 'machine-folder-access-1012-r9b'
ops = (previous / 'packaged-operations.cjs').read_text()
ops = ops.replace("'r8-candidate-verification.json' : 'r9-candidate-verification.json'", "'r9-candidate-verification.json' : 'r9b-candidate-verification.json'")
for before, after in [('11364', '46092'), ('83634bc8f513cc453f74f94751efb819', '46784d8ace11d21e87705a6ad93b1411'),
    ('6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228', '99dce9d41278ebd61f3fb6701fb60e166092b57c9a10784c994da4bcdd66ecab'),
    ('activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a', 'activation-mv4zd4vb-152a334b42a5ef82b6feff9498747bb6')]:
    ops = ops.replace(before, after)
create('packaged-operations.cjs', ops)
invoke = (previous / 'invoke-packaged.ps1').read_text().replace(old_r9, new_r9b).replace(old_r8, old_r9)
invoke = invoke.replace('observe-r9-machine.cjs', 'observe-r9b-machine.cjs')
create('invoke-packaged.ps1', invoke)
observer = (previous / 'observe-r9-machine.cjs').read_text().replace('r9-candidate-verification.json', 'r9b-candidate-verification.json')
observer = observer.replace('activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a', 'activation-mv4zd4vb-152a334b42a5ef82b6feff9498747bb6')
create('observe-r9b-machine.cjs', observer)
launch = (previous / 'launch-r9.ps1').read_text().replace(old_r9, new_r9b).replace(old_r8, old_r9)
for before, after in [('4d7bb476ae8ebc8e15af8ebdb8081d0cb56c524443bbfe3f36cf07b66a14a268', 'd99de2dbbcf6bedc7db957b487db73c7eb6bf63f1458fd3bd337e0396e5a7d10'),
    ('445b0e4e24d3f7cd39e487d257545025d63ca7ca02e8a425f904bc1787f489d0', 'a9a8c2007c12ecf7654f3eb38ae44a82df0a7c69888189090b517be361bc16fe'),
    ('11364', '46092'), ('134362637018564480', '134362667290535710'), ('83634bc8f513cc453f74f94751efb819', '46784d8ace11d21e87705a6ad93b1411'),
    ('6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228', '99dce9d41278ebd61f3fb6701fb60e166092b57c9a10784c994da4bcdd66ecab'),
    ('install_r9_supervisor', 'install_r9b_supervisor'), ('launch_r9_ui', 'launch_r9b_ui')]:
    launch = launch.replace(before, after)
create('launch-r9b.ps1', launch)
shortcut = (previous / 'update-coding-tools-shortcuts-r9.ps1').read_text().replace(old_r9, new_r9b)
shortcut = shortcut.replace('4d7bb476ae8ebc8e15af8ebdb8081d0cb56c524443bbfe3f36cf07b66a14a268', 'd99de2dbbcf6bedc7db957b487db73c7eb6bf63f1458fd3bd337e0396e5a7d10')
shortcut = shortcut.replace('445b0e4e24d3f7cd39e487d257545025d63ca7ca02e8a425f904bc1787f489d0', 'a9a8c2007c12ecf7654f3eb38ae44a82df0a7c69888189090b517be361bc16fe')
shortcut = shortcut.replace('activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a','activation-mv4zd4vb-152a334b42a5ef82b6feff9498747bb6')
create('update-coding-tools-shortcuts-r9b.ps1', shortcut)
print('Prepared additive r9b transition; no runtime effects')
