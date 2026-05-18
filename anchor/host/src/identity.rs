//! Owner Ed25519 identity — persisted out of operator process memory.
//!
//! ## On-disk schema (canonical-bytes envelope)
//!
//! ```text
//! Map({
//!   "format_version": Uint(1),
//!   "seed":           Bytes(32),
//!   "created_at_unix_ns": Timestamp,
//! })
//! ```
//!
//! Permissions: `0600` on Unix (owner read+write only) immediately after
//! atomic rename. On Windows, ACL inheritance from the parent directory
//! is the interim protection — hardening to a real Windows ACL deferred to
//! M-anchor-1.5 (full OS-sealed keystore).
//!
//! ## Migration from operator_keys/identity.key
//!
//! Pre-M-anchor-1 operators kept a 32-byte raw seed in
//! `~/.myco/operator_keys/identity.key`. The host's `load_or_create`
//! intentionally does NOT auto-migrate that file — the operator deployment
//! migration story is documented separately. Auto-migration is risky
//! (silent re-binding of trust) and deferred to an explicit one-shot tool.

use std::fs;
use std::io::{Read, Write};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

use myco_kernel_shared::canonical_bytes::{decode, encode, map_get_bytes, map_get_uint, Value};
use myco_kernel_shared::crypto::{Ed25519PrivateKey, Ed25519PublicKey, Ed25519Signature};

use crate::{HostError, Result, OWNER_KEY_FILENAME};

/// Current owner-key file format version. Bumped on any breaking change to
/// the canonical-bytes schema.
pub const OWNER_KEY_FORMAT_VERSION: u64 = 1;

/// In-memory owner identity inside the anchor_surface_host process.
///
/// The seed bytes never leave this struct; the only outward-facing API is
/// `public_key()` + `sign(message)`. The host process is the ONLY place
/// where this struct is constructed.
pub struct OwnerIdentity {
    private_key: Ed25519PrivateKey,
    public_key: Ed25519PublicKey,
}

impl OwnerIdentity {
    /// Load the owner identity from `<dir>/owner_key.cb`, or generate and
    /// persist a fresh one if no file exists.
    ///
    /// On Unix the file is `chmod 0600`d immediately after the atomic rename;
    /// on Windows it inherits ACLs from the parent directory (interim
    /// protection — full ACL hardening is M-anchor-1.5 work).
    pub fn load_or_create(dir: &Path) -> Result<Self> {
        ensure_dir(dir)?;
        let path = dir.join(OWNER_KEY_FILENAME);
        if path.exists() {
            return Self::load_from(&path);
        }
        let seed = generate_owner_seed();
        Self::save_to(&path, &seed)?;
        let private_key = Ed25519PrivateKey::from_seed(&seed);
        let public_key = private_key.public_key();
        Ok(OwnerIdentity {
            private_key,
            public_key,
        })
    }

    /// Construct from an explicit seed (testing convenience).
    ///
    /// **The host's production code path is [`load_or_create`].** This
    /// constructor exists for `tests/e2e.rs` to pin a known keypair.
    pub fn from_seed(seed: [u8; 32]) -> Self {
        let private_key = Ed25519PrivateKey::from_seed(&seed);
        let public_key = private_key.public_key();
        OwnerIdentity {
            private_key,
            public_key,
        }
    }

    /// Get the 32-byte Ed25519 public key bytes.
    pub fn public_key_bytes(&self) -> [u8; 32] {
        let mut out = [0u8; 32];
        out.copy_from_slice(self.public_key.as_ref());
        out
    }

    /// Sign a message with the owner's Ed25519 private key. Returns the
    /// 64-byte RFC 8032 signature.
    pub fn sign(&self, message: &[u8]) -> Ed25519Signature {
        self.private_key.sign(message)
    }

    /// **M-anchor-2 §9.2.1**: produce a birth attestation for a fresh
    /// substrate. Builds the L0/cards/AS_anchor_surface §3 5-tuple canonical bytes (with a
    /// domain-separator so the signature can't be confused with a plain
    /// Sign signature) and returns `(signature, attested_bytes)`.
    ///
    /// The caller (anchor_surface_host server) returns these alongside the
    /// owner pubkey so the substrate can persist all three in its DAG.
    /// Future boots re-verify by recomputing the canonical bytes from the
    /// stored 5-tuple fields and checking the signature.
    pub fn birth_attest(
        &self,
        substrate_id: &[u8; 32],
        genesis_timestamp_unix_ns: i64,
        spore_schema_hash: &[u8; 32],
        anchor_endpoint_pubkey: &[u8; 32],
    ) -> (Ed25519Signature, Vec<u8>) {
        let owner_pubkey = self.public_key_bytes();
        let attested_bytes = crate::protocol::birth_attestation_canonical_bytes(
            substrate_id,
            genesis_timestamp_unix_ns,
            spore_schema_hash,
            &owner_pubkey,
            anchor_endpoint_pubkey,
        );
        let signature = self.private_key.sign(&attested_bytes);
        (signature, attested_bytes)
    }

    /// **M-anchor-3 §9.2.5**: generate a fresh anchor-side nonce + sign the
    /// (nonce, issued_at, expiry) tuple. Returns `(nonce, issued_at_ns,
    /// expiry_ns, signature)`. `ttl_seconds` is clamped to `[1, 3600]`.
    pub fn generate_anchor_nonce(
        &self,
        ttl_seconds: u64,
    ) -> ([u8; 32], i64, i64, Ed25519Signature) {
        let ttl = ttl_seconds.clamp(1, 3600);
        let nonce = generate_random_32();
        let issued_at = current_unix_ns();
        let expiry = issued_at.saturating_add((ttl as i64) * 1_000_000_000);
        let bytes = crate::protocol::anchor_nonce_canonical_bytes(&nonce, issued_at, expiry);
        let signature = self.private_key.sign(&bytes);
        (nonce, issued_at, expiry, signature)
    }

    /// **M-anchor-3 §9.2.6**: read the anchor's current wall-clock + sign it.
    /// Returns `(timestamp_unix_ns, signature)`.
    pub fn anchor_wall_clock(&self) -> (i64, Ed25519Signature) {
        let now = current_unix_ns();
        let bytes = crate::protocol::anchor_wallclock_canonical_bytes(now);
        let signature = self.private_key.sign(&bytes);
        (now, signature)
    }

    /// **M-anchor-3 §9.2.7**: produce an owner liveness heartbeat. Returns
    /// `(timestamp_unix_ns, heartbeat_nonce, signature)`. The nonce is fresh
    /// per call so two heartbeats are byte-distinguishable even at the same
    /// timestamp resolution.
    pub fn heartbeat(&self) -> (i64, [u8; 32], Ed25519Signature) {
        let now = current_unix_ns();
        let nonce = generate_random_32();
        let bytes = crate::protocol::anchor_heartbeat_canonical_bytes(now, &nonce);
        let signature = self.private_key.sign(&bytes);
        (now, nonce, signature)
    }

    /// Load identity from an explicit file path. Errors if the file is
    /// missing, malformed, or version-mismatched.
    fn load_from(path: &Path) -> Result<Self> {
        let mut f = fs::File::open(path)?;
        let mut bytes = Vec::new();
        f.read_to_end(&mut bytes)?;
        let decoded = decode(&bytes)?;
        let map = match decoded {
            Value::Map(m) => m,
            _ => {
                return Err(HostError::Identity(
                    "owner_key.cb root is not a Map".to_string(),
                ))
            }
        };
        let version = map_get_uint(&map, "format_version")?;
        if version != OWNER_KEY_FORMAT_VERSION {
            return Err(HostError::Identity(format!(
                "owner_key.cb format_version {version} != {OWNER_KEY_FORMAT_VERSION}"
            )));
        }
        let seed_bytes = map_get_bytes(&map, "seed")?;
        if seed_bytes.len() != 32 {
            return Err(HostError::Identity(format!(
                "owner_key.cb seed has {} bytes (expected 32)",
                seed_bytes.len()
            )));
        }
        let mut seed = [0u8; 32];
        seed.copy_from_slice(seed_bytes);
        let private_key = Ed25519PrivateKey::from_seed(&seed);
        let public_key = private_key.public_key();
        Ok(OwnerIdentity {
            private_key,
            public_key,
        })
    }

    /// Persist seed → canonical-bytes envelope at `<path>` atomically
    /// (write to `.tmp`, rename, then chmod 0600 on Unix).
    fn save_to(path: &Path, seed: &[u8; 32]) -> Result<()> {
        use std::collections::BTreeMap;
        let parent = path.parent().ok_or_else(|| {
            HostError::Identity(format!("owner_key.cb path {path:?} has no parent dir"))
        })?;
        ensure_dir(parent)?;
        let tmp_path = path.with_extension("cb.tmp");
        let mut m = BTreeMap::new();
        m.insert(
            "format_version".to_string(),
            Value::Uint(OWNER_KEY_FORMAT_VERSION),
        );
        m.insert("seed".to_string(), Value::Bytes(seed.to_vec()));
        m.insert(
            "created_at_unix_ns".to_string(),
            Value::Timestamp(current_unix_ns()),
        );
        let bytes = encode(&Value::Map(m))?;
        {
            let mut f = fs::File::create(&tmp_path)?;
            f.write_all(bytes.as_ref())?;
            f.sync_all()?;
        }
        fs::rename(&tmp_path, path)?;
        restrict_secret_file_permissions(path)?;
        Ok(())
    }
}

impl std::fmt::Debug for OwnerIdentity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Never leak the private seed in debug output. Public key bytes are
        // public by definition.
        f.debug_struct("OwnerIdentity")
            .field("public_key", &hex_string(&self.public_key_bytes()))
            .field("private_key", &"<redacted>")
            .finish()
    }
}

fn hex_string(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

fn ensure_dir(dir: &Path) -> Result<()> {
    if !dir.exists() {
        fs::create_dir_all(dir)?;
    }
    Ok(())
}

fn current_unix_ns() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as i64)
        .unwrap_or(0)
}

/// **M-anchor-3**: generate a fresh 32-byte random value (for nonces and
/// heartbeat freshness markers). Uses the same OS-randomness composition
/// pattern as `generate_owner_seed` with a distinct domain string so the
/// two RNG draws cannot collide.
fn generate_random_32() -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-anchor-surface-runtime-random-v1");
    h.update(current_unix_ns().to_le_bytes());
    h.update(std::process::id().to_le_bytes());
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    // Counter that increments each call to guarantee uniqueness even when
    // current_unix_ns granularity collides.
    use std::sync::atomic::{AtomicU64, Ordering};
    static CTR: AtomicU64 = AtomicU64::new(0);
    let c = CTR.fetch_add(1, Ordering::Relaxed);
    h.update(c.to_le_bytes());
    let fn_addr = generate_random_32 as *const () as usize;
    h.update(fn_addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

/// Generate a fresh 32-byte owner seed.
///
/// Same construction pattern as the substrate-side `generate_substrate_signing_seed`:
/// mix in unix-ns, pid, stack address, and a function-code address. The
/// domain string is distinct so a substrate signing seed cannot collide with
/// an owner seed even on a same-millisecond birth.
fn generate_owner_seed() -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(b"myco-anchor-surface-owner-seed-v1");
    h.update(current_unix_ns().to_le_bytes());
    h.update(std::process::id().to_le_bytes());
    let stack_var = 0u8;
    let addr = &stack_var as *const u8 as usize;
    h.update(addr.to_le_bytes());
    let fn_addr = generate_owner_seed as *const () as usize;
    h.update(fn_addr.to_le_bytes());
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

/// Harden the on-disk permissions of the owner key file to "owner read+write
/// only" (`0600` on Unix). On Windows this is a no-op pending M-anchor-1.5.
fn restrict_secret_file_permissions(path: &Path) -> Result<()> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let perms = fs::Permissions::from_mode(0o600);
        fs::set_permissions(path, perms)?;
    }
    #[cfg(not(unix))]
    {
        let _ = path;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::crypto::verify_signature;
    use std::path::PathBuf;
    use std::sync::atomic::{AtomicU64, Ordering};

    static TEST_COUNTER: AtomicU64 = AtomicU64::new(0);

    fn fresh_dir() -> PathBuf {
        let counter = TEST_COUNTER.fetch_add(1, Ordering::Relaxed);
        let base = std::env::temp_dir().join(format!(
            "myco-anchor-host-test-{}-{}-{}",
            std::process::id(),
            current_unix_ns(),
            counter
        ));
        std::fs::create_dir_all(&base).expect("create test dir");
        base
    }

    #[test]
    fn load_or_create_persists_seed_and_returns_consistent_pubkey() {
        let dir = fresh_dir();
        let id1 = OwnerIdentity::load_or_create(&dir).unwrap();
        let id2 = OwnerIdentity::load_or_create(&dir).unwrap();
        assert_eq!(id1.public_key_bytes(), id2.public_key_bytes());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn fresh_dirs_yield_different_pubkeys() {
        let a = fresh_dir();
        let b = fresh_dir();
        let ia = OwnerIdentity::load_or_create(&a).unwrap();
        let ib = OwnerIdentity::load_or_create(&b).unwrap();
        assert_ne!(ia.public_key_bytes(), ib.public_key_bytes());
        let _ = fs::remove_dir_all(&a);
        let _ = fs::remove_dir_all(&b);
    }

    #[test]
    fn sign_then_verify_roundtrip() {
        let dir = fresh_dir();
        let id = OwnerIdentity::load_or_create(&dir).unwrap();
        let msg = b"hello m-anchor-1";
        let sig = id.sign(msg);
        let pk = id.public_key_bytes();
        verify_signature(&pk, sig.as_ref(), msg).unwrap();
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn debug_redacts_private_seed() {
        let id = OwnerIdentity::from_seed([0xffu8; 32]);
        let s = format!("{:?}", id);
        assert!(s.contains("<redacted>"));
        // Must not leak the raw 32-byte seed pattern (0xff repeated 32 times).
        assert!(!s.contains("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"));
    }

    #[test]
    fn from_seed_is_deterministic() {
        let seed = [0xab; 32];
        let id1 = OwnerIdentity::from_seed(seed);
        let id2 = OwnerIdentity::from_seed(seed);
        assert_eq!(id1.public_key_bytes(), id2.public_key_bytes());
        let sig1 = id1.sign(b"determinism");
        let sig2 = id2.sign(b"determinism");
        assert_eq!(sig1.as_ref(), sig2.as_ref());
    }

    #[cfg(unix)]
    #[test]
    fn owner_key_file_is_0600_on_unix() {
        use std::os::unix::fs::PermissionsExt;
        let dir = fresh_dir();
        let _id = OwnerIdentity::load_or_create(&dir).unwrap();
        let path = dir.join(OWNER_KEY_FILENAME);
        let meta = fs::metadata(&path).unwrap();
        let mode = meta.permissions().mode() & 0o777;
        assert_eq!(mode, 0o600, "owner_key.cb expected to be 0600 on Unix");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn malformed_owner_key_file_returns_identity_error() {
        let dir = fresh_dir();
        let path = dir.join(OWNER_KEY_FILENAME);
        std::fs::write(&path, b"not canonical bytes").unwrap();
        let err = OwnerIdentity::load_or_create(&dir).unwrap_err();
        match err {
            HostError::CanonicalBytes(_) | HostError::Identity(_) => {}
            other => panic!("expected canonical-bytes or identity error, got {other:?}"),
        }
        let _ = fs::remove_dir_all(&dir);
    }
}
