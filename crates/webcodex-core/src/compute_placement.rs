//! Side-effect-free server-first compute placement contracts and evaluator.
//!
//! This module deliberately contains no dispatch or workspace mutation. It is
//! the deterministic policy core used by the server's shadow-placement R1
//! projection and by later canary dispatch only after explicit promotion.

use serde_json::{json, Value};

pub const COMPUTE_PLACEMENT_SCHEMA_VERSION: u64 = 1;
pub const COMPUTE_PLACEMENT_POLICY_V1: &str = "server_first_clean_head_validation_v1";

pub const REASON_REMOTE_SERVER_ELIGIBLE: &str = "REMOTE_SERVER_ELIGIBLE";
pub const REASON_LOCAL_ONLY_POLICY: &str = "LOCAL_ONLY_POLICY";
pub const REASON_LOCAL_LIGHT_POLICY: &str = "LOCAL_LIGHT_POLICY";
pub const REASON_LOCAL_MEDIUM_POLICY: &str = "LOCAL_MEDIUM_POLICY";
pub const REASON_AUTHORITATIVE_WRITE_LOCAL_ONLY: &str = "AUTHORITATIVE_WRITE_LOCAL_ONLY";
pub const REASON_LOCAL_REMOTE_UNAVAILABLE: &str = "LOCAL_REMOTE_UNAVAILABLE";
pub const REASON_RUNNER_METADATA_STALE: &str = "RUNNER_METADATA_STALE";
pub const REASON_PROJECT_BINDING_MISMATCH: &str = "PROJECT_BINDING_MISMATCH";
pub const REASON_SOURCE_IDENTITY_INCOMPLETE: &str = "SOURCE_IDENTITY_INCOMPLETE";
pub const REASON_SOURCE_IDENTITY_MISMATCH: &str = "SOURCE_IDENTITY_MISMATCH";
pub const REASON_REMOTE_DIRTY_WORKTREE: &str = "REMOTE_DIRTY_WORKTREE";
pub const REASON_CAPABILITY_MISSING: &str = "CAPABILITY_MISSING";
pub const REASON_RUNNER_COMPUTE_NOT_OPTED_IN: &str = "RUNNER_COMPUTE_NOT_OPTED_IN";
pub const REASON_RUNNER_CAPACITY_UNKNOWN: &str = "RUNNER_CAPACITY_UNKNOWN";
pub const REASON_RUNNER_CAPACITY_EXHAUSTED: &str = "RUNNER_CAPACITY_EXHAUSTED";

/// Narrow R2B auto-offload scope for read-only Rust validation.
///
/// Resource class, source identity, capabilities and capacity remain placement
/// concerns below. This helper only answers whether the validation shape may
/// enter server-preferred placement at all.
pub fn validation_auto_offload_eligible(
    tool_name: &str,
    timeout_secs: u64,
    sync_wait_secs: u64,
    sandboxed: bool,
) -> bool {
    matches!(tool_name, "cargo_check" | "cargo_test") && timeout_secs > sync_wait_secs && !sandboxed
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComputeResourceClass {
    Light,
    Medium,
    Heavy,
}

impl ComputeResourceClass {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Light => "LIGHT",
            Self::Medium => "MEDIUM",
            Self::Heavy => "HEAVY",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComputeMutationMode {
    ReadOnly,
    AuthoritativeWrite,
}

impl ComputeMutationMode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ReadOnly => "read_only",
            Self::AuthoritativeWrite => "authoritative_write",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComputePlacementPolicy {
    LocalOnly,
    ServerPreferred,
}

impl ComputePlacementPolicy {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::LocalOnly => "local_only",
            Self::ServerPreferred => "server_preferred",
        }
    }
}

/// Internal placement input. It is intentionally not a public MCP tool input.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComputeIntentV1 {
    pub purpose: String,
    pub resource_class: ComputeResourceClass,
    /// Logical Runner project id, never a filesystem path.
    pub project_id: String,
    /// Exact Git HEAD required on a remote replica. `None` fails closed.
    pub expected_git_head: Option<String>,
    pub mutation_mode: ComputeMutationMode,
    pub requires_structured_validation: bool,
    pub requires_exact_source_validation: bool,
    pub placement_policy: ComputePlacementPolicy,
}

impl ComputeIntentV1 {
    pub fn to_json(&self) -> Value {
        json!({
            "schema_version": COMPUTE_PLACEMENT_SCHEMA_VERSION,
            "purpose": self.purpose,
            "resource_class": self.resource_class.as_str(),
            "project_id": self.project_id,
            "expected_git_head": self.expected_git_head,
            "mutation_mode": self.mutation_mode.as_str(),
            "requires_structured_validation": self.requires_structured_validation,
            "requires_exact_source_validation": self.requires_exact_source_validation,
            "placement_policy": self.placement_policy.as_str(),
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunnerProjectComputeSnapshotV1 {
    pub project_id: String,
    pub runtime_project_id: String,
    pub git_head: Option<String>,
    pub git_dirty: Option<bool>,
    pub disabled: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunnerComputeSnapshotV1 {
    pub client_id: String,
    pub agent_instance_id: String,
    pub status: String,
    pub connected: bool,
    pub transport: String,
    pub metadata_age_secs: i64,
    /// Derived by the owning runtime from its canonical heartbeat window.
    pub metadata_fresh: bool,
    pub pending_requests: usize,
    pub active_jobs: usize,
    pub running_jobs: usize,
    pub queued_jobs: usize,
    pub job_concurrency_limit: Option<usize>,
    pub supports_structured_validation: bool,
    pub supports_exact_source_validation: bool,
    pub server_compute_opt_in: bool,
    pub supports_structured_execution_jobs: bool,
    pub supports_lsp_read_only_navigation: bool,
    pub projects: Vec<RunnerProjectComputeSnapshotV1>,
}

impl RunnerComputeSnapshotV1 {
    pub fn capacity_available(&self) -> Option<bool> {
        self.job_concurrency_limit
            .map(|limit| limit > 0 && self.active_jobs < limit)
    }

    pub fn to_json(&self) -> Value {
        json!({
            "schema_version": COMPUTE_PLACEMENT_SCHEMA_VERSION,
            "client_id": self.client_id,
            "agent_instance_id": self.agent_instance_id,
            "status": self.status,
            "connected": self.connected,
            "transport": self.transport,
            "metadata_age_secs": self.metadata_age_secs,
            "metadata_fresh": self.metadata_fresh,
            "pending_requests": self.pending_requests,
            "active_jobs": self.active_jobs,
            "job_concurrency": {
                "limit": self.job_concurrency_limit,
                "running": self.running_jobs,
                "queued": self.queued_jobs,
                "capacity_available": self.capacity_available(),
            },
            "capabilities": {
                "structured_validation_argv": self.supports_structured_validation,
                "exact_source_validation": self.supports_exact_source_validation,
                "server_compute": self.server_compute_opt_in,
                "structured_execution_jobs": self.supports_structured_execution_jobs,
                "lsp_read_only_navigation": self.supports_lsp_read_only_navigation,
            },
            "projects": self.projects.iter().map(|project| json!({
                "project_id": project.project_id,
                "runtime_project_id": project.runtime_project_id,
                "git_head": project.git_head,
                "git_dirty": project.git_dirty,
                "disabled": project.disabled,
            })).collect::<Vec<_>>(),
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunnerPlacementRejectionV1 {
    pub runner_id: String,
    pub reason_code: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlacementDecisionV1 {
    pub placement: &'static str,
    pub selected_runner_id: Option<String>,
    pub selected_runtime_project_id: Option<String>,
    pub reason_code: &'static str,
    pub eligible_runner_count: usize,
    pub rejected_runners: Vec<RunnerPlacementRejectionV1>,
    pub shadow_only: bool,
}

impl PlacementDecisionV1 {
    pub fn to_json(&self) -> Value {
        json!({
            "schema_version": COMPUTE_PLACEMENT_SCHEMA_VERSION,
            "policy": COMPUTE_PLACEMENT_POLICY_V1,
            "placement": self.placement,
            "selected_runner_id": self.selected_runner_id,
            "selected_runtime_project_id": self.selected_runtime_project_id,
            "reason_code": self.reason_code,
            "eligible_runner_count": self.eligible_runner_count,
            "rejected_runners": self.rejected_runners.iter().map(|rejection| json!({
                "runner_id": rejection.runner_id,
                "reason_code": rejection.reason_code,
            })).collect::<Vec<_>>(),
            "shadow_only": self.shadow_only,
        })
    }
}

fn remote_rejection(
    intent: &ComputeIntentV1,
    runner: &RunnerComputeSnapshotV1,
) -> Option<&'static str> {
    if !runner.connected || runner.status != "online" || !runner.metadata_fresh {
        return Some(REASON_RUNNER_METADATA_STALE);
    }
    if !runner.server_compute_opt_in {
        return Some(REASON_RUNNER_COMPUTE_NOT_OPTED_IN);
    }
    let Some(project) = runner
        .projects
        .iter()
        .find(|project| project.project_id == intent.project_id && !project.disabled)
    else {
        return Some(REASON_PROJECT_BINDING_MISMATCH);
    };
    if intent.requires_structured_validation && !runner.supports_structured_validation {
        return Some(REASON_CAPABILITY_MISSING);
    }
    if intent.requires_exact_source_validation && !runner.supports_exact_source_validation {
        return Some(REASON_CAPABILITY_MISSING);
    }
    if project.git_dirty != Some(false) {
        return Some(REASON_REMOTE_DIRTY_WORKTREE);
    }
    let Some(expected_head) = intent.expected_git_head.as_deref() else {
        return Some(REASON_SOURCE_IDENTITY_INCOMPLETE);
    };
    let Some(remote_head) = project.git_head.as_deref() else {
        return Some(REASON_SOURCE_IDENTITY_INCOMPLETE);
    };
    if remote_head != expected_head {
        return Some(REASON_SOURCE_IDENTITY_MISMATCH);
    }
    let Some(limit) = runner.job_concurrency_limit else {
        return Some(REASON_RUNNER_CAPACITY_UNKNOWN);
    };
    if limit == 0 || runner.active_jobs >= limit {
        return Some(REASON_RUNNER_CAPACITY_EXHAUSTED);
    }
    None
}

/// Deterministic V1 evaluator. It never dispatches work.
pub fn choose_compute_placement(
    intent: &ComputeIntentV1,
    runners: &[RunnerComputeSnapshotV1],
) -> PlacementDecisionV1 {
    if intent.placement_policy == ComputePlacementPolicy::LocalOnly {
        return local_decision(REASON_LOCAL_ONLY_POLICY, Vec::new());
    }
    match intent.resource_class {
        ComputeResourceClass::Light => {
            return local_decision(REASON_LOCAL_LIGHT_POLICY, Vec::new());
        }
        ComputeResourceClass::Medium => {
            return local_decision(REASON_LOCAL_MEDIUM_POLICY, Vec::new());
        }
        ComputeResourceClass::Heavy => {}
    }
    if intent.mutation_mode == ComputeMutationMode::AuthoritativeWrite {
        return local_decision(REASON_AUTHORITATIVE_WRITE_LOCAL_ONLY, Vec::new());
    }
    if intent.expected_git_head.is_none() {
        return local_decision(REASON_SOURCE_IDENTITY_INCOMPLETE, Vec::new());
    }

    let mut eligible = Vec::new();
    let mut rejected = Vec::new();
    for runner in runners {
        if let Some(reason_code) = remote_rejection(intent, runner) {
            rejected.push(RunnerPlacementRejectionV1 {
                runner_id: runner.client_id.clone(),
                reason_code,
            });
            continue;
        }
        let runtime_project_id = runner
            .projects
            .iter()
            .find(|project| project.project_id == intent.project_id && !project.disabled)
            .map(|project| project.runtime_project_id.clone())
            .expect("eligible runner must have the requested project");
        eligible.push((
            runner.active_jobs,
            runner.queued_jobs,
            runner.pending_requests,
            runner.client_id.clone(),
            runtime_project_id,
        ));
    }
    eligible.sort_by(|a, b| (a.0, a.1, a.2, &a.3).cmp(&(b.0, b.1, b.2, &b.3)));
    let eligible_runner_count = eligible.len();
    if let Some((_, _, _, runner_id, runtime_project_id)) = eligible.into_iter().next() {
        PlacementDecisionV1 {
            placement: "remote",
            selected_runner_id: Some(runner_id),
            selected_runtime_project_id: Some(runtime_project_id),
            reason_code: REASON_REMOTE_SERVER_ELIGIBLE,
            eligible_runner_count,
            rejected_runners: rejected,
            shadow_only: true,
        }
    } else {
        local_decision(REASON_LOCAL_REMOTE_UNAVAILABLE, rejected)
    }
}

/// Apply the same deterministic placement policy while excluding the Runner
/// that owns the authoritative source project from remote-compute candidacy.
///
/// R2B uses this at the runtime boundary so "server preferred" can never mean
/// selecting the source Runner itself as a remote compute target. If no other
/// Runner remains eligible the normal local/fallback decision is returned.
pub fn choose_compute_placement_excluding_runner(
    intent: &ComputeIntentV1,
    runners: &[RunnerComputeSnapshotV1],
    excluded_runner_id: &str,
) -> PlacementDecisionV1 {
    let candidates = runners
        .iter()
        .filter(|runner| runner.client_id != excluded_runner_id)
        .cloned()
        .collect::<Vec<_>>();
    choose_compute_placement(intent, &candidates)
}

fn local_decision(
    reason_code: &'static str,
    rejected_runners: Vec<RunnerPlacementRejectionV1>,
) -> PlacementDecisionV1 {
    PlacementDecisionV1 {
        placement: "local",
        selected_runner_id: None,
        selected_runtime_project_id: None,
        reason_code,
        eligible_runner_count: 0,
        rejected_runners,
        shadow_only: true,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn runner(client_id: &str, head: Option<&str>, dirty: Option<bool>) -> RunnerComputeSnapshotV1 {
        RunnerComputeSnapshotV1 {
            client_id: client_id.to_string(),
            agent_instance_id: format!("instance-{client_id}"),
            status: "online".to_string(),
            connected: true,
            transport: "quic".to_string(),
            metadata_age_secs: 1,
            metadata_fresh: true,
            pending_requests: 0,
            active_jobs: 0,
            running_jobs: 0,
            queued_jobs: 0,
            job_concurrency_limit: Some(2),
            supports_structured_validation: true,
            supports_exact_source_validation: true,
            server_compute_opt_in: true,
            supports_structured_execution_jobs: true,
            supports_lsp_read_only_navigation: true,
            projects: vec![RunnerProjectComputeSnapshotV1 {
                project_id: "tools-codex-web".to_string(),
                runtime_project_id: format!("agent:{client_id}:tools-codex-web"),
                git_head: head.map(str::to_string),
                git_dirty: dirty,
                disabled: false,
            }],
        }
    }

    fn heavy_validation_intent(head: Option<&str>) -> ComputeIntentV1 {
        ComputeIntentV1 {
            purpose: "focused_validation".to_string(),
            resource_class: ComputeResourceClass::Heavy,
            project_id: "tools-codex-web".to_string(),
            expected_git_head: head.map(str::to_string),
            mutation_mode: ComputeMutationMode::ReadOnly,
            requires_structured_validation: true,
            requires_exact_source_validation: true,
            placement_policy: ComputePlacementPolicy::ServerPreferred,
        }
    }

    #[test]
    fn exact_clean_heavy_validation_selects_least_loaded_runner() {
        let mut busy = runner("server-b", Some("abc123"), Some(false));
        busy.active_jobs = 1;
        busy.running_jobs = 1;
        let idle = runner("server-a", Some("abc123"), Some(false));
        let decision =
            choose_compute_placement(&heavy_validation_intent(Some("abc123")), &[busy, idle]);
        assert_eq!(decision.placement, "remote");
        assert_eq!(decision.selected_runner_id.as_deref(), Some("server-a"));
        assert_eq!(
            decision.selected_runtime_project_id.as_deref(),
            Some("agent:server-a:tools-codex-web")
        );
        assert_eq!(decision.reason_code, REASON_REMOTE_SERVER_ELIGIBLE);
        assert_eq!(decision.eligible_runner_count, 2);
        assert!(decision.shadow_only);
    }

    #[test]
    fn light_medium_and_authoritative_write_stay_local() {
        let runners = [runner("server-a", Some("abc123"), Some(false))];
        let mut intent = heavy_validation_intent(Some("abc123"));
        intent.resource_class = ComputeResourceClass::Light;
        assert_eq!(
            choose_compute_placement(&intent, &runners).reason_code,
            REASON_LOCAL_LIGHT_POLICY
        );
        intent.resource_class = ComputeResourceClass::Medium;
        assert_eq!(
            choose_compute_placement(&intent, &runners).reason_code,
            REASON_LOCAL_MEDIUM_POLICY
        );
        intent.resource_class = ComputeResourceClass::Heavy;
        intent.mutation_mode = ComputeMutationMode::AuthoritativeWrite;
        assert_eq!(
            choose_compute_placement(&intent, &runners).reason_code,
            REASON_AUTHORITATIVE_WRITE_LOCAL_ONLY
        );
    }

    #[test]
    fn dirty_stale_mismatched_or_unknown_capacity_runner_fails_closed() {
        let intent = heavy_validation_intent(Some("abc123"));
        let mut dirty = runner("dirty", Some("abc123"), Some(true));
        let mut stale = runner("stale", Some("abc123"), Some(false));
        stale.metadata_fresh = false;
        let mismatched = runner("mismatch", Some("def456"), Some(false));
        let mut unknown_capacity = runner("unknown-capacity", Some("abc123"), Some(false));
        unknown_capacity.job_concurrency_limit = None;
        let decision = choose_compute_placement(
            &intent,
            &[dirty.clone(), stale, mismatched, unknown_capacity],
        );
        assert_eq!(decision.placement, "local");
        assert_eq!(decision.reason_code, REASON_LOCAL_REMOTE_UNAVAILABLE);
        let reasons = decision
            .rejected_runners
            .iter()
            .map(|rejection| rejection.reason_code)
            .collect::<Vec<_>>();
        assert!(reasons.contains(&REASON_REMOTE_DIRTY_WORKTREE));
        assert!(reasons.contains(&REASON_RUNNER_METADATA_STALE));
        assert!(reasons.contains(&REASON_SOURCE_IDENTITY_MISMATCH));
        assert!(reasons.contains(&REASON_RUNNER_CAPACITY_UNKNOWN));

        dirty.projects[0].git_dirty = Some(false);
        dirty.projects[0].git_head = None;
        let incomplete = choose_compute_placement(&intent, &[dirty]);
        assert_eq!(
            incomplete.rejected_runners[0].reason_code,
            REASON_SOURCE_IDENTITY_INCOMPLETE
        );
    }

    #[test]
    fn missing_expected_source_identity_fails_before_runner_selection() {
        let decision = choose_compute_placement(
            &heavy_validation_intent(None),
            &[runner("server-a", Some("abc123"), Some(false))],
        );
        assert_eq!(decision.placement, "local");
        assert_eq!(decision.reason_code, REASON_SOURCE_IDENTITY_INCOMPLETE);
        assert!(decision.rejected_runners.is_empty());
    }

    #[test]
    fn runner_must_explicitly_opt_in_as_compute_target() {
        let intent = heavy_validation_intent(Some("abc123"));
        let mut not_opted_in = runner("ordinary-runner", Some("abc123"), Some(false));
        not_opted_in.server_compute_opt_in = false;
        let decision = choose_compute_placement(&intent, &[not_opted_in]);
        assert_eq!(decision.placement, "local");
        assert_eq!(decision.reason_code, REASON_LOCAL_REMOTE_UNAVAILABLE);
        assert_eq!(
            decision.rejected_runners[0].reason_code,
            REASON_RUNNER_COMPUTE_NOT_OPTED_IN
        );
    }

    #[test]
    fn server_first_excludes_source_and_selects_distinct_exact_target() {
        let source = runner("source", Some("abc123"), Some(false));
        let target = runner("compute", Some("abc123"), Some(false));
        let decision = choose_compute_placement_excluding_runner(
            &heavy_validation_intent(Some("abc123")),
            &[source, target],
            "source",
        );
        assert_eq!(decision.placement, "remote");
        assert_eq!(decision.selected_runner_id.as_deref(), Some("compute"));
        assert_eq!(
            decision.selected_runtime_project_id.as_deref(),
            Some("agent:compute:tools-codex-web")
        );
    }

    #[test]
    fn server_first_source_only_never_selects_itself() {
        let decision = choose_compute_placement_excluding_runner(
            &heavy_validation_intent(Some("abc123")),
            &[runner("source", Some("abc123"), Some(false))],
            "source",
        );
        assert_eq!(decision.placement, "local");
        assert_eq!(decision.reason_code, REASON_LOCAL_REMOTE_UNAVAILABLE);
        assert!(decision.selected_runner_id.is_none());
    }

    #[test]
    fn server_first_ineligible_targets_fall_back_after_source_exclusion() {
        let intent = heavy_validation_intent(Some("abc123"));
        let source = runner("source", Some("abc123"), Some(false));
        let dirty = runner("dirty", Some("abc123"), Some(true));
        let mismatch = runner("mismatch", Some("def456"), Some(false));
        let mut unknown_capacity = runner("unknown", Some("abc123"), Some(false));
        unknown_capacity.job_concurrency_limit = None;
        let mut not_opted_in = runner("not-opted", Some("abc123"), Some(false));
        not_opted_in.server_compute_opt_in = false;

        let decision = choose_compute_placement_excluding_runner(
            &intent,
            &[source, dirty, mismatch, unknown_capacity, not_opted_in],
            "source",
        );
        assert_eq!(decision.placement, "local");
        assert_eq!(decision.reason_code, REASON_LOCAL_REMOTE_UNAVAILABLE);
        let reasons = decision
            .rejected_runners
            .iter()
            .map(|rejection| rejection.reason_code)
            .collect::<Vec<_>>();
        assert!(reasons.contains(&REASON_REMOTE_DIRTY_WORKTREE));
        assert!(reasons.contains(&REASON_SOURCE_IDENTITY_MISMATCH));
        assert!(reasons.contains(&REASON_RUNNER_CAPACITY_UNKNOWN));
        assert!(reasons.contains(&REASON_RUNNER_COMPUTE_NOT_OPTED_IN));
    }

    #[test]
    fn validation_auto_offload_scope_requires_long_unsandboxed_check_or_test() {
        assert!(validation_auto_offload_eligible(
            "cargo_check",
            600,
            90,
            false
        ));
        assert!(validation_auto_offload_eligible(
            "cargo_test",
            600,
            90,
            false
        ));
        assert!(!validation_auto_offload_eligible(
            "cargo_fmt",
            600,
            90,
            false
        ));
        assert!(!validation_auto_offload_eligible(
            "cargo_check",
            90,
            90,
            false
        ));
        assert!(!validation_auto_offload_eligible(
            "cargo_test",
            60,
            90,
            false
        ));
        assert!(!validation_auto_offload_eligible(
            "cargo_check",
            600,
            90,
            true
        ));
    }

    #[test]
    fn decision_and_intent_json_are_bounded_and_explicit() {
        let intent = heavy_validation_intent(Some("abc123"));
        assert_eq!(intent.to_json()["resource_class"], "HEAVY");
        let decision =
            choose_compute_placement(&intent, &[runner("server-a", Some("abc123"), Some(false))]);
        let value = decision.to_json();
        assert_eq!(value["shadow_only"], true);
        assert_eq!(value["policy"], COMPUTE_PLACEMENT_POLICY_V1);
        assert!(value.get("command").is_none());
        assert!(value.get("path").is_none());
    }
}
