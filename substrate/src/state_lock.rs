//! P09 single-integument enforcement: a process-level exclusive lock on a
//! substrate state directory.
//!
//! Two substrate processes opening the same state directory would race their
//! writes to `dag.cb` / `snapshot.cb` and corrupt the causal DAG. This lock
//! turns that into a clean, early boot failure instead of silent corruption:
//! the first substrate to boot a state dir holds an OS advisory lock for its
//! whole lifetime; a second one fails to acquire and aborts with a clear
//! message.
//!
//! The lock is an OS **advisory** lock bound to an open file handle, so it is
//! released automatically when the process exits OR crashes (the OS closes the
//! handle). A crashed substrate therefore never leaves a stale lock that would
//! block a legitimate restart.
//!
//! Platforms:
//! - Windows: open the lock file with `share_mode(0)` (FILE_SHARE_NONE) so a
//!   second open fails with a sharing violation. Pure std, no `unsafe`.
//! - Unix: `flock(LOCK_EX | LOCK_NB)` on the lock file's fd (one documented
//!   FFI call, narrowly `#[allow(unsafe_code)]` per the crate's FFI-adapter
//!   rule; Windows uses the std path above).

use std::fs::{File, OpenOptions};
use std::io;
use std::path::Path;

/// Name of the lock file created inside the state directory.
pub const LOCK_FILENAME: &str = "substrate.lock";

/// An acquired exclusive lock on a state directory.
///
/// The lock is held for as long as this value is alive; dropping it (or exiting
/// the process) releases it. Store it for the substrate's whole lifetime (e.g.
/// as a binding in `run_loop`).
#[derive(Debug)]
pub struct StateDirLock {
    /// RAII guard: the open lock-file handle. The OS lock is bound to it; it is
    /// released when this handle closes (drop / process exit / crash). Held
    /// purely for that side effect, never read (derive(Debug) does not count for
    /// dead-code analysis), hence the allow.
    #[allow(dead_code)]
    handle: File,
}

impl StateDirLock {
    /// Acquire an exclusive lock on `state_dir` (which must already exist).
    ///
    /// Returns an error whose message names the state dir if another substrate
    /// process already holds the lock, or the underlying IO error if the lock
    /// file cannot be created.
    pub fn acquire(state_dir: &Path) -> io::Result<Self> {
        let lock_path = state_dir.join(LOCK_FILENAME);
        match acquire_handle(&lock_path) {
            Ok(handle) => Ok(StateDirLock { handle }),
            Err(e) if is_already_locked(&e) => Err(io::Error::other(format!(
                "another myco-substrate process already holds the lock on this state dir ({}); \
                 a single state dir admits exactly one substrate at a time (P09 single integument)",
                state_dir.display()
            ))),
            Err(e) => Err(e),
        }
    }
}

#[cfg(windows)]
fn acquire_handle(lock_path: &Path) -> io::Result<File> {
    use std::os::windows::fs::OpenOptionsExt;
    // share_mode(0) == FILE_SHARE_NONE: while this handle is open, no other
    // process may open the same path, so a second substrate's open fails with a
    // sharing violation (ERROR_SHARING_VIOLATION). The exclusivity is released
    // when this handle closes (process exit or crash).
    OpenOptions::new()
        .create(true)
        .write(true)
        .share_mode(0)
        .open(lock_path)
}

#[cfg(windows)]
fn is_already_locked(e: &io::Error) -> bool {
    // ERROR_SHARING_VIOLATION (32): another process holds the file open with
    // FILE_SHARE_NONE.
    e.raw_os_error() == Some(32)
}

#[cfg(unix)]
#[allow(unsafe_code)] // FFI adapter: a single non-blocking flock(2) call.
fn acquire_handle(lock_path: &Path) -> io::Result<File> {
    use std::os::unix::io::AsRawFd;
    let handle = OpenOptions::new().create(true).write(true).open(lock_path)?;
    // SAFETY: `flock` is called on a valid fd this process just opened and owns.
    // LOCK_NB makes it non-blocking, returning EWOULDBLOCK if another open file
    // description holds the exclusive lock. The lock is released when the fd is
    // closed (drop of `handle` / process exit / crash).
    let rc = unsafe { libc::flock(handle.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) };
    if rc != 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(handle)
}

#[cfg(unix)]
fn is_already_locked(e: &io::Error) -> bool {
    // flock with LOCK_NB returns EWOULDBLOCK (== EAGAIN) when held elsewhere.
    e.kind() == io::ErrorKind::WouldBlock
}

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_state_dir() -> std::path::PathBuf {
        static SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let seq = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!(
            "myco-statelock-test-{}-{}",
            std::process::id(),
            seq
        ));
        std::fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn exclusive_while_held_then_reacquirable_after_release() {
        let dir = temp_state_dir();

        let first = StateDirLock::acquire(&dir).expect("first acquire succeeds");

        // A second acquire on the same dir must fail while the first is held.
        let err = StateDirLock::acquire(&dir)
            .expect_err("second acquire must fail while the first is held");
        assert!(
            err.to_string().contains("already holds the lock"),
            "expected the single-integument message; got: {err}"
        );

        // Releasing the first lock must let a fresh acquire succeed (proves the
        // lock auto-releases on drop, so a clean shutdown frees the state dir).
        drop(first);
        let second = StateDirLock::acquire(&dir).expect("acquire after release succeeds");
        drop(second);

        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn acquire_creates_lock_file_in_state_dir() {
        let dir = temp_state_dir();
        let lock = StateDirLock::acquire(&dir).expect("acquire");
        assert!(dir.join(LOCK_FILENAME).exists(), "lock file should exist");
        drop(lock);
        let _ = std::fs::remove_dir_all(&dir);
    }
}
