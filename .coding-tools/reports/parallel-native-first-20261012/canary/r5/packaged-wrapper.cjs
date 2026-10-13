'use strict';
const script = 'E:\\DEV\\Codex-web\\.coding-tools\\reports\\parallel-native-first-20261012\\canary\\r5\\packaged-token-policy.cjs';
process.argv = ['electron', 'packaged-wrapper', ...process.argv.slice(2)];
require(script);
