//! Non-default integration harness for the R3B2 dirty-source snapshot flow.
//! Wired only by the `internal-r3b2-test-support` feature in a later checkpoint.

use crate::shell_client::{ShellClientRegistry, ShellJobStartMetadata, ShellJobVisibility};
use crate::shell_protocol::{
    ShellAgentJobUpdateRequest, ShellAgentPollRequest, ShellAgentProjectSummary,
    ShellAgentResultRequest, ShellAgentShellRequest, ShellClientCapabilities,
    ShellClientRegisterRequest, ShellJobOpRequest, ShellJobValidationMetadata,
    ShellJobValidationProgress, ShellJobValidationSourceSnapshotIdentity, ShellJobValidationStep,
};
use crate::tool_runtime::{RuntimeInfo, ToolRuntime};
use std::sync::Arc;
use std::time::Duration;
use webcodex_core::source_snapshot::{
    SourceSnapshotAgentPayloadV1, SourceSnapshotEntryV1, SourceSnapshotV1,
    SOURCE_SNAPSHOT_AGENT_REQUEST_KIND,
};

const PROJECT_ID: &str = "agent-proj";
const PROJECT_PATH: &str = "/tmp/agent-proj";
const SNAPSHOT_MARKER: &str = "snapshot_test_marker";

fn require(ok: bool, message: impl Into<String>) -> Result<(), String> {
    if ok {
        Ok(())
    } else {
        Err(message.into())
    }
}

fn runtime(wait: Duration) -> ToolRuntime {
    let mut runtime = ToolRuntime::new(
        Arc::new(ShellClientRegistry::default()),
        Arc::new(RuntimeInfo::default()),
    );
    runtime.validation_sync_wait = wait;
    runtime
}

fn project(head: &str, dirty: bool) -> ShellAgentProjectSummary {
    ShellAgentProjectSummary {
        id: PROJECT_ID.into(),
        name: Some(PROJECT_ID.into()),
        path: PROJECT_PATH.into(),
        allow_patch: true,
        kind: Some("repo".into()),
        description: None,
        hooks: Vec::new(),
        disabled: false,
        revision: None,
        git_branch: None,
        git_head: Some(head.into()),
        git_dirty: Some(dirty),
        updated_at: 123,
        shell_profile: None,
    }
}

fn caps(server_compute: bool) -> ShellClientCapabilities {
    ShellClientCapabilities {
        async_shell_jobs: true,
        structured_validation_argv: true,
        exact_source_validation: true,
        source_snapshot_validation: true,
        server_compute,
        ..Default::default()
    }
}

async fn register(
    runtime: &ToolRuntime,
    id: &str,
    p: ShellAgentProjectSummary,
    compute: bool,
    limit: usize,
) -> Result<(), String> {
    runtime
        .shell_clients
        .register_with_auth_connection(
            ShellClientRegisterRequest {
                process_started_at: None,
                build: None,
                job_concurrency_limit: Some(limit),
                job_inventory: None,
                client_id: id.into(),
                agent_instance_id: "inst".into(),
                display_name: None,
                owner: None,
                hostname: None,
                capabilities: Some(caps(compute)),
                projects: Some(vec![p]),
                agent_protocol_version: Some("polling-v1".into()),
                policy: None,
            },
            None,
            None,
        )
        .await?;
    Ok(())
}

fn runtime_project(id: &str) -> String {
    crate::tool_runtime::agent_project_runtime_id(id, PROJECT_ID)
}

async fn poll(runtime: &ToolRuntime, id: &str) -> Result<Option<ShellAgentShellRequest>, String> {
    runtime
        .shell_clients
        .poll(ShellAgentPollRequest {
            client_id: id.into(),
            agent_instance_id: "inst".into(),
            projects: None,
        })
        .await
}

async fn wait_request(runtime: &ToolRuntime, id: &str) -> Result<ShellAgentShellRequest, String> {
    for _ in 0..200 {
        if let Some(request) = poll(runtime, id).await? {
            return Ok(request);
        }
        tokio::time::sleep(Duration::from_millis(5)).await;
    }
    Err(format!("agent request was not enqueued for {id}"))
}

fn snapshot(head: &str) -> Result<SourceSnapshotV1, String> {
    SourceSnapshotV1::from_entries(
        head,
        vec![SourceSnapshotEntryV1::upsert(
            "src/lib.rs",
            b"pub fn snapshot_test_marker() -> u8 { 7 }\n",
            false,
        )?],
    )
}

async fn complete_capture(
    runtime: &ToolRuntime,
    id: &str,
    request_id: &str,
    source: &SourceSnapshotV1,
) -> Result<(), String> {
    runtime
        .shell_clients
        .complete(ShellAgentResultRequest {
            client_id: id.into(),
            agent_instance_id: "inst".into(),
            request_id: request_id.into(),
            exit_code: Some(0),
            stdout: Some(serde_json::to_string(source).map_err(|e| e.to_string())?),
            stderr: None,
            duration_ms: Some(5),
            error: None,
        })
        .await
}

async fn complete_job(
    runtime: &ToolRuntime,
    id: &str,
    request: &ShellAgentShellRequest,
) -> Result<(), String> {
    let job_id = request
        .job_id
        .as_deref()
        .ok_or("validation request missing job_id")?;
    runtime
        .shell_clients
        .update_job(ShellAgentJobUpdateRequest {
            client_id: id.into(),
            agent_instance_id: "inst".into(),
            update_seq: None,
            job_id: job_id.into(),
            request_id: Some(request.request_id.clone()),
            status: "completed".into(),
            stdout_chunk: None,
            stderr_chunk: None,
            stdout_tail: Some("Finished `dev` profile\n".into()),
            stderr_tail: Some(String::new()),
            log_snapshot: None,
            exit_code: Some(0),
            duration_ms: Some(25),
            error: None,
            command_execution_state: None,
            validation_progress: Some(ShellJobValidationProgress {
                completed: 1,
                current_step: None,
                failed_step: None,
            }),
            finished: true,
        })
        .await?;
    Ok(())
}

fn spawn_check(
    runtime: ToolRuntime,
    id: &str,
) -> tokio::task::JoinHandle<crate::tool_runtime::ToolResult> {
    let project = runtime_project(id);
    tokio::spawn(async move {
        runtime
            .cargo_check_with_context(
                project,
                None,
                None,
                None,
                None,
                None,
                None,
                Some(600),
                None,
                None,
                None,
                None,
            )
            .await
    })
}

async fn successful_target_dispatch() -> Result<(), String> {
    let source = "r3b2-harness-source";
    let target = "r3b2-harness-target";
    let head = "4123456789abcdef0123456789abcdef01234567";
    let runtime = runtime(Duration::from_millis(300));
    register(&runtime, source, project(head, true), false, 1).await?;
    register(&runtime, target, project(head, false), true, 2).await?;
    let task = spawn_check(runtime.clone(), source);

    let capture = wait_request(&runtime, source).await?;
    require(
        capture.kind == SOURCE_SNAPSHOT_AGENT_REQUEST_KIND,
        format!("expected capture, got {}", capture.kind),
    )?;
    require(
        capture.job_id.is_none(),
        "capture must be transient/jobless",
    )?;
    let captured: SourceSnapshotAgentPayloadV1 =
        serde_json::from_str(capture.stdin.as_deref().ok_or("capture payload missing")?)
            .map_err(|e| e.to_string())?;
    require(
        captured
            == SourceSnapshotAgentPayloadV1::Capture {
                project_id: PROJECT_ID.into(),
                expected_git_head: head.into(),
            },
        "capture project/head mismatch",
    )?;
    require(
        poll(&runtime, target).await?.is_none(),
        "target started before capture completed",
    )?;

    let source_snapshot = snapshot(head)?;
    complete_capture(&runtime, source, &capture.request_id, &source_snapshot).await?;
    let request = wait_request(&runtime, target).await?;
    require(
        request.kind == "start_validation_job",
        format!("expected validation job, got {}", request.kind),
    )?;
    let job_id = request
        .job_id
        .as_deref()
        .ok_or("target validation missing job_id")?;
    require(
        request
            .job_context
            .as_ref()
            .and_then(|c| c.runtime_project_id.as_deref())
            == Some("agent:r3b2-harness-target:agent-proj"),
        "wrong target runtime project",
    )?;
    require(
        request
            .job_context
            .as_ref()
            .and_then(|c| c.validation.as_ref())
            .and_then(|v| v.source_identity.as_ref())
            .is_none(),
        "snapshot job persisted clean source_identity",
    )?;
    let request_identity = request
        .job_context
        .as_ref()
        .and_then(|c| c.validation.as_ref())
        .and_then(|v| v.source_snapshot_identity.as_ref())
        .ok_or("snapshot Job did not retain safe source snapshot identity")?;
    require(
        request_identity.base_git_head == source_snapshot.base_git_head
            && request_identity.snapshot_sha256 == source_snapshot.snapshot_sha256
            && request_identity.entry_count == source_snapshot.entries.len(),
        "request source snapshot identity did not match captured snapshot",
    )?;
    let execute: SourceSnapshotAgentPayloadV1 = serde_json::from_str(
        request
            .stdin
            .as_deref()
            .ok_or("Execute(snapshot) missing")?,
    )
    .map_err(|e| e.to_string())?;
    require(
        execute
            == SourceSnapshotAgentPayloadV1::Execute {
                snapshot: source_snapshot.clone(),
            },
        "Execute(snapshot) mismatch",
    )?;
    let hidden = runtime
        .shell_clients
        .get_hidden_job_for_auth(None, job_id)
        .await?;
    let hidden_identity = hidden
        .validation
        .as_ref()
        .and_then(|validation| validation.source_snapshot_identity.as_ref())
        .ok_or("durable hidden Job lost source snapshot identity")?;
    require(
        hidden_identity == request_identity,
        "durable hidden Job source snapshot identity changed",
    )?;
    require(
        !serde_json::to_string(&hidden)
            .map_err(|e| e.to_string())?
            .contains(SNAPSHOT_MARKER),
        "raw snapshot leaked into durable Job",
    )?;
    require(
        poll(&runtime, source).await?.is_none(),
        "source received validation Job",
    )?;

    let handoff = task.await.map_err(|e| e.to_string())?;
    require(
        handoff.success && handoff.output["promoted_to_job"] == true,
        format!("snapshot validation did not hand off: {:?}", handoff.error),
    )?;
    let status = runtime
        .job_status_for_auth(job_id.to_string(), false, None)
        .await;
    require(
        status.success,
        "public snapshot Job status was not queryable",
    )?;
    require(
        status.output["validation"]["source_snapshot_identity"]["base_git_head"]
            == source_snapshot.base_git_head
            && status.output["validation"]["source_snapshot_identity"]["snapshot_sha256"]
                == source_snapshot.snapshot_sha256
            && status.output["validation"]["source_snapshot_identity"]["entry_count"]
                == source_snapshot.entries.len(),
        "job_status source snapshot identity mismatch",
    )?;
    let log = runtime
        .job_log_for_auth(job_id.to_string(), None, Some(200), None, None, None)
        .await;
    require(log.success, "public snapshot Job log was not queryable")?;
    require(
        log.output["validation"]["source_snapshot_identity"]
            == status.output["validation"]["source_snapshot_identity"],
        "job_log source snapshot identity mismatch",
    )?;
    complete_job(&runtime, target, &request).await?;
    let terminal = runtime
        .job_status_for_auth(job_id.to_string(), false, None)
        .await;
    require(
        terminal.success
            && terminal.output["validation"]["passed"] == true
            && terminal.output["validation"]["source_snapshot_identity"]
                == status.output["validation"]["source_snapshot_identity"],
        format!(
            "target validation terminal proof failed: {:?}",
            terminal.error
        ),
    )
}

async fn mismatched_snapshot_identity_is_rejected_before_enqueue() -> Result<(), String> {
    let target = "r3b2-harness-mismatch-target";
    let head = "7123456789abcdef0123456789abcdef01234567";
    let runtime = runtime(Duration::from_millis(20));
    register(&runtime, target, project(head, false), true, 2).await?;
    let source_snapshot = snapshot(head)?;
    let payload = serde_json::to_string(&SourceSnapshotAgentPayloadV1::Execute {
        snapshot: source_snapshot.clone(),
    })
    .map_err(|e| e.to_string())?;
    let step = ShellJobValidationStep {
        name: "check".into(),
        program: "cargo".into(),
        args: vec!["check".into()],
        env: Vec::new(),
    };
    let error = runtime
        .shell_clients
        .start_job_with_metadata(
            ShellJobOpRequest {
                op: "start".into(),
                client_id: Some(target.into()),
                cwd: Some(PROJECT_PATH.into()),
                command: Some("cargo check".into()),
                timeout_secs: Some(600),
                job_id: None,
                since_stdout_line: None,
                since_stderr_line: None,
                tail_lines: None,
                limit: None,
                codex: None,
            },
            "r3b2-harness".into(),
            ShellJobStartMetadata {
                project_id: Some(runtime_project(target)),
                validation_steps: vec![step.clone()],
                validation: Some(ShellJobValidationMetadata {
                    tool: "cargo_check".into(),
                    kind: "check".into(),
                    steps: vec![step],
                    effective_timeout_secs: 600,
                    sync_wait_secs: 90,
                    adapter: "cargo_check".into(),
                    source_identity: None,
                    source_snapshot_identity: Some(ShellJobValidationSourceSnapshotIdentity {
                        base_git_head: source_snapshot.base_git_head.clone(),
                        snapshot_sha256: "0".repeat(64),
                        entry_count: source_snapshot.entries.len(),
                    }),
                }),
                visibility: ShellJobVisibility::HiddenUntilHandoff,
                stdin: Some(payload),
                ..Default::default()
            },
        )
        .await
        .expect_err("mismatched snapshot identity must fail before enqueue");
    require(
        error.contains("source snapshot validation identity mismatch"),
        format!("unexpected mismatch error: {error}"),
    )?;
    require(
        poll(&runtime, target).await?.is_none(),
        "mismatched snapshot identity enqueued a Runner request",
    )
}

async fn undispatched_fallback() -> Result<(), String> {
    let source = "r3b2-harness-fallback-source";
    let target = "r3b2-harness-fallback-target";
    let head = "5123456789abcdef0123456789abcdef01234567";
    let runtime = runtime(Duration::from_millis(20));
    register(&runtime, source, project(head, true), false, 1).await?;
    register(&runtime, target, project(head, false), true, 2).await?;
    let task = spawn_check(runtime.clone(), source);

    tokio::time::sleep(Duration::from_millis(80)).await;
    let request = wait_request(&runtime, source).await?;
    require(
        request.kind == "start_validation_job",
        format!("expected source fallback, got {}", request.kind),
    )?;
    require(
        request.stdin.is_none(),
        "source fallback carried snapshot stdin",
    )?;
    require(
        request
            .job_context
            .as_ref()
            .and_then(|c| c.validation.as_ref())
            .and_then(|v| v.source_identity.as_ref())
            .is_none(),
        "dirty fallback fabricated clean identity",
    )?;
    require(
        poll(&runtime, target).await?.is_none(),
        "target received fallback validation",
    )?;
    complete_job(&runtime, source, &request).await?;
    require(
        task.await.map_err(|e| e.to_string())?.success,
        "source fallback did not succeed",
    )
}

async fn dispatched_timeout_fails_closed() -> Result<(), String> {
    let source = "r3b2-harness-ambiguous-source";
    let target = "r3b2-harness-ambiguous-target";
    let head = "6123456789abcdef0123456789abcdef01234567";
    let runtime = runtime(Duration::from_millis(30));
    register(&runtime, source, project(head, true), false, 1).await?;
    register(&runtime, target, project(head, false), true, 2).await?;
    let task = spawn_check(runtime.clone(), source);

    let capture = wait_request(&runtime, source).await?;
    require(
        capture.kind == SOURCE_SNAPSHOT_AGENT_REQUEST_KIND && capture.job_id.is_none(),
        "expected transient dispatched capture",
    )?;
    let result = task.await.map_err(|e| e.to_string())?;
    require(
        !result.success,
        "dispatched capture timeout did not fail closed",
    )?;
    require(
        result.output["failure_kind"] == "source_snapshot_capture_outcome_unknown",
        format!("unexpected failure kind: {}", result.output["failure_kind"]),
    )?;
    require(
        result.output["command_started"] == false,
        "ambiguous capture claimed command start",
    )?;
    require(
        poll(&runtime, source).await?.is_none(),
        "source validation created after ambiguous capture",
    )?;
    require(
        poll(&runtime, target).await?.is_none(),
        "target validation created after ambiguous capture",
    )
}

pub async fn run_server_first_dirty_snapshot_validation_scenarios() -> Result<(), String> {
    successful_target_dispatch().await?;
    mismatched_snapshot_identity_is_rejected_before_enqueue().await?;
    undispatched_fallback().await?;
    dispatched_timeout_fails_closed().await?;
    Ok(())
}
