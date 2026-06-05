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

/** Build the payload for a `deposit_forged_understanding` request (the
 *  "use-forges" forging loop).
 *
 *  Activates L0 P2 永恒吞噬 + P6 永恒因果 — the agent's DIGESTED understanding
 *  (prose/knowledge it forged out of raw_material) is stored as a
 *  `forged_understanding:{label}` DAG node, causally parented by the prior tip
 *  AND each source raw_material node it was forged from. Max 512 KiB on the
 *  `understanding` bytes. The understanding is encoded UTF-8→bytes by the caller
 *  (mirrors how ingest encodes content). General — NOT tied to a gradient axis.
 */
export function depositForgedUnderstandingPayload(args: {
  label: string;
  understanding: Uint8Array;
  sourceRawMaterialHashes?: Uint8Array[];
  value?: number;
  confidence?: number;
  supersedes?: Uint8Array[];
}): Map<string, Value> {
  if (!args.label || args.label.length === 0) {
    throw new BridgeProtocolError(
      "deposit_forged_understanding: label must be a non-empty string",
    );
  }
  const sources = args.sourceRawMaterialHashes ?? [];
  for (const h of sources) {
    if (h.length !== 32) {
      throw new BridgeProtocolError(
        `source_raw_material_hashes entry must be 32 bytes; got ${h.length}`,
      );
    }
  }
  const supersedes = args.supersedes ?? [];
  for (const h of supersedes) {
    if (h.length !== 32) {
      throw new BridgeProtocolError(
        `supersedes entry must be 32 bytes; got ${h.length}`,
      );
    }
  }
  const m = new Map<string, Value>();
  m.set("label", { type: "string", value: args.label });
  m.set("understanding", { type: "bytes", value: args.understanding });
  m.set("source_raw_material_hashes", {
    type: "array",
    value: sources.map((h) => ({ type: "bytes", value: h }) as Value),
  });
  // Step-1 discernment fields — set ONLY when provided, so a forge omitting them
  // produces canonical bytes identical to the pre-step-1 shape (the substrate
  // composes a byte-identical node; no reseal). value/confidence are Uint 0..=100.
  if (args.value !== undefined) {
    m.set("value", { type: "uint", value: BigInt(args.value) });
  }
  if (args.confidence !== undefined) {
    m.set("confidence", { type: "uint", value: BigInt(args.confidence) });
  }
  if (supersedes.length > 0) {
    m.set("supersedes", {
      type: "array",
      value: supersedes.map((h) => ({ type: "bytes", value: h }) as Value),
    });
  }
  return m;
}

/** Parsed `deposit_forged_understanding_response` (the forging loop). Symmetric
 *  with {@link IngestResult}. */
export interface DepositForgedUnderstandingResult {
  /** DAG node hash of the newly-inserted forged_understanding node. */
  dagNodeHash: Uint8Array;
  /** Substrate's current DAG tip (after the deposit). */
  currentTip: Uint8Array | null;
  totalDagSize: bigint;
}

export function parseDepositForgedUnderstandingResponse(
  response: Message,
): DepositForgedUnderstandingResult {
  if (response.messageType !== MSG_TYPE.DEPOSIT_FORGED_UNDERSTANDING_RESPONSE) {
    throw new BridgeProtocolError(
      `expected deposit_forged_understanding_response; got ${response.messageType}`,
    );
  }
  const hashV = response.payload.get("dag_node_hash");
  const totalV = response.payload.get("total_dag_size");
  if (!hashV || hashV.type !== "bytes" || !totalV || totalV.type !== "uint") {
    throw new BridgeProtocolError(
      "deposit_forged_understanding_response missing required typed fields",
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
