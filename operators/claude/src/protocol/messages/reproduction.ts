// M20 P8 永恒繁衍: substrate reproduction (sprout_child).
//
// Split out of the former monolithic `protocol/messages.ts`. Payload/response
// Map field names + value types mirror the substrate handler byte-for-byte.

import { type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

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
