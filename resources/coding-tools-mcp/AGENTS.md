# AGENTS.md — Coding Tools MCP package

## Module layout

`coding_tools_mcp/server.py` is the composition root: `Runtime` class declaration,
lifecycle, dispatch, and the remaining HTTP/stdio entry points. Feature code lives
in the module that owns its domain:

| Domain | Module |
| --- | --- |
| File/search/patch tools | `file_tools.py` (FileToolsMixin) |
| Exec/verify/command policy | `exec_tools.py` (ExecToolsMixin) |
| Git tools | `git_tools.py` (GitToolsMixin) |
| Session output control | `session_control.py` (SessionControlMixin) |
| Document tools | `document_tools.py` (DocumentToolsMixin) |
| Task-state tools | `task_state.py` (TaskStateToolsMixin) |
| Candidate packet generation | `agent_candidate.py` (AgentCandidateMixin) |
| Context preparation | `context_tools.py` (ContextToolsMixin) |
| Agent workflow | `workflow_tools.py` (AgentWorkflowMixin) |
| Coordination lanes + task_control | `coordination.py` (CoordinationMixin) |
| HTTP transport | `mcp_http_handler.py`, `transport_http.py` |
| Tool schemas/validation | `tool_schema.py` |
| Command parsing | `command_parse.py` |
| Env/runtime config | `runtime_config.py` |
| Filesystem helpers | `fs_utils.py` |
| Landlock | `landlock_exec.py` |
| Process/session primitives | `processes.py` |
| Audit ledger | `orchestration_ledger.py` |

## Module-size rules

- `server.py` line budget: **3,500** (currently ~2,900). New tool behavior goes in
  the owning mixin module, not in `Runtime` body.
- Generic module budget: **1,600** lines. `orchestration_ledger.py` budget: **5,000**
  (canonical audit source; split it before adding another subsystem).
- Constants move with the code that uses them. If `server.py` still needs a moved
  name, re-export it (`from .module import NAME`) to keep the public namespace
  stable — tests and external importers depend on `coding_tools_mcp.server`.
- Mixin modules must not import from `server.py` (circular). They import leaf
  modules only; cross-cluster calls happen through `self`.
- Enforce with `python resources/coding-tools-mcp/scripts/check_module_size.py`
  (wired into CI). To raise a budget, add an explicit ALLOWLIST entry with a
  named reason.

## Validation

- Full suite: `python -m pytest tests/` from `resources/coding-tools-mcp`.
- After any extraction, run the suite; import-time NameErrors in moved code are
  the common failure mode. Re-export any moved constant the tests still patch or
  read through `coding_tools_mcp.server`.
