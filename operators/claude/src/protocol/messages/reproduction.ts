// M20 P8 永恒繁衍: substrate reproduction (sprout_child).
//
// Split out of the former monolithic `protocol/messages.ts`. Payload/response
// Map field names + value types mirror the substrate handler byte-for-byte.

import {
  encode,
  type Value,
} from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

/** **P08 §3.5 / L1/SCHEMA §3.1** — assemble the child's spore-schema canonical
 *  bytes (the 7-field shape the cultivator co-signs + the substrate validates
 *  for I7(a) static-schema closure). Rust-parity with
 *  `myco_kernel_schema::spore::SporeSchema::to_canonical_bytes`: a Map with
 *  exactly the seven named fields (canonically sorted by `encode`), each
 *  present (non-Null). The substrate checks blake3(these bytes) == the
 *  co-signed envelope's `spore_schema_hash` AND that all 7 fields are present;
 *  it builds the child's actual gradient from its own internal query, so these
 *  bytes are the STATIC-SCHEMA attestation (not the live gradient state).
 *
 *  Callers (mcp_server) populate `schemaDefinitions` /
 *  `initialAppetiteAxisSchema` from the parent's observed axes; the structural
 *  descriptor fields default to compact constant markers when not supplied.
 *  Every field must be a non-Null `Value` or the substrate rejects with C68. */
export function buildSporeSchemaCanonicalBytes(fields: {
  schemaDefinitions: Value;
  canonicalBytesSerializerSpec: Value;
  sporocarpTypeTree: Value;
  classifierDimensionTable: Value;
  initialAppetiteAxisSchema: Value;
  anchorSurfaceConfig: Value;
  parentImmuneSignalSummary: Value;
}): Uint8Array {
  const m = new Map<string, Value>();
  m.set("schema_definitions", fields.schemaDefinitions);
  m.set("canonical_bytes_serializer_spec", fields.canonicalBytesSerializerSpec);
  m.set("sporocarp_type_tree", fields.sporocarpTypeTree);
  m.set("classifier_dimension_table", fields.classifierDimensionTable);
  m.set("initial_appetite_axis_schema", fields.initialAppetiteAxisSchema);
  m.set("anchor_surface_config", fields.anchorSurfaceConfig);
  m.set("parent_immune_signal_summary", fields.parentImmuneSignalSummary);
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for a `sprout_child` request (M20 + P08 §3.5 / §5.1).
 *
 *  The substrate creates a child state_dir containing the parent's
 *  spore-schema (gradient axes + values + operator identity + the
 *  OWNER-MINTED deterministic child substrate_id). Operator can then spawn a
 *  new substrate process at `childStateDir` via the MYCO_STATE_DIR env var.
 *
 *  The parent emits a `spore_emission:{child_id_prefix}` DAG node recording
 *  the reproduction. The parent's causal DAG is NOT transferred to the child
 *  (L1 decision per L0 P8 — child starts its own causal history).
 *
 *  **P08 §5.1 — cultivator co-attestation is now REQUIRED**: a child spawn is
 *  a CI-class doctrine event, not a daily-mode mutation. The three attestation
 *  fields below MUST be present or the substrate refuses with C68
 *  (reproduction_unattested_spawn) before any side effect:
 *   - `spawn_cosign_envelope` — the cultivator-signed myco-spawn-cosign-v1
 *     canonical-bytes envelope (built via `buildSpawnCosignCanonicalBytes`);
 *   - `attestation_signature` — the cultivator's 64-byte Ed25519 signature
 *     over those exact envelope bytes;
 *   - `spore_schema_canonical_bytes` — the child's spore-schema canonical
 *     bytes, for I7(a) static-schema validation (blake3 must match the
 *     envelope's spore_schema_hash AND the 7-field shape must be well-formed).
 */
export function sproutChildPayload(args: {
  childStateDir: string;
  spawnCosignEnvelope: Uint8Array;
  attestationSignature: Uint8Array;
  sporeSchemaCanonicalBytes: Uint8Array;
  spore_metadata?: Map<string, Value>;
}): Map<string, Value> {
  if (!args.childStateDir || args.childStateDir.length === 0) {
    throw new BridgeProtocolError("sprout_child: childStateDir is required");
  }
  if (args.attestationSignature.length !== 64) {
    throw new BridgeProtocolError(
      `sprout_child: attestationSignature must be 64 bytes; got ${args.attestationSignature.length}`,
    );
  }
  if (args.spawnCosignEnvelope.length === 0) {
    throw new BridgeProtocolError("sprout_child: spawnCosignEnvelope is required");
  }
  if (args.sporeSchemaCanonicalBytes.length === 0) {
    throw new BridgeProtocolError(
      "sprout_child: sporeSchemaCanonicalBytes is required",
    );
  }
  const m = new Map<string, Value>();
  m.set("child_state_dir", { type: "string", value: args.childStateDir });
  m.set("spawn_cosign_envelope", {
    type: "bytes",
    value: args.spawnCosignEnvelope,
  });
  m.set("attestation_signature", {
    type: "bytes",
    value: args.attestationSignature,
  });
  m.set("spore_schema_canonical_bytes", {
    type: "bytes",
    value: args.sporeSchemaCanonicalBytes,
  });
  if (args.spore_metadata) {
    m.set("spore_metadata", { type: "map", value: args.spore_metadata });
  }
  return m;
}

/** Parsed `sprout_child_response` (M20 + P08 §3.5). */
export interface SproutChildResult {
  childSubstrateId: Uint8Array;
  childStateDir: string;
  childAxisCount: bigint;
  /** DAG node hash of the spore_emission:{prefix} node in the parent's DAG. */
  sporeEmissionHash: Uint8Array;
  /** **P08 §3.5 I7-closure**: DAG node hash of the
   *  `genesis_attested:{child_prefix}` node in the PARENT's DAG (the
   *  cultivator-attested birth record). */
  genesisAttestedHash: Uint8Array;
  /** **P08 §5.6**: the cultivator-signed child genesis timestamp (unix ns) —
   *  one of the inputs to the owner-minted child-id derivation. */
  childGenesisTimestampUnixNs: bigint;
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
  const gaV = response.payload.get("genesis_attested_hash");
  const tsV = response.payload.get("child_genesis_timestamp_unix_ns");
  if (
    !idV || idV.type !== "bytes" ||
    !dirV || dirV.type !== "string" ||
    !axisV || axisV.type !== "uint" ||
    !hashV || hashV.type !== "bytes" ||
    !gaV || gaV.type !== "bytes" ||
    !tsV || tsV.type !== "timestamp"
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
    genesisAttestedHash: gaV.value,
    childGenesisTimestampUnixNs: tsV.value,
  };
}
