//! Conservative model-facing success projection.
//!
//! Projection context is captured from the typed request before execution, but
//! the projection itself is applied by `kernel` only after business-session and
//! outer recording-session evidence has consumed the complete `ToolResult`.
//! Failures, partial results, non-default requests, and uncertain execution
//! outcomes are deliberately left byte-for-byte unchanged.

use super::{ToolCall, ToolResult};
use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ModelResultProjection {
    None,
    Read { default_request: bool, batch: bool },
    Search { default_request: bool, batch: bool },
    StructuredExecution,
}

impl ModelResultProjection {
    pub(crate) fn from_tool_call(call: &ToolCall) -> Self {
        match call {
            ToolCall::ReadFile { start_line, limit, with_line_numbers, .. } => Self::Read {
                default_request: start_line.is_none() && limit.is_none() && !with_line_numbers.unwrap_or(false),
                batch: false,
            },
            ToolCall::ReadFiles { items, with_line_numbers, .. } => Self::Read {
                default_request: !with_line_numbers.unwrap_or(false)
                    && items.iter().all(|item| item.start_line.is_none() && item.limit.is_none()),
                batch: true,
            },
            ToolCall::SearchProjectText {
                path, limit, context_before, context_after, include_globs, exclude_globs,
                result_mode, timeout_secs, ..
            } => Self::Search {
                default_request: path.is_none() && limit.is_none() && context_before.is_none()
                    && context_after.is_none() && include_globs.is_none() && exclude_globs.is_none()
                    && result_mode.is_none() && timeout_secs.is_none(),
                batch: false,
            },
            ToolCall::SearchProjectTexts { queries, .. } => Self::Search {
                default_request: queries.iter().all(|query| {
                    query.path.is_none() && query.limit.is_none() && query.context_before.is_none()
                        && query.context_after.is_none() && query.include_globs.is_none()
                        && query.exclude_globs.is_none() && query.result_mode.is_none()
                        && query.timeout_secs.is_none()
                }),
                batch: true,
            },
            ToolCall::RunProcess { .. } | ToolCall::RunScript { .. } => Self::StructuredExecution,
            _ => Self::None,
        }
    }

    pub(crate) fn apply(self, result: &mut ToolResult) {
        match self {
            Self::None => {}
            Self::Read { default_request, batch } => sparsify_complete_read_success(result, default_request, batch),
            Self::Search { default_request, batch } => sparsify_complete_default_search_success(result, default_request, batch),
            Self::StructuredExecution => sparsify_terminal_structured_execution_success(result),
        }
    }
}

pub(crate) fn sparsify_complete_read_success(result: &mut ToolResult, default_request: bool, batch: bool) {
    if !default_request || !result.success { return; }
    if batch {
        if !complete_read_batch(&result.output) { return; }
        if let Some(items) = result.output.get_mut("items").and_then(Value::as_array_mut) {
            for item in items {
                if let Some(output) = item.get_mut("output") { sparsify_complete_read_value(output); }
            }
        }
        remove_keys(&mut result.output, &["succeeded_count", "failed_count", "output_truncated", "next_index"]);
    } else if complete_read_value(&result.output) {
        sparsify_complete_read_value(&mut result.output);
    }
}

fn complete_read_batch(output: &Value) -> bool {
    if output.get("output_truncated").and_then(Value::as_bool) != Some(false)
        || !value_is_null_or_missing(output, "next_index")
        || output.get("failed_count").and_then(Value::as_u64) != Some(0) { return false; }
    let Some(requested) = output.get("requested_count").and_then(Value::as_u64) else { return false; };
    if output.get("returned_count").and_then(Value::as_u64) != Some(requested)
        || output.get("succeeded_count").and_then(Value::as_u64) != Some(requested) { return false; }
    let Some(items) = output.get("items").and_then(Value::as_array) else { return false; };
    items.len() as u64 == requested && items.iter().all(|item| {
        item.get("success").and_then(Value::as_bool) == Some(true)
            && value_is_null_or_missing(item, "error")
            && item.get("output").is_some_and(complete_read_value)
    })
}

fn complete_read_value(output: &Value) -> bool {
    let Some(total_lines) = output.get("total_lines").and_then(Value::as_u64) else { return false; };
    output.get("text").and_then(Value::as_str).is_some()
        && output.get("sha256").and_then(Value::as_str).is_some_and(|hash| !hash.is_empty())
        && output.get("format").and_then(Value::as_str) == Some("plain")
        && output.get("start_line").and_then(Value::as_u64) == Some(1)
        && output.get("returned_lines").and_then(Value::as_u64) == Some(total_lines)
        && output.get("has_more").and_then(Value::as_bool) == Some(false)
        && value_is_null_or_missing(output, "next_start_line")
}

fn sparsify_complete_read_value(output: &mut Value) {
    remove_keys(output, &["start_line", "limit", "returned_lines", "end_line", "has_more", "next_start_line", "format"]);
}

pub(crate) fn sparsify_complete_default_search_success(result: &mut ToolResult, default_request: bool, batch: bool) {
    if !default_request || !result.success { return; }
    if batch {
        if !complete_default_search_batch(&result.output) { return; }
        if let Some(items) = result.output.get_mut("items").and_then(Value::as_array_mut) {
            for item in items {
                if let Some(output) = item.get_mut("output") { sparsify_complete_default_search_value(output); }
            }
        }
        remove_keys(&mut result.output, &["succeeded_count", "failed_count", "output_truncated", "next_index"]);
    } else if complete_default_search_value(&result.output) {
        sparsify_complete_default_search_value(&mut result.output);
    }
}

fn complete_default_search_batch(output: &Value) -> bool {
    if output.get("output_truncated").and_then(Value::as_bool) != Some(false)
        || !value_is_null_or_missing(output, "next_index")
        || output.get("failed_count").and_then(Value::as_u64) != Some(0) { return false; }
    let Some(requested) = output.get("requested_count").and_then(Value::as_u64) else { return false; };
    if output.get("returned_count").and_then(Value::as_u64) != Some(requested)
        || output.get("succeeded_count").and_then(Value::as_u64) != Some(requested) { return false; }
    let Some(items) = output.get("items").and_then(Value::as_array) else { return false; };
    items.len() as u64 == requested && items.iter().all(|item| {
        item.get("success").and_then(Value::as_bool) == Some(true)
            && value_is_null_or_missing(item, "error")
            && item.get("output").is_some_and(complete_default_search_value)
    })
}

fn complete_default_search_value(output: &Value) -> bool {
    let Some(matches) = output.get("matches").and_then(Value::as_array) else { return false; };
    let Some(count) = output.get("count").and_then(Value::as_u64) else { return false; };
    let Some(exit_code) = output.get("exit_code").and_then(Value::as_i64) else { return false; };
    let exit_consistent = if count == 0 { exit_code == 0 || exit_code == 1 } else { exit_code == 0 };
    output.get("backend").and_then(Value::as_str) == Some("rg")
        && output.get("result_mode").and_then(Value::as_str) == Some("matches")
        && output.get("path").and_then(Value::as_str) == Some(".")
        && output.get("context_before").and_then(Value::as_u64) == Some(0)
        && output.get("context_after").and_then(Value::as_u64) == Some(0)
        && output.get("effective_timeout_secs").and_then(Value::as_u64).is_some_and(|timeout| timeout > 0)
        && output.get("truncated").and_then(Value::as_bool) == Some(false)
        && value_is_null_or_missing(output, "truncation_reason")
        && output.get("fallback").and_then(Value::as_bool) != Some(true)
        && count == matches.len() as u64 && exit_consistent
}

fn sparsify_complete_default_search_value(output: &mut Value) {
    remove_keys(output, &["backend", "result_mode", "effective_timeout_secs", "exit_code", "context_before", "context_after", "truncated", "truncation_reason"]);
}

pub(crate) fn sparsify_terminal_structured_execution_success(result: &mut ToolResult) {
    if !result.success || !safe_terminal_structured_execution_success(&result.output) { return; }
    remove_keys(&mut result.output, &["failure_kind", "tool_failure", "promoted_to_job", "job_id", "job_status"]);
}

fn safe_terminal_structured_execution_success(output: &Value) -> bool {
    output.get("command_started").and_then(Value::as_bool) == Some(true)
        && output.get("command_completed").and_then(Value::as_bool) == Some(true)
        && output.get("command_ok").and_then(Value::as_bool) == Some(true)
        && output.get("execution_state").and_then(Value::as_str) == Some("completed")
        && output.get("exit_code").and_then(Value::as_i64) == Some(0)
        && value_is_null_or_missing(output, "failure_kind")
        && output.get("tool_failure").and_then(Value::as_bool) == Some(false)
        && output.get("promoted_to_job").and_then(Value::as_bool) == Some(false)
        && output.get("terminal").and_then(Value::as_bool) == Some(true)
        && value_is_null_or_missing(output, "job_id")
        && value_is_null_or_missing(output, "job_status")
        && output.get("retry_safe").and_then(Value::as_bool) != Some(false)
        && output.get("outcome").and_then(Value::as_str).map_or(true, |outcome| outcome == "success")
}

fn value_is_null_or_missing(output: &Value, key: &str) -> bool {
    output.get(key).map_or(true, Value::is_null)
}

fn remove_keys(output: &mut Value, keys: &[&str]) {
    let Some(object) = output.as_object_mut() else { return; };
    for key in keys { object.remove(*key); }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn complete_read_output(path: &str) -> Value {
        json!({"path": path, "text": "one\ntwo\n", "sha256": "0123456789abcdef", "total_lines": 2, "start_line": 1, "limit": 2000, "returned_lines": 2, "end_line": 2, "has_more": false, "next_start_line": null, "format": "plain"})
    }

    fn complete_search_output() -> Value {
        json!({"project": "demo", "pattern": "needle", "path": ".", "backend": "rg", "result_mode": "matches", "effective_timeout_secs": 10, "exit_code": 0, "context_before": 0, "context_after": 0, "count": 1, "matches": [{"path": "src/lib.rs", "line": 1, "preview": "needle", "context_before": [], "context_after": []}], "truncated": false, "truncation_reason": null})
    }

    #[test]
    fn sparsify_complete_read_success_only_for_whole_file() {
        let mut complete = ToolResult::ok(complete_read_output("src/lib.rs"));
        sparsify_complete_read_success(&mut complete, true, false);
        assert_eq!(complete.output["text"], json!("one\ntwo\n"));
        assert_eq!(complete.output["sha256"], json!("0123456789abcdef"));
        assert_eq!(complete.output["total_lines"], json!(2));
        assert!(complete.output.get("start_line").is_none());
        assert!(complete.output.get("has_more").is_none());
        let mut partial = ToolResult::ok(complete_read_output("src/lib.rs"));
        partial.output["returned_lines"] = json!(1);
        partial.output["has_more"] = json!(true);
        partial.output["next_start_line"] = json!(2);
        let before_partial = partial.output.clone();
        sparsify_complete_read_success(&mut partial, true, false);
        assert_eq!(partial.output, before_partial);
        let mut nondefault = ToolResult::ok(complete_read_output("src/lib.rs"));
        let before_nondefault = nondefault.output.clone();
        sparsify_complete_read_success(&mut nondefault, false, false);
        assert_eq!(nondefault.output, before_nondefault);
        let mut batch = ToolResult::ok(json!({"project": "demo", "requested_count": 2, "returned_count": 2, "succeeded_count": 2, "failed_count": 0, "items": [{"index": 0, "path": "a.rs", "success": true, "output": complete_read_output("a.rs"), "error": null}, {"index": 1, "path": "b.rs", "success": true, "output": complete_read_output("b.rs"), "error": null}], "output_truncated": false, "next_index": null}));
        sparsify_complete_read_success(&mut batch, true, true);
        assert!(batch.output["items"][0]["output"].get("start_line").is_none());
        assert!(batch.output.get("failed_count").is_none());
    }

    #[test]
    fn sparsify_complete_default_search_success_preserves_nondefault_states() {
        let mut complete = ToolResult::ok(complete_search_output());
        sparsify_complete_default_search_success(&mut complete, true, false);
        assert_eq!(complete.output["count"], json!(1));
        assert!(complete.output.get("backend").is_none());
        assert!(complete.output.get("truncated").is_none());
        for (key, value) in [("backend", json!("grep")), ("truncated", json!(true)), ("context_before", json!(1)), ("fallback", json!(true))] {
            let mut preserved = ToolResult::ok(complete_search_output());
            preserved.output[key] = value;
            let before = preserved.output.clone();
            sparsify_complete_default_search_success(&mut preserved, true, false);
            assert_eq!(preserved.output, before, "state {key} must remain complete");
        }
        let mut nondefault = ToolResult::ok(complete_search_output());
        let before = nondefault.output.clone();
        sparsify_complete_default_search_success(&mut nondefault, false, false);
        assert_eq!(nondefault.output, before);
        let mut batch = ToolResult::ok(json!({"project": "demo", "requested_count": 1, "returned_count": 1, "succeeded_count": 1, "failed_count": 0, "items": [{"index": 0, "pattern": "needle", "success": true, "output": complete_search_output(), "error": null}], "output_truncated": false, "next_index": null}));
        sparsify_complete_default_search_success(&mut batch, true, true);
        assert!(batch.output["items"][0]["output"].get("backend").is_none());
        assert!(batch.output.get("failed_count").is_none());
    }

    #[test]
    fn sparsify_terminal_structured_execution_success_rejects_unsafe_outcomes() {
        let base = json!({"project": "demo", "cwd": ".", "executor": "local", "purpose": "validation", "exit_code": 0, "stdout_tail": "ok", "stderr_tail": "", "stdout_lines": 1, "stderr_lines": 0, "stdout_truncated": false, "stderr_truncated": false, "duration_ms": 5, "command_started": true, "command_completed": true, "command_ok": true, "execution_state": "completed", "failure_kind": null, "tool_failure": false, "promoted_to_job": false, "terminal": true, "job_id": null, "job_status": null, "effective_timeout_secs": 10, "sync_wait_secs": 10, "async_handoff_available": true});
        let mut complete = ToolResult::ok(base.clone());
        sparsify_terminal_structured_execution_success(&mut complete);
        for preserved in ["command_started", "command_completed", "command_ok", "execution_state", "terminal", "stdout_tail", "stderr_tail", "cwd", "executor", "purpose"] {
            assert!(complete.output.get(preserved).is_some(), "missing {preserved}");
        }
        for redundant in ["failure_kind", "tool_failure", "promoted_to_job", "job_id", "job_status"] {
            assert!(complete.output.get(redundant).is_none(), "retained {redundant}");
        }
        for (key, value) in [("execution_state", json!("outcome_unknown")), ("promoted_to_job", json!(true)), ("exit_code", json!(1)), ("retry_safe", json!(false))] {
            let mut unsafe_result = ToolResult::ok(base.clone());
            unsafe_result.output[key] = value;
            let before = unsafe_result.output.clone();
            sparsify_terminal_structured_execution_success(&mut unsafe_result);
            assert_eq!(unsafe_result.output, before, "unsafe state {key} must remain complete");
        }
    }
}
