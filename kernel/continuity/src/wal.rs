//! WAL (Write-Ahead Log) for delta atomicity (L1_CONTINUITY §4).
//!
//! ## Doctrine
//!
//! Per L1_CONTINUITY §4.1: a delta is either fully absorbed (event committed
//! with all causal edges) or not absorbed. The WAL provides the atomicity
//! mechanism:
//!
//! - Delta absorption writes to WAL first.
//! - DAG node creation + edge insertion + index update = single transaction.
//! - Cycle completion bumps DAG-tip atomically.
//! - On crash: WAL replayed on restart; incomplete cycles detected (WAL
//!   entries past DAG-tip) and rolled back.
//!
//! Per L1_CONTINUITY §4.2: crash detection on restart:
//!
//! 1. Read WAL.
//! 2. Compare to last persisted DAG-tip.
//! 3. WAL has uncommitted entries past DAG-tip:
//!    - Replay succeeds → enter cold-resume with `crashed_recovered` marker.
//!    - Replay fails → enter cold-resume with `crashed_unrecoverable` marker.
//! 4. Each crashed delta's recovery status fruits a `delta_recovery`
//!    sporocarp (committed / rolled-back / dead-letter).
//!
//! ## M3 scope
//!
//! In-memory WAL only. Per L1_CONTINUITY §6: production WAL implementation
//! is L4-platform-pick within {filesystem-level, embedded library, custom
//! append log}. M3 ships the LOGIC layer; M4 plugs disk persistence.

use myco_kernel_shared::canonical_bytes::CanonicalBytes;
use myco_kernel_shared::crypto::NodeHash;
use thiserror::Error;

/// WAL errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum WalError {
    /// Attempt to commit a WAL entry that doesn't exist.
    #[error("WAL entry not found at sequence {0}")]
    EntryNotFound(u64),

    /// Attempt to commit an entry that has already been committed.
    #[error("WAL entry at sequence {0} already committed")]
    AlreadyCommitted(u64),

    /// Attempt to roll back a committed entry.
    #[error("cannot roll back committed entry at sequence {0}")]
    CannotRollbackCommitted(u64),
}

/// State of a single WAL entry.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum WalEntryState {
    /// Pending: written to WAL but not yet committed (DAG-tip not yet
    /// advanced past this entry).
    Pending,
    /// Committed: DAG-tip has advanced past this entry; the entry survives
    /// crash recovery.
    Committed,
    /// Rolled back: entry was pending at crash time; replay failed OR caller
    /// explicitly rolled back. Entry retained in WAL for observability.
    RolledBack,
}

/// A single WAL entry — represents one delta or one cycle's worth of
/// pending state mutations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WalEntry {
    /// Monotonically-increasing sequence number assigned at append time.
    pub sequence: u64,
    /// Substrate metabolic-cycle at append time.
    pub at_cycle: u64,
    /// Canonical-bytes payload of the entry (substrate-defined format).
    pub payload: CanonicalBytes,
    /// Optional hash of the DAG node produced by this entry (set when
    /// the entry transitions to Committed).
    pub committed_node_hash: Option<NodeHash>,
    /// Current state of the entry.
    pub state: WalEntryState,
}

/// In-memory Write-Ahead Log.
///
/// M3: pure in-memory storage. M4+ wraps with disk persistence.
#[derive(Debug, Clone, Default)]
pub struct InMemoryWal {
    entries: Vec<WalEntry>,
    /// Last sequence number assigned (monotonic; never decreases).
    next_sequence: u64,
}

impl InMemoryWal {
    /// Construct an empty WAL.
    pub fn new() -> Self {
        InMemoryWal::default()
    }

    /// Append a new pending entry. Returns the assigned sequence number.
    pub fn append(&mut self, at_cycle: u64, payload: CanonicalBytes) -> u64 {
        let sequence = self.next_sequence;
        self.next_sequence += 1;
        self.entries.push(WalEntry {
            sequence,
            at_cycle,
            payload,
            committed_node_hash: None,
            state: WalEntryState::Pending,
        });
        sequence
    }

    /// Mark a pending entry as committed (after DAG insertion succeeded).
    pub fn commit(&mut self, sequence: u64, node_hash: NodeHash) -> Result<(), WalError> {
        let entry = self
            .entries
            .iter_mut()
            .find(|e| e.sequence == sequence)
            .ok_or(WalError::EntryNotFound(sequence))?;

        match entry.state {
            WalEntryState::Pending => {
                entry.state = WalEntryState::Committed;
                entry.committed_node_hash = Some(node_hash);
                Ok(())
            }
            WalEntryState::Committed => Err(WalError::AlreadyCommitted(sequence)),
            WalEntryState::RolledBack => Err(WalError::CannotRollbackCommitted(sequence)),
        }
    }

    /// Mark a pending entry as rolled back (e.g., DAG insertion failed
    /// mid-cycle, or post-crash replay couldn't reconstruct).
    pub fn rollback(&mut self, sequence: u64) -> Result<(), WalError> {
        let entry = self
            .entries
            .iter_mut()
            .find(|e| e.sequence == sequence)
            .ok_or(WalError::EntryNotFound(sequence))?;

        match entry.state {
            WalEntryState::Pending => {
                entry.state = WalEntryState::RolledBack;
                Ok(())
            }
            WalEntryState::Committed => Err(WalError::CannotRollbackCommitted(sequence)),
            WalEntryState::RolledBack => Ok(()), // idempotent
        }
    }

    /// All entries in append order (committed + pending + rolled back).
    pub fn entries(&self) -> &[WalEntry] {
        &self.entries
    }

    /// Pending entries (those needing recovery action at cold-resume).
    pub fn pending_entries(&self) -> Vec<&WalEntry> {
        self.entries
            .iter()
            .filter(|e| e.state == WalEntryState::Pending)
            .collect()
    }

    /// Total entry count.
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Whether the WAL is empty.
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Lookup an entry by sequence.
    pub fn get(&self, sequence: u64) -> Option<&WalEntry> {
        self.entries.iter().find(|e| e.sequence == sequence)
    }

    /// Statistics on entry states.
    pub fn state_counts(&self) -> (usize, usize, usize) {
        let mut pending = 0;
        let mut committed = 0;
        let mut rolled_back = 0;
        for e in &self.entries {
            match e.state {
                WalEntryState::Pending => pending += 1,
                WalEntryState::Committed => committed += 1,
                WalEntryState::RolledBack => rolled_back += 1,
            }
        }
        (pending, committed, rolled_back)
    }
}

/// Recovery action determined by replaying a WAL entry post-crash.
///
/// Per L1_CONTINUITY §4.2: each crashed delta fruits a `delta_recovery`
/// sporocarp with one of these recovery actions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum RecoveryAction {
    /// The entry's effects are already in the DAG; mark as committed.
    AlreadyCommitted,
    /// Replay succeeded; commit the entry.
    ReplayCommit,
    /// Replay failed; roll back the entry.
    ReplayRollback,
    /// Replay couldn't determine outcome; dead-letter the entry.
    DeadLetter,
}

/// Recovery report for one WAL entry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RecoveryReport {
    /// Which WAL entry this report concerns.
    pub sequence: u64,
    /// Action taken.
    pub action: RecoveryAction,
    /// Reason / description for observability.
    pub reason: String,
}

/// Trait for the per-entry replay decision logic.
///
/// M3 ships the orchestration; M4 wires concrete replay logic that
/// consults the DAG to see if the entry's effects are already present.
pub trait WalReplayDecider {
    /// Decide what to do with a pending WAL entry post-crash.
    fn decide(&mut self, entry: &WalEntry) -> RecoveryReport;
}

/// Replay all pending WAL entries post-crash.
///
/// For each pending entry: calls the decider; applies the decided action
/// to the WAL state; returns the recovery reports for sporocarp emission.
pub fn replay_pending(
    wal: &mut InMemoryWal,
    decider: &mut dyn WalReplayDecider,
) -> Vec<RecoveryReport> {
    let pending_sequences: Vec<u64> = wal.pending_entries().iter().map(|e| e.sequence).collect();

    let mut reports = Vec::with_capacity(pending_sequences.len());

    for seq in pending_sequences {
        let entry = wal.get(seq).expect("pending entry exists").clone();
        let report = decider.decide(&entry);

        match report.action {
            RecoveryAction::AlreadyCommitted | RecoveryAction::ReplayCommit => {
                // Commit needs a node_hash; for AlreadyCommitted we use the
                // entry's existing committed_node_hash if any; otherwise a
                // placeholder. Real M4 integration provides the hash.
                let hash = entry
                    .committed_node_hash
                    .unwrap_or_else(|| NodeHash::from_bytes([0u8; 32]));
                let _ = wal.commit(seq, hash);
            }
            RecoveryAction::ReplayRollback | RecoveryAction::DeadLetter => {
                let _ = wal.rollback(seq);
            }
        }
        reports.push(report);
    }

    reports
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{encode, Value};

    fn make_payload(s: &str) -> CanonicalBytes {
        encode(&Value::String(s.to_string())).unwrap()
    }

    fn make_hash(byte: u8) -> NodeHash {
        NodeHash::from_bytes([byte; 32])
    }

    #[test]
    fn test_new_wal_is_empty() {
        let wal = InMemoryWal::new();
        assert!(wal.is_empty());
        assert_eq!(wal.len(), 0);
    }

    #[test]
    fn test_append_assigns_monotonic_sequence() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        let s2 = wal.append(10, make_payload("b"));
        let s3 = wal.append(11, make_payload("c"));
        assert_eq!(s1, 0);
        assert_eq!(s2, 1);
        assert_eq!(s3, 2);
        assert_eq!(wal.len(), 3);
    }

    #[test]
    fn test_commit_transitions_state() {
        let mut wal = InMemoryWal::new();
        let s = wal.append(10, make_payload("a"));
        assert_eq!(wal.get(s).unwrap().state, WalEntryState::Pending);
        wal.commit(s, make_hash(0xab)).unwrap();
        assert_eq!(wal.get(s).unwrap().state, WalEntryState::Committed);
        assert_eq!(
            wal.get(s).unwrap().committed_node_hash,
            Some(make_hash(0xab))
        );
    }

    #[test]
    fn test_commit_unknown_sequence_errors() {
        let mut wal = InMemoryWal::new();
        let result = wal.commit(99, make_hash(0xab));
        assert_eq!(result, Err(WalError::EntryNotFound(99)));
    }

    #[test]
    fn test_double_commit_errors() {
        let mut wal = InMemoryWal::new();
        let s = wal.append(10, make_payload("a"));
        wal.commit(s, make_hash(0xab)).unwrap();
        let result = wal.commit(s, make_hash(0xcd));
        assert_eq!(result, Err(WalError::AlreadyCommitted(s)));
    }

    #[test]
    fn test_rollback_transitions_state() {
        let mut wal = InMemoryWal::new();
        let s = wal.append(10, make_payload("a"));
        wal.rollback(s).unwrap();
        assert_eq!(wal.get(s).unwrap().state, WalEntryState::RolledBack);
    }

    #[test]
    fn test_rollback_committed_errors() {
        let mut wal = InMemoryWal::new();
        let s = wal.append(10, make_payload("a"));
        wal.commit(s, make_hash(0xab)).unwrap();
        let result = wal.rollback(s);
        assert_eq!(result, Err(WalError::CannotRollbackCommitted(s)));
    }

    #[test]
    fn test_rollback_idempotent_on_already_rolled_back() {
        let mut wal = InMemoryWal::new();
        let s = wal.append(10, make_payload("a"));
        wal.rollback(s).unwrap();
        wal.rollback(s).unwrap(); // idempotent
        assert_eq!(wal.get(s).unwrap().state, WalEntryState::RolledBack);
    }

    #[test]
    fn test_pending_entries_filter() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        let s2 = wal.append(10, make_payload("b"));
        let s3 = wal.append(10, make_payload("c"));
        wal.commit(s1, make_hash(0xab)).unwrap();
        wal.rollback(s2).unwrap();

        let pending: Vec<u64> = wal.pending_entries().iter().map(|e| e.sequence).collect();
        assert_eq!(pending, vec![s3]);
    }

    #[test]
    fn test_state_counts() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        wal.append(10, make_payload("b"));
        let s3 = wal.append(10, make_payload("c"));
        wal.commit(s1, make_hash(0xab)).unwrap();
        wal.rollback(s3).unwrap();

        let (pending, committed, rolled_back) = wal.state_counts();
        assert_eq!(pending, 1);
        assert_eq!(committed, 1);
        assert_eq!(rolled_back, 1);
    }

    /// Replay decider that commits everything (post-crash replay succeeded).
    struct CommitAllDecider;
    impl WalReplayDecider for CommitAllDecider {
        fn decide(&mut self, entry: &WalEntry) -> RecoveryReport {
            RecoveryReport {
                sequence: entry.sequence,
                action: RecoveryAction::ReplayCommit,
                reason: "test commit all".to_string(),
            }
        }
    }

    /// Replay decider that rolls back everything (post-crash replay failed).
    struct RollbackAllDecider;
    impl WalReplayDecider for RollbackAllDecider {
        fn decide(&mut self, entry: &WalEntry) -> RecoveryReport {
            RecoveryReport {
                sequence: entry.sequence,
                action: RecoveryAction::ReplayRollback,
                reason: "test rollback all".to_string(),
            }
        }
    }

    #[test]
    fn test_replay_commits_pending_entries() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        let s2 = wal.append(10, make_payload("b"));

        let reports = replay_pending(&mut wal, &mut CommitAllDecider);
        assert_eq!(reports.len(), 2);
        assert_eq!(wal.get(s1).unwrap().state, WalEntryState::Committed);
        assert_eq!(wal.get(s2).unwrap().state, WalEntryState::Committed);
    }

    #[test]
    fn test_replay_rolls_back_pending_entries() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        let s2 = wal.append(10, make_payload("b"));

        let reports = replay_pending(&mut wal, &mut RollbackAllDecider);
        assert_eq!(reports.len(), 2);
        assert_eq!(wal.get(s1).unwrap().state, WalEntryState::RolledBack);
        assert_eq!(wal.get(s2).unwrap().state, WalEntryState::RolledBack);
    }

    #[test]
    fn test_replay_skips_already_committed() {
        let mut wal = InMemoryWal::new();
        let s1 = wal.append(10, make_payload("a"));
        wal.commit(s1, make_hash(0xab)).unwrap();
        let s2 = wal.append(10, make_payload("b"));

        let reports = replay_pending(&mut wal, &mut CommitAllDecider);
        // Only s2 is pending; s1 was already committed.
        assert_eq!(reports.len(), 1);
        assert_eq!(reports[0].sequence, s2);
    }
}
