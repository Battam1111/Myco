//! Myco v0.9 — cross-language canonical-bytes parity test crate.
//!
//! Empty library — purely a test harness. The actual tests live at
//! `tests/canonical_bytes_parity.rs`. They consume the shared JSON
//! contract at `<repo>/test_vectors/canonical_bytes_v1.json` and verify
//! that the Rust `kernel/shared::canonical_bytes::encode` implementation
//! produces byte-identical output to every vector.
//!
//! ## Why a separate test crate
//!
//! The JSON-consuming tests need `serde_json` for parsing. Adding it as
//! a dev-dep to `kernel/shared` would bloat the foundation crate's test
//! surface; isolating in this crate keeps `kernel/shared`'s deps minimal
//! while still enabling end-to-end cross-language verification.
//!
//! ## Cross-language parity (3-way)
//!
//! When `cargo test -p myco-test-vectors-rs` passes AND
//! `npm test` (anchor_client) passes AND
//! `pytest` (kernel/governance) passes, the three implementations of
//! the canonical-bytes serializer are byte-identical on every test
//! vector in the JSON. Drift would constitute L1_HARD_RULES C18
//! `canonical_bytes_render_drift` (CRITICAL).

#![warn(missing_docs)]
#![warn(clippy::all)]
#![forbid(unsafe_code)]
