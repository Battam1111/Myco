// Response parsers — advance / snapshot / hello_ack / compute_intent / immune
// events + checks / submit_mutation / query_recent_nodes / enumerate_dag_since.
//
// Split out of the former monolithic `protocol/messages.ts`. Each parser pins
// the substrate response Map field names + value types; field/type drift
// surfaces here as a `BridgeProtocolError` decode failure.

import { type Value } from "../../canonical/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

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
   *  evidence + timestamp). Operators can decode via the canonical-bytes
   *  renderer (`src/canonical/renderer.ts`; relocated from the deleted
   *  anchor client). */
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
  /** M26.3 P10.c: DAG node hash of the `compression_event:{rule_id}` event
   *  emitted after a successful compression mutation. Null otherwise. */
  compressionEventHash: Uint8Array | null;
  /** **v0.9 owner-key removal**: vestigial. The `dag_tip_cosign` /
   *  `l0_revision_attest` mutation types were removed with the anchor surface,
   *  so the substrate never emits `tip_cosigned:{prefix}` /
   *  `l0_revision_attested:{prefix}`; these always parse as `null`. Retained
   *  as optional back-compat fields so old response payloads still decode. */
  tipCosignEventHash: Uint8Array | null;
  /** **v0.9 owner-key removal**: vestigial (always `null`). See
   *  `tipCosignEventHash`. */
  l0RevisionEventHash: Uint8Array | null;
  /** v3.1.1 Sprint 8.G (P03 §10.4): true iff the substrate took the two-phase
   *  migration path for this mutation (migration_mode was requested + accepted). */
  migrationMode: boolean;
  /** Sprint 8.G: when `migrationMode`, whether the candidate schema was built
   *  successfully (true → a dual-validation window was opened; false → the
   *  migration rolled back immediately because the candidate could not be built). */
  candidateBuilt: boolean;
  /** Sprint 8.G: DAG node hash of the `schema_migration_started:{op}` event,
   *  if a migration window was opened. Null otherwise. */
  schemaMigrationStartedEventHash: Uint8Array | null;
  /** Sprint 8.G: DAG node hash of the `schema_migration_rolled_back:{op}` event,
   *  if the candidate build failed and rolled back immediately. Null otherwise. */
  schemaMigrationRolledBackEventHash: Uint8Array | null;
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
  const compressionHashV = response.payload.get("compression_event_hash");
  const tipCosignHashV = response.payload.get("tip_cosign_event_hash");
  const l0RevisionHashV = response.payload.get("l0_revision_event_hash");
  // v3.1.1 Sprint 8.G migration fields (back-compat: optional; defaults if absent).
  const migrationModeV = response.payload.get("migration_mode");
  const candidateBuiltV = response.payload.get("candidate_built");
  const migStartedHashV = response.payload.get(
    "schema_migration_started_event_hash",
  );
  const migRolledBackHashV = response.payload.get(
    "schema_migration_rolled_back_event_hash",
  );
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
    compressionEventHash:
      compressionHashV && compressionHashV.type === "bytes" ? compressionHashV.value : null,
    tipCosignEventHash:
      tipCosignHashV && tipCosignHashV.type === "bytes" ? tipCosignHashV.value : null,
    l0RevisionEventHash:
      l0RevisionHashV && l0RevisionHashV.type === "bytes" ? l0RevisionHashV.value : null,
    migrationMode:
      migrationModeV && migrationModeV.type === "bool" ? migrationModeV.value : false,
    candidateBuilt:
      candidateBuiltV && candidateBuiltV.type === "bool" ? candidateBuiltV.value : false,
    schemaMigrationStartedEventHash:
      migStartedHashV && migStartedHashV.type === "bytes" ? migStartedHashV.value : null,
    schemaMigrationRolledBackEventHash:
      migRolledBackHashV && migRolledBackHashV.type === "bytes"
        ? migRolledBackHashV.value
        : null,
  };
}

/** Parsed `query_migration_pending_response` (v3.1.1 Sprint 8.G / P03 §10.4). */
export interface MigrationPendingReport {
  /** Whether a two-phase schema migration is currently in flight. */
  pending: boolean;
  /** The migration's schema_diff op (empty when not pending). */
  op: string;
  /** Cycle at which the dual-validation window opened (0 when not pending). */
  startedAtCycle: bigint;
  /** Number of cycles the candidate must validate before commit (0 when not pending). */
  window: bigint;
  /** The substrate's current cycle counter (for computing progress). */
  currentCycle: bigint;
}

export function parseQueryMigrationPendingResponse(
  response: Message,
): MigrationPendingReport {
  if (response.messageType !== MSG_TYPE.QUERY_MIGRATION_PENDING_RESPONSE) {
    throw new BridgeProtocolError(
      `expected query_migration_pending_response; got ${response.messageType}`,
    );
  }
  const pendingV = response.payload.get("pending");
  const opV = response.payload.get("op");
  const startedV = response.payload.get("started_at_cycle");
  const windowV = response.payload.get("window");
  const currentV = response.payload.get("current_cycle");
  if (
    !pendingV || pendingV.type !== "bool" ||
    !opV || opV.type !== "string" ||
    !startedV || startedV.type !== "uint" ||
    !windowV || windowV.type !== "uint" ||
    !currentV || currentV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "query_migration_pending_response missing required typed fields",
    );
  }
  return {
    pending: pendingV.value,
    op: opV.value,
    startedAtCycle: startedV.value,
    window: windowV.value,
    currentCycle: currentV.value,
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

/** Parsed `read_node_by_hash_response` — the node, or null if it does not exist
 *  (found=false). Unlike the recent-nodes list, this reaches ANY node by hash. */
export function parseReadNodeByHashResponse(response: Message): RecentDagNode | null {
  if (response.messageType !== MSG_TYPE.READ_NODE_BY_HASH_RESPONSE) {
    throw new BridgeProtocolError(
      `expected read_node_by_hash_response; got ${response.messageType}`,
    );
  }
  const foundV = response.payload.get("found");
  if (!foundV || foundV.type !== "bool") {
    throw new BridgeProtocolError("read_node_by_hash_response missing found:bool");
  }
  if (!foundV.value) {
    return null;
  }
  const m = response.payload;
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
      "read_node_by_hash_response (found) missing node fields",
    );
  }
  const parentHashes: Uint8Array[] = parentsV.value.map((p) => {
    if (p.type !== "bytes") {
      throw new BridgeProtocolError(`parent_hashes contains non-Bytes: ${p.type}`);
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
}

/** One entry in the pilot's compact "what I know" map (list_plates). */
export interface PlateIndexEntry {
  hash: Uint8Array;
  label: string;
  /** Pilot-assigned importance 0..=100, or null if the plate carries none. */
  value: bigint | null;
}

/** Parsed `list_plates_response` — the compact live-plate index, sorted by value. */
export interface PlateIndexReport {
  totalPlates: bigint;
  livePlates: bigint;
  plates: PlateIndexEntry[];
}

export function parseListPlatesResponse(response: Message): PlateIndexReport {
  if (response.messageType !== MSG_TYPE.LIST_PLATES_RESPONSE) {
    throw new BridgeProtocolError(
      `expected list_plates_response; got ${response.messageType}`,
    );
  }
  const totalV = response.payload.get("total_plates");
  const liveV = response.payload.get("live_plates");
  const platesV = response.payload.get("plates");
  if (
    !totalV || totalV.type !== "uint" ||
    !liveV || liveV.type !== "uint" ||
    !platesV || platesV.type !== "array"
  ) {
    throw new BridgeProtocolError("list_plates_response missing required fields");
  }
  const plates: PlateIndexEntry[] = platesV.value.map((v) => {
    if (v.type !== "map") {
      throw new BridgeProtocolError(`plate index entry is not a Map: ${v.type}`);
    }
    const m = v.value;
    const hashV = m.get("hash");
    const labelV = m.get("label");
    const valueV = m.get("value");
    if (!hashV || hashV.type !== "bytes" || !labelV || labelV.type !== "string") {
      throw new BridgeProtocolError("plate index entry missing hash/label");
    }
    return {
      hash: hashV.value,
      label: labelV.value,
      value: valueV && valueV.type === "uint" ? valueV.value : null,
    };
  });
  return { totalPlates: totalV.value, livePlates: liveV.value, plates };
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
