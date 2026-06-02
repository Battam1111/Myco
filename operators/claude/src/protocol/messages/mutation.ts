// Mutation + attestation family — schema_diff builders, attestation-nonce
// request/response, REVEAL-key binding, DAG-tip co-sign + L0-revision
// envelopes, and the submit_mutation payload builder.
//
// Split out of the former monolithic `protocol/messages.ts`. Every
// canonical-bytes Map here is owner/operator-signed or substrate-verified;
// field name/type/order is the security + wire contract and must not drift
// (drift = C18 canonical_bytes_render_drift / C5 attestation_invalid).

import { encode, type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";
import { floatRepr } from "./floats.ts";

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
// **M26.4 F20 P14.c owner_objective_declaration** — owner-declared sparse
// weight vector over node_type prefixes (telos-drift cosine proxy).
// ---------------------------------------------------------------------------

/** Build the content_canonical_bytes for an `owner_objective_declaration`
 *  CI mutation (M26.4 F20). Byte-for-byte mirror of the Rust
 *  `substrate::events::encode_owner_objective` (substrate/src/events/telos.rs).
 *
 *  Shape:
 *  ```
 *  Map({
 *    "objective_id": String,
 *    "declared_at_cycle": Uint,
 *    "weights": Array<Map({ "prefix": String, "weight_repr": String })>,
 *  })
 *  ```
 *
 *  Each weight is rendered as a `weight_repr` STRING via {@link floatRepr}
 *  (the project-wide canonical-bytes float convention — CPython-repr oracle).
 *  The substrate decodes by `weight_repr.parse::<f64>()`, so any
 *  shortest-round-tripping decimal is accepted; using `floatRepr` keeps the
 *  submitted bytes identical to the sporocarp/schema_diff float renderings and
 *  to the M26.4 e2e inline objective Map (which asserts `"0.75"` / `"0.25"`).
 *
 *  The operator signs THESE bytes as the CI attestation. Map-key order here is
 *  irrelevant (canonical-bytes sorts keys); the field NAMES + value TYPES are
 *  the wire contract and must match Rust (drift = C18 / C5).
 *
 *  Note: the `weights` array MAY be empty here, but the substrate rejects an
 *  empty-weights declaration with C5 (`weights array MUST be non-empty`); the
 *  tool surface enforces `minItems: 1` so callers fail fast. */
export function buildOwnerObjectiveCanonicalBytes(args: {
  objectiveId: string;
  declaredAtCycle: bigint;
  weights: { prefix: string; weight: number }[];
}): Uint8Array {
  const m = new Map<string, Value>();
  m.set("objective_id", { type: "string", value: args.objectiveId });
  m.set("declared_at_cycle", { type: "uint", value: args.declaredAtCycle });
  m.set("weights", {
    type: "array",
    value: args.weights.map((w) => {
      const entry = new Map<string, Value>();
      entry.set("prefix", { type: "string", value: w.prefix });
      entry.set("weight_repr", { type: "string", value: floatRepr(w.weight) });
      return { type: "map", value: entry } as Value;
    }),
  });
  return encode({ type: "map", value: m }).bytes;
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

// ---------------------------------------------------------------------------
// **M-anchor-5 §9.2.2 / §9.2.4** — DAG-tip co-sign + L0 revision envelopes.
//
// Both envelopes are owner-signed canonical-bytes Maps. Their shapes mirror
// the Rust `build_dag_tip_cosign_canonical_bytes` and
// `build_l0_revision_canonical_bytes` byte-for-byte; any drift breaks the
// signature check on the substrate side and emits C18 canonical_bytes_render_drift
// (via C5 attestation_invalid for the immediate cosign flow).
// ---------------------------------------------------------------------------

/** Domain string for DAG-tip co-sign signatures (M-anchor-5 §9.2.2). */
export const DAG_TIP_COSIGN_DOMAIN = "myco-dag-tip-cosign-v1";

/** Domain string for L0 revision attestation signatures (M-anchor-5 §9.2.4). */
export const L0_REVISION_DOMAIN = "myco-l0-revision-v1";

/** Build the canonical-bytes Map the owner signs for a DAG-tip co-sign.
 *
 *  Shape (sorted by canonical-bytes Map iteration):
 *  ```
 *  Map({
 *    "anchor_nonce": Bytes(32),
 *    "anchor_timestamp_unix_ns": Timestamp,
 *    "domain": String("myco-dag-tip-cosign-v1"),
 *    "enumerated_node_hashes": Array<Bytes(32)>,
 *    "proposed_mutation_hash": Bytes(32),
 *    "tip_hash": Bytes(32),
 *  })
 *  ```
 *
 *  `proposedMutationHash` MAY be all-zero (32 zero bytes) for a standalone
 *  tip co-sign with no proposed CI mutation; the substrate accepts both
 *  shapes. */
export function buildDagTipCosignCanonicalBytes(args: {
  tipHash: Uint8Array;
  enumeratedNodeHashes: Uint8Array[];
  proposedMutationHash: Uint8Array;
  anchorTimestampUnixNs: bigint;
  anchorNonce: Uint8Array;
}): Uint8Array {
  if (args.tipHash.length !== 32) {
    throw new BridgeProtocolError(
      `tipHash must be 32 bytes; got ${args.tipHash.length}`,
    );
  }
  if (args.proposedMutationHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposedMutationHash must be 32 bytes; got ${args.proposedMutationHash.length}`,
    );
  }
  if (args.anchorNonce.length !== 32) {
    throw new BridgeProtocolError(
      `anchorNonce must be 32 bytes; got ${args.anchorNonce.length}`,
    );
  }
  for (const [i, h] of args.enumeratedNodeHashes.entries()) {
    if (h.length !== 32) {
      throw new BridgeProtocolError(
        `enumeratedNodeHashes[${i}] must be 32 bytes; got ${h.length}`,
      );
    }
  }
  const m = new Map<string, Value>();
  m.set("domain", { type: "string", value: DAG_TIP_COSIGN_DOMAIN });
  m.set("tip_hash", { type: "bytes", value: args.tipHash });
  m.set("enumerated_node_hashes", {
    type: "array",
    value: args.enumeratedNodeHashes.map(
      (h) => ({ type: "bytes", value: h }) as Value,
    ),
  });
  m.set("proposed_mutation_hash", {
    type: "bytes",
    value: args.proposedMutationHash,
  });
  m.set("anchor_timestamp_unix_ns", {
    type: "timestamp",
    value: args.anchorTimestampUnixNs,
  });
  m.set("anchor_nonce", { type: "bytes", value: args.anchorNonce });
  return encode({ type: "map", value: m }).bytes;
}

/** Domain string for reproduction spawn co-sign signatures (P08 §3.5 / §5.1).
 *  Mirrors the Rust `SPAWN_COSIGN_DOMAIN`. */
export const SPAWN_COSIGN_DOMAIN = "myco-spawn-cosign-v1";

/** **P08 §3.5 / §5.1** — build the canonical-bytes Map the cultivator signs to
 *  co-attest a child substrate spawn. Rust-parity with
 *  `substrate::events::build_spawn_cosign_canonical_bytes`; field
 *  name/type/order is the security + wire contract and must not drift.
 *
 *  Shape:
 *  ```
 *  Map({
 *    "anchor_nonce": Bytes(32),
 *    "anchor_timestamp_unix_ns": Timestamp,
 *    "child_genesis_timestamp_unix_ns": Timestamp,
 *    "depth_override": Bool,
 *    "domain": String("myco-spawn-cosign-v1"),
 *    "parent_substrate_id": Bytes(32),
 *    "spore_schema_hash": Bytes(32),
 *  })
 *  ```
 *
 *  - `parentSubstrateId` binds the spawn to THIS parent (replay guard);
 *  - `sporeSchemaHash` = blake3(spore_schema_canonical_bytes) — pins the
 *    child's static schema (I7(a));
 *  - `childGenesisTimestampUnixNs` feeds the §5.6 owner-minted child-id;
 *  - `anchorTimestampUnixNs` + `anchorNonce` are the anchor-surface wall-clock
 *    + unbiasable nonce (the §16.B rate throttle reads the timestamp);
 *  - `depthOverride` is the cultivator's explicit, signed override of the
 *    §16.A lineage-depth cap for THIS spawn (default false). */
export function buildSpawnCosignCanonicalBytes(args: {
  parentSubstrateId: Uint8Array;
  sporeSchemaHash: Uint8Array;
  childGenesisTimestampUnixNs: bigint;
  anchorTimestampUnixNs: bigint;
  anchorNonce: Uint8Array;
  depthOverride: boolean;
}): Uint8Array {
  if (args.parentSubstrateId.length !== 32) {
    throw new BridgeProtocolError(
      `parentSubstrateId must be 32 bytes; got ${args.parentSubstrateId.length}`,
    );
  }
  if (args.sporeSchemaHash.length !== 32) {
    throw new BridgeProtocolError(
      `sporeSchemaHash must be 32 bytes; got ${args.sporeSchemaHash.length}`,
    );
  }
  if (args.anchorNonce.length !== 32) {
    throw new BridgeProtocolError(
      `anchorNonce must be 32 bytes; got ${args.anchorNonce.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("domain", { type: "string", value: SPAWN_COSIGN_DOMAIN });
  m.set("parent_substrate_id", { type: "bytes", value: args.parentSubstrateId });
  m.set("spore_schema_hash", { type: "bytes", value: args.sporeSchemaHash });
  m.set("child_genesis_timestamp_unix_ns", {
    type: "timestamp",
    value: args.childGenesisTimestampUnixNs,
  });
  m.set("anchor_timestamp_unix_ns", {
    type: "timestamp",
    value: args.anchorTimestampUnixNs,
  });
  m.set("anchor_nonce", { type: "bytes", value: args.anchorNonce });
  m.set("depth_override", { type: "bool", value: args.depthOverride });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the canonical-bytes Map the owner signs for an L0 revision
 *  attestation.
 *
 *  Shape:
 *  ```
 *  Map({
 *    "anchor_nonce": Bytes(32),
 *    "anchor_timestamp_unix_ns": Timestamp,
 *    "diff_summary": String,
 *    "domain": String("myco-l0-revision-v1"),
 *    "new_l0_hash": Bytes(32),
 *    "prior_l0_hash": Bytes(32),
 *  })
 *  ```
 *
 *  `diffSummary` should be a short human-readable description of what
 *  changed (e.g., "Add §9.4 federation observatory"). The hashes are
 *  SHA-256 (or BLAKE3 — owner-tooling choice; the substrate doesn't
 *  re-derive these, it only attests to the signed envelope). */
export function buildL0RevisionCanonicalBytes(args: {
  priorL0Hash: Uint8Array;
  newL0Hash: Uint8Array;
  diffSummary: string;
  anchorTimestampUnixNs: bigint;
  anchorNonce: Uint8Array;
}): Uint8Array {
  if (args.priorL0Hash.length !== 32) {
    throw new BridgeProtocolError(
      `priorL0Hash must be 32 bytes; got ${args.priorL0Hash.length}`,
    );
  }
  if (args.newL0Hash.length !== 32) {
    throw new BridgeProtocolError(
      `newL0Hash must be 32 bytes; got ${args.newL0Hash.length}`,
    );
  }
  if (args.anchorNonce.length !== 32) {
    throw new BridgeProtocolError(
      `anchorNonce must be 32 bytes; got ${args.anchorNonce.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("domain", { type: "string", value: L0_REVISION_DOMAIN });
  m.set("prior_l0_hash", { type: "bytes", value: args.priorL0Hash });
  m.set("new_l0_hash", { type: "bytes", value: args.newL0Hash });
  m.set("diff_summary", { type: "string", value: args.diffSummary });
  m.set("anchor_timestamp_unix_ns", {
    type: "timestamp",
    value: args.anchorTimestampUnixNs,
  });
  m.set("anchor_nonce", { type: "bytes", value: args.anchorNonce });
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
  /** v3.1.1 Sprint 8.G (P03 §10.4): opt into the multi-cycle two-phase schema
   *  migration path for a `schema_evolution` mutation. When true (and the
   *  mutation is accepted), the substrate builds a CANDIDATE schema and
   *  validates it across a window of cycles before committing — instead of the
   *  default single-cycle apply. Omitted/false = the existing single-cycle
   *  path (back-compat). Only meaningful for `mutationType="schema_evolution"`. */
  migrationMode?: boolean;
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
  // v3.1.1 Sprint 8.G: opt into two-phase migration. Emitted only when true so
  // the default single-cycle payload bytes are unchanged.
  if (args.migrationMode === true) {
    m.set("migration_mode", { type: "bool", value: true });
  }
  return m;
}

/** Build the content_canonical_bytes for an `abort_migration` CI mutation
 *  (v3.1.1 Sprint 8.G / P03 §10.4).
 *
 *  An operator submits this (via `submitMutationPayload` with
 *  `mutationType="abort_migration"`) to force-roll-back an in-flight two-phase
 *  schema migration before its dual-validation window completes. The content
 *  records WHICH migration the operator intends to abort (the op name) plus a
 *  free-form reason, so the abort is auditable. The substrate forces the
 *  rollback path on an accepted abort_migration mutation regardless of the
 *  recorded op (it aborts whatever single migration is in flight). */
export function abortMigrationContentBytes(args: {
  op: string;
  reason: string;
}): Uint8Array {
  const m = new Map<string, Value>();
  m.set("op", { type: "string", value: args.op });
  m.set("reason", { type: "string", value: args.reason });
  return encode({ type: "map", value: m }).bytes;
}
