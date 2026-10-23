//! Bounded immutable source snapshots for exact dirty-source validation.
//!
//! The snapshot is deliberately small and content-addressed. It is not a CAS,
//! archive format, or writable workspace abstraction: it describes only the
//! bounded regular-file delta from one exact Git commit.

use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use base64::Engine as _;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

use crate::shell_protocol::valid_exact_git_oid;

pub const SOURCE_SNAPSHOT_SCHEMA_VERSION: u64 = 1;
pub const SOURCE_SNAPSHOT_AGENT_REQUEST_KIND: &str = "source_snapshot";
pub const SOURCE_SNAPSHOT_MAX_ENTRIES: usize = 128;
pub const SOURCE_SNAPSHOT_MAX_PATH_BYTES: usize = 1024;
pub const SOURCE_SNAPSHOT_MAX_FILE_BYTES: usize = 64 * 1024;
pub const SOURCE_SNAPSHOT_MAX_TOTAL_BYTES: usize = 128 * 1024;
pub const SOURCE_SNAPSHOT_MAX_SERIALIZED_BYTES: usize = 224 * 1024;

const SNAPSHOT_DIGEST_DOMAIN: &[u8] = b"webcodex-source-snapshot-v1\0";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceSnapshotOperationV1 {
    Upsert,
    Delete,
}

/// Transient Agent transport payload. This value may live in a pending
/// request, but must never be copied into durable Job/inventory metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum SourceSnapshotAgentPayloadV1 {
    Capture {
        project_id: String,
        expected_git_head: String,
    },
    Execute {
        snapshot: SourceSnapshotV1,
    },
}

impl SourceSnapshotAgentPayloadV1 {
    pub fn validate(&self) -> Result<(), String> {
        match self {
            Self::Capture {
                project_id,
                expected_git_head,
            } => {
                if project_id.is_empty()
                    || matches!(project_id.as_str(), "." | "..")
                    || !project_id.bytes().all(|byte| {
                        byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.')
                    })
                {
                    return Err("source snapshot capture requires a safe project id".to_string());
                }
                if !valid_exact_git_oid(expected_git_head) {
                    return Err("source snapshot capture requires a full Git object id".to_string());
                }
                Ok(())
            }
            Self::Execute { snapshot } => snapshot.validate(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceSnapshotEntryV1 {
    pub path: String,
    pub operation: SourceSnapshotOperationV1,
    #[serde(default)]
    pub executable: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_bytes: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_base64: Option<String>,
}

impl SourceSnapshotEntryV1 {
    pub fn upsert(
        path: impl Into<String>,
        content: &[u8],
        executable: bool,
    ) -> Result<Self, String> {
        let path = path.into();
        validate_source_snapshot_path(&path)?;
        if content.len() > SOURCE_SNAPSHOT_MAX_FILE_BYTES {
            return Err(format!(
                "source snapshot file exceeds {} bytes",
                SOURCE_SNAPSHOT_MAX_FILE_BYTES
            ));
        }
        Ok(Self {
            path,
            operation: SourceSnapshotOperationV1::Upsert,
            executable,
            content_bytes: Some(content.len() as u64),
            content_sha256: Some(sha256_hex(content)),
            content_base64: Some(BASE64_STANDARD.encode(content)),
        })
    }

    pub fn delete(path: impl Into<String>) -> Result<Self, String> {
        let path = path.into();
        validate_source_snapshot_path(&path)?;
        Ok(Self {
            path,
            operation: SourceSnapshotOperationV1::Delete,
            executable: false,
            content_bytes: None,
            content_sha256: None,
            content_base64: None,
        })
    }

    pub fn decoded_content(&self) -> Result<Option<Vec<u8>>, String> {
        match self.operation {
            SourceSnapshotOperationV1::Delete => Ok(None),
            SourceSnapshotOperationV1::Upsert => {
                let encoded = self.content_base64.as_deref().ok_or_else(|| {
                    "source snapshot upsert is missing content_base64".to_string()
                })?;
                let decoded = BASE64_STANDARD
                    .decode(encoded)
                    .map_err(|_| "source snapshot content_base64 is invalid".to_string())?;
                if BASE64_STANDARD.encode(&decoded) != encoded {
                    return Err("source snapshot content_base64 is not canonical".to_string());
                }
                Ok(Some(decoded))
            }
        }
    }

    fn validate(&self) -> Result<usize, String> {
        validate_source_snapshot_path(&self.path)?;
        match self.operation {
            SourceSnapshotOperationV1::Delete => {
                if self.executable
                    || self.content_bytes.is_some()
                    || self.content_sha256.is_some()
                    || self.content_base64.is_some()
                {
                    return Err(
                        "source snapshot delete must not carry file content metadata".to_string(),
                    );
                }
                Ok(0)
            }
            SourceSnapshotOperationV1::Upsert => {
                let expected_bytes = self
                    .content_bytes
                    .ok_or_else(|| "source snapshot upsert is missing content_bytes".to_string())?;
                let expected_hash = self.content_sha256.as_deref().ok_or_else(|| {
                    "source snapshot upsert is missing content_sha256".to_string()
                })?;
                if !valid_sha256_hex(expected_hash) {
                    return Err(
                        "source snapshot content_sha256 must be lowercase SHA-256 hex".to_string(),
                    );
                }
                let decoded = self
                    .decoded_content()?
                    .expect("upsert decoded_content must return bytes");
                if decoded.len() > SOURCE_SNAPSHOT_MAX_FILE_BYTES {
                    return Err(format!(
                        "source snapshot file exceeds {} bytes",
                        SOURCE_SNAPSHOT_MAX_FILE_BYTES
                    ));
                }
                if expected_bytes != decoded.len() as u64 {
                    return Err(
                        "source snapshot content_bytes does not match decoded content".to_string(),
                    );
                }
                if sha256_hex(&decoded) != expected_hash {
                    return Err("source snapshot content hash mismatch".to_string());
                }
                Ok(decoded.len())
            }
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceSnapshotV1 {
    pub schema_version: u64,
    pub base_git_head: String,
    pub entries: Vec<SourceSnapshotEntryV1>,
    pub snapshot_sha256: String,
}

impl SourceSnapshotV1 {
    pub fn from_entries(
        base_git_head: impl Into<String>,
        mut entries: Vec<SourceSnapshotEntryV1>,
    ) -> Result<Self, String> {
        let base_git_head = base_git_head.into();
        entries.sort_by(|left, right| left.path.cmp(&right.path));
        let mut snapshot = Self {
            schema_version: SOURCE_SNAPSHOT_SCHEMA_VERSION,
            base_git_head,
            entries,
            snapshot_sha256: String::new(),
        };
        snapshot.validate_structure()?;
        snapshot.snapshot_sha256 = snapshot.canonical_digest();
        snapshot.validate()?;
        Ok(snapshot)
    }

    pub fn validate(&self) -> Result<(), String> {
        self.validate_structure()?;
        if !valid_sha256_hex(&self.snapshot_sha256) {
            return Err("source snapshot digest must be lowercase SHA-256 hex".to_string());
        }
        if self.canonical_digest() != self.snapshot_sha256 {
            return Err("source snapshot digest mismatch".to_string());
        }
        let serialized_bytes = serde_json::to_vec(self)
            .map_err(|error| format!("failed to serialize source snapshot: {error}"))?
            .len();
        if serialized_bytes > SOURCE_SNAPSHOT_MAX_SERIALIZED_BYTES {
            return Err(format!(
                "source snapshot serialized payload exceeds {} bytes",
                SOURCE_SNAPSHOT_MAX_SERIALIZED_BYTES
            ));
        }
        Ok(())
    }

    pub fn canonical_digest(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(SNAPSHOT_DIGEST_DOMAIN);
        hasher.update(self.schema_version.to_be_bytes());
        update_len_prefixed(&mut hasher, self.base_git_head.as_bytes());
        hasher.update((self.entries.len() as u64).to_be_bytes());
        for entry in &self.entries {
            update_len_prefixed(&mut hasher, entry.path.as_bytes());
            hasher.update([match entry.operation {
                SourceSnapshotOperationV1::Upsert => 1,
                SourceSnapshotOperationV1::Delete => 2,
            }]);
            hasher.update([u8::from(entry.executable)]);
            hasher.update(entry.content_bytes.unwrap_or(0).to_be_bytes());
            match entry.content_sha256.as_deref() {
                Some(hash) => update_len_prefixed(&mut hasher, hash.as_bytes()),
                None => update_len_prefixed(&mut hasher, b""),
            }
        }
        format!("{:x}", hasher.finalize())
    }

    fn validate_structure(&self) -> Result<(), String> {
        if self.schema_version != SOURCE_SNAPSHOT_SCHEMA_VERSION {
            return Err("unsupported source snapshot schema version".to_string());
        }
        if !valid_exact_git_oid(&self.base_git_head) {
            return Err("source snapshot base_git_head must be a full Git object id".to_string());
        }
        if self.entries.is_empty() {
            return Err("source snapshot must contain at least one changed entry".to_string());
        }
        if self.entries.len() > SOURCE_SNAPSHOT_MAX_ENTRIES {
            return Err(format!(
                "source snapshot exceeds {} entries",
                SOURCE_SNAPSHOT_MAX_ENTRIES
            ));
        }

        let mut previous: Option<&str> = None;
        let mut case_folded = BTreeSet::new();
        let mut total_bytes = 0usize;
        for entry in &self.entries {
            if let Some(previous) = previous {
                if entry.path.as_str() <= previous {
                    return Err(
                        "source snapshot entries must be strictly path-sorted and unique"
                            .to_string(),
                    );
                }
            }
            previous = Some(&entry.path);
            let folded = entry.path.to_ascii_lowercase();
            if !case_folded.insert(folded) {
                return Err("source snapshot contains case-fold-colliding paths".to_string());
            }
            total_bytes = total_bytes
                .checked_add(entry.validate()?)
                .ok_or_else(|| "source snapshot total content size overflow".to_string())?;
            if total_bytes > SOURCE_SNAPSHOT_MAX_TOTAL_BYTES {
                return Err(format!(
                    "source snapshot exceeds {} decoded bytes",
                    SOURCE_SNAPSHOT_MAX_TOTAL_BYTES
                ));
            }
        }
        Ok(())
    }
}

fn is_windows_reserved_device_component(component: &str) -> bool {
    let basename = component
        .split_once('.')
        .map_or(component, |(basename, _)| basename);
    let upper = basename.to_ascii_uppercase();
    if matches!(upper.as_str(), "CON" | "PRN" | "AUX" | "NUL") {
        return true;
    }
    let bytes = upper.as_bytes();
    bytes.len() == 4
        && (bytes.starts_with(b"COM") || bytes.starts_with(b"LPT"))
        && matches!(bytes[3], b'1'..=b'9')
}

pub fn validate_source_snapshot_path(path: &str) -> Result<(), String> {
    if path.is_empty() || path.len() > SOURCE_SNAPSHOT_MAX_PATH_BYTES {
        return Err("source snapshot path is empty or too long".to_string());
    }
    if path.starts_with('/') || path.starts_with('\\') || path.contains('\\') || path.contains(':')
    {
        return Err("source snapshot path must be a portable project-relative path".to_string());
    }
    if path.chars().any(|ch| ch == '\0' || ch.is_control()) {
        return Err("source snapshot path contains a control character".to_string());
    }
    for component in path.split('/') {
        if component.is_empty()
            || component == "."
            || component == ".."
            || component.eq_ignore_ascii_case(".git")
            || component.ends_with('.')
            || component.ends_with(' ')
            || is_windows_reserved_device_component(component)
        {
            return Err("source snapshot path contains an unsafe component".to_string());
        }
    }
    Ok(())
}

pub fn sha256_hex(content: &[u8]) -> String {
    format!("{:x}", Sha256::digest(content))
}

fn valid_sha256_hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn update_len_prefixed(hasher: &mut Sha256, value: &[u8]) {
    hasher.update((value.len() as u64).to_be_bytes());
    hasher.update(value);
}

#[cfg(test)]
mod tests {
    use super::*;

    const HEAD: &str = "0123456789abcdef0123456789abcdef01234567";

    #[test]
    fn source_snapshot_contract_roundtrip_and_digest_are_deterministic() {
        let upsert =
            SourceSnapshotEntryV1::upsert("src/lib.rs", b"pub fn value() -> u8 { 2 }\n", false)
                .unwrap();
        let delete = SourceSnapshotEntryV1::delete("obsolete.txt").unwrap();
        let first =
            SourceSnapshotV1::from_entries(HEAD, vec![upsert.clone(), delete.clone()]).unwrap();
        let second = SourceSnapshotV1::from_entries(HEAD, vec![delete, upsert]).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.entries[0].path, "obsolete.txt");
        assert_eq!(first.entries[1].path, "src/lib.rs");
        assert_eq!(first.snapshot_sha256.len(), 64);
        first.validate().unwrap();

        let json = serde_json::to_string(&first).unwrap();
        let decoded: SourceSnapshotV1 = serde_json::from_str(&json).unwrap();
        decoded.validate().unwrap();
        assert_eq!(decoded.snapshot_sha256, first.snapshot_sha256);
    }

    #[test]
    fn source_snapshot_contract_rejects_malformed_unsafe_duplicate_unsorted_and_oversize() {
        for unsafe_path in [
            "../escape",
            "/absolute",
            "dir\\file",
            ".git/config",
            "dir/../file",
            "C:/drive",
            "dir//file",
            "CON",
            "nul.txt",
            "dir/PRN.log",
            "COM1.rs",
            "lpt9",
        ] {
            assert!(
                SourceSnapshotEntryV1::delete(unsafe_path).is_err(),
                "{unsafe_path}"
            );
        }
        for portable_path in ["console.rs", "auxiliary.txt", "com10.txt"] {
            assert!(
                SourceSnapshotEntryV1::delete(portable_path).is_ok(),
                "{portable_path}"
            );
        }
        assert!(SourceSnapshotEntryV1::upsert(
            "large.bin",
            &vec![0u8; SOURCE_SNAPSHOT_MAX_FILE_BYTES + 1],
            false,
        )
        .is_err());

        let a = SourceSnapshotEntryV1::upsert("a.txt", b"a", false).unwrap();
        let b = SourceSnapshotEntryV1::upsert("b.txt", b"b", false).unwrap();
        let valid = SourceSnapshotV1::from_entries(HEAD, vec![a.clone(), b.clone()]).unwrap();

        let mut unsorted = valid.clone();
        unsorted.entries.swap(0, 1);
        assert!(unsorted.validate().is_err());

        let mut duplicate = valid.clone();
        duplicate.entries = vec![a.clone(), a];
        assert!(duplicate.validate().is_err());

        let mut case_collision = valid.clone();
        case_collision.entries = vec![
            SourceSnapshotEntryV1::upsert("A.txt", b"a", false).unwrap(),
            SourceSnapshotEntryV1::upsert("a.txt", b"b", false).unwrap(),
        ];
        case_collision
            .entries
            .sort_by(|left, right| left.path.cmp(&right.path));
        assert!(case_collision.validate().is_err());

        let mut malformed = valid.clone();
        malformed.entries[0].content_base64 = Some("***".to_string());
        assert!(malformed.validate().is_err());

        let mut wrong_hash = valid.clone();
        wrong_hash.entries[0].content_sha256 = Some("0".repeat(64));
        assert!(wrong_hash.validate().is_err());

        let three_chunks = vec![
            SourceSnapshotEntryV1::upsert(
                "one.bin",
                &vec![1u8; SOURCE_SNAPSHOT_MAX_FILE_BYTES],
                false,
            )
            .unwrap(),
            SourceSnapshotEntryV1::upsert(
                "two.bin",
                &vec![2u8; SOURCE_SNAPSHOT_MAX_FILE_BYTES],
                false,
            )
            .unwrap(),
            SourceSnapshotEntryV1::upsert("three.bin", b"x", false).unwrap(),
        ];
        assert!(SourceSnapshotV1::from_entries(HEAD, three_chunks).is_err());
    }

    #[test]
    fn source_snapshot_transport_rejects_oversized_serialization_and_invalid_payloads() {
        let entries = (0..SOURCE_SNAPSHOT_MAX_ENTRIES)
            .map(|index| {
                let path = format!("{:03}-{}.bin", index, "x".repeat(390));
                SourceSnapshotEntryV1::upsert(path, &vec![index as u8; 1024], false).unwrap()
            })
            .collect::<Vec<_>>();
        let error = SourceSnapshotV1::from_entries(HEAD, entries).unwrap_err();
        assert!(error.contains("serialized payload"), "{error}");

        let capture = SourceSnapshotAgentPayloadV1::Capture {
            project_id: "demo".to_string(),
            expected_git_head: HEAD.to_string(),
        };
        capture.validate().unwrap();
        assert!(SourceSnapshotAgentPayloadV1::Capture {
            project_id: "demo".to_string(),
            expected_git_head: "short".to_string(),
        }
        .validate()
        .is_err());
        assert!(SourceSnapshotAgentPayloadV1::Capture {
            project_id: "../demo".to_string(),
            expected_git_head: HEAD.to_string(),
        }
        .validate()
        .is_err());

        let snapshot = SourceSnapshotV1::from_entries(
            HEAD,
            vec![SourceSnapshotEntryV1::upsert("src/lib.rs", b"ok\n", false).unwrap()],
        )
        .unwrap();
        SourceSnapshotAgentPayloadV1::Execute { snapshot }
            .validate()
            .unwrap();
    }
}
