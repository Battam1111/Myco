// Mutation family — schema_diff builders, the spawn-cosign envelope builder,
// and the submit_mutation payload builder.
//
// Split out of the former monolithic `protocol/messages.ts`. **v0.9 owner-key
// removal**: the attestation-nonce request/response, the M14 REVEAL-key
// binding, and the DAG-tip-cosign + L0-revision envelope builders were removed
// with the anchor surface; nothing here is owner-signed. The canonical-bytes
// Maps that remain are still the substrate's wire contract (e.g. the
// spawn-cosign envelope the substrate verifies for I7(a) + replay-guard);
// field name/type/order must not drift (drift = C18 canonical_bytes_render_drift
// / C68 reproduction_unattested_spawn).

import { encode, type Value } from "../../canonical/canonical_bytes.ts";
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

// ---------------------------------------------------------------------------
// **v0.9 owner-key removal** — the M13 attestation-nonce request/response
// (`requestAttestationNoncePayload` / `AttestationNonceResult` /
// `parseRequestAttestationNonceResponse`), the M14 REVEAL-key binding
// (`revealKeyBindingSigningInput`), and the M-anchor-5 §9.2.2 / §9.2.4
// DAG-tip-cosign + L0-revision envelopes (`DAG_TIP_COSIGN_DOMAIN` /
// `L0_REVISION_DOMAIN` / `buildDagTipCosignCanonicalBytes` /
// `buildL0RevisionCanonicalBytes`) were ALL removed with the anchor surface.
// The substrate no longer issues nonces, no longer verifies owner Ed25519
// signatures over CI mutations, and no longer accepts the `dag_tip_cosign` /
// `l0_revision_attest` mutation types. The spawn-cosign envelope below survives
// (the substrate still decodes its STRUCTURE for the keyless sprout_child path).
// ---------------------------------------------------------------------------

/** Domain string for reproduction spawn co-sign signatures (P08 §3.5 / §5.1).
 *  Mirrors the Rust `SPAWN_COSIGN_DOMAIN`. */
export const SPAWN_COSIGN_DOMAIN = "myco-spawn-cosign-v1";

/** **P08 §3.5 / §5.1** — build the canonical-bytes spawn-cosign envelope for a
 *  child substrate spawn. v0.9 keyless: the substrate decodes this STRUCTURE
 *  (parent replay-guard + I7(a) spore-schema binding + §16.B rate throttle) but
 *  no longer verifies a cultivator signature over it. Rust-parity with
 *  `substrate::events::build_spawn_cosign_canonical_bytes`; field
 *  name/type/order is the wire contract and must not drift.
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
 *  - `childGenesisTimestampUnixNs` feeds the §5.6 deterministically-minted child-id;
 *  - `anchorTimestampUnixNs` + `anchorNonce` keep their wire-contract names but
 *    are v0.9-keyless: the operator stamps a local wall-clock timestamp + a
 *    fresh random nonce (no anchor process; the §16.B rate throttle only needs
 *    the timestamp to be strictly increasing vs the prior spawn);
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

/** Build the payload for a `submit_mutation` request (M10).
 *
 *  **v0.9 keyless**: the substrate no longer verifies the owner Ed25519
 *  attestation signature — CI mutations are classified by the Python classifier
 *  on `mutation_type` + content. The signature-related fields below
 *  (`attestationSignature`, `nonce`, `expiryUnixNs`, `revealPubkey`,
 *  `identitySignatureOverRevealPubkey`, `anchorClockSubmittedAtUnixNs`) are now
 *  OPTIONAL passthroughs the substrate ignores; daily-mode callers omit them.
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
  /** **v0.9 owner-key removal**: vestigial optional passthrough. This was the
   *  M15 dual-clock submit-time stamp the anchor surface verified against an
   *  issued nonce window; the anchor surface + nonce issuance are gone, so the
   *  substrate ignores it. Retained only so callers holding a legacy value can
   *  still pass it without a type error. */
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
