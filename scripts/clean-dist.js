"use strict";

const fs = require("node:fs");
const path = require("node:path");

function cleanDistRoot(projectRoot = path.resolve(__dirname, "..")) {
  const distRoot = path.join(path.resolve(projectRoot), "dist");
  fs.rmSync(distRoot, {
    recursive: true,
    force: true,
    maxRetries: process.platform === "win32" ? 10 : 0,
    retryDelay: process.platform === "win32" ? 100 : 0,
  });
  return distRoot;
}

if (require.main === module) cleanDistRoot();

module.exports = { cleanDistRoot };
