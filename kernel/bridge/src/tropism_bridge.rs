//! TropismBridge — adapter that turns a [`BridgeClient`] into a
//! [`GradientAdvancer`] so the metabolic-cycle engine in
//! [`myco_kernel_continuity`] can drive Python's `kernel/tropism` directly.
//!
//! ## Pattern
//!
//! The cycle engine (M3) was designed to call trait methods generically:
//! `Tier1Validator::validate_tier1`, `GradientAdvancer::advance_gradient`, etc.
//! This module provides one concrete impl for the gradient-advance step
//! that delegates across the IPC boundary to the Python worker.
//!
//! The other four traits remain Rust-native at M5; M6+ may add bridges for
//! each (e.g., a Python skin breach detector for advanced detectors not
//! yet ported to Rust).
//!
//! ## Cycle counter
//!
//! [`TropismBridge`] tracks its own cycle counter mirroring the engine's.
//! On each `advance_gradient` call we read the engine's counter (passed
//! externally — the bridge takes a closure or external value), bump our
//! local counter, and send the value to the worker.
//!
//! For M5 we use a simple incrementing counter local to the bridge.
//! M6+ may sync this with the engine's counter explicitly.

use myco_kernel_continuity::cycle::GradientAdvancer;

use crate::client::BridgeClient;
use crate::protocol::AdvanceReport;

/// Adapter wrapping a [`BridgeClient`] for use as a [`GradientAdvancer`].
///
/// Holds the latest [`AdvanceReport`] for downstream inspection (e.g. by
/// a `DeltaAbsorber` that wants to commit emitted sporocarps to the DAG).
pub struct TropismBridge {
    client: BridgeClient,
    cycle_counter: u64,
    /// The most recent advance report; reset to default on each new advance.
    latest_advance_report: Option<AdvanceReport>,
}

impl TropismBridge {
    /// Construct a new bridge from an already-handshaken [`BridgeClient`].
    pub fn new(client: BridgeClient) -> Self {
        TropismBridge {
            client,
            cycle_counter: 0,
            latest_advance_report: None,
        }
    }

    /// Direct access to the underlying client for non-cycle operations
    /// (e.g., axis registration before the engine starts spinning).
    pub fn client_mut(&mut self) -> &mut BridgeClient {
        &mut self.client
    }

    /// Read-only access to the latest advance report.
    pub fn latest_advance_report(&self) -> Option<&AdvanceReport> {
        self.latest_advance_report.as_ref()
    }

    /// Current cycle counter (mirrors how many advance() calls have succeeded).
    pub fn cycle_counter(&self) -> u64 {
        self.cycle_counter
    }

    /// Consume the bridge and gracefully shutdown the underlying client.
    pub fn shutdown(self) -> Result<(), crate::BridgeError> {
        self.client.shutdown()
    }
}

impl GradientAdvancer for TropismBridge {
    fn advance_gradient(&mut self) -> Result<(), String> {
        self.cycle_counter = self.cycle_counter.wrapping_add(1);
        match self.client.advance(self.cycle_counter) {
            Ok(report) => {
                self.latest_advance_report = Some(report);
                Ok(())
            }
            Err(e) => Err(format!("tropism bridge advance failed: {e}")),
        }
    }
}
