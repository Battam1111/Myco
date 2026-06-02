// COV06 不弃不孤 — cultivator-mortality + succession FSM operator messages.
//
// Mirrors the Rust handlers in `substrate/src/cultivation.rs`
// (`handle_record_cultivator_heartbeat` / `handle_update_successor_chain` /
// `handle_accept_succession` / `handle_accept_bet_retired_proposal`). The
// signing-input Map shapes are the security boundary; one byte off breaks the
// substrate signature check (the substrate re-derives + verifies these exact
// canonical-bytes envelopes).
//
// The substrate has NO anchor socket (AS §5.2 forbids self-clock); the operator
// threads the anchor-signed heartbeat / successor-chain / succession-acceptance
// envelopes in. In production the anchor signs; the operator forwards.

import { encode, type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

// ---------------------------------------------------------------------------
// Domain-separation contexts — MUST byte-match substrate/src/cultivation.rs.
// ---------------------------------------------------------------------------

const HEARTBEAT_CONTEXT = "myco-cultivator-liveness-heartbeat-v1";
const SUCCESSOR_CHAIN_CONTEXT = "myco-successor-chain-entry-v1";
const SUCCESSION_ACCEPTANCE_CONTEXT = "myco-succession-acceptance-v1";
const BET_RETIRED_CONTEXT = "myco-bet-retired-seal-v1";

function requireLen(name: string, b: Uint8Array, n: number): void {
  if (b.length !== n) {
    throw new BridgeProtocolError(`${name} must be ${n} bytes; got ${b.length}`);
  }
}

// ---------------------------------------------------------------------------
// record_cultivator_heartbeat (anchor-signed liveness pulse; AS §3.7).
// ---------------------------------------------------------------------------

/** Canonical signing input for the `cultivator_liveness_heartbeat` envelope.
 *  The anchor signs THIS; the substrate verifies against the active owner key. */
export function cultivatorHeartbeatSigningInput(
  substrateId: Uint8Array,
  cultivatorPubkey: Uint8Array,
  anchorTimestampUnixNs: bigint,
  validUntilUnixNs: bigint,
  heartbeatNonce: Uint8Array,
): Uint8Array {
  requireLen("substrate_id", substrateId, 32);
  requireLen("cultivator_pubkey", cultivatorPubkey, 32);
  requireLen("heartbeat_nonce", heartbeatNonce, 32);
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: HEARTBEAT_CONTEXT });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("cultivator_pubkey", { type: "bytes", value: cultivatorPubkey });
  m.set("anchor_timestamp_unix_ns", { type: "timestamp", value: anchorTimestampUnixNs });
  m.set("valid_until_unix_ns", { type: "timestamp", value: validUntilUnixNs });
  m.set("heartbeat_nonce", { type: "bytes", value: heartbeatNonce });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the `record_cultivator_heartbeat` request payload. */
export function recordCultivatorHeartbeatPayload(args: {
  cultivatorPubkey: Uint8Array;
  anchorTimestampUnixNs: bigint;
  validUntilUnixNs: bigint;
  heartbeatNonce: Uint8Array;
  anchorSignature: Uint8Array;
}): Map<string, Value> {
  requireLen("cultivator_pubkey", args.cultivatorPubkey, 32);
  requireLen("heartbeat_nonce", args.heartbeatNonce, 32);
  requireLen("anchor_signature", args.anchorSignature, 64);
  const m = new Map<string, Value>();
  m.set("cultivator_pubkey", { type: "bytes", value: args.cultivatorPubkey });
  m.set("anchor_timestamp_unix_ns", { type: "timestamp", value: args.anchorTimestampUnixNs });
  m.set("valid_until_unix_ns", { type: "timestamp", value: args.validUntilUnixNs });
  m.set("heartbeat_nonce", { type: "bytes", value: args.heartbeatNonce });
  m.set("anchor_signature", { type: "bytes", value: args.anchorSignature });
  return m;
}

/** Parsed `record_cultivator_heartbeat_response`. */
export interface RecordCultivatorHeartbeatResult {
  /** DAG node hash of the emitted `cultivator_heartbeat_recorded` event. */
  recordedEventHash: Uint8Array;
  /** True iff a `cultivator_heartbeat_resumed` (T2) was also emitted. */
  resumed: boolean;
  /** The substrate's cultivation FSM sub-state after this pulse. */
  cultivationState: string;
}

export function parseRecordCultivatorHeartbeatResponse(
  response: Message,
): RecordCultivatorHeartbeatResult {
  if (response.messageType !== MSG_TYPE.RECORD_CULTIVATOR_HEARTBEAT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected record_cultivator_heartbeat_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("recorded_event_hash");
  const resumedV = response.payload.get("resumed");
  const stateV = response.payload.get("cultivation_state");
  if (
    !hashV || hashV.type !== "bytes" ||
    !resumedV || resumedV.type !== "bool" ||
    !stateV || stateV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "record_cultivator_heartbeat_response missing required typed fields",
    );
  }
  return {
    recordedEventHash: hashV.value,
    resumed: resumedV.value,
    cultivationState: stateV.value,
  };
}

// ---------------------------------------------------------------------------
// update_successor_chain (F21 SuccessorEntry append; §3.2.A).
// ---------------------------------------------------------------------------

/** Canonical signing input for a successor-chain-entry attestation. The active
 *  cultivator (or alive::legacy cultivator) signs THIS. `validUntilUnixNs`
 *  null → open-ended interval. */
export function successorChainSigningInput(
  substrateId: Uint8Array,
  successorPubkey: Uint8Array,
  validFromUnixNs: bigint,
  validUntilUnixNs: bigint | null,
): Uint8Array {
  requireLen("substrate_id", substrateId, 32);
  requireLen("successor_pubkey", successorPubkey, 32);
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: SUCCESSOR_CHAIN_CONTEXT });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("successor_pubkey", { type: "bytes", value: successorPubkey });
  m.set("valid_from_unix_ns", { type: "timestamp", value: validFromUnixNs });
  m.set(
    "valid_until_unix_ns",
    validUntilUnixNs === null
      ? { type: "null" }
      : { type: "timestamp", value: validUntilUnixNs },
  );
  return encode({ type: "map", value: m }).bytes;
}

/** Build the `update_successor_chain` request payload. */
export function updateSuccessorChainPayload(args: {
  successorPubkey: Uint8Array;
  validFromUnixNs: bigint;
  validUntilUnixNs: bigint | null;
  attestationSignature: Uint8Array;
}): Map<string, Value> {
  requireLen("successor_pubkey", args.successorPubkey, 32);
  requireLen("attestation_signature", args.attestationSignature, 64);
  const m = new Map<string, Value>();
  m.set("successor_pubkey", { type: "bytes", value: args.successorPubkey });
  m.set("valid_from_unix_ns", { type: "timestamp", value: args.validFromUnixNs });
  m.set(
    "valid_until_unix_ns",
    args.validUntilUnixNs === null
      ? { type: "null" }
      : { type: "timestamp", value: args.validUntilUnixNs },
  );
  m.set("attestation_signature", { type: "bytes", value: args.attestationSignature });
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
// accept_succession (T3 legacy→normal; the successor signs the acceptance).
// ---------------------------------------------------------------------------

/** Canonical signing input for a `succession_acceptance`. The successor signs
 *  THIS with their OWN key. */
export function successionAcceptanceSigningInput(
  substrateId: Uint8Array,
  successorPubkey: Uint8Array,
  priorCultivatorPubkey: Uint8Array,
  anchorTimestampUnixNs: bigint,
): Uint8Array {
  requireLen("substrate_id", substrateId, 32);
  requireLen("successor_pubkey", successorPubkey, 32);
  requireLen("prior_cultivator_pubkey", priorCultivatorPubkey, 32);
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: SUCCESSION_ACCEPTANCE_CONTEXT });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("successor_pubkey", { type: "bytes", value: successorPubkey });
  m.set("prior_cultivator_pubkey", { type: "bytes", value: priorCultivatorPubkey });
  m.set("anchor_timestamp_unix_ns", { type: "timestamp", value: anchorTimestampUnixNs });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the `accept_succession` request payload. */
export function acceptSuccessionPayload(args: {
  successorPubkey: Uint8Array;
  priorCultivatorPubkey: Uint8Array;
  anchorTimestampUnixNs: bigint;
  successorSignature: Uint8Array;
  catechumenateSessionCount: bigint;
}): Map<string, Value> {
  requireLen("successor_pubkey", args.successorPubkey, 32);
  requireLen("prior_cultivator_pubkey", args.priorCultivatorPubkey, 32);
  requireLen("successor_signature", args.successorSignature, 64);
  const m = new Map<string, Value>();
  m.set("successor_pubkey", { type: "bytes", value: args.successorPubkey });
  m.set("prior_cultivator_pubkey", { type: "bytes", value: args.priorCultivatorPubkey });
  m.set("anchor_timestamp_unix_ns", { type: "timestamp", value: args.anchorTimestampUnixNs });
  m.set("successor_signature", { type: "bytes", value: args.successorSignature });
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

/** Canonical signing input for the bet-retirement co-attestation. The
 *  cultivator signs THIS over the proposal hash. */
export function betRetiredSealSigningInput(
  substrateId: Uint8Array,
  proposalHash: Uint8Array,
): Uint8Array {
  requireLen("substrate_id", substrateId, 32);
  requireLen("proposal_hash", proposalHash, 32);
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: BET_RETIRED_CONTEXT });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("proposal_hash", { type: "bytes", value: proposalHash });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the `accept_bet_retired_proposal` request payload. */
export function acceptBetRetiredProposalPayload(args: {
  proposalHash: Uint8Array;
  cultivatorSignature: Uint8Array;
}): Map<string, Value> {
  requireLen("proposal_hash", args.proposalHash, 32);
  requireLen("cultivator_signature", args.cultivatorSignature, 64);
  const m = new Map<string, Value>();
  m.set("proposal_hash", { type: "bytes", value: args.proposalHash });
  m.set("cultivator_signature", { type: "bytes", value: args.cultivatorSignature });
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
