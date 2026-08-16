//! Model-hidden, project-local bridge from Coding Tools semantic localization
//! to the existing typed read-only Rust LSP runtime.

use super::projections::validate_path;
use super::{ConnectorCallOutcome, ConnectorRuntime};
use crate::auth::{AuthContext, SCOPE_PROJECT_READ};
use crate::tool_runtime::kernel::{
    ToolCallContext, ToolCallRequest as KernelToolCallRequest, ToolTransport,
};
use futures_util::stream::{self, StreamExt};
use serde::Deserialize;
use serde_json::{json, Value};
use std::path::Path;
use std::sync::atomic::Ordering;

pub(crate) const INTERNAL_SEMANTIC_ROUTE: &str = "/api/connector/internal/semantic/localize";
pub(crate) const INTERNAL_SEMANTIC_SUBPATH: &str = "internal/semantic/localize";
const MAX_SEMANTIC_QUERIES: usize = 8;
const MAX_SEMANTIC_RESULTS_PER_QUERY: usize = 50;
const MAX_DOCUMENT_SYMBOL_VISITS: usize = 1_000;
const WARM_SEMANTIC_CONCURRENCY: usize = 2;

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct SemanticLocalizeInput {
    pub workspace_sha256: String,
    #[serde(default)]
    pub path: Option<String>,
    pub queries: Vec<String>,
    #[serde(default)]
    pub max_results: Option<usize>,
}

impl ConnectorRuntime {
    pub(crate) async fn semantic_localize(
        &self,
        auth: &AuthContext,
        input: SemanticLocalizeInput,
    ) -> ConnectorCallOutcome {
        if !auth.is_project_credential()
            || auth.project_grant_id.as_deref() != Some(self.context.project_grant_id.as_str())
        {
            return ConnectorCallOutcome::error(
                403,
                "project_credential_required",
                "native semantic localization requires this project's dedicated credential",
                false,
                false,
                None,
                None,
                false,
            );
        }
        if !auth.has_scope(SCOPE_PROJECT_READ) {
            return ConnectorCallOutcome::scope_denied(SCOPE_PROJECT_READ);
        }
        if !valid_sha256(&input.workspace_sha256) {
            return invalid_semantic_input(
                "workspace_sha256 must be 64 lowercase hexadecimal characters",
            );
        }
        if input.queries.is_empty() || input.queries.len() > MAX_SEMANTIC_QUERIES {
            return invalid_semantic_input("queries must contain 1..=8 entries");
        }
        let max_results = input.max_results.unwrap_or(20);
        if !(1..=MAX_SEMANTIC_RESULTS_PER_QUERY).contains(&max_results) {
            return invalid_semantic_input("max_results must be 1..=50");
        }
        let path_scope = match normalize_scope_path(input.path.as_deref()) {
            Ok(path) => path,
            Err(message) => return invalid_semantic_input(message),
        };
        let mut queries = Vec::with_capacity(input.queries.len());
        for query in input.queries {
            let query = query.trim();
            if query.is_empty() || query.len() > 200 {
                return invalid_semantic_input("each query must be 1..=200 bytes after trimming");
            }
            queries.push(query.to_string());
        }

        let expected_workspace = match crate::project_context::portable_project_root_sha256(
            Path::new(&self.context.executor_root),
        ) {
            Ok(value) => value,
            Err(_) => {
                return ConnectorCallOutcome::error(
                    409,
                    "semantic_workspace_unavailable",
                    "the configured project workspace is unavailable",
                    true,
                    false,
                    None,
                    None,
                    false,
                )
            }
        };
        if input.workspace_sha256 != expected_workspace {
            return ConnectorCallOutcome::error(
                403,
                "semantic_workspace_mismatch",
                "the semantic request is not bound to this connector workspace",
                false,
                false,
                None,
                None,
                false,
            );
        }

        if let Some(document_path) = path_scope.as_deref().filter(|path| is_document_scope(path)) {
            let was_warm = self.semantic_lsp_warm.load(Ordering::Acquire);
            let outcome = self
                .tools
                .call_tool_with_context(
                    KernelToolCallRequest {
                        tool_name: "document_symbols".to_string(),
                        arguments: json!({
                            "project": self.context.executor_project.clone(),
                            "path": document_path,
                            "limit": MAX_SEMANTIC_RESULTS_PER_QUERY
                        }),
                    },
                    ToolCallContext {
                        transport: ToolTransport::Api,
                        session_id: None,
                        auth: Some(auth),
                        window: None,
                        record_oauth_scope_denials: false,
                    },
                )
                .await;
            if outcome.error_status.is_some() {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            }
            let Some(result) = outcome.result else {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            };
            if !result.success {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            }
            self.semantic_lsp_warm.store(true, Ordering::Release);
            let symbols = result
                .output
                .get("symbols")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or(&[]);
            let mut rows = Vec::with_capacity(queries.len());
            for (query_index, query) in queries.iter().enumerate() {
                let mut matches = Vec::new();
                collect_document_symbol_matches(
                    symbols,
                    document_path,
                    query,
                    max_results,
                    &mut matches,
                );
                rows.push(json!({
                    "query_index": query_index,
                    "query": query,
                    "handled": !matches.is_empty(),
                    "definitive": false,
                    "matches": matches
                }));
            }
            return ConnectorCallOutcome::success_project(json!({
                "schema_version": 1,
                "provider": "webcodex_native_lsp",
                "read_only": true,
                "lsp_state": if was_warm { "WARM" } else { "COLD_READY" },
                "semantic_concurrency": 1,
                "results": rows
            }));
        }

        let internal_limit = if path_scope.is_some() {
            MAX_SEMANTIC_RESULTS_PER_QUERY
        } else {
            max_results
        };
        let was_warm = self.semantic_lsp_warm.load(Ordering::Acquire);
        let concurrency = if was_warm {
            WARM_SEMANTIC_CONCURRENCY.min(queries.len())
        } else {
            1
        };
        let tools = self.tools.clone();
        let project = self.context.executor_project.clone();
        let request_auth = auth.clone();
        let calls = queries
            .iter()
            .cloned()
            .enumerate()
            .map(move |(query_index, query)| {
                let tools = tools.clone();
                let project = project.clone();
                let request_auth = request_auth.clone();
                async move {
                    let outcome = tools
                        .call_tool_with_context(
                            KernelToolCallRequest {
                                tool_name: "workspace_symbols".to_string(),
                                arguments: json!({
                                    "project": project,
                                    "query": query,
                                    "limit": internal_limit
                                }),
                            },
                            ToolCallContext {
                                transport: ToolTransport::Api,
                                session_id: None,
                                auth: Some(&request_auth),
                                window: None,
                                record_oauth_scope_denials: false,
                            },
                        )
                        .await;
                    (query_index, outcome)
                }
            });
        let mut outcomes = stream::iter(calls)
            .buffer_unordered(concurrency)
            .collect::<Vec<_>>()
            .await;
        outcomes.sort_by_key(|(query_index, _)| *query_index);

        let mut rows = Vec::with_capacity(queries.len());
        for (query_index, outcome) in outcomes {
            let query = &queries[query_index];
            if outcome.error_status.is_some() {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            }
            let Some(result) = outcome.result else {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            };
            if !result.success {
                self.semantic_lsp_warm.store(false, Ordering::Release);
                return native_lsp_unavailable();
            }

            let mut matches = Vec::new();
            for symbol in result
                .output
                .get("symbols")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                let Some(path) = symbol.get("path").and_then(Value::as_str) else {
                    continue;
                };
                if !path_in_scope(path, path_scope.as_deref()) {
                    continue;
                }
                let symbol_name = symbol.get("name").and_then(Value::as_str).unwrap_or("");
                if symbol_name.is_empty() {
                    continue;
                }
                let mut item = json!({
                    "path": path,
                    "symbol": symbol_name,
                    "kind": symbol.get("kind").and_then(Value::as_str).unwrap_or("symbol")
                });
                if let Some(start) = symbol.get("range").and_then(|range| range.get("start")) {
                    if let Some(line) = start.get("line").and_then(Value::as_u64) {
                        item["line"] = json!(line);
                    }
                    if let Some(column) = start.get("column").and_then(Value::as_u64) {
                        item["column"] = json!(column);
                    }
                }
                matches.push(item);
                if matches.len() >= max_results {
                    break;
                }
            }
            rows.push(json!({
                "query_index": query_index,
                "query": query,
                "handled": !matches.is_empty(),
                "definitive": false,
                "matches": matches
            }));
        }
        self.semantic_lsp_warm.store(true, Ordering::Release);

        ConnectorCallOutcome::success_project(json!({
            "schema_version": 1,
            "provider": "webcodex_native_lsp",
            "read_only": true,
            "lsp_state": if was_warm { "WARM" } else { "COLD_READY" },
            "semantic_concurrency": concurrency,
            "results": rows
        }))
    }
}

fn invalid_semantic_input(message: impl Into<String>) -> ConnectorCallOutcome {
    ConnectorCallOutcome::error(
        400,
        "invalid_arguments",
        message,
        false,
        false,
        None,
        None,
        true,
    )
}

fn native_lsp_unavailable() -> ConnectorCallOutcome {
    ConnectorCallOutcome::error(
        409,
        "native_lsp_unavailable",
        "native read-only LSP semantic localization is unavailable for this project",
        true,
        false,
        None,
        None,
        false,
    )
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn normalize_scope_path(raw: Option<&str>) -> Result<Option<String>, &'static str> {
    let Some(raw) = raw else {
        return Ok(None);
    };
    let normalized = raw.trim().replace('\\', "/");
    if normalized.is_empty() || normalized == "." {
        return Ok(None);
    }
    let normalized = normalized.trim_end_matches('/').to_string();
    validate_path(&normalized)?;
    Ok(Some(normalized))
}

fn path_in_scope(path: &str, scope: Option<&str>) -> bool {
    let Some(scope) = scope else {
        return true;
    };
    path == scope
        || path
            .strip_prefix(scope)
            .is_some_and(|suffix| suffix.starts_with('/'))
}

fn is_document_scope(path: &str) -> bool {
    let extension = Path::new(path)
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    matches!(
        extension.as_str(),
        "rs" | "py" | "pyi" | "ts" | "mts" | "cts" | "tsx" | "js" | "mjs" | "cjs" | "jsx"
    )
}

fn collect_document_symbol_matches(
    symbols: &[Value],
    path: &str,
    query: &str,
    max_results: usize,
    matches: &mut Vec<Value>,
) {
    let query = query.to_lowercase();
    let mut stack = symbols.iter().rev().collect::<Vec<_>>();
    let mut visited = 0usize;
    while let Some(symbol) = stack.pop() {
        if visited >= MAX_DOCUMENT_SYMBOL_VISITS {
            return;
        }
        visited += 1;
        if matches.len() >= max_results {
            return;
        }
        let name = symbol.get("name").and_then(Value::as_str).unwrap_or("");
        if !name.is_empty() && name.to_lowercase().contains(&query) {
            let mut item = json!({
                "path": path,
                "symbol": name,
                "kind": symbol.get("kind").and_then(Value::as_str).unwrap_or("symbol")
            });
            let start = symbol
                .get("selection_range")
                .or_else(|| symbol.get("range"))
                .and_then(|range| range.get("start"));
            if let Some(start) = start {
                if let Some(line) = start.get("line").and_then(Value::as_u64) {
                    item["line"] = json!(line);
                }
                if let Some(column) = start.get("column").and_then(Value::as_u64) {
                    item["column"] = json!(column);
                }
            }
            matches.push(item);
        }
        if let Some(children) = symbol.get("children").and_then(Value::as_array) {
            stack.extend(children.iter().rev());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::auth::{AuthContext, AuthKind};
    use crate::connector_runtime::tests::{auth, connector, PROJECT_CREDENTIAL};
    use crate::lsp_bridge::{
        AgentLspRequest, AgentLspResultEnvelope, PublicWorkspaceSymbol, WorkspaceSymbolsResult,
    };
    use crate::shell_protocol::{
        ShellAgentPollRequest, ShellAgentProjectSummary, ShellAgentResultRequest,
        ShellClientCapabilities, ShellClientRegisterRequest,
    };

    async fn register_semantic_agent(connector: &ConnectorRuntime, lsp_capable: bool) {
        connector
            .tools
            .shell_clients
            .register_with_auth(
                ShellClientRegisterRequest {
                    process_started_at: None,
                    build: None,
                    job_concurrency_limit: None,
                    job_inventory: None,
                    client_id: "hosted".to_string(),
                    agent_instance_id: "semantic-instance".to_string(),
                    display_name: None,
                    owner: Some("owner".to_string()),
                    hostname: None,
                    capabilities: Some(ShellClientCapabilities {
                        shell: true,
                        lsp_read_only_navigation: lsp_capable,
                        ..Default::default()
                    }),
                    projects: Some(vec![ShellAgentProjectSummary {
                        id: "demo".to_string(),
                        name: Some("demo".to_string()),
                        path: connector.context.executor_root.clone(),
                        allow_patch: true,
                        kind: Some("auto".to_string()),
                        description: None,
                        hooks: Vec::new(),
                        disabled: false,
                        revision: None,
                        git_branch: Some("main".to_string()),
                        git_head: None,
                        git_dirty: Some(false),
                        updated_at: 1,
                        shell_profile: None,
                    }]),
                    agent_protocol_version: Some("polling-v1".to_string()),
                    policy: None,
                },
                Some(&auth("u1")),
            )
            .await
            .unwrap();
    }

    fn valid_input(connector: &ConnectorRuntime) -> SemanticLocalizeInput {
        SemanticLocalizeInput {
            workspace_sha256: crate::project_context::portable_project_root_sha256(Path::new(
                &connector.context.executor_root,
            ))
            .unwrap(),
            path: Some("src".to_string()),
            queries: vec!["ToolRuntime".to_string()],
            max_results: Some(10),
        }
    }

    async fn complete_workspace_symbol_request(
        registry: &crate::shell_client::ShellClientRegistry,
        request: crate::shell_protocol::ShellAgentShellRequest,
    ) {
        let request_id = request.request_id;
        let payload = request.lsp.expect("typed LSP payload");
        let AgentLspRequest::WorkspaceSymbols { query, .. } = payload.request else {
            panic!("expected workspace symbols request");
        };
        let result = WorkspaceSymbolsResult {
            project: "demo".to_string(),
            query,
            symbols: Vec::new(),
            total_results: 0,
            returned_count: 0,
            truncated: false,
            external_results_omitted: 0,
            invalid_results_omitted: 0,
        };
        registry
            .complete(ShellAgentResultRequest {
                client_id: "hosted".to_string(),
                agent_instance_id: "semantic-instance".to_string(),
                request_id,
                exit_code: Some(0),
                stdout: Some(AgentLspResultEnvelope::ok(result).to_stdout_json()),
                stderr: Some(String::new()),
                duration_ms: Some(1),
                error: None,
            })
            .await
            .unwrap();
    }

    #[tokio::test]
    async fn native_semantic_bridge_rejects_wrong_authority_and_workspace() {
        let (_temp, connector) = connector();
        let input = valid_input(&connector);

        let wrong_grant = connector
            .semantic_localize(&auth("u2"), input.clone())
            .await;
        assert_eq!(wrong_grant.http_status, 403);
        assert_eq!(
            wrong_grant.body["error"]["code"],
            "project_credential_required"
        );

        let mut bootstrap = AuthContext::new(AuthKind::Bootstrap);
        bootstrap.is_bootstrap = true;
        let bootstrap = connector.semantic_localize(&bootstrap, input.clone()).await;
        assert_eq!(bootstrap.http_status, 403);
        assert_eq!(
            bootstrap.body["error"]["code"],
            "project_credential_required"
        );

        let mut wrong_workspace = input;
        wrong_workspace.workspace_sha256 = "0".repeat(64);
        let wrong_workspace = connector
            .semantic_localize(&auth("u1"), wrong_workspace)
            .await;
        assert_eq!(wrong_workspace.http_status, 403);
        assert_eq!(
            wrong_workspace.body["error"]["code"],
            "semantic_workspace_mismatch"
        );
        assert!(!wrong_workspace
            .body
            .to_string()
            .contains(&connector.context.executor_root));
    }

    #[tokio::test]
    async fn native_semantic_bridge_fails_closed_when_lsp_capability_is_unavailable() {
        let (_temp, connector) = connector();
        register_semantic_agent(&connector, false).await;
        let outcome = connector
            .semantic_localize(&auth("u1"), valid_input(&connector))
            .await;
        assert_eq!(outcome.http_status, 409);
        assert_eq!(outcome.body["error"]["code"], "native_lsp_unavailable");
    }

    #[tokio::test]
    async fn native_semantic_bridge_returns_only_normalized_project_relative_matches() {
        let (_temp, connector) = connector();
        register_semantic_agent(&connector, true).await;
        let registry = connector.tools.shell_clients.clone();
        let responder = tokio::spawn(async move {
            let request = loop {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    break request;
                }
                tokio::task::yield_now().await;
            };
            assert_eq!(request.kind, "lsp");
            let payload = request.lsp.expect("typed LSP payload");
            assert_eq!(payload.project_id, "demo");
            assert!(matches!(
                payload.request,
                AgentLspRequest::WorkspaceSymbols { ref query, limit }
                    if query == "ToolRuntime" && limit == MAX_SEMANTIC_RESULTS_PER_QUERY
            ));
            let result = WorkspaceSymbolsResult {
                project: "demo".to_string(),
                query: "ToolRuntime".to_string(),
                symbols: vec![
                    PublicWorkspaceSymbol {
                        name: "ToolRuntime".to_string(),
                        kind: "struct".to_string(),
                        kind_code: 23,
                        container_name: None,
                        path: "src/tool_runtime/mod.rs".to_string(),
                        range: None,
                    },
                    PublicWorkspaceSymbol {
                        name: "Outside".to_string(),
                        kind: "struct".to_string(),
                        kind_code: 23,
                        container_name: None,
                        path: "tests/outside.rs".to_string(),
                        range: None,
                    },
                ],
                total_results: 2,
                returned_count: 2,
                truncated: false,
                external_results_omitted: 0,
                invalid_results_omitted: 0,
            };
            let envelope = AgentLspResultEnvelope::ok(result).to_stdout_json();
            registry
                .complete(ShellAgentResultRequest {
                    client_id: "hosted".to_string(),
                    agent_instance_id: "semantic-instance".to_string(),
                    request_id: request.request_id,
                    exit_code: Some(0),
                    stdout: Some(envelope),
                    stderr: Some(String::new()),
                    duration_ms: Some(1),
                    error: None,
                })
                .await
                .unwrap();
        });

        let outcome = connector
            .semantic_localize(&auth("u1"), valid_input(&connector))
            .await;
        responder.await.unwrap();
        assert!(outcome.ok, "{}", outcome.body);
        assert_eq!(outcome.body["data"]["provider"], "webcodex_native_lsp");
        assert_eq!(outcome.body["data"]["results"][0]["handled"], true);
        let matches = outcome.body["data"]["results"][0]["matches"]
            .as_array()
            .unwrap();
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0]["path"], "src/tool_runtime/mod.rs");
        assert_eq!(matches[0]["symbol"], "ToolRuntime");
        let serialized = outcome.body.to_string();
        assert!(!serialized.contains("agent:hosted:demo"));
        assert!(!serialized.contains(&connector.context.executor_root));
        assert!(!serialized.contains(PROJECT_CREDENTIAL));
    }

    #[tokio::test]
    async fn native_semantic_bridge_uses_document_symbols_for_file_scope() {
        let (_temp, connector) = connector();
        register_semantic_agent(&connector, true).await;
        let registry = connector.tools.shell_clients.clone();
        let responder = tokio::spawn(async move {
            let request = loop {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    break request;
                }
                tokio::task::yield_now().await;
            };
            let request_id = request.request_id;
            let payload = request.lsp.expect("typed LSP payload");
            assert!(matches!(
                payload.request,
                AgentLspRequest::DocumentSymbols { ref path, limit }
                    if path == "src/tool_runtime/runtime.rs" && limit == MAX_SEMANTIC_RESULTS_PER_QUERY
            ));
            let result = json!({
                "project": "demo",
                "path": "src/tool_runtime/runtime.rs",
                "language": "rust",
                "symbols": [
                    {
                        "name": "ToolRuntime",
                        "kind": "struct",
                        "kind_code": 23,
                        "range": {
                            "start": {"line": 10, "column": 1},
                            "end": {"line": 20, "column": 1}
                        },
                        "selection_range": {
                            "start": {"line": 10, "column": 12},
                            "end": {"line": 10, "column": 23}
                        },
                        "children": [
                            {
                                "name": "handle_request",
                                "kind": "method",
                                "kind_code": 6,
                                "range": {
                                    "start": {"line": 14, "column": 5},
                                    "end": {"line": 16, "column": 5}
                                },
                                "selection_range": {
                                    "start": {"line": 14, "column": 8},
                                    "end": {"line": 14, "column": 22}
                                },
                                "children": []
                            }
                        ]
                    },
                    {
                        "name": "Unrelated",
                        "kind": "function",
                        "kind_code": 12,
                        "range": {
                            "start": {"line": 30, "column": 1},
                            "end": {"line": 31, "column": 1}
                        },
                        "selection_range": {
                            "start": {"line": 30, "column": 4},
                            "end": {"line": 30, "column": 13}
                        },
                        "children": []
                    }
                ],
                "total_count": 2,
                "returned_count": 2,
                "truncated": false,
                "external_results_omitted": 0,
                "invalid_results_omitted": 0
            });
            registry
                .complete(ShellAgentResultRequest {
                    client_id: "hosted".to_string(),
                    agent_instance_id: "semantic-instance".to_string(),
                    request_id,
                    exit_code: Some(0),
                    stdout: Some(AgentLspResultEnvelope::ok(result).to_stdout_json()),
                    stderr: Some(String::new()),
                    duration_ms: Some(1),
                    error: None,
                })
                .await
                .unwrap();
        });

        let mut input = valid_input(&connector);
        input.path = Some("src/tool_runtime/runtime.rs".to_string());
        input.queries = vec![
            "ToolRuntime".to_string(),
            "Unrelated".to_string(),
            "handle_request".to_string(),
        ];
        let outcome = connector.semantic_localize(&auth("u1"), input).await;
        responder.await.unwrap();
        assert!(outcome.ok, "{}", outcome.body);
        let rows = outcome.body["data"]["results"].as_array().unwrap();
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[0]["query"], "ToolRuntime");
        assert_eq!(rows[0]["handled"], true);
        let first_matches = rows[0]["matches"].as_array().unwrap();
        assert_eq!(first_matches.len(), 1);
        assert_eq!(first_matches[0]["path"], "src/tool_runtime/runtime.rs");
        assert_eq!(first_matches[0]["symbol"], "ToolRuntime");
        assert_eq!(first_matches[0]["line"], 10);
        assert_eq!(first_matches[0]["column"], 12);
        assert_eq!(rows[1]["query"], "Unrelated");
        assert_eq!(rows[1]["handled"], true);
        let second_matches = rows[1]["matches"].as_array().unwrap();
        assert_eq!(second_matches.len(), 1);
        assert_eq!(second_matches[0]["symbol"], "Unrelated");
        assert_eq!(rows[2]["query"], "handle_request");
        assert_eq!(rows[2]["handled"], true);
        assert_eq!(rows[2]["matches"][0]["symbol"], "handle_request");
        assert_eq!(rows[2]["matches"][0]["line"], 14);
    }

    #[tokio::test]
    async fn native_semantic_bridge_cold_workspace_queries_are_serial() {
        let (_temp, connector) = connector();
        register_semantic_agent(&connector, true).await;
        let registry = connector.tools.shell_clients.clone();
        let responder = tokio::spawn(async move {
            let first = loop {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    break request;
                }
                tokio::task::yield_now().await;
            };
            assert!(registry
                .poll(ShellAgentPollRequest {
                    client_id: "hosted".to_string(),
                    agent_instance_id: "semantic-instance".to_string(),
                    projects: None,
                })
                .await
                .unwrap()
                .is_none());
            complete_workspace_symbol_request(&registry, first).await;

            let second = loop {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    break request;
                }
                tokio::task::yield_now().await;
            };
            complete_workspace_symbol_request(&registry, second).await;
        });

        let mut input = valid_input(&connector);
        input.path = None;
        input.queries = vec!["ToolRuntime".to_string(), "LspSupervisor".to_string()];
        let outcome = connector.semantic_localize(&auth("u1"), input).await;
        responder.await.unwrap();

        assert!(outcome.ok, "{}", outcome.body);
        assert_eq!(outcome.body["data"]["lsp_state"], "COLD_READY");
        assert_eq!(outcome.body["data"]["semantic_concurrency"], 1);
    }

    #[tokio::test]
    async fn native_semantic_bridge_warm_workspace_queries_are_bounded_and_ordered() {
        let (_temp, connector) = connector();
        register_semantic_agent(&connector, true).await;
        connector.semantic_lsp_warm.store(true, Ordering::Release);
        let registry = connector.tools.shell_clients.clone();
        let responder = tokio::spawn(async move {
            let mut requests = Vec::new();
            while requests.len() < 2 {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    requests.push(request);
                } else {
                    tokio::task::yield_now().await;
                }
            }
            assert!(registry
                .poll(ShellAgentPollRequest {
                    client_id: "hosted".to_string(),
                    agent_instance_id: "semantic-instance".to_string(),
                    projects: None,
                })
                .await
                .unwrap()
                .is_none());
            complete_workspace_symbol_request(&registry, requests.remove(0)).await;
            let third = loop {
                if let Some(request) = registry
                    .poll(ShellAgentPollRequest {
                        client_id: "hosted".to_string(),
                        agent_instance_id: "semantic-instance".to_string(),
                        projects: None,
                    })
                    .await
                    .unwrap()
                {
                    break request;
                }
                tokio::task::yield_now().await;
            };
            complete_workspace_symbol_request(&registry, requests.remove(0)).await;
            complete_workspace_symbol_request(&registry, third).await;
        });

        let mut input = valid_input(&connector);
        input.path = None;
        input.queries = vec![
            "ToolRuntime".to_string(),
            "LspSupervisor".to_string(),
            "ConnectorRuntime".to_string(),
        ];
        let outcome = connector.semantic_localize(&auth("u1"), input).await;
        responder.await.unwrap();

        assert!(outcome.ok, "{}", outcome.body);
        assert_eq!(outcome.body["data"]["lsp_state"], "WARM");
        assert_eq!(outcome.body["data"]["semantic_concurrency"], 2);
        let results = outcome.body["data"]["results"].as_array().unwrap();
        assert_eq!(results.len(), 3);
        assert_eq!(results[0]["query"], "ToolRuntime");
        assert_eq!(results[1]["query"], "LspSupervisor");
        assert_eq!(results[2]["query"], "ConnectorRuntime");
    }
}
