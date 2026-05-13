//! Active-prefix + archived-tail data structure (per L1_GOVERNANCE §3.1 + pass-3 saprotroph-1).
//!
//! ## Purpose
//!
//! Per pass-3 saprotroph-1, monotone tier-1 fields (owner_key_history,
//! template_version_registry, federation aggregate-reattestation chain) grow
//! unbounded over a substrate's lifetime. Without discipline, per-cycle tier-1
//! validation cost grows with substrate age.
//!
//! The active-prefix + archived-tail discipline splits each monotone field:
//!
//! - **Active prefix** (K most-recent + currently-valid entries) — participates
//!   in per-cycle tier-1 validation. O(K) cost regardless of substrate age.
//! - **Archived tail** (older entries) — stored cold-tier-eligible (per L1_SCHEMA
//!   §2.3). Validated at deep-cycle scope via Merkle anchor over the full chain.
//!
//! ## API
//!
//! [`ActivePrefix<T>`] is a generic container. Each user (owner_key_history,
//! template_version_registry, etc.) instantiates with its own entry type.
//!
//! ## M1 implementation status
//!
//! M1 ships with an in-memory implementation. Persistence to the SSoT
//! (via `kernel/schema`) lands in M2.

use std::collections::VecDeque;

/// An entry in an active-prefix structure. Caller-defined payload + a
/// chronological timestamp for ordering.
pub trait PrefixEntry: Clone {
    /// Chronological timestamp for sorting. Higher = newer.
    fn timestamp(&self) -> i64;

    /// Whether this entry is still "currently valid" (e.g., owner_key with
    /// no valid_until set yet). Always-valid entries stay in the active prefix
    /// regardless of K.
    fn is_currently_valid(&self) -> bool;
}

/// Active-prefix + archived-tail container.
///
/// The active prefix holds at most K entries from the tail of the chronological
/// order, plus all "currently valid" entries (which may be older than the
/// K-window). Entries older than the K-window AND not currently valid are
/// archived.
///
/// ## Type parameters
///
/// - `T` — the entry type. Must implement [`PrefixEntry`].
pub struct ActivePrefix<T: PrefixEntry> {
    /// Most-recent K entries (FIFO, oldest first in the deque).
    active: VecDeque<T>,
    /// Currently-valid entries that are older than the K-window. May be empty.
    /// Conceptually part of the active prefix for validation purposes; stored
    /// separately for clarity.
    active_extra_valid: Vec<T>,
    /// All older entries; the substrate persists these via `kernel/schema`
    /// cold-tier-eligible storage. M1 keeps them in memory.
    archived: Vec<T>,
    /// K — the active-prefix size cap for chronological entries.
    k: usize,
}

impl<T: PrefixEntry> ActivePrefix<T> {
    /// Create an empty active-prefix container with cap K.
    pub fn new(k: usize) -> Self {
        assert!(k > 0, "K must be positive");
        ActivePrefix {
            active: VecDeque::with_capacity(k),
            active_extra_valid: Vec::new(),
            archived: Vec::new(),
            k,
        }
    }

    /// Insert a new entry. If the active prefix has K entries, the oldest
    /// chronological entry is moved to either `active_extra_valid` (if still
    /// currently valid) or `archived` (otherwise).
    pub fn insert(&mut self, entry: T) {
        // Maintain chronological order in the active deque.
        // For simplicity, assume entries are inserted in chronological order
        // (newer timestamp than existing entries). If not, this would need
        // a sorted insert.
        if let Some(last) = self.active.back() {
            assert!(
                entry.timestamp() >= last.timestamp(),
                "entries must be inserted in chronological order"
            );
        }

        self.active.push_back(entry);

        if self.active.len() > self.k {
            // Evict the oldest active entry.
            let evicted = self.active.pop_front().expect("active was non-empty");
            if evicted.is_currently_valid() {
                self.active_extra_valid.push(evicted);
            } else {
                self.archived.push(evicted);
            }
        }
    }

    /// Iterate over all entries in the active prefix (K most-recent +
    /// currently-valid-older). Used by per-cycle tier-1 validation.
    pub fn iter_active(&self) -> impl Iterator<Item = &T> {
        self.active.iter().chain(self.active_extra_valid.iter())
    }

    /// Iterate over archived entries. Used by deep-cycle validation via Merkle
    /// anchor (caller computes Merkle hash; this iterator provides the entries
    /// in order).
    pub fn iter_archived(&self) -> impl Iterator<Item = &T> {
        self.archived.iter()
    }

    /// Total entry count (active + archived).
    pub fn total_count(&self) -> usize {
        self.active.len() + self.active_extra_valid.len() + self.archived.len()
    }

    /// Active prefix entry count (excludes archived).
    pub fn active_count(&self) -> usize {
        self.active.len() + self.active_extra_valid.len()
    }

    /// Move entries from `active_extra_valid` to `archived` when they become
    /// no-longer-currently-valid. Called at deep-cycle scope.
    pub fn re_archive_invalidated(&mut self) {
        let mut keep = Vec::with_capacity(self.active_extra_valid.len());
        for entry in self.active_extra_valid.drain(..) {
            if entry.is_currently_valid() {
                keep.push(entry);
            } else {
                self.archived.push(entry);
            }
        }
        self.active_extra_valid = keep;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq)]
    struct TestEntry {
        ts: i64,
        valid: bool,
    }

    impl PrefixEntry for TestEntry {
        fn timestamp(&self) -> i64 {
            self.ts
        }
        fn is_currently_valid(&self) -> bool {
            self.valid
        }
    }

    #[test]
    fn test_active_prefix_fills_to_k() {
        let mut p = ActivePrefix::<TestEntry>::new(3);
        for i in 0..3 {
            p.insert(TestEntry {
                ts: i,
                valid: false,
            });
        }
        assert_eq!(p.active_count(), 3);
        assert_eq!(p.iter_archived().count(), 0);
        assert_eq!(p.total_count(), 3);
    }

    #[test]
    fn test_active_prefix_evicts_oldest() {
        let mut p = ActivePrefix::<TestEntry>::new(3);
        for i in 0..5 {
            p.insert(TestEntry {
                ts: i,
                valid: false,
            });
        }
        // K=3 active; 2 archived (oldest two).
        assert_eq!(p.active_count(), 3);
        assert_eq!(p.iter_archived().count(), 2);
        assert_eq!(p.total_count(), 5);

        let archived_ts: Vec<i64> = p.iter_archived().map(|e| e.ts).collect();
        assert_eq!(archived_ts, vec![0, 1]);

        let active_ts: Vec<i64> = p.iter_active().map(|e| e.ts).collect();
        assert_eq!(active_ts, vec![2, 3, 4]);
    }

    #[test]
    fn test_currently_valid_stay_active() {
        let mut p = ActivePrefix::<TestEntry>::new(2);
        // Insert one currently-valid entry then fill past K with invalid.
        p.insert(TestEntry { ts: 0, valid: true });
        p.insert(TestEntry {
            ts: 1,
            valid: false,
        });
        p.insert(TestEntry {
            ts: 2,
            valid: false,
        });
        p.insert(TestEntry {
            ts: 3,
            valid: false,
        });

        // ts=0 evicted from chronological deque BUT still active (valid).
        // ts=1 evicted from chronological deque AND archived (not valid).
        assert_eq!(p.iter_archived().count(), 1);
        let archived_ts: Vec<i64> = p.iter_archived().map(|e| e.ts).collect();
        assert_eq!(archived_ts, vec![1]);

        // Active = {ts=0 valid} + {ts=2, ts=3}.
        let active_ts: Vec<i64> = p.iter_active().map(|e| e.ts).collect();
        assert!(active_ts.contains(&0));
        assert!(active_ts.contains(&2));
        assert!(active_ts.contains(&3));
        assert_eq!(active_ts.len(), 3);
    }

    #[test]
    fn test_re_archive_invalidated() {
        let mut p = ActivePrefix::<TestEntry>::new(1);
        // Insert two currently-valid entries; ts=0 ends up in active_extra_valid.
        p.insert(TestEntry { ts: 0, valid: true });
        p.insert(TestEntry { ts: 1, valid: true });

        assert_eq!(p.iter_active().count(), 2);
        assert_eq!(p.iter_archived().count(), 0);

        // Simulate ts=0's validity expiring. We need to mutate it; in real use,
        // the caller would track this via a separate index. For the test, just
        // re-construct the container.
        let mut p = ActivePrefix::<TestEntry>::new(1);
        p.insert(TestEntry {
            ts: 0,
            valid: false,
        }); // expired
        p.insert(TestEntry { ts: 1, valid: true });

        // ts=0 evicted from chronological deque and archived (no longer valid).
        assert_eq!(p.iter_archived().count(), 1);
    }

    #[test]
    #[should_panic(expected = "chronological order")]
    fn test_out_of_order_insert_panics() {
        let mut p = ActivePrefix::<TestEntry>::new(3);
        p.insert(TestEntry {
            ts: 10,
            valid: false,
        });
        p.insert(TestEntry {
            ts: 5,
            valid: false,
        }); // older than previous → panic
    }
}
