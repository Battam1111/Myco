// Bridge wire protocol — TypeScript implementation (L4 M6).
//
// Mirror of Rust `kernel/bridge/src/protocol.rs` and Python
// `kernel/bridge_python/src/myco_kernel_bridge/protocol.py`. The body Map
// shape, HMAC key derivation, and message types MUST match those modules
// byte-for-byte; any drift = L1_HARD_RULES C18 canonical_bytes_render_drift.
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
  CanonicalBytesError,
  encode,
  type Value,
} from "@myco/anchor-client/src/canonical_bytes.ts";
import { decode } from "@myco/anchor-client/src/renderer.ts";

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
  SUBMIT_MUTATION: "submit_mutation",
  SUBMIT_MUTATION_RESPONSE: "submit_mutation_response",
  QUERY_IMMUNE_EVENTS: "query_immune_events",
  QUERY_IMMUNE_EVENTS_RESPONSE: "query_immune_events_response",
  RUN_IMMUNE_CHECK: "run_immune_check",
  RUN_IMMUNE_CHECK_RESPONSE: "run_immune_check_response",
  REQUEST_ATTESTATION_NONCE: "request_attestation_nonce",
  REQUEST_ATTESTATION_NONCE_RESPONSE: "request_attestation_nonce_response",
  ENUMERATE_DAG_SINCE: "enumerate_dag_since",
  ENUMERATE_DAG_SINCE_RESPONSE: "enumerate_dag_since_response",
  INGEST_RAW_MATERIAL: "ingest_raw_material",
  INGEST_RAW_MATERIAL_RESPONSE: "ingest_raw_material_response",
  PERTURB_AXIS_FROM_RAW_MATERIAL: "perturb_axis_from_raw_material",
  PERTURB_AXIS_FROM_RAW_MATERIAL_RESPONSE: "perturb_axis_from_raw_material_response",
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
  // M22.5 P8 birth-period quarantine — operator owner-signed override.
  LIFT_BIRTH_PERIOD_QUARANTINE: "lift_birth_period_quarantine",
  LIFT_BIRTH_PERIOD_QUARANTINE_RESPONSE: "lift_birth_period_quarantine_response",
  // M23.2 P7 必朽 — self-euthanasia owner-co-attestation.
  ACCEPT_SELF_EUTHANASIA_PROPOSAL: "accept_self_euthanasia_proposal",
  ACCEPT_SELF_EUTHANASIA_PROPOSAL_RESPONSE: "accept_self_euthanasia_proposal_response",
  // Phase α / M24.5 — Living Bets observatory primitive.
  QUERY_SUBSTRATE_OBSERVATORY: "query_substrate_observatory",
  QUERY_SUBSTRATE_OBSERVATORY_RESPONSE: "query_substrate_observatory_response",
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
    throw new BridgeProtocolError("HMAC key cannot be empty (per L1_SKIN §2)");
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

// ---------------------------------------------------------------------------
// Payload builders for common messages.
// ---------------------------------------------------------------------------

/** Build the payload for a `hello` request.
 *
 * M5-M8 minimum: only `session_secret`.
 * M9+ extended: also include `operator_pubkey` + `hello_signature` for TOFU pinning.
 *
 * The signature is computed over `canonical-bytes(Map({session_secret, operator_pubkey}))`
 * — i.e., the body without the signature field itself. Callers should pass
 * `null` for `operatorPubkey` / `helloSignature` for M5-M8 backward-compatible
 * mode (no identity binding).
 */
export function helloPayload(
  sessionSecret: Uint8Array,
  operatorPubkey?: Uint8Array,
  helloSignature?: Uint8Array,
): Map<string, Value> {
  if (sessionSecret.length !== 32) {
    throw new BridgeProtocolError(
      `session_secret must be exactly 32 bytes; got ${sessionSecret.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("session_secret", { type: "bytes", value: sessionSecret });
  if (operatorPubkey) {
    if (operatorPubkey.length !== 32) {
      throw new BridgeProtocolError(
        `operator_pubkey must be exactly 32 bytes; got ${operatorPubkey.length}`,
      );
    }
    m.set("operator_pubkey", { type: "bytes", value: operatorPubkey });
  }
  if (helloSignature) {
    if (helloSignature.length !== 64) {
      throw new BridgeProtocolError(
        `hello_signature must be exactly 64 bytes; got ${helloSignature.length}`,
      );
    }
    m.set("hello_signature", { type: "bytes", value: helloSignature });
  }
  return m;
}

/** Compute the canonical bytes of a hello body for signing (M9).
 *
 *  The signature input is the canonical-bytes encoding of a Map containing
 *  ONLY the session_secret + operator_pubkey fields. The hello_signature
 *  field itself is excluded (avoids recursive self-reference).
 *
 *  This must match the substrate-side reconstruction exactly.
 */
export function helloSigningBody(
  sessionSecret: Uint8Array,
  operatorPubkey: Uint8Array,
): Uint8Array {
  const m = new Map<string, Value>();
  m.set("session_secret", { type: "bytes", value: sessionSecret });
  m.set("operator_pubkey", { type: "bytes", value: operatorPubkey });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for a `register_axis` request. */
export function registerAxisPayload(args: {
  name: string;
  axisClass: "appetite" | "decay";
  fruitingThreshold: number;
  initialValue: number;
  decayRatePerCycle: number;
  isMortalitySignal: boolean;
  updateRuleKind: "noop" | "decay";
}): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("name", { type: "string", value: args.name });
  m.set("axis_class", { type: "string", value: args.axisClass });
  m.set("fruiting_threshold_repr", {
    type: "string",
    value: floatRepr(args.fruitingThreshold),
  });
  m.set("initial_value_repr", {
    type: "string",
    value: floatRepr(args.initialValue),
  });
  m.set("decay_rate_per_cycle_repr", {
    type: "string",
    value: floatRepr(args.decayRatePerCycle),
  });
  m.set("is_mortality_signal", {
    type: "bool",
    value: args.isMortalitySignal,
  });
  m.set("update_rule_kind", { type: "string", value: args.updateRuleKind });
  return m;
}

/** Build the payload for a `perturb` request. */
export function perturbPayload(
  axisName: string,
  delta: number,
): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("axis_name", { type: "string", value: axisName });
  m.set("delta_repr", { type: "string", value: floatRepr(delta) });
  return m;
}

/** Build the payload for an `advance` request. */
export function advancePayload(currentCycle: bigint): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("current_cycle", { type: "uint", value: currentCycle });
  return m;
}

/** Empty payload (snapshot, *_ack, shutdown, etc.). */
export function emptyPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Build the payload for a `query_recent_nodes` request (M8;
 *  extended M16 with optional `nodeTypePrefix` filter).
 *
 *  When `nodeTypePrefix` is set, the substrate returns only nodes whose
 *  node_type starts with the prefix (e.g. `"raw_material:"` for ingested
 *  raw material; `"mutation:"` for accepted mutations; `"immune:"` for
 *  immune sporocarps). Absent = no filter (return all node types).
 */
export function queryRecentNodesPayload(
  count: bigint,
  nodeTypePrefix?: string,
): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("count", { type: "uint", value: count });
  if (nodeTypePrefix !== undefined) {
    m.set("node_type_prefix", { type: "string", value: nodeTypePrefix });
  }
  return m;
}

// ---------------------------------------------------------------------------
// M20 P8 永恒繁衍: substrate reproduction (sprout_child).
// ---------------------------------------------------------------------------

/** Build the payload for a `sprout_child` request (M20).
 *
 *  The substrate creates a child state_dir containing the parent's
 *  spore-schema (gradient axes + values + operator identity + fresh
 *  substrate_id). Operator can then spawn a new substrate process at
 *  `childStateDir` via the MYCO_STATE_DIR env var.
 *
 *  The parent emits a `spore_emission:{child_id_prefix}` DAG node recording
 *  the reproduction. The parent's causal DAG is NOT transferred to the child
 *  (L1 decision per L0 P8 — child starts its own causal history).
 */
export function sproutChildPayload(args: {
  childStateDir: string;
  spore_metadata?: Map<string, Value>;
}): Map<string, Value> {
  if (!args.childStateDir || args.childStateDir.length === 0) {
    throw new BridgeProtocolError("sprout_child: childStateDir is required");
  }
  const m = new Map<string, Value>();
  m.set("child_state_dir", { type: "string", value: args.childStateDir });
  if (args.spore_metadata) {
    m.set("spore_metadata", { type: "map", value: args.spore_metadata });
  }
  return m;
}

/** Parsed `sprout_child_response` (M20). */
export interface SproutChildResult {
  childSubstrateId: Uint8Array;
  childStateDir: string;
  childAxisCount: bigint;
  /** DAG node hash of the spore_emission:{prefix} node in the parent's DAG. */
  sporeEmissionHash: Uint8Array;
}

export function parseSproutChildResponse(response: Message): SproutChildResult {
  if (response.messageType !== MSG_TYPE.SPROUT_CHILD_RESPONSE) {
    throw new BridgeProtocolError(
      `expected sprout_child_response; got ${response.messageType}`,
    );
  }
  const idV = response.payload.get("child_substrate_id");
  const dirV = response.payload.get("child_state_dir");
  const axisV = response.payload.get("child_axis_count");
  const hashV = response.payload.get("spore_emission_hash");
  if (
    !idV || idV.type !== "bytes" ||
    !dirV || dirV.type !== "string" ||
    !axisV || axisV.type !== "uint" ||
    !hashV || hashV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "sprout_child_response missing required typed fields",
    );
  }
  return {
    childSubstrateId: idV.value,
    childStateDir: dirV.value,
    childAxisCount: axisV.value,
    sporeEmissionHash: hashV.value,
  };
}

// ---------------------------------------------------------------------------
// M25.5 P5 万物互联: operator-facing federation message builders/parsers.
//
// All payloads/responses mirror `myco_substrate::server::handle_federation_*`
// + `handle_lift_birth_period_quarantine` + `handle_accept_self_euthanasia_proposal`
// + `handle_query_substrate_observatory`. Field name/type drift = bridge
// protocol drift, surface as decode errors here.
// ---------------------------------------------------------------------------

/** Build the payload for a `federation_open_listener` request (M22.1).
 *
 *  `bindAddr` may be `"127.0.0.1:0"` to let the OS pick a port. Resolved
 *  address is returned by the substrate in the response.
 */
export function federationOpenListenerPayload(args: {
  bindAddr: string;
}): Map<string, Value> {
  if (!args.bindAddr || args.bindAddr.length === 0) {
    throw new BridgeProtocolError(
      "federation_open_listener: bind_addr must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("bind_addr", { type: "string", value: args.bindAddr });
  return m;
}

/** Parsed `federation_open_listener_response` (M22.1). */
export interface FederationOpenListenerResult {
  /** Resolved bind address (port-zero replaced by OS-picked port). */
  boundAddr: string;
  /** DAG node hash of the `federation_listener_opened` event. */
  listenerOpenedEventHash: Uint8Array;
}

export function parseFederationOpenListenerResponse(
  response: Message,
): FederationOpenListenerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_OPEN_LISTENER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_open_listener_response; got ${response.messageType}`,
    );
  }
  const addrV = response.payload.get("bind_addr");
  const hashV = response.payload.get("listener_opened_event_hash");
  if (
    !addrV || addrV.type !== "string" ||
    !hashV || hashV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "federation_open_listener_response missing required typed fields",
    );
  }
  return {
    boundAddr: addrV.value,
    listenerOpenedEventHash: hashV.value,
  };
}

/** Build the payload for a `federation_close_listener` request (M22.1).
 *  Empty payload — idempotent, no-op if no listener active. */
export function federationCloseListenerPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_close_listener_response` (M22.1). */
export interface FederationCloseListenerResult {
  /** True iff a listener was active and got closed. */
  wasListening: boolean;
  /** The address that was bound (empty string when wasListening=false). */
  priorBindAddr: string;
  /** DAG hash of the `federation_listener_closed` event; null if no listener. */
  listenerClosedEventHash: Uint8Array | null;
}

export function parseFederationCloseListenerResponse(
  response: Message,
): FederationCloseListenerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_CLOSE_LISTENER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_close_listener_response; got ${response.messageType}`,
    );
  }
  const wasV = response.payload.get("was_listening");
  const addrV = response.payload.get("prior_bind_addr");
  if (
    !wasV || wasV.type !== "bool" ||
    !addrV || addrV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "federation_close_listener_response missing required typed fields",
    );
  }
  const hashV = response.payload.get("listener_closed_event_hash");
  return {
    wasListening: wasV.value,
    priorBindAddr: addrV.value,
    listenerClosedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for a `federation_status` request (M22.1).
 *  Empty payload — read-only state query. */
export function federationStatusPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_status_response` (M22.1). */
export interface FederationStatusResult {
  /** True iff a listener is currently bound. */
  isListening: boolean;
  /** Currently bound address; empty string when not listening. */
  boundAddr: string;
  /** Count of currently-tracked peers (any state — pending, established, etc.). */
  peerCount: bigint;
  /** Total federation events ingested from peers since process start. */
  eventsReceivedTotal: bigint;
  /** Total federation events sent to peers since process start. */
  eventsSentTotal: bigint;
}

export function parseFederationStatusResponse(
  response: Message,
): FederationStatusResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_STATUS_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_status_response; got ${response.messageType}`,
    );
  }
  const isV = response.payload.get("is_listening");
  const addrV = response.payload.get("bind_addr");
  const peerV = response.payload.get("peer_count");
  const recvV = response.payload.get("events_received_total");
  const sentV = response.payload.get("events_sent_total");
  if (
    !isV || isV.type !== "bool" ||
    !addrV || addrV.type !== "string" ||
    !peerV || peerV.type !== "uint" ||
    !recvV || recvV.type !== "uint" ||
    !sentV || sentV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "federation_status_response missing required typed fields",
    );
  }
  return {
    isListening: isV.value,
    boundAddr: addrV.value,
    peerCount: peerV.value,
    eventsReceivedTotal: recvV.value,
    eventsSentTotal: sentV.value,
  };
}

/** Build the payload for a `federation_connect_peer` request (M22.2). */
export function federationConnectPeerPayload(args: {
  remoteAddr: string;
}): Map<string, Value> {
  if (!args.remoteAddr || args.remoteAddr.length === 0) {
    throw new BridgeProtocolError(
      "federation_connect_peer: remote_addr must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("remote_addr", { type: "string", value: args.remoteAddr });
  return m;
}

/** Parsed `federation_connect_peer_response` (M22.2). */
export interface FederationConnectPeerResult {
  /** One of: "pinned" | "self_connection" | "identity_drift" | "already_pinned". */
  outcome: string;
  /** Set when outcome ∈ {"pinned","identity_drift","already_pinned"}. */
  peerSubstrateId: Uint8Array | null;
  /** Echo of remote_addr (or substrate-determined string for some outcomes). */
  remoteAddr: string;
  /** Peer's reported DAG tip (only present on initial "pinned" outcome). */
  peerDagTip: Uint8Array | null;
  /** DAG hash of `federation_peer_pinned` event; present only when newly pinned. */
  peerPinnedEventHash: Uint8Array | null;
}

export function parseFederationConnectPeerResponse(
  response: Message,
): FederationConnectPeerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_CONNECT_PEER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_connect_peer_response; got ${response.messageType}`,
    );
  }
  const outV = response.payload.get("outcome");
  const addrV = response.payload.get("remote_addr");
  if (
    !outV || outV.type !== "string" ||
    !addrV || addrV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "federation_connect_peer_response missing required typed fields",
    );
  }
  const idV = response.payload.get("peer_substrate_id");
  const tipV = response.payload.get("peer_dag_tip");
  const hashV = response.payload.get("peer_pinned_event_hash");
  return {
    outcome: outV.value,
    peerSubstrateId: idV && idV.type === "bytes" ? idV.value : null,
    remoteAddr: addrV.value,
    peerDagTip: tipV && tipV.type === "bytes" ? tipV.value : null,
    peerPinnedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for a `federation_poll` request (M22.2). Empty payload. */
export function federationPollPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_poll_response` (M22.2). */
export interface FederationPollResult {
  /** Count of inbound connections accepted this poll. */
  acceptedConnections: bigint;
  /** Count of peers newly pinned this poll (via inbound HELLO completion). */
  pinnedPeers: bigint;
  /** Count of peers rejected this poll (TOFU mismatches, frame errors). */
  rejectedPeers: bigint;
  /** Count of outbound event batches sent to peers this poll. */
  eventBatchesSent: bigint;
}

export function parseFederationPollResponse(
  response: Message,
): FederationPollResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_POLL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_poll_response; got ${response.messageType}`,
    );
  }
  const acceptedV = response.payload.get("accepted_connections");
  const pinnedV = response.payload.get("pinned_peers");
  const rejectedV = response.payload.get("rejected_peers");
  const sentV = response.payload.get("event_batches_sent");
  if (
    !acceptedV || acceptedV.type !== "uint" ||
    !pinnedV || pinnedV.type !== "uint" ||
    !rejectedV || rejectedV.type !== "uint" ||
    !sentV || sentV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "federation_poll_response missing required typed fields",
    );
  }
  return {
    acceptedConnections: acceptedV.value,
    pinnedPeers: pinnedV.value,
    rejectedPeers: rejectedV.value,
    eventBatchesSent: sentV.value,
  };
}

/** Build the payload for `federation_pull_events_from_peer` (M22.3). */
export function federationPullEventsFromPeerPayload(args: {
  peerSubstrateId: Uint8Array;
  sinceNodeHash?: Uint8Array;
  maxEvents?: bigint;
}): Map<string, Value> {
  if (args.peerSubstrateId.length !== 32) {
    throw new BridgeProtocolError(
      `peer_substrate_id must be 32 bytes; got ${args.peerSubstrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("peer_substrate_id", { type: "bytes", value: args.peerSubstrateId });
  if (args.sinceNodeHash !== undefined) {
    if (args.sinceNodeHash.length !== 32) {
      throw new BridgeProtocolError(
        `since_node_hash must be 32 bytes; got ${args.sinceNodeHash.length}`,
      );
    }
    m.set("since_node_hash", { type: "bytes", value: args.sinceNodeHash });
  }
  if (args.maxEvents !== undefined) {
    m.set("max_events", { type: "uint", value: args.maxEvents });
  }
  return m;
}

/** Parsed `federation_pull_events_from_peer_response` (M22.3). */
export interface FederationPullEventsFromPeerResult {
  /** Count of events the peer returned. */
  eventsReceivedCount: bigint;
  /** Count of events ingested into the receiver's DAG as
   *  `federation_received:{peer_prefix}` wrappers (allowlist-filtered). */
  eventsIngestedCount: bigint;
  /** True iff the peer indicated this batch completes its known events. */
  isLastBatch: boolean;
  /** DAG node hash of the `federation_events_received` marker emitted by the
   *  receiver; null if no events were ingested (allowlist may have filtered all). */
  eventsReceivedEventHash: Uint8Array | null;
}

export function parseFederationPullEventsFromPeerResponse(
  response: Message,
): FederationPullEventsFromPeerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_pull_events_from_peer_response; got ${response.messageType}`,
    );
  }
  const recvV = response.payload.get("events_received_count");
  const ingV = response.payload.get("events_ingested_count");
  const lastV = response.payload.get("is_last_batch");
  if (
    !recvV || recvV.type !== "uint" ||
    !ingV || ingV.type !== "uint" ||
    !lastV || lastV.type !== "bool"
  ) {
    throw new BridgeProtocolError(
      "federation_pull_events_from_peer_response missing required typed fields",
    );
  }
  const hashV = response.payload.get("events_received_event_hash");
  return {
    eventsReceivedCount: recvV.value,
    eventsIngestedCount: ingV.value,
    isLastBatch: lastV.value,
    eventsReceivedEventHash:
      hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for `federation_link_to_parent_from_hint` (M22.4).
 *  Empty payload — substrate scans its own DAG for the hint event. */
export function federationLinkToParentFromHintPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_link_to_parent_from_hint_response` (M22.4). */
export interface FederationLinkToParentFromHintResult {
  /** True iff a parent_federation_hint event was found in the DAG. */
  hintFound: boolean;
  /** True iff a federation_parent_linked event already existed (idempotent). */
  alreadyLinked: boolean;
  /** Present when hintFound=true. */
  parentSubstrateId: Uint8Array | null;
  /** Present when hintFound=true. */
  parentFederationAddr: string | null;
  /** Present when a new federation_parent_linked event was emitted. */
  parentLinkedEventHash: Uint8Array | null;
  /** Present when hintFound=true but connect failed
   *  (values: "self_connection" | "identity_drift" | "already_pinned" | "unknown"). */
  connectOutcome: string | null;
}

export function parseFederationLinkToParentFromHintResponse(
  response: Message,
): FederationLinkToParentFromHintResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_link_to_parent_from_hint_response; got ${response.messageType}`,
    );
  }
  const foundV = response.payload.get("hint_found");
  const linkedV = response.payload.get("already_linked");
  if (
    !foundV || foundV.type !== "bool" ||
    !linkedV || linkedV.type !== "bool"
  ) {
    throw new BridgeProtocolError(
      "federation_link_to_parent_from_hint_response missing required typed fields",
    );
  }
  const idV = response.payload.get("parent_substrate_id");
  const addrV = response.payload.get("parent_federation_addr");
  const hashV = response.payload.get("parent_linked_event_hash");
  const outV = response.payload.get("connect_outcome");
  return {
    hintFound: foundV.value,
    alreadyLinked: linkedV.value,
    parentSubstrateId: idV && idV.type === "bytes" ? idV.value : null,
    parentFederationAddr: addrV && addrV.type === "string" ? addrV.value : null,
    parentLinkedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
    connectOutcome: outV && outV.type === "string" ? outV.value : null,
  };
}

/** Compute the canonical-bytes signing input for `lift_birth_period_quarantine`
 *  owner attestation (M22.5; Phase β security fix).
 *
 *  Mirrors Rust reconstruction in `handle_lift_birth_period_quarantine`:
 *  ```
 *  canonical_bytes(Map({
 *    "context": "myco-lift-birth-period-quarantine-v1",
 *    "substrate_id": Bytes(32),
 *    "current_cycle": Uint(cycle_counter),
 *  }))
 *  ```
 *
 *  The operator IDENTITY key signs THIS. The `current_cycle` field binds the
 *  signature to a specific point in time — replay across cycles is blocked.
 */
export function liftBirthPeriodQuarantineSigningInput(
  substrateId: Uint8Array,
  currentCycle: bigint,
): Uint8Array {
  if (substrateId.length !== 32) {
    throw new BridgeProtocolError(
      `substrate_id must be 32 bytes; got ${substrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("context", {
    type: "string",
    value: "myco-lift-birth-period-quarantine-v1",
  });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("current_cycle", { type: "uint", value: currentCycle });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for `lift_birth_period_quarantine` (M22.5). */
export function liftBirthPeriodQuarantinePayload(args: {
  ownerSignature: Uint8Array;
}): Map<string, Value> {
  if (args.ownerSignature.length !== 64) {
    throw new BridgeProtocolError(
      `owner_signature must be 64 bytes; got ${args.ownerSignature.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("owner_signature", { type: "bytes", value: args.ownerSignature });
  return m;
}

/** Parsed `lift_birth_period_quarantine_response` (M22.5). */
export interface LiftBirthPeriodQuarantineResult {
  /** True iff the substrate was in active quarantine when the call landed. */
  wasInQuarantine: boolean;
  /** DAG node hash of the emitted `birth_period_quarantine_lifted` event;
   *  null when wasInQuarantine=false (nothing to lift). */
  quarantineLiftedEventHash: Uint8Array | null;
}

export function parseLiftBirthPeriodQuarantineResponse(
  response: Message,
): LiftBirthPeriodQuarantineResult {
  if (response.messageType !== MSG_TYPE.LIFT_BIRTH_PERIOD_QUARANTINE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected lift_birth_period_quarantine_response; got ${response.messageType}`,
    );
  }
  const wasV = response.payload.get("was_in_quarantine");
  if (!wasV || wasV.type !== "bool") {
    throw new BridgeProtocolError(
      "lift_birth_period_quarantine_response missing was_in_quarantine bool",
    );
  }
  const hashV = response.payload.get("quarantine_lifted_event_hash");
  return {
    wasInQuarantine: wasV.value,
    quarantineLiftedEventHash:
      hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Compute the canonical-bytes signing input for `accept_self_euthanasia_proposal`
 *  owner co-attestation (M23.2 P7 必朽).
 *
 *  Mirrors Rust reconstruction in `handle_accept_self_euthanasia_proposal`:
 *  ```
 *  canonical_bytes(Map({
 *    "context": "myco-self-euthanasia-v1",
 *    "proposal_hash": Bytes(32),
 *    "substrate_id": Bytes(32),
 *  }))
 *  ```
 *
 *  The operator IDENTITY key signs THIS. The triple binding
 *  (context + proposal_hash + substrate_id) prevents replay:
 *  - context: distinct from other operator co-attestations
 *  - proposal_hash: this specific proposal in this DAG
 *  - substrate_id: not replayable against another substrate
 */
export function acceptSelfEuthanasiaProposalSigningInput(
  proposalHash: Uint8Array,
  substrateId: Uint8Array,
): Uint8Array {
  if (proposalHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposal_hash must be 32 bytes; got ${proposalHash.length}`,
    );
  }
  if (substrateId.length !== 32) {
    throw new BridgeProtocolError(
      `substrate_id must be 32 bytes; got ${substrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: "myco-self-euthanasia-v1" });
  m.set("proposal_hash", { type: "bytes", value: proposalHash });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for `accept_self_euthanasia_proposal` (M23.2). */
export function acceptSelfEuthanasiaProposalPayload(args: {
  proposalHash: Uint8Array;
  ownerSignature: Uint8Array;
}): Map<string, Value> {
  if (args.proposalHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposal_hash must be 32 bytes; got ${args.proposalHash.length}`,
    );
  }
  if (args.ownerSignature.length !== 64) {
    throw new BridgeProtocolError(
      `owner_signature must be 64 bytes; got ${args.ownerSignature.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("proposal_hash", { type: "bytes", value: args.proposalHash });
  m.set("owner_signature", { type: "bytes", value: args.ownerSignature });
  return m;
}

/** Parsed `accept_self_euthanasia_proposal_response` (M23.2). */
export interface AcceptSelfEuthanasiaProposalResult {
  /** The mortality_signal axis name that originally fruited (echoed from proposal). */
  axisName: string;
  /** DAG node hash of the emitted `self_euthanasia_executed:{axis}` event —
   *  the substrate's signed post-mortem record. The substrate gracefully
   *  shuts down AFTER this response is written. */
  executedEventHash: Uint8Array;
}

export function parseAcceptSelfEuthanasiaProposalResponse(
  response: Message,
): AcceptSelfEuthanasiaProposalResult {
  if (response.messageType !== MSG_TYPE.ACCEPT_SELF_EUTHANASIA_PROPOSAL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected accept_self_euthanasia_proposal_response; got ${response.messageType}`,
    );
  }
  const axisV = response.payload.get("axis_name");
  const hashV = response.payload.get("executed_event_hash");
  if (
    !axisV || axisV.type !== "string" ||
    !hashV || hashV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "accept_self_euthanasia_proposal_response missing required typed fields",
    );
  }
  return {
    axisName: axisV.value,
    executedEventHash: hashV.value,
  };
}

/** Build the payload for `query_substrate_observatory` (Phase α / M24.5).
 *
 *  `operatorAttestedContextWindowBytes` is optional. When supplied, the
 *  substrate computes signal #6 (read-window-relative position); otherwise
 *  signal #6 is omitted from the response.
 */
export function querySubstrateObservatoryPayload(args: {
  operatorAttestedContextWindowBytes?: bigint;
} = {}): Map<string, Value> {
  const m = new Map<string, Value>();
  if (args.operatorAttestedContextWindowBytes !== undefined) {
    m.set("operator_attested_context_window_bytes", {
      type: "uint",
      value: args.operatorAttestedContextWindowBytes,
    });
  }
  return m;
}

/** Signal #1 — persistence budget. Always present in v1+. */
export interface ObservatorySignal1 {
  dagNodeCount: bigint;
  dagEdgeCount: bigint;
  dagTotalContentBytes: bigint;
  manifestCycleCounter: bigint;
}

/** Signal #2 — evolution rate. Present from format_version >= 2. */
export interface ObservatorySignal2 {
  evolutionEventCount: bigint;
  axisRegisterCount: bigint;
  /** evolution_event_count / max(1, manifest_cycle_counter). */
  rate: number;
}

/** Signal #3 — read-pattern diversity. Present from format_version >= 2. */
export interface ObservatorySignal3 {
  distinctPerturbedAxesCount: bigint;
}

/** Signal #4 — federation health. Present from format_version >= 2. */
export interface ObservatorySignal4 {
  /** Cumulative fork detection count (placeholder pre-M25; 0n). */
  signal4aCumulativeForkCount: bigint;
  /** Currently-established peer count. */
  signal4bReachablePeerCount: bigint;
  /** Cumulative count of `federation_received:*` envelopes ingested. */
  eventsReceivedFromPeers: bigint;
}

/** Signal #5 — time trends (format_version >= 3). */
export interface ObservatorySignal5 {
  /** Raw substrate-private structure; surface untouched for forward-compat. */
  raw: Map<string, Value>;
}

/** Signal #6 — read-window-relative position. Present iff caller supplied
 *  operator_attested_context_window_bytes. */
export interface ObservatorySignal6 {
  substrateTotalBytes: bigint;
  operatorAttestedContextWindowBytes: bigint;
  /** substrate_total / context_window. Parsed from repr string; +Infinity when
   *  window=0 (substrate emits "inf"). */
  ratio: number;
}

/** **Signal #7 — compute per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Wall-clock nanoseconds elapsed in the most recent metabolic cycle. */
export interface ObservatorySignal7 {
  /** Most recent cycle's compute_ns. 0n if no cycle has advanced yet. */
  currentCycleNs: bigint;
  /** Rolling arithmetic mean of compute_ns across the observatory history. */
  rollingMeanNs: number;
}

/** **Signal #8 — network per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Federation egress wire bytes (4-byte length prefix + body) in the most
 *  recent metabolic cycle. */
export interface ObservatorySignal8 {
  /** Most recent cycle's egress bytes. */
  currentCycleBytes: bigint;
  /** Rolling arithmetic mean of network bytes across the history window. */
  rollingMeanBytes: number;
}

/** **Signal #9 — storage per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Byte delta of `dag.cb` + `snapshot.cb` on disk in the most recent cycle. */
export interface ObservatorySignal9 {
  /** Most recent cycle's storage byte delta. */
  currentCycleBytes: bigint;
  /** Rolling arithmetic mean of storage delta across the history window. */
  rollingMeanBytes: number;
}

/** **Signal #10 — composite health score (M26.2)**. Renamed from
 *  `ObservatorySignal7` in earlier schemas. Composite blends signals
 *  1, 2, 4b, 7, 8, 9; production signals contribute positively, cost
 *  signals contribute negatively. Higher = healthier. */
export interface ObservatorySignal10 {
  compositeHealthScore: number;
  compositeFormatVersion: bigint;
  /** Per-signal weights (format_version >= 4 includes signals 7/8/9). */
  weights?: Map<string, number>;
  /** Method tag for the weight derivation (e.g. "emergent_variance"). */
  weightsMethod?: string;
}

/** Doctrine-instability burst status. NOT one of the 10 Living Bet signals
 *  — this is a C37 detector output. Pre-M26.2 schemas emitted this under the
 *  `signal_8_doctrine_revision_burst` key (a naming collision with the actual
 *  signal #8 introduced in M26.2). format_version >= 4 emits under
 *  `doctrine_revision_burst_status`. */
export interface ObservatoryDoctrineRevisionBurstStatus {
  /** Raw substrate-private structure; surface untouched for forward-compat. */
  raw: Map<string, Value>;
}

/** bet_weakening_quorum — composite L0 §7 falsifiability counter
 *  (format_version >= 3). */
export interface ObservatoryBetWeakeningQuorum {
  raw: Map<string, Value>;
}

/** Parsed `query_substrate_observatory_response`. Supports format_versions
 *  1 through 4. **M26.2 (v4)** added signals 7/8/9 (cost), renamed the
 *  composite to signal_10, and decoupled doctrine_revision_burst_status
 *  from numbered Living Bet signals. Pre-v4 producers that still emit the
 *  old `signal_7_composite_health` key are parsed into `signal10` for
 *  forward compatibility. */
export interface ObservatorySnapshot {
  formatVersion: bigint;
  capturedAtUnixNs: bigint;
  signal1?: ObservatorySignal1;
  signal2?: ObservatorySignal2;
  signal3?: ObservatorySignal3;
  signal4?: ObservatorySignal4;
  signal5?: ObservatorySignal5;
  signal6?: ObservatorySignal6;
  /** Signal #7 cost (M26.2+); pre-M26.2 producers emit no signal_7
   *  `compute_per_cycle` key — this stays undefined. */
  signal7?: ObservatorySignal7;
  /** Signal #8 cost (M26.2+). */
  signal8?: ObservatorySignal8;
  /** Signal #9 cost (M26.2+). */
  signal9?: ObservatorySignal9;
  /** Composite #10 (M26.2+). Backward-compat: pre-v4 producers' old
   *  `signal_7_composite_health` key is also surfaced here. */
  signal10?: ObservatorySignal10;
  /** C37 detector status. Pre-v4 key `signal_8_doctrine_revision_burst`
   *  is also accepted (backward compat). */
  doctrineRevisionBurstStatus?: ObservatoryDoctrineRevisionBurstStatus;
  betWeakeningQuorum?: ObservatoryBetWeakeningQuorum;
}

export function parseQuerySubstrateObservatoryResponse(
  response: Message,
): ObservatorySnapshot {
  if (response.messageType !== MSG_TYPE.QUERY_SUBSTRATE_OBSERVATORY_RESPONSE) {
    throw new BridgeProtocolError(
      `expected query_substrate_observatory_response; got ${response.messageType}`,
    );
  }
  const verV = response.payload.get("observatory_format_version");
  const capturedV = response.payload.get("captured_at_unix_ns");
  if (
    !verV || verV.type !== "uint" ||
    !capturedV || capturedV.type !== "timestamp"
  ) {
    throw new BridgeProtocolError(
      "query_substrate_observatory_response missing observatory_format_version or captured_at_unix_ns",
    );
  }
  const snap: ObservatorySnapshot = {
    formatVersion: verV.value,
    capturedAtUnixNs: capturedV.value,
  };

  // Signal #1 (persistence budget) — always emitted from v1.
  const s1 = response.payload.get("signal_1_persistence_budget");
  if (s1 && s1.type === "map") {
    const m = s1.value;
    const nc = m.get("dag_node_count");
    const ec = m.get("dag_edge_count");
    const cb = m.get("dag_total_content_bytes");
    const cc = m.get("manifest_cycle_counter");
    if (
      nc && nc.type === "uint" &&
      ec && ec.type === "uint" &&
      cb && cb.type === "uint" &&
      cc && cc.type === "uint"
    ) {
      snap.signal1 = {
        dagNodeCount: nc.value,
        dagEdgeCount: ec.value,
        dagTotalContentBytes: cb.value,
        manifestCycleCounter: cc.value,
      };
    }
  }

  // Signal #2 (evolution rate) — format_version >= 2.
  const s2 = response.payload.get("signal_2_evolution_rate");
  if (s2 && s2.type === "map") {
    const m = s2.value;
    const ec = m.get("evolution_event_count");
    const ar = m.get("axis_register_count");
    const rr = m.get("rate_repr");
    if (
      ec && ec.type === "uint" &&
      ar && ar.type === "uint" &&
      rr && rr.type === "string"
    ) {
      snap.signal2 = {
        evolutionEventCount: ec.value,
        axisRegisterCount: ar.value,
        rate: parseFloat(rr.value),
      };
    }
  }

  // Signal #3 (read-pattern diversity).
  const s3 = response.payload.get("signal_3_read_pattern_diversity");
  if (s3 && s3.type === "map") {
    const m = s3.value;
    const dc = m.get("distinct_perturbed_axes_count");
    if (dc && dc.type === "uint") {
      snap.signal3 = { distinctPerturbedAxesCount: dc.value };
    }
  }

  // Signal #4 (federation health).
  const s4 = response.payload.get("signal_4_federation_health");
  if (s4 && s4.type === "map") {
    const m = s4.value;
    const fa = m.get("signal_4a_cumulative_fork_count");
    const fb = m.get("signal_4b_reachable_peer_count");
    const er = m.get("events_received_from_peers");
    if (
      fa && fa.type === "uint" &&
      fb && fb.type === "uint" &&
      er && er.type === "uint"
    ) {
      snap.signal4 = {
        signal4aCumulativeForkCount: fa.value,
        signal4bReachablePeerCount: fb.value,
        eventsReceivedFromPeers: er.value,
      };
    }
  }

  // Signal #5 (time trends) — substrate-private structure; preserved raw.
  const s5 = response.payload.get("signal_5_time_trends");
  if (s5 && s5.type === "map") {
    snap.signal5 = { raw: s5.value };
  }

  // Signal #6 (read-window-relative position) — present iff operator
  // supplied operator_attested_context_window_bytes in the request.
  const s6 = response.payload.get("signal_6_read_window_position");
  if (s6 && s6.type === "map") {
    const m = s6.value;
    const tb = m.get("substrate_total_bytes");
    const cw = m.get("operator_attested_context_window_bytes");
    const rr = m.get("ratio_repr");
    if (
      tb && tb.type === "uint" &&
      cw && cw.type === "uint" &&
      rr && rr.type === "string"
    ) {
      // Substrate emits "inf" when window=0; parseFloat returns NaN.
      const ratio = rr.value === "inf" ? Infinity :
        rr.value === "-inf" ? -Infinity :
          rr.value === "nan" ? NaN : parseFloat(rr.value);
      snap.signal6 = {
        substrateTotalBytes: tb.value,
        operatorAttestedContextWindowBytes: cw.value,
        ratio,
      };
    }
  }

  // -----------------------------------------------------------------------
  // **M26.2 P11.b** signals #7/#8/#9 (cost per cycle). format_version >= 4.
  // Each cost signal carries {current_cycle_*, rolling_mean_*_repr}.
  // -----------------------------------------------------------------------
  const s7Cost = response.payload.get("signal_7_compute_per_cycle");
  if (s7Cost && s7Cost.type === "map") {
    const m = s7Cost.value;
    const cur = m.get("current_cycle_ns");
    const meanRepr = m.get("rolling_mean_ns_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal7 = {
        currentCycleNs: cur.value,
        rollingMeanNs: parseFloat(meanRepr.value),
      };
    }
  }

  const s8Cost = response.payload.get("signal_8_network_per_cycle");
  if (s8Cost && s8Cost.type === "map") {
    const m = s8Cost.value;
    const cur = m.get("current_cycle_bytes");
    const meanRepr = m.get("rolling_mean_bytes_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal8 = {
        currentCycleBytes: cur.value,
        rollingMeanBytes: parseFloat(meanRepr.value),
      };
    }
  }

  const s9Cost = response.payload.get("signal_9_storage_per_cycle");
  if (s9Cost && s9Cost.type === "map") {
    const m = s9Cost.value;
    const cur = m.get("current_cycle_bytes");
    const meanRepr = m.get("rolling_mean_bytes_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal9 = {
        currentCycleBytes: cur.value,
        rollingMeanBytes: parseFloat(meanRepr.value),
      };
    }
  }

  // -----------------------------------------------------------------------
  // Signal #10 — composite health. M26.2 RENAMED from `signal_7_composite_health`.
  // Backward compat: pre-v4 producers still emit under the old key, so we
  // accept either and surface as `snap.signal10`.
  // -----------------------------------------------------------------------
  const s10 =
    response.payload.get("signal_10_composite_health") ??
    response.payload.get("signal_7_composite_health");
  if (s10 && s10.type === "map") {
    const m = s10.value;
    const sr = m.get("composite_health_score_repr");
    const fv = m.get("composite_format_version");
    if (
      sr && sr.type === "string" &&
      fv && fv.type === "uint"
    ) {
      const sig10: ObservatorySignal10 = {
        compositeHealthScore: parseFloat(sr.value),
        compositeFormatVersion: fv.value,
      };
      const wMap = m.get("weights");
      if (wMap && wMap.type === "map") {
        const weights = new Map<string, number>();
        for (const [k, v] of wMap.value) {
          if (v.type === "string") weights.set(k, parseFloat(v.value));
        }
        if (weights.size > 0) sig10.weights = weights;
      }
      const wm = m.get("weights_method");
      if (wm && wm.type === "string") sig10.weightsMethod = wm.value;
      snap.signal10 = sig10;
    }
  }

  // -----------------------------------------------------------------------
  // Doctrine-revision burst status. M26.2 RENAMED key from
  // `signal_8_doctrine_revision_burst` to `doctrine_revision_burst_status`
  // (the old key collided with M26.2 actual signal #8). Backward-compat:
  // also accept the old key for pre-v4 producers.
  // -----------------------------------------------------------------------
  const burst =
    response.payload.get("doctrine_revision_burst_status") ??
    response.payload.get("signal_8_doctrine_revision_burst");
  if (burst && burst.type === "map") {
    snap.doctrineRevisionBurstStatus = { raw: burst.value };
  }

  // bet_weakening_quorum (M25.2) — composite L0 §7 falsifiability counter.
  const bq = response.payload.get("bet_weakening_quorum");
  if (bq && bq.type === "map") {
    snap.betWeakeningQuorum = { raw: bq.value };
  }

  return snap;
}

// ---------------------------------------------------------------------------
// M17 P3 永恒进化: schema_diff builders. Mirror Python's
// `kernel/governance::schema_evolution.schema_diff_*_bytes` byte-for-byte.
// ---------------------------------------------------------------------------

/** Build canonical-bytes for a modify_axis_threshold schema_diff (M17).
 *
 *  This is the content_canonical_bytes for a submit_mutation with
 *  mutation_type="schema_evolution". Operator signs THIS as the attestation.
 */
export function schemaDiffModifyAxisThresholdBytes(
  axisName: string,
  newThreshold: number,
): Uint8Array {
  const m = new Map<string, Value>();
  m.set("op", { type: "string", value: "modify_axis_threshold" });
  m.set("axis_name", { type: "string", value: axisName });
  m.set("new_threshold_repr", { type: "string", value: floatRepr(newThreshold) });
  return encode({ type: "map", value: m }).bytes;
}

/** Build canonical-bytes for an add_axis_to_gradient schema_diff (M17). */
export function schemaDiffAddAxisBytes(args: {
  axisName: string;
  axisClass: "appetite" | "decay";
  fruitingThreshold: number;
  initialValue: number;
  decayRatePerCycle: number;
  isMortalitySignal: boolean;
  updateRuleKind: "noop" | "decay";
}): Uint8Array {
  const m = new Map<string, Value>();
  m.set("op", { type: "string", value: "add_axis_to_gradient" });
  m.set("axis_name", { type: "string", value: args.axisName });
  m.set("axis_class", { type: "string", value: args.axisClass });
  m.set("fruiting_threshold_repr", {
    type: "string",
    value: floatRepr(args.fruitingThreshold),
  });
  m.set("initial_value_repr", {
    type: "string",
    value: floatRepr(args.initialValue),
  });
  m.set("decay_rate_per_cycle_repr", {
    type: "string",
    value: floatRepr(args.decayRatePerCycle),
  });
  m.set("is_mortality_signal", {
    type: "bool",
    value: args.isMortalitySignal,
  });
  m.set("update_rule_kind", { type: "string", value: args.updateRuleKind });
  return encode({ type: "map", value: m }).bytes;
}

// ---------------------------------------------------------------------------
// M16 P2 永恒吞噬: ingest_raw_material + perturb_axis_from_raw_material
// ---------------------------------------------------------------------------

/** Allowed content kinds for `ingest_raw_material`. The substrate accepts
 *  arbitrary strings (L0 P2 "no filter on intake"), but these are the
 *  canonical kinds operators should use when possible. */
export type RawMaterialKind =
  | "text"
  | "file"
  | "conversation"
  | "url"
  | "llm_response"
  | (string & Record<never, never>); // allow custom

/** Build the payload for an `ingest_raw_material` request (M16).
 *
 *  Activates L0 P2 永恒吞噬 — universal intake. The substrate stores the
 *  payload as a `raw_material:{kind}` DAG node. Max 1 MiB per ingestion.
 */
export function ingestRawMaterialPayload(args: {
  contentKind: RawMaterialKind;
  contentBytes: Uint8Array;
  sourceUri?: string;
  meta?: Map<string, Value>;
}): Map<string, Value> {
  if (!args.contentKind || args.contentKind.length === 0) {
    throw new BridgeProtocolError(
      "ingest_raw_material: content_kind must be a non-empty string",
    );
  }
  const m = new Map<string, Value>();
  m.set("content_kind", { type: "string", value: args.contentKind });
  m.set("content_bytes", { type: "bytes", value: args.contentBytes });
  if (args.sourceUri !== undefined) {
    m.set("source_uri", { type: "string", value: args.sourceUri });
  }
  if (args.meta !== undefined) {
    m.set("meta", { type: "map", value: args.meta });
  }
  return m;
}

/** Parsed `ingest_raw_material_response` (M16). */
export interface IngestResult {
  /** DAG node hash of the newly-inserted raw_material node. */
  dagNodeHash: Uint8Array;
  /** Substrate's current DAG tip (after ingestion). */
  currentTip: Uint8Array | null;
  totalDagSize: bigint;
}

export function parseIngestRawMaterialResponse(response: Message): IngestResult {
  if (response.messageType !== MSG_TYPE.INGEST_RAW_MATERIAL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected ingest_raw_material_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("dag_node_hash");
  const totalV = response.payload.get("total_dag_size");
  if (!hashV || hashV.type !== "bytes" || !totalV || totalV.type !== "uint") {
    throw new BridgeProtocolError(
      "ingest_raw_material_response missing required typed fields",
    );
  }
  const tipV = response.payload.get("current_tip");
  return {
    dagNodeHash: hashV.value,
    currentTip: tipV && tipV.type === "bytes" ? tipV.value : null,
    totalDagSize: totalV.value,
  };
}

/** Build the payload for a `perturb_axis_from_raw_material` request (M16).
 *
 *  Activates L0 P6 永恒因果 + P2 永恒吞噬 — the gradient change is causally
 *  linked to a specific raw_material DAG node. The substrate inserts a
 *  `perturb_from_raw:{axis}` DAG node with parents [prior_tip, raw_material_hash].
 */
export function perturbAxisFromRawMaterialPayload(args: {
  axisName: string;
  delta: number;
  rawMaterialHash: Uint8Array;
}): Map<string, Value> {
  if (args.rawMaterialHash.length !== 32) {
    throw new BridgeProtocolError(
      `raw_material_hash must be 32 bytes; got ${args.rawMaterialHash.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("axis_name", { type: "string", value: args.axisName });
  m.set("delta_repr", { type: "string", value: floatRepr(args.delta) });
  m.set("raw_material_hash", { type: "bytes", value: args.rawMaterialHash });
  return m;
}

/** Parsed `perturb_axis_from_raw_material_response` (M16). */
export interface PerturbFromRawResult {
  /** DAG node hash of the causal-link node (parents: [prior_tip, raw_material_hash]). */
  causalLinkHash: Uint8Array;
  /** Echo of the raw_material_hash referenced. */
  rawMaterialHash: Uint8Array;
}

export function parsePerturbAxisFromRawMaterialResponse(
  response: Message,
): PerturbFromRawResult {
  if (response.messageType !== MSG_TYPE.PERTURB_AXIS_FROM_RAW_MATERIAL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected perturb_axis_from_raw_material_response; got ${response.messageType}`,
    );
  }
  const linkV = response.payload.get("causal_link_hash");
  const rawV = response.payload.get("raw_material_hash");
  if (
    !linkV || linkV.type !== "bytes" ||
    !rawV || rawV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "perturb_axis_from_raw_material_response missing required typed fields",
    );
  }
  return {
    causalLinkHash: linkV.value,
    rawMaterialHash: rawV.value,
  };
}

/** Build the payload for a `compute_intent` request (M8).
 *
 *  Operator-side typically omits pivot_hash (lets substrate default to DAG tip)
 *  and omits dag_nodes (substrate auto-fills with its own DAG).
 *  The operator can override these for diagnostic queries.
 */
export function computeIntentPayload(args: {
  radiusCycles: bigint;
  pivotHash?: Uint8Array;
}): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("radius_cycles", { type: "uint", value: args.radiusCycles });
  if (args.pivotHash) {
    m.set("pivot_hash", { type: "bytes", value: args.pivotHash });
  }
  return m;
}

/** Build the payload for a `request_attestation_nonce` request (M13;
 *  extended M15 with optional anchor-clock binding).
 *
 *  Bound to the SHA-256 hash of the mutation's content_canonical_bytes.
 *  Substrate issues a 32-byte nonce + returns expiry + bound dag_tip.
 *
 *  M15: optionally supply `anchorClockUnixNs` — the operator's view of "now"
 *  on the operator's wall clock. When present, the substrate records BOTH
 *  the substrate-clock issuance time AND the anchor-clock issuance time;
 *  the response echoes an `anchor_clock_expiry_unix_ns` so the operator can
 *  later supply `anchor_clock_submitted_at_unix_ns` at submit time. The
 *  dual-clock check at verification rejects clock-skew attacks that try to
 *  extend nonce lifetime by manipulating one clock.
 */
export function requestAttestationNoncePayload(
  contentHash: Uint8Array,
  anchorClockUnixNs?: bigint,
): Map<string, Value> {
  if (contentHash.length !== 32) {
    throw new BridgeProtocolError(
      `content_hash must be exactly 32 bytes; got ${contentHash.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("content_hash", { type: "bytes", value: contentHash });
  if (anchorClockUnixNs !== undefined) {
    m.set("anchor_clock_unix_ns", { type: "timestamp", value: anchorClockUnixNs });
  }
  return m;
}

/** Parsed `request_attestation_nonce_response` (M13; extended M15). */
export interface AttestationNonceResult {
  nonce: Uint8Array;
  boundDagTip: Uint8Array;
  expiryUnixNs: bigint;
  ttlSeconds: bigint;
  /** Anchor-clock expiry echo (M15). Present iff caller supplied
   *  `anchorClockUnixNs` in the request. Operator passes this back as
   *  reference at submit time for the dual-clock check. */
  anchorClockExpiryUnixNs: bigint | null;
}

export function parseRequestAttestationNonceResponse(
  response: Message,
): AttestationNonceResult {
  if (response.messageType !== MSG_TYPE.REQUEST_ATTESTATION_NONCE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected request_attestation_nonce_response; got ${response.messageType}`,
    );
  }
  const nonceV = response.payload.get("nonce");
  const tipV = response.payload.get("bound_dag_tip");
  const expiryV = response.payload.get("expiry_unix_ns");
  const ttlV = response.payload.get("ttl_seconds");
  if (
    !nonceV || nonceV.type !== "bytes" ||
    !tipV || tipV.type !== "bytes" ||
    !expiryV || expiryV.type !== "timestamp" ||
    !ttlV || ttlV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "request_attestation_nonce_response missing required typed fields",
    );
  }
  const anchorExpiryV = response.payload.get("anchor_clock_expiry_unix_ns");
  const anchorClockExpiryUnixNs =
    anchorExpiryV && anchorExpiryV.type === "timestamp" ? anchorExpiryV.value : null;
  return {
    nonce: nonceV.value,
    boundDagTip: tipV.value,
    expiryUnixNs: expiryV.value,
    ttlSeconds: ttlV.value,
    anchorClockExpiryUnixNs,
  };
}

/** Compute the canonical-bytes signing input for an identity-over-REVEAL
 *  signature (M14; M24.2 v2 binding adds substrate_id).
 *  Mirrors Rust's reconstruction in verify_reveal_keypair_envelope.
 *
 *  Signing input (M24.2 v2) = canonical_bytes(Map({
 *    "context": "myco-reveal-key-binding-v2",
 *    "reveal_pubkey": Bytes(reveal_pubkey),
 *    "substrate_id": Bytes(substrate_id),
 *  }))
 *
 *  M24.2 SECURITY: substrate_id is now required so a signature for
 *  substrate A cannot be replayed against substrate B with the same pinned
 *  operator. (Phase β audit Surface 5.3.)
 *
 *  The IDENTITY key signs this to prove that the operator authorized this
 *  REVEAL keypair FOR THIS SUBSTRATE. M14+ activates C17 operator_witness_forgery
 *  on failure.
 */
export function revealKeyBindingSigningInput(
  revealPubkey: Uint8Array,
  substrateId: Uint8Array,
): Uint8Array {
  if (revealPubkey.length !== 32) {
    throw new BridgeProtocolError(
      `revealPubkey must be exactly 32 bytes; got ${revealPubkey.length}`,
    );
  }
  if (substrateId.length !== 32) {
    throw new BridgeProtocolError(
      `substrateId must be exactly 32 bytes; got ${substrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: "myco-reveal-key-binding-v2" });
  m.set("reveal_pubkey", { type: "bytes", value: revealPubkey });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for a `submit_mutation` request (M10; extended M13; M14).
 *
 *  CI mutations require `attestationSignature` — a 64-byte Ed25519 signature
 *  over `contentCanonicalBytes`. Daily mutations omit it.
 *
 *  M13: optional `nonce` + `expiryUnixNs` for anchor-surface envelope.
 *
 *  M14: optional `revealPubkey` + `identitySignatureOverRevealPubkey` for
 *  per-handshake REVEAL keypair. When REVEAL is present, the attestation
 *  signature is interpreted as REVEAL-signed-over-content (not IDENTITY-signed).
 *  The substrate verifies BOTH layers: IDENTITY-over-REVEAL (closes C17) and
 *  REVEAL-over-content (closes C5 attestation path).
 */
export function submitMutationPayload(args: {
  mutationType: string;
  touchedFields?: string[];
  touchedFiles?: string[];
  touchedMetaStructures?: string[];
  contentCanonicalBytes: Uint8Array;
  attestationSignature?: Uint8Array;
  nonce?: Uint8Array;
  expiryUnixNs?: bigint;
  revealPubkey?: Uint8Array;
  identitySignatureOverRevealPubkey?: Uint8Array;
  /** M15: operator's anchor-clock "now" at submit time (unix nanoseconds).
   *  Required iff the nonce was issued WITH `anchorClockUnixNs` (dual-clock
   *  mode). Substrate verifies `anchor_issued ≤ this ≤ anchor_expiry`. */
  anchorClockSubmittedAtUnixNs?: bigint;
}): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("mutation_type", { type: "string", value: args.mutationType });
  m.set("touched_fields", {
    type: "array",
    value: (args.touchedFields ?? []).map(
      (s) => ({ type: "string", value: s }) as Value,
    ),
  });
  m.set("touched_files", {
    type: "array",
    value: (args.touchedFiles ?? []).map(
      (s) => ({ type: "string", value: s }) as Value,
    ),
  });
  m.set("touched_meta_structures", {
    type: "array",
    value: (args.touchedMetaStructures ?? []).map(
      (s) => ({ type: "string", value: s }) as Value,
    ),
  });
  m.set("content_canonical_bytes", {
    type: "bytes",
    value: args.contentCanonicalBytes,
  });
  if (args.attestationSignature) {
    if (args.attestationSignature.length !== 64) {
      throw new BridgeProtocolError(
        `attestation_signature must be 64 bytes; got ${args.attestationSignature.length}`,
      );
    }
    m.set("attestation_signature", {
      type: "bytes",
      value: args.attestationSignature,
    });
  }
  if (args.nonce) {
    if (args.nonce.length !== 32) {
      throw new BridgeProtocolError(
        `nonce must be 32 bytes; got ${args.nonce.length}`,
      );
    }
    m.set("nonce", { type: "bytes", value: args.nonce });
  }
  if (args.expiryUnixNs !== undefined) {
    m.set("expiry_unix_ns", { type: "timestamp", value: args.expiryUnixNs });
  }
  if (args.revealPubkey) {
    if (args.revealPubkey.length !== 32) {
      throw new BridgeProtocolError(
        `revealPubkey must be 32 bytes; got ${args.revealPubkey.length}`,
      );
    }
    m.set("reveal_pubkey", { type: "bytes", value: args.revealPubkey });
  }
  if (args.identitySignatureOverRevealPubkey) {
    if (args.identitySignatureOverRevealPubkey.length !== 64) {
      throw new BridgeProtocolError(
        `identitySignatureOverRevealPubkey must be 64 bytes; got ${args.identitySignatureOverRevealPubkey.length}`,
      );
    }
    m.set("identity_signature_over_reveal_pubkey", {
      type: "bytes",
      value: args.identitySignatureOverRevealPubkey,
    });
  }
  if (args.anchorClockSubmittedAtUnixNs !== undefined) {
    m.set("anchor_clock_submitted_at_unix_ns", {
      type: "timestamp",
      value: args.anchorClockSubmittedAtUnixNs,
    });
  }
  return m;
}

// ---------------------------------------------------------------------------
// M15: enumerate_dag_since (DAG enumeration closure).
// ---------------------------------------------------------------------------

/** Build the payload for an `enumerate_dag_since` request (M15).
 *
 *  When `prevTip` is undefined, the substrate enumerates from genesis.
 *  When supplied, the substrate enumerates nodes inserted AFTER prevTip.
 *  On unknown prevTip, the substrate emits C6 dag_enumeration_unclosed
 *  and returns an error envelope.
 */
export function enumerateDagSincePayload(prevTip?: Uint8Array): Map<string, Value> {
  const m = new Map<string, Value>();
  if (prevTip) {
    if (prevTip.length !== 32) {
      throw new BridgeProtocolError(
        `prev_tip must be exactly 32 bytes; got ${prevTip.length}`,
      );
    }
    m.set("prev_tip", { type: "bytes", value: prevTip });
  }
  return m;
}

/** One DAG node from an enumeration response (M15). Carries all metadata
 *  needed for owner-side Merkle chain reconstruction. */
export interface EnumeratedDagNode {
  /** Substrate-claimed Merkle hash. Owner recomputes from parent_hashes +
   *  content_canonical_bytes via `merkleHash` and compares. */
  hash: Uint8Array;
  parentHashes: Uint8Array[];
  nodeType: string;
  atCycle: bigint;
  contentCanonicalBytes: Uint8Array;
}

/** Parsed `enumerate_dag_since_response` (M15). */
export interface DagEnumerationReport {
  /** Current DAG tip at substrate (null if DAG is empty). */
  currentTip: Uint8Array | null;
  /** Echo of the prev_tip the caller passed (null if absent). */
  prevTip: Uint8Array | null;
  totalDagSize: bigint;
  enumeratedCount: bigint;
  nodes: EnumeratedDagNode[];
}

export function parseEnumerateDagSinceResponse(response: Message): DagEnumerationReport {
  if (response.messageType !== MSG_TYPE.ENUMERATE_DAG_SINCE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected enumerate_dag_since_response; got ${response.messageType}`,
    );
  }
  const totalV = response.payload.get("total_dag_size");
  const enumCountV = response.payload.get("enumerated_count");
  const nodesV = response.payload.get("nodes");
  if (
    !totalV || totalV.type !== "uint" ||
    !enumCountV || enumCountV.type !== "uint" ||
    !nodesV || nodesV.type !== "array"
  ) {
    throw new BridgeProtocolError(
      "enumerate_dag_since_response missing required typed fields",
    );
  }
  const currentTipV = response.payload.get("current_tip");
  const currentTip =
    currentTipV && currentTipV.type === "bytes" ? currentTipV.value : null;
  const prevTipV = response.payload.get("prev_tip");
  const prevTip = prevTipV && prevTipV.type === "bytes" ? prevTipV.value : null;

  const nodes: EnumeratedDagNode[] = nodesV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(
        `enumerated node is not a Map: ${v.type}`,
      );
    }
    const m = v.value;
    const hashV = m.get("hash");
    const parentsV = m.get("parent_hashes");
    const typeV = m.get("node_type");
    const cycleV = m.get("at_cycle");
    const contentV = m.get("content_canonical_bytes");
    if (
      !hashV || hashV.type !== "bytes" ||
      !parentsV || parentsV.type !== "array" ||
      !typeV || typeV.type !== "string" ||
      !cycleV || cycleV.type !== "uint" ||
      !contentV || contentV.type !== "bytes"
    ) {
      throw new BridgeProtocolError(
        "enumerated node Map missing required typed fields",
      );
    }
    const parentHashes: Uint8Array[] = parentsV.value.map((p) => {
      if (p.type !== "bytes") {
        throw new BridgeProtocolError(
          `parent_hashes contains non-Bytes: ${p.type}`,
        );
      }
      return p.value;
    });
    return {
      hash: hashV.value,
      parentHashes,
      nodeType: typeV.value,
      atCycle: cycleV.value,
      contentCanonicalBytes: contentV.value,
    };
  });
  return {
    currentTip,
    prevTip,
    totalDagSize: totalV.value,
    enumeratedCount: enumCountV.value,
    nodes,
  };
}

/**
 * Format a number as a Python-compatible repr string.
 *
 * Identical convention to the Rust + Python `float_repr` helpers. This is
 * how M5/M6 round-trips floats across language boundaries deterministically.
 *
 * - NaN → "nan"
 * - +Inf → "inf"
 * - -Inf → "-inf"
 * - Integer-valued and within ±1e16 → "N.0" (e.g., "0.0", "1.0", "-2.0")
 * - Otherwise → default `String(n)` (which matches Python's `repr` for most cases)
 */
export function floatRepr(n: number): string {
  if (Number.isNaN(n)) return "nan";
  if (!Number.isFinite(n)) return n > 0 ? "inf" : "-inf";
  if (Math.abs(n) < 1e16 && Math.trunc(n) === n) {
    // Integer-valued: emit "N.0" — matches Rust's `format!("{f:.1}")` and Python's repr.
    return `${n.toFixed(1)}`;
  }
  return String(n);
}

// ---------------------------------------------------------------------------
// Response parsers.
// ---------------------------------------------------------------------------

/** Parsed sporocarp from an `advance_response`. */
export interface SporocarpReport {
  sporocarpType: string;
  axisName: string;
  fruitingValue: number;
  atCycle: bigint;
  canonicalBytes: Uint8Array;
  hash: Uint8Array;
}

/** Parsed `advance_response` payload (extended M18). */
export interface AdvanceReport {
  /** Echo of the substrate's authoritative cycle counter (when from myco-substrate). */
  cycleNumber: bigint | null;
  fruitedAxes: string[];
  sporocarps: SporocarpReport[];
  // M18 P4 永恒迭代 cycle-pipeline outputs:
  /** Count of raw_material:* nodes absorbed during this cycle. */
  deltasAbsorbed: bigint;
  /** Count of handshake events processed during this cycle. */
  handshakeEventsProcessed: bigint;
  /** Node types of immune:* events observed during this cycle's skin-breach check. */
  skinBreaches: string[];
  /** DAG node hash of the absorption_event:cycle_{N} node, if any was emitted. */
  absorptionEventHash: Uint8Array | null;
  // M19 P7 必朽 endogenous mortality:
  /** DAG node hashes of any self_euthanasia_proposal:{axis_name} nodes
   *  emitted this cycle (one per mortality_signal fruiting). */
  selfEuthanasiaProposalHashes: Uint8Array[];
}

/** Parse an `advance_response` message into an AdvanceReport. */
export function parseAdvanceResponse(response: Message): AdvanceReport {
  if (response.messageType !== MSG_TYPE.ADVANCE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected advance_response; got ${response.messageType}`,
    );
  }
  const cycleNumberV = response.payload.get("cycle_number");
  const cycleNumber =
    cycleNumberV && cycleNumberV.type === "uint" ? cycleNumberV.value : null;

  const fruitedV = response.payload.get("fruited_axes");
  if (!fruitedV || fruitedV.type !== "array") {
    throw new BridgeProtocolError("advance_response missing fruited_axes");
  }
  const fruitedAxes: string[] = fruitedV.value.map((v) => {
    if (v.type !== "string") {
      throw new BridgeProtocolError(
        `fruited_axes contains non-String: ${v.type}`,
      );
    }
    return v.value;
  });

  const sporocarpsV = response.payload.get("sporocarps");
  if (!sporocarpsV || sporocarpsV.type !== "array") {
    throw new BridgeProtocolError("advance_response missing sporocarps");
  }
  const sporocarps: SporocarpReport[] = sporocarpsV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(
        `sporocarps contains non-Map: ${v.type}`,
      );
    }
    const sp = v.value;
    const typeV = sp.get("sporocarp_type");
    const axisV = sp.get("axis_name");
    const fvReprV = sp.get("fruiting_value_repr");
    const cycleV = sp.get("at_cycle");
    const cbV = sp.get("canonical_bytes");
    const hashV = sp.get("hash");
    if (
      !typeV || typeV.type !== "string" ||
      !axisV || axisV.type !== "string" ||
      !fvReprV || fvReprV.type !== "string" ||
      !cycleV || cycleV.type !== "uint" ||
      !cbV || cbV.type !== "bytes" ||
      !hashV || hashV.type !== "bytes"
    ) {
      throw new BridgeProtocolError(
        "sporocarp Map missing required typed fields",
      );
    }
    return {
      sporocarpType: typeV.value,
      axisName: axisV.value,
      fruitingValue: parseFloat(fvReprV.value),
      atCycle: cycleV.value,
      canonicalBytes: cbV.value,
      hash: hashV.value,
    };
  });

  // M18 P4 永恒迭代 fields (back-compat optional).
  const deltasV = response.payload.get("deltas_absorbed");
  const handshakeV = response.payload.get("handshake_events_processed");
  const breachesV = response.payload.get("skin_breaches");
  const absorbHashV = response.payload.get("absorption_event_hash");
  const deltasAbsorbed = deltasV && deltasV.type === "uint" ? deltasV.value : 0n;
  const handshakeEventsProcessed =
    handshakeV && handshakeV.type === "uint" ? handshakeV.value : 0n;
  const skinBreaches: string[] =
    breachesV && breachesV.type === "array"
      ? breachesV.value
          .map((v) => (v.type === "string" ? v.value : ""))
          .filter((s) => s.length > 0)
      : [];
  const absorptionEventHash =
    absorbHashV && absorbHashV.type === "bytes" ? absorbHashV.value : null;
  // M19 P7 必朽 — self_euthanasia_proposal_hashes (back-compat optional).
  const propsV = response.payload.get("self_euthanasia_proposal_hashes");
  const selfEuthanasiaProposalHashes: Uint8Array[] =
    propsV && propsV.type === "array"
      ? propsV.value
          .map((v) => (v.type === "bytes" ? v.value : null))
          .filter((b): b is Uint8Array => b !== null)
      : [];
  return {
    cycleNumber,
    fruitedAxes,
    sporocarps,
    deltasAbsorbed,
    handshakeEventsProcessed,
    skinBreaches,
    absorptionEventHash,
    selfEuthanasiaProposalHashes,
  };
}

/** Parsed `snapshot_response` — axis name → current value. */
export function parseSnapshotResponse(response: Message): Map<string, number> {
  if (response.messageType !== MSG_TYPE.SNAPSHOT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected snapshot_response; got ${response.messageType}`,
    );
  }
  const valuesV = response.payload.get("values");
  if (!valuesV || valuesV.type !== "map") {
    throw new BridgeProtocolError("snapshot_response missing values map");
  }
  const out = new Map<string, number>();
  for (const [k, v] of valuesV.value) {
    if (v.type !== "string") {
      throw new BridgeProtocolError(
        `snapshot value for ${k} is not String: ${v.type}`,
      );
    }
    const n = parseFloat(v.value);
    if (Number.isNaN(n) && v.value !== "nan") {
      throw new BridgeProtocolError(
        `snapshot value for ${k} failed to parse: ${v.value}`,
      );
    }
    out.set(k, n);
  }
  return out;
}

/** Parsed `hello_ack`. */
export interface HelloAck {
  kernelTropismVersion: string;
  pythonVersion: string;
  /** Set when responding from myco-substrate (3-tier). Empty for direct Python. */
  substrateVersion: string;
}

/** One cluster from an `compute_intent_response` (M8). */
export interface IntentCluster {
  clusterId: bigint;
  nodeCount: bigint;
  /** Cluster member DAG node hashes (32-byte each). */
  nodeHashes: Uint8Array[];
}

/** Parsed `compute_intent_response` (M8). */
export interface IntentReport {
  coldStart: boolean;
  neighborhoodNodeCount: bigint;
  fullSetNodeCount: bigint;
  clusterCount: bigint;
  clusters: IntentCluster[];
}

export function parseComputeIntentResponse(response: Message): IntentReport {
  if (response.messageType !== MSG_TYPE.COMPUTE_INTENT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected compute_intent_response; got ${response.messageType}`,
    );
  }
  const coldStartV = response.payload.get("cold_start");
  if (!coldStartV || coldStartV.type !== "bool") {
    throw new BridgeProtocolError("compute_intent_response missing cold_start");
  }
  const neighborhoodV = response.payload.get("neighborhood_node_count");
  const fullSetV = response.payload.get("full_set_node_count");
  const clusterCountV = response.payload.get("cluster_count");
  const clustersV = response.payload.get("clusters");
  if (
    !neighborhoodV || neighborhoodV.type !== "uint" ||
    !fullSetV || fullSetV.type !== "uint" ||
    !clusterCountV || clusterCountV.type !== "uint" ||
    !clustersV || clustersV.type !== "array"
  ) {
    throw new BridgeProtocolError(
      "compute_intent_response missing required typed fields",
    );
  }
  const clusters: IntentCluster[] = clustersV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(`cluster is not a Map: ${v.type}`);
    }
    const m = v.value;
    const idV = m.get("cluster_id");
    const ncV = m.get("node_count");
    const hashesV = m.get("node_hashes");
    if (
      !idV || idV.type !== "uint" ||
      !ncV || ncV.type !== "uint" ||
      !hashesV || hashesV.type !== "array"
    ) {
      throw new BridgeProtocolError("cluster Map missing required fields");
    }
    const nodeHashes: Uint8Array[] = hashesV.value.map((h) => {
      if (h.type !== "bytes") {
        throw new BridgeProtocolError(
          `node_hashes contains non-Bytes: ${h.type}`,
        );
      }
      return h.value;
    });
    return {
      clusterId: idV.value,
      nodeCount: ncV.value,
      nodeHashes,
    };
  });
  return {
    coldStart: coldStartV.value,
    neighborhoodNodeCount: neighborhoodV.value,
    fullSetNodeCount: fullSetV.value,
    clusterCount: clusterCountV.value,
    clusters,
  };
}

/** One immune event from a `query_immune_events_response` (M11). */
export interface ImmuneEvent {
  hash: Uint8Array;
  /** Full node_type, e.g. "immune:C14_untyped_mutation_blocked". */
  nodeType: string;
  atCycle: bigint;
  /** Raw canonical-bytes of the immune event payload (Map with detector_id +
   *  evidence + timestamp). Operators can decode via anchor_client renderer. */
  contentCanonicalBytes: Uint8Array;
}

/** Parsed `query_immune_events_response` (M11). */
export interface ImmuneEventsReport {
  totalImmuneCount: bigint;
  returnedCount: bigint;
  events: ImmuneEvent[];
}

/** Build the payload for a `query_immune_events` request (M11). */
export function queryImmuneEventsPayload(count: bigint): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("count", { type: "uint", value: count });
  return m;
}

/** One C9 integrity check result (M12). */
export interface IntegrityCheck {
  checkId: string;
  passed: boolean;
  evidence: string;
}

/** Parsed `run_immune_check_response` (M12). */
export interface ImmuneCheckReport {
  totalChecks: bigint;
  failedChecks: bigint;
  immuneEventsEmitted: bigint;
  checks: IntegrityCheck[];
}

export function parseRunImmuneCheckResponse(
  response: Message,
): ImmuneCheckReport {
  if (response.messageType !== MSG_TYPE.RUN_IMMUNE_CHECK_RESPONSE) {
    throw new BridgeProtocolError(
      `expected run_immune_check_response; got ${response.messageType}`,
    );
  }
  const totalV = response.payload.get("total_checks");
  const failedV = response.payload.get("failed_checks");
  const emittedV = response.payload.get("immune_events_emitted");
  const checksV = response.payload.get("checks");
  if (
    !totalV || totalV.type !== "uint" ||
    !failedV || failedV.type !== "uint" ||
    !emittedV || emittedV.type !== "uint" ||
    !checksV || checksV.type !== "array"
  ) {
    throw new BridgeProtocolError(
      "run_immune_check_response missing required typed fields",
    );
  }
  const checks: IntegrityCheck[] = checksV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(`check entry not a Map: ${v.type}`);
    }
    const m = v.value;
    const idV = m.get("check_id");
    const passedV = m.get("passed");
    const evidenceV = m.get("evidence");
    if (
      !idV || idV.type !== "string" ||
      !passedV || passedV.type !== "bool" ||
      !evidenceV || evidenceV.type !== "string"
    ) {
      throw new BridgeProtocolError("check entry missing required typed fields");
    }
    return {
      checkId: idV.value,
      passed: passedV.value,
      evidence: evidenceV.value,
    };
  });
  return {
    totalChecks: totalV.value,
    failedChecks: failedV.value,
    immuneEventsEmitted: emittedV.value,
    checks,
  };
}

export function parseQueryImmuneEventsResponse(
  response: Message,
): ImmuneEventsReport {
  if (response.messageType !== MSG_TYPE.QUERY_IMMUNE_EVENTS_RESPONSE) {
    throw new BridgeProtocolError(
      `expected query_immune_events_response; got ${response.messageType}`,
    );
  }
  const totalV = response.payload.get("total_immune_count");
  const returnedV = response.payload.get("returned_count");
  const eventsV = response.payload.get("events");
  if (
    !totalV || totalV.type !== "uint" ||
    !returnedV || returnedV.type !== "uint" ||
    !eventsV || eventsV.type !== "array"
  ) {
    throw new BridgeProtocolError(
      "query_immune_events_response missing required typed fields",
    );
  }
  const events: ImmuneEvent[] = eventsV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(
        `immune_event is not a Map: ${v.type}`,
      );
    }
    const m = v.value;
    const hashV = m.get("hash");
    const typeV = m.get("node_type");
    const cycleV = m.get("at_cycle");
    const contentV = m.get("content_canonical_bytes");
    if (
      !hashV || hashV.type !== "bytes" ||
      !typeV || typeV.type !== "string" ||
      !cycleV || cycleV.type !== "uint" ||
      !contentV || contentV.type !== "bytes"
    ) {
      throw new BridgeProtocolError(
        "immune_event Map missing required typed fields",
      );
    }
    return {
      hash: hashV.value,
      nodeType: typeV.value,
      atCycle: cycleV.value,
      contentCanonicalBytes: contentV.value,
    };
  });
  return {
    totalImmuneCount: totalV.value,
    returnedCount: returnedV.value,
    events,
  };
}

/** Parsed `submit_mutation_response` (M10; extended M17 with evolution fields). */
export interface MutationResult {
  /** "daily" | "contract_identity_level" | "untyped" */
  classification: string;
  accepted: boolean;
  rejectionReason: string;
  mutationType: string;
  /** Set iff accepted: the DAG node hash where this mutation was recorded. */
  dagNodeHash: Uint8Array | null;
  // M17 P3 永恒进化 fields:
  /** True iff this was a schema_evolution mutation that triggered an apply. */
  schemaApplyAttempted: boolean;
  /** True iff schema apply ran successfully (without rollback). */
  schemaApplySucceeded: boolean;
  /** Empty if succeeded; failure reason (e.g., "AxisNotFound: x") otherwise. */
  schemaApplyFailureReason: string;
  /** The schema_diff op that was applied (e.g., "modify_axis_threshold"). */
  schemaApplyOp: string;
  /** Compact human-readable summary of the applied diff. */
  schemaApplySummary: string;
  /** DAG node hash of the evolution_succeeded:{op} or evolution_failed:{op}
   *  event (separate from the mutation:schema_evolution DAG node). */
  evolutionEventHash: Uint8Array | null;
}

export function parseSubmitMutationResponse(response: Message): MutationResult {
  if (response.messageType !== MSG_TYPE.SUBMIT_MUTATION_RESPONSE) {
    throw new BridgeProtocolError(
      `expected submit_mutation_response; got ${response.messageType}`,
    );
  }
  const classV = response.payload.get("classification");
  const acceptedV = response.payload.get("accepted");
  const reasonV = response.payload.get("rejection_reason");
  const typeV = response.payload.get("mutation_type");
  const hashV = response.payload.get("dag_node_hash");
  if (
    !classV || classV.type !== "string" ||
    !acceptedV || acceptedV.type !== "bool" ||
    !reasonV || reasonV.type !== "string" ||
    !typeV || typeV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "submit_mutation_response missing required typed fields",
    );
  }
  // M17 P3 永恒进化 fields (back-compat: optional; defaults if absent).
  const applyAttemptedV = response.payload.get("schema_apply_attempted");
  const applySucceededV = response.payload.get("schema_apply_succeeded");
  const applyReasonV = response.payload.get("schema_apply_failure_reason");
  const applyOpV = response.payload.get("schema_apply_op");
  const applySummaryV = response.payload.get("schema_apply_summary");
  const evoHashV = response.payload.get("evolution_event_hash");
  return {
    classification: classV.value,
    accepted: acceptedV.value,
    rejectionReason: reasonV.value,
    mutationType: typeV.value,
    dagNodeHash: hashV && hashV.type === "bytes" ? hashV.value : null,
    schemaApplyAttempted:
      applyAttemptedV && applyAttemptedV.type === "bool" ? applyAttemptedV.value : false,
    schemaApplySucceeded:
      applySucceededV && applySucceededV.type === "bool" ? applySucceededV.value : false,
    schemaApplyFailureReason:
      applyReasonV && applyReasonV.type === "string" ? applyReasonV.value : "",
    schemaApplyOp: applyOpV && applyOpV.type === "string" ? applyOpV.value : "",
    schemaApplySummary:
      applySummaryV && applySummaryV.type === "string" ? applySummaryV.value : "",
    evolutionEventHash: evoHashV && evoHashV.type === "bytes" ? evoHashV.value : null,
  };
}

/** One DAG node from a `query_recent_nodes_response` (M8). */
export interface RecentDagNode {
  hash: Uint8Array;
  parentHashes: Uint8Array[];
  nodeType: string;
  atCycle: bigint;
  contentCanonicalBytes: Uint8Array;
}

/** Parsed `query_recent_nodes_response` (M8; extended M16). */
export interface RecentNodesReport {
  /** Total node count in the substrate's DAG (unfiltered). */
  totalDagSize: bigint;
  /** When `node_type_prefix` filter applied: total nodes matching the filter
   *  (before the count-limit was applied). When no filter: equals totalDagSize. */
  filteredTotal: bigint;
  returnedCount: bigint;
  dagTip: Uint8Array | null;
  nodes: RecentDagNode[];
}

export function parseQueryRecentNodesResponse(response: Message): RecentNodesReport {
  if (response.messageType !== MSG_TYPE.QUERY_RECENT_NODES_RESPONSE) {
    throw new BridgeProtocolError(
      `expected query_recent_nodes_response; got ${response.messageType}`,
    );
  }
  const totalV = response.payload.get("total_dag_size");
  const returnedV = response.payload.get("returned_count");
  const nodesV = response.payload.get("nodes");
  if (
    !totalV || totalV.type !== "uint" ||
    !returnedV || returnedV.type !== "uint" ||
    !nodesV || nodesV.type !== "array"
  ) {
    throw new BridgeProtocolError(
      "query_recent_nodes_response missing required typed fields",
    );
  }
  const tipV = response.payload.get("dag_tip");
  const dagTip = tipV && tipV.type === "bytes" ? tipV.value : null;

  const nodes: RecentDagNode[] = nodesV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(`recent_node is not a Map: ${v.type}`);
    }
    const m = v.value;
    const hashV = m.get("hash");
    const parentsV = m.get("parent_hashes");
    const typeV = m.get("node_type");
    const cycleV = m.get("at_cycle");
    const contentV = m.get("content_canonical_bytes");
    if (
      !hashV || hashV.type !== "bytes" ||
      !parentsV || parentsV.type !== "array" ||
      !typeV || typeV.type !== "string" ||
      !cycleV || cycleV.type !== "uint" ||
      !contentV || contentV.type !== "bytes"
    ) {
      throw new BridgeProtocolError("recent_node Map missing required fields");
    }
    const parentHashes: Uint8Array[] = parentsV.value.map((p) => {
      if (p.type !== "bytes") {
        throw new BridgeProtocolError(
          `parent_hashes contains non-Bytes: ${p.type}`,
        );
      }
      return p.value;
    });
    return {
      hash: hashV.value,
      parentHashes,
      nodeType: typeV.value,
      atCycle: cycleV.value,
      contentCanonicalBytes: contentV.value,
    };
  });
  // M16: filtered_total optional (back-compat for older substrate that omits).
  const filteredV = response.payload.get("filtered_total");
  const filteredTotal =
    filteredV && filteredV.type === "uint" ? filteredV.value : totalV.value;
  return {
    totalDagSize: totalV.value,
    filteredTotal,
    returnedCount: returnedV.value,
    dagTip,
    nodes,
  };
}

/** Parse a `hello_ack` response. */
export function parseHelloAck(response: Message): HelloAck {
  if (response.messageType !== MSG_TYPE.HELLO_ACK) {
    throw new BridgeProtocolError(
      `expected hello_ack; got ${response.messageType}`,
    );
  }
  const tropV = response.payload.get("kernel_tropism_version");
  const pyV = response.payload.get("python_version");
  const subV = response.payload.get("substrate_version");
  if (!tropV || tropV.type !== "string") {
    throw new BridgeProtocolError("hello_ack missing kernel_tropism_version");
  }
  if (!pyV || pyV.type !== "string") {
    throw new BridgeProtocolError("hello_ack missing python_version");
  }
  return {
    kernelTropismVersion: tropV.value,
    pythonVersion: pyV.value,
    substrateVersion: subV && subV.type === "string" ? subV.value : "",
  };
}
