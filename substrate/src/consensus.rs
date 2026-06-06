//! **L2/FEDERATION §6.5 — Stage-1 population-consensus floor runtime**.
//!
//! This module is the runtime half of the consensus floor: the operator-facing
//! handlers (propose / submit-peer-vote / query), the DAG-derivation helpers
//! that reconstruct consensus state (since `FederationState.peers` is
//! in-memory-only, ALL consensus state lives as DAG events and is re-derived on
//! demand), the §6.5.a activation crossing emitter, and the C49 gate.
//!
//! The pure encode/decode/verify surface (vote signing message, cert
//! self-verification, f-bound math) lives in [`crate::events`]
//! (`events/consensus.rs`); this module orchestrates it against `ServerState`.
//!
//! ## Stage-1 scope (vs full Tendermint — DEFERRED)
//!
//! This is a **single-round quorum-certificate floor**: a substrate proposes a
//! claim, collects ≥2/3 distinct-peer signed votes, and mints a self-evidencing
//! certificate. It is BFT-SAFE (no honest substrate acts without 2/3 of the
//! pinned peer set vouching) but provides **safety, not liveness** — there is no
//! leader election, no view-change, no prevote/precommit rounds. A partition
//! leaves a claim `pending` indefinitely (§14). Multi-round Tendermint, the P14
//! `consensus_participation` sub-criterion, claim-class 2/3 action sites, and
//! the `population_consensus_stuck` (>7 timeouts) signal are Stage 2 / Stage 1.5.

use std::collections::{BTreeMap, HashMap, HashSet};

use myco_kernel_bridge::protocol::{msg_type, Message};
use myco_kernel_shared::canonical_bytes::Value;
use myco_kernel_shared::crypto::Ed25519PrivateKey;

use crate::events::{
    self, byzantine_threshold_check_node_type, claim_hash as compute_claim_hash,
    decode_federation_peer_pinned_signer, decode_population_consensus_reached,
    decode_population_vote, f_tolerated, population_consensus_reached_node_type,
    population_vote_node_type, quorum_threshold, verify_population_vote, verify_quorum_cert,
    CertPeerVote, CertVerifyOutcome, PopulationClaimClass, CONSENSUS_FLOOR_MIN_PEERS,
    NODE_TYPE_FEDERATION_PEER_PINNED_PREFIX,
};
use crate::server::{emit_substrate_event, save_dag_state, ServerState};
use crate::SubstrateError;

// ===========================================================================
// DAG-derived consensus state.
// ===========================================================================

/// **§6.5.a** — the consensus floor is active iff the substrate has ≥3 pinned
/// peers (NB: this counts the live in-memory peer connections; activation
/// crossings are recorded as DAG events at poll/connect time).
pub(crate) fn consensus_floor_active(state: &ServerState) -> bool {
    state.federation.peer_count() >= CONSENSUS_FLOOR_MIN_PEERS
}

/// Re-derive the §10 FED_HELLO pin set (`peer_substrate_id → signer_pubkey`)
/// from the DAG's `federation_peer_pinned:*` events. Legacy peers (pinned by
/// substrate-ID TOFU with no `signer_pubkey`) contribute no entry — they are
/// consensus-passive (no verifiable votes). On the rare event of a peer being
/// re-pinned with a different pubkey, the last-seen pin wins (insertion order).
///
/// **Revoked peers are excluded.** A revoked peer is no longer a consensus
/// participant: [`peer_set_size_n`] already drops it from N (the quorum
/// denominator), so its votes MUST also be dropped from every tally (the
/// numerator). Otherwise the asymmetry is exploitable — a peer revoked for
/// key-compromise both *shrinks* N (lowering the quorum bar) AND, if the
/// attacker still holds its key, supplies a *counted* vote, letting a coalition
/// forge a quorum certificate entirely out of revoked keys. The local-N
/// under-claim guard in [`find_valid_quorum_cert`] does NOT catch this on its own
/// (a revoked voter still resolves to a valid pubkey), so the exclusion belongs
/// here, at the single pin source every consensus path consults.
pub(crate) fn derive_pinned_signer_pubkeys(state: &ServerState) -> HashMap<[u8; 32], [u8; 32]> {
    let mut out = HashMap::new();
    for node in state.dag.iter_in_insertion_order() {
        if !node
            .node_type
            .starts_with(NODE_TYPE_FEDERATION_PEER_PINNED_PREFIX)
        {
            continue;
        }
        if let Some((id, pk)) =
            decode_federation_peer_pinned_signer(node.content_canonical_bytes.as_ref())
        {
            // Revoked → not a consensus participant; its vote must never count
            // (keeps numerator consistent with the `peer_set_size_n` denominator).
            if state.revoked_federation_peers.contains(&id) {
                continue;
            }
            out.insert(id, pk);
        }
    }
    out
}

/// The consensus participant set size N = self + all currently-pinned,
/// non-revoked peers. Uses the LIVE peer connections (the authoritative present
/// membership), excluding any peer on the owner-revocation list. The `+1` is
/// this substrate itself (it always votes on a claim it proposes).
pub(crate) fn peer_set_size_n(state: &ServerState) -> usize {
    let live_non_revoked = state
        .federation
        .peers
        .iter()
        .filter_map(|p| p.peer_substrate_id)
        .filter(|id| !state.revoked_federation_peers.contains(id))
        .collect::<HashSet<_>>()
        .len();
    live_non_revoked + 1
}

/// The sorted set of pinned-peer ids (self EXCLUDED — used only for the
/// `peer_set_merkle_root` at activation, which is over the peer set).
fn pinned_peer_ids(state: &ServerState) -> Vec<[u8; 32]> {
    state
        .federation
        .peers
        .iter()
        .filter_map(|p| p.peer_substrate_id)
        .collect()
}

/// Allocate the next `round_id` for a `(claim_type, claim_hash)` pair: one more
/// than the highest round seen in any existing `population_vote` for that claim,
/// or `0` if none. Monotonic-per-claim → replay prevention across rounds.
fn next_round_id(state: &ServerState, claim_type: &str, claim_hash: &[u8; 32]) -> u64 {
    let mut max_round: Option<u64> = None;
    let want_nt = population_vote_node_type(claim_type);
    for node in state.dag.iter_in_insertion_order() {
        if node.node_type != want_nt {
            continue;
        }
        if let Some(v) = decode_population_vote(node.content_canonical_bytes.as_ref()) {
            if &v.claim_hash == claim_hash {
                max_round = Some(max_round.map_or(v.round_id, |m| m.max(v.round_id)));
            }
        }
    }
    match max_round {
        Some(r) => r + 1,
        None => 0,
    }
}

/// Whether a `population_vote` for `(claim_type, claim_hash, round_id, voter)`
/// is already recorded in the DAG (so re-ingesting the same peer vote is a
/// no-op). Walks matching `population_vote:{claim_type}` nodes.
fn population_vote_already_recorded(
    state: &ServerState,
    claim_type: &str,
    claim_hash: &[u8; 32],
    round_id: u64,
    voter_substrate_id: &[u8; 32],
) -> bool {
    let want_nt = population_vote_node_type(claim_type);
    state.dag.iter_in_insertion_order().any(|node| {
        if node.node_type != want_nt {
            return false;
        }
        match decode_population_vote(node.content_canonical_bytes.as_ref()) {
            Some(v) => {
                &v.claim_hash == claim_hash
                    && v.round_id == round_id
                    && &v.voter_substrate_id == voter_substrate_id
            }
            None => false,
        }
    })
}

/// Count DISTINCT verified voters for a `(claim_type, claim_hash, round_id)`
/// triple by walking every matching `population_vote` event, re-verifying each
/// signature against the voter's pinned pubkey (this substrate's own pubkey
/// resolves via [`ServerState::substrate_signing_pubkey`]; peers via the §10
/// pin set), and collecting DISTINCT `voter_substrate_id`s that verify.
///
/// Returns `(distinct_verified, total_votes_seen)`.
fn tally_votes(
    state: &ServerState,
    claim_type: &str,
    claim_hash: &[u8; 32],
    round_id: u64,
    pins: &HashMap<[u8; 32], [u8; 32]>,
) -> (usize, usize) {
    let self_id = state.substrate_id();
    let self_pubkey = state.substrate_signing_pubkey();
    let want_nt = population_vote_node_type(claim_type);
    let mut verified: HashSet<[u8; 32]> = HashSet::new();
    let mut total = 0usize;
    for node in state.dag.iter_in_insertion_order() {
        if node.node_type != want_nt {
            continue;
        }
        let vote = match decode_population_vote(node.content_canonical_bytes.as_ref()) {
            Some(v) => v,
            None => continue,
        };
        if &vote.claim_hash != claim_hash || vote.round_id != round_id {
            continue;
        }
        total += 1;
        // Resolve the voter's pubkey: self OR a pinned peer. A vote from an
        // unpinned peer cannot count (no pubkey to verify against).
        let pubkey = if vote.voter_substrate_id == self_id {
            self_pubkey
        } else {
            match pins.get(&vote.voter_substrate_id) {
                Some(pk) => *pk,
                None => continue,
            }
        };
        if verify_population_vote(&vote, &pubkey) {
            verified.insert(vote.voter_substrate_id);
        }
    }
    (verified.len(), total)
}

/// Collect the `CertPeerVote` entries (id, sig, tip) for every DISTINCT verified
/// voter on a `(claim_type, claim_hash, round_id)` triple — the body of a quorum
/// certificate. First-seen vote per voter wins (deterministic insertion order).
fn collect_cert_votes(
    state: &ServerState,
    claim_type: &str,
    claim_hash: &[u8; 32],
    round_id: u64,
    pins: &HashMap<[u8; 32], [u8; 32]>,
) -> Vec<CertPeerVote> {
    let self_id = state.substrate_id();
    let self_pubkey = state.substrate_signing_pubkey();
    let want_nt = population_vote_node_type(claim_type);
    let mut seen: HashSet<[u8; 32]> = HashSet::new();
    let mut out = Vec::new();
    for node in state.dag.iter_in_insertion_order() {
        if node.node_type != want_nt {
            continue;
        }
        let vote = match decode_population_vote(node.content_canonical_bytes.as_ref()) {
            Some(v) => v,
            None => continue,
        };
        if &vote.claim_hash != claim_hash || vote.round_id != round_id {
            continue;
        }
        if seen.contains(&vote.voter_substrate_id) {
            continue;
        }
        let pubkey = if vote.voter_substrate_id == self_id {
            self_pubkey
        } else {
            match pins.get(&vote.voter_substrate_id) {
                Some(pk) => *pk,
                None => continue,
            }
        };
        if verify_population_vote(&vote, &pubkey) {
            seen.insert(vote.voter_substrate_id);
            out.push(CertPeerVote {
                peer_substrate_id: vote.voter_substrate_id,
                peer_signature: vote.voter_signature,
                peer_dag_tip_at_vote: vote.peer_dag_tip_at_vote,
            });
        }
    }
    out
}

/// Find a VALID quorum certificate in the DAG for a `(claim_type, claim_hash)`
/// pair: a `population_consensus_reached:{claim_type}` event whose embedded
/// signatures re-verify (via [`verify_quorum_cert`]) against the §10 pins and
/// whose distinct-verified count meets quorum. Returns the cert event's node
/// hash + the verify outcome's distinct-voter count, or `None`.
///
/// This is the function the **C49 gate** consults: a population action while the
/// floor is active is allowed iff a valid matching cert exists.
///
/// **N-underclaim hardening** — the cert carries a self-asserted
/// `peer_set_size_n` that drives the embedded quorum threshold. A Byzantine
/// minter could under-claim N to lower its own quorum bar (e.g. claim N=3,
/// quorum 3, when the true network is larger). [`verify_quorum_cert`] checks the
/// cert against its OWN claimed N; here we ADDITIONALLY require the distinct
/// verified voters to meet quorum against the VERIFIER's authoritative present
/// peer-set N ([`peer_set_size_n`]). A cert thus needs enough real signatures to
/// satisfy BOTH bars — the verifier never accepts fewer vouchers than its own
/// view of N demands.
pub(crate) fn find_valid_quorum_cert(
    state: &ServerState,
    claim_type: &str,
    claim_hash: &[u8; 32],
) -> Option<([u8; 32], usize)> {
    let pins = derive_pinned_signer_pubkeys(state);
    let self_id = state.substrate_id();
    let self_pubkey = state.substrate_signing_pubkey();
    let local_threshold = quorum_threshold(peer_set_size_n(state));
    let want_nt = population_consensus_reached_node_type(claim_type);
    for node in state.dag.iter_in_insertion_order() {
        if node.node_type != want_nt {
            continue;
        }
        let cert = match decode_population_consensus_reached(node.content_canonical_bytes.as_ref()) {
            Some(c) => c,
            None => continue,
        };
        if &cert.claim_hash != claim_hash {
            continue;
        }
        // Re-verify the cert self-evidences against OUR view of the §10 pins
        // (+ our own pubkey, since this substrate may be one of the voters).
        let outcome = verify_quorum_cert(&cert, |id| {
            if id == &self_id {
                Some(self_pubkey)
            } else {
                pins.get(id).copied()
            }
        });
        if let CertVerifyOutcome::Valid {
            verified_distinct_voters,
        } = outcome
        {
            // N-underclaim guard: also meet the verifier's local quorum bar.
            if verified_distinct_voters >= local_threshold {
                return Some((node.hash.0, verified_distinct_voters));
            }
        }
    }
    None
}

// ===========================================================================
// §6.5.a activation crossing.
// ===========================================================================

/// Emit a `consensus_floor_activated` / `_deactivated` event if the pinned-peer
/// count just crossed the 2↔3 boundary. Call AFTER a poll/connect that may have
/// changed `peer_count`, passing the count BEFORE the operation. Idempotent: no
/// event when the boundary was not crossed.
pub(crate) fn emit_consensus_floor_crossing_if_needed(
    state: &mut ServerState,
    prior_peer_count: usize,
) -> Result<(), SubstrateError> {
    let now_count = state.federation.peer_count();
    let was_active = prior_peer_count >= CONSENSUS_FLOOR_MIN_PEERS;
    let is_active = now_count >= CONSENSUS_FLOOR_MIN_PEERS;
    if was_active == is_active {
        return Ok(()); // no crossing.
    }
    let cycle = state.cycle_counter();
    if is_active {
        // 2 → 3 activation.
        let root = events::peer_set_merkle_root(&pinned_peer_ids(state));
        let content = events::encode_consensus_floor_activated(now_count, cycle, &root);
        let _ = emit_substrate_event(
            state,
            events::NODE_TYPE_CONSENSUS_FLOOR_ACTIVATED.to_string(),
            content,
        )?;
    } else {
        // 3 → 2 deactivation.
        let content = events::encode_consensus_floor_deactivated(now_count, cycle);
        let _ = emit_substrate_event(
            state,
            events::NODE_TYPE_CONSENSUS_FLOOR_DEACTIVATED.to_string(),
            content,
        )?;
    }
    Ok(())
}

// ===========================================================================
// Operator handlers.
// ===========================================================================

/// `federation_propose_population_claim` — mint THIS substrate's own vote over a
/// population claim, opening (or re-opening at a fresh round) a consensus round.
///
/// Payload:
/// ```text
/// Map({ "claim_type": String, "claim_payload": Bytes })
/// ```
/// Response: `round_id` + `claim_hash` + tally (`votes_received` / `quorum_needed`
/// / `peer_set_size_n`) + (if quorum already met) the cert event hash.
pub(crate) fn handle_federation_propose_population_claim(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let claim_type = require_claim_type(request)?;
    let claim_payload = match request.payload.get("claim_payload") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_propose_population_claim: claim_payload must be Bytes".to_string(),
            ));
        }
    };
    let ch = compute_claim_hash(&claim_payload);
    let round_id = next_round_id(state, &claim_type, &ch);

    // Sign our own vote over the canonical signing message.
    let self_id = state.substrate_id();
    let dag_tip = state.dag.tip().map(|t| t.0).unwrap_or([0u8; 32]);
    let signing_msg = events::build_population_vote_signing_message(
        &claim_type, &ch, &self_id, round_id, &dag_tip,
    );
    let key = Ed25519PrivateKey::from_seed(&state.substrate_signing_seed);
    let sig = key.sign(&signing_msg).0;

    let cycle = state.cycle_counter();
    let vote_content = events::encode_population_vote(
        &claim_type, &ch, &claim_payload, round_id, &self_id, &sig, &dag_tip, cycle,
    );
    let _ = emit_substrate_event(state, population_vote_node_type(&claim_type), vote_content)?;

    // Tally + (defensively) mint a cert if quorum is already met. With N≥3 and
    // only our own vote this never fires, but the path is here so a single
    // call-site reaches quorum once peer votes have already been ingested.
    let cert_hash = recheck_quorum_and_maybe_emit_cert(state, &claim_type, &ch, &claim_payload, round_id)?;

    let pins = derive_pinned_signer_pubkeys(state);
    let (votes, _total) = tally_votes(state, &claim_type, &ch, round_id, &pins);
    let n = peer_set_size_n(state);

    let mut payload = BTreeMap::new();
    payload.insert("claim_type".to_string(), Value::String(claim_type));
    payload.insert("claim_hash".to_string(), Value::Bytes(ch.to_vec()));
    payload.insert("round_id".to_string(), Value::Uint(round_id));
    payload.insert("votes_received".to_string(), Value::Uint(votes as u64));
    payload.insert(
        "quorum_needed".to_string(),
        Value::Uint(quorum_threshold(n) as u64),
    );
    payload.insert("peer_set_size_n".to_string(), Value::Uint(n as u64));
    payload.insert("floor_active".to_string(), Value::Bool(consensus_floor_active(state)));
    if let Some(h) = cert_hash {
        payload.insert("consensus_reached_event_hash".to_string(), Value::Bytes(h.to_vec()));
    }
    let _ = save_dag_state(state);
    Ok(Some(Message::new(
        msg_type::FEDERATION_PROPOSE_POPULATION_CLAIM_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// `federation_submit_peer_vote` — ingest a peer's vote over a population claim.
///
/// The peer's vote arrives as the canonical `population_vote` body bytes (the
/// same shape the substrate emits + that rides FED_EVENT_BATCH). The substrate:
///   1. decodes it;
///   2. resolves the voter's §10 pinned `signer_pubkey` and VERIFIES the
///      embedded Ed25519 signature (a vote from an unpinned peer, or a tampered
///      signature, is rejected — `accepted=false`);
///   3. records it as a `population_vote:{claim_type}` event (content-hash
///      idempotent — re-submitting the identical vote is a no-op);
///   4. re-tallies + auto-emits the quorum cert if quorum is reached.
///
/// Payload:
/// ```text
/// Map({ "vote_event_bytes": Bytes })   // canonical population_vote body
/// ```
pub(crate) fn handle_federation_submit_peer_vote(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let vote_bytes = match request.payload.get("vote_event_bytes") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_submit_peer_vote: vote_event_bytes must be Bytes".to_string(),
            ));
        }
    };
    let vote = match decode_population_vote(&vote_bytes) {
        Some(v) => v,
        None => {
            return Ok(Some(reject_vote_response(
                request,
                "vote_event_bytes is not a well-formed population_vote body",
            )));
        }
    };

    // Verify the embedded signature against the voter's pinned pubkey.
    let pins = derive_pinned_signer_pubkeys(state);
    let voter_pubkey = match pins.get(&vote.voter_substrate_id) {
        Some(pk) => *pk,
        None => {
            return Ok(Some(reject_vote_response(
                request,
                "voter has no §10 FED_HELLO pinned signer_pubkey (unpinned / legacy peer); \
                 vote cannot be verified",
            )));
        }
    };
    if !verify_population_vote(&vote, &voter_pubkey) {
        return Ok(Some(reject_vote_response(
            request,
            "peer vote signature failed Ed25519 verification against pinned signer_pubkey",
        )));
    }

    // Record the verified vote — but only once per (claim_hash, round_id,
    // voter). Re-submitting the SAME peer vote is a no-op (the duplicate would
    // never inflate the distinct-voter tally anyway, but skipping it keeps the
    // DAG free of redundant vote nodes). We re-encode from the decoded fields
    // so the stored bytes are canonical; the freshness tip + signature (the
    // signed material) are preserved verbatim, `emitted_at_cycle` (metadata,
    // outside the signed message) is the local record cycle.
    if !population_vote_already_recorded(
        state,
        &vote.claim_type,
        &vote.claim_hash,
        vote.round_id,
        &vote.voter_substrate_id,
    ) {
        let cycle = state.cycle_counter();
        let vote_content = events::encode_population_vote(
            &vote.claim_type,
            &vote.claim_hash,
            &vote.claim_payload,
            vote.round_id,
            &vote.voter_substrate_id,
            &vote.voter_signature,
            &vote.peer_dag_tip_at_vote,
            cycle,
        );
        let _ = emit_substrate_event(
            state,
            population_vote_node_type(&vote.claim_type),
            vote_content,
        )?;
    }

    let cert_hash = recheck_quorum_and_maybe_emit_cert(
        state,
        &vote.claim_type,
        &vote.claim_hash,
        &vote.claim_payload,
        vote.round_id,
    )?;

    let pins = derive_pinned_signer_pubkeys(state);
    let (votes, _total) = tally_votes(state, &vote.claim_type, &vote.claim_hash, vote.round_id, &pins);
    let n = peer_set_size_n(state);

    let mut payload = BTreeMap::new();
    payload.insert("accepted".to_string(), Value::Bool(true));
    payload.insert("claim_type".to_string(), Value::String(vote.claim_type.clone()));
    payload.insert("claim_hash".to_string(), Value::Bytes(vote.claim_hash.to_vec()));
    payload.insert("round_id".to_string(), Value::Uint(vote.round_id));
    payload.insert("votes_received".to_string(), Value::Uint(votes as u64));
    payload.insert(
        "quorum_needed".to_string(),
        Value::Uint(quorum_threshold(n) as u64),
    );
    payload.insert("peer_set_size_n".to_string(), Value::Uint(n as u64));
    if let Some(h) = cert_hash {
        payload.insert("consensus_reached_event_hash".to_string(), Value::Bytes(h.to_vec()));
    }
    let _ = save_dag_state(state);
    Ok(Some(Message::new(
        msg_type::FEDERATION_SUBMIT_PEER_VOTE_RESPONSE,
        request.request_id,
        payload,
    )))
}

/// `federation_query_consensus` — report a population claim's status:
/// `reached` (a valid cert exists) | `pending` (no quorum yet) | `stuck`
/// (DEFERRED: >7 consecutive timeouts; never reported in Stage 1) + tally.
///
/// Payload:
/// ```text
/// Map({ "claim_type": String, "claim_payload": Bytes })
/// ```
pub(crate) fn handle_federation_query_consensus(
    state: &mut ServerState,
    request: &Message,
) -> Result<Option<Message>, SubstrateError> {
    let claim_type = require_claim_type(request)?;
    let claim_payload = match request.payload.get("claim_payload") {
        Some(Value::Bytes(b)) => b.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "federation_query_consensus: claim_payload must be Bytes".to_string(),
            ));
        }
    };
    let ch = compute_claim_hash(&claim_payload);

    // Latest round for this claim (the tally is per-round).
    let round_id = next_round_id(state, &claim_type, &ch).saturating_sub(1);
    let pins = derive_pinned_signer_pubkeys(state);
    let (votes, _total) = tally_votes(state, &claim_type, &ch, round_id, &pins);
    let n = peer_set_size_n(state);

    let cert = find_valid_quorum_cert(state, &claim_type, &ch);
    let status = if cert.is_some() { "reached" } else { "pending" };

    let mut payload = BTreeMap::new();
    payload.insert("claim_type".to_string(), Value::String(claim_type));
    payload.insert("claim_hash".to_string(), Value::Bytes(ch.to_vec()));
    payload.insert("status".to_string(), Value::String(status.to_string()));
    payload.insert("round_id".to_string(), Value::Uint(round_id));
    payload.insert("votes_received".to_string(), Value::Uint(votes as u64));
    payload.insert(
        "quorum_needed".to_string(),
        Value::Uint(quorum_threshold(n) as u64),
    );
    payload.insert("peer_set_size_n".to_string(), Value::Uint(n as u64));
    payload.insert("floor_active".to_string(), Value::Bool(consensus_floor_active(state)));
    if let Some((h, voters)) = cert {
        payload.insert("consensus_reached_event_hash".to_string(), Value::Bytes(h.to_vec()));
        payload.insert("cert_verified_voters".to_string(), Value::Uint(voters as u64));
    }
    Ok(Some(Message::new(
        msg_type::FEDERATION_QUERY_CONSENSUS_RESPONSE,
        request.request_id,
        payload,
    )))
}

// ===========================================================================
// C49 gate.
// ===========================================================================

/// **C49 `consensus_floor_bypass`** (L1/HARD_RULES C49; L2/FEDERATION §6.5) —
/// the gate a population-level substrate-private ACTION must pass while the
/// floor is active.
///
/// Returns `Ok(())` to PROCEED; `Err(evidence)` to REJECT (the caller emits the
/// C49 immune sporocarp + refuses the action). The action is rejected iff:
///   - the floor is active (`peer_count ≥ 3`), AND
///   - the action's `class` is a population-only class (§6.5.b), AND
///   - NO valid `population_consensus_reached:{claim_type}` cert exists in the
///     DAG for this `claim_hash` with a ≥2/3 quorum.
///
/// Below the floor, or with a valid matching cert, the action proceeds.
///
/// **Stage-1 wiring**: only [`PopulationClaimClass::PeerRevocation`] is wired at
/// its action site (the C13 `revoke_federation_peer` path). Classes 2/3 get the
/// enum here; their action sites are Stage 2.
// **v0.9 owner-key removal**: the sole caller (the `revoke_federation_peer`
// owner-attested mutation block in `attestation::handle_submit_mutation`) was
// removed. The C49 consensus-floor action gate is retained dormant — the C13
// egress / consensus machinery in federation/ + consensus/ is kept per the
// removal scope; a future keyless peer-revocation path can re-wire this.
#[allow(dead_code)]
pub(crate) fn check_c49_population_action_allowed(
    state: &ServerState,
    class: PopulationClaimClass,
    claim_hash: &[u8; 32],
) -> Result<(), String> {
    if !consensus_floor_active(state) {
        // Below the floor: pairwise-trust + owner-attestation governs (§6.5.a).
        return Ok(());
    }
    let claim_type = class.claim_type();
    if find_valid_quorum_cert(state, claim_type, claim_hash).is_some() {
        return Ok(()); // a valid quorum cert authorizes the action.
    }
    Err(format!(
        "C49_consensus_floor_bypass: population action class={claim_type} attempted while the \
         consensus floor is ACTIVE (peer_count={} ≥ {CONSENSUS_FLOOR_MIN_PEERS}) WITHOUT a valid \
         ≥2/3 population_consensus_reached:{claim_type} certificate for claim_hash={}",
        state.federation.peer_count(),
        crate::server::hex_first_8_bytes(claim_hash),
    ))
}

// ===========================================================================
// internal helpers.
// ===========================================================================

/// Re-tally a `(claim_type, claim_hash, round_id)` and, if the distinct verified
/// voters now meet quorum AND no valid cert yet exists, emit the quorum
/// certificate + a `byzantine_threshold_check` witness. Returns the cert event
/// hash if one is (or was already) present, else `None`.
fn recheck_quorum_and_maybe_emit_cert(
    state: &mut ServerState,
    claim_type: &str,
    claim_hash: &[u8; 32],
    claim_payload: &[u8],
    round_id: u64,
) -> Result<Option<[u8; 32]>, SubstrateError> {
    // Already certified? (idempotent — a re-submitted vote shouldn't double-mint.)
    if let Some((h, _)) = find_valid_quorum_cert(state, claim_type, claim_hash) {
        return Ok(Some(h));
    }
    let pins = derive_pinned_signer_pubkeys(state);
    let n = peer_set_size_n(state);
    let threshold = quorum_threshold(n);
    let (distinct, total) = tally_votes(state, claim_type, claim_hash, round_id, &pins);

    // Always emit the per-round byzantine_threshold_check witness so the
    // (N, f, votes_received, votes_consistent) audit trail exists per round.
    let cycle = state.cycle_counter();
    let btc = events::encode_byzantine_threshold_check(
        claim_type,
        n,
        f_tolerated(n),
        total,
        distinct,
        round_id,
        cycle,
    );
    let _ = emit_substrate_event(state, byzantine_threshold_check_node_type(claim_type), btc)?;

    if distinct < threshold {
        // Not enough votes yet → record a pending marker + act NOT.
        let pending = events::encode_population_consensus_pending(
            claim_type, claim_hash, round_id, distinct, threshold, cycle,
        );
        let _ = emit_substrate_event(
            state,
            events::population_consensus_pending_node_type(claim_type),
            pending,
        )?;
        return Ok(None);
    }

    // Quorum reached — mint the self-verifying certificate.
    let cert_votes = collect_cert_votes(state, claim_type, claim_hash, round_id, &pins);
    let cert_content = events::encode_population_consensus_reached(
        claim_type,
        claim_hash,
        claim_payload,
        round_id,
        n,
        f_tolerated(n),
        &cert_votes,
        cycle,
    );
    let h = emit_substrate_event(
        state,
        population_consensus_reached_node_type(claim_type),
        cert_content,
    )?;
    Ok(Some(h.0))
}

/// Extract the required `claim_type` String from the request payload + validate
/// it is one of the three §6.5.b population classes.
fn require_claim_type(request: &Message) -> Result<String, SubstrateError> {
    let s = match request.payload.get("claim_type") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => {
            return Err(SubstrateError::Protocol(
                "consensus: claim_type must be a non-empty String".to_string(),
            ));
        }
    };
    if PopulationClaimClass::from_claim_type(&s).is_none() {
        return Err(SubstrateError::Protocol(format!(
            "consensus: unknown claim_type {s:?} (must be one of the three §6.5.b classes: \
             peer_revocation / universal_junk_classification / cross_substrate_aggregate_metric)"
        )));
    }
    Ok(s)
}

/// Build a `federation_submit_peer_vote_response` with `accepted=false` + reason.
fn reject_vote_response(request: &Message, reason: &str) -> Message {
    let mut payload = BTreeMap::new();
    payload.insert("accepted".to_string(), Value::Bool(false));
    payload.insert("reason".to_string(), Value::String(reason.to_string()));
    Message::new(
        msg_type::FEDERATION_SUBMIT_PEER_VOTE_RESPONSE,
        request.request_id,
        payload,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::persistence::Manifest;
    use myco_kernel_schema::dag::Dag;

    fn test_state() -> ServerState {
        let g = Manifest::genesis();
        ServerState::new(
            std::env::temp_dir().join(format!(
                "myco-consensus-unit-{}-{:x}",
                std::process::id(),
                &0u8 as *const u8 as usize as u64
            )),
            Some(g.substrate_id),
            Some(g.genesis_time_unix_ns),
            g.cycle_counter,
            g.last_absorbed_cycle,
            g.generation_depth,
            Dag::new(),
            [0u8; 32],
        )
    }

    fn push_pin(state: &mut ServerState, id: &[u8; 32], pk: &[u8; 32]) {
        let content = events::encode_federation_peer_pinned(id, "127.0.0.1:0", 1, Some(pk));
        let parents = state.dag.tip().map(|t| vec![t]).unwrap_or_default();
        let cycle = state.cycle_counter();
        state
            .dag
            .insert_node(
                parents,
                events::federation_peer_pinned_node_type(id),
                cycle,
                content,
            )
            .expect("insert pin");
    }

    /// **Security regression (adversarial-review finding)** — a revoked peer must
    /// be excluded from the consensus pin set, so its (possibly compromised) key
    /// can never supply a counted vote. Before this fix `peer_set_size_n` dropped
    /// revoked peers from N (the quorum denominator) while the pin set still
    /// resolved their pubkeys (the numerator), so a coalition holding f+1
    /// revoked-for-compromise keys could both shrink N AND vote — forging a quorum
    /// certificate entirely out of revoked keys.
    #[test]
    fn revoked_peer_excluded_from_consensus_pins() {
        let mut state = test_state();
        let (p1, pk1) = ([0xA1u8; 32], [0x11u8; 32]);
        let (p2, pk2) = ([0xA2u8; 32], [0x22u8; 32]);
        let (p3, pk3) = ([0xA3u8; 32], [0x33u8; 32]);
        push_pin(&mut state, &p1, &pk1);
        push_pin(&mut state, &p2, &pk2);
        push_pin(&mut state, &p3, &pk3);

        // All three resolve before any revocation.
        let pins = derive_pinned_signer_pubkeys(&state);
        assert_eq!(pins.len(), 3);
        assert_eq!(pins.get(&p2), Some(&pk2));

        // Revoke p2: its pubkey must no longer resolve, so a vote signed by p2's
        // key can never be counted toward a quorum tally / cert.
        state.revoked_federation_peers.insert(p2);
        let pins = derive_pinned_signer_pubkeys(&state);
        assert_eq!(
            pins.len(),
            2,
            "revoked peer must be excluded from the consensus pin set"
        );
        assert_eq!(pins.get(&p2), None, "revoked peer pubkey must not resolve");
        assert_eq!(pins.get(&p1), Some(&pk1));
        assert_eq!(pins.get(&p3), Some(&pk3));
    }
}
