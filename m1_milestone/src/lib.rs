//! Myco v0.9 — M1 milestone end-to-end test crate.
//!
//! This crate exists solely to host the M1 milestone goal verification per
//! L3_OUTLINE §8 milestone framing: **a single substrate can perform a
//! handshake + store a single DAG node end-to-end**.
//!
//! The actual test code lives at `tests/m1_end_to_end.rs`. This `lib.rs` is
//! empty by design — the crate is a test harness, not a library exposing API.
//!
//! ## Why a dedicated crate
//!
//! The integration test crosses three kernel crates (`myco-kernel-shared`,
//! `myco-kernel-skin`, `myco-kernel-schema`). Putting the test in any one of
//! those crates would require it to dev-depend on a sibling — which is
//! awkward for kernel/skin (which has no `kernel/schema` dependency at
//! production scope). A dedicated test-only crate keeps production
//! dependency graphs clean while enabling cross-crate verification.
//!
//! ## What this proves
//!
//! When `cargo test -p myco-m1-milestone` passes, the M1 milestone is
//! achieved: kernel/shared canonical-bytes + crypto + sealed_derive ◯+◯
//! kernel/skin handshake + envelope validation ◯+◯ kernel/schema DAG
//! insertion + tip maintenance all interoperate via their public APIs.
//!
//! ## What this does NOT prove
//!
//! - Transport layer (TCP / Unix sockets / etc.) — abstracted at L4
//!   platform-pick; M1 logic-only.
//! - Cross-language canonical-bytes parity — kernel/shared's serializer
//!   produces identical bytes here in Rust; the Python + TypeScript hosts
//!   land at M2.
//! - Persistence across cold-resume — kernel/continuity (M3) wires the WAL.
//! - Attestation envelope signature flow — kernel/governance (M2).
//! - Sporocarp emission + appetite gradient — kernel/tropism (M3).

#![warn(missing_docs)]
#![warn(clippy::all)]
#![forbid(unsafe_code)]
