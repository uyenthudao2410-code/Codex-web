"use strict";

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

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

function forbiddenReason(relativePath, isDirectory) {
  const normalized = relativePath.split(path.sep).join("/");
  const parts = normalized.split("/").filter(Boolean);
  if (parts[0] === "coding-tools-mcp" && DEV_ONLY_CODING_MCP_DIRECTORIES.has(parts[1])) {
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

function collectAllowedFiles(root, { source = false } = {}) {
  const resolvedRoot = path.resolve(root);
  const files = new Map();
  const stack = [resolvedRoot];
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolute = path.join(current, entry.name);
      const relative = path.relative(resolvedRoot, absolute);
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
      const normalized = relative.split(path.sep).join("/");
      const stat = fs.statSync(absolute);
      files.set(normalized, { size: stat.size, sha256: sha256File(absolute) });
    }
  }
  return files;
}

function assertExactPackagedResources(sourceResourcesRoot, packagedResourcesRoot) {
  if (!sourceResourcesRoot || !fs.existsSync(sourceResourcesRoot)) {
    throw new Error(`source resources root is missing: ${sourceResourcesRoot || "<empty>"}`);
  }
  assertSanitizedPackagedResources(packagedResourcesRoot);
  const sourceFiles = collectAllowedFiles(sourceResourcesRoot, { source: true });
  const packagedFiles = collectAllowedFiles(packagedResourcesRoot);
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

async function afterPack(context) {
  if (context?.electronPlatformName !== "win32") {
    return;
  }
  const sourceResourcesRoot = path.resolve(__dirname, "..", "resources");
  const packagedResourcesRoot = path.join(context.appOutDir, "resources", "resources");
  assertExactPackagedResources(sourceResourcesRoot, packagedResourcesRoot);
}

exports.default = afterPack;
exports.assertSanitizedPackagedResources = assertSanitizedPackagedResources;
exports.assertExactPackagedResources = assertExactPackagedResources;
exports.forbiddenReason = forbiddenReason;
