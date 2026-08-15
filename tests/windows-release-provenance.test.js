"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const {
  computeProofId,
  finalizeProvenanceObject,
  validateProvenance,
} = require("../scripts/windows-release-provenance");

function fixture() {
  return {
    schema_version: 1,
    kind: "tools-codex-web.windows_release_candidate_provenance",
    generated_at_utc: "2026-08-15T00:00:00.000Z",
    source: {
      git_sha: "1234567890abcdef1234567890abcdef12345678",
      git_tree: "abcdef1234567890abcdef1234567890abcdef12",
      worktree_clean: true,
      exact_source: true,
    },
    versions: {
      desktop_app: "0.3.4",
      coding_tools_mcp: "0.4.1",
      webcodex_npm: "0.3.5",
    },
    native: {
      platform: "win32-x64",
      build_identity: "0.3.5 (commit 1234567890ab, dirty=false, built_at=1)",
      archive: {
        name: "webcodex-v0.3.5-win32-x64.tar.gz",
        size_bytes: 4096,
        sha256: "a".repeat(64),
      },
      binaries: {
        "webcodex.exe": { size_bytes: 1000, sha256: "b".repeat(64) },
        "webcodex-server.exe": { size_bytes: 1100, sha256: "c".repeat(64) },
        "webcodex-runner.exe": { size_bytes: 1200, sha256: "d".repeat(64) },
      },
    },
    package: {
      source_archive: { name: "npm-package-source.zip", size_bytes: 2000, sha256: "e".repeat(64) },
      npm_tarball: { name: "yyjeqhc-webcodex-0.3.5.tgz", size_bytes: 3000, sha256: "f".repeat(64) },
    },
    release: {
      native_packaging_mode: "development",
      publishable: false,
    },
    proof: {
      name: "windows_artifact_to_npm_install_smoke",
      status: "passed",
      artifact_rehash_sha256: "a".repeat(64),
      npm_tarball_rehash_sha256: "f".repeat(64),
    },
  };
}

test("finalized Windows provenance is exact-source, content-bound, and timestamp-independent", () => {
  const first = finalizeProvenanceObject(fixture(), { requireExactSource: true });
  assert.match(first.proof_id, /^sha256:[a-f0-9]{64}$/);
  assert.equal(first.proof_id, computeProofId(first));
  assert.equal(validateProvenance(first, { requireExactSource: true }), true);

  const later = fixture();
  later.generated_at_utc = "2030-01-01T00:00:00.000Z";
  assert.equal(finalizeProvenanceObject(later, { requireExactSource: true }).proof_id, first.proof_id);

  first.package.npm_tarball.sha256 = "0".repeat(64);
  assert.throws(() => validateProvenance(first, { requireExactSource: true }), /npm tarball bytes changed|proof_id/);
});

test("exact-source gate and development publishability fail closed", () => {
  const notExact = fixture();
  notExact.source.exact_source = false;
  assert.throws(() => finalizeProvenanceObject(notExact, { requireExactSource: true }), /exact-source proof requires/);

  const publishableDevelopment = fixture();
  publishableDevelopment.release.publishable = true;
  assert.throws(() => finalizeProvenanceObject(publishableDevelopment), /must never be publishable/);

  const wrongCommit = fixture();
  wrongCommit.native.build_identity = "0.3.5 (commit ffffffffffff, dirty=false, built_at=1)";
  assert.throws(() => finalizeProvenanceObject(wrongCommit, { requireExactSource: true }), /binary commit must match/);
});

test("Windows CI requires and uploads exact-source provenance", () => {
  const root = path.resolve(__dirname, "..");
  const workflow = fs.readFileSync(path.join(root, ".github", "workflows", "ci.yml"), "utf8");
  const smoke = fs.readFileSync(path.join(root, "scripts", "npm_install_windows_smoke.ps1"), "utf8");
  const packager = fs.readFileSync(path.join(root, "scripts", "package_release_artifact.ps1"), "utf8");
  assert.match(workflow, /npm_install_windows_smoke\.ps1[^\n]*-RequireExactSource[^\n]*-ProvenanceOut/);
  assert.match(workflow, /windows-release-provenance-\$\{\{ github\.sha \}\}/);
  assert.match(workflow, /cargo test --locked[^\n]*-p webcodex-workspace/);
  assert.match(smoke, /windows-release-provenance\.js/);
  assert.match(smoke, /npm_tarball_rehash_sha256/);
  assert.match(packager, /exact_source/);
  assert.match(packager, /build_identity/);
});
