//! anchor-surface-host — daemon binary.
//!
//! Listens on `127.0.0.1:0` (OS-picks a port), writes the resolved port to
//! `<anchor_surface_dir>/port.txt` (0600 on Unix), and serves get_pubkey /
//! sign / ping requests over canonical-bytes envelopes.
//!
//! ## Environment variables
//!
//! - `MYCO_ANCHOR_SURFACE_DIR`: override the host directory (defaults to
//!   `$HOME/.myco/anchor_surface/` or `%USERPROFILE%\.myco\anchor_surface\`).
//! - `MYCO_ANCHOR_SURFACE_BIND_ADDR`: override the bind address (default
//!   `127.0.0.1:0`). Useful for tests that want to pin a specific port.
//! - `MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX`: 64-char hex (32 bytes) override
//!   of the owner seed. **Testing only** — production hosts always
//!   load-or-create from `owner_key.cb`.
//!
//! ## Stdout/stderr
//!
//! On successful boot, the host prints a single line to stdout:
//!
//! ```text
//! anchor-surface-host listening on 127.0.0.1:<PORT>
//! ```
//!
//! This lets test harnesses block on first-line stdout to know the host is
//! ready (instead of polling port.txt with delays).

use std::io::Write;
use std::net::{TcpListener, TcpStream};
use std::path::Path;
use std::thread;

use anchor_surface_host::identity::OwnerIdentity;
use anchor_surface_host::protocol::{read_frame, write_frame, Request, Response};
use anchor_surface_host::{
    default_anchor_surface_dir, HostError, PORT_DISCOVERY_FILENAME,
};

fn main() {
    if let Err(e) = run() {
        eprintln!("anchor-surface-host fatal: {e}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), HostError> {
    let dir = default_anchor_surface_dir();
    std::fs::create_dir_all(&dir)?;

    // M-anchor-1: load (or genesis) the owner Ed25519 identity. The seed
    // bytes never leave the OwnerIdentity struct — only signatures + pubkey
    // are exposed via the protocol layer.
    let identity = if let Ok(hex_seed) = std::env::var("MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX") {
        let seed = parse_hex_seed(&hex_seed)?;
        OwnerIdentity::from_seed(seed)
    } else {
        OwnerIdentity::load_or_create(&dir)?
    };

    let bind_addr =
        std::env::var("MYCO_ANCHOR_SURFACE_BIND_ADDR").unwrap_or_else(|_| "127.0.0.1:0".to_string());
    let listener = TcpListener::bind(&bind_addr)?;
    let local_addr = listener.local_addr()?;
    write_port_discovery(&dir, local_addr.port())?;

    println!("anchor-surface-host listening on {}", local_addr);
    std::io::stdout().flush().ok();

    // Wrap the identity in Arc so per-connection threads share it without
    // copying the seed.
    let identity = std::sync::Arc::new(identity);

    for incoming in listener.incoming() {
        match incoming {
            Ok(stream) => {
                let id = identity.clone();
                thread::spawn(move || {
                    if let Err(e) = serve_connection(stream, id) {
                        eprintln!("anchor-surface-host connection error: {e}");
                    }
                });
            }
            Err(e) => {
                eprintln!("anchor-surface-host accept error: {e}");
            }
        }
    }
    Ok(())
}

fn parse_hex_seed(hex: &str) -> Result<[u8; 32], HostError> {
    if hex.len() != 64 {
        return Err(HostError::Identity(format!(
            "MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX has {} chars (expected 64)",
            hex.len()
        )));
    }
    let mut out = [0u8; 32];
    for i in 0..32 {
        out[i] = u8::from_str_radix(&hex[i * 2..i * 2 + 2], 16).map_err(|e| {
            HostError::Identity(format!("hex parse at byte {i}: {e}"))
        })?;
    }
    Ok(out)
}

/// Write the OS-assigned port to `<dir>/port.txt` (0600 on Unix). Operator
/// clients read this file to find a running host.
fn write_port_discovery(dir: &Path, port: u16) -> Result<(), HostError> {
    let path = dir.join(PORT_DISCOVERY_FILENAME);
    let tmp = dir.join(format!("{PORT_DISCOVERY_FILENAME}.tmp"));
    {
        let mut f = std::fs::File::create(&tmp)?;
        writeln!(f, "{port}")?;
        f.sync_all()?;
    }
    std::fs::rename(&tmp, &path)?;
    restrict_owner_only(&path)?;
    Ok(())
}

fn restrict_owner_only(path: &Path) -> Result<(), HostError> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let perms = std::fs::Permissions::from_mode(0o600);
        std::fs::set_permissions(path, perms)?;
    }
    #[cfg(not(unix))]
    {
        let _ = path;
    }
    Ok(())
}

/// Serve one accepted TCP connection. Reads framed requests, dispatches them
/// against the owner identity, writes framed responses. Closes the connection
/// on clean EOF or on any protocol/I/O error.
fn serve_connection(
    mut stream: TcpStream,
    identity: std::sync::Arc<OwnerIdentity>,
) -> Result<(), HostError> {
    loop {
        let frame = match read_frame(&mut stream)? {
            Some(b) => b,
            None => return Ok(()), // clean EOF
        };
        let response = match Request::decode(&frame) {
            Ok(Request::GetPubkey) => Response::Pubkey {
                pubkey: identity.public_key_bytes(),
            },
            Ok(Request::Sign { message }) => {
                let sig = identity.sign(&message);
                let mut sig_bytes = [0u8; 64];
                sig_bytes.copy_from_slice(sig.as_ref());
                Response::Signature {
                    signature: sig_bytes,
                }
            }
            Ok(Request::Ping) => Response::Pong,
            // M-anchor-2 §9.2.1: birth attestation.
            Ok(Request::BirthAttest {
                substrate_id,
                genesis_timestamp_unix_ns,
                spore_schema_hash,
                anchor_endpoint_pubkey,
            }) => {
                let (sig, attested_bytes) = identity.birth_attest(
                    &substrate_id,
                    genesis_timestamp_unix_ns,
                    &spore_schema_hash,
                    &anchor_endpoint_pubkey,
                );
                let mut sig_bytes = [0u8; 64];
                sig_bytes.copy_from_slice(sig.as_ref());
                Response::BirthAttestation {
                    signature: sig_bytes,
                    owner_pubkey: identity.public_key_bytes(),
                    attested_canonical_bytes: attested_bytes,
                }
            }
            // M-anchor-3 §9.2.5: anchor-generated nonce.
            Ok(Request::GenerateAnchorNonce { ttl_seconds }) => {
                let (nonce, issued_at, expiry, sig) =
                    identity.generate_anchor_nonce(ttl_seconds);
                let mut sig_bytes = [0u8; 64];
                sig_bytes.copy_from_slice(sig.as_ref());
                Response::AnchorNonce {
                    nonce,
                    anchor_timestamp_unix_ns: issued_at,
                    expiry_unix_ns: expiry,
                    signature: sig_bytes,
                }
            }
            // M-anchor-3 §9.2.6: anchor wall-clock.
            Ok(Request::GetAnchorWallClock) => {
                let (now, sig) = identity.anchor_wall_clock();
                let mut sig_bytes = [0u8; 64];
                sig_bytes.copy_from_slice(sig.as_ref());
                Response::AnchorWallClock {
                    anchor_timestamp_unix_ns: now,
                    signature: sig_bytes,
                }
            }
            // M-anchor-3 §9.2.7: owner liveness heartbeat.
            Ok(Request::Heartbeat) => {
                let (now, nonce, sig) = identity.heartbeat();
                let mut sig_bytes = [0u8; 64];
                sig_bytes.copy_from_slice(sig.as_ref());
                Response::HeartbeatResponse {
                    anchor_timestamp_unix_ns: now,
                    heartbeat_nonce: nonce,
                    signature: sig_bytes,
                }
            }
            Err(e) => Response::Error {
                message: format!("decode: {e}"),
            },
        };
        let body = response.encode()?;
        write_frame(&mut stream, &body)?;
    }
}
