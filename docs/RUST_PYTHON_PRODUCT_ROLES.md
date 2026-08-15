# Rust / Python Product Roles

**Observed source baseline:** `main` / `dff81e251836666fc825c40bf86e4167afd29c39`  
**Audit date:** 2026-08-15  
**Purpose:** keep runtime ownership, release gates, and CI scope explicit. This is a product-role contract, not a deprecation plan.

## 1. Authority boundary

The desktop product hot path is:

```text
Electron supervisor
  -> one Coding Tools MCP Python runtime
  -> Smart-v3 / EOCL / write lease / deterministic proof
```

Rust does **not** own a second desktop mutation authority. The Rust WebCodex server/runtime remains a separately shipped product/runtime and an optional authenticated native capability provider. The Python native-semantic adapter is default-off and may bind only to the project-scoped, read-only Rust Connector boundary.

## 2. Product-role matrix

| Subsystem / package | Runtime role | Release role | Why it exists / concrete consumer | CI policy |
|---|---|---|---|---|
| Electron desktop | **PRODUCTION** | **RELEASE-GATE** | Starts and supervises the Python Coding Tools MCP desktop runtime. | Root Node/Electron tests; Windows desktop integration. |
| Python Coding Tools MCP | **PRODUCTION** | **RELEASE-GATE** | Desktop execution hot path; Smart-v3, EOCL, task state, proof, routing telemetry. | Full Python MCP suite in canonical CI; focused tests for changed behavior. |
| root `webcodex` / `webcodex-server` | **PRODUCTION on Linux/server**, **SUPPORTING for optional native semantic path** | **RELEASE-GATE** | Real Linux/server runtime; owns ToolRuntime + Connector/LSP boundary. `webcodex-server` is also one of the three npm native binaries. The Windows artifact keeps this binary for the package contract, but that does not declare long-running Windows Server support. | Full Linux workspace proof. Do not add the root Server test suite to Windows merely because the binary is packaged. |
| `webcodex-cli` | **PRODUCTION / published client** | **RELEASE-GATE** | Produces the public `webcodex` binary and discovers package-local Server/Runner binaries. | Linux workspace; direct Windows package tests; npm smoke. |
| `webcodex-runner` | **PRODUCTION / published runner** | **RELEASE-GATE** | Published Runner binary; agent execution and LSP service used by WebCodex runtime paths. | Linux workspace; direct Windows package tests; npm smoke. |
| `webcodex-admin` | **SUPPORTING** | **TRANSITIVE RELEASE-GATE** | Used by root Server and CLI admin flows. No Windows-specific source branch observed in the role audit. | Linux workspace tests; compile transitively on Windows. Add a direct Windows gate only if Windows-specific behavior is introduced. |
| `webcodex-agent-config` | **SUPPORTING** | **TRANSITIVE RELEASE-GATE** | Shared configuration/path policy used by Server, CLI, and Runner. | Linux workspace; direct Windows package tests. |
| `webcodex-core` | **SUPPORTING shared core** | **TRANSITIVE RELEASE-GATE** | Shared build identity, LSP bridge, validation/sensitive-path primitives used by Server/CLI/Runner. Current Windows-path checks are platform-independent string handling rather than `cfg(windows)` implementations. | Linux workspace tests; compile transitively on Windows. Revisit direct Windows tests if platform-specific implementation appears. |
| `webcodex-persistent-shell` | **SUPPORTING runtime primitive** | **TRANSITIVE RELEASE-GATE** | Used by Server and Runner; includes fail-closed/platform process behavior. | Linux workspace; direct Windows package tests. |
| `webcodex-process` | **SUPPORTING runner primitive** | **TRANSITIVE RELEASE-GATE** | Runner process-tree/job-object lifecycle, including Windows-specific implementation. | Linux workspace; direct Windows package tests. |
| `webcodex-sandbox` | **SUPPORTING security primitive** | **TRANSITIVE RELEASE-GATE** | Used by Server and Runner; Linux Landlock implementation is explicitly target-specific. | Linux workspace tests. Compile transitively on Windows; no reason to force Linux Landlock tests into Windows. |
| `webcodex-workspace` | **SUPPORTING workspace/identity primitive** | **TRANSITIVE RELEASE-GATE** | Used by Server/Runner and owns the portable project-root identity required by the authenticated Python <-> Rust semantic bridge. The normalization has a real `cfg(windows)` implementation. | Linux workspace plus **direct Windows package tests**. Windows drive/extended-UNC normalization has focused tests. |
| npm `@yyjeqhc/webcodex` | **DISTRIBUTION** | **RELEASE-GATE** | Thin installer/wrapper for exactly three native binaries: `webcodex`, `webcodex-server`, `webcodex-runner`. | Native package tests + exact-source artifact-to-npm-install smoke. |

## 3. Why canonical Linux CI remains full-workspace

`cargo metadata --no-deps --format-version 1` shows that every Rust workspace package is in the dependency closure of the three native binaries or the real Linux Server runtime. In particular:

- root Server depends on `admin`, `agent-config`, `core`, `persistent-shell`, `sandbox`, and `workspace`;
- CLI depends on root Server library plus `admin`, `agent-config`, and `core`;
- Runner depends on `agent-config`, `core`, `persistent-shell`, `process`, `sandbox`, and `workspace`.

Therefore there is no source-grounded package that can currently be labeled dead/reference-only and removed from canonical Linux `cargo test --locked --workspace` merely to shorten CI. Any future reduction requires a real dependency/product-role change first.

## 4. Why Windows CI remains selected, not full-workspace

Windows is a published client + Runner platform. The direct package test set is intentionally narrower than Linux and should cover Windows-specific or Windows-material behavior:

```text
webcodex-agent-config
webcodex-process
webcodex-persistent-shell
webcodex-workspace
webcodex-cli
webcodex-runner
```

The root Server suite remains Linux-only because the product does not claim a long-running Windows Server runtime. `webcodex-admin`, `webcodex-core`, and `webcodex-sandbox` still compile transitively when the shipped binaries are built; their current role audit found no separate Windows implementation that justifies a direct Windows package-test gate. If such code is added later, the selected list must be revisited.

## 5. Release invariant

The npm distribution contract remains exactly:

```text
webcodex
webcodex-server
webcodex-runner
```

The Windows exact-source smoke builds and packages those three binaries from one source identity, verifies their shared build identity/checksums, installs the npm tarball offline, and rehashes the same candidate bytes. Packaging `webcodex-server.exe` on Windows is a distribution compatibility invariant, not authority to start a second desktop runtime.

## 6. Semantic-bridge consequence

The authenticated native semantic bridge depends on Rust `ToolRuntime`/Connector plus `webcodex-workspace` portable root identity. This remains an **optional read-only accelerator** beneath the Python MCP authority boundary. Its live activation still requires a real project-bound Rust Connector URL and project credential; tests or CI scope must not fabricate that production binding.

## 7. Change rule

Before removing a Rust package, broadening/narrowing CI, or moving authority between Python and Rust, require all three:

1. dependency evidence showing the package is no longer needed by a shipped/runtime path;
2. release evidence showing the package/binary is no longer part of the published contract;
3. an explicit owner/authority decision that does not create a second mutation plane.

Until then, optimize CI within these roles rather than treating implementation-language overlap as proof of duplication.
