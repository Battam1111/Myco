//! **v3.1.1 Sprint 2** — Windows DPAPI sealing for substrate_signing_key.
//!
//! ## Doctrine traceability
//!
//! - **L1/SKIN §4.2** + **L1/HARD_RULES C4 substrate_secret_unsealed**:
//!   substrate_secret MUST live in OS-mediated sealed storage. The substrate
//!   process MUST NOT keep plaintext on disk such that a filesystem-read
//!   attack extracts the seed without compromising the user account.
//! - **L0/cards/AS_anchor_surface.md** + **M-anchor-1**: owner key custody is
//!   "outside the substrate process AND outside any process the agent can
//!   spawn or read". DPAPI on Windows binds the substrate_signing_seed to
//!   the Windows user's master key — the seed cannot be unwrapped except
//!   by code running as the same user (which is the trust boundary).
//!
//! ## What DPAPI does
//!
//! Windows Data Protection API (DPAPI) is built into Windows since 2000.
//! `CryptProtectData` encrypts a blob using a key derived from the current
//! user's logon credentials; `CryptUnprotectData` reverses this only when
//! invoked by the same user account. The encryption key is managed by the
//! Windows operating system; it never appears in user-space memory in
//! plaintext.
//!
//! ## What DPAPI does NOT do
//!
//! - **In-memory protection**: once we call `CryptUnprotectData`, the
//!   plaintext seed lives in our substrate process's memory for the duration
//!   of the run. An attacker who compromises the process (P1.a self-hosting
//!   risk) sees the seed. DPAPI raises the bar from "read a file" to
//!   "compromise the process" — same threat-model gain as TPM-sealed storage
//!   (without TPM-sealed-derive's stronger in-process protection).
//! - **Cross-user attacks**: any code running as the same Windows user can
//!   unwrap. Multi-user hosts MUST partition substrates by user account.
//! - **Cross-machine portability**: a DPAPI-wrapped blob cannot be moved to
//!   another machine without first unwrapping on the source machine. This
//!   is by design — it binds the seed to the host.
//!
//! ## Platform support
//!
//! This module is **Windows-only**. The entire file is `#[cfg(windows)]`-
//! gated. On non-Windows platforms, callers fall through to the legacy
//! plain-bytes path (with `chmod 0600` on Unix per persistence.rs). Real
//! OS-sealing for Linux (kernel keyring) and macOS (Secure Enclave) is
//! scheduled for follow-up sprints.
//!
//! ## Format and migration
//!
//! - **Format v1**: legacy. Plain canonical-bytes Map carrying `seed:
//!   Bytes`. Predates Sprint 2.
//! - **Format v2** (this module): canonical-bytes Map carrying
//!   `dpapi_ciphertext: Bytes` (the output of `CryptProtectData` over the
//!   v1 plaintext-Map's canonical bytes). On Windows v2 substrates this is
//!   the on-disk shape; on non-Windows substrates v2 is NOT used (writers
//!   stay at v1 with chmod hardening).
//!
//! Migration: v1-format files loaded on Windows are re-saved as v2 atomically
//! after successful first boot. The plaintext seed never touches disk again.

#![cfg(windows)]

use thiserror::Error;
use windows_sys::Win32::Foundation::{LocalFree, HLOCAL};
use windows_sys::Win32::Security::Cryptography::{
    CryptProtectData, CryptUnprotectData, CRYPT_INTEGER_BLOB,
};

/// DPAPI wrap/unwrap errors.
#[derive(Debug, Error)]
pub enum DpapiError {
    /// CryptProtectData / CryptUnprotectData returned FALSE. Carries the
    /// Windows GetLastError() code for diagnosis.
    #[error("DPAPI {operation} failed (Windows error code {code:#010x})")]
    WinApi {
        /// Which call failed — "protect" or "unprotect".
        operation: &'static str,
        /// Windows error code from GetLastError() at failure time.
        code: u32,
    },

    /// The DPAPI output blob has zero length — should be unreachable under
    /// healthy Windows; defensive guard.
    #[error("DPAPI {operation} returned empty blob")]
    EmptyBlob {
        /// Which call returned empty — "protect" or "unprotect".
        operation: &'static str,
    },
}

/// Description string passed to DPAPI. Visible via Windows diagnostic tools;
/// pins the wrap as "Myco substrate signing key" for auditability.
const DPAPI_DESCRIPTION: &str = "Myco substrate_signing_key (v3.1.1 Sprint 2)";

/// Encrypt `plaintext` using DPAPI bound to the current Windows user. The
/// returned ciphertext can ONLY be decrypted by `unprotect` running as the
/// same user on the same machine.
///
/// **Safety**: this is an FFI boundary. `plaintext` is borrowed immutably;
/// the returned `Vec<u8>` is fully owned. Internally we use `LocalFree` to
/// release the DPAPI output buffer immediately after copying.
pub fn protect(plaintext: &[u8]) -> Result<Vec<u8>, DpapiError> {
    // Build the input BLOB. `pbData` is a non-const pointer in the Win32
    // signature, but DPAPI does not mutate it; the cast is safe.
    let mut input = CRYPT_INTEGER_BLOB {
        cbData: plaintext.len() as u32,
        pbData: plaintext.as_ptr() as *mut u8,
    };

    // Description string — must be a wide null-terminated string.
    let mut description_utf16: Vec<u16> = DPAPI_DESCRIPTION.encode_utf16().chain(Some(0)).collect();

    // Output blob — DPAPI allocates and we LocalFree.
    let mut output = CRYPT_INTEGER_BLOB {
        cbData: 0,
        pbData: std::ptr::null_mut(),
    };

    // SAFETY: input.pbData points at `plaintext` for `cbData` bytes;
    // description_utf16 is a valid null-terminated wide string for its
    // lifetime; pOptionalEntropy is null (acceptable per WinAPI docs);
    // pPromptStruct is null (no UI); flags = 0 (no extra protection).
    // CryptProtectData allocates *pDataOut on success.
    let ok = unsafe {
        CryptProtectData(
            &mut input as *mut _,
            description_utf16.as_mut_ptr(),
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            0,
            &mut output as *mut _,
        )
    };

    if ok == 0 {
        let code = unsafe { windows_sys::Win32::Foundation::GetLastError() };
        return Err(DpapiError::WinApi {
            operation: "protect",
            code,
        });
    }

    if output.cbData == 0 || output.pbData.is_null() {
        // Defensive: free anything that might have been allocated.
        if !output.pbData.is_null() {
            unsafe {
                LocalFree(output.pbData as HLOCAL);
            }
        }
        return Err(DpapiError::EmptyBlob { operation: "protect" });
    }

    // SAFETY: output.pbData is a Windows-allocated buffer of output.cbData
    // bytes. We copy out then LocalFree.
    let ciphertext: Vec<u8> = unsafe {
        let slice = std::slice::from_raw_parts(output.pbData, output.cbData as usize);
        let copy = slice.to_vec();
        LocalFree(output.pbData as HLOCAL);
        copy
    };

    Ok(ciphertext)
}

/// Decrypt `ciphertext` previously produced by `protect` (on the same
/// machine, by the same user). Returns the original plaintext.
///
/// Errors if the ciphertext is corrupt, was produced on a different
/// machine, or was produced under a different user account.
pub fn unprotect(ciphertext: &[u8]) -> Result<Vec<u8>, DpapiError> {
    let mut input = CRYPT_INTEGER_BLOB {
        cbData: ciphertext.len() as u32,
        pbData: ciphertext.as_ptr() as *mut u8,
    };

    // We don't need the original description on unwrap, but DPAPI returns it
    // — we accept and immediately LocalFree.
    let mut description_out: *mut u16 = std::ptr::null_mut();

    let mut output = CRYPT_INTEGER_BLOB {
        cbData: 0,
        pbData: std::ptr::null_mut(),
    };

    // SAFETY: same FFI contract as `protect`. CryptUnprotectData allocates
    // *pDataOut and *ppszDataDescr on success.
    let ok = unsafe {
        CryptUnprotectData(
            &mut input as *mut _,
            &mut description_out as *mut _,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            0,
            &mut output as *mut _,
        )
    };

    if ok == 0 {
        let code = unsafe { windows_sys::Win32::Foundation::GetLastError() };
        return Err(DpapiError::WinApi {
            operation: "unprotect",
            code,
        });
    }

    // Free the description string immediately — we don't use it.
    if !description_out.is_null() {
        unsafe {
            LocalFree(description_out as HLOCAL);
        }
    }

    if output.cbData == 0 || output.pbData.is_null() {
        if !output.pbData.is_null() {
            unsafe {
                LocalFree(output.pbData as HLOCAL);
            }
        }
        return Err(DpapiError::EmptyBlob {
            operation: "unprotect",
        });
    }

    let plaintext: Vec<u8> = unsafe {
        let slice = std::slice::from_raw_parts(output.pbData, output.cbData as usize);
        let copy = slice.to_vec();
        LocalFree(output.pbData as HLOCAL);
        copy
    };

    Ok(plaintext)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn protect_unprotect_round_trip_returns_original_plaintext() {
        let original = b"substrate_signing_seed_test_value_32b!".as_slice();
        let ciphertext = protect(original).expect("protect succeeds on Windows");
        // DPAPI output is structurally different from input.
        assert_ne!(ciphertext, original.to_vec());
        // Plaintext must round-trip exactly.
        let recovered = unprotect(&ciphertext).expect("unprotect succeeds");
        assert_eq!(recovered, original.to_vec());
    }

    #[test]
    fn protect_short_payload_round_trips() {
        let original = b"x";
        let ciphertext = protect(original).expect("protect short payload");
        let recovered = unprotect(&ciphertext).expect("unprotect short payload");
        assert_eq!(recovered, original.to_vec());
    }

    #[test]
    fn protect_32_byte_seed_round_trips() {
        // The actual substrate_signing_seed is 32 bytes Ed25519. Test that
        // shape explicitly.
        let mut seed = [0u8; 32];
        for (i, byte) in seed.iter_mut().enumerate() {
            *byte = (i as u8).wrapping_mul(17).wrapping_add(0xa5);
        }
        let ciphertext = protect(&seed).expect("protect 32-byte seed");
        let recovered = unprotect(&ciphertext).expect("unprotect 32-byte seed");
        assert_eq!(recovered, seed.to_vec());
    }

    #[test]
    fn unprotect_corrupted_ciphertext_returns_winapi_error() {
        let original = b"sentinel_value";
        let ciphertext = protect(original).expect("protect");
        // Mangle the middle byte.
        let mut corrupted = ciphertext.clone();
        if corrupted.len() >= 10 {
            let mid = corrupted.len() / 2;
            corrupted[mid] ^= 0xff;
        }
        let result = unprotect(&corrupted);
        assert!(
            result.is_err(),
            "corrupted ciphertext must fail to unwrap; got Ok"
        );
        // Error must be the WinApi variant (CryptUnprotectData returned FALSE
        // for the bad ciphertext) — not EmptyBlob.
        match result {
            Err(DpapiError::WinApi { operation, .. }) => {
                assert_eq!(operation, "unprotect");
            }
            other => panic!("unexpected variant: {other:?}"),
        }
    }

    #[test]
    fn protect_produces_different_ciphertext_each_call_for_same_plaintext() {
        // DPAPI uses a random salt internally — same plaintext encrypted
        // twice produces different ciphertexts (semantic security).
        let plaintext = b"deterministic_input_should_get_random_ciphertext";
        let c1 = protect(plaintext).expect("protect 1");
        let c2 = protect(plaintext).expect("protect 2");
        assert_ne!(
            c1, c2,
            "DPAPI must produce semantically-secure (randomized) ciphertexts; \
             matching outputs would indicate ECB-mode or missing salt"
        );
        // Both still decrypt to the same plaintext.
        let p1 = unprotect(&c1).expect("unprotect 1");
        let p2 = unprotect(&c2).expect("unprotect 2");
        assert_eq!(p1, plaintext);
        assert_eq!(p2, plaintext);
    }

    #[test]
    fn unprotect_empty_input_errors_not_panics() {
        let result = unprotect(b"");
        assert!(
            result.is_err(),
            "empty ciphertext must error, not panic or return empty plaintext"
        );
    }
}
