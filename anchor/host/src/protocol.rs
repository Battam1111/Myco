//! Anchor surface host wire protocol — canonical-bytes envelopes over local TCP.
//!
//! ## Wire format
//!
//! Each on-the-wire frame is:
//!
//! ```text
//!  [u32 BE length, 4 bytes][canonical-bytes Map envelope, length bytes]
//! ```
//!
//! No HMAC at M-anchor-1 (localhost-only binding + 0600 port-discovery file
//! is the interim defense). M-anchor-1.5 adds a per-session HMAC key written
//! into the discovery file.
//!
//! ## Envelope shape
//!
//! Every message is a canonical-bytes Map with a `type` string key
//! discriminating between request types:
//!
//! ```text
//! GetPubkeyRequest:  Map({"type": "get_pubkey"})
//! GetPubkeyResponse: Map({"pubkey": Bytes(32)})
//!
//! SignRequest:       Map({"type": "sign", "message": Bytes(N)})
//! SignResponse:      Map({"signature": Bytes(64)})
//!
//! PingRequest:       Map({"type": "ping"})
//! PingResponse:      Map({"ok": Bool(true)})
//!
//! ErrorResponse:     Map({"error": String(message)})
//! ```
//!
//! Responses carry only the response-shaped keys (no `type` discriminator) so
//! that decoding logic on the operator side maps cleanly to each request type.

use std::collections::BTreeMap;
use std::io::{ErrorKind, Read, Write};
use std::net::TcpStream;

use myco_kernel_shared::canonical_bytes::{
    decode, encode, map_get_bool, map_get_bytes, map_get_string, map_get_uint, Value,
};

use crate::HostError;

/// Domain string prefixed to anchor wall-clock signatures (M-anchor-3 §9.2.6).
/// Different domains for different signed-payload categories prevent
/// cross-protocol signature confusion attacks.
pub const ANCHOR_WALLCLOCK_DOMAIN: &str = "myco-anchor-wallclock-v1";

/// Domain string prefixed to anchor heartbeat signatures (M-anchor-3 §9.2.7).
pub const ANCHOR_HEARTBEAT_DOMAIN: &str = "myco-anchor-heartbeat-v1";

/// Domain string prefixed to anchor nonce signatures (M-anchor-3 §9.2.5).
pub const ANCHOR_NONCE_DOMAIN: &str = "myco-anchor-nonce-v1";

/// Domain string prefixed to birth attestation signatures (M-anchor-2 §9.2.1).
/// Per L0/cards/AS_anchor_surface §3: 5-tuple = (substrate-ID, genesis-timestamp,
/// initial-spore-schema-canonical-bytes-hash, owner-public-key,
/// anchor-surface-endpoint-public-key).
pub const BIRTH_ATTESTATION_DOMAIN: &str = "myco-birth-attestation-v1";

/// Build the canonical-bytes Map that gets signed for a birth attestation
/// (L0/cards/AS_anchor_surface §3 5-tuple). Exposed so substrate-side verification can rebuild
/// the exact bytes and re-verify the signature offline.
pub fn birth_attestation_canonical_bytes(
    substrate_id: &[u8; 32],
    genesis_timestamp_unix_ns: i64,
    spore_schema_hash: &[u8; 32],
    owner_pubkey: &[u8; 32],
    anchor_endpoint_pubkey: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(BIRTH_ATTESTATION_DOMAIN.to_string()),
    );
    m.insert(
        "substrate_id".to_string(),
        Value::Bytes(substrate_id.to_vec()),
    );
    m.insert(
        "genesis_timestamp_unix_ns".to_string(),
        Value::Timestamp(genesis_timestamp_unix_ns),
    );
    m.insert(
        "spore_schema_hash".to_string(),
        Value::Bytes(spore_schema_hash.to_vec()),
    );
    m.insert(
        "owner_pubkey".to_string(),
        Value::Bytes(owner_pubkey.to_vec()),
    );
    m.insert(
        "anchor_endpoint_pubkey".to_string(),
        Value::Bytes(anchor_endpoint_pubkey.to_vec()),
    );
    encode(&Value::Map(m))
        .expect("birth attestation canonical-bytes encode infallible")
        .0
}

/// Build the canonical-bytes that get signed for an anchor wall-clock
/// reading (M-anchor-3 §9.2.6).
pub fn anchor_wallclock_canonical_bytes(anchor_timestamp_unix_ns: i64) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(ANCHOR_WALLCLOCK_DOMAIN.to_string()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    encode(&Value::Map(m))
        .expect("anchor wallclock canonical-bytes encode infallible")
        .0
}

/// Build the canonical-bytes signed for an anchor-generated nonce
/// (M-anchor-3 §9.2.5).
pub fn anchor_nonce_canonical_bytes(
    nonce: &[u8; 32],
    issued_at_unix_ns: i64,
    expiry_unix_ns: i64,
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(ANCHOR_NONCE_DOMAIN.to_string()),
    );
    m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    m.insert(
        "issued_at_unix_ns".to_string(),
        Value::Timestamp(issued_at_unix_ns),
    );
    m.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    encode(&Value::Map(m))
        .expect("anchor nonce canonical-bytes encode infallible")
        .0
}

/// Build the canonical-bytes signed for an anchor heartbeat (M-anchor-3 §9.2.7).
pub fn anchor_heartbeat_canonical_bytes(
    anchor_timestamp_unix_ns: i64,
    heartbeat_nonce: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "domain".to_string(),
        Value::String(ANCHOR_HEARTBEAT_DOMAIN.to_string()),
    );
    m.insert(
        "anchor_timestamp_unix_ns".to_string(),
        Value::Timestamp(anchor_timestamp_unix_ns),
    );
    m.insert(
        "heartbeat_nonce".to_string(),
        Value::Bytes(heartbeat_nonce.to_vec()),
    );
    encode(&Value::Map(m))
        .expect("anchor heartbeat canonical-bytes encode infallible")
        .0
}

/// Maximum frame body size on the wire (1 MiB). DoS protection consistent
/// with `myco_kernel_bridge::protocol::MAX_FRAME_BODY_SIZE`.
pub const MAX_FRAME_BODY_SIZE: usize = 1024 * 1024;

/// Request types accepted by the anchor surface host.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Request {
    /// Return the 32-byte owner public key.
    GetPubkey,
    /// Sign the supplied message bytes; return the 64-byte Ed25519 signature.
    Sign {
        /// Bytes to sign with the owner's Ed25519 private key.
        message: Vec<u8>,
    },
    /// Liveness check; expect `PingResponse { ok: true }`.
    Ping,
    /// **M-anchor-2 §9.2.1**: birth-attest a fresh substrate. Returns the
    /// owner's Ed25519 signature over the canonical-bytes Map of the
    /// L0/cards/AS_anchor_surface §3 5-tuple. The substrate stores this signature in its DAG as
    /// a `birth_attestation:{substrate_id_prefix}` event; every boot
    /// re-verifies the signature against the current owner pubkey.
    BirthAttest {
        /// Fresh substrate identifier (32-byte hash; substrate-side construction
        /// per L1/GOVERNANCE §4.1).
        substrate_id: [u8; 32],
        /// Substrate's genesis wall-clock (substrate-process clock at this
        /// stage of M-anchor-2; replaceable with anchor-stamped time once
        /// M-anchor-3 is in production use).
        genesis_timestamp_unix_ns: i64,
        /// 32-byte hash of the initial spore-schema canonical bytes (F-row
        /// content; substrate-side computation per L1/SCHEMA §3.1).
        spore_schema_hash: [u8; 32],
        /// 32-byte anchor-endpoint pubkey. In v0.9 anchor collapsed to
        /// operator process (L0/cards/AS_anchor_surface §5), so this equals the owner pubkey;
        /// future M-anchor-1.5 may decouple them.
        anchor_endpoint_pubkey: [u8; 32],
    },
    /// **M-anchor-3 §9.2.5**: generate a fresh anchor-side nonce + sign it
    /// with issuance + expiry timestamps. Substrate carries the nonce in
    /// mutation envelopes to prove freshness against anchor wall-clock.
    GenerateAnchorNonce {
        /// Time-to-live in seconds. Anchor adds `ttl_seconds * 1e9` to its
        /// current wall-clock to compute `expiry_unix_ns`. Clamped to
        /// `[1, 3600]` (1s to 1h) to bound abuse.
        ttl_seconds: u64,
    },
    /// **M-anchor-3 §9.2.6**: read the anchor's current wall-clock. Result
    /// is signed; substrate can pin time-bound checks against this
    /// authoritative timestamp (per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics) "anchor wall-clock authoritative
    /// for time-bound defenses").
    GetAnchorWallClock,
    /// **M-anchor-3 §9.2.7**: owner liveness heartbeat. Returns a freshly-
    /// generated nonce + current timestamp + signature. Used by successor-
    /// activation gating (L1/GOVERNANCE §3.2): if the most recent heartbeat
    /// is stale beyond a threshold, successor key can activate without the
    /// current Cultivator's signature.
    Heartbeat,
}

impl Request {
    /// Encode this request as canonical bytes.
    pub fn encode(&self) -> Result<Vec<u8>, HostError> {
        let mut m = BTreeMap::new();
        match self {
            Request::GetPubkey => {
                m.insert("type".to_string(), Value::String("get_pubkey".to_string()));
            }
            Request::Sign { message } => {
                m.insert("type".to_string(), Value::String("sign".to_string()));
                m.insert("message".to_string(), Value::Bytes(message.clone()));
            }
            Request::Ping => {
                m.insert("type".to_string(), Value::String("ping".to_string()));
            }
            Request::BirthAttest {
                substrate_id,
                genesis_timestamp_unix_ns,
                spore_schema_hash,
                anchor_endpoint_pubkey,
            } => {
                m.insert(
                    "type".to_string(),
                    Value::String("birth_attest".to_string()),
                );
                m.insert(
                    "substrate_id".to_string(),
                    Value::Bytes(substrate_id.to_vec()),
                );
                m.insert(
                    "genesis_timestamp_unix_ns".to_string(),
                    Value::Timestamp(*genesis_timestamp_unix_ns),
                );
                m.insert(
                    "spore_schema_hash".to_string(),
                    Value::Bytes(spore_schema_hash.to_vec()),
                );
                m.insert(
                    "anchor_endpoint_pubkey".to_string(),
                    Value::Bytes(anchor_endpoint_pubkey.to_vec()),
                );
            }
            Request::GenerateAnchorNonce { ttl_seconds } => {
                m.insert(
                    "type".to_string(),
                    Value::String("generate_anchor_nonce".to_string()),
                );
                m.insert("ttl_seconds".to_string(), Value::Uint(*ttl_seconds));
            }
            Request::GetAnchorWallClock => {
                m.insert(
                    "type".to_string(),
                    Value::String("get_anchor_wall_clock".to_string()),
                );
            }
            Request::Heartbeat => {
                m.insert("type".to_string(), Value::String("heartbeat".to_string()));
            }
        }
        Ok(encode(&Value::Map(m))?.0)
    }

    /// Decode a request from canonical bytes.
    pub fn decode(bytes: &[u8]) -> Result<Self, HostError> {
        let decoded = decode(bytes)?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(HostError::Protocol(format!(
                    "request root is not a Map: {other:?}"
                )))
            }
        };
        let type_str = map_get_string(&map, "type")?;
        match type_str {
            "get_pubkey" => Ok(Request::GetPubkey),
            "sign" => {
                let msg = map_get_bytes(&map, "message")?.to_vec();
                Ok(Request::Sign { message: msg })
            }
            "ping" => Ok(Request::Ping),
            "birth_attest" => {
                let substrate_id = bytes_to_arr32(map_get_bytes(&map, "substrate_id")?, "substrate_id")?;
                let genesis_ts = match map.get("genesis_timestamp_unix_ns") {
                    Some(Value::Timestamp(t)) => *t,
                    _ => {
                        return Err(HostError::Protocol(
                            "birth_attest: genesis_timestamp_unix_ns missing or wrong type"
                                .to_string(),
                        ))
                    }
                };
                let spore_schema_hash =
                    bytes_to_arr32(map_get_bytes(&map, "spore_schema_hash")?, "spore_schema_hash")?;
                let anchor_endpoint_pubkey = bytes_to_arr32(
                    map_get_bytes(&map, "anchor_endpoint_pubkey")?,
                    "anchor_endpoint_pubkey",
                )?;
                Ok(Request::BirthAttest {
                    substrate_id,
                    genesis_timestamp_unix_ns: genesis_ts,
                    spore_schema_hash,
                    anchor_endpoint_pubkey,
                })
            }
            "generate_anchor_nonce" => {
                let ttl = map_get_uint(&map, "ttl_seconds")?;
                Ok(Request::GenerateAnchorNonce { ttl_seconds: ttl })
            }
            "get_anchor_wall_clock" => Ok(Request::GetAnchorWallClock),
            "heartbeat" => Ok(Request::Heartbeat),
            other => Err(HostError::Protocol(format!(
                "unknown request type {other}"
            ))),
        }
    }
}

fn bytes_to_arr32(bytes: &[u8], field: &str) -> Result<[u8; 32], HostError> {
    if bytes.len() != 32 {
        return Err(HostError::Protocol(format!(
            "{field}: expected 32 bytes, got {}",
            bytes.len()
        )));
    }
    let mut out = [0u8; 32];
    out.copy_from_slice(bytes);
    Ok(out)
}

/// Response types emitted by the anchor surface host.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Response {
    /// 32-byte Ed25519 public key.
    Pubkey {
        /// The owner's 32-byte Ed25519 public key bytes.
        pubkey: [u8; 32],
    },
    /// 64-byte Ed25519 signature.
    Signature {
        /// The 64-byte Ed25519 signature over the requested message.
        signature: [u8; 64],
    },
    /// Ping reply.
    Pong,
    /// Error reply (substituted for any of the above when the host failed
    /// to process the request).
    Error {
        /// Human-readable error description.
        message: String,
    },
    /// **M-anchor-2 §9.2.1** birth attestation response. The 5-tuple
    /// canonical bytes that were signed are returned alongside the signature
    /// + owner pubkey so the substrate can store ALL THREE in its DAG and
    /// re-verify offline on every boot.
    BirthAttestation {
        /// Ed25519 signature over `attested_canonical_bytes`.
        signature: [u8; 64],
        /// Owner public key used to sign (also the key the substrate verifies
        /// against on subsequent boots).
        owner_pubkey: [u8; 32],
        /// The exact canonical-bytes that were signed. Substrate emits this
        /// as the content of the `birth_attestation` DAG event; future
        /// verification recomputes against these bytes.
        attested_canonical_bytes: Vec<u8>,
    },
    /// **M-anchor-3 §9.2.5** anchor-generated nonce. Substrate stores the
    /// nonce + expiry + signature; when including in a mutation envelope,
    /// substrate can verify `current_anchor_time < expiry`.
    AnchorNonce {
        /// 32-byte random nonce.
        nonce: [u8; 32],
        /// Anchor-side issuance timestamp (ns).
        anchor_timestamp_unix_ns: i64,
        /// Anchor-side expiry timestamp (ns).
        expiry_unix_ns: i64,
        /// Ed25519 signature over the canonical-bytes of the nonce-tuple.
        signature: [u8; 64],
    },
    /// **M-anchor-3 §9.2.6** anchor wall-clock response. Used by substrate
    /// for time-bound defenses per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics).
    AnchorWallClock {
        /// Anchor-side wall-clock at response time (ns).
        anchor_timestamp_unix_ns: i64,
        /// Ed25519 signature over the canonical-bytes of the timestamp.
        signature: [u8; 64],
    },
    /// **M-anchor-3 §9.2.7** owner liveness heartbeat. Substrate persists
    /// the most recent heartbeat; successor activation gate checks staleness.
    HeartbeatResponse {
        /// Anchor-side timestamp at heartbeat issuance (ns).
        anchor_timestamp_unix_ns: i64,
        /// 32-byte random nonce that uniquely identifies this heartbeat call.
        heartbeat_nonce: [u8; 32],
        /// Ed25519 signature over the heartbeat canonical-bytes.
        signature: [u8; 64],
    },
}

impl Response {
    /// Encode this response as canonical bytes.
    pub fn encode(&self) -> Result<Vec<u8>, HostError> {
        let mut m = BTreeMap::new();
        match self {
            Response::Pubkey { pubkey } => {
                m.insert("pubkey".to_string(), Value::Bytes(pubkey.to_vec()));
            }
            Response::Signature { signature } => {
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
            }
            Response::Pong => {
                m.insert("ok".to_string(), Value::Bool(true));
            }
            Response::Error { message } => {
                m.insert("error".to_string(), Value::String(message.clone()));
            }
            Response::BirthAttestation {
                signature,
                owner_pubkey,
                attested_canonical_bytes,
            } => {
                // Use a discriminator field to distinguish from plain Signature
                // (both carry `signature`). `birth_attestation` discriminator.
                m.insert(
                    "kind".to_string(),
                    Value::String("birth_attestation".to_string()),
                );
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
                m.insert(
                    "owner_pubkey".to_string(),
                    Value::Bytes(owner_pubkey.to_vec()),
                );
                m.insert(
                    "attested_canonical_bytes".to_string(),
                    Value::Bytes(attested_canonical_bytes.clone()),
                );
            }
            Response::AnchorNonce {
                nonce,
                anchor_timestamp_unix_ns,
                expiry_unix_ns,
                signature,
            } => {
                m.insert(
                    "kind".to_string(),
                    Value::String("anchor_nonce".to_string()),
                );
                m.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
                m.insert(
                    "anchor_timestamp_unix_ns".to_string(),
                    Value::Timestamp(*anchor_timestamp_unix_ns),
                );
                m.insert(
                    "expiry_unix_ns".to_string(),
                    Value::Timestamp(*expiry_unix_ns),
                );
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
            }
            Response::AnchorWallClock {
                anchor_timestamp_unix_ns,
                signature,
            } => {
                m.insert(
                    "kind".to_string(),
                    Value::String("anchor_wall_clock".to_string()),
                );
                m.insert(
                    "anchor_timestamp_unix_ns".to_string(),
                    Value::Timestamp(*anchor_timestamp_unix_ns),
                );
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
            }
            Response::HeartbeatResponse {
                anchor_timestamp_unix_ns,
                heartbeat_nonce,
                signature,
            } => {
                m.insert(
                    "kind".to_string(),
                    Value::String("heartbeat".to_string()),
                );
                m.insert(
                    "anchor_timestamp_unix_ns".to_string(),
                    Value::Timestamp(*anchor_timestamp_unix_ns),
                );
                m.insert(
                    "heartbeat_nonce".to_string(),
                    Value::Bytes(heartbeat_nonce.to_vec()),
                );
                m.insert("signature".to_string(), Value::Bytes(signature.to_vec()));
            }
        }
        Ok(encode(&Value::Map(m))?.0)
    }

    /// Decode a response from canonical bytes. M-anchor-2 introduces a
    /// `kind` discriminator on the new response shapes (BirthAttestation,
    /// AnchorNonce, AnchorWallClock, Heartbeat) since multiple share the
    /// `signature` field. Old responses (Pubkey/Signature/Pong/Error) are
    /// detected by their unique keys.
    pub fn decode(bytes: &[u8]) -> Result<Self, HostError> {
        let decoded = decode(bytes)?;
        let map = match decoded {
            Value::Map(m) => m,
            other => {
                return Err(HostError::Protocol(format!(
                    "response root is not a Map: {other:?}"
                )))
            }
        };
        if let Ok(err) = map_get_string(&map, "error") {
            return Ok(Response::Error {
                message: err.to_string(),
            });
        }
        // M-anchor-2+3: discriminator-tagged responses.
        if let Ok(kind) = map_get_string(&map, "kind") {
            return match kind {
                "birth_attestation" => {
                    let sig_bytes = map_get_bytes(&map, "signature")?;
                    if sig_bytes.len() != 64 {
                        return Err(HostError::Protocol(format!(
                            "birth_attestation signature length {} != 64",
                            sig_bytes.len()
                        )));
                    }
                    let mut signature = [0u8; 64];
                    signature.copy_from_slice(sig_bytes);
                    let owner_pk_bytes = map_get_bytes(&map, "owner_pubkey")?;
                    if owner_pk_bytes.len() != 32 {
                        return Err(HostError::Protocol(format!(
                            "birth_attestation owner_pubkey length {} != 32",
                            owner_pk_bytes.len()
                        )));
                    }
                    let mut owner_pubkey = [0u8; 32];
                    owner_pubkey.copy_from_slice(owner_pk_bytes);
                    let attested_canonical_bytes =
                        map_get_bytes(&map, "attested_canonical_bytes")?.to_vec();
                    Ok(Response::BirthAttestation {
                        signature,
                        owner_pubkey,
                        attested_canonical_bytes,
                    })
                }
                "anchor_nonce" => {
                    let nonce_bytes = map_get_bytes(&map, "nonce")?;
                    if nonce_bytes.len() != 32 {
                        return Err(HostError::Protocol(format!(
                            "anchor_nonce nonce length {} != 32",
                            nonce_bytes.len()
                        )));
                    }
                    let mut nonce = [0u8; 32];
                    nonce.copy_from_slice(nonce_bytes);
                    let anchor_timestamp_unix_ns = match map.get("anchor_timestamp_unix_ns") {
                        Some(Value::Timestamp(t)) => *t,
                        _ => {
                            return Err(HostError::Protocol(
                                "anchor_nonce: anchor_timestamp_unix_ns missing or wrong type"
                                    .to_string(),
                            ))
                        }
                    };
                    let expiry_unix_ns = match map.get("expiry_unix_ns") {
                        Some(Value::Timestamp(t)) => *t,
                        _ => {
                            return Err(HostError::Protocol(
                                "anchor_nonce: expiry_unix_ns missing or wrong type".to_string(),
                            ))
                        }
                    };
                    let sig_bytes = map_get_bytes(&map, "signature")?;
                    if sig_bytes.len() != 64 {
                        return Err(HostError::Protocol(format!(
                            "anchor_nonce signature length {} != 64",
                            sig_bytes.len()
                        )));
                    }
                    let mut signature = [0u8; 64];
                    signature.copy_from_slice(sig_bytes);
                    Ok(Response::AnchorNonce {
                        nonce,
                        anchor_timestamp_unix_ns,
                        expiry_unix_ns,
                        signature,
                    })
                }
                "anchor_wall_clock" => {
                    let anchor_timestamp_unix_ns = match map.get("anchor_timestamp_unix_ns") {
                        Some(Value::Timestamp(t)) => *t,
                        _ => {
                            return Err(HostError::Protocol(
                                "anchor_wall_clock: anchor_timestamp_unix_ns missing or wrong type"
                                    .to_string(),
                            ))
                        }
                    };
                    let sig_bytes = map_get_bytes(&map, "signature")?;
                    if sig_bytes.len() != 64 {
                        return Err(HostError::Protocol(format!(
                            "anchor_wall_clock signature length {} != 64",
                            sig_bytes.len()
                        )));
                    }
                    let mut signature = [0u8; 64];
                    signature.copy_from_slice(sig_bytes);
                    Ok(Response::AnchorWallClock {
                        anchor_timestamp_unix_ns,
                        signature,
                    })
                }
                "heartbeat" => {
                    let anchor_timestamp_unix_ns = match map.get("anchor_timestamp_unix_ns") {
                        Some(Value::Timestamp(t)) => *t,
                        _ => {
                            return Err(HostError::Protocol(
                                "heartbeat: anchor_timestamp_unix_ns missing or wrong type"
                                    .to_string(),
                            ))
                        }
                    };
                    let nonce_bytes = map_get_bytes(&map, "heartbeat_nonce")?;
                    if nonce_bytes.len() != 32 {
                        return Err(HostError::Protocol(format!(
                            "heartbeat nonce length {} != 32",
                            nonce_bytes.len()
                        )));
                    }
                    let mut heartbeat_nonce = [0u8; 32];
                    heartbeat_nonce.copy_from_slice(nonce_bytes);
                    let sig_bytes = map_get_bytes(&map, "signature")?;
                    if sig_bytes.len() != 64 {
                        return Err(HostError::Protocol(format!(
                            "heartbeat signature length {} != 64",
                            sig_bytes.len()
                        )));
                    }
                    let mut signature = [0u8; 64];
                    signature.copy_from_slice(sig_bytes);
                    Ok(Response::HeartbeatResponse {
                        anchor_timestamp_unix_ns,
                        heartbeat_nonce,
                        signature,
                    })
                }
                other => Err(HostError::Protocol(format!(
                    "unknown response kind {other}"
                ))),
            };
        }
        // Legacy (M-anchor-1) responses: dispatch by unique key presence.
        if let Ok(pk) = map_get_bytes(&map, "pubkey") {
            if pk.len() != 32 {
                return Err(HostError::Protocol(format!(
                    "pubkey length {} != 32",
                    pk.len()
                )));
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(pk);
            return Ok(Response::Pubkey { pubkey: arr });
        }
        if let Ok(sig) = map_get_bytes(&map, "signature") {
            if sig.len() != 64 {
                return Err(HostError::Protocol(format!(
                    "signature length {} != 64",
                    sig.len()
                )));
            }
            let mut arr = [0u8; 64];
            arr.copy_from_slice(sig);
            return Ok(Response::Signature { signature: arr });
        }
        if let Ok(true) = map_get_bool(&map, "ok") {
            return Ok(Response::Pong);
        }
        Err(HostError::Protocol(
            "response Map missing recognized key (kind/pubkey/signature/ok/error)".to_string(),
        ))
    }
}

// ---------------------------------------------------------------------------
// Frame I/O — length-prefixed canonical-bytes envelopes over TCP.
// ---------------------------------------------------------------------------

/// Read exactly `n` bytes from `stream`. Returns `Ok(None)` on clean EOF;
/// `Err` on mid-read EOF / I/O error.
fn read_exact_or_eof(stream: &mut TcpStream, n: usize) -> Result<Option<Vec<u8>>, HostError> {
    if n == 0 {
        return Ok(Some(Vec::new()));
    }
    let mut buf = vec![0u8; n];
    let mut read = 0;
    while read < n {
        match stream.read(&mut buf[read..]) {
            Ok(0) => {
                if read == 0 {
                    return Ok(None);
                }
                return Err(HostError::Protocol(format!(
                    "truncated read: got {} of {} bytes before EOF",
                    read, n
                )));
            }
            Ok(got) => {
                read += got;
            }
            Err(e) if e.kind() == ErrorKind::Interrupted => continue,
            Err(e) => return Err(HostError::Io(e)),
        }
    }
    Ok(Some(buf))
}

/// Read one length-prefixed frame from `stream`. Returns:
///
/// - `Ok(Some(body))` — frame body (canonical-bytes envelope) without length prefix.
/// - `Ok(None)` — clean EOF between frames.
/// - `Err` — mid-frame EOF, oversized frame, or I/O error.
pub fn read_frame(stream: &mut TcpStream) -> Result<Option<Vec<u8>>, HostError> {
    let length_bytes = match read_exact_or_eof(stream, 4)? {
        Some(b) => b,
        None => return Ok(None),
    };
    let length = u32::from_be_bytes([
        length_bytes[0],
        length_bytes[1],
        length_bytes[2],
        length_bytes[3],
    ]) as usize;
    if length > MAX_FRAME_BODY_SIZE {
        return Err(HostError::Protocol(format!(
            "incoming frame size {} exceeds cap {}",
            length, MAX_FRAME_BODY_SIZE
        )));
    }
    match read_exact_or_eof(stream, length)? {
        Some(b) => Ok(Some(b)),
        None => Err(HostError::Protocol(
            "EOF after length prefix; no body bytes".to_string(),
        )),
    }
}

/// Write one length-prefixed frame to `stream` and flush.
pub fn write_frame(stream: &mut TcpStream, frame_body: &[u8]) -> Result<(), HostError> {
    if frame_body.len() > MAX_FRAME_BODY_SIZE {
        return Err(HostError::Protocol(format!(
            "outgoing frame size {} exceeds cap {}",
            frame_body.len(),
            MAX_FRAME_BODY_SIZE
        )));
    }
    let length = frame_body.len() as u32;
    stream.write_all(&length.to_be_bytes())?;
    stream.write_all(frame_body)?;
    stream.flush()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_get_pubkey_roundtrip() {
        let req = Request::GetPubkey;
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn request_sign_roundtrip() {
        let req = Request::Sign {
            message: vec![1, 2, 3, 4, 5],
        };
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn request_ping_roundtrip() {
        let req = Request::Ping;
        let bytes = req.encode().unwrap();
        let decoded = Request::decode(&bytes).unwrap();
        assert_eq!(decoded, req);
    }

    #[test]
    fn response_pubkey_roundtrip() {
        let resp = Response::Pubkey { pubkey: [0xaa; 32] };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_signature_roundtrip() {
        let resp = Response::Signature {
            signature: [0xcc; 64],
        };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_pong_roundtrip() {
        let resp = Response::Pong;
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn response_error_roundtrip() {
        let resp = Response::Error {
            message: "kaboom".to_string(),
        };
        let bytes = resp.encode().unwrap();
        let decoded = Response::decode(&bytes).unwrap();
        assert_eq!(decoded, resp);
    }

    #[test]
    fn request_decode_rejects_unknown_type() {
        let mut m = BTreeMap::new();
        m.insert("type".to_string(), Value::String("nope".to_string()));
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Request::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("nope")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }

    #[test]
    fn response_decode_rejects_unknown_shape() {
        let mut m = BTreeMap::new();
        m.insert("random".to_string(), Value::Int(42));
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Response::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("missing recognized key")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }

    #[test]
    fn response_decode_rejects_wrong_pubkey_length() {
        let mut m = BTreeMap::new();
        m.insert("pubkey".to_string(), Value::Bytes(vec![1, 2, 3])); // not 32
        let bytes = encode(&Value::Map(m)).unwrap().0;
        let err = Response::decode(&bytes).unwrap_err();
        match err {
            HostError::Protocol(msg) => assert!(msg.contains("32")),
            other => panic!("expected protocol error, got {other:?}"),
        }
    }
}
