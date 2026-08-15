"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const SCHEMA_VERSION = 1;
const KIND = "tools-codex-web.windows_release_candidate_provenance";
const SHA256_RE = /^[a-f0-9]{64}$/;
const GIT_OBJECT_RE = /^[a-f0-9]{40}$/;
const SEMVER_RE = /^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;
const BINARIES = Object.freeze(["webcodex.exe", "webcodex-server.exe", "webcodex-runner.exe"]);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function requireSha(value, label) {
  assert(typeof value === "string" && SHA256_RE.test(value), `${label} must be a lowercase SHA-256`);
  return value;
}

function requireGitObject(value, label) {
  assert(typeof value === "string" && GIT_OBJECT_RE.test(value), `${label} must be a full lowercase Git object id`);
  return value;
}

function requirePositiveInteger(value, label) {
  assert(Number.isSafeInteger(value) && value > 0, `${label} must be a positive integer`);
  return value;
}

function requireSemver(value, label) {
  assert(typeof value === "string" && SEMVER_RE.test(value), `${label} must be a semantic version`);
  return value;
}

function canonicalEvidence(provenance) {
  const source = provenance.source || {};
  const versions = provenance.versions || {};
  const native = provenance.native || {};
  const binaries = native.binaries || {};
  const packageEvidence = provenance.package || {};
  const release = provenance.release || {};
  const proof = provenance.proof || {};
  const canonicalBinaries = {};
  for (const name of BINARIES) {
    const binary = binaries[name] || {};
    canonicalBinaries[name] = {
      size_bytes: binary.size_bytes,
      sha256: binary.sha256,
    };
  }
  return {
    schema_version: provenance.schema_version,
    kind: provenance.kind,
    source: {
      git_sha: source.git_sha,
      git_tree: source.git_tree,
      worktree_clean: source.worktree_clean,
      exact_source: source.exact_source,
    },
    versions: {
      desktop_app: versions.desktop_app,
      coding_tools_mcp: versions.coding_tools_mcp,
      webcodex_npm: versions.webcodex_npm,
    },
    native: {
      platform: native.platform,
      build_identity: native.build_identity,
      archive: {
        name: native.archive && native.archive.name,
        size_bytes: native.archive && native.archive.size_bytes,
        sha256: native.archive && native.archive.sha256,
      },
      binaries: canonicalBinaries,
    },
    package: {
      source_archive: {
        name: packageEvidence.source_archive && packageEvidence.source_archive.name,
        size_bytes: packageEvidence.source_archive && packageEvidence.source_archive.size_bytes,
        sha256: packageEvidence.source_archive && packageEvidence.source_archive.sha256,
      },
      npm_tarball: {
        name: packageEvidence.npm_tarball && packageEvidence.npm_tarball.name,
        size_bytes: packageEvidence.npm_tarball && packageEvidence.npm_tarball.size_bytes,
        sha256: packageEvidence.npm_tarball && packageEvidence.npm_tarball.sha256,
      },
    },
    release: {
      native_packaging_mode: release.native_packaging_mode,
      publishable: release.publishable,
    },
    proof: {
      name: proof.name,
      status: proof.status,
      artifact_rehash_sha256: proof.artifact_rehash_sha256,
      npm_tarball_rehash_sha256: proof.npm_tarball_rehash_sha256,
    },
  };
}

function computeProofId(provenance) {
  const bytes = Buffer.from(JSON.stringify(canonicalEvidence(provenance)), "utf8");
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

function validateProvenance(provenance, { requireExactSource = false } = {}) {
  assert(isPlainObject(provenance), "provenance must be an object");
  assert(provenance.schema_version === SCHEMA_VERSION, `schema_version must be ${SCHEMA_VERSION}`);
  assert(provenance.kind === KIND, `kind must be ${KIND}`);

  const source = provenance.source;
  assert(isPlainObject(source), "source must be an object");
  requireGitObject(source.git_sha, "source.git_sha");
  requireGitObject(source.git_tree, "source.git_tree");
  assert(typeof source.worktree_clean === "boolean", "source.worktree_clean must be boolean");
  assert(typeof source.exact_source === "boolean", "source.exact_source must be boolean");
  if (requireExactSource) {
    assert(source.worktree_clean, "exact-source proof requires a clean worktree");
    assert(source.exact_source, "exact-source proof requires source.exact_source=true");
  }

  const versions = provenance.versions;
  assert(isPlainObject(versions), "versions must be an object");
  requireSemver(versions.desktop_app, "versions.desktop_app");
  requireSemver(versions.coding_tools_mcp, "versions.coding_tools_mcp");
  requireSemver(versions.webcodex_npm, "versions.webcodex_npm");

  const native = provenance.native;
  assert(isPlainObject(native), "native must be an object");
  assert(native.platform === "win32-x64", "native.platform must be win32-x64");
  assert(typeof native.build_identity === "string" && native.build_identity.length > 0, "native.build_identity is required");
  assert(isPlainObject(native.archive), "native.archive must be an object");
  assert(typeof native.archive.name === "string" && native.archive.name.endsWith("-win32-x64.tar.gz"), "native.archive.name must be the Windows artifact");
  requirePositiveInteger(native.archive.size_bytes, "native.archive.size_bytes");
  requireSha(native.archive.sha256, "native.archive.sha256");
  assert(isPlainObject(native.binaries), "native.binaries must be an object");
  assert(
    JSON.stringify(Object.keys(native.binaries).sort()) === JSON.stringify([...BINARIES].sort()),
    "native.binaries must contain exactly the three release binaries"
  );
  for (const name of BINARIES) {
    const binary = native.binaries[name];
    assert(isPlainObject(binary), `native.binaries.${name} must be an object`);
    requirePositiveInteger(binary.size_bytes, `native.binaries.${name}.size_bytes`);
    requireSha(binary.sha256, `native.binaries.${name}.sha256`);
  }

  const commitMatch = native.build_identity.match(/\(commit ([0-9A-Fa-f]{12,40})(?:,|\))/);
  if (source.exact_source) {
    assert(commitMatch, "exact-source binary identity must contain a concrete commit");
    assert(source.git_sha.startsWith(commitMatch[1].toLowerCase()), "binary commit must match source.git_sha");
    assert(/, dirty=false(?:,|\))/.test(native.build_identity), "exact-source binary identity must report dirty=false");
  }

  const packageEvidence = provenance.package;
  assert(isPlainObject(packageEvidence), "package must be an object");
  for (const key of ["source_archive", "npm_tarball"]) {
    const item = packageEvidence[key];
    assert(isPlainObject(item), `package.${key} must be an object`);
    assert(typeof item.name === "string" && item.name.length > 0, `package.${key}.name is required`);
    requirePositiveInteger(item.size_bytes, `package.${key}.size_bytes`);
    requireSha(item.sha256, `package.${key}.sha256`);
  }

  const release = provenance.release;
  assert(isPlainObject(release), "release must be an object");
  assert(["development", "release"].includes(release.native_packaging_mode), "release.native_packaging_mode is invalid");
  assert(typeof release.publishable === "boolean", "release.publishable must be boolean");
  if (release.native_packaging_mode === "development") {
    assert(release.publishable === false, "development smoke provenance must never be publishable");
  }

  const proof = provenance.proof;
  assert(isPlainObject(proof), "proof must be an object");
  assert(proof.name === "windows_artifact_to_npm_install_smoke", "proof.name is invalid");
  assert(proof.status === "passed", "proof.status must be passed");
  requireSha(proof.artifact_rehash_sha256, "proof.artifact_rehash_sha256");
  requireSha(proof.npm_tarball_rehash_sha256, "proof.npm_tarball_rehash_sha256");
  assert(proof.artifact_rehash_sha256 === native.archive.sha256, "artifact bytes changed after packaging");
  assert(proof.npm_tarball_rehash_sha256 === packageEvidence.npm_tarball.sha256, "npm tarball bytes changed after smoke install");

  if (provenance.proof_id !== undefined) {
    assert(/^sha256:[a-f0-9]{64}$/.test(provenance.proof_id), "proof_id must be a typed SHA-256");
    assert(provenance.proof_id === computeProofId(provenance), "proof_id does not match the canonical evidence");
  }
  return true;
}

function finalizeProvenanceObject(provenance, options = {}) {
  const result = JSON.parse(JSON.stringify(provenance));
  delete result.proof_id;
  validateProvenance(result, options);
  result.proof_id = computeProofId(result);
  validateProvenance(result, options);
  return result;
}

function atomicWriteJson(file, value) {
  const target = path.resolve(file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const temp = `${target}.tmp-${process.pid}`;
  fs.writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temp, target);
}

function main(argv = process.argv.slice(2)) {
  const action = argv[0];
  const file = argv[1];
  const requireExactSource = argv.includes("--require-exact-source");
  if (!file || !["finalize", "validate"].includes(action)) {
    throw new Error("usage: node scripts/windows-release-provenance.js <finalize|validate> <file> [--require-exact-source]");
  }
  const provenance = JSON.parse(fs.readFileSync(path.resolve(file), "utf8"));
  if (action === "finalize") {
    const finalized = finalizeProvenanceObject(provenance, { requireExactSource });
    atomicWriteJson(file, finalized);
    process.stdout.write(`${finalized.proof_id}\n`);
    return finalized;
  }
  validateProvenance(provenance, { requireExactSource });
  process.stdout.write(`${provenance.proof_id || computeProofId(provenance)}\n`);
  return provenance;
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(error && error.message ? error.message : String(error));
    process.exitCode = 1;
  }
}

module.exports = {
  BINARIES,
  KIND,
  SCHEMA_VERSION,
  canonicalEvidence,
  computeProofId,
  finalizeProvenanceObject,
  validateProvenance,
};
