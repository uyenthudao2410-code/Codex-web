const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_REFRESH_INTERVAL_MS = 30_000;
const MAX_COMPONENT_FILES = 4096;
const MAX_COMPONENT_BYTES = 64 * 1024 * 1024;

const COMPONENT_SPECS = Object.freeze({
  recovery_host: Object.freeze({
    files: Object.freeze([
      'package.json',
      'electron/recoveryHost.js',
      'electron/paths.js',
      'electron/services/commandRunner.js',
      'electron/services/componentRevision.js',
      'electron/services/config.js',
      'electron/services/environmentService.js',
      'electron/services/healthService.js',
      'electron/services/hubProxyGateway.js',
      'electron/services/jsonStore.js',
      'electron/services/logService.js',
      'electron/services/nativeService.js',
      'electron/services/proxyService.js',
      'electron/services/recoveryActionStore.js',
      'electron/services/recoveryActivation.js',
      'electron/services/recoveryHost.js',
      'electron/services/recoveryHostLauncher.js',
      'electron/services/recoveryIpc.js',
      // Recovery-plane source is Recovery Host-owned so accepted bytes activate through the safe host handoff.
      'electron/services/recoveryPlaneService.js',
      'electron/services/runtimeOrchestrator.js',
      'electron/services/runtimePaths.js',
      'electron/services/secretStore.js',
      'electron/services/settingsStore.js',
      'electron/services/tunnelService.js',
      'resources/recovery-mcp/recovery_mcp.py'
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
      'electron/chatViewController.js'
    ]),
    directories: Object.freeze([
      Object.freeze({ path: 'renderer', extensions: Object.freeze(['.css', '.html', '.js']) })
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

  status(component, runningRevision = undefined) {
    const disk = this.disk(component);
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
  ComponentRevisionTracker,
  componentOwnsPath,
  hashComponentRevision,
  DEFAULT_REFRESH_INTERVAL_MS,
  MAX_COMPONENT_FILES,
  MAX_COMPONENT_BYTES
};
