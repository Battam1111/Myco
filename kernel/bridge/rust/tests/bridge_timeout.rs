//! **v3.1.1 Sprint 7.E.2** — `call_with_timeout` hung-worker timeout test.
//!
//! These tests prove the reader-thread + `recv_timeout` design actually
//! BOUNDS a substrate-→-Python call when the worker is alive-but-blocked
//! (deadlock, infinite loop, GIL contention). The failure mode this guards
//! against is the original stub behavior: `call_with_timeout` ignored its
//! deadline and blocked forever, wedging the whole substrate on a hung worker.
//!
//! ## Simulating a hung worker
//!
//! We spawn a stub child — `python -c "import sys; sys.stdin.read()"` — that
//! reads stdin until EOF and NEVER writes a byte to stdout. From the
//! controller's perspective this is indistinguishable from a Python worker
//! that received our request frame but deadlocked before producing a response:
//! the reader thread blocks on an empty stdout, and the waiter must time out.
//!
//! We attach the client to that child via the test-only
//! `BridgeClient::from_spawned_child_for_test` (which skips the `hello`
//! handshake the hung stub would never complete).
//!
//! ## Watchdog
//!
//! Every test body runs on a worker thread guarded by an overall wall-clock
//! watchdog. If `call_with_timeout` ever regressed back to an unbounded block,
//! the watchdog fires and the test FAILS loudly instead of hanging the whole
//! `cargo test` run forever.

use std::process::{Command, Stdio};
use std::sync::mpsc;
use std::time::{Duration, Instant};

use myco_kernel_bridge::client::BridgeClient;
use myco_kernel_bridge::protocol::{advance_payload, empty_payload, msg_type};
use myco_kernel_bridge::BridgeError;

/// Spawn the hung-worker stub: consumes stdin, never writes stdout.
///
/// `python` is a hard dependency of the bridge e2e suite already (the real
/// client spawns `python -m myco_kernel_bridge`), so relying on it here adds
/// no new environmental requirement.
fn spawn_hung_child() -> std::process::Child {
    Command::new("python")
        .arg("-c")
        // Block forever reading stdin; emit nothing on stdout. `sys.stdin.read()`
        // returns only at EOF, which never comes while the client holds stdin.
        .arg("import sys; sys.stdin.read()")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("spawn `python -c` hung-worker stub")
}

/// Run `body` on a worker thread with an overall watchdog. If `body` does not
/// finish within `budget`, panic — this converts a hypothetical real hang in
/// `call_with_timeout` into a hard test failure rather than a frozen suite.
fn with_watchdog<F>(budget: Duration, body: F)
where
    F: FnOnce() + Send + 'static,
{
    let (tx, rx) = mpsc::channel::<()>();
    let handle = std::thread::spawn(move || {
        body();
        let _ = tx.send(());
    });
    match rx.recv_timeout(budget) {
        Ok(()) => {
            // Body completed; join to surface any panic from inside it.
            handle.join().expect("test body thread panicked");
        }
        Err(mpsc::RecvTimeoutError::Timeout) => {
            panic!(
                "WATCHDOG: test body did not complete within {budget:?} — \
                 call_with_timeout likely hung (regression: deadline ignored)"
            );
        }
        Err(mpsc::RecvTimeoutError::Disconnected) => {
            // Sender dropped without sending → body thread panicked. Join to
            // propagate the original panic message.
            handle.join().expect("test body thread panicked");
        }
    }
}

#[test]
fn call_with_timeout_returns_timeout_on_hung_worker() {
    // Overall watchdog generously larger than the call timeout so a correct
    // implementation finishes well inside it, but a true hang trips it.
    with_watchdog(Duration::from_secs(20), || {
        let child = spawn_hung_child();
        let mut client = BridgeClient::from_spawned_child_for_test(child, [0x5a; 32])
            .expect("attach client to hung stub child");

        let timeout = Duration::from_millis(500);
        let started = Instant::now();
        let result = client.call_with_timeout(msg_type::ADVANCE, advance_payload(1), timeout);
        let elapsed = started.elapsed();

        // 1. It must be a Timeout, not a block, not some other error.
        match result {
            Err(BridgeError::Timeout(d)) => {
                assert_eq!(d, timeout, "Timeout should report the requested deadline");
            }
            other => panic!("expected Err(BridgeError::Timeout); got {other:?}"),
        }

        // 2. It returned no earlier than the deadline (it actually waited) and
        //    no absurdly late (it did not hang). Allow generous slack on the
        //    upper bound for CI scheduling jitter while still proving bounded.
        assert!(
            elapsed >= timeout,
            "should have waited at least the timeout ({timeout:?}); waited {elapsed:?}"
        );
        assert!(
            elapsed < Duration::from_secs(10),
            "call_with_timeout took {elapsed:?} — far beyond the {timeout:?} deadline (hang?)"
        );

        // 3. The connection is now poisoned: the serial stream cannot safely
        //    carry another request (a late response would mis-pair). Every
        //    subsequent call must fail fast with Desynchronized — including a
        //    blocking `call`, which must NOT block.
        let started2 = Instant::now();
        let second = client.call_with_timeout(msg_type::SNAPSHOT, empty_payload(), timeout);
        assert!(
            matches!(second, Err(BridgeError::Desynchronized)),
            "after a timeout, the next call must fail fast with Desynchronized; got {second:?}"
        );
        assert!(
            started2.elapsed() < Duration::from_millis(200),
            "poisoned call must return immediately, not wait out the timeout again"
        );

        // 4. Dropping the client must not hang: Drop kills the stub child,
        //    waits it, then joins the reader thread (which wakes on the child's
        //    stdout EOF). The watchdog covers this.
        drop(client);
    });
}

#[test]
fn blocking_call_is_also_poisoned_after_a_timeout() {
    // Same setup, but prove the *blocking* path (`call`, used by the legacy
    // forward path) is equally protected: once poisoned by a prior timeout it
    // returns Desynchronized immediately rather than blocking on the (long)
    // BLOCKING_CALL_DEADLINE.
    with_watchdog(Duration::from_secs(20), || {
        let child = spawn_hung_child();
        let mut client = BridgeClient::from_spawned_child_for_test(child, [0x42; 32])
            .expect("attach client to hung stub child");

        // First, time out a call to poison the connection.
        let timeout = Duration::from_millis(300);
        let first = client.call_with_timeout(msg_type::ADVANCE, advance_payload(1), timeout);
        assert!(
            matches!(first, Err(BridgeError::Timeout(_))),
            "expected Timeout; got {first:?}"
        );

        // Now a blocking `call` must fail fast, not block on the hour-long
        // blocking deadline.
        let started = Instant::now();
        let second = client.call(msg_type::SNAPSHOT, empty_payload());
        assert!(
            matches!(second, Err(BridgeError::Desynchronized)),
            "blocking call after a timeout must be Desynchronized; got {second:?}"
        );
        assert!(
            started.elapsed() < Duration::from_millis(200),
            "blocking call on a poisoned client must return immediately"
        );

        drop(client);
    });
}
