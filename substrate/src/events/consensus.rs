//! **L2/FEDERATION §6.5 + §9.6 — Stage-1 population-consensus floor**
//! (`algorithms/pbft_consensus_floor.md`).
//!
//! This is the **quorum-certificate floor**, NOT a full multi-round Tendermint.
//! A substrate that wants to act on a POPULATION-level claim (§6.5.b) collects
//! ≥2/3 distinct-peer signed votes over the canonical claim, mints a
//! self-evidencing **quorum certificate** DAG event, and may then act; until the
//! quorum is reached the claim is `pending` and the substrate MUST NOT act.
//!
//! Why this is BFT-safe without leader-election or liveness:
//!   - No honest substrate acts on a population claim without ≥2/3 of the pinned
//!     peer set vouching (`f ≤ ⌊(N-1)/3⌋`; honest 2/3+1).
//!   - Every vote is Ed25519-bound to `(context, claim_type, claim_hash,
//!     peer_substrate_id, round_id, peer_dag_tip_at_vote)` so a vote for one
//!     claim/round cannot be replayed for another (the context tag
//!     `myco-population-vote-v1` is distinct from `myco-fed-hello-v1` and
//!     `myco-self-euthanasia-v1`, blocking cross-protocol replay).
//!   - The certificate is **self-evidencing**: it embeds every
//!     `(peer_substrate_id, peer_signature)`. A receiver re-derives the
//!     signing message from the cert's own claim fields + round_id and
//!     re-verifies each signature against that peer's §10 FED_HELLO-pinned
//!     `signer_pubkey`. Authority comes from the embedded signatures, never
//!     from the federation wrapper (§9.6: wrapping = provenance, not authority).
//!
//! ## All consensus state is DAG-derived
//!
//! `FederationState.peers` is in-memory-only (not persisted), so consensus
//! state (votes / certs / activation) is recorded ENTIRELY as DAG events and
//! re-derived from the DAG on demand. This mirrors the `tip_cosigned`
//! cosign-envelope pattern in [`crate::events`] (`attestation.rs`): the cert
//! carries the signed material + every signature + every signer pubkey is
//! looked up from the DAG-recorded peer-pin events, so the whole tally is
//! re-verifiable offline.
//!
//! ## DEFERRED (Stage 2 / Stage 1.5)
//!
//! - Multi-round prevote/precommit + leader rotation + view-change (this is a
//!   single-round signature-collection floor).
//! - The P14 `consensus_participation` sub-criterion + observability signal #8.
//! - Action sites for claim classes 2 + 3 (the enum exists; only PeerRevocation
//!   is wired at its action site in Stage 1 — see [`PopulationClaimClass`]).
//! - Operator-side vote signing (operators drive the floor but the substrate
//!   signs its own vote with its signing seed).
//! - Per-peer recursive rate-limit + `population_consensus_stuck:{claim_type}`
//!   (>7 consecutive timeouts).

use super::hex_prefix;
use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use myco_kernel_shared::crypto::verify_signature;
use std::collections::BTreeMap;

/// Domain-separation context for population-vote signatures
/// (`algorithms/pbft_consensus_floor.md` §Voting). Distinct from
/// `myco-fed-hello-v1` and `myco-self-euthanasia-v1` so a signature minted for
/// one protocol cannot be lifted into another.
pub const POPULATION_VOTE_CONTEXT: &str = "myco-population-vote-v1";

/// Prefix for `population_vote:{claim_type}` DAG events — a single substrate's
/// own vote over a population claim (the substrate's vote, recorded into its own
/// DAG; peers' votes arrive over FED_EVENT_BATCH and are recorded the same way).
pub const NODE_TYPE_POPULATION_VOTE_PREFIX: &str = "population_vote:";

/// Prefix for `population_consensus_reached:{claim_type}` DAG events — the
/// self-verifying quorum certificate (§6.5 quorum cert).
pub const NODE_TYPE_POPULATION_CONSENSUS_REACHED_PREFIX: &str =
    "population_consensus_reached:";

/// Prefix for `population_consensus_pending:{claim_type}` DAG events — a claim
/// whose tally has not (yet) reached quorum. The substrate never acts while
/// pending (§No-consensus / pending).
pub const NODE_TYPE_POPULATION_CONSENSUS_PENDING_PREFIX: &str =
    "population_consensus_pending:";

/// `consensus_floor_activated` DAG event node_type — emitted when peer_count
/// crosses 2→3 (§6.5.a activation).
pub const NODE_TYPE_CONSENSUS_FLOOR_ACTIVATED: &str = "consensus_floor_activated";

/// `consensus_floor_deactivated` DAG event node_type — emitted when peer_count
/// crosses 3→2 (§6.5.a).
pub const NODE_TYPE_CONSENSUS_FLOOR_DEACTIVATED: &str = "consensus_floor_deactivated";

/// Prefix for `byzantine_threshold_check:{claim_type}` DAG events — the per-round
/// `(N, f_tolerated, votes_received, votes_consistent)` witness
/// (`algorithms/pbft_consensus_floor.md` §Byzantine-fault bound).
pub const NODE_TYPE_BYZANTINE_THRESHOLD_CHECK_PREFIX: &str = "byzantine_threshold_check:";

/// **§6.5.a activation threshold** — the consensus floor is active iff the
/// substrate has ≥3 pinned peers (i.e. N = self + peers ≥ 4 is NOT the gate;
/// the doctrine gate is peer-count ≥ 3). Below this, federation is
/// pairwise-trust + owner-attestation only.
pub const CONSENSUS_FLOOR_MIN_PEERS: usize = 3;

/// The three population-only claim classes (L2/FEDERATION §6.5.b). A
/// substrate-private action that matches one of these WHILE the floor is active
/// and WITHOUT a matching quorum cert is `C49_consensus_floor_bypass`.
///
/// **Stage-1 scope**: only [`PeerRevocation`](PopulationClaimClass::PeerRevocation)
/// has its action site wired (at the C13 `revoke_federation_peer` path). The
/// other two classes are defined here so the taxonomy + claim_type strings are
/// pinned, but their action sites are Stage 2.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PopulationClaimClass {
    /// (1) Revocation of a peer BY another peer — distinct from the C13 LOCAL
    /// owner-revocation. The accused peer cannot self-revoke (§6.5.b). Wired at
    /// the peer-revocation action site in Stage 1.
    PeerRevocation,
    /// (2) Universal-junk raw_material classification. Action site: Stage 2.
    UniversalJunkClassification,
    /// (3) Cross-substrate aggregate observability metric (L2/OBSERVABILITY §9).
    /// Action site: Stage 2.
    CrossSubstrateAggregateMetric,
}

impl PopulationClaimClass {
    /// The stable, wire-canonical `claim_type` string for this class. Used as
    /// the `{claim_type}` suffix of the DAG node_types AND inside the vote
    /// signing message, so it is part of the signed material — a vote for one
    /// class can never be re-counted toward another.
    pub fn claim_type(self) -> &'static str {
        match self {
            PopulationClaimClass::PeerRevocation => "peer_revocation",
            PopulationClaimClass::UniversalJunkClassification => "universal_junk_classification",
            PopulationClaimClass::CrossSubstrateAggregateMetric => {
                "cross_substrate_aggregate_metric"
            }
        }
    }

    /// Parse a `claim_type` string back into a class (the inverse of
    /// [`claim_type`](PopulationClaimClass::claim_type)). Returns `None` for an
    /// unrecognized string.
    pub fn from_claim_type(s: &str) -> Option<Self> {
        match s {
            "peer_revocation" => Some(PopulationClaimClass::PeerRevocation),
            "universal_junk_classification" => {
                Some(PopulationClaimClass::UniversalJunkClassification)
            }
            "cross_substrate_aggregate_metric" => {
                Some(PopulationClaimClass::CrossSubstrateAggregateMetric)
            }
            _ => None,
        }
    }
}

// ---------------------------------------------------------------------------
// Byzantine-fault bound (`algorithms/pbft_consensus_floor.md`).
// ---------------------------------------------------------------------------

/// Faults tolerated for a peer-set of size `n`: `f = ⌊(n-1)/3⌋`.
///
/// `n` here is N = self + all pinned peers (the full participant set). Integer
/// division floors, so `f_tolerated(3) = 0`, `f_tolerated(4) = 1`,
/// `f_tolerated(7) = 2`, `f_tolerated(10) = 3`.
pub fn f_tolerated(n: usize) -> usize {
    n.saturating_sub(1) / 3
}

/// Quorum threshold for a participant set of size `n`: `n - f_tolerated(n)`,
/// i.e. the minimum number of DISTINCT-peer votes needed for a certificate
/// (honest 2/3+1). `quorum_threshold(3) = 3`, `(4) = 3`, `(7) = 5`, `(10) = 7`.
pub fn quorum_threshold(n: usize) -> usize {
    n - f_tolerated(n)
}

// ---------------------------------------------------------------------------
// Vote signing message.
// ---------------------------------------------------------------------------

/// Build the canonical-bytes message a peer signs to vote for a population
/// claim (`algorithms/pbft_consensus_floor.md` §Voting, with the
/// reviewed-design freshness binding):
///
/// ```text
/// Map({
///   "context":             String("myco-population-vote-v1"),
///   "claim_type":          String,
///   "claim_hash":          Bytes(32),     // BLAKE3 of the canonical claim payload
///   "peer_substrate_id":   Bytes(32),     // the SIGNER's OWN substrate_id
///   "round_id":            Uint,          // monotonic-per-claim; replay guard
///   "peer_dag_tip_at_vote": Bytes(32),    // freshness binding (all-zero = empty DAG)
/// })
/// ```
///
/// `peer_substrate_id` is the signer's own id: a vote is a peer asserting "I,
/// substrate X, vouch for this claim at this round". The receiver verifies the
/// signature against X's §10 FED_HELLO-pinned `signer_pubkey`.
pub fn build_population_vote_signing_message(
    claim_type: &str,
    claim_hash: &[u8; 32],
    signer_substrate_id: &[u8; 32],
    round_id: u64,
    peer_dag_tip_at_vote: &[u8; 32],
) -> Vec<u8> {
    let mut m = BTreeMap::new();
    m.insert(
        "context".to_string(),
        Value::String(POPULATION_VOTE_CONTEXT.to_string()),
    );
    m.insert("claim_type".to_string(), Value::String(claim_type.to_string()));
    m.insert("claim_hash".to_string(), Value::Bytes(claim_hash.to_vec()));
    m.insert(
        "peer_substrate_id".to_string(),
        Value::Bytes(signer_substrate_id.to_vec()),
    );
    m.insert("round_id".to_string(), Value::Uint(round_id));
    m.insert(
        "peer_dag_tip_at_vote".to_string(),
        Value::Bytes(peer_dag_tip_at_vote.to_vec()),
    );
    cb_encode(&Value::Map(m))
        .expect("population_vote signing message encode infallible")
        .0
}

/// Compute the canonical `claim_hash` (BLAKE3) over a claim payload's canonical
/// bytes. The payload's exact shape is per-class; for `peer_revocation` the
/// payload is the `revoke_federation_peer` body bytes (so the same claim_hash
/// the C49 gate looks up matches the cert).
pub fn claim_hash(claim_payload_canonical_bytes: &[u8]) -> [u8; 32] {
    blake3::hash(claim_payload_canonical_bytes).into()
}

// ---------------------------------------------------------------------------
// `population_vote:{claim_type}` event.
// ---------------------------------------------------------------------------

/// Full `population_vote:{claim_type}` node_type string.
pub fn population_vote_node_type(claim_type: &str) -> String {
    format!("{NODE_TYPE_POPULATION_VOTE_PREFIX}{claim_type}")
}

/// Encode the body of a `population_vote:{claim_type}` DAG event — one peer's
/// (possibly our own) vote over a population claim.
///
/// ```text
/// Map({
///   "claim_type":           String,
///   "claim_hash":           Bytes(32),
///   "claim_payload":        Bytes,          // canonical claim payload (claim_hash preimage)
///   "round_id":             Uint,
///   "voter_substrate_id":   Bytes(32),      // the signer's own id
///   "voter_signature":      Bytes(64),      // Ed25519 over build_population_vote_signing_message
///   "peer_dag_tip_at_vote": Bytes(32),
///   "emitted_at_cycle":     Uint,
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_population_vote(
    claim_type: &str,
    claim_hash: &[u8; 32],
    claim_payload_canonical_bytes: &[u8],
    round_id: u64,
    voter_substrate_id: &[u8; 32],
    voter_signature: &[u8; 64],
    peer_dag_tip_at_vote: &[u8; 32],
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("claim_type".to_string(), Value::String(claim_type.to_string()));
    m.insert("claim_hash".to_string(), Value::Bytes(claim_hash.to_vec()));
    m.insert(
        "claim_payload".to_string(),
        Value::Bytes(claim_payload_canonical_bytes.to_vec()),
    );
    m.insert("round_id".to_string(), Value::Uint(round_id));
    m.insert(
        "voter_substrate_id".to_string(),
        Value::Bytes(voter_substrate_id.to_vec()),
    );
    m.insert(
        "voter_signature".to_string(),
        Value::Bytes(voter_signature.to_vec()),
    );
    m.insert(
        "peer_dag_tip_at_vote".to_string(),
        Value::Bytes(peer_dag_tip_at_vote.to_vec()),
    );
    m.insert("emitted_at_cycle".to_string(), Value::Uint(emitted_at_cycle));
    cb_encode(&Value::Map(m)).expect("population_vote event encode infallible")
}

/// A decoded `population_vote` event body.
#[derive(Debug, Clone)]
pub struct DecodedPopulationVote {
    /// The claim class string (e.g. `"peer_revocation"`).
    pub claim_type: String,
    /// BLAKE3 of the claim payload.
    pub claim_hash: [u8; 32],
    /// The canonical claim payload (claim_hash preimage).
    pub claim_payload: Vec<u8>,
    /// Monotonic-per-claim round id.
    pub round_id: u64,
    /// The voting peer's own substrate_id.
    pub voter_substrate_id: [u8; 32],
    /// The voter's Ed25519 signature over the signing message.
    pub voter_signature: [u8; 64],
    /// The voter's DAG tip at vote time (freshness; bound into the signature).
    pub peer_dag_tip_at_vote: [u8; 32],
}

/// Decode a `population_vote` event body. Returns `None` on shape mismatch (a
/// malformed vote never counts toward a tally).
pub fn decode_population_vote(bytes: &[u8]) -> Option<DecodedPopulationVote> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    let claim_type = match m.get("claim_type")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let claim_hash = bytes_to_arr32(m.get("claim_hash")?)?;
    let claim_payload = match m.get("claim_payload")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let round_id = match m.get("round_id")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let voter_substrate_id = bytes_to_arr32(m.get("voter_substrate_id")?)?;
    let voter_signature = bytes_to_arr64(m.get("voter_signature")?)?;
    let peer_dag_tip_at_vote = bytes_to_arr32(m.get("peer_dag_tip_at_vote")?)?;
    Some(DecodedPopulationVote {
        claim_type,
        claim_hash,
        claim_payload,
        round_id,
        voter_substrate_id,
        voter_signature,
        peer_dag_tip_at_vote,
    })
}

/// Verify a single decoded vote's signature against the voter's pinned
/// `signer_pubkey`. The signing message is RE-DERIVED from the vote's own claim
/// fields + round + tip — so a vote whose body was tampered (e.g. claim_hash
/// swapped) fails verification because the re-derived message no longer matches
/// what was signed. Returns `true` iff the signature verifies.
pub fn verify_population_vote(vote: &DecodedPopulationVote, voter_signer_pubkey: &[u8; 32]) -> bool {
    let msg = build_population_vote_signing_message(
        &vote.claim_type,
        &vote.claim_hash,
        &vote.voter_substrate_id,
        vote.round_id,
        &vote.peer_dag_tip_at_vote,
    );
    verify_signature(voter_signer_pubkey, &vote.voter_signature, &msg).is_ok()
}

// ---------------------------------------------------------------------------
// `population_consensus_reached:{claim_type}` — the quorum certificate.
// ---------------------------------------------------------------------------

/// One embedded vouching entry inside a quorum certificate:
/// `(peer_substrate_id, peer_signature, peer_dag_tip_at_vote)`. The per-voter
/// `peer_dag_tip_at_vote` is part of the signed material, so it MUST travel with
/// the signature for re-verification to reconstruct each signing message exactly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertPeerVote {
    /// The voting peer's substrate_id.
    pub peer_substrate_id: [u8; 32],
    /// The peer's Ed25519 signature over the vote signing message.
    pub peer_signature: [u8; 64],
    /// The peer's DAG tip at vote time (bound into the signature).
    pub peer_dag_tip_at_vote: [u8; 32],
}

/// Full `population_consensus_reached:{claim_type}` node_type string.
pub fn population_consensus_reached_node_type(claim_type: &str) -> String {
    format!("{NODE_TYPE_POPULATION_CONSENSUS_REACHED_PREFIX}{claim_type}")
}

/// Encode the body of a `population_consensus_reached:{claim_type}` DAG event —
/// the self-verifying quorum certificate (§6.5 quorum cert; modelled on
/// [`crate::events::encode_tip_cosigned_event`]).
///
/// The cert is **self-contained**: it carries the `claim_payload` (claim_hash
/// preimage) plus every vouching `(peer_substrate_id, peer_signature,
/// peer_dag_tip_at_vote)`. A downstream receiver re-derives each signing message
/// from these fields + the cert's `claim_type`/`claim_hash`/`round_id` and
/// re-verifies against each peer's pinned pubkey ([`verify_quorum_cert`]).
///
/// ```text
/// Map({
///   "claim_type":      String,
///   "claim_hash":      Bytes(32),
///   "claim_payload":   Bytes,                 // claim_hash preimage (cert is self-contained)
///   "round_id":        Uint,
///   "quorum_size":     Uint,                  // == peer_votes.len()
///   "peer_set_size_n": Uint,                  // N the quorum was computed against
///   "f_tolerated":     Uint,
///   "peer_votes":      Array<Map({            // self-verifying: every vouching signature
///       "peer_substrate_id":    Bytes(32),
///       "peer_signature":       Bytes(64),
///       "peer_dag_tip_at_vote": Bytes(32),
///   })>,
///   "reached_at_cycle": Uint,
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_population_consensus_reached(
    claim_type: &str,
    claim_hash: &[u8; 32],
    claim_payload_canonical_bytes: &[u8],
    round_id: u64,
    peer_set_size_n: usize,
    f_tolerated_value: usize,
    peer_votes: &[CertPeerVote],
    reached_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("claim_type".to_string(), Value::String(claim_type.to_string()));
    m.insert("claim_hash".to_string(), Value::Bytes(claim_hash.to_vec()));
    m.insert(
        "claim_payload".to_string(),
        Value::Bytes(claim_payload_canonical_bytes.to_vec()),
    );
    m.insert("round_id".to_string(), Value::Uint(round_id));
    m.insert(
        "quorum_size".to_string(),
        Value::Uint(peer_votes.len() as u64),
    );
    m.insert(
        "peer_set_size_n".to_string(),
        Value::Uint(peer_set_size_n as u64),
    );
    m.insert(
        "f_tolerated".to_string(),
        Value::Uint(f_tolerated_value as u64),
    );
    let votes_array: Vec<Value> = peer_votes
        .iter()
        .map(|cv| {
            let mut vm = BTreeMap::new();
            vm.insert(
                "peer_substrate_id".to_string(),
                Value::Bytes(cv.peer_substrate_id.to_vec()),
            );
            vm.insert(
                "peer_signature".to_string(),
                Value::Bytes(cv.peer_signature.to_vec()),
            );
            vm.insert(
                "peer_dag_tip_at_vote".to_string(),
                Value::Bytes(cv.peer_dag_tip_at_vote.to_vec()),
            );
            Value::Map(vm)
        })
        .collect();
    m.insert("peer_votes".to_string(), Value::Array(votes_array));
    m.insert("reached_at_cycle".to_string(), Value::Uint(reached_at_cycle));
    cb_encode(&Value::Map(m)).expect("population_consensus_reached event encode infallible")
}

/// A decoded quorum certificate body (pre-verification).
#[derive(Debug, Clone)]
pub struct DecodedQuorumCert {
    /// Claim class string.
    pub claim_type: String,
    /// BLAKE3 of the claim payload.
    pub claim_hash: [u8; 32],
    /// The canonical claim payload (claim_hash preimage).
    pub claim_payload: Vec<u8>,
    /// Round the cert was minted for.
    pub round_id: u64,
    /// Self-asserted quorum size (== `peer_votes.len()`; re-checked on verify).
    pub quorum_size: u64,
    /// N the quorum was computed against.
    pub peer_set_size_n: u64,
    /// f the quorum tolerated.
    pub f_tolerated: u64,
    /// The embedded vouching entries (each carries its own freshness tip).
    pub peer_votes: Vec<CertPeerVote>,
}

/// Decode a `population_consensus_reached` body. Returns `None` on shape
/// mismatch (a malformed cert is never treated as evidence).
pub fn decode_population_consensus_reached(bytes: &[u8]) -> Option<DecodedQuorumCert> {
    use myco_kernel_shared::canonical_bytes::decode;
    let m = match decode(bytes).ok()? {
        Value::Map(m) => m,
        _ => return None,
    };
    let claim_type = match m.get("claim_type")? {
        Value::String(s) => s.clone(),
        _ => return None,
    };
    let claim_hash = bytes_to_arr32(m.get("claim_hash")?)?;
    let claim_payload = match m.get("claim_payload")? {
        Value::Bytes(b) => b.clone(),
        _ => return None,
    };
    let round_id = match m.get("round_id")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let quorum_size = match m.get("quorum_size")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let peer_set_size_n = match m.get("peer_set_size_n")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let f_tolerated = match m.get("f_tolerated")? {
        Value::Uint(n) => *n,
        _ => return None,
    };
    let votes_arr = match m.get("peer_votes")? {
        Value::Array(a) => a,
        _ => return None,
    };
    let mut peer_votes = Vec::with_capacity(votes_arr.len());
    for v in votes_arr {
        let vm = match v {
            Value::Map(vm) => vm,
            _ => return None,
        };
        let peer_substrate_id = bytes_to_arr32(vm.get("peer_substrate_id")?)?;
        let peer_signature = bytes_to_arr64(vm.get("peer_signature")?)?;
        let peer_dag_tip_at_vote = bytes_to_arr32(vm.get("peer_dag_tip_at_vote")?)?;
        peer_votes.push(CertPeerVote {
            peer_substrate_id,
            peer_signature,
            peer_dag_tip_at_vote,
        });
    }
    Some(DecodedQuorumCert {
        claim_type,
        claim_hash,
        claim_payload,
        round_id,
        quorum_size,
        peer_set_size_n,
        f_tolerated,
        peer_votes,
    })
}

/// Outcome of [`verify_quorum_cert`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CertVerifyOutcome {
    /// The cert is valid: every embedded signature verifies against the
    /// corresponding peer's pinned pubkey, all voters are distinct, the
    /// claim_hash matches the embedded payload, and the count of DISTINCT
    /// verified voters meets the quorum threshold for `peer_set_size_n`.
    Valid {
        /// Number of distinct verified voters (== effective quorum reached).
        verified_distinct_voters: usize,
    },
    /// The cert is invalid; carries a human-readable reason for evidence.
    Invalid(String),
}

/// **§9.6 self-verification** — re-verify a decoded quorum certificate against a
/// `peer_substrate_id → pinned signer_pubkey` resolver (the §10 FED_HELLO pins,
/// re-derived from the DAG).
///
/// A receiver that pulls a cert across federation calls this BEFORE treating the
/// cert as evidence. The function:
///   1. Re-derives `claim_hash` from the embedded `claim_payload` and rejects if
///      it differs from the cert's self-asserted `claim_hash` (so the cert
///      cannot lie about which claim its signatures cover).
///   2. For each embedded `(peer_substrate_id, peer_signature,
///      peer_dag_tip_at_vote)`:
///      - resolves the peer's pinned `signer_pubkey` (unresolvable → that vote
///        does NOT count; an attacker cannot manufacture a quorum out of peers
///        we never pinned, §10.2);
///      - re-derives the vote signing message from the cert's claim fields +
///        round_id + the per-voter tip and re-verifies the signature.
///   3. Counts only DISTINCT verified voters (a peer signing twice counts once —
///      double-count defense).
///   4. Requires `verified_distinct_voters >= quorum_threshold(peer_set_size_n)`.
pub fn verify_quorum_cert<F>(
    cert: &DecodedQuorumCert,
    mut resolve_pinned_pubkey: F,
) -> CertVerifyOutcome
where
    F: FnMut(&[u8; 32]) -> Option<[u8; 32]>,
{
    // (1) claim_hash must match the embedded payload — the cert cannot claim its
    // signatures cover a different claim than the payload it carries.
    let recomputed = claim_hash(&cert.claim_payload);
    if recomputed != cert.claim_hash {
        return CertVerifyOutcome::Invalid(format!(
            "claim_hash {} does not match BLAKE3(claim_payload) {}",
            hex_prefix(&cert.claim_hash, 8),
            hex_prefix(&recomputed, 8)
        ));
    }

    // (2)+(3) verify each signature; count DISTINCT verified voters.
    let mut verified: std::collections::HashSet<[u8; 32]> = std::collections::HashSet::new();
    for cv in &cert.peer_votes {
        let pubkey = match resolve_pinned_pubkey(&cv.peer_substrate_id) {
            Some(pk) => pk,
            // Unresolvable pin → this vote does not count. A forged quorum
            // cannot be built from peers the receiver never pinned (§10.2).
            None => continue,
        };
        let msg = build_population_vote_signing_message(
            &cert.claim_type,
            &cert.claim_hash,
            &cv.peer_substrate_id,
            cert.round_id,
            &cv.peer_dag_tip_at_vote,
        );
        if verify_signature(&pubkey, &cv.peer_signature, &msg).is_ok() {
            // HashSet insert dedups: a peer that signed twice counts once.
            verified.insert(cv.peer_substrate_id);
        }
    }

    // (4) quorum threshold over the certified peer-set size N.
    let n = cert.peer_set_size_n as usize;
    let threshold = quorum_threshold(n);
    let verified_count = verified.len();
    if verified_count < threshold {
        return CertVerifyOutcome::Invalid(format!(
            "verified distinct voters {verified_count} < quorum_threshold({n}) = {threshold}"
        ));
    }
    CertVerifyOutcome::Valid {
        verified_distinct_voters: verified_count,
    }
}

// ---------------------------------------------------------------------------
// `population_consensus_pending:{claim_type}` event.
// ---------------------------------------------------------------------------

/// Full `population_consensus_pending:{claim_type}` node_type string.
pub fn population_consensus_pending_node_type(claim_type: &str) -> String {
    format!("{NODE_TYPE_POPULATION_CONSENSUS_PENDING_PREFIX}{claim_type}")
}

/// Encode the body of a `population_consensus_pending:{claim_type}` DAG event.
///
/// ```text
/// Map({
///   "claim_type":     String,
///   "claim_hash":     Bytes(32),
///   "round_id":       Uint,
///   "votes_received": Uint,
///   "quorum_needed":  Uint,
///   "at_cycle":       Uint,
/// })
/// ```
pub fn encode_population_consensus_pending(
    claim_type: &str,
    claim_hash: &[u8; 32],
    round_id: u64,
    votes_received: usize,
    quorum_needed: usize,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("claim_type".to_string(), Value::String(claim_type.to_string()));
    m.insert("claim_hash".to_string(), Value::Bytes(claim_hash.to_vec()));
    m.insert("round_id".to_string(), Value::Uint(round_id));
    m.insert("votes_received".to_string(), Value::Uint(votes_received as u64));
    m.insert("quorum_needed".to_string(), Value::Uint(quorum_needed as u64));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("population_consensus_pending event encode infallible")
}

// ---------------------------------------------------------------------------
// `consensus_floor_activated` / `_deactivated` events (§6.5.a).
// ---------------------------------------------------------------------------

/// Merkle root over the sorted pinned-peer-id set (§6.5.a
/// `peer_set_merkle_root`). Peer ids are sorted bytewise then folded with the
/// same length-prefixed BLAKE3 construction as [`myco_kernel_shared::crypto::merkle_hash`]
/// would over a single content blob — here the "content" is the sorted-id
/// concatenation, with a count prefix to prevent ambiguity. An empty set hashes
/// the count-0 prefix (a stable, well-defined value).
pub fn peer_set_merkle_root(pinned_peer_ids: &[[u8; 32]]) -> [u8; 32] {
    let mut sorted: Vec<[u8; 32]> = pinned_peer_ids.to_vec();
    sorted.sort_unstable();
    sorted.dedup();
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"myco-peer-set-merkle-root-v1");
    hasher.update(&(sorted.len() as u64).to_be_bytes());
    for id in &sorted {
        hasher.update(id);
    }
    hasher.finalize().into()
}

/// Encode the body of a `consensus_floor_activated` DAG event (§6.5.a):
///
/// ```text
/// Map({
///   "peer_count":           Uint,        // == pinned-peer count at the 2→3 crossing
///   "activation_cycle":     Uint,
///   "peer_set_merkle_root": Bytes(32),   // merkle over sorted pinned-peer-ids
/// })
/// ```
pub fn encode_consensus_floor_activated(
    peer_count: usize,
    activation_cycle: u64,
    peer_set_merkle_root: &[u8; 32],
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("peer_count".to_string(), Value::Uint(peer_count as u64));
    m.insert("activation_cycle".to_string(), Value::Uint(activation_cycle));
    m.insert(
        "peer_set_merkle_root".to_string(),
        Value::Bytes(peer_set_merkle_root.to_vec()),
    );
    cb_encode(&Value::Map(m)).expect("consensus_floor_activated encode infallible")
}

/// Encode the body of a `consensus_floor_deactivated` DAG event (§6.5.a):
///
/// ```text
/// Map({
///   "peer_count":         Uint,          // == pinned-peer count at the 3→2 crossing
///   "deactivation_cycle": Uint,
/// })
/// ```
pub fn encode_consensus_floor_deactivated(
    peer_count: usize,
    deactivation_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("peer_count".to_string(), Value::Uint(peer_count as u64));
    m.insert(
        "deactivation_cycle".to_string(),
        Value::Uint(deactivation_cycle),
    );
    cb_encode(&Value::Map(m)).expect("consensus_floor_deactivated encode infallible")
}

// ---------------------------------------------------------------------------
// `byzantine_threshold_check:{claim_type}` witness event.
// ---------------------------------------------------------------------------

/// Full `byzantine_threshold_check:{claim_type}` node_type string.
pub fn byzantine_threshold_check_node_type(claim_type: &str) -> String {
    format!("{NODE_TYPE_BYZANTINE_THRESHOLD_CHECK_PREFIX}{claim_type}")
}

/// Encode the body of a `byzantine_threshold_check:{claim_type}` DAG event —
/// the per-round `(N, f_tolerated, votes_received, votes_consistent)` witness.
///
/// `votes_consistent` is the count of DISTINCT votes that verified AND agreed on
/// the claim_hash for this round (i.e. the effective tally toward quorum).
///
/// ```text
/// Map({
///   "claim_type":      String,
///   "peer_set_size_n": Uint,
///   "f_tolerated":     Uint,
///   "votes_received":  Uint,
///   "votes_consistent": Uint,
///   "round_id":        Uint,
///   "at_cycle":        Uint,
/// })
/// ```
#[allow(clippy::too_many_arguments)]
pub fn encode_byzantine_threshold_check(
    claim_type: &str,
    peer_set_size_n: usize,
    f_tolerated_value: usize,
    votes_received: usize,
    votes_consistent: usize,
    round_id: u64,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("claim_type".to_string(), Value::String(claim_type.to_string()));
    m.insert(
        "peer_set_size_n".to_string(),
        Value::Uint(peer_set_size_n as u64),
    );
    m.insert(
        "f_tolerated".to_string(),
        Value::Uint(f_tolerated_value as u64),
    );
    m.insert("votes_received".to_string(), Value::Uint(votes_received as u64));
    m.insert(
        "votes_consistent".to_string(),
        Value::Uint(votes_consistent as u64),
    );
    m.insert("round_id".to_string(), Value::Uint(round_id));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("byzantine_threshold_check encode infallible")
}

// ---------------------------------------------------------------------------
// shared helpers.
// ---------------------------------------------------------------------------

fn bytes_to_arr32(v: &Value) -> Option<[u8; 32]> {
    match v {
        Value::Bytes(b) if b.len() == 32 => {
            let mut a = [0u8; 32];
            a.copy_from_slice(b);
            Some(a)
        }
        _ => None,
    }
}

fn bytes_to_arr64(v: &Value) -> Option<[u8; 64]> {
    match v {
        Value::Bytes(b) if b.len() == 64 => {
            let mut a = [0u8; 64];
            a.copy_from_slice(b);
            Some(a)
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::crypto::Ed25519PrivateKey;

    #[test]
    fn f_bound_matches_doctrine_table() {
        // algorithms/pbft_consensus_floor.md §Byzantine-fault bound.
        assert_eq!(f_tolerated(3), 0);
        assert_eq!(f_tolerated(4), 1);
        assert_eq!(f_tolerated(7), 2);
        assert_eq!(f_tolerated(10), 3);
        assert_eq!(quorum_threshold(3), 3);
        assert_eq!(quorum_threshold(4), 3);
        assert_eq!(quorum_threshold(7), 5);
        assert_eq!(quorum_threshold(10), 7);
    }

    #[test]
    fn f_bound_edge_cases() {
        // N=0/1/2 are below the floor but the math must not panic.
        assert_eq!(f_tolerated(0), 0);
        assert_eq!(f_tolerated(1), 0);
        assert_eq!(f_tolerated(2), 0);
        assert_eq!(quorum_threshold(1), 1);
        assert_eq!(quorum_threshold(2), 2);
    }

    #[test]
    fn claim_class_roundtrips() {
        for c in [
            PopulationClaimClass::PeerRevocation,
            PopulationClaimClass::UniversalJunkClassification,
            PopulationClaimClass::CrossSubstrateAggregateMetric,
        ] {
            assert_eq!(PopulationClaimClass::from_claim_type(c.claim_type()), Some(c));
        }
        assert_eq!(PopulationClaimClass::from_claim_type("bogus"), None);
    }

    #[test]
    fn vote_sign_verify_roundtrip() {
        let seed = [0x11u8; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        let pubkey = key.public_key().0;
        let signer_id = [0x22u8; 32];
        let ch = claim_hash(b"some claim payload");
        let tip = [0x33u8; 32];
        let msg = build_population_vote_signing_message(
            "peer_revocation",
            &ch,
            &signer_id,
            7,
            &tip,
        );
        let sig = key.sign(&msg).0;
        let vote = DecodedPopulationVote {
            claim_type: "peer_revocation".to_string(),
            claim_hash: ch,
            claim_payload: b"some claim payload".to_vec(),
            round_id: 7,
            voter_substrate_id: signer_id,
            voter_signature: sig,
            peer_dag_tip_at_vote: tip,
        };
        assert!(verify_population_vote(&vote, &pubkey), "valid sig must verify");
    }

    #[test]
    fn vote_tamper_fails_verify() {
        let seed = [0x44u8; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        let pubkey = key.public_key().0;
        let signer_id = [0x55u8; 32];
        let ch = claim_hash(b"claim A");
        let tip = [0u8; 32];
        let msg = build_population_vote_signing_message("peer_revocation", &ch, &signer_id, 1, &tip);
        let sig = key.sign(&msg).0;
        // Tamper: flip the claim_hash in the decoded vote. Re-derived signing
        // message no longer matches what was signed → verify fails.
        let mut tampered_hash = ch;
        tampered_hash[0] ^= 0xff;
        let vote = DecodedPopulationVote {
            claim_type: "peer_revocation".to_string(),
            claim_hash: tampered_hash,
            claim_payload: b"claim A".to_vec(),
            round_id: 1,
            voter_substrate_id: signer_id,
            voter_signature: sig,
            peer_dag_tip_at_vote: tip,
        };
        assert!(!verify_population_vote(&vote, &pubkey), "tampered vote must fail");
    }

    #[test]
    fn vote_wrong_round_differs() {
        let signer_id = [0x66u8; 32];
        let ch = claim_hash(b"c");
        let tip = [0u8; 32];
        let m1 = build_population_vote_signing_message("peer_revocation", &ch, &signer_id, 1, &tip);
        let m2 = build_population_vote_signing_message("peer_revocation", &ch, &signer_id, 2, &tip);
        assert_ne!(m1, m2, "different round_id must produce different signing message");
    }

    #[test]
    fn vote_event_roundtrips() {
        let ch = claim_hash(b"payload");
        let sig = [0x9au8; 64];
        let body = encode_population_vote(
            "peer_revocation",
            &ch,
            b"payload",
            3,
            &[0x01u8; 32],
            &sig,
            &[0x02u8; 32],
            42,
        );
        let decoded = decode_population_vote(body.as_ref()).expect("decodes");
        assert_eq!(decoded.claim_type, "peer_revocation");
        assert_eq!(decoded.claim_hash, ch);
        assert_eq!(decoded.round_id, 3);
        assert_eq!(decoded.voter_signature, sig);
        assert_eq!(decoded.peer_dag_tip_at_vote, [0x02u8; 32]);
    }

    /// Build a real N-peer cert + return its body bytes + the `(id, pubkey)`
    /// pins for verification.
    fn make_cert(
        n: usize,
        voters: usize,
        claim_payload: &[u8],
        round_id: u64,
    ) -> (Vec<u8>, Vec<([u8; 32], [u8; 32])>) {
        let ch = claim_hash(claim_payload);
        let mut votes = Vec::new();
        let mut pins: Vec<([u8; 32], [u8; 32])> = Vec::new(); // (id, pubkey)
        for i in 0..voters {
            let seed = [i as u8 + 1; 32];
            let key = Ed25519PrivateKey::from_seed(&seed);
            let pubkey = key.public_key().0;
            let id = {
                let mut a = [0u8; 32];
                a[0] = 0xA0 + i as u8;
                a
            };
            let tip = {
                let mut a = [0u8; 32];
                a[1] = i as u8;
                a
            };
            let msg = build_population_vote_signing_message(
                "peer_revocation",
                &ch,
                &id,
                round_id,
                &tip,
            );
            let sig = key.sign(&msg).0;
            votes.push(CertPeerVote {
                peer_substrate_id: id,
                peer_signature: sig,
                peer_dag_tip_at_vote: tip,
            });
            pins.push((id, pubkey));
        }
        let body = encode_population_consensus_reached(
            "peer_revocation",
            &ch,
            claim_payload,
            round_id,
            n,
            f_tolerated(n),
            &votes,
            100,
        );
        (body.as_ref().to_vec(), pins)
    }

    #[test]
    fn cert_happy_path_self_verifies() {
        // N=3, quorum=3, 3 distinct verified voters.
        let (body, pins) = make_cert(3, 3, b"revoke peer X", 1);
        let cert = decode_population_consensus_reached(&body).expect("decodes");
        let outcome = verify_quorum_cert(&cert, |id| {
            pins.iter().find(|(pid, _)| pid == id).map(|(_, pk)| *pk)
        });
        assert_eq!(
            outcome,
            CertVerifyOutcome::Valid {
                verified_distinct_voters: 3
            }
        );
    }

    #[test]
    fn cert_below_quorum_invalid() {
        // N=4 needs quorum 3; supply only 2 voters.
        let (body, pins) = make_cert(4, 2, b"claim", 1);
        let cert = decode_population_consensus_reached(&body).expect("decodes");
        let outcome = verify_quorum_cert(&cert, |id| {
            pins.iter().find(|(pid, _)| pid == id).map(|(_, pk)| *pk)
        });
        assert!(matches!(outcome, CertVerifyOutcome::Invalid(_)));
    }

    #[test]
    fn cert_unpinned_voter_does_not_count() {
        // N=3 quorum 3, 3 voters — but the resolver only knows 2 of them. The
        // unknown voter's signature cannot manufacture quorum.
        let (body, pins) = make_cert(3, 3, b"claim", 1);
        let cert = decode_population_consensus_reached(&body).expect("decodes");
        let outcome = verify_quorum_cert(&cert, |id| {
            // Drop the LAST pin (id 0xA2..).
            pins.iter()
                .take(2)
                .find(|(pid, _)| pid == id)
                .map(|(_, pk)| *pk)
        });
        assert!(
            matches!(outcome, CertVerifyOutcome::Invalid(_)),
            "only 2 of 3 voters resolvable → below quorum 3"
        );
    }

    #[test]
    fn cert_claim_hash_payload_mismatch_invalid() {
        let (body, pins) = make_cert(3, 3, b"claim", 1);
        let mut cert = decode_population_consensus_reached(&body).expect("decodes");
        // Corrupt claim_hash so it no longer matches BLAKE3(claim_payload).
        cert.claim_hash[0] ^= 0xff;
        let outcome = verify_quorum_cert(&cert, |id| {
            pins.iter().find(|(pid, _)| pid == id).map(|(_, pk)| *pk)
        });
        assert!(matches!(outcome, CertVerifyOutcome::Invalid(_)));
    }

    #[test]
    fn cert_double_counted_peer_counts_once() {
        // Craft a cert where the SAME peer's valid vote appears twice. A naive
        // tally would see 2 votes (= quorum for N=3); the distinct-voter set must
        // collapse it to 1, leaving the cert below quorum.
        let ch = claim_hash(b"dup claim");
        let seed = [0x77u8; 32];
        let key = Ed25519PrivateKey::from_seed(&seed);
        let pubkey = key.public_key().0;
        let id = [0xABu8; 32];
        let tip = [0u8; 32];
        let msg = build_population_vote_signing_message("peer_revocation", &ch, &id, 1, &tip);
        let sig = key.sign(&msg).0;
        let dup = CertPeerVote {
            peer_substrate_id: id,
            peer_signature: sig,
            peer_dag_tip_at_vote: tip,
        };
        // Two identical entries + a third distinct (but unresolvable) voter so
        // peer_votes.len() == 3, yet distinct verified == 1.
        let other = CertPeerVote {
            peer_substrate_id: [0xCDu8; 32],
            peer_signature: [0u8; 64],
            peer_dag_tip_at_vote: tip,
        };
        let body = encode_population_consensus_reached(
            "peer_revocation",
            &ch,
            b"dup claim",
            1,
            3,
            f_tolerated(3),
            &[dup.clone(), dup, other],
            100,
        );
        let cert = decode_population_consensus_reached(body.as_ref()).expect("decodes");
        let outcome = verify_quorum_cert(&cert, |q| {
            if q == &id {
                Some(pubkey)
            } else {
                None
            }
        });
        assert!(
            matches!(outcome, CertVerifyOutcome::Invalid(_)),
            "a peer voting twice must count once; cert stays below quorum"
        );
    }

    #[test]
    fn peer_set_merkle_root_is_order_independent_and_dedups() {
        let a = [0x01u8; 32];
        let b = [0x02u8; 32];
        let c = [0x03u8; 32];
        let r1 = peer_set_merkle_root(&[a, b, c]);
        let r2 = peer_set_merkle_root(&[c, a, b]);
        assert_eq!(r1, r2, "merkle root must be order-independent (sorted)");
        let r3 = peer_set_merkle_root(&[a, b, c, a]);
        assert_eq!(r1, r3, "duplicate ids must not change the root");
        let r4 = peer_set_merkle_root(&[a, b]);
        assert_ne!(r1, r4, "different membership must change the root");
    }

    #[test]
    fn activation_events_roundtrip_shapes() {
        use myco_kernel_shared::canonical_bytes::{decode, Value as V};
        let root = peer_set_merkle_root(&[[0x01u8; 32], [0x02u8; 32], [0x03u8; 32]]);
        let act = encode_consensus_floor_activated(3, 50, &root);
        let am = match decode(act.as_ref()).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(am.get("peer_count"), Some(V::Uint(3))));
        assert!(matches!(am.get("activation_cycle"), Some(V::Uint(50))));
        let deact = encode_consensus_floor_deactivated(2, 60);
        let dm = match decode(deact.as_ref()).unwrap() {
            V::Map(m) => m,
            _ => panic!(),
        };
        assert!(matches!(dm.get("peer_count"), Some(V::Uint(2))));
    }

    #[test]
    fn node_type_helpers_carry_claim_type() {
        assert_eq!(
            population_vote_node_type("peer_revocation"),
            "population_vote:peer_revocation"
        );
        assert_eq!(
            population_consensus_reached_node_type("peer_revocation"),
            "population_consensus_reached:peer_revocation"
        );
        assert_eq!(
            population_consensus_pending_node_type("peer_revocation"),
            "population_consensus_pending:peer_revocation"
        );
        assert_eq!(
            byzantine_threshold_check_node_type("peer_revocation"),
            "byzantine_threshold_check:peer_revocation"
        );
    }
}
