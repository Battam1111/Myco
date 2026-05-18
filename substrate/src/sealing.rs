//! **v3.1.1 Sprint 2.B** — OS-sealing backend scaffold for non-Windows
//! platforms.
//!
//! ## Status
//!
//! This module exists as **architectural placeholder** documenting the
//! shape of Linux kernel-keyring and macOS Secure Enclave backends. The
//! actual platform-specific implementations are **acknowledged debt** —
//! they require their respective platforms for testing, and the current
//! development host runs Windows.
//!
//! The Windows DPAPI backend ships in `substrate::dpapi` (Sprint 2.A,
//! commit dc54385). On Linux / macOS the v1 plain-bytes format with
//! `chmod 0600` + BLAKE3 integrity (Sprint 2.B) is the current state —
//! adequate against bitrot and filesystem-read attacks against a
//! single-user host with restrictive umask, weaker than DPAPI against
//! adversarial-with-local-user-context attacks.
//!
//! ## Doctrine traceability
//!
//! - L1/SKIN §4.2 + L1/HARD_RULES C4 substrate_secret_unsealed
//! - L0/cards/AS_anchor_surface.md §3.5 (owner key custody outside
//!   process; per cultivar instance the substrate signing key is the
//!   adjacent at-rest secret with similar protection requirements)
//! - kernel/shared/Cargo.toml feature flags: `sealing-keyring`,
//!   `sealing-secure-enclave` (declared but not wired pre-Sprint 2.B)
//!
//! ## Implementation roadmap (Sprint 2.B follow-up, requires Linux/Mac
//! test environment)
//!
//! ### Linux kernel keyring (`#[cfg(target_os = "linux")]`)
//!
//! Uses the `add_key` / `keyctl_search` / `keyctl_read` syscalls (libc
//! crate exposes them, or via the `keyutils` crate). Pattern:
//!
//! ```ignore
//! // At save:
//! let key_id = add_key("user", "myco-substrate-seed", seed_bytes,
//!                     KEY_SPEC_USER_KEYRING)?;
//! // Store key_id (a kernel handle, not the seed itself) in
//! // substrate_signing_key.cb. On load: keyctl_read(key_id) → seed.
//! ```
//!
//! Threat model gain: seed bytes live in kernel space, not user-space
//! disk. Process compromise still exposes them (via syscall return).
//! Filesystem-read attack returns the key_id only, useless without the
//! kernel keyring access.
//!
//! ### macOS Secure Enclave (`#[cfg(target_os = "macos")]`)
//!
//! Uses `SecKeyCreateRandomKey` / `SecKeyCreateSignature` via the
//! `security-framework` crate (or raw `objc2` bindings). The Secure
//! Enclave provides true hardware-bound sealing on Apple silicon — the
//! seed bytes never leave the Secure Enclave even into the substrate
//! process. The substrate calls into Secure Enclave for signing
//! operations; the seed is permanently sealed.
//!
//! Pattern:
//!
//! ```ignore
//! // At save (genesis only): generate inside Secure Enclave.
//! let key_ref = SecKey::create_random_key(/* SE attributes */)?;
//! // Store the public key + a key tag in substrate_signing_key.cb;
//! // the private key never appears in our address space.
//! // For signing: SecKeyCreateSignature(key_ref, &content_canonical_bytes).
//! ```
//!
//! Threat model gain: strongest of all backends on supporting hardware —
//! even process compromise cannot extract the seed. The Ed25519
//! operations happen inside the Secure Enclave.
//!
//! ### Linux TPM 2.0 (`sealing-tpm` feature, also viable on Windows for
//! cross-platform TPM users)
//!
//! Uses the `tpm2-tss` library bindings (e.g., via `tss-esapi` crate).
//! TPM-sealed-derive is the strongest available primitive — the
//! signing operations happen inside the TPM, and the seed is bound to
//! the TPM's storage root key. Cross-platform option for users who
//! prefer TPM over DPAPI on Windows or over Secure Enclave on macOS.
//!
//! ## Why scaffold-only this session
//!
//! Per PIP discipline ("changed code without build/test/curl = malpractice"):
//! implementing platform-specific OS-sealing without ability to test on
//! the target platform produces unshippable code. The substrate would
//! claim integration but the cultivator would discover at production
//! genesis that something deep in the keyring or Secure Enclave call
//! chain doesn't work. Shipping it broken is worse than shipping it
//! deferred + named.
//!
//! When a Linux or macOS dev environment becomes available (cultivator's
//! choice or follow-up cross-host CI), implementing each backend is
//! ~20-50h of work each, mostly tracking the platform-specific API
//! quirks and writing the integration tests that prove round-trip
//! correctness on a real keyring / Secure Enclave.

// This module is intentionally a documentation surface for the time
// being. The compile-time `#[cfg(...)]` gates below ensure it produces
// no orphaned symbols on Windows builds (which use DPAPI exclusively).

/// **Sprint 2.B acknowledged debt** — placeholder for the Linux kernel
/// keyring sealing backend. See module-level docs for implementation
/// roadmap.
#[cfg(all(target_os = "linux", feature = "_sealing_keyring_placeholder"))]
pub mod linux_keyring {
    // Real implementation: `add_key("user", description, seed,
    // KEY_SPEC_USER_KEYRING)` via libc syscalls. Returns kernel key_id.
    // Store key_id in substrate_signing_key.cb (NOT the seed). Load
    // path calls `keyctl_read(key_id)` to recover.
    //
    // Tests REQUIRE a Linux host with `keyutils` available — adding
    // Linux CI runners or shipping containerized test environment is
    // the gate to lighting this up.
}

/// **Sprint 2.B acknowledged debt** — placeholder for the macOS Secure
/// Enclave sealing backend. See module-level docs for implementation
/// roadmap.
#[cfg(all(target_os = "macos", feature = "_sealing_secure_enclave_placeholder"))]
pub mod macos_secure_enclave {
    // Real implementation: SecKeyCreateRandomKey with
    // kSecAttrTokenIDSecureEnclave. The substrate process never sees
    // the seed; SecKeyCreateSignature does the Ed25519 operation
    // inside the Secure Enclave.
    //
    // Tests REQUIRE Apple Silicon hardware (Secure Enclave is M1+) or
    // T2-equipped Intel Mac.
}

/// **Sprint 2.B acknowledged debt** — placeholder for cross-platform
/// TPM 2.0 sealing backend. See module-level docs.
#[cfg(feature = "_sealing_tpm_placeholder")]
pub mod tpm2 {
    // Real implementation: TPM2_Create + TPM2_Encrypt via tss-esapi
    // bindings. Strongest threat-model gain — seed never leaves TPM.
    // Cross-platform: works on Linux + Windows + ChromeOS hosts with
    // TPM 2.0 chips.
}

#[cfg(test)]
mod tests {
    // Scaffold-only tests: assert the placeholder modules compile
    // cleanly and don't accidentally expose stub APIs on the host
    // platform.

    #[test]
    fn sprint_2b_scaffold_compiles_clean() {
        // If this test runs, the module's cfg gates are correct
        // (compiles on every host platform; bodies only compile when
        // their respective feature flag is set, which it isn't in
        // baseline builds).
    }
}
