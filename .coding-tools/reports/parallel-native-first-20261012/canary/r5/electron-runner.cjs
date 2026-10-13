'use strict';

// Small argv adapter for packaged Electron RUN_AS_NODE invocations. Electron
// consumes command-line switches before the user script; the reviewed helpers
// intentionally read their mode from process.argv[2].
const args = process.argv.slice(2);
if (args.length < 2) throw new Error('PACKAGED_RUNNER_ARGS_REQUIRED');
const [profile, script, ...rest] = args;
process.argv = ['electron', `--user-data-dir=${profile}`, script, ...rest];
require(script);
