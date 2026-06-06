// COV06 不弃不孤 — cultivator-mortality + succession FSM operator messages.
//
// Mirrors the Rust handlers in `substrate/src/cultivation.rs`
// (`handle_update_successor_chain` / `handle_accept_succession` /
// `handle_accept_bet_retired_proposal`). The payload Map field names + value
// types are the wire contract; field/type drift breaks the substrate decode.
//
// **v0.9 owner-key removal**: the `record_cultivator_heartbeat` handler + the
// heartbeat-staleness watchdog were dropped with the anchor surface, and the
// owner Ed25519 signature gates on update_successor_chain / accept_succession /
// accept_bet_retired_proposal were removed (the handlers are now KEYLESS — the
// C46 catechumenate floor + the structural interval/proposal-reference gates are
// the surviving authorization roots). The signing-input helpers + the signature
// payload fields are therefore gone.

import { type Value } from "../../canonical/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

function requireLen(name: string, b: Uint8Array, n: number): void {
  if (b.length !== n) {
    throw new BridgeProtocolError(`${name} must be ${n} bytes; got ${b.length}`);
  }
}

// ---------------------------------------------------------------------------
// update_successor_chain (F21 SuccessorEntry append; §3.2.A; KEYLESS v0.9).
// ---------------------------------------------------------------------------

/** Build the `update_successor_chain` request payload (KEYLESS v0.9).
 *
 *  The owner Ed25519 attestation gate was removed; the substrate validates the
 *  structural interval rules (monotone valid_from + non-overlap) only, so this
 *  sends just the entry fields. */
export function updateSuccessorChainPayload(args: {
  successorPubkey: Uint8Array;
  validFromUnixNs: bigint;
  validUntilUnixNs: bigint | null;
}): Map<string, Value> {
  requireLen("successor_pubkey", args.successorPubkey, 32);
  const m = new Map<string, Value>();
  m.set("successor_pubkey", { type: "bytes", value: args.successorPubkey });
  m.set("valid_from_unix_ns", { type: "timestamp", value: args.validFromUnixNs });
  m.set(
    "valid_until_unix_ns",
    args.validUntilUnixNs === null
      ? { type: "null" }
      : { type: "timestamp", value: args.validUntilUnixNs },
  );
  return m;
}

/** Parsed `update_successor_chain_response`. */
export interface UpdateSuccessorChainResult {
  updatedEventHash: Uint8Array;
  chainLength: bigint;
}

export function parseUpdateSuccessorChainResponse(
  response: Message,
): UpdateSuccessorChainResult {
  if (response.messageType !== MSG_TYPE.UPDATE_SUCCESSOR_CHAIN_RESPONSE) {
    throw new BridgeProtocolError(
      `expected update_successor_chain_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("updated_event_hash");
  const lenV = response.payload.get("chain_length");
  if (!hashV || hashV.type !== "bytes" || !lenV || lenV.type !== "uint") {
    throw new BridgeProtocolError(
      "update_successor_chain_response missing required typed fields",
    );
  }
  return { updatedEventHash: hashV.value, chainLength: lenV.value };
}

// ---------------------------------------------------------------------------
// accept_succession (T3 legacy→normal; KEYLESS v0.9).
// ---------------------------------------------------------------------------

/** Build the `accept_succession` request payload (KEYLESS v0.9).
 *
 *  The successor Ed25519 signature gate (and the C12 fresh-owner-heartbeat
 *  takeover guard) were removed with the anchor surface; the C46 catechumenate
 *  floor (catechumenate_session_count ≥ 50) is the surviving un-fabricable
 *  authorization gate, so this sends just the lineage fields + the count. */
export function acceptSuccessionPayload(args: {
  successorPubkey: Uint8Array;
  priorCultivatorPubkey: Uint8Array;
  anchorTimestampUnixNs: bigint;
  catechumenateSessionCount: bigint;
}): Map<string, Value> {
  requireLen("successor_pubkey", args.successorPubkey, 32);
  requireLen("prior_cultivator_pubkey", args.priorCultivatorPubkey, 32);
  const m = new Map<string, Value>();
  m.set("successor_pubkey", { type: "bytes", value: args.successorPubkey });
  m.set("prior_cultivator_pubkey", { type: "bytes", value: args.priorCultivatorPubkey });
  m.set("anchor_timestamp_unix_ns", { type: "timestamp", value: args.anchorTimestampUnixNs });
  m.set("catechumenate_session_count", { type: "uint", value: args.catechumenateSessionCount });
  return m;
}

/** Parsed `accept_succession_response`. */
export interface AcceptSuccessionResult {
  completedEventHash: Uint8Array;
  cultivationState: string;
}

export function parseAcceptSuccessionResponse(
  response: Message,
): AcceptSuccessionResult {
  if (response.messageType !== MSG_TYPE.ACCEPT_SUCCESSION_RESPONSE) {
    throw new BridgeProtocolError(
      `expected accept_succession_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("completed_event_hash");
  const stateV = response.payload.get("cultivation_state");
  if (!hashV || hashV.type !== "bytes" || !stateV || stateV.type !== "string") {
    throw new BridgeProtocolError(
      "accept_succession_response missing required typed fields",
    );
  }
  return { completedEventHash: hashV.value, cultivationState: stateV.value };
}

// ---------------------------------------------------------------------------
// accept_bet_retired_proposal (T7 / LB §4 → alive::archived).
// ---------------------------------------------------------------------------

/** Build the `accept_bet_retired_proposal` request payload (KEYLESS v0.9).
 *
 *  The cultivator Ed25519 co-attestation gate was removed with the anchor
 *  surface; the deliberate structural gate is that `proposal_hash` reference a
 *  real `bet_retired_proposal` DAG node, so this sends just the hash. */
export function acceptBetRetiredProposalPayload(args: {
  proposalHash: Uint8Array;
}): Map<string, Value> {
  requireLen("proposal_hash", args.proposalHash, 32);
  const m = new Map<string, Value>();
  m.set("proposal_hash", { type: "bytes", value: args.proposalHash });
  return m;
}

/** Parsed `accept_bet_retired_proposal_response`. */
export interface AcceptBetRetiredProposalResult {
  sealedEventHash: Uint8Array;
  reason: string;
}

export function parseAcceptBetRetiredProposalResponse(
  response: Message,
): AcceptBetRetiredProposalResult {
  if (response.messageType !== MSG_TYPE.ACCEPT_BET_RETIRED_PROPOSAL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected accept_bet_retired_proposal_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("sealed_event_hash");
  const reasonV = response.payload.get("reason");
  if (!hashV || hashV.type !== "bytes" || !reasonV || reasonV.type !== "string") {
    throw new BridgeProtocolError(
      "accept_bet_retired_proposal_response missing required typed fields",
    );
  }
  return { sealedEventHash: hashV.value, reason: reasonV.value };
}
