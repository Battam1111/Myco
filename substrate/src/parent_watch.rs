//! CHAR07 同体共命 operator-liveness: the substrate body lives only as long as
//! its operator (the bond). When the operator process that spawned this
//! substrate dies, the substrate should sleep (exit cleanly) instead of
//! orphaning.
//!
//! ## Why this exists in addition to stdin-EOF detection
//!
//! `run_loop`'s stdin reader exits on EOF and the main loop treats that as a
//! clean shutdown, which handles a graceful operator disconnect. But on Windows
//! the operator's death does **not** reliably deliver EOF to the substrate's
//! stdin (pipe-handle lifetime), so a substrate can outlive a dead operator as
//! an orphan. Combined with the state-dir lock (`state_lock.rs`), an orphan
//! holding the lock would block the next operator's substrate from booting.
//! This watch is an independent, OS-level liveness check on the operator
//! process, polled once per idle tick.
//!
//! ## Mechanism
//!
//! The operator passes its own PID via the `MYCO_OPERATOR_PID` env var when it
//! spawns the substrate. The watch holds an OS reference to that process:
//! - **Windows**: an `OpenProcess(SYNCHRONIZE)` handle; `WaitForSingleObject(_, 0)`
//!   reports whether the process has exited (handle-based, immune to PID reuse).
//! - **Unix**: the operator PID; `kill(pid, 0)` reports liveness (`ESRCH` = gone).
//!
//! If `MYCO_OPERATOR_PID` is absent (e.g. a manual run) or the operator process
//! cannot be opened, the watch is `Disabled` and the substrate falls back to
//! stdin-EOF detection (`operator_gone()` always returns `false`).

/// Env var the operator sets to its own PID when spawning the substrate, so the
/// substrate can watch the operator for liveness.
pub const OPERATOR_PID_ENV: &str = "MYCO_OPERATOR_PID";

/// A liveness watch on the operator process that spawned this substrate.
pub enum ParentWatch {
    /// No operator to watch (env var absent/unparseable, or the process could
    /// not be opened). `operator_gone()` is always `false`.
    Disabled,
    /// Windows: an owned SYNCHRONIZE handle to the operator process.
    #[cfg(windows)]
    Windows(windows_impl::Handle),
    /// Unix: the operator PID, probed with `kill(pid, 0)`.
    #[cfg(unix)]
    Unix(u32),
}

impl ParentWatch {
    /// Build a watch from `MYCO_OPERATOR_PID`. Returns [`ParentWatch::Disabled`]
    /// if the var is absent/unparseable (or, on Windows, the process cannot be
    /// opened): falling back to "do not watch" rather than "already gone" avoids
    /// a spurious immediate exit at boot.
    pub fn from_env() -> Self {
        match std::env::var(OPERATOR_PID_ENV)
            .ok()
            .and_then(|s| s.trim().parse::<u32>().ok())
        {
            Some(pid) => Self::watch_pid(pid),
            None => ParentWatch::Disabled,
        }
    }

    /// Build a watch on a specific operator PID.
    pub fn watch_pid(pid: u32) -> Self {
        #[cfg(windows)]
        {
            match windows_impl::Handle::open(pid) {
                Some(h) => ParentWatch::Windows(h),
                None => ParentWatch::Disabled,
            }
        }
        #[cfg(unix)]
        {
            ParentWatch::Unix(pid)
        }
        #[cfg(not(any(windows, unix)))]
        {
            let _ = pid;
            ParentWatch::Disabled
        }
    }

    /// True if the watched operator process has exited. Always `false` when
    /// [`ParentWatch::Disabled`].
    pub fn operator_gone(&self) -> bool {
        match self {
            ParentWatch::Disabled => false,
            #[cfg(windows)]
            ParentWatch::Windows(h) => h.process_exited(),
            #[cfg(unix)]
            ParentWatch::Unix(pid) => unix_impl::pid_gone(*pid),
        }
    }
}

#[cfg(windows)]
#[allow(unsafe_code)] // FFI adapter: OpenProcess / WaitForSingleObject / CloseHandle.
mod windows_impl {
    use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
    use windows_sys::Win32::System::Threading::{OpenProcess, WaitForSingleObject};

    /// `SYNCHRONIZE` access right (winnt.h): the minimum needed to wait on a
    /// process handle. Literal, to avoid windows-sys re-export path churn.
    const SYNCHRONIZE: u32 = 0x0010_0000;
    /// `WaitForSingleObject` return when the object is signaled (process exited).
    const WAIT_OBJECT_0: u32 = 0x0000_0000;

    /// An owned `OpenProcess(SYNCHRONIZE)` handle to the operator process.
    pub struct Handle(HANDLE);

    impl Handle {
        /// Open a SYNCHRONIZE handle to `pid`. `None` if the process cannot be
        /// opened (already exited or inaccessible).
        pub fn open(pid: u32) -> Option<Handle> {
            // SAFETY: OpenProcess is a pure query; `0` (FALSE) = non-inheritable
            // handle. A null return means the open failed (process gone / no
            // access), which we surface as `None`.
            let h = unsafe { OpenProcess(SYNCHRONIZE, 0, pid) };
            if h.is_null() {
                None
            } else {
                Some(Handle(h))
            }
        }

        /// True if the watched process has terminated.
        pub fn process_exited(&self) -> bool {
            // SAFETY: `self.0` is a valid SYNCHRONIZE handle this struct owns.
            // Timeout 0 polls; WAIT_OBJECT_0 means the process object is
            // signaled, i.e. the process has terminated.
            let rc = unsafe { WaitForSingleObject(self.0, 0) };
            rc == WAIT_OBJECT_0
        }
    }

    impl Drop for Handle {
        fn drop(&mut self) {
            // SAFETY: `self.0` is a valid handle this struct owns; closed once.
            unsafe {
                let _ = CloseHandle(self.0);
            }
        }
    }
}

#[cfg(unix)]
#[allow(unsafe_code)] // FFI adapter: kill(pid, 0) liveness probe.
mod unix_impl {
    /// True if no live process has PID `pid` (operator has exited). `kill(pid,
    /// 0)` sends no signal; it only checks: `Ok` = alive, `ESRCH` = gone. Other
    /// errors (e.g. `EPERM`) imply the process exists, so we treat them as alive.
    pub fn pid_gone(pid: u32) -> bool {
        // SAFETY: signal 0 performs only permission/existence checking and never
        // affects the target process.
        let rc = unsafe { libc::kill(pid as libc::pid_t, 0) };
        if rc == 0 {
            false
        } else {
            std::io::Error::last_os_error().raw_os_error() == Some(libc::ESRCH)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disabled_watch_always_reports_alive() {
        assert!(!ParentWatch::Disabled.operator_gone());
    }

    #[cfg(any(windows, unix))]
    #[test]
    fn operator_gone_flips_when_watched_process_dies() {
        let mut child = spawn_sleeper();
        let pid = child.id();
        let watch = ParentWatch::watch_pid(pid);
        assert!(
            !watch.operator_gone(),
            "a live watched process must read as present"
        );
        child.kill().expect("kill the watched child");
        let _ = child.wait();
        // Let the OS mark the process object signaled / reflect the exit.
        std::thread::sleep(std::time::Duration::from_millis(300));
        assert!(
            watch.operator_gone(),
            "a terminated watched process must read as gone"
        );
    }

    #[cfg(any(windows, unix))]
    fn spawn_sleeper() -> std::process::Child {
        // A long-running process we control and kill early.
        #[cfg(windows)]
        {
            std::process::Command::new("ping")
                .args(["-n", "30", "127.0.0.1"])
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn()
                .expect("spawn ping sleeper")
        }
        #[cfg(unix)]
        {
            std::process::Command::new("sleep")
                .arg("30")
                .spawn()
                .expect("spawn sleep sleeper")
        }
    }
}
