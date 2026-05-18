//! E2E test for anchor_surface_host (M-anchor-1).
//!
//! Spawns the host binary in a temporary directory, connects to it over TCP,
//! exercises ping / get_pubkey / sign, and verifies the signature against the
//! host's reported pubkey using `myco_kernel_shared::crypto::verify_signature`.

use std::io::{BufRead, BufReader};
use std::net::TcpStream;
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::OnceLock;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anchor_surface_host::protocol::{read_frame, write_frame, Request, Response};
use myco_kernel_shared::crypto::verify_signature;

static TEST_COUNTER: AtomicU64 = AtomicU64::new(0);

fn host_binary_path() -> std::path::PathBuf {
    // Cargo sets CARGO_BIN_EXE_<binary-name> for integration tests.
    let env_key = "CARGO_BIN_EXE_anchor-surface-host";
    static CACHED: OnceLock<std::path::PathBuf> = OnceLock::new();
    CACHED
        .get_or_init(|| {
            std::env::var_os(env_key)
                .map(std::path::PathBuf::from)
                .unwrap_or_else(|| panic!("{env_key} env var not set by cargo"))
        })
        .clone()
}

fn current_unix_ns() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0)
}

fn fresh_dir() -> std::path::PathBuf {
    let counter = TEST_COUNTER.fetch_add(1, Ordering::Relaxed);
    let base = std::env::temp_dir().join(format!(
        "myco-anchor-host-e2e-{}-{}-{}",
        std::process::id(),
        current_unix_ns(),
        counter
    ));
    std::fs::create_dir_all(&base).unwrap();
    base
}

/// Spawn the host binary with `MYCO_ANCHOR_SURFACE_DIR=<dir>`. Returns the
/// child process + the TCP port reported on its stdout. The caller must call
/// `child.kill()` + `child.wait()` to clean up.
fn spawn_host(dir: &Path, owner_seed_hex: Option<&str>) -> (Child, u16) {
    let bin = host_binary_path();
    let mut cmd = Command::new(&bin);
    cmd.env("MYCO_ANCHOR_SURFACE_DIR", dir);
    cmd.env("MYCO_ANCHOR_SURFACE_BIND_ADDR", "127.0.0.1:0");
    if let Some(seed_hex) = owner_seed_hex {
        cmd.env("MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX", seed_hex);
    }
    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = cmd.spawn().expect("spawn anchor-surface-host");
    let stdout = child.stdout.take().expect("piped stdout");
    let mut reader = BufReader::new(stdout);
    let mut line = String::new();
    reader.read_line(&mut line).expect("read stdout line");
    // Parse: "anchor-surface-host listening on 127.0.0.1:<PORT>"
    let port = line
        .trim()
        .rsplit(':')
        .next()
        .and_then(|s| s.parse::<u16>().ok())
        .unwrap_or_else(|| panic!("could not parse port from stdout line: {line:?}"));
    // Reattach reader (so child stays alive); the rest of stdout we ignore.
    drop(reader);
    (child, port)
}

fn connect(port: u16) -> TcpStream {
    let mut last_err: Option<std::io::Error> = None;
    for _ in 0..10 {
        match TcpStream::connect_timeout(
            &format!("127.0.0.1:{port}").parse().unwrap(),
            Duration::from_millis(500),
        ) {
            Ok(s) => return s,
            Err(e) => {
                last_err = Some(e);
                std::thread::sleep(Duration::from_millis(50));
            }
        }
    }
    panic!("failed to connect to 127.0.0.1:{port}: {:?}", last_err);
}

fn send_request(stream: &mut TcpStream, req: Request) -> Response {
    let bytes = req.encode().expect("encode request");
    write_frame(stream, &bytes).expect("write frame");
    let frame = read_frame(stream)
        .expect("read frame")
        .expect("got at least one frame, not EOF");
    Response::decode(&frame).expect("decode response")
}

#[test]
fn e2e_ping_get_pubkey_sign_verify() {
    let dir = fresh_dir();
    let (mut child, port) = spawn_host(&dir, None);
    let mut stream = connect(port);

    // 1. Ping liveness.
    let resp = send_request(&mut stream, Request::Ping);
    assert_eq!(resp, Response::Pong);

    // 2. Get the owner pubkey.
    let pubkey = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey response, got {other:?}"),
    };
    assert_ne!(pubkey, [0u8; 32], "pubkey not all zeros");

    // 3. Sign a message; verify against the reported pubkey.
    let message = b"hello m-anchor-1";
    let signature = match send_request(
        &mut stream,
        Request::Sign {
            message: message.to_vec(),
        },
    ) {
        Response::Signature { signature } => signature,
        other => panic!("expected Signature response, got {other:?}"),
    };
    verify_signature(&pubkey, &signature, message).expect("verify_signature");

    // 4. Tampered message rejected.
    let tampered = b"hello m-anchor-2";
    let err = verify_signature(&pubkey, &signature, tampered).unwrap_err();
    let _ = err;

    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn e2e_owner_key_file_persists_and_pubkey_stable_across_runs() {
    let dir = fresh_dir();

    // First boot: load_or_create generates a fresh key.
    let (mut child1, port1) = spawn_host(&dir, None);
    let pubkey1 = {
        let mut stream = connect(port1);
        match send_request(&mut stream, Request::GetPubkey) {
            Response::Pubkey { pubkey } => pubkey,
            other => panic!("expected Pubkey, got {other:?}"),
        }
    };
    let _ = child1.kill();
    let _ = child1.wait();

    // The owner key file must exist.
    assert!(
        dir.join(anchor_surface_host::OWNER_KEY_FILENAME).exists(),
        "owner_key.cb expected to be persisted"
    );

    // Second boot: load_or_create finds the persisted key.
    let (mut child2, port2) = spawn_host(&dir, None);
    let pubkey2 = {
        let mut stream = connect(port2);
        match send_request(&mut stream, Request::GetPubkey) {
            Response::Pubkey { pubkey } => pubkey,
            other => panic!("expected Pubkey, got {other:?}"),
        }
    };
    let _ = child2.kill();
    let _ = child2.wait();
    let _ = std::fs::remove_dir_all(&dir);

    assert_eq!(pubkey1, pubkey2, "pubkey stable across host restarts");
}

#[test]
fn e2e_owner_seed_hex_override_yields_deterministic_pubkey() {
    let dir = fresh_dir();
    // Owner seed all-0xab; pubkey is deterministic per RFC 8032.
    let seed_hex = "ab".repeat(32);
    let (mut child, port) = spawn_host(&dir, Some(&seed_hex));
    let mut stream = connect(port);
    let pubkey = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey, got {other:?}"),
    };
    let sig = match send_request(
        &mut stream,
        Request::Sign {
            message: b"determinism check".to_vec(),
        },
    ) {
        Response::Signature { signature } => signature,
        other => panic!("expected Signature, got {other:?}"),
    };
    verify_signature(&pubkey, &sig, b"determinism check").unwrap();
    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

// ---------------------------------------------------------------------------
// **M-anchor-2 + M-anchor-3** — anchor surface stage-1 RPCs.
//
// BirthAttest (§9.2.1): L0/cards/AS_anchor_surface §3 5-tuple signed by owner pubkey.
// GenerateAnchorNonce (§9.2.5): freshness marker with TTL.
// GetAnchorWallClock (§9.2.6): authoritative time for time-bound defenses.
// Heartbeat (§9.2.7): owner liveness proof for successor activation gate.
// ---------------------------------------------------------------------------

#[test]
fn m_anchor_2_birth_attest_signature_verifies_against_owner_pubkey() {
    use anchor_surface_host::protocol::birth_attestation_canonical_bytes;

    let dir = fresh_dir();
    let seed_hex = "cd".repeat(32);
    let (mut child, port) = spawn_host(&dir, Some(&seed_hex));
    let mut stream = connect(port);

    let substrate_id = [0x11u8; 32];
    let genesis_ts: i64 = 1_700_000_000_000_000_000;
    let spore_hash = [0x22u8; 32];
    // Anchor endpoint pubkey: per L0/cards/AS_anchor_surface §5 collapsed to owner pubkey in v0.9.
    let owner_pk = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey, got {other:?}"),
    };
    let anchor_endpoint_pk = owner_pk;

    let resp = send_request(
        &mut stream,
        Request::BirthAttest {
            substrate_id,
            genesis_timestamp_unix_ns: genesis_ts,
            spore_schema_hash: spore_hash,
            anchor_endpoint_pubkey: anchor_endpoint_pk,
        },
    );
    let (sig, owner_pubkey_returned, attested_bytes) = match resp {
        Response::BirthAttestation {
            signature,
            owner_pubkey,
            attested_canonical_bytes,
        } => (signature, owner_pubkey, attested_canonical_bytes),
        other => panic!("expected BirthAttestation, got {other:?}"),
    };
    // Returned owner pubkey must match the one we queried separately.
    assert_eq!(owner_pubkey_returned, owner_pk);
    // Signature verifies against the returned canonical-bytes.
    verify_signature(&owner_pubkey_returned, &sig, &attested_bytes)
        .expect("birth attestation signature must verify");
    // Independent reconstruction must produce byte-identical attested bytes.
    let reconstructed = birth_attestation_canonical_bytes(
        &substrate_id,
        genesis_ts,
        &spore_hash,
        &owner_pk,
        &anchor_endpoint_pk,
    );
    assert_eq!(
        attested_bytes, reconstructed,
        "attested_canonical_bytes must match independent reconstruction (determinism)"
    );
    // Tampered 5-tuple field must invalidate the signature.
    let mut wrong_substrate_id = substrate_id;
    wrong_substrate_id[0] ^= 0xff;
    let wrong_bytes = birth_attestation_canonical_bytes(
        &wrong_substrate_id,
        genesis_ts,
        &spore_hash,
        &owner_pk,
        &anchor_endpoint_pk,
    );
    assert!(
        verify_signature(&owner_pubkey_returned, &sig, &wrong_bytes).is_err(),
        "tampered substrate_id must invalidate signature"
    );

    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn m_anchor_3_generate_anchor_nonce_signature_verifies_and_has_distinct_nonces() {
    use anchor_surface_host::protocol::anchor_nonce_canonical_bytes;

    let dir = fresh_dir();
    let seed_hex = "ef".repeat(32);
    let (mut child, port) = spawn_host(&dir, Some(&seed_hex));
    let mut stream = connect(port);

    let owner_pk = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey, got {other:?}"),
    };

    let mk_nonce = |s: &mut TcpStream| match send_request(
        s,
        Request::GenerateAnchorNonce { ttl_seconds: 60 },
    ) {
        Response::AnchorNonce {
            nonce,
            anchor_timestamp_unix_ns,
            expiry_unix_ns,
            signature,
        } => (nonce, anchor_timestamp_unix_ns, expiry_unix_ns, signature),
        other => panic!("expected AnchorNonce, got {other:?}"),
    };

    let (n1, t1, e1, s1) = mk_nonce(&mut stream);
    let (n2, t2, e2, s2) = mk_nonce(&mut stream);

    // 1. Both signatures verify against the owner pubkey + canonical bytes.
    let bytes1 = anchor_nonce_canonical_bytes(&n1, t1, e1);
    let bytes2 = anchor_nonce_canonical_bytes(&n2, t2, e2);
    verify_signature(&owner_pk, &s1, &bytes1).expect("anchor nonce #1 sig must verify");
    verify_signature(&owner_pk, &s2, &bytes2).expect("anchor nonce #2 sig must verify");

    // 2. Two successive calls produce distinct nonces.
    assert_ne!(n1, n2, "successive anchor nonces must differ");

    // 3. Expiry = issued_at + ttl_seconds * 1e9.
    assert_eq!(e1 - t1, 60_000_000_000_i64);

    // 4. ttl_seconds clamps to [1, 3600].
    let resp = send_request(&mut stream, Request::GenerateAnchorNonce { ttl_seconds: 0 });
    let (_n, t_zero, e_zero, _s) = match resp {
        Response::AnchorNonce {
            nonce,
            anchor_timestamp_unix_ns,
            expiry_unix_ns,
            signature,
        } => (nonce, anchor_timestamp_unix_ns, expiry_unix_ns, signature),
        other => panic!("expected AnchorNonce, got {other:?}"),
    };
    assert_eq!(
        e_zero - t_zero,
        1_000_000_000_i64,
        "ttl_seconds=0 must clamp up to 1"
    );

    let resp = send_request(
        &mut stream,
        Request::GenerateAnchorNonce {
            ttl_seconds: 999_999,
        },
    );
    let (_n, t_big, e_big, _s) = match resp {
        Response::AnchorNonce {
            nonce,
            anchor_timestamp_unix_ns,
            expiry_unix_ns,
            signature,
        } => (nonce, anchor_timestamp_unix_ns, expiry_unix_ns, signature),
        other => panic!("expected AnchorNonce, got {other:?}"),
    };
    assert_eq!(
        e_big - t_big,
        3600_000_000_000_i64,
        "ttl_seconds=999_999 must clamp down to 3600"
    );

    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn m_anchor_3_get_anchor_wall_clock_signature_verifies_and_advances() {
    use anchor_surface_host::protocol::anchor_wallclock_canonical_bytes;

    let dir = fresh_dir();
    let seed_hex = "33".repeat(32);
    let (mut child, port) = spawn_host(&dir, Some(&seed_hex));
    let mut stream = connect(port);

    let owner_pk = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey, got {other:?}"),
    };

    let read_clock = |s: &mut TcpStream| match send_request(s, Request::GetAnchorWallClock) {
        Response::AnchorWallClock {
            anchor_timestamp_unix_ns,
            signature,
        } => (anchor_timestamp_unix_ns, signature),
        other => panic!("expected AnchorWallClock, got {other:?}"),
    };

    let (t1, s1) = read_clock(&mut stream);
    // Wait a tiny bit to guarantee t2 > t1 even on very fast systems.
    std::thread::sleep(Duration::from_millis(2));
    let (t2, s2) = read_clock(&mut stream);

    // 1. Both signatures verify.
    let bytes1 = anchor_wallclock_canonical_bytes(t1);
    let bytes2 = anchor_wallclock_canonical_bytes(t2);
    verify_signature(&owner_pk, &s1, &bytes1).expect("wall clock #1 sig verify");
    verify_signature(&owner_pk, &s2, &bytes2).expect("wall clock #2 sig verify");

    // 2. Monotone forward (t2 > t1).
    assert!(t2 > t1, "anchor wall clock must advance: got t1={t1}, t2={t2}");

    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn m_anchor_3_heartbeat_signature_verifies_and_nonces_are_distinct() {
    use anchor_surface_host::protocol::anchor_heartbeat_canonical_bytes;

    let dir = fresh_dir();
    let seed_hex = "44".repeat(32);
    let (mut child, port) = spawn_host(&dir, Some(&seed_hex));
    let mut stream = connect(port);

    let owner_pk = match send_request(&mut stream, Request::GetPubkey) {
        Response::Pubkey { pubkey } => pubkey,
        other => panic!("expected Pubkey, got {other:?}"),
    };

    let heartbeat = |s: &mut TcpStream| match send_request(s, Request::Heartbeat) {
        Response::HeartbeatResponse {
            anchor_timestamp_unix_ns,
            heartbeat_nonce,
            signature,
        } => (anchor_timestamp_unix_ns, heartbeat_nonce, signature),
        other => panic!("expected HeartbeatResponse, got {other:?}"),
    };

    let (t1, n1, s1) = heartbeat(&mut stream);
    let (t2, n2, s2) = heartbeat(&mut stream);

    // 1. Both signatures verify.
    let bytes1 = anchor_heartbeat_canonical_bytes(t1, &n1);
    let bytes2 = anchor_heartbeat_canonical_bytes(t2, &n2);
    verify_signature(&owner_pk, &s1, &bytes1).expect("heartbeat #1 sig verify");
    verify_signature(&owner_pk, &s2, &bytes2).expect("heartbeat #2 sig verify");

    // 2. Nonces distinct (freshness guarantee).
    assert_ne!(n1, n2, "heartbeat nonces must differ across calls");

    drop(stream);
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn e2e_port_discovery_file_written() {
    let dir = fresh_dir();
    let (mut child, port) = spawn_host(&dir, None);
    // Give the host a moment to write port.txt (it does so before printing
    // the stdout line, but flushing order is OS-dependent).
    let port_file = dir.join(anchor_surface_host::PORT_DISCOVERY_FILENAME);
    let mut found_port: Option<u16> = None;
    for _ in 0..20 {
        if port_file.exists() {
            let raw = std::fs::read_to_string(&port_file).unwrap();
            found_port = raw.trim().parse::<u16>().ok();
            if found_port.is_some() {
                break;
            }
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    let found = found_port.expect("port.txt should be written");
    assert_eq!(found, port, "port.txt contents match listener port");
    let _ = child.kill();
    let _ = child.wait();
    let _ = std::fs::remove_dir_all(&dir);
}
