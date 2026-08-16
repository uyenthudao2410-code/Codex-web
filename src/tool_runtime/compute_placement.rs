//! Runtime adapter for the side-effect-free server-first placement core.
//!
//! `ShellClientRegistry` and Runner Job inventory remain canonical. This module
//! derives sanitized compute snapshots for observability and the narrow
//! server-first validation policy; it never mutates a workspace.

use super::{agent_project_runtime_id, ToolRuntime, ACTIVE_JOB_STATUSES};
use crate::auth::AuthContext;
use crate::shell_client::CLIENT_ONLINE_WINDOW_SECS;
use crate::shell_protocol::{ShellClientView, ShellJobInfo};
use serde_json::{json, Value};
use webcodex_core::compute_placement::{
    choose_compute_placement, ComputeIntentV1, ComputeMutationMode, ComputePlacementPolicy,
    ComputeResourceClass, RunnerComputeSnapshotV1, RunnerProjectComputeSnapshotV1,
    COMPUTE_PLACEMENT_POLICY_V1, COMPUTE_PLACEMENT_SCHEMA_VERSION,
};

const RUNNING_JOB_STATUSES: &[&str] = &["running", "started"];
const QUEUED_JOB_STATUSES: &[&str] = &["queued", "agent_queued"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct RemoteValidationTargetV1 {
    pub(crate) client_id: String,
    pub(crate) runtime_project_id: String,
}

fn agent_runtime_project_binding(runtime_project_id: &str) -> Option<(&str, &str)> {
    let rest = runtime_project_id.strip_prefix("agent:")?;
    let (client_id, project_id) = rest.split_once(':')?;
    (!client_id.is_empty() && !project_id.is_empty()).then_some((client_id, project_id))
}

fn heavy_validation_intent(
    project_id: &str,
    expected_git_head: &str,
    purpose: &str,
) -> ComputeIntentV1 {
    ComputeIntentV1 {
        purpose: purpose.to_string(),
        resource_class: ComputeResourceClass::Heavy,
        project_id: project_id.to_string(),
        expected_git_head: Some(expected_git_head.to_string()),
        mutation_mode: ComputeMutationMode::ReadOnly,
        requires_structured_validation: true,
        requires_exact_source_validation: true,
        placement_policy: ComputePlacementPolicy::ServerPreferred,
    }
}

pub(crate) fn validation_auto_offload_eligible(
    tool_name: &str,
    timeout_secs: u64,
    sync_wait_secs: u64,
    sandbox: Option<&str>,
) -> bool {
    matches!(tool_name, "cargo_check" | "cargo_test")
        && timeout_secs > sync_wait_secs
        && sandbox.is_none()
}

impl ToolRuntime {
    pub(crate) async fn select_server_preferred_validation_target(
        &self,
        source_runtime_project_id: &str,
        expected_git_head: &str,
        purpose: &str,
        auth: Option<&AuthContext>,
    ) -> Option<RemoteValidationTargetV1> {
        let (source_client_id, project_id) =
            agent_runtime_project_binding(source_runtime_project_id)?;
        let clients = self.shell_clients.list_clients_for_auth(auth).await;
        let jobs = self.shell_clients.list_all_jobs_for_auth(auth).await;
        let now = chrono::Utc::now().timestamp();
        let mut runners = runner_compute_snapshots(&clients, &jobs, now);
        runners.retain(|runner| runner.client_id != source_client_id);
        let intent = heavy_validation_intent(project_id, expected_git_head, purpose);
        let decision = choose_compute_placement(&intent, &runners);
        let client_id = decision.selected_runner_id?;
        let runtime_project_id = decision.selected_runtime_project_id?;
        (client_id != source_client_id).then_some(RemoteValidationTargetV1 {
            client_id,
            runtime_project_id,
        })
    }

    pub(crate) async fn revalidate_server_preferred_validation_target(
        &self,
        source_runtime_project_id: &str,
        expected_git_head: &str,
        purpose: &str,
        target: &RemoteValidationTargetV1,
        auth: Option<&AuthContext>,
    ) -> bool {
        let Some((source_client_id, project_id)) =
            agent_runtime_project_binding(source_runtime_project_id)
        else {
            return false;
        };
        let Some((target_client_id, target_project_id)) =
            agent_runtime_project_binding(&target.runtime_project_id)
        else {
            return false;
        };
        if source_client_id == target.client_id
            || target_client_id != target.client_id
            || target_project_id != project_id
        {
            return false;
        }

        let clients = self.shell_clients.list_clients_for_auth(auth).await;
        let jobs = self.shell_clients.list_all_jobs_for_auth(auth).await;
        let now = chrono::Utc::now().timestamp();
        let runners = runner_compute_snapshots(&clients, &jobs, now);
        let Some(source) = runners
            .iter()
            .find(|runner| runner.client_id == source_client_id)
        else {
            return false;
        };
        let source_still_exact = source.supports_exact_source_validation
            && source.connected
            && source.status == "online"
            && source.metadata_fresh
            && source.projects.iter().any(|project| {
                project.project_id == project_id
                    && !project.disabled
                    && project.git_dirty == Some(false)
                    && project.git_head.as_deref() == Some(expected_git_head)
            });
        if !source_still_exact {
            return false;
        }

        let target_runners = runners
            .into_iter()
            .filter(|runner| runner.client_id == target.client_id)
            .collect::<Vec<_>>();
        let intent = heavy_validation_intent(project_id, expected_git_head, purpose);
        let decision = choose_compute_placement(&intent, &target_runners);
        decision.selected_runner_id.as_deref() == Some(target.client_id.as_str())
            && decision.selected_runtime_project_id.as_deref()
                == Some(target.runtime_project_id.as_str())
    }
}

pub(crate) fn runner_compute_snapshots(
    clients: &[ShellClientView],
    jobs: &[ShellJobInfo],
    now: i64,
) -> Vec<RunnerComputeSnapshotV1> {
    let mut snapshots = clients
        .iter()
        .map(|client| {
            let client_jobs = jobs
                .iter()
                .filter(|job| job.client_id == client.client_id)
                .collect::<Vec<_>>();
            let active_jobs = client_jobs
                .iter()
                .filter(|job| ACTIVE_JOB_STATUSES.contains(&job.status.as_str()))
                .count();
            let running_jobs = client_jobs
                .iter()
                .filter(|job| RUNNING_JOB_STATUSES.contains(&job.status.as_str()))
                .count();
            let queued_jobs = client_jobs
                .iter()
                .filter(|job| QUEUED_JOB_STATUSES.contains(&job.status.as_str()))
                .count();
            let mut projects = client
                .projects
                .iter()
                .map(|project| RunnerProjectComputeSnapshotV1 {
                    project_id: project.id.clone(),
                    runtime_project_id: agent_project_runtime_id(&client.client_id, &project.id),
                    git_head: project.git_head.clone(),
                    git_dirty: project.git_dirty,
                    disabled: project.disabled,
                })
                .collect::<Vec<_>>();
            projects.sort_by(|a, b| a.project_id.cmp(&b.project_id));
            let metadata_age_secs = now.saturating_sub(client.last_seen);
            RunnerComputeSnapshotV1 {
                client_id: client.client_id.clone(),
                agent_instance_id: client.agent_instance_id.clone(),
                status: client.status.clone(),
                connected: client.connected,
                transport: client.transport.clone(),
                metadata_age_secs,
                metadata_fresh: metadata_age_secs <= CLIENT_ONLINE_WINDOW_SECS,
                pending_requests: client.pending_requests,
                active_jobs,
                running_jobs,
                queued_jobs,
                job_concurrency_limit: client.job_concurrency_limit,
                supports_structured_validation: client.capabilities.structured_validation_argv,
                supports_exact_source_validation: client.capabilities.exact_source_validation,
                server_compute_opt_in: client.capabilities.server_compute,
                supports_structured_execution_jobs: client.capabilities.structured_execution_jobs,
                supports_lsp_read_only_navigation: client.capabilities.lsp_read_only_navigation,
                projects,
            }
        })
        .collect::<Vec<_>>();
    snapshots.sort_by(|a, b| a.client_id.cmp(&b.client_id));
    snapshots
}

/// Sanitized runtime projection for R1. No project paths, command text,
/// environment, secrets, stdout/stderr, or authorization material are emitted.
pub(crate) fn compute_runtime_projection(
    clients: &[ShellClientView],
    jobs: &[ShellJobInfo],
    now: i64,
) -> Value {
    let runners = runner_compute_snapshots(clients, jobs, now);
    let known_capacity_count = runners
        .iter()
        .filter(|runner| runner.job_concurrency_limit.is_some())
        .count();
    let available_capacity_count = runners
        .iter()
        .filter(|runner| runner.capacity_available() == Some(true))
        .count();
    let structured_validation_count = runners
        .iter()
        .filter(|runner| runner.supports_structured_validation)
        .count();
    let exact_source_validation_count = runners
        .iter()
        .filter(|runner| runner.supports_exact_source_validation)
        .count();
    let server_compute_count = runners
        .iter()
        .filter(|runner| runner.server_compute_opt_in)
        .count();
    let clean_source_project_count = runners
        .iter()
        .flat_map(|runner| runner.projects.iter())
        .filter(|project| {
            !project.disabled && project.git_dirty == Some(false) && project.git_head.is_some()
        })
        .count();
    json!({
        "schema_version": COMPUTE_PLACEMENT_SCHEMA_VERSION,
        "mode": "server_preferred",
        "policy": COMPUTE_PLACEMENT_POLICY_V1,
        "dispatch_enabled": true,
        "runner_stale_after_secs": CLIENT_ONLINE_WINDOW_SECS,
        "supported_canary_intent": {
            "resource_class": ComputeResourceClass::Heavy.as_str(),
            "mutation_mode": ComputeMutationMode::ReadOnly.as_str(),
            "placement_policy": ComputePlacementPolicy::ServerPreferred.as_str(),
            "requires_exact_clean_git_head": true,
            "requires_structured_validation": true,
            "requires_exact_source_validation": true,
            "requires_server_compute_opt_in": true,
        },
        "non_remote_resource_classes": [
            ComputeResourceClass::Light.as_str(),
            ComputeResourceClass::Medium.as_str(),
        ],
        "summary": {
            "runner_count": runners.len(),
            "online_count": runners.iter().filter(|runner| runner.connected && runner.status == "online").count(),
            "known_capacity_count": known_capacity_count,
            "available_capacity_count": available_capacity_count,
            "structured_validation_count": structured_validation_count,
            "exact_source_validation_count": exact_source_validation_count,
            "server_compute_count": server_compute_count,
            "clean_source_project_count": clean_source_project_count,
        },
        "runners": runners.iter().map(RunnerComputeSnapshotV1::to_json).collect::<Vec<_>>(),
    })
}

pub(crate) fn compact_compute_projection(compute: Option<&Value>) -> Value {
    let Some(compute) = compute else {
        return json!({
            "schema_version": COMPUTE_PLACEMENT_SCHEMA_VERSION,
            "mode": "server_preferred",
            "policy": COMPUTE_PLACEMENT_POLICY_V1,
            "dispatch_enabled": true,
            "summary": {
                "runner_count": 0,
                "online_count": 0,
                "known_capacity_count": 0,
                "available_capacity_count": 0,
                "structured_validation_count": 0,
                "exact_source_validation_count": 0,
                "server_compute_count": 0,
                "clean_source_project_count": 0,
            },
        });
    };
    json!({
        "schema_version": compute.get("schema_version").cloned().unwrap_or_else(|| json!(COMPUTE_PLACEMENT_SCHEMA_VERSION)),
        "mode": compute.get("mode").cloned().unwrap_or_else(|| json!("server_preferred")),
        "policy": compute.get("policy").cloned().unwrap_or_else(|| json!(COMPUTE_PLACEMENT_POLICY_V1)),
        "dispatch_enabled": compute.get("dispatch_enabled").cloned().unwrap_or_else(|| json!(true)),
        "summary": compute.get("summary").cloned().unwrap_or_else(|| json!({})),
    })
}
