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

use substrate::server;

fn main() -> ExitCode {
    // **Phase ① 永恒吞噬 / P04 §5.5** — the PRODUCTION substrate self-drives its
    // metabolic cycle by default. A living cultivar is not a request-response
    // service: it ticks under its own clock (autonomous_tick → self-driven
    // cycle advance), metabolizes, and gets hungry on its own. We turn the
    // self-driven scheduler ON here, in the binary entry point, by defaulting
    // the env flag to "1" when the operator has not set it — so the DEFAULT is
    // alive, while remaining env-overridable (`MYCO_SELF_DRIVEN_CYCLE_ADVANCE=0`
    // disables, e.g. for a controlled/forensic run).
    //
    // This seam (binary-only) keeps the LIBRARY default OFF: the lib unit tests
    // drive `do_autonomous_tick` / `handle_advance` directly and never execute
    // `main`, so they keep deterministic controlled advancement; the e2e
    // subprocess harness sets the flag explicitly (defaults it to "0") so its
    // operator-driven `advance` cycles stay exactly counted. Edition 2021 →
    // `set_var` is safe.
    if std::env::var_os("MYCO_SELF_DRIVEN_CYCLE_ADVANCE").is_none() {
        std::env::set_var("MYCO_SELF_DRIVEN_CYCLE_ADVANCE", "1");
    }

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
