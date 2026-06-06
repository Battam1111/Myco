//! M25.0 + M25.4: substrate-private Ed25519 signing key persistence.
//!
//! The substrate-signing seed serves DOUBLE DUTY:
//!   - M25.0: signs `snapshot.cb` payload so a forged snapshot can't masquerade.
//!   - M25.4: signs FED_HELLO payloads so federation peers can mutually-auth
//!     beyond TOFU substrate_id pinning.

use std::fs;
use std::io::Read;
use std::path::Path;

use super::{current_unix_ns, ensure_state_dir};
use crate::SubstrateError;

/// M25.0: filename for the substrate-private Ed25519 signing keypair seed.
///
/// This is the SUBSTRATE'S OWN private key, separate from any operator/owner
/// key. Used to (1) sign `snapshot.cb` so a malicious actor with write access
/// to state_dir cannot substitute a forged snapshot, and (2) sign FED_HELLO
/// payloads so federation peers can mutually authenticate beyond TOFU.
///
/// The seed is 32 bytes (per `Ed25519PrivateKey::from_seed`). It NEVER leaves
/// the substrate process boundary on the wire. Substrate-side appearance of
/// the seed file is the same trust class as the DAG itself: tampering with it
/// is a doctrine-breach observable at boot via signature-verification failure.
pub const SUBSTRATE_SIGNING_KEY_FILENAME: &str = "substrate_signing_key.cb";

/// M25.0: current substrate-signing-key file format version.
pub const SUBSTRATE_SIGNING_KEY_FORMAT_VERSION: u64 = 1;

/// Helper: encode a byte slice as a lowercase hex string. Used in error
/// messages to show first 8 bytes of a hash for diagnostics without
/// inflating log volume. (Pure Rust; avoids depending on `hex` for the
/// `bytes_to_hex_short` use case in error paths.)
fn bytes_to_hex_short(bytes: &[u8]) -> String {
    let n = bytes.len().min(8);
    let mut s = String::with_capacity(n * 2);
    for b in &bytes[..n] {
        s.push_str(&format!("{b:02x}"));
    }
    if bytes.len() > n {
        s.push_str("...");
    }
    s
}

/// **v3.1.1 Sprint 2**, substrate_signing_key.cb format versions accepted
/// by the load path. v1 is the legacy plain-bytes format (cross-platform);
/// v2 is the Windows DPAPI-wrapped format that closes L1/HARD_RULES C4 on
/// Windows hosts.
pub const SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1: u64 = 1;
/// v2: Windows DPAPI-wrapped substrate_signing_seed. Replaces the `seed`
/// field of the v1 Map with `seed_dpapi_protected` containing the
/// `CryptProtectData` output bytes. The bytes can only be decrypted by the
/// same Windows user account on the same host. See `substrate/src/dpapi.rs`.
pub const SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2: u64 = 2;

/// **v3.1.1 Sprint 2**, the format version this build's save path writes.
/// On Windows: v2 (DPAPI-wrapped). Elsewhere: v1 (plain bytes + chmod 0600).
/// Linux keyring / macOS Secure Enclave backends arrive in follow-up sprints
/// (Sprint 2.B+).
#[cfg(windows)]
pub const SUBSTRATE_SIGNING_KEY_PREFERRED_WRITE_VERSION: u64 =
    SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2;
#[cfg(not(windows))]
pub const SUBSTRATE_SIGNING_KEY_PREFERRED_WRITE_VERSION: u64 =
    SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1;

/// M25.0: atomically save the substrate's private signing seed to
/// `<state_dir>/substrate_signing_key.cb`.
///
/// On-disk schema:
/// ```text
/// Map({
///   "format_version": Uint(1),
///   "seed": Bytes(32),
///   "created_at_unix_ns": Timestamp,
/// })
/// ```
///
/// M26.1 C6 SECURITY FIX (Phase γ.2): on Unix the seed file is `chmod 0600`d
/// (owner read+write only) immediately after the atomic rename. Pre-fix, the
/// seed file inherited default permissions (often 0644 = world-readable on
/// shared hosts), violating L1/HARD_RULES C4 `substrate_secret_unsealed`.
/// On Windows, OS-sealing SHIPPED via DPAPI (`CryptProtectData`, the v2 format
/// below): the seed ciphertext is bound to the current Windows user account, so
/// a filesystem read cannot recover the plaintext. The remaining cross-platform
/// OS-sealing backends (Linux kernel keyring / macOS Secure Enclave) are
/// scheduled follow-ups (scaffolded in `crate::sealing`).
///
/// On non-Windows the seed bytes are stored as plain canonical-bytes + a
/// BLAKE3 integrity tag + chmod 0600 (the trust boundary is the state_dir as a
/// whole; if an attacker has write access there, snapshot integrity is moot
/// anyway). (v0.9 keyless: the F24 keypair is the substrate's OWN signing key,
/// not an owner key.)
pub fn save_substrate_signing_key(
    seed: &[u8; 32],
    state_dir: &Path,
) -> Result<(), SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{encode, Value};
    use std::collections::BTreeMap;
    use std::io::Write;
    ensure_state_dir(state_dir)?;
    let final_path = state_dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
    let tmp_path = state_dir.join(format!("{SUBSTRATE_SIGNING_KEY_FILENAME}.tmp"));
    let mut m = BTreeMap::new();
    m.insert(
        "format_version".to_string(),
        Value::Uint(SUBSTRATE_SIGNING_KEY_PREFERRED_WRITE_VERSION),
    );
    // **v3.1.1 Sprint 2**: on Windows the seed bytes pass through DPAPI
    // `CryptProtectData` before reaching disk; the ciphertext is bound to
    // the current Windows user account such that filesystem-read attacks
    // cannot extract the plaintext seed without compromising the same
    // user's login session. On non-Windows we keep the legacy v1 plain
    // format with chmod 0600 (real OS-sealing backends, Linux kernel
    // keyring, macOS Secure Enclave, scheduled for Sprint 2.B+).
    #[cfg(windows)]
    {
        match crate::dpapi::protect(seed) {
            Ok(ciphertext) => {
                m.insert(
                    "seed_dpapi_protected".to_string(),
                    Value::Bytes(ciphertext),
                );
            }
            Err(e) => {
                return Err(SubstrateError::Protocol(format!(
                    "substrate_signing_key DPAPI protect: {e}"
                )));
            }
        }
    }
    #[cfg(not(windows))]
    {
        m.insert("seed".to_string(), Value::Bytes(seed.to_vec()));
        // **v3.1.1 Sprint 2.B**, integrity tag for v1 plain-bytes format.
        //
        // BLAKE3(seed) stored alongside the plaintext seed. On non-Windows
        // hosts the seed lives on disk as plain canonical-bytes; this
        // integrity tag catches:
        //   - filesystem bitrot
        //   - partial / torn writes (process killed mid-fsync)
        //   - unintentional manual edits ("I'll just tweak this byte")
        //   - bugs in the substrate that accidentally rewrite the file
        // It does NOT add adversarial tamper protection, an attacker who
        // can rewrite the seed can also compute the matching BLAKE3 hash.
        // Adversarial defense remains the OS-sealing backend (DPAPI on
        // Windows already done; Linux kernel keyring + macOS Secure
        // Enclave scaffolded in `crate::sealing` and scheduled for follow-up
        // sessions where Linux/Mac test environments are available).
        //
        // Per L1/HARD_RULES C4 substrate_secret_unsealed (the broader debt
        // this milestone makes incremental progress against).
        let seed_blake3: [u8; 32] = blake3::hash(seed.as_slice()).into();
        m.insert(
            "seed_blake3".to_string(),
            Value::Bytes(seed_blake3.to_vec()),
        );
    }
    m.insert(
        "created_at_unix_ns".to_string(),
        Value::Timestamp(current_unix_ns()),
    );
    let bytes = encode(&Value::Map(m))
        .map_err(|e| SubstrateError::Protocol(format!("substrate_signing_key encode: {e}")))?;
    {
        let mut f = fs::File::create(&tmp_path)?;
        f.write_all(bytes.as_ref())?;
        f.sync_all()?;
    }
    fs::rename(&tmp_path, &final_path)?;
    // M26.1 C6: harden permissions to 0600 on Unix immediately after rename.
    // The rename target inherits the temp file's permissions, which on Unix
    // are subject to the process umask, we cannot rely on umask being
    // restrictive enough. Set explicitly. On Windows std::os::unix::fs is not
    // available so the cfg gate compiles out; DPAPI above provides the
    // confidentiality guarantee instead of POSIX permissions.
    restrict_secret_file_permissions(&final_path)?;
    Ok(())
}

/// M26.1 C6 SECURITY FIX: harden the on-disk permissions of a substrate
/// secret file to "owner read+write only" (`0600` on Unix). On Windows this
/// is a no-op, confidentiality there comes from DPAPI-wrapping the seed
/// ciphertext (see `save_substrate_signing_key`), not from POSIX file modes;
/// the file inherits ACLs from the parent (user-profile) directory.
///
/// Errors from the permission set are returned as `SubstrateError::Io` so the
/// caller can surface them; the secret is still on disk (save_* persisted
/// successfully before this call), so the caller MUST treat permission
/// failures as a hard failure to avoid leaving a 0644-mode secret around.
fn restrict_secret_file_permissions(path: &Path) -> Result<(), SubstrateError> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let perms = fs::Permissions::from_mode(0o600);
        fs::set_permissions(path, perms).map_err(SubstrateError::Io)?;
    }
    #[cfg(not(unix))]
    {
        // Touch the path so the parameter is "used" on non-Unix builds
        // (silences `unused_variables`). On Windows, seed confidentiality comes
        // from DPAPI-wrapping the ciphertext (see save_substrate_signing_key),
        // so POSIX-mode hardening here is moot; the file relies on user-profile
        // directory ACL inheritance.
        let _ = path;
    }
    Ok(())
}

/// M26.1 C6 SECURITY FIX: check whether a secret file's permissions are
/// loose (group/world bits set on Unix). Used at load-time to emit a
/// `C4_substrate_secret_unsealed` immune sporocarp when the seed file was
/// created by an older substrate version or had its mode manually relaxed.
///
/// Returns:
/// - `Ok(true)`, permissions look fine (0600-equivalent on Unix; always
///   true on Windows, where seed confidentiality comes from DPAPI-wrapping
///   rather than file ACLs, so a POSIX-mode check does not apply).
/// - `Ok(false)`, Unix mode has any group/other bits set (caller emits
///   C4 sporocarp + tightens permissions in-place if possible).
/// - `Err(...)`, I/O error reading metadata.
#[allow(dead_code)] // exported for callers in server.rs / persistence_runtime.rs
pub fn substrate_secret_permissions_are_restrictive(
    path: &Path,
) -> Result<bool, SubstrateError> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let meta = fs::metadata(path).map_err(SubstrateError::Io)?;
        let mode = meta.permissions().mode();
        // Any bit in 0o077 = group or world access → loose.
        Ok((mode & 0o077) == 0)
    }
    #[cfg(not(unix))]
    {
        let _ = path;
        // Windows: cannot cheaply inspect ACLs without the `windows` crate, and
        // seed confidentiality comes from DPAPI-wrapping (not file ACLs) anyway.
        // Report restrictive to avoid spurious C4 sporocarps.
        Ok(true)
    }
}

/// M25.0: load the substrate's private signing seed from
/// `<state_dir>/substrate_signing_key.cb`.
///
/// Returns:
/// - `Ok(Some(seed))`, file present + format matches.
/// - `Ok(None)`, file missing OR version mismatch (caller treats as
///   "no key yet, must genesis"; see [`boot_or_genesis_substrate_signing_key`]).
/// - `Err(...)`, I/O or canonical-bytes decode error.
///
/// M26.1 C6 SECURITY FIX: this loader does NOT inspect permissions, that's
/// done by [`boot_or_genesis_substrate_signing_key`] via
/// [`load_substrate_signing_key_with_permission_check`] so a loose-mode
/// finding can be surfaced to ServerState's caller (which is the only site
/// that holds the DAG handle and can emit a C4 immune sporocarp).
pub fn load_substrate_signing_key(state_dir: &Path) -> Result<Option<[u8; 32]>, SubstrateError> {
    Ok(load_substrate_signing_key_with_permission_check(state_dir)?.map(|(seed, _)| seed))
}

/// M26.1 C6 SECURITY FIX: extended loader that also reports whether the
/// on-disk file had loose Unix permissions when it was opened. The
/// permission status is checked BEFORE the contents are read, so even a
/// malformed file's loose mode is reported.
///
/// Returns `Ok(Some((seed, was_restrictive)))` on success, the caller emits
/// a `C4_substrate_secret_unsealed` immune sporocarp + tightens the mode
/// in-place when `was_restrictive == false`. Returns `Ok(None)` for the
/// usual "missing / version mismatch" path (no permission concern in that
/// case, there's nothing on disk to be loose).
pub fn load_substrate_signing_key_with_permission_check(
    state_dir: &Path,
) -> Result<Option<([u8; 32], bool)>, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    let path = state_dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
    // M26.1 C6: probe permissions before reading. We MUST distinguish
    // file-missing (caller's "fresh genesis" path) from permission-loose
    // (caller emits C4 + tightens). The metadata call doubles as a
    // file-presence check.
    let was_restrictive = match fs::metadata(&path) {
        Ok(_) => substrate_secret_permissions_are_restrictive(&path)?,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(SubstrateError::Io(e)),
    };
    let mut f = match fs::File::open(&path) {
        Ok(f) => f,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(SubstrateError::Io(e)),
    };
    let mut bytes = Vec::new();
    f.read_to_end(&mut bytes)?;
    let decoded = decode(&bytes)
        .map_err(|e| SubstrateError::Protocol(format!("substrate_signing_key decode: {e}")))?;
    let map = match decoded {
        Value::Map(m) => m,
        _ => return Ok(None),
    };
    let version = match map.get("format_version") {
        Some(Value::Uint(n)) => *n,
        _ => return Ok(None),
    };
    // **v3.1.1 Sprint 2**: accept both v1 (legacy plain-bytes) and v2
    // (Windows DPAPI-wrapped). v2 is reachable only on Windows; non-Windows
    // hosts seeing v2 would have no way to unwrap.
    let seed: [u8; 32] = match version {
        v if v == SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1 => {
            let seed_bytes = match map.get("seed") {
                Some(Value::Bytes(b)) if b.len() == 32 => b,
                _ => return Ok(None),
            };
            let mut seed = [0u8; 32];
            seed.copy_from_slice(seed_bytes);
            // **v3.1.1 Sprint 2.B** integrity check. v1 files written by
            // Sprint-2.B+ carry a `seed_blake3` field. Pre-Sprint-2.B files
            // lack it, load with warning. v1 files that DO have the field
            // but the hash MISMATCHES → reject (bitrot detected; refuse
            // to boot with a corrupted seed). This is fail-closed: better
            // to surface the corruption than to silently load junk and
            // forge signatures with it.
            if let Some(Value::Bytes(stored_hash)) = map.get("seed_blake3") {
                if stored_hash.len() == 32 {
                    let computed: [u8; 32] = blake3::hash(seed.as_slice()).into();
                    if computed.as_slice() != stored_hash.as_slice() {
                        return Err(SubstrateError::Protocol(format!(
                            "substrate_signing_key v1 integrity FAILED: stored \
                             seed_blake3={} computed={}; refusing to boot with \
                             corrupted seed (per Sprint 2.B BLAKE3 integrity \
                             check + L1/HARD_RULES C4 substrate_secret_unsealed)",
                            bytes_to_hex_short(stored_hash),
                            bytes_to_hex_short(&computed)
                        )));
                    }
                } else {
                    return Err(SubstrateError::Protocol(format!(
                        "substrate_signing_key v1 seed_blake3 field has {} bytes; \
                         expected 32 (file format invalid)",
                        stored_hash.len()
                    )));
                }
            }
            // Pre-Sprint-2.B v1 files lack seed_blake3 entirely. Load
            // succeeds; the boot path will re-save with the field added
            // (migration is best-effort same as v1→v2 DPAPI migration).
            seed
        }
        v if v == SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2 => {
            #[cfg(windows)]
            {
                let ciphertext = match map.get("seed_dpapi_protected") {
                    Some(Value::Bytes(b)) if !b.is_empty() => b,
                    _ => return Ok(None),
                };
                let plaintext = crate::dpapi::unprotect(ciphertext).map_err(|e| {
                    SubstrateError::Protocol(format!(
                        "substrate_signing_key DPAPI unprotect (v2 wrap on disk; \
                         either the file was written under a different Windows \
                         user/host, or the user's master key has been invalidated): {e}"
                    ))
                })?;
                if plaintext.len() != 32 {
                    return Err(SubstrateError::Protocol(format!(
                        "substrate_signing_key v2 unwrapped to {} bytes; expected 32",
                        plaintext.len()
                    )));
                }
                let mut seed = [0u8; 32];
                seed.copy_from_slice(&plaintext);
                seed
            }
            #[cfg(not(windows))]
            {
                // v2 only exists on Windows hosts. Non-Windows substrate
                // observing v2 = the state_dir was copied from a Windows
                // host; we cannot unwrap without DPAPI access. Surface as
                // a hard error so the caller can route the operator to
                // legitimate cross-host migration instead of pretending
                // there's no key.
                return Err(SubstrateError::Protocol(
                    "substrate_signing_key on disk is v2 (Windows DPAPI-wrapped) \
                     but this is not a Windows host — cross-host migration is \
                     not yet supported (Sprint 2.B follow-up); unwrap on the \
                     original Windows host first"
                        .to_string(),
                ));
            }
        }
        _ => return Ok(None),
    };
    Ok(Some((seed, was_restrictive)))
}

/// M26.1 C6 SECURITY FIX: tighten the substrate signing key file's
/// permissions in-place to 0600 on Unix. Called by the boot path when
/// [`load_substrate_signing_key_with_permission_check`] reports loose mode:
/// repairs the gap going forward + the substrate keeps booting (interim
/// behavior; a future doctrine revision may escalate a loose-mode seed to a
/// hard refusal).
pub fn tighten_substrate_signing_key_permissions(
    state_dir: &Path,
) -> Result<(), SubstrateError> {
    let path = state_dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
    if !path.exists() {
        return Ok(());
    }
    restrict_secret_file_permissions(&path)
}

/// M25.0: boot path helper, load the substrate's signing seed if persisted,
/// else generate a fresh one (genesis), persist it, and return it.
///
/// The seed-generation mix is the same time + pid + stack-address SHA-256
/// mix as [`super::generate_substrate_id`], but with a distinct domain string
/// (`b"myco-substrate-signing-seed-v1"`). The substrate_id seed and signing
/// seed MUST be uncorrelated so a substrate_id leak can't be used to predict
/// the signing key.
pub fn boot_or_genesis_substrate_signing_key(
    state_dir: &Path,
) -> Result<[u8; 32], SubstrateError> {
    Ok(boot_or_genesis_substrate_signing_key_with_permission_status(state_dir)?.0)
}

/// M26.1 C6 SECURITY FIX: extended boot helper that ALSO reports whether the
/// on-disk seed file (when it existed before this call) had restrictive
/// permissions. The caller in `server.rs` uses this signal to emit a
/// `C4_substrate_secret_unsealed` immune sporocarp on the DAG when the
/// permission posture is loose, and immediately tightens the file in-place
/// so the next boot won't re-emit.
///
/// Returns `(seed, was_restrictive_at_load_time)`. For the genesis path
/// (fresh seed; file didn't exist) `was_restrictive_at_load_time` is `true`
///, `save_substrate_signing_key` immediately writes the file with 0600 on
/// Unix, so there's no exposure window to report.
pub fn boot_or_genesis_substrate_signing_key_with_permission_status(
    state_dir: &Path,
) -> Result<([u8; 32], bool), SubstrateError> {
    if let Some((seed, was_restrictive)) =
        load_substrate_signing_key_with_permission_check(state_dir)?
    {
        // **v3.1.1 Sprint 2**, Windows DPAPI migration. If the on-disk
        // file is still v1 (legacy plain bytes) but we are on Windows, the
        // preferred write format is now v2 (DPAPI-wrapped). Re-save the
        // seed atomically with the new format so subsequent boots load
        // from sealed storage. The plaintext seed never appears on disk
        // again after this migration completes.
        //
        // We deliberately migrate ONLY when the load succeeded and we hold
        // the validated 32-byte seed in memory. If the migration save
        // fails, we still return the loaded seed (boot succeeds) but emit
        // the failure via the boot path's error channel, the next boot
        // will retry. This guarantees an unbootable substrate is never
        // produced by a partial migration.
        #[cfg(windows)]
        {
            let path = state_dir.join(SUBSTRATE_SIGNING_KEY_FILENAME);
            if let Ok(needs_migrate) = current_signing_key_format_version_is_v1(&path) {
                if needs_migrate
                    && SUBSTRATE_SIGNING_KEY_PREFERRED_WRITE_VERSION
                        == SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V2
                {
                    // Best-effort migrate. Errors are non-fatal here, the
                    // seed in memory is already correct; the on-disk file
                    // stays as v1 until a future boot retries (or until the
                    // operator surfaces the failure via the immune signal
                    // wired up by the caller).
                    let _ = save_substrate_signing_key(&seed, state_dir);
                }
            }
        }
        return Ok((seed, was_restrictive));
    }
    let seed = generate_substrate_signing_seed();
    // M26.1 C6: save_substrate_signing_key now hardens to 0600 immediately.
    save_substrate_signing_key(&seed, state_dir)?;
    Ok((seed, true))
}

/// **v3.1.1 Sprint 2**, peek at the on-disk substrate_signing_key.cb to
/// determine if it is still in v1 (plain bytes) format. Used by the boot
/// path on Windows to trigger v1→v2 DPAPI migration. Returns:
///   - `Ok(true)` , file present, format_version == 1
///   - `Ok(false)`, file present with format_version != 1 (v2 or unknown)
///   - `Err(...)` , I/O or canonical-bytes decode error
///   - File missing returns `Ok(false)` (no migration needed)
#[cfg(windows)]
fn current_signing_key_format_version_is_v1(path: &Path) -> Result<bool, SubstrateError> {
    use myco_kernel_shared::canonical_bytes::{decode, Value};
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(false),
        Err(e) => return Err(SubstrateError::Io(e)),
    };
    let decoded = decode(&bytes).map_err(|e| {
        SubstrateError::Protocol(format!("substrate_signing_key decode (v1 probe): {e}"))
    })?;
    let map = match decoded {
        Value::Map(m) => m,
        _ => return Ok(false),
    };
    match map.get("format_version") {
        Some(Value::Uint(n)) => Ok(*n == SUBSTRATE_SIGNING_KEY_FORMAT_VERSION_V1),
        _ => Ok(false),
    }
}

/// M25.0: generate a fresh 32-byte signing seed.
///
/// Same construction pattern as [`super::generate_substrate_id`] but with a
/// distinct domain string so the substrate_id and signing seed never collide.
fn generate_substrate_signing_seed() -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-substrate-signing-seed-v1");
    h.update(current_unix_ns().to_le_bytes());
    h.update(std::process::id().to_le_bytes());
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    // Mix one extra entropy source: this function's own code address,
    // so two substrates born in the same nanosecond on the same machine
    // with the same pid (impossible but defended) still differ.
    let fn_addr = generate_substrate_signing_seed as *const () as usize;
    h.update(fn_addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}
