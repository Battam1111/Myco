// Bridge wire protocol — framing, constants, message-type registry, and the
// body / HMAC / frame-body codec.
//
// Split out of the former monolithic `protocol/messages.ts` (L4 M6). Mirror of
// Rust `kernel/bridge/rust/src/protocol.rs` and Python
// `kernel/bridge/python/src/myco_kernel_bridge/protocol.py`. The body Map
// shape, HMAC key derivation, and message types MUST match those modules
// byte-for-byte; any drift = L1/HARD_RULES C18 canonical_bytes_render_drift.
//
// ## Wire frame (length-prefixed)
//
// ```
//   [u32 BE length, 4 bytes][hmac, 32 bytes][body, length-32 bytes]
// ```
//
// Body = canonical-bytes Map with four keys (canonically sorted):
//
// - `v`: Uint(PROTOCOL_VERSION = 1)
// - `type`: String(message_type)
// - `request_id`: Uint(correlation_id)
// - `payload`: Map(type-specific)
//
// HMAC = HMAC-SHA256(body, key=session_secret). The `hello` message uses
// `BOOTSTRAP_KEY` instead of the (not-yet-exchanged) session_secret.

import { sha256 } from "@noble/hashes/sha2.js";
import { hmac } from "@noble/hashes/hmac.js";
import {
  CanonicalBytes,
  encode,
  type Value,
} from "../../canonical/canonical_bytes.ts";
import { decode } from "../../canonical/renderer.ts";

/** Bridge wire protocol version. Bumped on any breaking change. */
export const PROTOCOL_VERSION = 1n;

/** HMAC-SHA256 output size in bytes. */
export const HMAC_SIZE = 32;

/** Maximum frame body+hmac size on the wire (1 MiB). DoS protection. */
export const MAX_FRAME_BODY_SIZE = 1024 * 1024;

/** Bootstrap key for the `hello` message HMAC. Deterministic SHA-256 of the
 * literal `"myco-bridge-protocol-v1-bootstrap"`. Not a real secret — the IPC
 * channel is the trust boundary. Pinned identically across Rust/Python/TS. */
export const BOOTSTRAP_KEY: Uint8Array = sha256(
  new TextEncoder().encode("myco-bridge-protocol-v1-bootstrap"),
);

/** Message type string constants. Mirrors Rust `msg_type::*` and Python `MessageType`. */
export const MSG_TYPE = {
  HELLO: "hello",
  HELLO_ACK: "hello_ack",
  REGISTER_AXIS: "register_axis",
  REGISTER_AXIS_ACK: "register_axis_ack",
  PERTURB: "perturb",
  PERTURB_ACK: "perturb_ack",
  ADVANCE: "advance",
  ADVANCE_RESPONSE: "advance_response",
  SNAPSHOT: "snapshot",
  SNAPSHOT_RESPONSE: "snapshot_response",
  SHUTDOWN: "shutdown",
  SHUTDOWN_ACK: "shutdown_ack",
  ERROR: "error",
  COMPUTE_INTENT: "compute_intent",
  COMPUTE_INTENT_RESPONSE: "compute_intent_response",
  QUERY_RECENT_NODES: "query_recent_nodes",
  QUERY_RECENT_NODES_RESPONSE: "query_recent_nodes_response",
  READ_NODE_BY_HASH: "read_node_by_hash",
  READ_NODE_BY_HASH_RESPONSE: "read_node_by_hash_response",
  LIST_PLATES: "list_plates",
  LIST_PLATES_RESPONSE: "list_plates_response",
  SUBMIT_MUTATION: "submit_mutation",
  SUBMIT_MUTATION_RESPONSE: "submit_mutation_response",
  QUERY_IMMUNE_EVENTS: "query_immune_events",
  QUERY_IMMUNE_EVENTS_RESPONSE: "query_immune_events_response",
  RUN_IMMUNE_CHECK: "run_immune_check",
  RUN_IMMUNE_CHECK_RESPONSE: "run_immune_check_response",
  // v0.9 owner-key removal: REQUEST_ATTESTATION_NONCE(+_RESPONSE) removed — the
  // substrate no longer issues anchor-surface attestation nonces (CI mutations
  // are classified keyless by Python).
  ENUMERATE_DAG_SINCE: "enumerate_dag_since",
  ENUMERATE_DAG_SINCE_RESPONSE: "enumerate_dag_since_response",
  INGEST_RAW_MATERIAL: "ingest_raw_material",
  INGEST_RAW_MATERIAL_RESPONSE: "ingest_raw_material_response",
  PERTURB_AXIS_FROM_RAW_MATERIAL: "perturb_axis_from_raw_material",
  PERTURB_AXIS_FROM_RAW_MATERIAL_RESPONSE: "perturb_axis_from_raw_material_response",
  // The "use-forges" forging loop — deposit the agent's DIGESTED understanding
  // (forged out of raw_material) as a forged_understanding:{label} DAG node.
  DEPOSIT_FORGED_UNDERSTANDING: "deposit_forged_understanding",
  DEPOSIT_FORGED_UNDERSTANDING_RESPONSE: "deposit_forged_understanding_response",
  SPROUT_CHILD: "sprout_child",
  SPROUT_CHILD_RESPONSE: "sprout_child_response",
  // M22 P5 万物互联: inter-substrate federation (M25.5 TS wiring).
  FEDERATION_OPEN_LISTENER: "federation_open_listener",
  FEDERATION_OPEN_LISTENER_RESPONSE: "federation_open_listener_response",
  FEDERATION_CLOSE_LISTENER: "federation_close_listener",
  FEDERATION_CLOSE_LISTENER_RESPONSE: "federation_close_listener_response",
  FEDERATION_STATUS: "federation_status",
  FEDERATION_STATUS_RESPONSE: "federation_status_response",
  FEDERATION_CONNECT_PEER: "federation_connect_peer",
  FEDERATION_CONNECT_PEER_RESPONSE: "federation_connect_peer_response",
  FEDERATION_POLL: "federation_poll",
  FEDERATION_POLL_RESPONSE: "federation_poll_response",
  FEDERATION_PULL_EVENTS_FROM_PEER: "federation_pull_events_from_peer",
  FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE: "federation_pull_events_from_peer_response",
  FEDERATION_LINK_TO_PARENT_FROM_HINT: "federation_link_to_parent_from_hint",
  FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE: "federation_link_to_parent_from_hint_response",
  // L2/FEDERATION §6.5 — Stage-1 population-consensus floor (quorum cert).
  FEDERATION_PROPOSE_POPULATION_CLAIM: "federation_propose_population_claim",
  FEDERATION_PROPOSE_POPULATION_CLAIM_RESPONSE:
    "federation_propose_population_claim_response",
  FEDERATION_SUBMIT_PEER_VOTE: "federation_submit_peer_vote",
  FEDERATION_SUBMIT_PEER_VOTE_RESPONSE: "federation_submit_peer_vote_response",
  FEDERATION_QUERY_CONSENSUS: "federation_query_consensus",
  FEDERATION_QUERY_CONSENSUS_RESPONSE: "federation_query_consensus_response",
  // M22.5 P8 birth-period quarantine — operator owner-signed override.
  LIFT_BIRTH_PERIOD_QUARANTINE: "lift_birth_period_quarantine",
  LIFT_BIRTH_PERIOD_QUARANTINE_RESPONSE: "lift_birth_period_quarantine_response",
  // M23.2 P7 必朽 — self-euthanasia owner-co-attestation.
  ACCEPT_SELF_EUTHANASIA_PROPOSAL: "accept_self_euthanasia_proposal",
  ACCEPT_SELF_EUTHANASIA_PROPOSAL_RESPONSE: "accept_self_euthanasia_proposal_response",
  // Phase α / M24.5 — Living Bets observatory primitive.
  QUERY_SUBSTRATE_OBSERVATORY: "query_substrate_observatory",
  QUERY_SUBSTRATE_OBSERVATORY_RESPONSE: "query_substrate_observatory_response",
  // v3.1.1 Sprint 8.G (P03 §10.4) — two-phase schema migration status.
  QUERY_MIGRATION_PENDING: "query_migration_pending",
  QUERY_MIGRATION_PENDING_RESPONSE: "query_migration_pending_response",
  // COV06 不弃不孤 — cultivator-mortality + succession FSM (L1/GOVERNANCE §3.2).
  // v0.9 owner-key removal: RECORD_CULTIVATOR_HEARTBEAT(+_RESPONSE) removed (the
  // anchor-signed cultivator-liveness heartbeat handler + the staleness watchdog
  // were dropped with the anchor surface). The keyless succession FSM remains.
  UPDATE_SUCCESSOR_CHAIN: "update_successor_chain",
  UPDATE_SUCCESSOR_CHAIN_RESPONSE: "update_successor_chain_response",
  ACCEPT_SUCCESSION: "accept_succession",
  ACCEPT_SUCCESSION_RESPONSE: "accept_succession_response",
  ACCEPT_BET_RETIRED_PROPOSAL: "accept_bet_retired_proposal",
  ACCEPT_BET_RETIRED_PROPOSAL_RESPONSE: "accept_bet_retired_proposal_response",
  // CHAR07 §8.1/§8.2 cultivator-attested anti-tyranny assessment intake.
  SUBMIT_CHAR07_ASSESSMENT: "submit_char07_assessment",
  SUBMIT_CHAR07_ASSESSMENT_RESPONSE: "submit_char07_assessment_response",
} as const;

export type MessageType = (typeof MSG_TYPE)[keyof typeof MSG_TYPE];

/** A decoded bridge message. */
export interface Message {
  /** Protocol version. Always 1 on a valid M6 frame. */
  version: bigint;
  /** Message type tag. */
  messageType: string;
  /** Correlation ID — request and response share this value. */
  requestId: bigint;
  /** Type-specific payload Map. */
  payload: Map<string, Value>;
}

/** Bridge protocol error. */
export class BridgeProtocolError extends Error {
  constructor(message: string) {
    super(`bridge protocol: ${message}`);
    this.name = "BridgeProtocolError";
  }
}

/** Frame HMAC verification failure. */
export class HmacMismatchError extends BridgeProtocolError {
  constructor(message: string) {
    super(`HMAC mismatch: ${message}`);
    this.name = "HmacMismatchError";
  }
}

/** Frame body+hmac size exceeded the cap. */
export class FrameTooLargeError extends BridgeProtocolError {
  constructor(message: string) {
    super(`frame too large: ${message}`);
    this.name = "FrameTooLargeError";
  }
}

// ---------------------------------------------------------------------------
// Body encode / decode.
// ---------------------------------------------------------------------------

/** Encode the body of a message to canonical bytes (NOT including HMAC). */
export function bodyToCanonicalBytes(message: Message): CanonicalBytes {
  const bodyMap = new Map<string, Value>();
  bodyMap.set("v", { type: "uint", value: message.version });
  bodyMap.set("type", { type: "string", value: message.messageType });
  bodyMap.set("request_id", { type: "uint", value: message.requestId });
  bodyMap.set("payload", { type: "map", value: message.payload });
  return encode({ type: "map", value: bodyMap });
}

/** Decode a canonical-bytes body into a Message. */
export function canonicalBytesToBody(body: Uint8Array): Message {
  let decoded: Value;
  try {
    decoded = decode(new CanonicalBytes(body));
  } catch (e) {
    throw new BridgeProtocolError(
      `body decode failed: ${e instanceof Error ? e.message : String(e)}`,
    );
  }
  if (decoded.type !== "map") {
    throw new BridgeProtocolError(`body is not a Map: got ${decoded.type}`);
  }
  const map = decoded.value;

  const v = map.get("v");
  if (!v || v.type !== "uint") {
    throw new BridgeProtocolError("body missing/invalid 'v' field");
  }
  if (v.value !== PROTOCOL_VERSION) {
    throw new BridgeProtocolError(
      `protocol version mismatch: got ${v.value}, expected ${PROTOCOL_VERSION}`,
    );
  }
  const typeV = map.get("type");
  if (!typeV || typeV.type !== "string") {
    throw new BridgeProtocolError("body missing/invalid 'type' field");
  }
  const requestIdV = map.get("request_id");
  if (!requestIdV || requestIdV.type !== "uint") {
    throw new BridgeProtocolError("body missing/invalid 'request_id' field");
  }
  const payloadV = map.get("payload");
  if (!payloadV || payloadV.type !== "map") {
    throw new BridgeProtocolError("body missing/invalid 'payload' field");
  }

  return {
    version: v.value,
    messageType: typeV.value,
    requestId: requestIdV.value,
    payload: payloadV.value,
  };
}

// ---------------------------------------------------------------------------
// HMAC compute / verify.
// ---------------------------------------------------------------------------

/** Compute HMAC-SHA256 over `body` bytes with `key`. Returns 32 bytes. */
export function computeHmac(body: Uint8Array, key: Uint8Array): Uint8Array {
  if (key.length === 0) {
    throw new BridgeProtocolError("HMAC key cannot be empty (per L1/SKIN §2)");
  }
  return hmac(sha256, key, body);
}

/** Constant-time HMAC compare. */
function constantTimeCompare(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i]! ^ b[i]!;
  }
  return diff === 0;
}

// ---------------------------------------------------------------------------
// Frame body (HMAC + canonical-bytes body) encode / decode.
// ---------------------------------------------------------------------------

/**
 * Encode a message into a frame body (HMAC + canonical-bytes body).
 *
 * The caller (framing layer) prepends the u32 BE length prefix.
 */
export function encodeFrameBody(message: Message, key: Uint8Array): Uint8Array {
  const body = bodyToCanonicalBytes(message).bytes;
  const hmacBytes = computeHmac(body, key);
  const out = new Uint8Array(HMAC_SIZE + body.length);
  out.set(hmacBytes, 0);
  out.set(body, HMAC_SIZE);
  return out;
}

/** Decode a frame body (HMAC + canonical-bytes body) into a Message. */
export function decodeFrameBody(frame: Uint8Array, key: Uint8Array): Message {
  if (frame.length < HMAC_SIZE) {
    throw new BridgeProtocolError(
      `frame body too small: ${frame.length} < HMAC size ${HMAC_SIZE}`,
    );
  }
  const hmacReceived = frame.subarray(0, HMAC_SIZE);
  const body = frame.subarray(HMAC_SIZE);
  const hmacExpected = computeHmac(body, key);
  if (!constantTimeCompare(hmacReceived, hmacExpected)) {
    throw new HmacMismatchError(
      "frame HMAC verification failed (wrong key or wire corruption)",
    );
  }
  return canonicalBytesToBody(body);
}
