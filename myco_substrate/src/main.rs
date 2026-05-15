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

use std::process::ExitCode;

use myco_substrate::server;

fn main() -> ExitCode {
    // M23.1 P4 永恒迭代: run_loop manages its own stdin (via a background
    // reader thread) and stdout (locked inside the loop). The binary just
    // dispatches and surfaces the exit code.
    match server::run_loop() {
        Ok(code) => ExitCode::from(code),
        Err(err) => {
            eprintln!("myco-substrate fatal: {err}");
            ExitCode::from(1)
        }
    }
}
