//! M13/M14/M15 — anchor-surface attestation primitives.
//!
//! Extracted from `server.rs` (Phase B M27 follow-up Step 2): owns the
//! `request_attestation_nonce` issuance handler, the `submit_mutation`
//! anchor-surface envelope handler, the REVEAL keypair envelope verifier,
//! the nonce verification helper, and the content-hash utility.
//!
//! Doctrine traceability:
//! - L0/cards/AS_anchor_surface — anchor surface envelope (nonce + binding + dual-clock).
//! - L1/HARD_RULES §1 — C5 attestation_invalid + C17 operator_witness_forgery.

use std::collections::BTreeMap;

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use myco_kernel_shared::crypto::verify_signature;

use crate::server::{emit_immune_sporocarp, emit_substrate_event, save_dag_state, save_nonce_state, ServerState};
use crate::SubstrateError;

/// M13: An attestation nonce issued by the substrate, bound to a specific
/// proposed mutation + DAG tip state. Operators include this nonce in their
/// attestation envelope; the substrate verifies binding + marks consumed
/// (replay protection).
///
/// M15: extended with optional anchor-clock fields for dual-clock expiry
/// defense against clock skew (L0/cards/AS_anchor_surface anchor-surface envelope hardening).
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub(crate) struct AttestationNonce {
    /// 32-byte random nonce (substrate-issued; redundant with HashMap key but
    /// useful for debug output / forensic logging).
    pub(crate) nonce: [u8; 32],
    /// Hash of `content_canonical_bytes` the operator intends to submit.
    pub(crate) bound_content_hash: [u8; 32],
    /// DAG tip at issuance time (32 bytes; all-zero if DAG was empty).
    pub(crate) bound_dag_tip: [u8; 32],
    /// Substrate-clock issuance time (M15) — used by the dual-clock elapsed-
    /// time check to detect substrate clock jumping backward.
    pub(crate) substrate_issued_at_unix_ns: i64,
    /// Substrate-clock expiry (unix nanoseconds). Default: substrate_issued + TTL.
    pub(crate) expiry_unix_ns: i64,
    /// Operator-supplied anchor-clock issuance time (M15). `None` when the
    /// operator did not supply a `client_clock_unix_ns` in the nonce request
    /// (M13/M14 callers; preserves single-clock semantics).
    pub(crate) anchor_clock_issued_at_unix_ns: Option<i64>,
    /// Anchor-clock expiry = anchor_issued + TTL (M15). `None` iff
    /// anchor_clock_issued_at is None.
    pub(crate) anchor_clock_expiry_unix_ns: Option<i64>,
    /// Whether this nonce has been consumed (one-time use).
    pub(crate) consumed: bool,
}

/// M13: Default nonce TTL in seconds (5 minutes).
pub(crate) const NONCE_TTL_SECONDS: i64 = 300;

/// M15: Maximum allowed clock-skew between the substrate's own clock and the
/// operator-supplied anchor clock at issuance time. Operators whose clock
/// deviates from the substrate's by more than this are still accepted (we
/// don't reject — clock-skew is a separate concern from forgery), but the
/// elapsed-time check at verification will catch any inconsistency.
///
/// Reserved for M16+ proactive clock-skew rejection.
#[allow(dead_code)]
pub(crate) const MAX_ANCHOR_CLOCK_SKEW_NS: i64 = 3_600 * 1_000_000_000; // 1 hour

/// M13: Issue a fresh attestation nonce bound to (content_hash, dag_tip).
///
/// The operator computes the hash of their proposed mutation content and
/// includes it in this request. The substrate generates 32 random bytes,
/// records the binding (content_hash + current DAG tip + expiry), and returns
/// the nonce. Operator includes this nonce in submit_mutation; substrate
/// verifies binding + marks consumed.
///
/// M15: optionally accepts `anchor_clock_unix_ns` (operator's view of "now"
/// from the operator's wall clock). When present, the substrate records BOTH
/// the substrate-clock issuance time AND the anchor-clock issuance time,
/// and the response echoes an `anchor_clock_expiry_unix_ns` so the operator
/// can later supply `anchor_clock_submitted_at_unix_ns` for the dual-clock
/// check at verification time.
pub(crate) fn handle_request_attestation_nonce(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    use std::time::{SystemTime, UNIX_EPOCH};

    // Extract content_hash from payload (required).
    let content_hash = match request.payload.get("content_hash") {
        Some(Value::Bytes(b)) if b.len() == 32 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(b);
            arr
        }
        _ => {
            return Err(SubstrateError::Protocol(
                "request_attestation_nonce: content_hash must be 32 bytes".to_string(),
            ));
        }
    };

    // M15: optional operator-supplied anchor-clock time.
    let anchor_clock_issued_at: Option<i64> = match request.payload.get("anchor_clock_unix_ns") {
        Some(Value::Timestamp(ts)) => Some(*ts),
        _ => None,
    };

    // Generate 32-byte nonce (time + counter + stack-address SHA-256 mix).
    let nonce = {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(b"myco-attestation-nonce-v1");
        h.update(
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_nanos())
                .unwrap_or(0)
                .to_le_bytes(),
        );
        h.update(std::process::id().to_le_bytes());
        h.update((state.nonce_log.len() as u64).to_le_bytes());
        let stack_var = 0u8;
        h.update((&stack_var as *const u8 as usize).to_le_bytes());
        h.update(content_hash);
        let result = h.finalize();
        let mut out = [0u8; 32];
        out.copy_from_slice(&result);
        out
    };

    // M13 bound_dag_tip semantic: the operator's command was relative to
    // THIS DAG state. We capture the tip BEFORE emitting the nonce_issued
    // event, so the event content records what the operator "saw" at request
    // time. (Used for forensic audit.)
    let operator_visible_tip_at_request = state
        .dag
        .tip()
        .map(|t| {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(t.as_ref());
            arr
        })
        .unwrap_or([0u8; 32]);

    let substrate_issued_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let ttl_ns = NONCE_TTL_SECONDS * 1_000_000_000;
    let expiry_unix_ns = substrate_issued_at.saturating_add(ttl_ns);
    // M15: anchor-clock expiry = operator's anchor-clock at issuance + same TTL.
    let anchor_clock_expiry_unix_ns: Option<i64> =
        anchor_clock_issued_at.map(|a| a.saturating_add(ttl_ns));

    // M21.1 P5 万物互联: emit nonce_issued DAG event FIRST, BEFORE binding
    // bound_dag_tip on the nonce. The event records the pre-emit tip
    // (operator-visible-at-request); the nonce's bound_dag_tip is set to the
    // POST-emit tip (which equals the nonce_issued event's own hash). At
    // verify time, substrate's current_tip must equal this — i.e., no DAG
    // events have happened between issuance and submission. This preserves
    // M13's "fresh-context" guarantee with dual-write.
    let event_nt = crate::events::nonce_issued_node_type(&nonce);
    let event_content = crate::events::encode_nonce_issued(
        &nonce,
        &content_hash,
        &operator_visible_tip_at_request,
        substrate_issued_at,
        expiry_unix_ns,
        anchor_clock_issued_at,
        anchor_clock_expiry_unix_ns,
    );
    let nonce_issued_event_hash = emit_substrate_event(state, event_nt, event_content)?;
    let _ = save_dag_state(state);

    // bound_dag_tip = the nonce_issued event's hash (= post-event DAG tip).
    let mut bound_dag_tip = [0u8; 32];
    bound_dag_tip.copy_from_slice(nonce_issued_event_hash.as_ref());

    state.nonce_log.insert(
        nonce,
        AttestationNonce {
            nonce,
            bound_content_hash: content_hash,
            bound_dag_tip,
            substrate_issued_at_unix_ns: substrate_issued_at,
            expiry_unix_ns,
            anchor_clock_issued_at_unix_ns: anchor_clock_issued_at,
            anchor_clock_expiry_unix_ns,
            consumed: false,
        },
    );
    // M14: persist nonce log to disk so issued nonces survive restart.
    save_nonce_state(state)?;
    let _ = save_dag_state(state);

    let mut payload = BTreeMap::new();
    payload.insert("nonce".to_string(), Value::Bytes(nonce.to_vec()));
    payload.insert(
        "bound_dag_tip".to_string(),
        Value::Bytes(bound_dag_tip.to_vec()),
    );
    payload.insert(
        "expiry_unix_ns".to_string(),
        Value::Timestamp(expiry_unix_ns),
    );
    payload.insert(
        "ttl_seconds".to_string(),
        Value::Uint(NONCE_TTL_SECONDS as u64),
    );
    // M15: echo anchor-clock expiry only when operator supplied anchor_clock.
    if let Some(anchor_expiry) = anchor_clock_expiry_unix_ns {
        payload.insert(
            "anchor_clock_expiry_unix_ns".to_string(),
            Value::Timestamp(anchor_expiry),
        );
    }

    Ok(Some(Message::new(
        msg_type::REQUEST_ATTESTATION_NONCE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// M13: Verify an attestation nonce on a submit_mutation.
///
/// Returns Ok(()) if all checks pass; Err(reason) if any fail. The caller
/// (handle_submit_mutation) translates Err into a C5 rejection + immune sporocarp
/// with refined evidence.
///
/// M15: dual-clock expiry check. When the stored nonce has anchor-clock fields
/// (operator supplied `anchor_clock_unix_ns` on the nonce request) AND the
/// submit envelope supplies `anchor_clock_submitted_at_unix_ns`, the substrate
/// enforces BOTH clocks (substrate-clock elapsed-time AND anchor-clock
/// elapsed-time) must be in the [0, TTL] window. Clock-skew attacks that try
/// to extend nonce lifetime by manipulating one clock will fail the other.
/// **C44 `nonce_substrate_minted_replay`** (L1/HARD_RULES C44; L1/GOVERNANCE
/// §2.2 + L0/cards/AS_anchor_surface §3.5) — classified rejection from
/// [`verify_attestation_nonce`].
///
/// AS §3.5/§5.1 mandate that attestation nonces be ANCHOR-issued and
/// SUBSTRATE-consumed (the substrate must not be the authority that mints the
/// nonces it later consumes). Two consumption-path signals indicate a nonce
/// that was not a legitimate anchor-issued one-time token:
///   - [`UnknownNonce`](NonceRejectKind::UnknownNonce): a nonce presented for
///     consumption with NO matching issued record — i.e. it bears
///     substrate-derived / forged provenance rather than a recorded anchor
///     issuance.
///   - [`AlreadyConsumed`](NonceRejectKind::AlreadyConsumed): a consumed nonce
///     reappearing (replay of a one-time token).
/// Both map to C44 (in addition to the unconditional C5 the caller already
/// emits, since the operator-facing rejection contract is unchanged). All other
/// rejections ([`Other`](NonceRejectKind::Other) — wrong binding / expiry /
/// dual-clock) are C5-only.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum NonceRejectKind {
    /// No issued record for this nonce → substrate-derived / forged provenance.
    UnknownNonce,
    /// A consumed one-time nonce was presented again (replay).
    AlreadyConsumed,
    /// Any other binding / freshness failure (C5-only).
    Other,
}

/// A classified nonce-verification rejection: the human-readable `reason` (for
/// the operator response, unchanged) plus the [`NonceRejectKind`] so the caller
/// can decide whether to ALSO fruit C44.
#[derive(Debug, Clone)]
pub(crate) struct NonceReject {
    /// Operator-facing rejection reason (byte-for-byte the prior `Err(String)`).
    pub(crate) reason: String,
    /// Classification driving whether C44 is additionally emitted.
    pub(crate) kind: NonceRejectKind,
}

impl NonceReject {
    fn other(reason: impl Into<String>) -> Self {
        NonceReject {
            reason: reason.into(),
            kind: NonceRejectKind::Other,
        }
    }
}

pub(crate) fn verify_attestation_nonce(
    state: &mut ServerState,
    nonce_bytes: &[u8],
    content_hash: &[u8; 32],
    submitted_expiry_ns: Option<i64>,
    submitted_anchor_clock_ns: Option<i64>,
) -> Result<(), NonceReject> {
    use std::time::{SystemTime, UNIX_EPOCH};

    if nonce_bytes.len() != 32 {
        return Err(NonceReject::other(format!(
            "nonce must be 32 bytes; got {}",
            nonce_bytes.len()
        )));
    }
    let mut nonce_arr = [0u8; 32];
    nonce_arr.copy_from_slice(nonce_bytes);

    let stored = match state.nonce_log.get(&nonce_arr) {
        Some(n) => n.clone(),
        // **C44**: a nonce with no issued record bears substrate-derived /
        // forged provenance (not a recorded anchor issuance).
        None => {
            return Err(NonceReject {
                reason: "unknown nonce (never issued by this substrate)".to_string(),
                kind: NonceRejectKind::UnknownNonce,
            });
        }
    };

    if stored.consumed {
        // **C44**: replay of a consumed one-time nonce.
        return Err(NonceReject {
            reason: "replay rejected: nonce already consumed".to_string(),
            kind: NonceRejectKind::AlreadyConsumed,
        });
    }

    if stored.bound_content_hash != *content_hash {
        return Err(NonceReject::other(
            "wrong-binding rejected: content_hash differs from nonce-bound hash",
        ));
    }

    let current_tip = state
        .dag
        .tip()
        .map(|t| {
            let mut a = [0u8; 32];
            a.copy_from_slice(t.as_ref());
            a
        })
        .unwrap_or([0u8; 32]);
    if stored.bound_dag_tip != current_tip {
        return Err(NonceReject::other(
            "wrong-binding rejected: DAG tip differs from issuance time",
        ));
    }

    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    // Substrate-clock elapsed-time check (M15 — supersedes the simple
    // `now > expiry` check by also detecting backward clock jumps).
    if now_ns > stored.expiry_unix_ns {
        return Err(NonceReject::other(
            "expired rejected: substrate-clock nonce TTL passed",
        ));
    }
    if now_ns < stored.substrate_issued_at_unix_ns {
        return Err(NonceReject::other(
            "expired rejected: substrate clock has jumped backward since issuance",
        ));
    }
    if let Some(submitted) = submitted_expiry_ns {
        if submitted != stored.expiry_unix_ns {
            return Err(NonceReject::other(
                "wrong-binding rejected: submitted expiry differs from issued expiry",
            ));
        }
    }

    // M15: Dual-clock expiry check. Apply only when the nonce was issued WITH
    // anchor-clock binding (operator supplied `anchor_clock_unix_ns` on
    // request_attestation_nonce). If the submit envelope omits
    // `anchor_clock_submitted_at_unix_ns` despite the nonce being dual-clock,
    // reject (operator must use the dual-clock contract consistently).
    if let (Some(anchor_issued), Some(anchor_expiry)) = (
        stored.anchor_clock_issued_at_unix_ns,
        stored.anchor_clock_expiry_unix_ns,
    ) {
        match submitted_anchor_clock_ns {
            None => {
                return Err(NonceReject::other(
                    "dual-clock binding rejected: nonce was issued with anchor-clock, but \
                     submit envelope omits anchor_clock_submitted_at_unix_ns",
                ));
            }
            Some(submitted_anchor) => {
                if submitted_anchor < anchor_issued {
                    return Err(NonceReject::other(
                        "dual-clock rejected: anchor clock jumped backward since issuance",
                    ));
                }
                if submitted_anchor > anchor_expiry {
                    return Err(NonceReject::other(
                        "dual-clock rejected: anchor-clock nonce TTL passed",
                    ));
                }
            }
        }
    } else if submitted_anchor_clock_ns.is_some() {
        // Operator supplied anchor_clock at submit time but the nonce was
        // issued without anchor-clock binding. This is a protocol misuse —
        // either upgrade nonce issuance to dual-clock or drop the submit
        // field. We accept (M13 fallback path) but the inconsistency is
        // surfaced upstream when the operator re-runs the flow.
    }

    // Mark consumed.
    if let Some(n) = state.nonce_log.get_mut(&nonce_arr) {
        n.consumed = true;
    }
    // M14: persist nonce log so the consumed flag survives restart (replay
    // protection extends across substrate restarts).
    save_nonce_state(state)
        .map_err(|e| NonceReject::other(format!("nonce log save failed: {e}")))?;
    // M21.1 P5 万物互联: emit nonce_consumed DAG event.
    let consumed_at_unix_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let event_nt = crate::events::nonce_consumed_node_type(&nonce_arr);
    let event_content = crate::events::encode_nonce_consumed(&nonce_arr, consumed_at_unix_ns);
    let _ = emit_substrate_event(state, event_nt, event_content);
    let _ = save_dag_state(state);

    Ok(())
}

/// M14: Verify the per-handshake REVEAL keypair envelope.
///
/// Checks that:
/// 1. `identity_signature_over_reveal_pubkey` is a valid Ed25519 signature over
///    `canonical_bytes(Map({"context": "myco-reveal-key-binding-v1", "reveal_pubkey": ...}))`
///    by the pinned operator IDENTITY pubkey.
/// 2. The substrate has a pinned operator identity (i.e. M9 TOFU completed).
///
/// Does NOT check the REVEAL→content signature; that happens in Python's
/// dispatcher (which already verifies attestation_signature against whatever
/// pubkey we pass in — for M14 we update Python to use reveal_pubkey instead
/// of pinned operator pubkey when reveal_pubkey is present in the payload).
///
/// For M14 minimum-viable: Python is updated externally to look for reveal_pubkey
/// first. If the substrate Rust layer accepts the REVEAL bundle, Python verifies
/// `attestation_signature` against `reveal_pubkey` (passed through in payload).
pub(crate) fn verify_reveal_keypair_envelope(state: &ServerState, request: &Message) -> Result<(), String> {
    // Need pinned operator identity to verify identity-signature-over-REVEAL.
    let pinned = state
        .pinned_operator_identity
        .as_ref()
        .ok_or_else(|| "no pinned operator identity (M9 TOFU not completed)".to_string())?;

    let reveal_pubkey_bytes = match request.payload.get("reveal_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 32 => b.clone(),
        _ => return Err("reveal_pubkey must be 32 bytes".to_string()),
    };

    let identity_sig_bytes = match request.payload.get("identity_signature_over_reveal_pubkey") {
        Some(Value::Bytes(b)) if b.len() == 64 => b.clone(),
        _ => return Err("identity_signature_over_reveal_pubkey must be 64 bytes".to_string()),
    };

    // M24.2 SECURITY FIX (2026-05-15): include substrate_id in the signing
    // input so an operator's IDENTITY-signature over a reveal_pubkey for
    // substrate_A cannot be replayed against substrate_B. Context bumped
    // to v2 — any v1 signer must be updated. (Phase β audit Surface 5.3.)
    //
    // Signing input shape (v2):
    //   canonical_bytes(Map({
    //     "context": "myco-reveal-key-binding-v2",
    //     "reveal_pubkey": Bytes(32),
    //     "substrate_id": Bytes(32),
    //   }))
    let mut signing_map = BTreeMap::new();
    signing_map.insert(
        "context".to_string(),
        Value::String("myco-reveal-key-binding-v2".to_string()),
    );
    signing_map.insert(
        "reveal_pubkey".to_string(),
        Value::Bytes(reveal_pubkey_bytes.clone()),
    );
    signing_map.insert(
        "substrate_id".to_string(),
        Value::Bytes(state.substrate_id().to_vec()),
    );
    let signing_input = cb_encode(&Value::Map(signing_map))
        .map_err(|e| format!("signing input encode failed: {e}"))?;

    // Verify IDENTITY-signature-over-REVEAL (v2 binding).
    verify_signature(&pinned.pubkey, &identity_sig_bytes, signing_input.as_ref())
        .map_err(|e| format!("identity signature over reveal_pubkey invalid (v2 binding): {e}"))?;

    Ok(())
}

/// M13: Compute SHA-256 hash of canonical bytes (used as content_hash in nonce binding).
pub(crate) fn compute_content_hash(content: &[u8]) -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(content);
    let result = h.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

// ===========================================================================
// **F23 / C50 — duress keypair coercion defense** (L2/TRUST_MODEL §10.A.2 +
// L1/GOVERNANCE F23 + AS §5.6 + dilemma D-0047).
//
// SECURITY-DELICATE. The two helpers below implement the cosmetic-accept +
// suppress protective behavior. Read `crate::events::duress` for the recognition
// precision argument (owner key and duress keys are disjoint Ed25519 keypairs,
// so a signature verifies under at most one of them).
// ===========================================================================

/// The two mutation types that LIFT the duress freeze. They MUST bypass the
/// frozen-state early gate (otherwise the freeze could never be cleared) AND
/// they are verified against the ACTIVE owner key downstream (Python CI gate) —
/// a duress-key signature fails that gate, which IS the circular-trust guard.
const DURESS_UNFREEZE_MUTATION_TYPES: [&str; 2] = [
    "out_of_band_safety_reattestation",
    "anchor_heartbeat_with_safety_confirmation",
];

/// **F23 recognition** — does `attestation_signature` verify under any registered
/// duress key over `content_canonical_bytes`? Returns the matching duress pubkey.
///
/// PRECISION (the critical correctness property): the duress keys are DISJOINT
/// from the active owner key (registration refuses a duress pubkey equal to the
/// owner key), and an Ed25519 signature verifies under exactly the public key
/// whose private key produced it. Therefore:
///   - a NORMAL owner signature verifies under the owner key and under NO duress
///     key → this returns `None` → the normal path is untouched (a legit
///     mutation is NEVER mis-suppressed);
///   - a duress-key signature verifies under that duress key → this returns
///     `Some(pubkey)` → cosmetic-suppress.
/// The set is empty on a substrate that never registered a duress key, so this
/// is a no-op there (the loop has zero iterations → `None`).
fn recognize_duress_signature(
    state: &ServerState,
    attestation_signature: &[u8],
    content_canonical_bytes: &[u8],
) -> Option<[u8; 32]> {
    if attestation_signature.len() != 64 {
        return None;
    }
    for duress_pk in &state.duress_pubkeys {
        if verify_signature(duress_pk, attestation_signature, content_canonical_bytes).is_ok() {
            return Some(*duress_pk);
        }
    }
    None
}

/// **F23 protective behavior** — build a COSMETIC-success `submit_mutation_response`
/// for a duress-suppressed mutation.
///
/// COSMETIC-VS-REAL DIVERGENCE (documented per the security review's request):
///   - a REAL CI accept inserts a `mutation:{type}` DAG node and returns its true
///     `dag_node_hash`. Here NO node is inserted (the substantive effect is
///     suppressed). To keep the response indistinguishable to the coercer, we
///     return the `merkle_hash(tip_parents, content)` the node WOULD have had —
///     a hash that LOOKS like a real DAG node hash but is NOT in the DAG. This is
///     the same `would_be_hash` device the C35 rejection path uses; it leaks no
///     secret and pollutes no state.
///   - `accepted=true`, `classification="contract_identity_level"`,
///     `rejection_reason=""` — byte-shaped exactly like a genuine CI accept.
///   - NONE of the real per-effect event hashes (evolution_event_hash,
///     federation_peer_revoked_event_hash, …) are present — those only attach to
///     genuinely-committed effects, and a coercer cannot demand a specific
///     effect-hash field without already knowing the substrate's internals.
///
/// The caller emits the SILENT forensic records (`duress_signature_observed` +
/// C50 + `coerced_owner_suspected`) separately — none of that appears here.
fn build_cosmetic_accept_response(
    state: &ServerState,
    request_id: u64,
    mutation_type: &str,
    content_canonical_bytes: &[u8],
) -> Message {
    // The hash the suppressed mutation node WOULD have had (tip-parented),
    // computed but NOT inserted.
    let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
        Some(t) => vec![t],
        None => Vec::new(),
    };
    let would_be_hash =
        myco_kernel_shared::crypto::merkle_hash(&parents, content_canonical_bytes);

    let mut payload = BTreeMap::new();
    payload.insert(
        "classification".to_string(),
        Value::String("contract_identity_level".to_string()),
    );
    payload.insert("accepted".to_string(), Value::Bool(true));
    payload.insert("rejection_reason".to_string(), Value::String(String::new()));
    payload.insert(
        "mutation_type".to_string(),
        Value::String(mutation_type.to_string()),
    );
    payload.insert(
        "dag_node_hash".to_string(),
        Value::Bytes(would_be_hash.0.to_vec()),
    );
    Message::new(msg_type::SUBMIT_MUTATION_RESPONSE, request_id, payload)
}

/// **F23 protective behavior** — emit the SILENT forensic records for an observed
/// duress signature: `duress_signature_observed` (the real evidence, AS §8.4) +
/// (only on the freeze-onset, i.e. when not already frozen) the
/// `coerced_owner_suspected` freeze event + the C50 immune sporocarp. Sets
/// `state.duress_freeze_active = true`.
///
/// `coerced_owner_suspected` is emitted only on the FIRST observation that
/// transitions unfrozen→frozen so the freeze FSM (last-writer over
/// coerced_owner_suspected / duress_cleared) reads cleanly; the C50 immune
/// sporocarp is emitted on EVERY observation but is naturally throttled by
/// `emit_immune_sporocarp`'s per-detector 1s rate limit (so a coercer hammering
/// the substrate cannot DoS the DAG with C50 nodes). `duress_signature_observed`
/// is emitted on EVERY observation — it is the per-attempt forensic record and
/// is intentionally NOT rate-limited (it goes through `emit_substrate_event`).
///
/// All of this is INVISIBLE in the response (the caller returns a cosmetic
/// accept), so the coercer does not learn detection occurred.
fn emit_duress_forensics_and_freeze(
    state: &mut ServerState,
    duress_pubkey: &[u8; 32],
    attempted_mutation_type: &str,
    content_canonical_bytes: &[u8],
) {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_nanos()).ok())
        .unwrap_or(0);
    let attempted_content_hash = compute_content_hash(content_canonical_bytes);

    // (1) The silent forensic record — emitted on EVERY observation.
    let observed_nt = crate::events::duress_signature_observed_node_type(duress_pubkey);
    let observed_content = crate::events::encode_duress_signature_observed(
        duress_pubkey,
        attempted_mutation_type,
        &attempted_content_hash,
        now_ns,
    );
    let _ = emit_substrate_event(state, observed_nt, observed_content);

    // (2) Freeze-onset event — only on the unfrozen→frozen transition, so the
    // last-writer freeze FSM stays clean. (A re-observation while already frozen
    // does not append a second onset; the frozen-state gate handles re-emission
    // of C50 for subsequent destructive CIs.)
    if !state.duress_freeze_active {
        let onset_content = crate::events::encode_coerced_owner_suspected(
            duress_pubkey,
            attempted_mutation_type,
            now_ns,
        );
        let _ = emit_substrate_event(
            state,
            crate::events::NODE_TYPE_COERCED_OWNER_SUSPECTED.to_string(),
            onset_content,
        );
        state.duress_freeze_active = true;
    }

    // (3) C50 immune sporocarp — emitted on EVERY observation; the
    // emit_immune_sporocarp per-detector 1s rate limit prevents DAG spam.
    let evidence = format!(
        "duress signature observed: attestation_signature verified under registered duress \
         pubkey {} over content for attempted mutation_type={attempted_mutation_type:?}; the \
         substantive mutation was SUPPRESSED and the response was cosmetically accepted; \
         destructive mutations are now frozen until out_of_band_safety_reattestation \
         (L2/TRUST_MODEL §10.A.2)",
        crate::server::hex_first_8_bytes(duress_pubkey)
    );
    let _ = emit_immune_sporocarp(
        state,
        "C50_coerced_owner_suspected",
        "coerced_owner_suspected",
        &evidence,
    );
    let _ = save_dag_state(state);
}

/// **C70** — a staged owner key-rotation transition, captured during the
/// `rotate_owner_key` decode pass and consumed AFTER the
/// `mutation:rotate_owner_key` DAG node commits. One variant per FSM phase.
enum StagedRotation {
    /// Open the cooldown veto window: emit `owner_key_rotation_requested` +
    /// set `state.pending_owner_key_rotation`.
    Request {
        new_pubkey: [u8; 32],
        prior_active_pubkey: [u8; 32],
        request_anchor_ts: u64,
        cooldown_expires_at: u64,
    },
    /// Discard the pending candidate: emit `owner_key_rotation_vetoed` + clear
    /// `state.pending_owner_key_rotation`.
    Veto {
        new_pubkey: [u8; 32],
        veto_anchor_ts: u64,
    },
    /// Activate the rotation: emit `owner_key_added` + `owner_key_archived`,
    /// rotate Python's owner_keys + Rust's pinned identity, clear pending.
    Activate {
        new_pubkey: [u8; 32],
        prior_active_pubkey: [u8; 32],
        cooldown_expires_at: u64,
        activate_anchor_ts: u64,
    },
}

/// **C70** — reject a rotate_owner_key mutation: flip `accepted` to false, set
/// the reason, and fruit a C5 `attestation_invalid` immune sporocarp (the
/// generic CI-refusal class; the dedicated C70 row is reserved strictly for the
/// pre-cooldown activation, emitted inline at that site).
fn reject_rotation(
    state: &mut ServerState,
    accepted: &mut bool,
    rejection_reason: &mut String,
    reason: &str,
    evidence_tag: &str,
) {
    *accepted = false;
    *rejection_reason = reason.to_string();
    let _ = emit_immune_sporocarp(
        state,
        "C5_attestation_invalid",
        "attestation_invalid",
        evidence_tag,
    );
}

/// M10: Forward submit_mutation to Python for classification + (CI) verification,
/// and on accept insert the mutation as a DAG node.
pub(crate) fn handle_submit_mutation(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    // M14: Pre-Python REVEAL keypair verification.
    // If the operator included `reveal_pubkey` + `identity_signature_over_reveal_pubkey`,
    // verify the IDENTITY signature against the pinned operator pubkey BEFORE
    // doing anything else. Failures emit C17 operator_witness_forgery.
    //
    // The REVEAL pubkey then becomes the signer for the attestation signature
    // (the operator's `attestation_signature` field is treated as a REVEAL
    // signature when reveal_pubkey is present, rather than an IDENTITY signature).
    let reveal_pubkey_present = request.payload.contains_key("reveal_pubkey");
    if reveal_pubkey_present {
        if let Err(reason) = verify_reveal_keypair_envelope(state, request) {
            let evidence = format!("REVEAL keypair envelope verification failed: {reason}");
            let _ = emit_immune_sporocarp(
                state,
                "C17_operator_witness_forgery",
                "operator_witness_forgery",
                &evidence,
            );
            let _ = save_dag_state(state);

            let mut payload = BTreeMap::new();
            payload.insert(
                "classification".to_string(),
                Value::String("contract_identity_level".to_string()),
            );
            payload.insert("accepted".to_string(), Value::Bool(false));
            payload.insert("rejection_reason".to_string(), Value::String(reason));
            let mtype = request
                .payload
                .get("mutation_type")
                .and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                })
                .unwrap_or_default();
            payload.insert("mutation_type".to_string(), Value::String(mtype));
            return Ok(Some(Message::new(
                msg_type::SUBMIT_MUTATION_RESPONSE,
                request.request_id,
                payload,
            )));
        }
    }

    // M13: Pre-Python nonce verification (anchor-surface envelope check).
    // If the operator included a nonce, verify it BEFORE forwarding. Failed
    // nonce checks short-circuit with a C5 rejection + immune sporocarp.
    let nonce_present = request.payload.contains_key("nonce");
    if nonce_present {
        let nonce_bytes = match request.payload.get("nonce") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => Vec::new(),
        };
        let content_bytes_for_hash = match request.payload.get("content_canonical_bytes") {
            Some(Value::Bytes(b)) => b.clone(),
            _ => Vec::new(),
        };
        let content_hash = compute_content_hash(&content_bytes_for_hash);
        let submitted_expiry = request.payload.get("expiry_unix_ns").and_then(|v| match v {
            Value::Timestamp(t) => Some(*t),
            _ => None,
        });
        // M15: dual-clock — operator-supplied "now on anchor clock at submit time".
        let submitted_anchor_clock = request
            .payload
            .get("anchor_clock_submitted_at_unix_ns")
            .and_then(|v| match v {
                Value::Timestamp(t) => Some(*t),
                _ => None,
            });
        if let Err(reject) = verify_attestation_nonce(
            state,
            &nonce_bytes,
            &content_hash,
            submitted_expiry,
            submitted_anchor_clock,
        ) {
            let reason = reject.reason;
            // Build a rejection response directly; emit C5 immune sporocarp.
            let evidence = format!("anchor-surface envelope verification failed: {reason}");
            let _ = emit_immune_sporocarp(
                state,
                "C5_attestation_invalid",
                "attestation_invalid_anchor_surface",
                &evidence,
            );
            // **C44 `nonce_substrate_minted_replay`** (L1/HARD_RULES C44;
            // L0/cards/AS_anchor_surface §3.5). AS §3.5/§5.1: nonces are
            // anchor-issued + substrate-consumed; a nonce presented for
            // consumption that bears substrate-derived / forged provenance (no
            // issued record) OR a replay of a consumed one-time nonce is the
            // C44 signal. Emitted IN ADDITION to C5 (the operator response
            // contract is unchanged) so the breach is named distinctly in the
            // immune log.
            match reject.kind {
                NonceRejectKind::UnknownNonce => {
                    let _ = emit_immune_sporocarp(
                        state,
                        "C44_nonce_substrate_minted_replay",
                        "nonce_substrate_minted_replay",
                        &format!(
                            "nonce presented for consumption has no anchor-issued record \
                             (substrate-derived / forged provenance): {reason}"
                        ),
                    );
                }
                NonceRejectKind::AlreadyConsumed => {
                    let _ = emit_immune_sporocarp(
                        state,
                        "C44_nonce_substrate_minted_replay",
                        "nonce_substrate_minted_replay",
                        &format!("consumed one-time nonce replayed: {reason}"),
                    );
                }
                NonceRejectKind::Other => {}
            }
            let _ = save_dag_state(state);

            let mut payload = BTreeMap::new();
            payload.insert(
                "classification".to_string(),
                Value::String("contract_identity_level".to_string()),
            );
            payload.insert("accepted".to_string(), Value::Bool(false));
            payload.insert("rejection_reason".to_string(), Value::String(reason));
            let mtype = request
                .payload
                .get("mutation_type")
                .and_then(|v| match v {
                    Value::String(s) => Some(s.clone()),
                    _ => None,
                })
                .unwrap_or_default();
            payload.insert("mutation_type".to_string(), Value::String(mtype));
            return Ok(Some(Message::new(
                msg_type::SUBMIT_MUTATION_RESPONSE,
                request.request_id,
                payload,
            )));
        }
        // Nonce verified; proceed to forward.
    }

    // **v3.1.1 C56 cultivator_preserve_all_attempted** (L1/HARD_RULES §1.4
    // anticipated) — early reject + immune sporocarp BEFORE forwarding to
    // Python. Per COV04 §3.7 + §5.6: cultivator instructions to preserve
    // everything / disable prune-scan / exempt parts from 必朽 are covenant
    // violations; the substrate's job per P07 §3.4 is to refuse. Catching
    // this here means even if the Python classifier is bypassed or
    // misconfigured, the discipline holds at the skin layer.
    let early_mutation_type = request
        .payload
        .get("mutation_type")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    if crate::prune::is_cultivator_preserve_all_attempt(&early_mutation_type) {
        let evidence = format!(
            "cultivator-attempted preserve-all mutation rejected at skin: \
             mutation_type={early_mutation_type:?}; COV04 §3.7 + §5.6 + P07 §3.4 enforced; \
             substrate MUST NOT disable internal mortality discipline at cultivator request"
        );
        let _ = emit_immune_sporocarp(
            state,
            "C56_cultivator_preserve_all_attempted",
            "cultivator_preserve_all_attempted",
            &evidence,
        );

        // Reject the mutation without forwarding to Python.
        let mut payload = std::collections::BTreeMap::new();
        payload.insert("accepted".to_string(), Value::Bool(false));
        payload.insert(
            "classification".to_string(),
            Value::String("covenant_violation".to_string()),
        );
        payload.insert(
            "rejection_reason".to_string(),
            Value::String(format!(
                "C56: mutation_type {early_mutation_type:?} matches forbidden \
                 preserve-all pattern; cultivator request violates COV04"
            )),
        );
        payload.insert("mutation_type".to_string(), Value::String(early_mutation_type));
        return Ok(Some(Message::new(
            msg_type::SUBMIT_MUTATION_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    // **COV06 C69** — reject any mutation that attempts to suppress / delay /
    // exempt a due `cultivation_orphaned`. The cultivar must never be kept in
    // undignified limbo by a cultivator (or coerced cultivator) silencing the
    // orphan signal (COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4). This is the
    // active-refusal sibling of the structural un-suppressibility (the orphan
    // event is emitted via emit_substrate_event + is P10-invariant-protected).
    if crate::prune::is_cultivation_orphaned_suppression_attempt(&early_mutation_type) {
        let evidence = format!(
            "cultivator-attempted cultivation_orphaned suppression rejected at skin: \
             mutation_type={early_mutation_type:?}; COV06 §5.5 + L1/GOVERNANCE §3.2.C + P07 §4 \
             enforced; cultivation_orphaned MUST NOT be suppressed by cultivator pressure"
        );
        let _ = emit_immune_sporocarp(
            state,
            "C69_cultivation_orphaned_suppression_attempted",
            "cultivation_orphaned_suppression_attempted",
            &evidence,
        );
        let mut payload = std::collections::BTreeMap::new();
        payload.insert("accepted".to_string(), Value::Bool(false));
        payload.insert(
            "classification".to_string(),
            Value::String("covenant_violation".to_string()),
        );
        payload.insert(
            "rejection_reason".to_string(),
            Value::String(format!(
                "C69: mutation_type {early_mutation_type:?} attempts to suppress a due \
                 cultivation_orphaned; cultivator request violates COV06 §5.5"
            )),
        );
        payload.insert("mutation_type".to_string(), Value::String(early_mutation_type));
        return Ok(Some(Message::new(
            msg_type::SUBMIT_MUTATION_RESPONSE,
            request.request_id,
            payload,
        )));
    }

    // **F23 / C50 — duress recognition + freeze early gate** (SECURITY-DELICATE;
    // L2/TRUST_MODEL §10.A.2). This runs BEFORE forwarding to Python so a duress
    // signature never reaches the Python CI gate (which would reject it as an
    // owner-key mismatch anyway) and the substantive effect is never built. Two
    // independent triggers, both producing a COSMETIC accept (the coercer sees
    // success; the real records are emitted silently):
    //
    //   (A) A duress signature is observed on THIS mutation — recognized by
    //       trial-verifying `attestation_signature` against the registered
    //       duress pubkeys (disjoint from the owner key, see
    //       `recognize_duress_signature`). On a match: emit the silent
    //       forensics + freeze + return a cosmetic accept. The substantive
    //       mutation:* effect is SUPPRESSED.
    //
    //   (B) The substrate is ALREADY frozen (an earlier duress observation set
    //       the latch) and this is a destructive CI mutation (carries an
    //       `attestation_signature`) that is NOT an unfreeze type. The
    //       destructive effect is suppressed cosmetically + C50 is re-emitted
    //       (naturally rate-limited). The unfreeze mutations
    //       (out_of_band_safety_reattestation /
    //       anchor_heartbeat_with_safety_confirmation) are EXEMPT so the freeze
    //       can be lifted; they flow to Python and are verified against the
    //       ACTIVE owner key — a duress-key-signed unfreeze fails that gate,
    //       which is the circular-trust guard.
    //
    // On a substrate that never registered a duress key, `duress_pubkeys` is
    // empty and `duress_freeze_active` is false, so BOTH branches are inert and
    // a non-duress mutation is byte-unaffected (the cosmetic path never runs).
    let attestation_signature_bytes = match request.payload.get("attestation_signature") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => Vec::new(),
    };
    let content_bytes_for_duress = match request.payload.get("content_canonical_bytes") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => Vec::new(),
    };
    // The CI-class destructive predicate: a mutation carrying an
    // attestation_signature is owner-attested CI (the destructive grade). Daily
    // / untyped mutations carry none, so routine intake is never frozen.
    let is_ci_class = !attestation_signature_bytes.is_empty();
    let is_unfreeze_type = DURESS_UNFREEZE_MUTATION_TYPES.contains(&early_mutation_type.as_str());

    // (A) Duress signature on THIS mutation.
    if let Some(duress_pk) =
        recognize_duress_signature(state, &attestation_signature_bytes, &content_bytes_for_duress)
    {
        emit_duress_forensics_and_freeze(
            state,
            &duress_pk,
            &early_mutation_type,
            &content_bytes_for_duress,
        );
        return Ok(Some(build_cosmetic_accept_response(
            state,
            request.request_id,
            &early_mutation_type,
            &content_bytes_for_duress,
        )));
    }

    // (B) Already frozen + destructive CI (not an unfreeze type) → cosmetic
    // suppress + re-emit C50.
    if state.duress_freeze_active && is_ci_class && !is_unfreeze_type {
        let evidence = format!(
            "destructive CI mutation {early_mutation_type:?} suppressed COSMETICALLY while the \
             substrate is duress-frozen (a duress signature was observed and not yet cleared); \
             unfreeze requires out_of_band_safety_reattestation signed by the ACTIVE owner key \
             (L2/TRUST_MODEL §10.A.2)"
        );
        // Re-emit C50 (naturally rate-limited by emit_immune_sporocarp's
        // per-detector 1s window so a frozen-state mutation storm can't spam
        // the DAG). No `coerced_owner_suspected` onset event here — the freeze
        // is already latched; re-emitting an onset would muddy the FSM.
        let _ = emit_immune_sporocarp(
            state,
            "C50_coerced_owner_suspected",
            "coerced_owner_suspected",
            &evidence,
        );
        let _ = save_dag_state(state);
        return Ok(Some(build_cosmetic_accept_response(
            state,
            request.request_id,
            &early_mutation_type,
            &content_bytes_for_duress,
        )));
    }

    let client = state
        .python_client
        .as_mut()
        .ok_or_else(|| SubstrateError::Handshake("python worker not connected".to_string()))?;

    // Forward verbatim to Python under a per-op hard timeout.
    // **v3.1.1 Sprint 7.E.2** — a hung Python worker surfaces
    // BridgeError::Timeout instead of wedging the substrate forever; duration
    // is recorded for the Sprint 6.J C65 slow-call observability.
    let timeout = crate::python_call_health::python_op_timeout(msg_type::SUBMIT_MUTATION);
    let call_start = std::time::Instant::now();
    let python_response_result =
        client.call_with_timeout(msg_type::SUBMIT_MUTATION, request.payload.clone(), timeout);
    crate::python_call_health::record_call_duration(call_start.elapsed());
    let python_response = python_response_result.map_err(SubstrateError::Bridge)?;
    if python_response.message_type != msg_type::SUBMIT_MUTATION_RESPONSE {
        return Err(SubstrateError::Protocol(format!(
            "expected submit_mutation_response; got {}",
            python_response.message_type
        )));
    }

    // Parse Python's response.
    let classification = python_response
        .payload
        .get("classification")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let accepted = python_response
        .payload
        .get("accepted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let rejection_reason = python_response
        .payload
        .get("rejection_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let content_bytes = python_response
        .payload
        .get("content_canonical_bytes")
        .and_then(|v| match v {
            Value::Bytes(b) => Some(b.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let mutation_type = python_response
        .payload
        .get("mutation_type")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // M17 P3 永恒进化: read evolution outcome fields from Python's response.
    let schema_apply_attempted = python_response
        .payload
        .get("schema_apply_attempted")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_succeeded = python_response
        .payload
        .get("schema_apply_succeeded")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let schema_apply_failure_reason = python_response
        .payload
        .get("schema_apply_failure_reason")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_op = python_response
        .payload
        .get("schema_apply_op")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();
    let schema_apply_summary = python_response
        .payload
        .get("schema_apply_summary")
        .and_then(|v| match v {
            Value::String(s) => Some(s.clone()),
            _ => None,
        })
        .unwrap_or_default();

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — read the two-phase-migration outcome
    // fields. `migration_mode=true` means the operator requested the multi-cycle
    // two-phase path: Python built a CANDIDATE (deep-copy + apply-to-copy) and
    // LEFT the active gradient unchanged. `candidate_built` says whether that
    // candidate construction succeeded. Both default false (back-compat: the
    // single-cycle path leaves these absent), so a non-migration submit_mutation
    // is byte-unaffected.
    let migration_mode = python_response
        .payload
        .get("migration_mode")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);
    let candidate_built = python_response
        .payload
        .get("candidate_built")
        .and_then(|v| match v {
            Value::Bool(b) => Some(*b),
            _ => None,
        })
        .unwrap_or(false);

    // **M26.4 + M26.3 + M-anchor-5**: rebind acceptance / rejection state as
    // mutable so the M26.4 owner_objective_declaration validation, M26.3
    // compression invariant-set check, AND M-anchor-5 cosign + L0 revision
    // envelope decodes can override Python's `accepted=true` on local
    // validation failure.
    let mut accepted = accepted;
    let mut rejection_reason = rejection_reason;

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — single-in-flight migration guard
    // (MVP). The two-phase path keeps exactly ONE candidate validating at a
    // time; a second `migration_mode=true` schema_evolution while one is
    // outstanding is rejected here at the skin (override Python's accept). This
    // keeps `state.migration_candidate` an unambiguous single Option and the
    // Python-side candidate_gradient single-valued. (A future revision could
    // queue or multiplex migrations; the MVP refuses.)
    if accepted && migration_mode && state.migration_candidate.is_some() {
        accepted = false;
        rejection_reason = format!(
            "a schema migration is already in flight (op={}); the MVP allows \
             only one two-phase migration at a time — abort it (abort_migration) \
             or let its dual-validation window complete before starting another",
            state
                .migration_candidate
                .as_ref()
                .map(|c| c.op_name.clone())
                .unwrap_or_default()
        );
        let _ = emit_immune_sporocarp(
            state,
            "C14_untyped_mutation_blocked",
            "schema_migration_already_in_flight",
            &rejection_reason,
        );
    }

    // **M-anchor-5 §9.2.2 dag_tip_cosign + §9.2.4 l0_revision_attest**: pre-
    // decode the envelopes so the substrate can stage the to-emit DAG event
    // AFTER the mutation:* DAG node is committed. Mirrors the staging
    // pattern used for compression witnesses + owner objective declarations.
    //
    // The CI gate that runs in Python already verified the operator's
    // `attestation_signature` over `content_canonical_bytes`. Post-M-anchor-1
    // the operator signing path routes through anchor_surface_host (owner's
    // Ed25519 key), so that signature IS the owner's signature. We capture
    // it and persist it in the emitted DAG event alongside the envelope so
    // owner-side tooling can re-verify offline.
    let mut staged_cosign: Option<(Vec<u8>, [u8; 64], [u8; 32], [u8; 32])> = None;
    if accepted && mutation_type == "dag_tip_cosign" {
        match crate::events::decode_dag_tip_cosign(&content_bytes) {
            Some((tip_hash, _enum, _proposed, _ts, _nonce)) => {
                let sig_bytes_opt = request
                    .payload
                    .get("attestation_signature")
                    .and_then(|v| match v {
                        Value::Bytes(b) => Some(b.clone()),
                        _ => None,
                    });
                let owner_pk_arr = state
                    .pinned_operator_identity
                    .as_ref()
                    .map(|p| p.pubkey)
                    .unwrap_or([0u8; 32]);
                match sig_bytes_opt {
                    Some(sig_vec) if sig_vec.len() == 64 => {
                        let mut sig_arr = [0u8; 64];
                        sig_arr.copy_from_slice(&sig_vec);
                        staged_cosign = Some((
                            content_bytes.clone(),
                            sig_arr,
                            owner_pk_arr,
                            tip_hash,
                        ));
                    }
                    _ => {
                        accepted = false;
                        rejection_reason =
                            "dag_tip_cosign: missing or malformed attestation_signature"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "dag_tip_cosign_signature_missing_or_malformed",
                        );
                    }
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "dag_tip_cosign canonical-bytes decode failed (wrong domain or shape)"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "dag_tip_cosign_decode_failed",
                );
            }
        }
    }
    let mut staged_l0_revision: Option<(Vec<u8>, [u8; 64], [u8; 32], [u8; 32])> = None;
    if accepted && mutation_type == "l0_revision_attest" {
        match crate::events::decode_l0_revision(&content_bytes) {
            Some((prior_l0_hash, _new, _summary, _ts, _nonce)) => {
                let sig_bytes_opt = request
                    .payload
                    .get("attestation_signature")
                    .and_then(|v| match v {
                        Value::Bytes(b) => Some(b.clone()),
                        _ => None,
                    });
                let owner_pk_arr = state
                    .pinned_operator_identity
                    .as_ref()
                    .map(|p| p.pubkey)
                    .unwrap_or([0u8; 32]);
                match sig_bytes_opt {
                    Some(sig_vec) if sig_vec.len() == 64 => {
                        let mut sig_arr = [0u8; 64];
                        sig_arr.copy_from_slice(&sig_vec);
                        staged_l0_revision = Some((
                            content_bytes.clone(),
                            sig_arr,
                            owner_pk_arr,
                            prior_l0_hash,
                        ));
                    }
                    _ => {
                        accepted = false;
                        rejection_reason =
                            "l0_revision_attest: missing or malformed attestation_signature"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "l0_revision_signature_missing_or_malformed",
                        );
                    }
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "l0_revision_attest canonical-bytes decode failed (wrong domain or shape)"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "l0_revision_decode_failed",
                );
            }
        }
    }

    // **C13 — local federation peer revocation** (L1/GOVERNANCE §5.2 +
    // L2/FEDERATION §6.5.b per-peer OWNER revocation). Same staged-envelope
    // pattern as dag_tip_cosign / l0_revision_attest: the Python CI gate
    // already verified `attestation_signature` over `content_canonical_bytes`
    // against the active owner key, so that signature IS the owner's signature
    // over the revocation body. We decode the body, capture the owner signature
    // + pinned owner pubkey, and emit the `federation_peer_revoked:{prefix}`
    // event AFTER the `mutation:revoke_federation_peer` DAG node commits.
    //
    // A missing/short signature or an undecodable body overrides Python's
    // accept and rejects with C5 (no new HARD_RULES row for the unattested
    // case — C13 is reserved strictly for the egress block).
    //
    // Staged tuple: (revoked_id, revoked_pubkey, reason, anchor_ts_secs,
    //                owner_sig, owner_pubkey).
    let mut staged_peer_revocation: Option<(
        [u8; 32],
        [u8; 32],
        String,
        u64,
        [u8; 64],
        [u8; 32],
    )> = None;
    if accepted && mutation_type == "revoke_federation_peer" {
        match crate::events::decode_revoke_federation_peer(&content_bytes) {
            Some((revoked_id, revoked_pubkey, reason, anchor_ts_secs)) => {
                let sig_bytes_opt = request
                    .payload
                    .get("attestation_signature")
                    .and_then(|v| match v {
                        Value::Bytes(b) => Some(b.clone()),
                        _ => None,
                    });
                let owner_pk_arr = state
                    .pinned_operator_identity
                    .as_ref()
                    .map(|p| p.pubkey)
                    .unwrap_or([0u8; 32]);
                match sig_bytes_opt {
                    Some(sig_vec) if sig_vec.len() == 64 => {
                        let mut sig_arr = [0u8; 64];
                        sig_arr.copy_from_slice(&sig_vec);
                        staged_peer_revocation = Some((
                            revoked_id,
                            revoked_pubkey,
                            reason,
                            anchor_ts_secs,
                            sig_arr,
                            owner_pk_arr,
                        ));
                    }
                    _ => {
                        accepted = false;
                        rejection_reason =
                            "revoke_federation_peer: missing or malformed attestation_signature"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "revoke_federation_peer_signature_missing_or_malformed",
                        );
                    }
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "revoke_federation_peer canonical-bytes decode failed (wrong domain or shape)"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "revoke_federation_peer_decode_failed",
                );
            }
        }
    }

    // **C49 `consensus_floor_bypass`** (L1/HARD_RULES C49; L2/FEDERATION §6.5) —
    // the peer-revocation ACTION site. `revoke_federation_peer` is the LOCAL
    // owner-revocation half of §6.5.b class (1); when the consensus floor is
    // ACTIVE (peer_count ≥ 3), a peer-revocation that another peer would
    // observe as a population claim requires a ≥2/3 quorum certificate. If the
    // floor is active and NO valid `population_consensus_reached:peer_revocation`
    // cert exists in the DAG for THIS revocation's claim (claim_hash = BLAKE3 of
    // the owner-signed revoke body), the action is a floor bypass: reject +
    // fruit C49 + drop the staged revocation so no `federation_peer_revoked`
    // event is emitted. Below the floor (≤2 peers — the v0.9 single-cultivator
    // reality), the owner-attested revoke proceeds unchanged (this gate is a
    // no-op). Stage-1 wires C49 at peer-revocation ONLY; classes 2/3 action
    // sites are Stage 2.
    if accepted && staged_peer_revocation.is_some() {
        let claim_hash = crate::events::claim_hash(&content_bytes);
        if let Err(evidence) = crate::consensus::check_c49_population_action_allowed(
            state,
            crate::events::PopulationClaimClass::PeerRevocation,
            &claim_hash,
        ) {
            accepted = false;
            rejection_reason = evidence.clone();
            staged_peer_revocation = None;
            let _ = emit_immune_sporocarp(
                state,
                "C49_consensus_floor_bypass",
                "consensus_floor_bypass",
                &evidence,
            );
        }
    }

    // **F23 / C50 duress_keypair_registration** (L1/GOVERNANCE F23 + AS §5.6).
    // Same staged-envelope pattern as C13 revoke_federation_peer: Python's CI
    // gate already verified `attestation_signature` over `content_canonical_bytes`
    // against the ACTIVE owner key — that signature IS the owner's signature over
    // the registration body, and it being an active-owner-key signature (NOT a
    // duress-key signature) is the circular-trust guard for MUTATING the
    // registration. We decode the body, REFUSE a duress pubkey equal to the
    // active owner key (the catastrophic-mis-recognition guard), capture the
    // owner signature + pubkey, and emit `duress_keypair_registered:{prefix}`
    // AFTER the `mutation:duress_keypair_registration` DAG node commits.
    //
    // Staged tuple: (duress_pubkey, label, anchor_ts_secs, owner_sig, owner_pubkey).
    let mut staged_duress_registration: Option<([u8; 32], String, u64, [u8; 64], [u8; 32])> = None;
    if accepted && mutation_type == "duress_keypair_registration" {
        match crate::events::decode_duress_keypair_registration(&content_bytes) {
            Some((duress_pubkey, label, anchor_ts_secs)) => {
                let active_owner_pk = state
                    .pinned_operator_identity
                    .as_ref()
                    .map(|p| p.pubkey)
                    .unwrap_or([0u8; 32]);
                if duress_pubkey == active_owner_pk {
                    // Circular self-duress: registering the owner key as a duress
                    // key would make owner signatures verify under a "duress" key
                    // and silently suppress legit mutations. Refuse with C5.
                    accepted = false;
                    rejection_reason =
                        "duress_keypair_registration: duress_pubkey equals the active owner key \
                         (circular self-duress); refused"
                            .to_string();
                    let _ = emit_immune_sporocarp(
                        state,
                        "C5_attestation_invalid",
                        "attestation_invalid",
                        "duress_registration_equals_owner_key",
                    );
                } else {
                    let sig_bytes_opt =
                        request.payload.get("attestation_signature").and_then(|v| match v {
                            Value::Bytes(b) => Some(b.clone()),
                            _ => None,
                        });
                    match sig_bytes_opt {
                        Some(sig_vec) if sig_vec.len() == 64 => {
                            let mut sig_arr = [0u8; 64];
                            sig_arr.copy_from_slice(&sig_vec);
                            staged_duress_registration = Some((
                                duress_pubkey,
                                label,
                                anchor_ts_secs,
                                sig_arr,
                                active_owner_pk,
                            ));
                        }
                        _ => {
                            accepted = false;
                            rejection_reason =
                                "duress_keypair_registration: missing or malformed \
                                 attestation_signature"
                                    .to_string();
                            let _ = emit_immune_sporocarp(
                                state,
                                "C5_attestation_invalid",
                                "attestation_invalid",
                                "duress_registration_signature_missing_or_malformed",
                            );
                        }
                    }
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "duress_keypair_registration canonical-bytes decode failed (wrong domain \
                     or shape)"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "duress_registration_decode_failed",
                );
            }
        }
    }

    // **F23 / C50 out_of_band_safety_reattestation** — the unfreeze attestation.
    // Python's CI gate verified `attestation_signature` against the ACTIVE owner
    // key; a duress-key signature fails that gate (Python returns accepted=false),
    // so reaching here with accepted=true PROVES the active owner key signed it —
    // the circular-trust guard for clearing the freeze. We decode the body,
    // capture the owner signature + pubkey, and stage a `duress_cleared` emission
    // + freeze-flag reset for AFTER the mutation node commits.
    //
    // Staged tuple: (statement, anchor_ts_secs, owner_sig, owner_pubkey).
    let mut staged_duress_clearance: Option<(String, u64, [u8; 64], [u8; 32])> = None;
    if accepted && mutation_type == "out_of_band_safety_reattestation" {
        match crate::events::decode_out_of_band_safety_reattestation(&content_bytes) {
            Some((statement, anchor_ts_secs)) => {
                let owner_pk = state
                    .pinned_operator_identity
                    .as_ref()
                    .map(|p| p.pubkey)
                    .unwrap_or([0u8; 32]);
                let sig_bytes_opt =
                    request.payload.get("attestation_signature").and_then(|v| match v {
                        Value::Bytes(b) => Some(b.clone()),
                        _ => None,
                    });
                match sig_bytes_opt {
                    Some(sig_vec) if sig_vec.len() == 64 => {
                        let mut sig_arr = [0u8; 64];
                        sig_arr.copy_from_slice(&sig_vec);
                        staged_duress_clearance =
                            Some((statement, anchor_ts_secs, sig_arr, owner_pk));
                    }
                    _ => {
                        accepted = false;
                        rejection_reason =
                            "out_of_band_safety_reattestation: missing or malformed \
                             attestation_signature"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "out_of_band_safety_reattestation_signature_missing_or_malformed",
                        );
                    }
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "out_of_band_safety_reattestation canonical-bytes decode failed (wrong \
                     domain or shape)"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "out_of_band_safety_reattestation_decode_failed",
                );
            }
        }
    }

    // **C70 — owner key-rotation FSM** (L1/GOVERNANCE §3.1). The substrate runs
    // a 3-state FSM per pending rotation: request → PENDING_COOLDOWN → veto
    // (VETOED) | activate (ACTIVATED). Python's CI gate already verified the
    // operator `attestation_signature` over `content_canonical_bytes` against
    // the ACTIVE owner key, so reaching here with accepted=true proves the
    // active owner key signed the envelope. The substrate adds the
    // phase-specific guards (current-key binding, single-in-flight, the cooldown
    // veto window → C70, and the SECOND dual-cosign signature on activate that
    // Python does not check). The staged variant is consumed AFTER the
    // `mutation:rotate_owner_key` DAG node commits.
    //
    // Anchor-time MVP: the cooldown is compared against the envelope's
    // operator-supplied anchor timestamps (mirrors the M15 dual-clock nonce
    // times). Verifying the anchor's SIGNATURE over the wall-clock (full F4
    // closure) needs the absent substrate anchor-client — FOLLOW-UP, same gap as
    // the duress heartbeat unfreeze.
    let mut staged_rotation: Option<StagedRotation> = None;
    if accepted && mutation_type == "rotate_owner_key" {
        let active_owner_pk = state
            .pinned_operator_identity
            .as_ref()
            .map(|p| p.pubkey)
            .unwrap_or([0u8; 32]);
        match crate::events::rotate_owner_key_phase(&content_bytes).as_deref() {
            // ---- REQUEST: open the 30-day cooldown veto window ----
            Some(crate::events::ROTATE_PHASE_REQUEST) => {
                match crate::events::decode_rotate_owner_key_request(&content_bytes) {
                    Some((prior, new_pk, request_ts, cooldown_claimed, _nonce)) => {
                        let expected_cooldown =
                            request_ts.saturating_add(crate::events::OWNER_KEY_ROTATION_COOLDOWN_SECS);
                        if state.pending_owner_key_rotation.is_some() {
                            reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key request: a rotation is already pending \
                                 (single-in-flight); veto or activate it first",
                                "rotation_request_single_in_flight",
                            );
                        } else if prior != active_owner_pk {
                            reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key request: prior_active_pubkey does not match \
                                 the current active owner key",
                                "rotation_request_prior_key_mismatch",
                            );
                        } else if new_pk == prior {
                            reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key request: new_pubkey equals the current key \
                                 (no-op rotation refused)",
                                "rotation_request_noop",
                            );
                        } else if cooldown_claimed != expected_cooldown {
                            reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key request: cooldown_expires_at does not equal \
                                 request_anchor_ts + 30d",
                                "rotation_request_cooldown_mismatch",
                            );
                        } else {
                            staged_rotation = Some(StagedRotation::Request {
                                new_pubkey: new_pk,
                                prior_active_pubkey: prior,
                                request_anchor_ts: request_ts,
                                cooldown_expires_at: expected_cooldown,
                            });
                        }
                    }
                    None => reject_rotation(
                        state,
                        &mut accepted,
                        &mut rejection_reason,
                        "rotate_owner_key request: envelope decode failed",
                        "rotation_request_decode_failed",
                    ),
                }
            }
            // ---- VETO: discard a pending candidate within the window ----
            Some(crate::events::ROTATE_PHASE_VETO) => {
                match crate::events::decode_rotate_owner_key_veto(&content_bytes) {
                    Some((veto_new_pk, veto_ts, _nonce)) => {
                        match state.pending_owner_key_rotation.as_ref() {
                            None => reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key veto: no rotation is pending",
                                "rotation_veto_no_pending",
                            ),
                            Some(pending) if veto_new_pk != pending.new_pubkey => {
                                reject_rotation(
                                    state,
                                    &mut accepted,
                                    &mut rejection_reason,
                                    "rotate_owner_key veto: new_pubkey does not match the \
                                     pending rotation",
                                    "rotation_veto_candidate_mismatch",
                                );
                            }
                            Some(pending) if veto_ts >= pending.cooldown_expires_at => {
                                reject_rotation(
                                    state,
                                    &mut accepted,
                                    &mut rejection_reason,
                                    "rotate_owner_key veto: veto after the cooldown window \
                                     elapsed is moot",
                                    "rotation_veto_after_window",
                                );
                            }
                            Some(pending) => {
                                staged_rotation = Some(StagedRotation::Veto {
                                    new_pubkey: pending.new_pubkey,
                                    veto_anchor_ts: veto_ts,
                                });
                            }
                        }
                    }
                    None => reject_rotation(
                        state,
                        &mut accepted,
                        &mut rejection_reason,
                        "rotate_owner_key veto: envelope decode failed",
                        "rotation_veto_decode_failed",
                    ),
                }
            }
            // ---- ACTIVATE: dual-cosign, post-cooldown → rotate ----
            Some(crate::events::ROTATE_PHASE_ACTIVATE) => {
                match crate::events::decode_rotate_owner_key_activate(&content_bytes) {
                    Some((
                        prior,
                        new_pk,
                        _req_ts,
                        cooldown_claimed,
                        activate_ts,
                        _nonce,
                        new_key_cosig,
                        activate_core,
                    )) => {
                        // Verify the SECOND signature: the NEW key over the
                        // activate-core (Python only checked the OLD key over the
                        // full envelope). This is the dual-cosign that proves the
                        // new key holder consents — a stolen-new-key alone cannot
                        // forge the old key's signature, and a stolen-old-key
                        // alone cannot forge the new key's cosignature.
                        let cosig_ok = verify_signature(&new_pk, &new_key_cosig, &activate_core)
                            .is_ok();
                        match state.pending_owner_key_rotation.as_ref() {
                            None => reject_rotation(
                                state,
                                &mut accepted,
                                &mut rejection_reason,
                                "rotate_owner_key activate: no rotation is pending",
                                "rotation_activate_no_pending",
                            ),
                            Some(pending)
                                if new_pk != pending.new_pubkey
                                    || prior != pending.prior_active_pubkey
                                    || cooldown_claimed != pending.cooldown_expires_at =>
                            {
                                reject_rotation(
                                    state,
                                    &mut accepted,
                                    &mut rejection_reason,
                                    "rotate_owner_key activate: envelope parameters do not \
                                     match the pending rotation",
                                    "rotation_activate_param_mismatch",
                                );
                            }
                            Some(_) if !cosig_ok => {
                                reject_rotation(
                                    state,
                                    &mut accepted,
                                    &mut rejection_reason,
                                    "rotate_owner_key activate: new-key cosignature invalid \
                                     (dual-cosign failed)",
                                    "rotation_activate_cosign_invalid",
                                );
                            }
                            Some(pending) if activate_ts < pending.request_anchor_ts => {
                                reject_rotation(
                                    state,
                                    &mut accepted,
                                    &mut rejection_reason,
                                    "rotate_owner_key activate: activate anchor timestamp runs \
                                     backward relative to the request",
                                    "rotation_activate_clock_backward",
                                );
                            }
                            Some(pending) if activate_ts < pending.cooldown_expires_at => {
                                // **C70 rotation_veto_window_violation**: activation
                                // attempted before the 30-day veto window elapsed —
                                // a stolen-new-key takeover trying to skip the veto
                                // window. Reject + fruit C70.
                                accepted = false;
                                rejection_reason = format!(
                                    "C70 rotation_veto_window_violation: rotate_owner_key \
                                     activation at anchor_ts={activate_ts} before the cooldown \
                                     expires at {} (30-day veto window not elapsed)",
                                    pending.cooldown_expires_at
                                );
                                let _ = emit_immune_sporocarp(
                                    state,
                                    "C70_rotation_veto_window_violation",
                                    "rotation_veto_window_violation",
                                    &rejection_reason,
                                );
                            }
                            Some(pending) => {
                                staged_rotation = Some(StagedRotation::Activate {
                                    new_pubkey: pending.new_pubkey,
                                    prior_active_pubkey: pending.prior_active_pubkey,
                                    cooldown_expires_at: pending.cooldown_expires_at,
                                    activate_anchor_ts: activate_ts,
                                });
                            }
                        }
                    }
                    None => reject_rotation(
                        state,
                        &mut accepted,
                        &mut rejection_reason,
                        "rotate_owner_key activate: envelope decode failed",
                        "rotation_activate_decode_failed",
                    ),
                }
            }
            // ---- Unknown / missing phase ----
            _ => reject_rotation(
                state,
                &mut accepted,
                &mut rejection_reason,
                "rotate_owner_key: missing or unknown phase (expected request|veto|activate)",
                "rotation_unknown_phase",
            ),
        }
    }

    // **M26.4 F20 owner_objective_declaration**: decode the OwnerObjective
    // payload before insertion so we can refuse malformed declarations
    // (rejected with C5 attestation_invalid; no DAG churn). Pre-apply
    // staging keeps the latest accepted objective ready to assign to
    // `state.owner_objective` AFTER the mutation DAG node is committed.
    let mut staged_owner_objective: Option<crate::events::OwnerObjective> = None;

    // **v3.1.1 Sprint 2.C set_backup_encryption_status** (L1/SKIN §8): stage
    // the declared status string AFTER validating it lies within
    // `BACKUP_ENCRYPTION_STATUS_VALID_VALUES`. Malformed / unknown status
    // strings are rejected at the skin with C5 — the substrate refuses to
    // record an enum value it doesn't understand, mirroring the
    // owner_objective_declaration discipline.
    let mut staged_backup_encryption_status: Option<(String, Option<String>)> = None;
    if accepted && mutation_type == "set_backup_encryption_status" {
        // Mutation content layout (canonical-bytes Map):
        //   { "status": String, "key_id": String | Null }
        // We decode + extract BOTH fields here because `content_bytes` is
        // moved downstream into the mutation DAG node (so we can't re-decode
        // later after the staged status is consumed for the
        // backup_encryption_status_declared event).
        match myco_kernel_shared::canonical_bytes::decode(&content_bytes) {
            Ok(Value::Map(m)) => {
                let candidate_status = match m.get("status") {
                    Some(Value::String(s)) => Some(s.clone()),
                    _ => None,
                };
                let key_id: Option<String> = match m.get("key_id") {
                    Some(Value::String(s)) => Some(s.clone()),
                    _ => None,
                };
                match candidate_status {
                    Some(status)
                        if crate::events::BACKUP_ENCRYPTION_STATUS_VALID_VALUES
                            .contains(&status.as_str()) =>
                    {
                        staged_backup_encryption_status = Some((status, key_id));
                    }
                    Some(unknown) => {
                        accepted = false;
                        rejection_reason = format!(
                            "set_backup_encryption_status: unknown status {unknown:?}; \
                             allowed: {:?}",
                            crate::events::BACKUP_ENCRYPTION_STATUS_VALID_VALUES
                        );
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "backup_encryption_status_unknown_value",
                        );
                    }
                    None => {
                        accepted = false;
                        rejection_reason =
                            "set_backup_encryption_status: status field missing or not String"
                                .to_string();
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "backup_encryption_status_missing",
                        );
                    }
                }
            }
            _ => {
                accepted = false;
                rejection_reason =
                    "set_backup_encryption_status: content canonical-bytes decode failed"
                        .to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "backup_encryption_status_decode_failed",
                );
            }
        }
    }
    if accepted && mutation_type == "owner_objective_declaration" {
        match crate::events::decode_owner_objective(&content_bytes) {
            Some(obj) => {
                if obj.weights.is_empty() {
                    accepted = false;
                    rejection_reason =
                        "owner_objective_declaration: weights array MUST be non-empty"
                            .to_string();
                    let _ = emit_immune_sporocarp(
                        state,
                        "C5_attestation_invalid",
                        "attestation_invalid",
                        "owner_objective_empty_weights",
                    );
                } else {
                    staged_owner_objective = Some(obj);
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "owner_objective_declaration canonical-bytes decode failed".to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "owner_objective_decode_failed",
                );
            }
        }
    }

    // **M26.3 P10 / P10.b**: BEFORE inserting any DAG node for a
    // compression mutation, verify the CompressionWitness doesn't target any
    // invariant-set member. If it does, override Python's `accepted=true`
    // and emit C51_compression_invariant_corruption. This check MUST happen
    // here in Rust because the invariant set seed lives in Rust events.rs
    // and the DAG (where compressed_node_hashes are resolved to node_types)
    // is Rust-owned. `accepted` + `rejection_reason` are already mutable
    // from the M26.4 rebinding above; just reuse them.
    let mut compression_witness: Option<(String, Vec<[u8; 32]>, Vec<u8>, [u8; 32])> = None;
    if accepted && mutation_type == "compression" {
        match crate::events::decode_compression_witness_minimal(&content_bytes) {
            Some(witness) => {
                let (rule_id, compressed_hashes, _agg, _tip) = &witness;
                let invariant_set = crate::events::seed_compression_invariant_set();
                let current_cycle = state.cycle_counter();
                let mut violation: Option<String> = None;
                for h in compressed_hashes {
                    // Look up node in DAG by hash.
                    let node_opt = state
                        .dag
                        .iter_in_insertion_order()
                        .find(|n| n.hash.as_ref() == h.as_slice());
                    let node = match node_opt {
                        Some(n) => n,
                        None => {
                            violation = Some(format!(
                                "compression witness references node hash not present in DAG"
                            ));
                            break;
                        }
                    };
                    // (a) Forbidden-prefix check.
                    if crate::events::node_type_in_invariant_set(
                        &node.node_type,
                        &invariant_set,
                    ) {
                        violation = Some(format!(
                            "compression targets invariant-set node_type={} (rule_id={})",
                            node.node_type, rule_id
                        ));
                        break;
                    }
                    // (b) Recent-cycles floor check.
                    let age = current_cycle.saturating_sub(node.created_at_cycle);
                    if age < invariant_set.recent_cycles_floor {
                        violation = Some(format!(
                            "compression targets node from cycle {} (age {} < floor {})",
                            node.created_at_cycle, age, invariant_set.recent_cycles_floor
                        ));
                        break;
                    }
                }
                if let Some(reason) = violation {
                    accepted = false;
                    rejection_reason = format!(
                        "P10.b compression_invariant_corruption: {}",
                        reason
                    );
                    // Emit C51 immune sporocarp before continuing the rejection path.
                    let _ = emit_immune_sporocarp(
                        state,
                        "C51_compression_invariant_corruption",
                        "compression_invariant_corruption",
                        &reason,
                    );
                } else {
                    compression_witness = Some(witness);
                }
            }
            None => {
                accepted = false;
                rejection_reason =
                    "compression witness canonical-bytes decode failed".to_string();
                let _ = emit_immune_sporocarp(
                    state,
                    "C5_attestation_invalid",
                    "attestation_invalid",
                    "compression_witness_decode_failed",
                );
            }
        }
    }

    // **v3.1.1 Sprint 8.G**: the mutation:schema_evolution DAG node consumes
    // `content_bytes` (moved into the insert below). The migration branch needs
    // the same bytes (they ARE the schema_diff) for the schema_migration_started
    // event + the CandidateState. Capture a clone ONLY when migration mode is
    // active so the default single-cycle path pays nothing.
    let migration_diff_bytes: Option<Vec<u8>> = if migration_mode && accepted {
        Some(content_bytes.clone())
    } else {
        None
    };

    // If accepted: wrap as DAG node with parent=tip.
    // If rejected: emit an immune sporocarp (M11 C14 for UNTYPED; C5 for invalid CI attestation).
    let dag_node_hash = if accepted {
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let node_type = format!("mutation:{mutation_type}");
        let current_cycle = state.cycle_counter();
        let hash = state
            .dag
            .insert_node(
                parents,
                node_type,
                current_cycle,
                CanonicalBytes(content_bytes),
            )
            .map_err(|e| SubstrateError::Protocol(format!("mutation DAG insert: {e}")))?;
        Some(hash)
    } else {
        // M11: emit immune sporocarp for the rejection.
        let (detector_id, detector_name) = match classification.as_str() {
            "untyped" => ("C14_untyped_mutation_blocked", "untyped_mutation_blocked"),
            "contract_identity_level" => ("C5_attestation_invalid", "attestation_invalid"),
            _ => ("C_unknown", "unknown_breach"),
        };
        let evidence_str = format!(
            "mutation_type={mutation_type}; classification={classification}; reason={rejection_reason}"
        );
        // Best-effort emit; ignore errors (we don't want to mask the original rejection).
        let _ = emit_immune_sporocarp(state, detector_id, detector_name, &evidence_str);
        None
    };

    // **v3.1.1 Sprint 2.C**: after a successful set_backup_encryption_status
    // mutation, commit the staged status to ServerState AND emit a
    // `backup_encryption_status_declared:{status}` DAG event. From this
    // moment forward, boot-time derivation will pick up the new status
    // and suppress `backup_encryption_undeclared` Daily emissions.
    if accepted && staged_backup_encryption_status.is_some() {
        let (status, key_id) =
            staged_backup_encryption_status.expect("guarded by Some check");
        let cycle = state.cycle_counter();
        let body = crate::events::encode_backup_encryption_status_declared(
            &status,
            key_id.as_deref(),
            cycle,
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let nt = crate::events::backup_encryption_status_declared_node_type(&status);
        let _ = state
            .dag
            .insert_node(parents, nt, cycle, body)
            .map_err(|e| {
                SubstrateError::Protocol(format!(
                    "backup_encryption_status_declared DAG insert: {e}"
                ))
            })?;
        state.backup_encryption_status = Some(status);
    }

    // **M26.4 F20**: after a successful owner_objective_declaration, commit
    // the staged objective onto ServerState AND emit an
    // `owner_objective_declared:{objective_id}` DAG event. From this cycle
    // onward, `compute_telos_alignment_cosine` uses the new objective.
    if accepted && staged_owner_objective.is_some() {
        let obj = staged_owner_objective.expect("guarded by Some check");
        let body = crate::events::encode_owner_objective_declared(
            &obj.objective_id,
            obj.declared_at_cycle,
            obj.weights.len() as u64,
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let nt = format!(
            "{}{}",
            crate::events::NODE_TYPE_OWNER_OBJECTIVE_DECLARED_PREFIX,
            obj.objective_id
        );
        let cycle = state.cycle_counter();
        let _ = state
            .dag
            .insert_node(parents, nt, cycle, body)
            .map_err(|e| {
                SubstrateError::Protocol(format!("owner_objective_declared DAG insert: {e}"))
            })?;
        state.owner_objective = Some(obj);
    }

    // **M26.3 P10.c**: after a successful compression mutation, emit the
    // `compression_event:{rule_id}` DAG node (sibling to evolution_succeeded
    // for schema_evolution). The compression_event records the rule_id,
    // compressed_node_hashes, aggregate_summary, and the DAG tip at witness
    // time — the I9 audit trail. Child substrates inheriting via spore-schema
    // (L1/SCHEMA §3.1) replay this and verify P10.b invariant set membership.
    let compression_event_hash = if accepted && compression_witness.is_some() {
        let (rule_id, compressed_hashes, agg_summary, attestation_tip) =
            compression_witness.as_ref().expect("guarded by Some check");
        let event_canonical = crate::events::encode_compression_event(
            rule_id,
            compressed_hashes,
            agg_summary,
            attestation_tip,
            state.cycle_counter(),
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let event_node_type = crate::events::compression_event_node_type(rule_id);
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| {
                SubstrateError::Protocol(format!("compression event DAG insert: {e}"))
            })?;
        Some(h)
    } else {
        None
    };

    // **M-anchor-5 §9.2.2**: after a successful `dag_tip_cosign` mutation,
    // emit `tip_cosigned:{tip_prefix}` DAG event capturing the cosign
    // envelope + owner signature + pubkey. This is the AUDIT TRAIL that lets
    // the owner re-verify offline that "at substrate-cycle N, owner co-signed
    // tip hash 0xABCD..." — making any post-hoc substrate-side rewrite of the
    // sub-chain detectable. The envelope's `enumerated_node_hashes` also
    // pins the in-order history walk, so child substrates inheriting via
    // spore-schema can spot any DAG re-write that violates ordering.
    let tip_cosign_event_hash = if accepted && staged_cosign.is_some() {
        let (envelope_bytes, sig, pubkey, tip_hash) =
            staged_cosign.as_ref().expect("guarded by Some check");
        let event_canonical = crate::events::encode_tip_cosigned_event(
            envelope_bytes,
            sig,
            pubkey,
            state.cycle_counter(),
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let event_node_type = crate::events::tip_cosigned_node_type(tip_hash);
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| {
                SubstrateError::Protocol(format!("tip_cosigned event DAG insert: {e}"))
            })?;
        Some(h)
    } else {
        None
    };

    // **M-anchor-5 §9.2.4**: after a successful `l0_revision_attest`
    // mutation, emit `l0_revision_attested:{prior_l0_hash_prefix}` DAG event
    // capturing the L0-revision envelope + owner signature + pubkey. This is
    // the on-chain anchor that lets the owner prove (offline) "L0 evolved
    // from version X to version Y at substrate-cycle N, here's the diff
    // summary, and here is my signature attesting to that change." Without
    // this event, the substrate could silently shift its doctrine ground
    // truth between sessions; with it, every doctrine revision is anchored
    // into the DAG and any sub-chain rewrite becomes immediately detectable.
    let l0_revision_event_hash = if accepted && staged_l0_revision.is_some() {
        let (envelope_bytes, sig, pubkey, prior_l0_hash) =
            staged_l0_revision.as_ref().expect("guarded by Some check");
        let event_canonical = crate::events::encode_l0_revision_attested_event(
            envelope_bytes,
            sig,
            pubkey,
            state.cycle_counter(),
        );
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let event_node_type = crate::events::l0_revision_attested_node_type(prior_l0_hash);
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| {
                SubstrateError::Protocol(format!("l0_revision_attested event DAG insert: {e}"))
            })?;
        Some(h)
    } else {
        None
    };

    // **C13**: after a successful `revoke_federation_peer` mutation, emit the
    // `federation_peer_revoked:{prefix}` DAG event (owner-attested CRL entry)
    // AND insert the target into `state.revoked_federation_peers`. From this
    // point the federation egress site blocks any envelope to the revoked peer
    // (+ emits C13) and the ingest site drops the revoked peer's events.
    // Idempotent (HashSet + content-hash-idempotent DAG insert).
    // `emit_federation_peer_revoked` returns `Ok(None)` when the peer was
    // already revoked (idempotent no-op); `Option::flatten` collapses that into
    // the `peer_revoked_event_hash` Option uniformly.
    let peer_revoked_event_hash = if accepted && staged_peer_revocation.is_some() {
        let (revoked_id, revoked_pubkey, reason, anchor_ts_secs, owner_sig, owner_pubkey) =
            staged_peer_revocation.as_ref().expect("guarded by Some check");
        crate::federation::handlers::emit_federation_peer_revoked(
            state,
            revoked_id,
            revoked_pubkey,
            reason,
            *anchor_ts_secs,
            owner_sig,
            owner_pubkey,
        )?
    } else {
        None
    };

    // **F23**: after a successful `duress_keypair_registration` mutation, emit
    // the `duress_keypair_registered:{prefix}` DAG event (owner-attested record)
    // AND insert the pubkey into `state.duress_pubkeys`. From this point a
    // signature verifying under that pubkey is recognized as duress. Idempotent
    // at the set level (HashSet) and content-hash-idempotent at the DAG level.
    let duress_registered_event_hash = if accepted && staged_duress_registration.is_some() {
        let (duress_pubkey, label, anchor_ts_secs, owner_sig, owner_pubkey) =
            staged_duress_registration.as_ref().expect("guarded by Some check");
        let nt = crate::events::duress_keypair_registered_node_type(duress_pubkey);
        let content = crate::events::encode_duress_keypair_registered(
            duress_pubkey,
            label,
            *anchor_ts_secs,
            owner_sig,
            owner_pubkey,
        );
        let h = emit_substrate_event(state, nt, content)?;
        state.duress_pubkeys.insert(*duress_pubkey);
        Some(h)
    } else {
        None
    };

    // **F23**: after a successful `out_of_band_safety_reattestation` mutation,
    // emit a `duress_cleared` DAG event AND reset the freeze flag. Reaching here
    // with accepted=true proves the ACTIVE owner key signed the reattestation
    // (Python's CI gate rejects a duress-key signature) — the circular-trust
    // guard. The `duress_cleared` event is the freeze-FSM "off" transition; a
    // later duress observation re-freezes via a fresh `coerced_owner_suspected`.
    let duress_cleared_event_hash = if accepted && staged_duress_clearance.is_some() {
        let (statement, anchor_ts_secs, owner_sig, owner_pubkey) =
            staged_duress_clearance.as_ref().expect("guarded by Some check");
        let content = crate::events::encode_duress_cleared(
            statement,
            *anchor_ts_secs,
            owner_sig,
            owner_pubkey,
        );
        let h = emit_substrate_event(
            state,
            crate::events::NODE_TYPE_DURESS_CLEARED.to_string(),
            content,
        )?;
        state.duress_freeze_active = false;
        Some(h)
    } else {
        None
    };

    // **C70** — after the `mutation:rotate_owner_key` DAG node commits, apply the
    // staged FSM transition: emit the phase event(s) + (on activate) rotate the
    // owner key on BOTH the Python (next-CI-attestation) and Rust (pinned
    // identity → next-boot genesis key) sides, then update
    // `state.pending_owner_key_rotation`. The phase-specific guards (cooldown,
    // dual-cosign, single-in-flight) were all enforced in the decode pass above,
    // so reaching here means the transition is authorized.
    let mut rotation_requested_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    let mut rotation_vetoed_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    let mut owner_key_added_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    let mut owner_key_archived_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    if accepted {
        if let Some(staged) = staged_rotation {
            match staged {
                StagedRotation::Request {
                    new_pubkey,
                    prior_active_pubkey,
                    request_anchor_ts,
                    cooldown_expires_at,
                } => {
                    let content = crate::events::encode_owner_key_rotation_requested(
                        &new_pubkey,
                        &prior_active_pubkey,
                        request_anchor_ts,
                        cooldown_expires_at,
                    );
                    let h = emit_substrate_event(
                        state,
                        crate::events::NODE_TYPE_OWNER_KEY_ROTATION_REQUESTED.to_string(),
                        content,
                    )?;
                    state.pending_owner_key_rotation =
                        Some(crate::events::PendingOwnerKeyRotation {
                            new_pubkey,
                            prior_active_pubkey,
                            request_anchor_ts,
                            cooldown_expires_at,
                            requested_at_cycle: state.cycle_counter(),
                        });
                    rotation_requested_event_hash = Some(h);
                }
                StagedRotation::Veto {
                    new_pubkey,
                    veto_anchor_ts,
                } => {
                    let content = crate::events::encode_owner_key_rotation_vetoed(
                        &new_pubkey,
                        veto_anchor_ts,
                    );
                    let h = emit_substrate_event(
                        state,
                        crate::events::NODE_TYPE_OWNER_KEY_ROTATION_VETOED.to_string(),
                        content,
                    )?;
                    state.pending_owner_key_rotation = None;
                    rotation_vetoed_event_hash = Some(h);
                }
                StagedRotation::Activate {
                    new_pubkey,
                    prior_active_pubkey,
                    cooldown_expires_at,
                    activate_anchor_ts,
                } => {
                    // 1. Rotate Python's owner_keys FIRST — it is the only step
                    //    that can fail (its monotonicity invariant rejects an
                    //    activate timestamp that predates the active key's
                    //    valid_from). Doing it first means a failure leaves NO
                    //    owner_key_added on-chain and the pending rotation intact,
                    //    so the owner can retry with a corrected anchor time
                    //    rather than the substrate ending up in a half-rotated
                    //    state. (In production the anchor clock advances, so a
                    //    legitimate activation never trips this.)
                    let rotate_result = match state.python_client.as_mut() {
                        Some(client) => client.apply_owner_key_rotation(
                            &prior_active_pubkey,
                            &new_pubkey,
                            activate_anchor_ts,
                            cooldown_expires_at,
                        ),
                        None => Ok(()),
                    };
                    if let Err(e) = rotate_result {
                        accepted = false;
                        rejection_reason = format!(
                            "rotate_owner_key activate: Python owner_keys rotation \
                             rejected (likely a non-monotonic anchor timestamp): {e}"
                        );
                        let _ = emit_immune_sporocarp(
                            state,
                            "C5_attestation_invalid",
                            "attestation_invalid",
                            "rotation_activate_python_apply_failed",
                        );
                    } else {
                        // 2. owner_key_added(new) + owner_key_archived(prior) — the
                        //    on-chain audit trail (the positive witness that
                        //    replaces the former acknowledged-debt sentinel).
                        let added = crate::events::encode_owner_key_added(
                            &new_pubkey,
                            &prior_active_pubkey,
                            activate_anchor_ts,
                        );
                        let h_added = emit_substrate_event(
                            state,
                            crate::events::NODE_TYPE_OWNER_KEY_ADDED.to_string(),
                            added,
                        )?;
                        let archived = crate::events::encode_owner_key_archived(
                            &prior_active_pubkey,
                            activate_anchor_ts,
                        );
                        let h_archived = emit_substrate_event(
                            state,
                            crate::events::NODE_TYPE_OWNER_KEY_ARCHIVED.to_string(),
                            archived,
                        )?;
                        owner_key_added_event_hash = Some(h_added);
                        owner_key_archived_event_hash = Some(h_archived);

                        // 3. Rotate Rust's pinned identity (identity continuity:
                        //    keep first_pinned_unix_ns; only the pubkey changes).
                        //    This is also what the next boot hands Python as the
                        //    genesis owner key, so the rotation survives a restart.
                        if let Some(pinned) = state.pinned_operator_identity.as_mut() {
                            pinned.pubkey = new_pubkey;
                        }

                        // 4. Close out the FSM.
                        state.pending_owner_key_rotation = None;
                    }
                }
            }
        }
    }

    // M17 P3 永恒进化: after mutation acceptance, emit the evolution event DAG node.
    // - schema_apply_attempted + schema_apply_succeeded → evolution_succeeded:{op}
    // - schema_apply_attempted + !schema_apply_succeeded → evolution_failed:{op}
    //   (mutation:schema_evolution still in DAG as audit trail of the attempt.)
    let evolution_event_hash = if schema_apply_attempted {
        let event_node_type = if schema_apply_succeeded {
            format!("evolution_succeeded:{schema_apply_op}")
        } else {
            format!("evolution_failed:{schema_apply_op}")
        };
        let mut event_map = BTreeMap::new();
        event_map.insert("op".to_string(), Value::String(schema_apply_op.clone()));
        event_map.insert("succeeded".to_string(), Value::Bool(schema_apply_succeeded));
        event_map.insert(
            "summary".to_string(),
            Value::String(schema_apply_summary.clone()),
        );
        if !schema_apply_succeeded {
            event_map.insert(
                "failure_reason".to_string(),
                Value::String(schema_apply_failure_reason.clone()),
            );
        }
        let event_canonical = cb_encode(&Value::Map(event_map))
            .map_err(|e| SubstrateError::Protocol(format!("evolution event encode: {e}")))?;
        let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
            Some(t) => vec![t],
            None => Vec::new(),
        };
        let cycle = state.cycle_counter();
        let h = state
            .dag
            .insert_node(parents, event_node_type, cycle, event_canonical)
            .map_err(|e| SubstrateError::Protocol(format!("evolution event DAG insert: {e}")))?;
        Some(h)
    } else {
        None
    };

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — two-phase migration branch.
    //
    // Reached only when the operator opted in (`migration_mode=true`) and the
    // mutation was ACCEPTED (CI attestation passed + not blocked by the
    // single-in-flight guard above). Python has already built the candidate
    // (deep-copy + apply-to-copy) and left the active gradient unchanged.
    //
    //   candidate_built=true  → open the dual-validation window: construct a
    //     CandidateState, store it on ServerState, emit
    //     schema_migration_started:{op}. We do NOT emit evolution_succeeded
    //     yet — that fires on commit, cycles later. (schema_apply_attempted is
    //     false in migration mode, so the M17 block above did not fire either.)
    //   candidate_built=false → the apply-to-copy itself failed (e.g. the diff
    //     references a missing axis). There is nothing to validate, so we go
    //     straight to the rollback terminal: emit schema_migration_rolled_back
    //     + the legacy evolution_failed sibling. No candidate is stored.
    let mut migration_started_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    let mut migration_rolled_back_event_hash: Option<myco_kernel_shared::crypto::NodeHash> = None;
    if accepted && migration_mode {
        let op = schema_apply_op.clone();
        let window = myco_kernel_schema::migration::DEFAULT_DUAL_VALIDATION_WINDOW_CYCLES;
        let cycle = state.cycle_counter();
        // The schema_diff bytes captured before the mutation node consumed
        // `content_bytes`. `migration_mode && accepted` guarantees this is Some.
        let diff_bytes = migration_diff_bytes.clone().unwrap_or_default();
        if candidate_built {
            // Construct the CandidateState (the diff bytes are the mutation
            // content) and move it straight into the Validating phase, starting
            // the window at the current cycle.
            let mut candidate = myco_kernel_schema::migration::CandidateState::new(
                diff_bytes.clone(),
                op.clone(),
                cycle,
                window,
            );
            candidate.enter_validating(cycle);
            let started_at_unix_ns = candidate.started_at_unix_ns;
            state.migration_candidate = Some(candidate);

            let content = crate::events::encode_schema_migration_started(
                &op,
                &diff_bytes,
                cycle,
                window,
                started_at_unix_ns,
            );
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let nt = crate::events::schema_migration_started_node_type(&op);
            let h = state
                .dag
                .insert_node(parents, nt, cycle, content)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("schema_migration_started DAG insert: {e}"))
                })?;
            migration_started_event_hash = Some(h);
        } else {
            // Candidate construction failed → terminal rollback now.
            let reason = if schema_apply_failure_reason.is_empty() {
                "migration candidate construction failed (apply-to-copy error)".to_string()
            } else {
                schema_apply_failure_reason.clone()
            };
            let content =
                crate::events::encode_schema_migration_rolled_back(&op, &reason, cycle);
            let parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let nt = crate::events::schema_migration_rolled_back_node_type(&op);
            let h = state.dag.insert_node(parents, nt, cycle, content).map_err(|e| {
                SubstrateError::Protocol(format!(
                    "schema_migration_rolled_back DAG insert: {e}"
                ))
            })?;
            migration_rolled_back_event_hash = Some(h);

            // Legacy evolution_failed:{op} sibling (back-compat).
            let mut ev_map = BTreeMap::new();
            ev_map.insert("op".to_string(), Value::String(op.clone()));
            ev_map.insert("succeeded".to_string(), Value::Bool(false));
            ev_map.insert(
                "summary".to_string(),
                Value::String("two-phase migration candidate build failed".to_string()),
            );
            ev_map.insert("failure_reason".to_string(), Value::String(reason));
            let ev_canonical = cb_encode(&Value::Map(ev_map)).map_err(|e| {
                SubstrateError::Protocol(format!("legacy evolution event encode: {e}"))
            })?;
            let ev_parents: Vec<myco_kernel_shared::crypto::NodeHash> = match state.dag.tip() {
                Some(t) => vec![t],
                None => Vec::new(),
            };
            let _ = state
                .dag
                .insert_node(ev_parents, format!("evolution_failed:{op}"), cycle, ev_canonical)
                .map_err(|e| {
                    SubstrateError::Protocol(format!("legacy evolution_failed DAG insert: {e}"))
                })?;
        }
    }

    // **v3.1.1 Sprint 8.G (P03 §10.4)** — operator-initiated abort. An accepted
    // `abort_migration` CI mutation forces the rollback path for the in-flight
    // migration (Python abort_migration + schema_migration_rolled_back + legacy
    // evolution_failed sibling + clear the candidate). No-op if no migration is
    // in flight (the mutation is still recorded as a mutation:abort_migration
    // DAG node above, but there is nothing to roll back).
    if accepted && mutation_type == "abort_migration" {
        if let Some(op) = state.migration_candidate.as_ref().map(|c| c.op_name.clone()) {
            let reason = "operator-initiated abort_migration (CI mutation)".to_string();
            if let Err(e) = crate::ingest::force_migration_rollback(state, &op, &reason) {
                let _ = emit_immune_sporocarp(
                    state,
                    "C31_cycle_step_failed",
                    "cycle_step_failed",
                    &format!("operator abort_migration (op={op}) failed: {e}"),
                );
            }
        }
    }

    // Build response to operator.
    let mut payload = BTreeMap::new();
    payload.insert("classification".to_string(), Value::String(classification));
    payload.insert("accepted".to_string(), Value::Bool(accepted));
    payload.insert(
        "rejection_reason".to_string(),
        Value::String(rejection_reason),
    );
    payload.insert("mutation_type".to_string(), Value::String(mutation_type));
    if let Some(h) = dag_node_hash {
        payload.insert(
            "dag_node_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // M17 evolution fields surfaced to operator.
    payload.insert(
        "schema_apply_attempted".to_string(),
        Value::Bool(schema_apply_attempted),
    );
    payload.insert(
        "schema_apply_succeeded".to_string(),
        Value::Bool(schema_apply_succeeded),
    );
    payload.insert(
        "schema_apply_failure_reason".to_string(),
        Value::String(schema_apply_failure_reason),
    );
    payload.insert(
        "schema_apply_op".to_string(),
        Value::String(schema_apply_op),
    );
    payload.insert(
        "schema_apply_summary".to_string(),
        Value::String(schema_apply_summary),
    );
    if let Some(h) = evolution_event_hash {
        payload.insert(
            "evolution_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **M26.3**: surface the compression_event hash so operator can verify
    // emission landed in the DAG.
    if let Some(h) = compression_event_hash {
        payload.insert(
            "compression_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **M-anchor-5 §9.2.2 / §9.2.4**: surface the two new anchor-attestation
    // event hashes so the operator side can index them for offline replay /
    // owner-side independent verification.
    if let Some(h) = tip_cosign_event_hash {
        payload.insert(
            "tip_cosign_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = l0_revision_event_hash {
        payload.insert(
            "l0_revision_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **C13** — surface the federation_peer_revoked event hash so the operator
    // side can index the on-chain CRL entry / confirm the revocation landed.
    if let Some(h) = peer_revoked_event_hash {
        payload.insert(
            "federation_peer_revoked_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **F23** — surface the duress-registration / duress-clearance event hashes
    // so owner-side tooling can confirm a genuine (owner-attested) registration
    // or unfreeze landed on-chain. These attach ONLY to the genuine
    // (Python-CI-accepted, active-owner-key-signed) path — a duress-suppressed
    // mutation returns via the cosmetic-accept path far above and never reaches
    // this response builder.
    if let Some(h) = duress_registered_event_hash {
        payload.insert(
            "duress_keypair_registered_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = duress_cleared_event_hash {
        payload.insert(
            "duress_cleared_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **C70** — surface the rotation-FSM event hashes so the operator side can
    // index them / confirm the transition landed on-chain.
    if let Some(h) = rotation_requested_event_hash {
        payload.insert(
            "owner_key_rotation_requested_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = rotation_vetoed_event_hash {
        payload.insert(
            "owner_key_rotation_vetoed_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = owner_key_added_event_hash {
        payload.insert(
            "owner_key_added_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = owner_key_archived_event_hash {
        payload.insert(
            "owner_key_archived_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    // **v3.1.1 Sprint 8.G (P03 §10.4)** — surface migration outcome so the
    // operator can distinguish "started a window" from "applied in one cycle".
    payload.insert("migration_mode".to_string(), Value::Bool(migration_mode));
    payload.insert("candidate_built".to_string(), Value::Bool(candidate_built));
    if let Some(h) = migration_started_event_hash {
        payload.insert(
            "schema_migration_started_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }
    if let Some(h) = migration_rolled_back_event_hash {
        payload.insert(
            "schema_migration_rolled_back_event_hash".to_string(),
            Value::Bytes(h.as_ref().to_vec()),
        );
    }

    Ok(Some(Message::new(
        msg_type::SUBMIT_MUTATION_RESPONSE,
        request.request_id,
        payload,
    )))
}
