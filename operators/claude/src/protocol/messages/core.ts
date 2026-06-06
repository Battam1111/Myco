// Core lifecycle request payload builders — hello / register_axis / perturb /
// advance / snapshot-empty / query_recent_nodes / compute_intent.
//
// Split out of the former monolithic `protocol/messages.ts`. Payload Map field
// names + value types + insertion order are the wire contract; do not alter.

import { type Value } from "../../canonical/canonical_bytes.ts";
import { BridgeProtocolError } from "./wire.ts";
import { floatRepr } from "./floats.ts";

// ---------------------------------------------------------------------------
// Payload builders for common messages.
// ---------------------------------------------------------------------------

/** Build the payload for a `hello` request.
 *
 * **v0.9 keyless** (owner-key removal): the hello carries ONLY the
 * `session_secret`. The M9 `operator_pubkey` + `hello_signature` TOFU-pinning
 * fields were removed with the anchor surface — `substrate/src/handshake.rs`
 * now completes the handshake on a well-formed 32-byte `session_secret` alone
 * and ignores any identity fields. Mirrors the Rust/Python `hello_payload`,
 * which are likewise session-secret-only.
 */
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
