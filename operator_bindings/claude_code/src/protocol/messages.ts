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

/** Build the payload for a `hello` request. */
export function helloPayload(sessionSecret: Uint8Array): Map<string, Value> {
  if (sessionSecret.length !== 32) {
    throw new BridgeProtocolError(
      `session_secret must be exactly 32 bytes; got ${sessionSecret.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("session_secret", { type: "bytes", value: sessionSecret });
  return m;
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

/** Parsed `advance_response` payload. */
export interface AdvanceReport {
  /** Echo of the substrate's authoritative cycle counter (when from myco-substrate). */
  cycleNumber: bigint | null;
  fruitedAxes: string[];
  sporocarps: SporocarpReport[];
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

  return { cycleNumber, fruitedAxes, sporocarps };
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
