"use strict";

const fs = require("node:fs");
const path = require("node:path");

if (process.platform !== "win32") {
  process.stderr.write("The local Windows Sandbox dev candidate must be built on Windows.\n");
  process.exit(2);
}

const candidateTag = process.argv[2] || "r5";
if (!/^[a-z0-9][a-z0-9-]{0,31}$/.test(candidateTag)) {
  process.stderr.write("Candidate tag must contain only lowercase letters, digits, and hyphens.\n");
  process.exit(2);
}

const outputDirectory = path.resolve(
  __dirname,
  "..",
  "dist",
  `windows-candidate-mxc-wsb-cbe1774-${candidateTag}`
);
if (fs.existsSync(outputDirectory)) {
  process.stderr.write(`Refusing to overwrite existing dev-candidate output: ${outputDirectory}; choose a new candidate tag.\n`);
  process.exit(2);
}

// The MXC Windows Sandbox binaries are an unsigned, experimental local source
// build. Only the unpacked developer candidate opts into packaging them; the
// normal installer/release path remains fail-closed in afterPack.
process.env.CODEX_ALLOW_MXC_WSB_DEV_CANDIDATE = "1";

const builder = require("electron-builder");
if (!builder || typeof builder.build !== "function") {
  process.stderr.write("electron-builder build API is unavailable.\n");
  process.exit(2);
}

process.stdout.write(`Building unpacked Windows dev candidate into ${outputDirectory}\n`);
builder.build({
  dir: true,
  config: {
    directories: { output: outputDirectory }
  }
}).catch((error) => {
  const message = `Unpacked Windows dev candidate build failed: ${String(error?.message || error)}\n`;
  process.stderr.write(message, () => process.exit(1));
});
