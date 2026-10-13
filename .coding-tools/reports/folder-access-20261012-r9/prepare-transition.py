"""Prepare additive, identity-bound r9 helpers from the reviewed r8 transition."""
from pathlib import Path
import json

root = Path(r'E:\DEV\Codex-web')
old = root / '.coding-tools/reports/sandbox-not-started-20261012'
new = root / '.coding-tools/reports/folder-access-20261012-r9'
transition = new / 'transition'
transition.mkdir(exist_ok=True)

def create(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)

create(new / 'r8-candidate-verification.json', (old / 'r8-candidate-verification.json').read_text())
verify = (old / 'verify-r8-candidate.cjs').read_text()
verify = verify.replace('machine-exec-lifecycle-1012-r8', 'machine-folder-access-1012-r9').replace('r8-candidate-verification', 'r9-candidate-verification')
create(new / 'verify-r9-candidate.cjs', verify)

operations = (old / 'r8-transition/packaged-operations.cjs').read_text()
operations = operations.replace("'r7-candidate-verification.json' : 'r8-candidate-verification.json'", "'r8-candidate-verification.json' : 'r9-candidate-verification.json'")
operations = operations.replace("'workspace_f93b5bac9dc74fae9cea66f44c4ebc94'", "'workspace_bc86004be2684b958ab7a9a6f9530cd7'")
operations = operations.replace("'generation_a420c8bfcfcb4e42b5bb7fc5e5cec097'", "'generation_03f9c04f1b14414fa4bfa7d91cc8ea7a'")
operations = operations.replace("'stopped-observation'].includes(mode)", "'stopped-observation', 'activate'].includes(mode)")
for prior, current in [('42692', '11364'), ('a491a6ccf338a6ea8f6dc8989e40ef74', '83634bc8f513cc453f74f94751efb819'),
    ('8d96439dbc0671127872598f49e79625a25581fff79edb55019ca3a30e26bebd', '6169e7f206f69e2d5364248f93d965c97f58340a908844b2c8f9ef2832f17228'),
    ('activation-mv4vxaab-907c8a927b8eb80e4e7b8b56bdb150ed', 'activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a')]:
    operations = operations.replace(prior, current)
operations = operations.replace("  } else if (mode === 'metadata'", "  } else if (mode === 'activate') {\n    const { canonicalLedgerCensus } = load('fullCleanActivation');\n    const census = await canonicalLedgerCensus({ paths, workspace: root, allowAcceptancePending: true });\n    requireState(Array.isArray(census.lifecycle?.blockers) && census.lifecycle.blockers.every(reason => reason === 'live_runtime_state_process')\n      && census.lifecycle.unexplained_active_runs === 0 && census.lifecycle.unbound_live_resource_residues === 0\n      && ['active_tool_calls','active_commands','starting_commands','active_background_operations','active_managed_processes','foreign_heavy_processes','active_agent_lanes','owned_codex_sidecar_residues']\n        .every(key => census.counts[key] === 0), 'ACTIVE_LOCAL_WORK_PREVENTS_FOLDER_ACTIVATION');\n    receipt = await service.activateWorkspace({ workspaceId, workspaceGeneration: currentGeneration, confirmActivate: true });\n  } else if (mode === 'metadata'")
create(transition / 'packaged-operations.cjs', operations)

observer = (old / 'r8-transition/observe-r8-machine.cjs').read_text()
observer = observer.replace('r8-candidate-verification.json', 'r9-candidate-verification.json')
observer = observer.replace('activation-mv4vxaab-907c8a927b8eb80e4e7b8b56bdb150ed', 'activation-mv4xk8xx-3d9f30b9b0542ef0458f3c3b241d365a')
create(transition / 'observe-r9-machine.cjs', observer)
print(json.dumps({'prepared': True, 'runtime_effects': 0}))
