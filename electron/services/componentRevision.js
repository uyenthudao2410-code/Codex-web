const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_REFRESH_INTERVAL_MS = 30_000;
const MAX_COMPONENT_FILES = 4096;
const MAX_COMPONENT_BYTES = 64 * 1024 * 1024;
const RECOVERY_HOST_LEGACY_V1_CONTRACT = 'recovery_host_legacy_v1_without_device_identity';
const RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS = Object.freeze({
  'electron/services/deviceIdentity.js': '8b673b83c76f6cf745d36849af677ce9f97e8b3441ffd14f1c220311c20e144e',
  'electron/services/runtimeIdentity.js': '4774b0922cbcf859addd99899a76db449477cfe0643bcacdb00f9549d02caea5'
});
const COMPONENT_ORDER = Object.freeze(['recovery_host', 'coding_mcp', 'electron_ui']);

const COMPONENT_SPECS = Object.freeze({
  recovery_host: Object.freeze({
    files: Object.freeze([
      'package.json',
      'electron/recoveryHost.js',
      'electron/paths.js',
      'electron/services/commandRunner.js',
      'electron/services/componentRevision.js',
      'electron/services/config.js',
      'electron/services/controlPlaneApprovedPatchBridge.js',
      'electron/services/controlPlaneDocumentWriteBridge.js',
      'electron/services/controlPlaneExecBridge.js',
      'electron/services/controlPlaneFileReadBridge.js',
      'electron/services/controlPlanePolicyStore.js',
      'electron/services/controlPlaneReadOnlyBridge.js',
      'electron/services/controlPlaneRouteEvidence.js',
      'electron/services/controlledRestartGuard.js',
      'electron/services/pathSemantics.js',
      'electron/services/tokenMeasurement.js',
      'electron/services/tunnelProcessEnvironment.js',
      'electron/services/connectorAttestation.js',
      'electron/services/deviceIdentity.js',
      'electron/services/environmentService.js',
      'electron/services/healthService.js',
      'electron/services/hubProxyGateway.js',
      'electron/services/jsonStore.js',
      'electron/services/logService.js',
      'electron/services/mcpSemanticHealth.js',
      'electron/services/nativeService.js',
      'electron/services/proxyService.js',
      'electron/services/processIdentity.js',
      'electron/services/recoveryActionStore.js',
      'electron/services/recoveryActivation.js',
      'electron/services/recoveryBootstrap.js',
      'electron/services/activationEpoch.js',
      'electron/services/activationClosure.js',
      'electron/services/activationPostflight.js',
      'electron/services/fullCleanActivation.js',
      'electron/services/recoveryHost.js',
      'electron/services/recoveryHostLauncher.js',
      'electron/services/recoveryIpc.js',
      // Recovery-plane source is Recovery Host-owned so accepted bytes activate through the safe host handoff.
      'electron/services/recoveryPlaneService.js',
      'electron/services/runtimeIdentity.js',
      'electron/services/runtimeOrchestrator.js',
      'electron/services/runtimePaths.js',
      'electron/services/secretStore.js',
      'electron/services/settingsStore.js',
      'electron/services/tunnelService.js',
      'resources/recovery-mcp/recovery_mcp.py',
      'resources/recovery-supervisor/recovery-supervisor.ps1',
      'electron/services/trustedRecoveryBootstrap.js',
      'scripts/full-clean-activation.js',
      'scripts/trusted-recovery-bootstrap.js'
    ])
  }),
  coding_mcp: Object.freeze({
    root: 'resources',
    files: Object.freeze(['coding-tools-mcp/pyproject.toml']),
    directories: Object.freeze([
      Object.freeze({ path: 'coding-tools-mcp/coding_tools_mcp', extensions: Object.freeze(['.py']) })
    ])
  }),
  electron_ui: Object.freeze({
    files: Object.freeze([
      'package.json',
      'electron/main.js',
      'electron/preload.js',
      'electron/panelPreload.js',
      'electron/browserPreload.js',
      'electron/app-icon.ico',
      'electron/app-icon.png',
      'electron/services/buildVerificationService.js',
      'electron/services/codexDesktopConfig.js',
      'electron/services/controlPlaneEnrollment.js',
      'electron/services/panelLayout.js',
      'electron/services/uiPerformanceMetrics.js',
      'electron/services/workHubFiles.js',
      'renderer/app-icon.png'
    ]),
    directories: Object.freeze([
      // These are loaded by the Electron renderer, including the local font
      // binaries referenced by renderer/fonts.css.
      Object.freeze({ path: 'renderer', extensions: Object.freeze(['.css', '.html', '.js', '.woff2']) })
    ])
  })
});

function normalizedRelative(relative) {
  return String(relative || '').replace(/\\/g, '/').replace(/^\.\//, '');
}

function withinRoot(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function collectDirectory(root, directory, extensions, output) {
  const absolute = path.resolve(root, directory);
  if (!withinRoot(root, absolute)) throw Object.assign(new Error('Component revision path escaped the application root.'), { code: 'REVISION_PATH_INVALID' });
  if (!fs.existsSync(absolute)) {
    output.add(`${normalizedRelative(directory)}/<missing>`);
    return;
  }
  const entries = fs.readdirSync(absolute, { withFileTypes: true })
    .sort((left, right) => left.name.localeCompare(right.name));
  for (const entry of entries) {
    const child = path.join(absolute, entry.name);
    if (entry.isDirectory()) {
      collectDirectory(root, path.relative(root, child), extensions, output);
    } else if (entry.isFile() && extensions.includes(path.extname(entry.name).toLowerCase())) {
      output.add(normalizedRelative(path.relative(root, child)));
    }
  }
}

function componentFiles(root, spec) {
  const output = new Set((spec.files || []).map(normalizedRelative));
  for (const directory of spec.directories || []) {
    collectDirectory(root, directory.path, directory.extensions || [], output);
  }
  const files = [...output].sort();
  if (files.length > MAX_COMPONENT_FILES) {
    throw Object.assign(new Error('Component revision file count exceeded the bounded limit.'), { code: 'REVISION_INPUT_TOO_LARGE' });
  }
  return files;
}

function componentOwnsPath(component, workspaceRelative, specs = COMPONENT_SPECS) {
  const spec = specs[component];
  const relative = normalizedRelative(workspaceRelative);
  if (!spec || !relative) return false;
  const rootPrefix = spec.root ? `${normalizedRelative(spec.root)}/` : '';
  if ((spec.files || []).some((file) => relative === `${rootPrefix}${normalizedRelative(file)}`)) return true;
  return (spec.directories || []).some((directory) => {
    const prefix = `${rootPrefix}${normalizedRelative(directory.path)}/`;
    return relative.startsWith(prefix)
      && (directory.extensions || []).includes(path.extname(relative).toLowerCase());
  });
}

function componentOwners(workspaceRelative, specs = COMPONENT_SPECS) {
  const configured = Object.keys(specs || {});
  const ordered = [
    ...COMPONENT_ORDER.filter((component) => configured.includes(component)),
    ...configured.filter((component) => !COMPONENT_ORDER.includes(component)).sort()
  ];
  return ordered.filter((component) => componentOwnsPath(component, workspaceRelative, specs));
}

function hashComponentRevision(appRoot, component, specs = COMPONENT_SPECS) {
  const root = path.resolve(String(appRoot || ''));
  const spec = specs[component];
  if (!path.isAbsolute(root) || !spec) {
    throw Object.assign(new Error('Component revision input is invalid.'), { code: 'REVISION_INPUT_INVALID' });
  }
  const hash = crypto.createHash('sha256');
  hash.update('webcodex-component-revision-v1\0');
  hash.update(component);
  hash.update('\0');
  let totalBytes = 0;
  let missingFiles = 0;
  const files = componentFiles(root, spec);
  for (const relative of files) {
    hash.update(relative);
    hash.update('\0');
    if (relative.endsWith('/<missing>')) {
      missingFiles += 1;
      hash.update('<missing-directory>\0');
      continue;
    }
    const absolute = path.resolve(root, relative);
    if (!withinRoot(root, absolute)) {
      throw Object.assign(new Error('Component revision path escaped the application root.'), { code: 'REVISION_PATH_INVALID' });
    }
    let content;
    try { content = fs.readFileSync(absolute); }
    catch {
      missingFiles += 1;
      hash.update('<missing-file>\0');
      continue;
    }
    totalBytes += content.length;
    if (totalBytes > MAX_COMPONENT_BYTES) {
      throw Object.assign(new Error('Component revision bytes exceeded the bounded limit.'), { code: 'REVISION_INPUT_TOO_LARGE' });
    }
    hash.update(String(content.length));
    hash.update('\0');
    hash.update(content);
    hash.update('\0');
  }
  return {
    revision: hash.digest('hex'),
    file_count: files.length,
    missing_files: missingFiles,
    total_bytes: totalBytes
  };
}

function recoveryHostLegacyV1Revision(appRoot) {
  const root = path.resolve(String(appRoot || ''));
  if (!path.isAbsolute(root)) {
    throw Object.assign(new Error('Recovery Host legacy revision root is invalid.'), { code: 'REVISION_INPUT_INVALID' });
  }
  const pinnedAddedFiles = [];
  const currentFiles = new Set((COMPONENT_SPECS.recovery_host.files || []).map(normalizedRelative));
  for (const [relativeValue, expectedSha256] of Object.entries(RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS)) {
    const relative = normalizedRelative(relativeValue);
    if (!currentFiles.has(relative)) {
      throw Object.assign(new Error('Recovery Host legacy revision bridge no longer matches the current component manifest.'), { code: 'REVISION_BRIDGE_CONTRACT_INVALID' });
    }
    const absolute = path.resolve(root, relative);
    if (!withinRoot(root, absolute)) {
      throw Object.assign(new Error('Recovery Host legacy revision bridge path escaped the application root.'), { code: 'REVISION_PATH_INVALID' });
    }
    let content;
    try { content = fs.readFileSync(absolute); }
    catch {
      throw Object.assign(new Error('Recovery Host legacy revision bridge file is unavailable.'), { code: 'REVISION_BRIDGE_FILE_MISSING' });
    }
    // Git may materialize text files as CRLF on Windows even though the
    // canonical repository bytes are LF. The legacy bridge pins source
    // semantics, not checkout-specific line endings, so normalize only this
    // pinned text-file proof. Ordinary component revisions intentionally keep
    // hashing the exact on-disk bytes above.
    const canonicalContent = Buffer.from(content.toString('utf8').replace(/\r\n/g, '\n'), 'utf8');
    const actualSha256 = crypto.createHash('sha256').update(canonicalContent).digest('hex');
    if (actualSha256 !== expectedSha256) {
      throw Object.assign(new Error('Recovery Host legacy revision bridge file digest changed.'), {
        code: 'REVISION_BRIDGE_DIGEST_MISMATCH',
        details: { path: relative, expected_sha256: expectedSha256, actual_sha256: actualSha256 }
      });
    }
    pinnedAddedFiles.push({ path: relative, sha256: actualSha256 });
  }
  const addedPaths = new Set(Object.keys(RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS).map(normalizedRelative));
  const legacyRecoveryHostSpec = Object.freeze({
    ...COMPONENT_SPECS.recovery_host,
    files: Object.freeze((COMPONENT_SPECS.recovery_host.files || []).filter((relative) => !addedPaths.has(normalizedRelative(relative))))
  });
  const legacySpecs = { ...COMPONENT_SPECS, recovery_host: legacyRecoveryHostSpec };
  return {
    ...hashComponentRevision(root, 'recovery_host', legacySpecs),
    contract: RECOVERY_HOST_LEGACY_V1_CONTRACT,
    pinned_added_files: pinnedAddedFiles
  };
}

class ComponentRevisionTracker {
  constructor({ paths, specs = COMPONENT_SPECS, refreshIntervalMs = DEFAULT_REFRESH_INTERVAL_MS, now = () => Date.now() }) {
    this.paths = paths;
    this.specs = specs;
    this.refreshIntervalMs = Math.max(0, Number(refreshIntervalMs) || 0);
    this.now = now;
    this.cache = new Map();
    this.running = new Map();
  }

  disk(component, options = {}) {
    const now = this.now();
    const cached = this.cache.get(component);
    if (!options.force && cached && now - cached.checkedAt < this.refreshIntervalMs) return cached.value;
    const spec = this.specs[component];
    const root = spec?.root === 'resources' ? this.paths.resourcesRoot() : this.paths.appRoot();
    const value = {
      ...hashComponentRevision(root, component, this.specs),
      checked_at: new Date(now).toISOString()
    };
    this.cache.set(component, { checkedAt: now, value });
    return value;
  }

  captureRunning(component) {
    const disk = this.disk(component, { force: true });
    this.running.set(component, disk.revision);
    return disk.revision;
  }

  status(component, runningRevision = undefined, options = {}) {
    const disk = this.disk(component, { force: options?.force === true });
    const running = runningRevision === undefined
      ? String(this.running.get(component) || '')
      : String(runningRevision || '');
    return {
      running_revision: running || null,
      disk_revision: disk.revision,
      update_pending: running ? running !== disk.revision : null,
      state: running ? (running === disk.revision ? 'current' : 'update_pending') : 'unknown',
      checked_at: disk.checked_at,
      file_count: disk.file_count
    };
  }
}

module.exports = {
  COMPONENT_SPECS,
  COMPONENT_ORDER,
  ComponentRevisionTracker,
  componentOwnsPath,
  componentOwners,
  hashComponentRevision,
  recoveryHostLegacyV1Revision,
  RECOVERY_HOST_LEGACY_V1_CONTRACT,
  RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS,
  DEFAULT_REFRESH_INTERVAL_MS,
  MAX_COMPONENT_FILES,
  MAX_COMPONENT_BYTES
};
