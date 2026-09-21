"use strict";

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { spawnSync } = require("node:child_process");
const { flipFuses, FuseVersion, FuseV1Options } = require("@electron/fuses");

const FORBIDDEN_DIRECTORY_NAMES = new Set([
  "__pycache__",
  ".pytest_cache",
  ".coding-tools",
]);
const DEV_ONLY_CODING_MCP_DIRECTORIES = new Set([
  "tests",
  "benchmarks",
  "scripts",
]);
const SANCTIONED_CODING_MCP_RUNTIME_FILES = new Set([
  "coding-tools-mcp/scripts/reconcile_exact_stale_run.py",
]);
const CONTROL_PLANE_ADAPTER_FILES = Object.freeze([
  "node_agent.py",
  "node-agent.cmd",
  "recovery_identity_observer.cjs",
  "recovery_approved_patch_bridge.cjs",
  "recovery_document_write_bridge.cjs",
  "recovery_exec_bridge.cjs",
  "recovery_file_read_bridge.cjs",
  "recovery_read_only_bridge.cjs",
  "recovery_runtime_adapter.cjs",
]);

function assertRunAsNode(executable, { spawnSyncFn = spawnSync } = {}) {
  const environment = { ...process.env, ELECTRON_RUN_AS_NODE: "1" };
  delete environment.NODE_OPTIONS;
  delete environment.NODE_EXTRA_CA_CERTS;
  const result = spawnSyncFn(executable, ["-e", "process.stdout.write('CODING_TOOLS_RUN_AS_NODE_OK')"], {
    env: environment,
    encoding: "utf8",
    timeout: 5000,
    windowsHide: true
  });
  if (result?.error || result?.status !== 0 || String(result?.stdout || "") !== "CODING_TOOLS_RUN_AS_NODE_OK") {
    throw new Error("packaged Electron RunAsNode fuse is not executable");
  }
  return { executable, run_as_node: true };
}

async function configureWindowsFuses(context) {
  if (context?.electronPlatformName !== "win32") return null;
  const executableName = String(context?.packager?.appInfo?.productFilename || "Coding Tools MCP");
  const executable = path.join(context.appOutDir, `${executableName}.exe`);
  if (!fs.existsSync(executable)) {
    throw new Error(`packaged Electron executable is missing: ${executable}`);
  }
  // The installed node agent invokes only the allowlisted CJS adapters with
  // ELECTRON_RUN_AS_NODE. Keep this fuse enabled so it does not silently turn
  // into a GUI launch and leave a read-only action without a typed receipt.
  await flipFuses(executable, {
    version: FuseVersion.V1,
    [FuseV1Options.RunAsNode]: true
  });
  return assertRunAsNode(executable);
}

function forbiddenReason(relativePath, isDirectory) {
  const normalized = relativePath.split(path.sep).join("/");
  const parts = normalized.split("/").filter(Boolean);
  if (parts[0] === "coding-tools-mcp" && DEV_ONLY_CODING_MCP_DIRECTORIES.has(parts[1])) {
    if (parts[1] === "scripts"
      && ((isDirectory && parts.length === 2)
        || (!isDirectory && SANCTIONED_CODING_MCP_RUNTIME_FILES.has(normalized)))) {
      return "";
    }
    return "development-only Coding MCP directory";
  }
  if (parts.some((part) => FORBIDDEN_DIRECTORY_NAMES.has(part))) {
    return "volatile runtime/cache directory";
  }
  if (parts.some((part) => part.endsWith(".egg-info"))) {
    return "Python packaging metadata";
  }
  if (!isDirectory && /\.(?:pyc|pyo)$/i.test(normalized)) {
    return "compiled Python cache file";
  }
  return "";
}

function assertSanitizedPackagedResources(resourcesRoot) {
  if (!resourcesRoot || !fs.existsSync(resourcesRoot)) {
    throw new Error(`packaged resources root is missing: ${resourcesRoot || "<empty>"}`);
  }
  const root = path.resolve(resourcesRoot);
  const stack = [root];
  let scannedEntries = 0;
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolute = path.join(current, entry.name);
      const relative = path.relative(root, absolute);
      scannedEntries += 1;
      const reason = forbiddenReason(relative, entry.isDirectory());
      if (reason) {
        throw new Error(`packaged resources sanitation failed: ${relative} (${reason})`);
      }
      if (entry.isDirectory()) {
        stack.push(absolute);
      }
    }
  }
  return { scanned_entries: scannedEntries, sanitized: true };
}

function sha256File(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function collectAllowedFiles(root, { source = false, separatelyVerifiedTopLevelDirectories = new Set() } = {}) {
  const resolvedRoot = path.resolve(root);
  const files = new Map();
  const stack = [resolvedRoot];
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolute = path.join(current, entry.name);
      const relative = path.relative(resolvedRoot, absolute);
      const normalized = relative.split(path.sep).join("/");
      const [topLevelDirectory] = normalized.split("/", 1);
      if (separatelyVerifiedTopLevelDirectories.has(topLevelDirectory)) {
        continue;
      }
      const reason = forbiddenReason(relative, entry.isDirectory());
      if (reason) {
        if (source) continue;
        throw new Error(`packaged resources sanitation failed: ${relative} (${reason})`);
      }
      if (entry.isDirectory()) {
        stack.push(absolute);
        continue;
      }
      if (!entry.isFile()) throw new Error(`packaged resources contain unsupported entry: ${relative}`);
      const stat = fs.statSync(absolute);
      files.set(normalized, { size: stat.size, sha256: sha256File(absolute) });
    }
  }
  return files;
}

function assertExactPackagedResources(
  sourceResourcesRoot,
  packagedResourcesRoot,
  { separatelyVerifiedTopLevelDirectories = [] } = {}
) {
  if (!sourceResourcesRoot || !fs.existsSync(sourceResourcesRoot)) {
    throw new Error(`source resources root is missing: ${sourceResourcesRoot || "<empty>"}`);
  }
  assertSanitizedPackagedResources(packagedResourcesRoot);
  const separatelyVerified = new Set(separatelyVerifiedTopLevelDirectories);
  const sourceFiles = collectAllowedFiles(sourceResourcesRoot, {
    source: true,
    separatelyVerifiedTopLevelDirectories: separatelyVerified,
  });
  const packagedFiles = collectAllowedFiles(packagedResourcesRoot, {
    separatelyVerifiedTopLevelDirectories: separatelyVerified,
  });
  const allPaths = new Set([...sourceFiles.keys(), ...packagedFiles.keys()]);
  for (const relative of [...allPaths].sort()) {
    const expected = sourceFiles.get(relative);
    const actual = packagedFiles.get(relative);
    if (!expected) throw new Error(`packaged resource is not present in current source: ${relative}`);
    if (!actual) throw new Error(`packaged resource missing from current source projection: ${relative}`);
    if (expected.size !== actual.size || expected.sha256 !== actual.sha256) {
      throw new Error(`packaged resource source mismatch: ${relative}`);
    }
  }
  return { exact_source: true, file_count: sourceFiles.size };
}

function assertExactControlPlaneAdapter(sourceRoot, packagedRoot) {
  if (!sourceRoot || !fs.existsSync(sourceRoot)) {
    throw new Error(`control-plane adapter source root is missing: ${sourceRoot || "<empty>"}`);
  }
  if (!packagedRoot || !fs.existsSync(packagedRoot)) {
    throw new Error(`packaged control-plane adapter root is missing: ${packagedRoot || "<empty>"}`);
  }
  const packagedNames = fs.readdirSync(packagedRoot).sort();
  const expectedNames = [...CONTROL_PLANE_ADAPTER_FILES].sort();
  if (JSON.stringify(packagedNames) !== JSON.stringify(expectedNames)) {
    throw new Error("packaged control-plane adapter has an unexpected file set");
  }
  for (const file of CONTROL_PLANE_ADAPTER_FILES) {
    const source = path.join(sourceRoot, file);
    const packaged = path.join(packagedRoot, file);
    if (!fs.statSync(source).isFile() || !fs.statSync(packaged).isFile()) {
      throw new Error(`control-plane adapter file is missing or not regular: ${file}`);
    }
    if (sha256File(source) !== sha256File(packaged)) {
      throw new Error(`packaged control-plane adapter source mismatch: ${file}`);
    }
  }
  return { exact_source: true, file_count: CONTROL_PLANE_ADAPTER_FILES.length };
}

async function afterPack(context) {
  if (context?.electronPlatformName !== "win32") {
    return;
  }
  await configureWindowsFuses(context);
  const sourceResourcesRoot = path.resolve(__dirname, "..", "resources");
  const packagedResourcesRoot = path.join(context.appOutDir, "resources", "resources");
  assertExactPackagedResources(sourceResourcesRoot, packagedResourcesRoot, {
    separatelyVerifiedTopLevelDirectories: ["control-plane"],
  });
  assertExactControlPlaneAdapter(
    path.resolve(__dirname, "..", "control-plane", "control_plane"),
    path.join(context.appOutDir, "resources", "resources", "control-plane")
  );
}

exports.default = afterPack;
exports.assertSanitizedPackagedResources = assertSanitizedPackagedResources;
exports.assertExactPackagedResources = assertExactPackagedResources;
exports.assertExactControlPlaneAdapter = assertExactControlPlaneAdapter;
exports.assertRunAsNode = assertRunAsNode;
exports.configureWindowsFuses = configureWindowsFuses;
exports.forbiddenReason = forbiddenReason;
exports.SANCTIONED_CODING_MCP_RUNTIME_FILES = SANCTIONED_CODING_MCP_RUNTIME_FILES;
exports.CONTROL_PLANE_ADAPTER_FILES = CONTROL_PLANE_ADAPTER_FILES;
