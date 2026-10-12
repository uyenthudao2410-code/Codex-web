'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = 'E:\\Github\\Tools-Codex-web';
const result = {
  observation_kind: 'readonly_host_workspace_path_probe',
  observed_at: new Date().toISOString(),
  node: process.execPath,
  cwd: process.cwd(),
  process_container_launched: false,
  windows_sandbox_launched: false,
  mutation_performed: false
};
for (const [label, target] of [['workspace', root], ['cwd_directory', process.cwd()]]) {
  try {
    result[label] = { realpath: fs.realpathSync.native(target), directory: fs.statSync(target).isDirectory() };
  } catch (error) {
    result[label] = { code: String(error.code || 'FAILED') };
  }
}
result.windows_sandbox_executable_present = fs.existsSync(path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsSandbox.exe'));
process.stdout.write(JSON.stringify(result) + '\n');
