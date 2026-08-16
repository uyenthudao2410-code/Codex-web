//! Runner-owned capture and materialization of bounded immutable source snapshots.
//!
//! These helpers never mutate the registered checkout. Materialization happens
//! in a private temporary clone that is removed when the owner is dropped.

use std::collections::BTreeSet;
use std::ffi::OsStr;
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use tempfile::TempDir;
use webcodex_core::source_snapshot::{
    sha256_hex, validate_source_snapshot_path, SourceSnapshotAgentPayloadV1, SourceSnapshotEntryV1,
    SourceSnapshotOperationV1, SourceSnapshotV1, SOURCE_SNAPSHOT_AGENT_REQUEST_KIND,
    SOURCE_SNAPSHOT_MAX_ENTRIES, SOURCE_SNAPSHOT_MAX_FILE_BYTES, SOURCE_SNAPSHOT_MAX_PATH_BYTES,
    SOURCE_SNAPSHOT_MAX_SERIALIZED_BYTES,
};

use super::projects::find_project_shell_context_by_id;
use super::CommandResult;
use crate::shell_protocol::ShellAgentShellRequest;

const GIT_PATH_LIST_MAX_BYTES: usize =
    (SOURCE_SNAPSHOT_MAX_ENTRIES * (SOURCE_SNAPSHOT_MAX_PATH_BYTES + 1) * 2) + 1;
const GIT_SMALL_OUTPUT_MAX_BYTES: usize = 16 * 1024;

pub(crate) fn capture_source_snapshot(
    project_root: &Path,
    expected_head: &str,
) -> Result<SourceSnapshotV1, String> {
    capture_source_snapshot_with_before_recheck(project_root, expected_head, || {})
}

pub(crate) fn handle_source_snapshot_request(
    projects_dir: &Path,
    request: &ShellAgentShellRequest,
) -> CommandResult {
    let fail = |code: &str| CommandResult {
        exit_code: Some(1),
        stdout: None,
        stderr: None,
        duration_ms: Some(0),
        error: Some(code.to_string()),
    };
    if request.kind != SOURCE_SNAPSHOT_AGENT_REQUEST_KIND
        || request.job_id.is_some()
        || request.cwd.is_some()
        || request.path.is_some()
        || request.content.is_some()
        || request.max_bytes.is_some()
        || request.expected_sha256.is_some()
        || request.expected_prefix.is_some()
        || request.start_line.is_some()
        || request.end_line.is_some()
        || request.create_dirs
        || !request.command.is_empty()
        || request.process.is_some()
        || request.script.is_some()
        || request.validation.is_some()
        || request.lsp.is_some()
        || request.sandbox.is_some()
        || request.job_context.is_some()
        || request.persistent_shell.is_some()
    {
        return fail("invalid_source_snapshot_request");
    }
    let Some(raw) = request.stdin.as_deref() else {
        return fail("missing_source_snapshot_payload");
    };
    let payload: SourceSnapshotAgentPayloadV1 = match serde_json::from_str(raw) {
        Ok(payload) => payload,
        Err(_) => return fail("invalid_source_snapshot_payload"),
    };
    if payload.validate().is_err() {
        return fail("invalid_source_snapshot_payload");
    }
    let SourceSnapshotAgentPayloadV1::Capture {
        project_id,
        expected_git_head,
    } = payload
    else {
        return fail("source_snapshot_execute_not_enabled");
    };
    let project = match find_project_shell_context_by_id(projects_dir, &project_id) {
        Some(project) => project,
        None => return fail("source_snapshot_project_unavailable"),
    };
    let snapshot = match capture_source_snapshot(Path::new(&project.path), &expected_git_head) {
        Ok(snapshot) => snapshot,
        Err(_) => return fail("source_snapshot_capture_failed"),
    };
    let stdout = match serde_json::to_string(&snapshot) {
        Ok(stdout) if stdout.len() <= SOURCE_SNAPSHOT_MAX_SERIALIZED_BYTES => stdout,
        _ => return fail("source_snapshot_response_too_large"),
    };
    CommandResult {
        exit_code: Some(0),
        stdout: Some(stdout),
        stderr: None,
        duration_ms: Some(0),
        error: None,
    }
}

fn capture_source_snapshot_with_before_recheck<F>(
    project_root: &Path,
    expected_head: &str,
    before_recheck: F,
) -> Result<SourceSnapshotV1, String>
where
    F: FnOnce(),
{
    ensure_directory(project_root)?;
    verify_head(project_root, expected_head)?;
    let initial = changed_paths(project_root)?;
    if initial.all.is_empty() {
        return Err("source snapshot capture requires a dirty worktree".to_string());
    }
    if initial.all.len() > SOURCE_SNAPSHOT_MAX_ENTRIES {
        return Err(format!(
            "source snapshot exceeds {} changed entries",
            SOURCE_SNAPSHOT_MAX_ENTRIES
        ));
    }

    let mut entries = Vec::with_capacity(initial.all.len());
    for path in &initial.all {
        entries.push(capture_entry(
            project_root,
            expected_head,
            path,
            initial.tracked.contains(path),
        )?);
    }
    let snapshot = SourceSnapshotV1::from_entries(expected_head, entries)?;

    before_recheck();
    verify_head(project_root, expected_head)?;
    let current = changed_paths(project_root)?;
    if current.tracked != initial.tracked || current.untracked != initial.untracked {
        return Err("source snapshot capture detected source drift in changed paths".to_string());
    }
    for expected in &snapshot.entries {
        let observed = capture_entry(
            project_root,
            expected_head,
            &expected.path,
            initial.tracked.contains(&expected.path),
        )?;
        if &observed != expected {
            return Err(format!(
                "source snapshot capture detected source drift for {}",
                expected.path
            ));
        }
    }
    snapshot.validate()?;
    Ok(snapshot)
}

#[derive(Debug)]
struct ChangedPaths {
    tracked: BTreeSet<String>,
    untracked: BTreeSet<String>,
    all: BTreeSet<String>,
}

fn changed_paths(project_root: &Path) -> Result<ChangedPaths, String> {
    let tracked = parse_nul_paths(&git_stdout_bounded(
        project_root,
        ["diff", "--name-only", "--no-renames", "-z", "HEAD", "--"],
        GIT_PATH_LIST_MAX_BYTES,
    )?)?;
    let untracked = parse_nul_paths(&git_stdout_bounded(
        project_root,
        ["ls-files", "--others", "--exclude-standard", "-z", "--"],
        GIT_PATH_LIST_MAX_BYTES,
    )?)?;
    let mut all = tracked.clone();
    all.extend(untracked.iter().cloned());
    for path in &all {
        validate_source_snapshot_path(path)?;
    }
    Ok(ChangedPaths {
        tracked,
        untracked,
        all,
    })
}

fn capture_entry(
    project_root: &Path,
    expected_head: &str,
    path: &str,
    tracked_change: bool,
) -> Result<SourceSnapshotEntryV1, String> {
    validate_source_snapshot_path(path)?;
    let base_mode = if tracked_change {
        base_regular_executable(project_root, expected_head, path)?
    } else {
        None
    };
    let absolute = join_safe_relative(project_root, path);
    match fs::symlink_metadata(&absolute) {
        Ok(metadata) => {
            let file_type = metadata.file_type();
            if file_type.is_symlink() || !file_type.is_file() {
                return Err(format!(
                    "source snapshot only supports regular files: {path}"
                ));
            }
            if metadata.len() > SOURCE_SNAPSHOT_MAX_FILE_BYTES as u64 {
                return Err(format!("source snapshot file is too large: {path}"));
            }
            let content = fs::read(&absolute)
                .map_err(|error| format!("failed to read source snapshot file {path}: {error}"))?;
            if content.len() > SOURCE_SNAPSHOT_MAX_FILE_BYTES {
                return Err(format!("source snapshot file is too large: {path}"));
            }
            let executable = executable_metadata(&metadata, base_mode.unwrap_or(false));
            SourceSnapshotEntryV1::upsert(path, &content, executable)
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            if !tracked_change {
                return Err(format!(
                    "untracked source snapshot file disappeared during capture: {path}"
                ));
            }
            if base_mode.is_none() {
                return Err(format!(
                    "deleted source snapshot path is not a regular file in base HEAD: {path}"
                ));
            }
            SourceSnapshotEntryV1::delete(path)
        }
        Err(error) => Err(format!(
            "failed to inspect source snapshot path {path}: {error}"
        )),
    }
}

fn base_regular_executable(
    project_root: &Path,
    expected_head: &str,
    path: &str,
) -> Result<Option<bool>, String> {
    let output = git_stdout_bounded_args(
        project_root,
        [
            OsStr::new("ls-tree"),
            OsStr::new("-z"),
            OsStr::new(expected_head),
            OsStr::new("--"),
            OsStr::new(path),
        ],
        GIT_SMALL_OUTPUT_MAX_BYTES,
    )?;
    if output.is_empty() {
        return Ok(None);
    }
    let record = output
        .split(|byte| *byte == 0)
        .next()
        .ok_or_else(|| "invalid git ls-tree output".to_string())?;
    let header_end = record
        .iter()
        .position(|byte| *byte == b'\t')
        .ok_or_else(|| "invalid git ls-tree record".to_string())?;
    let header = std::str::from_utf8(&record[..header_end])
        .map_err(|_| "git ls-tree returned non-UTF8 metadata".to_string())?;
    let mode = header
        .split_whitespace()
        .next()
        .ok_or_else(|| "git ls-tree record is missing mode".to_string())?;
    match mode {
        "100644" => Ok(Some(false)),
        "100755" => Ok(Some(true)),
        other => Err(format!(
            "source snapshot rejects non-regular base Git mode {other} for {path}"
        )),
    }
}

#[cfg(unix)]
fn executable_metadata(metadata: &fs::Metadata, _base_executable: bool) -> bool {
    use std::os::unix::fs::PermissionsExt;
    metadata.permissions().mode() & 0o111 != 0
}

#[cfg(not(unix))]
fn executable_metadata(_metadata: &fs::Metadata, base_executable: bool) -> bool {
    base_executable
}

pub(crate) struct MaterializedSourceSnapshot {
    temp_dir: TempDir,
    checkout_root: PathBuf,
    snapshot_sha256: String,
}

impl MaterializedSourceSnapshot {
    pub(crate) fn root(&self) -> &Path {
        &self.checkout_root
    }

    pub(crate) fn snapshot_sha256(&self) -> &str {
        &self.snapshot_sha256
    }

    #[cfg(test)]
    fn temp_root(&self) -> &Path {
        self.temp_dir.path()
    }
}

pub(crate) fn materialize_source_snapshot(
    registered_repo: &Path,
    snapshot: &SourceSnapshotV1,
) -> Result<MaterializedSourceSnapshot, String> {
    snapshot.validate()?;
    ensure_directory(registered_repo)?;
    let temp_dir = tempfile::Builder::new()
        .prefix("webcodex-source-snapshot-")
        .tempdir()
        .map_err(|error| format!("failed to create source snapshot tempdir: {error}"))?;
    let checkout_root = temp_dir.path().join("checkout");

    git_status_args(
        None,
        [
            OsStr::new("clone"),
            OsStr::new("--no-checkout"),
            OsStr::new("--shared"),
            OsStr::new("--"),
            registered_repo.as_os_str(),
            checkout_root.as_os_str(),
        ],
        "clone source snapshot base",
    )?;
    git_status_args(
        Some(&checkout_root),
        [
            OsStr::new("checkout"),
            OsStr::new("--detach"),
            OsStr::new("--force"),
            OsStr::new(&snapshot.base_git_head),
        ],
        "checkout source snapshot base",
    )?;
    verify_head(&checkout_root, &snapshot.base_git_head)?;

    for entry in &snapshot.entries {
        apply_entry(&checkout_root, entry)?;
    }
    verify_materialized_entries(&checkout_root, snapshot)?;

    Ok(MaterializedSourceSnapshot {
        temp_dir,
        checkout_root,
        snapshot_sha256: snapshot.snapshot_sha256.clone(),
    })
}

fn apply_entry(root: &Path, entry: &SourceSnapshotEntryV1) -> Result<(), String> {
    validate_source_snapshot_path(&entry.path)?;
    let target = ensure_safe_parent_chain(root, &entry.path)?;
    match entry.operation {
        SourceSnapshotOperationV1::Delete => {
            let metadata = fs::symlink_metadata(&target).map_err(|error| {
                format!(
                    "source snapshot delete target is unavailable {}: {error}",
                    entry.path
                )
            })?;
            if metadata.file_type().is_symlink() || !metadata.file_type().is_file() {
                return Err(format!(
                    "source snapshot delete target is not a regular file: {}",
                    entry.path
                ));
            }
            fs::remove_file(&target).map_err(|error| {
                format!("failed to delete snapshot path {}: {error}", entry.path)
            })?;
        }
        SourceSnapshotOperationV1::Upsert => {
            if let Ok(metadata) = fs::symlink_metadata(&target) {
                if metadata.file_type().is_symlink() || !metadata.file_type().is_file() {
                    return Err(format!(
                        "source snapshot upsert target is not a regular file: {}",
                        entry.path
                    ));
                }
            }
            let bytes = entry
                .decoded_content()?
                .expect("validated upsert must have decoded bytes");
            let mut file = OpenOptions::new()
                .create(true)
                .truncate(true)
                .write(true)
                .open(&target)
                .map_err(|error| format!("failed to open snapshot path {}: {error}", entry.path))?;
            file.write_all(&bytes).map_err(|error| {
                format!("failed to write snapshot path {}: {error}", entry.path)
            })?;
            file.sync_all().map_err(|error| {
                format!("failed to flush snapshot path {}: {error}", entry.path)
            })?;
            set_executable(&target, entry.executable)?;
        }
    }
    Ok(())
}

fn verify_materialized_entries(root: &Path, snapshot: &SourceSnapshotV1) -> Result<(), String> {
    for entry in &snapshot.entries {
        let target = ensure_existing_safe_parent_chain(root, &entry.path)?;
        match entry.operation {
            SourceSnapshotOperationV1::Delete => match fs::symlink_metadata(&target) {
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
                Ok(_) => {
                    return Err(format!(
                        "source snapshot delete verification failed: {} still exists",
                        entry.path
                    ))
                }
                Err(error) => {
                    return Err(format!(
                        "failed to verify snapshot deletion {}: {error}",
                        entry.path
                    ))
                }
            },
            SourceSnapshotOperationV1::Upsert => {
                let metadata = fs::symlink_metadata(&target).map_err(|error| {
                    format!("failed to verify snapshot path {}: {error}", entry.path)
                })?;
                if metadata.file_type().is_symlink() || !metadata.file_type().is_file() {
                    return Err(format!(
                        "materialized snapshot path is not a regular file: {}",
                        entry.path
                    ));
                }
                let content = fs::read(&target).map_err(|error| {
                    format!("failed to verify snapshot bytes {}: {error}", entry.path)
                })?;
                if Some(sha256_hex(&content).as_str()) != entry.content_sha256.as_deref() {
                    return Err(format!(
                        "materialized snapshot hash mismatch: {}",
                        entry.path
                    ));
                }
                if executable_metadata(&metadata, entry.executable) != entry.executable {
                    return Err(format!(
                        "materialized snapshot executable bit mismatch: {}",
                        entry.path
                    ));
                }
            }
        }
    }
    Ok(())
}

fn ensure_safe_parent_chain(root: &Path, relative: &str) -> Result<PathBuf, String> {
    let mut components = relative.split('/').collect::<Vec<_>>();
    let file_name = components
        .pop()
        .ok_or_else(|| "source snapshot path is empty".to_string())?;
    let mut current = root.to_path_buf();
    for component in components {
        current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) => {
                if metadata.file_type().is_symlink() || !metadata.file_type().is_dir() {
                    return Err(format!(
                        "source snapshot parent is not a safe directory: {}",
                        current.display()
                    ));
                }
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                fs::create_dir(&current).map_err(|error| {
                    format!(
                        "failed to create snapshot parent {}: {error}",
                        current.display()
                    )
                })?;
            }
            Err(error) => {
                return Err(format!(
                    "failed to inspect snapshot parent {}: {error}",
                    current.display()
                ))
            }
        }
    }
    current.push(file_name);
    Ok(current)
}

fn ensure_existing_safe_parent_chain(root: &Path, relative: &str) -> Result<PathBuf, String> {
    let mut components = relative.split('/').collect::<Vec<_>>();
    let file_name = components
        .pop()
        .ok_or_else(|| "source snapshot path is empty".to_string())?;
    let mut current = root.to_path_buf();
    for component in components {
        current.push(component);
        let metadata = fs::symlink_metadata(&current).map_err(|error| {
            format!(
                "failed to inspect snapshot parent {}: {error}",
                current.display()
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.file_type().is_dir() {
            return Err(format!(
                "source snapshot parent is not a safe directory: {}",
                current.display()
            ));
        }
    }
    current.push(file_name);
    Ok(current)
}

fn join_safe_relative(root: &Path, relative: &str) -> PathBuf {
    let mut path = root.to_path_buf();
    for component in relative.split('/') {
        path.push(component);
    }
    path
}

fn verify_head(project_root: &Path, expected_head: &str) -> Result<(), String> {
    let raw = git_stdout_bounded(
        project_root,
        ["rev-parse", "--verify", "HEAD"],
        GIT_SMALL_OUTPUT_MAX_BYTES,
    )?;
    let actual = std::str::from_utf8(&raw)
        .map_err(|_| "git rev-parse HEAD returned non-UTF8 output".to_string())?
        .trim();
    if actual != expected_head {
        return Err(format!(
            "source snapshot base HEAD mismatch: expected {expected_head}, observed {actual}"
        ));
    }
    Ok(())
}

fn parse_nul_paths(output: &[u8]) -> Result<BTreeSet<String>, String> {
    if !output.is_empty() && output.last() != Some(&0) {
        return Err("Git -z path output was not NUL terminated".to_string());
    }
    let mut paths = BTreeSet::new();
    for raw in output
        .split(|byte| *byte == 0)
        .filter(|part| !part.is_empty())
    {
        let path = std::str::from_utf8(raw)
            .map_err(|_| "source snapshot does not support non-UTF8 Git paths".to_string())?
            .to_string();
        validate_source_snapshot_path(&path)?;
        if !paths.insert(path) {
            return Err("Git returned a duplicate changed path".to_string());
        }
    }
    Ok(paths)
}

fn git_stdout_bounded<const N: usize>(
    project_root: &Path,
    args: [&str; N],
    max_bytes: usize,
) -> Result<Vec<u8>, String> {
    git_stdout_bounded_args(project_root, args.map(OsStr::new), max_bytes)
}

fn git_stdout_bounded_args<I, S>(
    project_root: &Path,
    args: I,
    max_bytes: usize,
) -> Result<Vec<u8>, String>
where
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let mut child = Command::new("git")
        .arg("-C")
        .arg(project_root)
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| format!("failed to start git for source snapshot: {error}"))?;
    let mut stdout = Vec::new();
    child
        .stdout
        .take()
        .ok_or_else(|| "failed to capture git stdout".to_string())?
        .take((max_bytes + 1) as u64)
        .read_to_end(&mut stdout)
        .map_err(|error| format!("failed to read git output: {error}"))?;
    if stdout.len() > max_bytes {
        let _ = child.kill();
        let _ = child.wait();
        return Err("git source snapshot output exceeded the bounded limit".to_string());
    }
    let status = child
        .wait()
        .map_err(|error| format!("failed to wait for git source snapshot command: {error}"))?;
    if !status.success() {
        return Err(format!(
            "git source snapshot command failed with status {:?}",
            status.code()
        ));
    }
    Ok(stdout)
}

fn git_status_args<I, S>(cwd: Option<&Path>, args: I, purpose: &str) -> Result<(), String>
where
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let mut command = Command::new("git");
    if let Some(cwd) = cwd {
        command.arg("-C").arg(cwd);
    }
    let status = command
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|error| format!("failed to {purpose}: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!(
            "failed to {purpose}: git exited with {:?}",
            status.code()
        ))
    }
}

fn ensure_directory(path: &Path) -> Result<(), String> {
    let metadata = fs::metadata(path)
        .map_err(|error| format!("failed to inspect repository {}: {error}", path.display()))?;
    if metadata.is_dir() {
        Ok(())
    } else {
        Err(format!(
            "repository path is not a directory: {}",
            path.display()
        ))
    }
}

#[cfg(unix)]
fn set_executable(path: &Path, executable: bool) -> Result<(), String> {
    use std::os::unix::fs::PermissionsExt;
    let mut permissions = fs::metadata(path)
        .map_err(|error| format!("failed to inspect permissions {}: {error}", path.display()))?
        .permissions();
    permissions.set_mode(if executable { 0o755 } else { 0o644 });
    fs::set_permissions(path, permissions)
        .map_err(|error| format!("failed to set permissions {}: {error}", path.display()))
}

#[cfg(not(unix))]
fn set_executable(_path: &Path, _executable: bool) -> Result<(), String> {
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn git(repo: &Path, args: &[&str]) {
        let status = Command::new("git")
            .arg("-C")
            .arg(repo)
            .args(args)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .unwrap();
        assert!(status.success(), "git {:?} failed", args);
    }

    fn git_text(repo: &Path, args: &[&str]) -> String {
        let output = Command::new("git")
            .arg("-C")
            .arg(repo)
            .args(args)
            .output()
            .unwrap();
        assert!(output.status.success(), "git {:?} failed", args);
        String::from_utf8(output.stdout).unwrap().trim().to_string()
    }

    fn fixture_repo() -> TempDir {
        let temp = tempfile::tempdir().unwrap();
        git(temp.path(), &["init", "-q"]);
        git(
            temp.path(),
            &["config", "user.email", "snapshot@example.invalid"],
        );
        git(temp.path(), &["config", "user.name", "Snapshot Test"]);
        fs::write(temp.path().join("tracked.txt"), b"tracked base\n").unwrap();
        fs::write(temp.path().join("delete.txt"), b"delete base\n").unwrap();
        git(temp.path(), &["add", "tracked.txt", "delete.txt"]);
        git(temp.path(), &["commit", "-q", "-m", "base"]);
        temp
    }

    #[test]
    fn source_snapshot_capture_materialize_preserves_authoritative_checkout() {
        let repo = fixture_repo();
        let head = git_text(repo.path(), &["rev-parse", "HEAD"]);
        fs::write(repo.path().join("tracked.txt"), b"tracked dirty\n").unwrap();
        fs::write(repo.path().join("staged.txt"), b"staged new\n").unwrap();
        git(repo.path(), &["add", "staged.txt"]);
        fs::write(repo.path().join("untracked.txt"), b"untracked\n").unwrap();
        fs::remove_file(repo.path().join("delete.txt")).unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let path = repo.path().join("tracked.txt");
            let mut permissions = fs::metadata(&path).unwrap().permissions();
            permissions.set_mode(0o755);
            fs::set_permissions(path, permissions).unwrap();
        }

        let status_before = git_text(
            repo.path(),
            &["status", "--porcelain=v1", "--untracked-files=all"],
        );
        let index_before = fs::read(repo.path().join(".git").join("index")).unwrap();
        let tracked_before = fs::read(repo.path().join("tracked.txt")).unwrap();

        let snapshot = capture_source_snapshot(repo.path(), &head).unwrap();
        assert_eq!(snapshot.base_git_head, head);
        assert_eq!(snapshot.entries.len(), 4);
        let paths = snapshot
            .entries
            .iter()
            .map(|entry| entry.path.as_str())
            .collect::<Vec<_>>();
        assert_eq!(
            paths,
            vec!["delete.txt", "staged.txt", "tracked.txt", "untracked.txt"]
        );
        let materialized = materialize_source_snapshot(repo.path(), &snapshot).unwrap();
        assert_eq!(materialized.snapshot_sha256(), snapshot.snapshot_sha256);
        assert_eq!(
            fs::read(materialized.root().join("tracked.txt")).unwrap(),
            b"tracked dirty\n"
        );
        assert_eq!(
            fs::read(materialized.root().join("staged.txt")).unwrap(),
            b"staged new\n"
        );
        assert_eq!(
            fs::read(materialized.root().join("untracked.txt")).unwrap(),
            b"untracked\n"
        );
        assert!(!materialized.root().join("delete.txt").exists());
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            assert_ne!(
                fs::metadata(materialized.root().join("tracked.txt"))
                    .unwrap()
                    .permissions()
                    .mode()
                    & 0o111,
                0
            );
        }

        assert_eq!(git_text(repo.path(), &["rev-parse", "HEAD"]), head);
        assert_eq!(
            git_text(
                repo.path(),
                &["status", "--porcelain=v1", "--untracked-files=all"]
            ),
            status_before
        );
        assert_eq!(
            fs::read(repo.path().join(".git").join("index")).unwrap(),
            index_before
        );
        assert_eq!(
            fs::read(repo.path().join("tracked.txt")).unwrap(),
            tracked_before
        );

        let temp_root = materialized.temp_root().to_path_buf();
        assert!(temp_root.exists());
        drop(materialized);
        assert!(!temp_root.exists());
    }

    #[test]
    fn source_snapshot_capture_rejects_concurrent_drift() {
        let repo = fixture_repo();
        let head = git_text(repo.path(), &["rev-parse", "HEAD"]);
        fs::write(repo.path().join("tracked.txt"), b"first dirty value\n").unwrap();
        let tracked = repo.path().join("tracked.txt");
        let result = capture_source_snapshot_with_before_recheck(repo.path(), &head, || {
            fs::write(&tracked, b"second dirty value\n").unwrap();
        });
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("source drift"));
    }

    #[test]
    fn source_snapshot_agent_capture_uses_registered_project_and_rejects_execute() {
        let repo = fixture_repo();
        let head = git_text(repo.path(), &["rev-parse", "HEAD"]);
        fs::write(repo.path().join("tracked.txt"), b"agent dirty\n").unwrap();
        let projects = tempfile::tempdir().unwrap();
        fs::write(
            projects.path().join("demo.toml"),
            format!(
                "id = \"demo\"\npath = {:?}\nallow_patch = true\n",
                repo.path().to_string_lossy()
            ),
        )
        .unwrap();
        let request_for = |payload: SourceSnapshotAgentPayloadV1| ShellAgentShellRequest {
            request_id: "snapshot-test".to_string(),
            client_id: "runner".to_string(),
            kind: SOURCE_SNAPSHOT_AGENT_REQUEST_KIND.to_string(),
            job_id: None,
            cwd: None,
            path: None,
            content: None,
            max_bytes: None,
            expected_sha256: None,
            expected_prefix: None,
            start_line: None,
            end_line: None,
            create_dirs: false,
            command: String::new(),
            process: None,
            script: None,
            stdin: Some(serde_json::to_string(&payload).unwrap()),
            timeout_secs: 30,
            requested_by: "test".to_string(),
            created_at: 0,
            validation: None,
            lsp: None,
            sandbox: None,
            job_context: None,
            persistent_shell: None,
        };

        let capture = request_for(SourceSnapshotAgentPayloadV1::Capture {
            project_id: "demo".to_string(),
            expected_git_head: head,
        });
        let result = handle_source_snapshot_request(projects.path(), &capture);
        assert_eq!(result.exit_code, Some(0), "{:?}", result.error);
        let snapshot: SourceSnapshotV1 =
            serde_json::from_str(result.stdout.as_deref().unwrap()).unwrap();
        snapshot.validate().unwrap();
        assert!(snapshot
            .entries
            .iter()
            .any(|entry| entry.path == "tracked.txt"));

        let execute = request_for(SourceSnapshotAgentPayloadV1::Execute { snapshot });
        let rejected = handle_source_snapshot_request(projects.path(), &execute);
        assert_eq!(rejected.exit_code, Some(1));
        assert_eq!(
            rejected.error.as_deref(),
            Some("source_snapshot_execute_not_enabled")
        );
    }

    #[cfg(unix)]
    #[test]
    fn source_snapshot_capture_rejects_symlink_changes() {
        use std::os::unix::fs::symlink;

        let repo = fixture_repo();
        let head = git_text(repo.path(), &["rev-parse", "HEAD"]);
        fs::remove_file(repo.path().join("tracked.txt")).unwrap();
        symlink("delete.txt", repo.path().join("tracked.txt")).unwrap();
        let result = capture_source_snapshot(repo.path(), &head);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("regular files"));
    }
}
