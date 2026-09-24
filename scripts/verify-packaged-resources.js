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
  "%SystemDrive%",
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
const MXC_EXEC_SHA256 = "6049c64723af1173c3739dc6cd6b2f33f6c021bb2832c4216233cba7f71aee9a";
const MXC_EXEC_SIGNER = "CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US";
const MXC_WSB_SOURCE_COMMIT = "cbe1774364ea2ec846f56ab744e43a416f751420";
const MXC_WSB_LOCAL_PATCH_SHA256 = "85a0991dd4473b31574ad6c71d2c489389e6719a3e6ef9116f5f9156a7b7c8df";
const MXC_WSB_BINARY_NAMES = Object.freeze([
  "wxc-exec.exe",
  "wxc-windows-sandbox-daemon.exe",
  "wxc-windows-sandbox-guest.exe"
]);

function assertMxcWindowsExecutor(resourcesRoot, { spawnSyncFn = spawnSync } = {}) {
  const executable = path.join(path.resolve(resourcesRoot), "tools", "wxc-exec.exe");
  if (!fs.existsSync(executable) || !fs.statSync(executable).isFile()) {
    throw new Error("bundled Microsoft MXC Windows executor is missing");
  }
  const sha256 = sha256File(executable);
  if (sha256 !== MXC_EXEC_SHA256) {
    throw new Error("bundled Microsoft MXC Windows executor does not match the pinned binary");
  }
  if (process.platform === "win32") {
    const systemRoot = process.env.SystemRoot || process.env.WINDIR || "C:\\Windows";
    const nativePowerShellRoot = path.join(systemRoot, "System32", "WindowsPowerShell", "v1.0");
    const powershellLiteral = value => `'${String(value).replace(/'/g, "''")}'`;
    const script = `$s=Get-AuthenticodeSignature -LiteralPath ${powershellLiteral(executable)}; if ($s.Status.ToString() -ne ${powershellLiteral("Valid")} -or $s.SignerCertificate.Subject -ne ${powershellLiteral(MXC_EXEC_SIGNER)}) { exit 1 }`;
    const encodedScript = Buffer.from(script, "utf16le").toString("base64");
    const result = spawnSyncFn(path.join(nativePowerShellRoot, "powershell.exe"), [
      "-NoProfile", "-NonInteractive", "-EncodedCommand", encodedScript
    ], {
      env: {
        ...process.env,
        PSModulePath: path.join(nativePowerShellRoot, "Modules")
      },
      windowsHide: true,
      encoding: "utf8",
      timeout: 10_000
    });
    if (result?.error || result?.status !== 0) {
      throw new Error("bundled Microsoft MXC Windows executor signature is not valid");
    }
  }
  return { executable, sha256, authenticode_verified: process.platform === "win32" };
}

function assertMxcWindowsSandboxCandidate(resourcesRoot) {
  const directory = path.join(path.resolve(resourcesRoot), "tools", "mxc-windows-sandbox");
  if (!fs.existsSync(directory)) return null;
  const provenancePath = path.join(directory, "mxc-windows-sandbox.provenance.json");
  let provenance;
  try {
    provenance = JSON.parse(fs.readFileSync(provenancePath, "utf8"));
  } catch {
    throw new Error("MXC Windows Sandbox candidate provenance is missing or invalid");
  }
  const expectedKeys = "authenticode,backend,binaries,build_profile,component,distribution,experimental,license,lifecycle,local_patch_file,local_patch_sha256,mxc_crate_version,rustc,schema_version,source_commit,source_commit_signature,source_repository,target";
  if (!provenance || typeof provenance !== "object" || Array.isArray(provenance)
    || Object.keys(provenance).sort().join(",") !== expectedKeys
    || provenance.component !== "Microsoft MXC Windows Sandbox state-aware candidate"
    || provenance.source_repository !== "https://github.com/microsoft/mxc"
    || provenance.source_commit !== MXC_WSB_SOURCE_COMMIT
    || provenance.local_patch_file !== "scripts/patches/mxc-windows-sandbox-c-drive-share.patch"
    || provenance.local_patch_sha256 !== MXC_WSB_LOCAL_PATCH_SHA256
    || provenance.source_commit_signature !== "unsigned"
    || provenance.mxc_crate_version !== "0.8.0"
    || provenance.schema_version !== "0.10.0-alpha"
    || provenance.backend !== "windows_sandbox"
    || provenance.lifecycle !== "state-aware"
    || provenance.experimental !== true
    || provenance.build_profile !== "release"
    || provenance.target !== "x86_64-pc-windows-msvc"
    || provenance.authenticode !== "unsigned-local-source-build"
    || provenance.distribution !== "development-candidate-only"
    || provenance.license !== "MIT"
    || typeof provenance.rustc !== "string"
    || Object.keys(provenance.binaries || {}).sort().join(",") !== [...MXC_WSB_BINARY_NAMES].sort().join(",")) {
    throw new Error("MXC Windows Sandbox candidate provenance does not match the pinned development build");
  }
  const hashes = {};
  for (const name of MXC_WSB_BINARY_NAMES) {
    const file = path.join(directory, name);
    let stat;
    let sha256;
    try {
      stat = fs.statSync(file);
      if (!stat.isFile()) throw new Error("not-file");
      sha256 = sha256File(file);
    } catch {
      throw new Error(`MXC Windows Sandbox candidate binary is missing: ${name}`);
    }
    const receipt = provenance.binaries[name];
    if (!receipt || typeof receipt !== "object" || Array.isArray(receipt)
      || Object.keys(receipt).sort().join(",") !== "sha256,size_bytes"
      || !/^[a-f0-9]{64}$/.test(String(receipt.sha256 || ""))
      || !Number.isSafeInteger(receipt.size_bytes) || receipt.size_bytes <= 0
      || stat.size !== receipt.size_bytes || sha256 !== receipt.sha256) {
      throw new Error(`MXC Windows Sandbox candidate binary hash mismatch: ${name}`);
    }
    hashes[name] = sha256;
  }
  return Object.freeze({
    directory,
    source_commit: MXC_WSB_SOURCE_COMMIT,
    local_patch_sha256: MXC_WSB_LOCAL_PATCH_SHA256,
    hashes: Object.freeze(hashes)
  });
}

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
  assertMxcWindowsExecutor(sourceResourcesRoot);
  const mxcWindowsSandboxCandidate = assertMxcWindowsSandboxCandidate(sourceResourcesRoot);
  if (mxcWindowsSandboxCandidate && process.env.CODEX_ALLOW_MXC_WSB_DEV_CANDIDATE !== "1") {
    throw new Error("unsigned experimental MXC Windows Sandbox binaries are development-candidate-only; set CODEX_ALLOW_MXC_WSB_DEV_CANDIDATE=1 only for the unpacked dev build");
  }
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
exports.assertMxcWindowsExecutor = assertMxcWindowsExecutor;
exports.assertMxcWindowsSandboxCandidate = assertMxcWindowsSandboxCandidate;
exports.forbiddenReason = forbiddenReason;
exports.SANCTIONED_CODING_MCP_RUNTIME_FILES = SANCTIONED_CODING_MCP_RUNTIME_FILES;
exports.CONTROL_PLANE_ADAPTER_FILES = CONTROL_PLANE_ADAPTER_FILES;
