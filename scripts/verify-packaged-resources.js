"use strict";

const fs = require("node:fs");
const path = require("node:path");

const FORBIDDEN_DIRECTORY_NAMES = new Set([
  "__pycache__",
  ".pytest_cache",
  ".coding-tools",
]);

function forbiddenReason(relativePath, isDirectory) {
  const normalized = relativePath.split(path.sep).join("/");
  const parts = normalized.split("/").filter(Boolean);
  if (parts.some((part) => FORBIDDEN_DIRECTORY_NAMES.has(part))) {
    return "volatile runtime/cache directory";
  }
  if (parts.some((part) => part.endsWith(".egg-info"))) {
    return "Python packaging metadata";
  }
  if (normalized === "coding-tools-mcp/benchmarks/reports" || normalized.startsWith("coding-tools-mcp/benchmarks/reports/")) {
    return "raw benchmark/runtime report";
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

async function afterPack(context) {
  if (context?.electronPlatformName !== "win32") {
    return;
  }
  const packagedResourcesRoot = path.join(context.appOutDir, "resources", "resources");
  assertSanitizedPackagedResources(packagedResourcesRoot);
}

exports.default = afterPack;
exports.assertSanitizedPackagedResources = assertSanitizedPackagedResources;
exports.forbiddenReason = forbiddenReason;
