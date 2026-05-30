// M16 P2 永恒吞噬: ingest_raw_material + perturb_axis_from_raw_material.
//
// Split out of the former monolithic `protocol/messages.ts`. Payload/response
// Map field names + value types mirror the substrate handlers byte-for-byte.

import { type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";
import { floatRepr } from "./floats.ts";

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
