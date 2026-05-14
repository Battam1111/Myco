//! `myco-substrate` binary entry point.
//!
//! Reads operator request frames from stdin, dispatches them to the Python
//! kernel/tropism worker (via the M5 bridge) or runs them locally as a
//! CycleEngine step, and writes responses to stdout.
//!
//! Exit codes:
//!
//! - `0` — clean shutdown (received `shutdown` from the operator runtime).
//! - `1` — fatal I/O or subprocess error.
//! - `2` — handshake failed before completion.

use std::io::{stdin, stdout};
use std::process::ExitCode;

use myco_substrate::server;

fn main() -> ExitCode {
    let stdin_handle = stdin();
    let stdout_handle = stdout();
    let mut stdin_lock = stdin_handle.lock();
    let mut stdout_lock = stdout_handle.lock();

    let result = server::run_loop(&mut stdin_lock, &mut stdout_lock);
    match result {
        Ok(code) => ExitCode::from(code),
        Err(err) => {
            // Surface to stderr — the operator runtime can capture this.
            eprintln!("myco-substrate fatal: {err}");
            ExitCode::from(1)
        }
    }
}
