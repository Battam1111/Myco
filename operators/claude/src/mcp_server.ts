// MCP server — exposes substrate operations to Claude Code as MCP tools.
//
// This is the L4 M6 operators/<claude> binding per
// L3/PACKAGE_MAP §11. It maps Claude Code's MCP tool-call surface to the
// substrate's M5/M6 wire protocol.
//
// ## Tool surface
//
// 25 tools exposed to Claude Code, grouped by concern:
//
// Gradient lifecycle:
//   `myco_register_axis`, `myco_perturb_axis`, `myco_advance_cycle`,
//   `myco_snapshot`.
// Introspection / handshake:
//   `substrate_info`, `myco_shutdown_substrate`, `myco_current_intent`,
//   `myco_query_recent_nodes`, `myco_query_migration_pending`.
// Immune / integrity:
//   `myco_run_immune_check`, `myco_query_immune_events`,
//   `myco_enumerate_dag_since`.
// Mutation / evolution (P3; v0.9 keyless — no owner-attestation surface):
//   `myco_submit_mutation`, `myco_evolve_schema`.
// Ingestion (P2):
//   `myco_ingest_raw_material`, `myco_perturb_axis_from_raw_material`,
//   `myco_query_raw_material`.
// Reproduction / mortality (P8 / P7):
//   `myco_sprout_child`, `myco_query_self_euthanasia_proposals`.
// Owner objective (P14):
//   `myco_declare_owner_objective` (P14 §3.2 owner-objective declaration).
// (v0.9 owner-key removal: `myco_request_attestation_nonce`, `myco_cosign_dag_tip`,
//  and `myco_attest_l0_revision` were removed with the anchor surface.)
// Perception (substrate self-knowledge):
//   `myco_query_substrate_observatory` (Phase α M24.5 vital signs),
//   `myco_query_substrate_id` (P8 §5.6 self-derived id; v0.9 keyless).
//
// The server lazily spawns the substrate subprocess on the first tool call;
// subsequent calls reuse the same substrate.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import {
  SubstrateClient,
  type SubstrateClientConfig,
} from "./substrate_client.ts";
import type {
  AdvanceReport,
  DagEnumerationReport,
  ImmuneCheckReport,
  ImmuneEventsReport,
  IntentReport,
  MutationResult,
  ObservatorySnapshot,
  RecentDagNode,
  RecentNodesReport,
} from "./protocol/messages.ts";
import { bytesToHex as toHex, hexTo32 } from "./hex.ts";
import type { Value } from "./canonical/canonical_bytes.ts";

/** Build a canonical-bytes Map `Value` from typed entries. Keeps the nested
 *  value type checked as `Value` (vs. a bare object literal, which TS infers too
 *  narrowly and then forces an `as never` cast at the call site). */
function cbMap(entries: [string, Value][]): Value {
  return { type: "map", value: new Map<string, Value>(entries) };
}

/** Byte-equality for two Uint8Arrays (used to match a DAG node by hash). */
function _bytesEq(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

/** Decode a node's canonical-bytes content into HUMAN-READABLE text.
 *
 *  The content of every DAG node is already transmitted in the recent-nodes
 *  response (`RecentDagNode.contentCanonicalBytes`); this decodes that
 *  canonical-bytes Map (reusing the operator's local canonical decode utilities
 *  it already imports for querySubstrateId) and renders per node-type:
 *   - `raw_material:*` → kind + decoded UTF-8 of the "bytes" field + source_uri.
 *   - `forged_understanding:*` → label + decoded "understanding" text + the
 *     source raw_material hashes.
 *   - anything else → a best-effort key/value decode of the top-level Map.
 */
async function renderNodeContentText(node: RecentDagNode): Promise<string> {
  const { decode } = await import("./canonical/renderer.ts");
  const { CanonicalBytes } = await import(
    "./canonical/canonical_bytes.ts"
  );
  const utf8 = new TextDecoder("utf-8", { fatal: false });
  const header = `[cycle ${node.atCycle}] ${node.nodeType}  hash=${toHex(node.hash)}`;

  let decoded: Value;
  try {
    decoded = decode(new CanonicalBytes(node.contentCanonicalBytes));
  } catch (e) {
    return `${header}\n  (content is not decodable canonical-bytes: ${e instanceof Error ? e.message : String(e)}; ${node.contentCanonicalBytes.length} raw bytes)`;
  }
  if (decoded.type !== "map") {
    return `${header}\n  content (non-Map ${decoded.type}): ${_renderScalar(decoded, utf8)}`;
  }
  const m = decoded.value;
  const lines: string[] = [header];

  if (node.nodeType.startsWith("raw_material:")) {
    const kind = m.get("kind");
    const bytes = m.get("bytes");
    const sourceUri = m.get("source_uri");
    lines.push(`  kind: ${kind && kind.type === "string" ? kind.value : "(none)"}`);
    if (bytes && bytes.type === "bytes") {
      lines.push(`  content (${bytes.value.length} bytes):`);
      lines.push(_indentBlock(utf8.decode(bytes.value)));
    } else {
      lines.push("  content: (missing 'bytes' field)");
    }
    if (sourceUri && sourceUri.type === "string") {
      lines.push(`  source_uri: ${sourceUri.value}`);
    }
    return lines.join("\n");
  }

  if (node.nodeType.startsWith("forged_understanding:")) {
    const label = m.get("label");
    const understanding = m.get("understanding");
    const sources = m.get("source_raw_material_hashes");
    const forgedAt = m.get("forged_at_cycle");
    lines.push(`  label: ${label && label.type === "string" ? label.value : "(none)"}`);
    if (forgedAt && forgedAt.type === "uint") {
      lines.push(`  forged_at_cycle: ${forgedAt.value}`);
    }
    if (understanding && understanding.type === "bytes") {
      lines.push(`  understanding (${understanding.value.length} bytes):`);
      lines.push(_indentBlock(utf8.decode(understanding.value)));
    } else {
      lines.push("  understanding: (missing 'understanding' field)");
    }
    if (sources && sources.type === "array") {
      if (sources.value.length === 0) {
        lines.push("  source_raw_material_hashes: (none)");
      } else {
        lines.push(`  source_raw_material_hashes (${sources.value.length}):`);
        for (const s of sources.value) {
          if (s.type === "bytes") lines.push(`    - ${toHex(s.value)}`);
        }
      }
    }
    return lines.join("\n");
  }

  // Best-effort key/value decode for any other node type.
  lines.push("  content (key/value):");
  for (const [k, v] of m) {
    lines.push(`    ${k}: ${_renderScalar(v, utf8)}`);
  }
  return lines.join("\n");
}

/** Whether a decoded string "looks like" clean text worth previewing: no C0
 *  control chars other than tab (0x09) / newline (0x0a) / CR (0x0d), and no
 *  U+FFFD replacement char (which `TextDecoder({fatal:false})` inserts for
 *  invalid UTF-8 — its presence means the bytes were not valid text). Pure
 *  char-code scan; no regex with non-ASCII literals. */
function _looksLikeText(s: string): boolean {
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c === 0xfffd) return false; // replacement char → not valid UTF-8 text
    if (c < 0x20 && c !== 0x09 && c !== 0x0a && c !== 0x0d) return false;
  }
  return true;
}

/** Compact one-line render of a canonical-bytes scalar/aggregate for the
 *  best-effort key/value path. Bytes are shown as hex (with a UTF-8 preview when
 *  they look like text); nested aggregates are summarized by size. */
function _renderScalar(v: Value, utf8: InstanceType<typeof TextDecoder>): string {
  switch (v.type) {
    case "null":
      return "null";
    case "bool":
      return String(v.value);
    case "int":
    case "uint":
    case "timestamp":
      return String(v.value);
    case "string":
      return JSON.stringify(v.value);
    case "bytes":
    case "hash": {
      const hex = toHex(v.value);
      const preview = utf8.decode(v.value);
      const printable = _looksLikeText(preview);
      return printable && preview.length > 0
        ? `0x${hex.substring(0, 32)}${hex.length > 32 ? "…" : ""} (utf8: ${JSON.stringify(preview.length > 120 ? preview.substring(0, 120) + "…" : preview)})`
        : `0x${hex.substring(0, 64)}${hex.length > 64 ? `…<${v.value.length} bytes>` : ""}`;
    }
    case "array":
      return `[array of ${v.value.length}]`;
    case "map":
      return `{map of ${v.value.size}}`;
  }
}

/** Indent every line of a text block by 4 spaces (for nested content display). */
function _indentBlock(text: string): string {
  return text
    .split("\n")
    .map((line) => `    ${line}`)
    .join("\n");
}

/** Configuration for the MCP server. */
export interface McpServerConfig {
  substrate?: SubstrateClientConfig;
}

/** Format an AdvanceReport as a readable summary string. */
function formatAdvance(report: AdvanceReport): string {
  const parts: string[] = [];
  if (report.cycleNumber !== null) {
    parts.push(`cycle=${report.cycleNumber}`);
  }
  parts.push(`fruited_axes=[${report.fruitedAxes.join(",")}]`);
  parts.push(`sporocarps=${report.sporocarps.length}`);
  for (const sp of report.sporocarps) {
    parts.push(
      `  - ${sp.sporocarpType} on ${sp.axisName} (value=${sp.fruitingValue}, at_cycle=${sp.atCycle}, hash=${toHex(sp.hash).substring(0, 16)}…)`,
    );
  }
  return parts.join("\n");
}

function formatIntent(report: IntentReport): string {
  const lines: string[] = [];
  lines.push(
    `cold_start=${report.coldStart}  neighborhood=${report.neighborhoodNodeCount} nodes  full_set=${report.fullSetNodeCount} nodes  clusters=${report.clusterCount}`,
  );
  for (const cluster of report.clusters) {
    const hashPreviews = cluster.nodeHashes
      .slice(0, 3)
      .map((h) => toHex(h).substring(0, 12) + "…")
      .join(", ");
    const more =
      cluster.nodeHashes.length > 3
        ? ` … (+${cluster.nodeHashes.length - 3} more)`
        : "";
    lines.push(
      `  cluster #${cluster.clusterId}: ${cluster.nodeCount} nodes [${hashPreviews}${more}]`,
    );
  }
  return lines.join("\n");
}

function formatImmuneCheck(report: ImmuneCheckReport): string {
  const lines: string[] = [];
  lines.push(
    `total_checks=${report.totalChecks}  failed_checks=${report.failedChecks}  immune_events_emitted=${report.immuneEventsEmitted}`,
  );
  for (const check of report.checks) {
    const marker = check.passed ? "✓" : "✗";
    lines.push(`  ${marker} ${check.checkId}: ${check.evidence}`);
  }
  return lines.join("\n");
}

function formatImmuneEvents(report: ImmuneEventsReport): string {
  const lines: string[] = [];
  lines.push(
    `total_immune_count=${report.totalImmuneCount}  returned=${report.returnedCount}`,
  );
  for (const ev of report.events) {
    // Truncate hash for readability.
    lines.push(
      `  [${ev.atCycle}] ${ev.nodeType}  hash=${toHex(ev.hash).substring(0, 16)}…`,
    );
  }
  if (report.totalImmuneCount === 0n) {
    lines.push("  (no immune events recorded)");
  }
  return lines.join("\n");
}

function formatMutation(result: MutationResult): string {
  const lines: string[] = [];
  lines.push(`classification=${result.classification}  accepted=${result.accepted}`);
  if (!result.accepted) {
    lines.push(`rejection_reason: ${result.rejectionReason}`);
  } else if (result.dagNodeHash) {
    lines.push(`mutation_type=${result.mutationType}`);
    lines.push(`dag_node_hash=${toHex(result.dagNodeHash).substring(0, 24)}…`);
  }
  return lines.join("\n");
}

function formatRecentNodes(report: RecentNodesReport): string {
  const lines: string[] = [];
  const tip = report.dagTip ? toHex(report.dagTip).substring(0, 16) : "(empty)";
  lines.push(
    `total_dag_size=${report.totalDagSize}  returned=${report.returnedCount}  tip=${tip}…`,
  );
  for (const node of report.nodes) {
    lines.push(
      `  [${node.atCycle}] ${node.nodeType}  hash=${toHex(node.hash).substring(0, 16)}…  parents=${node.parentHashes.length}`,
    );
  }
  return lines.join("\n");
}

function formatEnumeration(
  report: DagEnumerationReport,
  verifyErrors: string[],
): string {
  const lines: string[] = [];
  const currentTip = report.currentTip
    ? toHex(report.currentTip).substring(0, 16)
    : "(empty)";
  const prevTip = report.prevTip
    ? toHex(report.prevTip).substring(0, 16)
    : "(genesis)";
  lines.push(
    `enumerated_count=${report.enumeratedCount}  total_dag_size=${report.totalDagSize}  current_tip=${currentTip}…  since=${prevTip}…`,
  );
  if (verifyErrors.length === 0) {
    lines.push(`✓ chain verification passed (all ${report.nodes.length} nodes hash-consistent)`);
  } else {
    lines.push(`✗ chain verification FAILED (${verifyErrors.length} errors):`);
    for (const err of verifyErrors.slice(0, 5)) {
      lines.push(`  - ${err}`);
    }
    if (verifyErrors.length > 5) {
      lines.push(`  … (+${verifyErrors.length - 5} more errors)`);
    }
  }
  for (const node of report.nodes.slice(0, 10)) {
    lines.push(
      `  [${node.atCycle}] ${node.nodeType}  hash=${toHex(node.hash).substring(0, 16)}…  parents=${node.parentHashes.length}`,
    );
  }
  if (report.nodes.length > 10) {
    lines.push(`  … (+${report.nodes.length - 10} more nodes)`);
  }
  return lines.join("\n");
}

/** Format the Phase α / M24.5 observatory snapshot — one line per present
 *  cultivar vital sign (signals #1-10 + the C37 doctrine-burst detector + the
 *  bet-weakening quorum). Signals the substrate omits at the current
 *  format_version are simply absent from the output. */
function formatObservatory(obs: ObservatorySnapshot): string {
  const lines: string[] = [];
  lines.push(
    `observatory_format_version=${obs.formatVersion}  captured_at_unix_ns=${obs.capturedAtUnixNs}`,
  );
  if (obs.signal1) {
    lines.push(
      `  #1 persistence_budget: dag_nodes=${obs.signal1.dagNodeCount} edges=${obs.signal1.dagEdgeCount} content_bytes=${obs.signal1.dagTotalContentBytes} cycle=${obs.signal1.manifestCycleCounter}`,
    );
  }
  if (obs.signal2) {
    lines.push(
      `  #2 evolution_rate: rate=${obs.signal2.rate} (evolution_events=${obs.signal2.evolutionEventCount} axis_registers=${obs.signal2.axisRegisterCount})`,
    );
  }
  if (obs.signal3) {
    lines.push(
      `  #3 read_pattern_diversity: distinct_perturbed_axes=${obs.signal3.distinctPerturbedAxesCount}`,
    );
  }
  if (obs.signal4) {
    lines.push(
      `  #4 federation_health: reachable_peers=${obs.signal4.signal4bReachablePeerCount} forks=${obs.signal4.signal4aCumulativeForkCount} events_received=${obs.signal4.eventsReceivedFromPeers}`,
    );
  }
  if (obs.signal5) {
    lines.push(`  #5 time_trends: present (raw, ${obs.signal5.raw.size} keys)`);
  }
  if (obs.signal6) {
    lines.push(
      `  #6 read_window_position: ratio=${obs.signal6.ratio} (substrate_total_bytes=${obs.signal6.substrateTotalBytes} window_bytes=${obs.signal6.operatorAttestedContextWindowBytes})`,
    );
  }
  if (obs.signal7) {
    lines.push(
      `  #7 compute_per_cycle: current_ns=${obs.signal7.currentCycleNs} rolling_mean_ns=${obs.signal7.rollingMeanNs}`,
    );
  }
  if (obs.signal8) {
    lines.push(
      `  #8 network_per_cycle: current_bytes=${obs.signal8.currentCycleBytes} rolling_mean_bytes=${obs.signal8.rollingMeanBytes}`,
    );
  }
  if (obs.signal9) {
    lines.push(
      `  #9 storage_per_cycle: current_bytes=${obs.signal9.currentCycleBytes} rolling_mean_bytes=${obs.signal9.rollingMeanBytes}`,
    );
  }
  if (obs.signal10) {
    lines.push(
      `  #10 composite_health: score=${obs.signal10.compositeHealthScore} (composite_format_version=${obs.signal10.compositeFormatVersion}${obs.signal10.weightsMethod ? `, weights_method=${obs.signal10.weightsMethod}` : ""})`,
    );
  }
  if (obs.doctrineRevisionBurstStatus) {
    lines.push(
      `  doctrine_revision_burst (C37): present (raw, ${obs.doctrineRevisionBurstStatus.raw.size} keys)`,
    );
  }
  if (obs.betWeakeningQuorum) {
    lines.push(
      `  bet_weakening_quorum: present (raw, ${obs.betWeakeningQuorum.raw.size} keys)`,
    );
  }
  if (obs.saturationStatus) {
    lines.push(
      `  saturation_status (P11.c): present (raw, ${obs.saturationStatus.raw.size} keys)`,
    );
  }
  if (obs.char07) {
    lines.push(
      "  char07 同体共命: honest_disagreement + capability_asymmetry + flourishing (raw)",
    );
  }
  return lines.join("\n");
}

const TOOL_DEFINITIONS = [
  {
    name: "myco_register_axis",
    description:
      "Register a new gradient axis on the substrate. Axes are operator-defined channels through which deltas accumulate; when an axis crosses its fruiting threshold, the substrate emits a sporocarp. `axis_class` is 'appetite' (grows toward threshold; resets after fruit) or 'decay' (decays toward zero each cycle; mortality-signal pattern).",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", description: "Stable axis identifier" },
        axis_class: {
          type: "string",
          enum: ["appetite", "decay"],
          description: "APPETITE (default) or DECAY (mortality-signal)",
        },
        fruiting_threshold: {
          type: "number",
          description:
            "Gradient value at which a sporocarp is emitted (crossing direction depends on axis_class)",
        },
        initial_value: {
          type: "number",
          description: "Gradient value at genesis (default 0 for appetite, 1 for decay)",
        },
        decay_rate_per_cycle: {
          type: "number",
          description:
            "Multiplicative per-cycle factor (only used for DECAY; e.g. 0.9 = 10%/cycle)",
        },
        is_mortality_signal: {
          type: "boolean",
          description: "Whether this axis is the substrate's mortality signal (CI-protected per L1/HARD_RULES F7)",
        },
        update_rule_kind: {
          type: "string",
          enum: ["noop", "decay"],
          description: "Update rule (noop = no substrate-internal update; decay = multiplicative decay)",
        },
      },
      required: [
        "name",
        "axis_class",
        "fruiting_threshold",
        "initial_value",
        "decay_rate_per_cycle",
        "is_mortality_signal",
        "update_rule_kind",
      ],
    },
  },
  {
    name: "myco_perturb_axis",
    description:
      "Apply a delta (positive or negative) to a registered axis. This is the operator-side input channel into the substrate's gradient configuration. Effects materialize in the gradient on the NEXT myco_advance_cycle call.",
    inputSchema: {
      type: "object",
      properties: {
        axis_name: { type: "string" },
        delta: {
          type: "number",
          description:
            "Amount to add to the axis's gradient value (negative subtracts)",
        },
      },
      required: ["axis_name", "delta"],
    },
  },
  {
    name: "myco_advance_cycle",
    description:
      "Run one substrate metabolic cycle. Triggers gradient advance, fruiting checks, and sporocarp emission. Returns the list of fruited axes and the sporocarps emitted (each with type, canonical bytes, and content hash).",
    inputSchema: {
      type: "object",
      properties: {
        current_cycle: {
          type: "integer",
          description: "Informational cycle counter (substrate has its own authoritative counter)",
          minimum: 0,
        },
      },
      required: ["current_cycle"],
    },
  },
  {
    name: "myco_snapshot",
    description:
      "Read current values of all registered gradient axes. Useful for inspection between cycles.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "substrate_info",
    description:
      "Report substrate version + Python kernel/tropism version + Python interpreter version. Useful for verifying which substrate stack is live in this session.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "myco_shutdown_substrate",
    description:
      "Gracefully shut down the substrate. After this call, no more substrate operations will work in this session.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "myco_current_intent",
    description:
      "Compute the substrate's current 'intent' — its self-knowledge derived from the causal DAG of sporocarps. Runs cluster_C over the neighborhood + ancestors+descendants of the DAG tip. Returns clusters grouping causally-related events. Captures what the substrate has been 'thinking about' lately.",
    inputSchema: {
      type: "object",
      properties: {
        radius_cycles: {
          type: "integer",
          description:
            "Neighborhood radius in metabolic cycles (default 10). Wider radius = more historical context",
          minimum: 0,
        },
      },
      required: [],
    },
  },
  {
    name: "myco_query_recent_nodes",
    description:
      "List the last N DAG nodes (sporocarps) in the substrate's causal history. Useful for inspecting what the substrate has DONE — its observable behavior over recent cycles.",
    inputSchema: {
      type: "object",
      properties: {
        count: {
          type: "integer",
          description: "Number of most-recent DAG nodes to return (default 50)",
          minimum: 1,
          maximum: 1000,
        },
      },
      required: [],
    },
  },
  // **v0.9 owner-key removal**: the `myco_request_attestation_nonce` tool was
  // removed — the substrate no longer issues anchor-surface attestation nonces
  // (the M13 nonce-issuance handler was deleted with the anchor surface).
  {
    name: "myco_run_immune_check",
    description:
      "Trigger an ad-hoc immune verification scan. The substrate runs comprehensive integrity checks (substrate_id well-formedness, DAG hash-chain integrity, cycle-counter monotonicity, canonical-bytes drift detection, orphan-node detection). For each failed check, the substrate emits a C9 cold_resume_invariant_failure immune sporocarp (visible via myco_query_immune_events). Returns a per-check report.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "myco_query_immune_events",
    description:
      "List recent immune events recorded by the substrate's defensive system: rejected untyped mutations (C14), invalid CI attestations (C5), pubkey mismatches at handshake (C2), and detected DAG tampering (C7). Each event is a DAG node with node_type starting with 'immune:'. Useful for auditing the substrate's defensive history.",
    inputSchema: {
      type: "object",
      properties: {
        count: {
          type: "integer",
          description: "Number of most-recent immune events to return (default 50)",
          minimum: 1,
          maximum: 1000,
        },
      },
      required: [],
    },
  },
  {
    name: "myco_query_migration_pending",
    description:
      "P03 §10.4 (Resumable Evolution): Report whether a two-phase schema migration is currently in flight. When an operator submits a schema_evolution mutation with migration_mode=true, the substrate builds a CANDIDATE schema and validates it alongside the active schema for a window of metabolic cycles before committing (instead of the default single-cycle apply). This tool reports {pending, op, started_at_cycle, window, current_cycle} — pending=true plus how far through the dual-validation window the migration has progressed. Survives substrate restart (the candidate is resumed from the causal DAG).",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "myco_sprout_child",
    description:
      "P8 永恒繁衍 (Eternal Reproduction): Sprout a child substrate from the parent's spore-schema (L0/cards/P08 §5.2). **A child spawn is a CI-class doctrine event (P08 §3.5 / §5.1), NOT a daily-mode mutation.** This tool assembles the child's spore-schema from the parent's current gradient, stamps a local wall-clock timestamp + a fresh random nonce, and builds a myco-spawn-cosign-v1 envelope. v0.9 keyless: there is no owner key and no signature — the substrate decodes the envelope STRUCTURE and verifies the I7(a) static-schema binding + the parent replay-guard + the §16.B rate throttle BEFORE creating anything; a malformed/replayed spawn is refused with C68 (the 'daily-mode spawn = doctrine collapse' signal). On success the child's substrate_id is minted deterministically as blake3(parent_id, spore_schema_hash, child_genesis_ts) [§5.6], the child DAG is built (with a birth_closure_pending marker so the child runs its own I3 self-check on first boot), and the parent emits genesis_attested:{child_prefix} (the I7-closure record). The parent's causal DAG is NOT transferred. After sprout, spawn a separate substrate process pointing at child_state_dir via MYCO_STATE_DIR. Rejects if the target already contains a dag.cb/manifest.cb.",
    inputSchema: {
      type: "object",
      properties: {
        child_state_dir: {
          type: "string",
          description:
            "Absolute path for the child substrate's state_dir. Must not contain an existing dag.cb/manifest.cb. The substrate will create the directory if needed.",
        },
        depth_override: {
          type: "boolean",
          description:
            "Optional (default false). When true, the spawn-cosign envelope carries a depth_override permitting this spawn to exceed the §16.A reproduction_lineage_depth_max (forkbomb depth cap) for THIS child. Use only deliberately: it is recorded as a depth_override_exercised DAG event.",
        },
      },
      required: ["child_state_dir"],
    },
  },
  {
    name: "myco_query_self_euthanasia_proposals",
    description:
      "P7 必朽 (Endogenous-pair Mortality): List the substrate's pending `self_euthanasia_proposal:*` DAG nodes. These are emitted automatically when a mortality_signal axis fruits (crosses its decay threshold): the substrate proposing its own end. v0.9 keyless: executing a proposal (myco_accept_self_euthanasia_proposal) references a real proposal_hash and is gated at the CI human-in-the-loop level, not by an owner co-signature (the owner key was removed). M19-MV: proposals are informational. Each entry includes the axis_name, fruiting_value, at_cycle, and triggering_sporocarp_hash.",
    inputSchema: {
      type: "object",
      properties: {
        count: {
          type: "integer",
          description: "Number of most-recent proposals to return (default 50).",
          minimum: 1,
          maximum: 1000,
        },
      },
      required: [],
    },
  },
  {
    name: "myco_evolve_schema",
    description:
      "P3 永恒进化 (Eternal Evolution): Submit an owner-attested schema mutation that actually CHANGES the substrate's gradient schema. Unlike prior CI mutations (M10–M15) which were recorded but not applied, this triggers real schema modification with snapshot-rollback semantics. On success: substrate emits evolution_succeeded:{op} DAG event. On failure (invariant violation, missing axis, etc.): rollback + evolution_failed:{op} event. Supported ops: modify_axis_threshold (change an axis's fruiting threshold), add_axis_to_gradient (register a new axis through the CI attestation gate).",
    inputSchema: {
      type: "object",
      properties: {
        op: {
          type: "string",
          enum: ["modify_axis_threshold", "add_axis_to_gradient"],
          description: "The schema-diff operation to apply.",
        },
        axis_name: {
          type: "string",
          description: "Target axis name.",
        },
        new_threshold: {
          type: "number",
          description: "(modify_axis_threshold) The new fruiting threshold.",
        },
        axis_class: {
          type: "string",
          enum: ["appetite", "decay"],
          description: "(add_axis_to_gradient) APPETITE or DECAY.",
        },
        fruiting_threshold: {
          type: "number",
          description: "(add_axis_to_gradient) Fruiting threshold.",
        },
        initial_value: {
          type: "number",
          description: "(add_axis_to_gradient) Initial gradient value.",
        },
        decay_rate_per_cycle: {
          type: "number",
          description: "(add_axis_to_gradient) Per-cycle decay rate.",
        },
        is_mortality_signal: {
          type: "boolean",
          description: "(add_axis_to_gradient) Whether this is the mortality signal axis.",
        },
        update_rule_kind: {
          type: "string",
          enum: ["noop", "decay"],
          description: "(add_axis_to_gradient) Update rule.",
        },
        migration_mode: {
          type: "boolean",
          description:
            "(P03 §10.4) When true, take the MULTI-CYCLE TWO-PHASE migration path: the substrate builds a candidate schema and validates it alongside the active schema for a window of cycles before committing, instead of the default single-cycle apply. The active schema is never at risk during validation. Poll myco_query_migration_pending to watch progress. Omitted/false = single-cycle apply (default).",
        },
      },
      required: ["op", "axis_name"],
    },
  },
  {
    name: "myco_ingest_raw_material",
    description:
      "P2 永恒吞噬 (Eternal Ingestion): Ingest a raw-material payload into the substrate. The substrate stores it as a `raw_material:{kind}` DAG node — anything the agent can present becomes first-class substrate content (L0 P2 'no filter on intake'). Subsequent perturbations of gradient axes can be causally linked to this material via myco_perturb_axis_from_raw_material. Max 1 MiB per call. Returns: dag_node_hash (the raw_material node id), current_tip, total_dag_size.",
    inputSchema: {
      type: "object",
      properties: {
        content_kind: {
          type: "string",
          description:
            'The kind of raw material: "text" (free text), "file" (file contents), "conversation" (message in dialogue), "url" (web fetch), "llm_response" (output from another LLM), or any custom kind tag.',
        },
        content: {
          type: "string",
          description:
            "The raw material payload (UTF-8 text). For binary content, base64-encode and use content_kind='binary:<original_kind>'.",
        },
        source_uri: {
          type: "string",
          description:
            "Optional provenance hint (file path, URL, message id, etc.). Stored alongside the content in the DAG node.",
        },
      },
      required: ["content_kind", "content"],
    },
  },
  {
    name: "myco_perturb_axis_from_raw_material",
    description:
      "P2 永恒吞噬 + P6 永恒因果 (Eternal Ingestion + Causality): Perturb a gradient axis with explicit causal linkage to a previously-ingested raw_material node. The substrate records a `perturb_from_raw:{axis}` DAG node whose parents are BOTH the prior DAG tip AND the referenced raw_material — making the gradient change traceable back through causal history to its environmental source. Use this instead of myco_perturb_axis when the perturbation has a specific raw-material origin you want preserved.",
    inputSchema: {
      type: "object",
      properties: {
        axis_name: {
          type: "string",
          description: "Name of the previously-registered axis to perturb.",
        },
        delta: {
          type: "number",
          description:
            "Amount to perturb the axis by (negative subtracts). Effects materialize on next myco_advance_cycle.",
        },
        raw_material_hash_hex: {
          type: "string",
          description:
            "64-character hex string (32-byte hash) of the raw_material DAG node from a prior myco_ingest_raw_material call. The hash must reference a raw_material:* node, otherwise substrate rejects.",
        },
      },
      required: ["axis_name", "delta", "raw_material_hash_hex"],
    },
  },
  {
    name: "myco_query_raw_material",
    description:
      "Query the substrate's recently-ingested raw material (DAG nodes with node_type starting `raw_material:`). Useful for auditing what the substrate has eaten lately, or finding hashes to pass to myco_perturb_axis_from_raw_material. Optional count parameter (default 50, max 1000).",
    inputSchema: {
      type: "object",
      properties: {
        count: {
          type: "integer",
          description: "Number of most-recent raw_material nodes to return (default 50).",
          minimum: 1,
          maximum: 1000,
        },
        kind_filter: {
          type: "string",
          description:
            'Optional sub-filter: e.g. "text", "file", "conversation". Becomes prefix "raw_material:<kind_filter>". Omit to return all raw_material kinds.',
        },
      },
      required: [],
    },
  },
  {
    name: "myco_forge_understanding",
    description:
      "P2 永恒吞噬 + P6 永恒因果 (the 'use-forges' forging loop): Deposit the agent's DIGESTED understanding back into the substrate as a `forged_understanding:{label}` DAG node. Where myco_ingest_raw_material stores UNDIGESTED intake, this stores what the agent FORGED out of it — prose/knowledge it metabolized. The new node is causally parented by BOTH the prior DAG tip AND each source raw_material node it cites, so the digested understanding stays traceable through causal history to its undigested sources. General — NOT tied to a gradient axis. Max 512 KiB on the understanding text. Returns: dag_node_hash (the forged_understanding node id), current_tip, total_dag_size.",
    inputSchema: {
      type: "object",
      properties: {
        label: {
          type: "string",
          description:
            "A short tag for this forged understanding (analogous to content_kind for raw_material). Becomes the node_type `forged_understanding:<label>`. E.g. \"synthesis\", \"lesson\", \"summary:auth-flow\".",
        },
        understanding: {
          type: "string",
          description:
            "The digested understanding (UTF-8 prose/knowledge the agent forged). Encoded UTF-8→bytes, max 512 KiB.",
        },
        source_raw_material_hashes: {
          type: "array",
          items: { type: "string" },
          description:
            "Optional list of 64-hex (32-byte) hashes of the raw_material:* DAG nodes this understanding was forged from (from prior myco_ingest_raw_material / myco_query_raw_material calls). Each must reference a raw_material:* node or the substrate rejects. MAY be empty/omitted (a forged understanding need not cite a specific source).",
        },
        value: {
          type: "integer",
          minimum: 0,
          maximum: 100,
          description:
            "OPTIONAL importance you assign this plate (0–100). Recall ranks by it — set higher for understanding worth standing on later, lower for incidental notes. Omit if you have no strong signal.",
        },
        confidence: {
          type: "integer",
          minimum: 0,
          maximum: 100,
          description:
            "OPTIONAL your confidence in this plate (0–100). Lets a future pilot know how much to trust it. Omit if you have no strong signal.",
        },
        supersedes: {
          type: "array",
          items: { type: "string" },
          description:
            "OPTIONAL list of 64-hex hashes of prior forged_understanding:* plates this one CORRECTS or REPLACES (each must reference a forged_understanding:* node). Use when you have re-forged a sharper understanding — it records the supersession edge so the old plate can mature out (P06-clean: the old plate is never edited, just superseded).",
        },
      },
      required: ["label", "understanding"],
    },
  },
  {
    name: "myco_read_node_content",
    description:
      "Read back the HUMAN-READABLE content of a single DAG node by its hash — fetched directly via the substrate (ANY node, not just the recent window). Decodes the node's canonical-bytes content and renders it as text: for raw_material:* → the kind + the decoded UTF-8 of the ingested bytes + source_uri; for forged_understanding:* → the label + the decoded understanding text + the source raw_material hashes; for other node types → a best-effort key/value decode. If the node does not exist in the DAG, says so.",
    inputSchema: {
      type: "object",
      properties: {
        node_hash_hex: {
          type: "string",
          description:
            "64-character hex string (32-byte hash) of the DAG node to read. Obtain from any tool that returns node hashes (myco_query_recent_nodes, myco_query_raw_material, myco_forge_understanding, etc.).",
        },
      },
      required: ["node_hash_hex"],
    },
  },
  {
    name: "myco_recall",
    description:
      "Read your compact \"what I know\" map: every LIVE forged_understanding plate you have crystallized, as (label, importance value, hash), sorted by importance (highest first). Superseded plates (ones you later corrected/replaced via forge's `supersedes`) are excluded — so this is your CURRENT mind, not your history. Read the whole map, judge which plates are relevant to what you are doing now (your OWN judgment — the armor does not rank relevance for you), then read the full content of the ones you want with myco_read_node_content. This is how you stand on your accumulated understanding instead of re-deriving it. Returns: total_plates, live_plates, and the sorted plate list (label / value / hash).",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "myco_orient",
    description:
      "Orient yourself at the START of a session — the first thing a new pilot should do. In one call this surfaces (1) your self-model: the plate labeled \"myco-self-model\" if you have forged one (who this cultivar is, what it is for), and (2) your compact map of every live forged_understanding plate (label / importance / hash), sorted by importance. You inherit a mind, not a blank slate — read this, then read the relevant plates' full content with myco_read_node_content and stand on them. Equivalent to myco_recall plus auto-reading your self-model.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "myco_query_forged_understanding",
    description:
      "Query the substrate's forged_understanding:* DAG nodes (the agent's deposited DIGESTED understandings — the output side of the 'use-forges' forging loop, vs. myco_query_raw_material's undigested intake side). Lists each with metadata: cycle, label, hash, size. Use myco_read_node_content on a hash to read the full understanding text. Optional count parameter (default 50, max 1000).",
    inputSchema: {
      type: "object",
      properties: {
        count: {
          type: "integer",
          description: "Number of most-recent forged_understanding nodes to return (default 50).",
          minimum: 1,
          maximum: 1000,
        },
      },
      required: [],
    },
  },
  {
    name: "myco_enumerate_dag_since",
    description:
      "Enumerate DAG node hashes added since a given prev_tip (or from genesis if omitted), with full per-node metadata so the caller can independently reconstruct the substrate's Merkle chain (L1/HARD_RULES C6 dag_enumeration_unclosed closure). The substrate cannot hide parallel-branch forgery: every node's BLAKE3 hash is recomputed from declared parents+content and compared. On unknown prev_tip the substrate emits a C6 immune sporocarp. Returns: enumerated_count, current_tip, hash-chain verification result, and per-node summaries.",
    inputSchema: {
      type: "object",
      properties: {
        prev_tip_hex: {
          type: "string",
          description:
            "Optional 64-character hex string (32-byte hash) of the prev_tip to enumerate-since. Omit to enumerate from genesis.",
        },
      },
      required: [],
    },
  },
  {
    name: "myco_submit_mutation",
    description:
      "Submit a mutation for the substrate to classify. The substrate classifies via L1/GOVERNANCE rules: daily mutations are auto-accepted; untyped mutations are rejected. Accepted mutations are recorded as DAG nodes (causal history preserved). Rejected mutations trigger immune sporocarp emission (visible via myco_query_immune_events). (v0.9 keyless: the substrate no longer verifies an owner Ed25519 attestation on CI mutations — classification is content + mutation_type based.)",
    inputSchema: {
      type: "object",
      properties: {
        mutation_type: {
          type: "string",
          description:
            'Mutation tag (e.g., "operator_facing_note" for DAILY, "appetite_axis_schema_meta" for CI, "untyped_test" for rejection)',
        },
        content: {
          type: "string",
          description: "Free-form content payload (encoded as UTF-8 bytes)",
        },
        touched_fields: {
          type: "array",
          items: { type: "string" },
          description: "Optional list of SSoT field names touched",
        },
        touched_meta_structures: {
          type: "array",
          items: { type: "string" },
          description:
            "Optional list of meta-structure names touched (e.g. appetite_axis_schema)",
        },
      },
      required: ["mutation_type", "content"],
    },
  },
  // **v0.9 owner-key removal**: the `myco_cosign_dag_tip` (M-anchor-5 §3.2) and
  // `myco_attest_l0_revision` (§3.4) tools were removed — the substrate no
  // longer accepts the `dag_tip_cosign` / `l0_revision_attest` CI mutation types
  // (the owner Ed25519 attestation surface they drove was deleted with the
  // anchor). L0 doctrine sealing is now the keyless BLAKE3 bundle-hash ceremony
  // (operators/claude/ceremonies/) recorded in git, not an on-DAG owner signature.
  {
    name: "myco_declare_owner_objective",
    description:
      "P14 §3.2 / M26.4 F20 (cultivator-objective declaration): declare the cultivator's telos as a sparse weight vector over substrate node_type prefixes. The substrate uses it as the reference centroid for P14.c telos-drift detection (cosine alignment of recent sporocarp activity against the declared objective; sustained low/negative alignment grades up to a C24 telos_drift_critical immune event). Weights SHOULD be non-negative and need not sum to 1 (the substrate normalizes for the cosine). v0.9 keyless: the objective is cultivator-stated CONTENT, classified contract-identity-level by the Python classifier (mutation_type=owner_objective_declaration): there is no owner key and no signature; the trust root is the live human at the CI gate (the doctrine-repo PR review enforced by the BLAKE3 drift gate). On accept, the substrate emits `owner_objective_declared:{objective_id}`. Example weights: [{prefix:\"axis_perturbed:\",weight:0.75},{prefix:\"raw_material:\",weight:0.25}]. An empty weights array is rejected (C5).",
    inputSchema: {
      type: "object",
      properties: {
        objective_id: {
          type: "string",
          description:
            "Stable identifier for this objective declaration (operator-supplied; appears in the emitted owner_objective_declared:{id} event).",
        },
        weights: {
          type: "array",
          minItems: 1,
          items: {
            type: "object",
            properties: {
              prefix: {
                type: "string",
                description:
                  'A node_type prefix the owner values (e.g. "axis_perturbed:", "raw_material:", "sporocarp:").',
              },
              weight: {
                type: "number",
                description:
                  "Non-negative weight for this prefix. Relative magnitude is what matters (the substrate normalizes for the cosine).",
              },
            },
            required: ["prefix", "weight"],
          },
          description:
            'The sparse weight vector. Must contain at least one entry (an empty array is rejected by the substrate with C5). Example: [{"prefix":"axis_perturbed:","weight":0.75},{"prefix":"raw_material:","weight":0.25}].',
        },
        declared_at_cycle: {
          type: "integer",
          minimum: 0,
          description:
            "Cycle at which this objective is declared (anchors the audit). Default 0.",
        },
      },
      required: ["objective_id", "weights"],
    },
  },
  {
    name: "myco_query_substrate_observatory",
    description:
      "PERCEPTION (Phase α / M24.5 observatory snapshot): expose ALL cultivar vital signs from inside the substrate so Claude can read its own metabolic state. Returns the Living Bets signals #1-10 — #1 persistence budget (DAG size + cycle counter), #2 evolution rate, #3 read-pattern diversity, #4 federation health, #5 time trends, #6 read-window-relative position (iff a context-window is attested), #7/#8/#9 compute/network/storage cost per cycle, #10 composite health score — plus the C37 doctrine-revision-burst detector and the bet_weakening_quorum (the composite L0/cards/LB_living_bets falsifiability counter). Signals the substrate omits at the current observatory_format_version are absent from the output. Read-only.",
    inputSchema: {
      type: "object",
      properties: {
        operator_attested_context_window_bytes: {
          type: "integer",
          minimum: 0,
          description:
            "Optional. When supplied, the substrate computes signal #6 (read-window-relative position = substrate_total_bytes / this window); omit to leave signal #6 out of the snapshot.",
        },
      },
      required: [],
    },
  },
  {
    name: "myco_query_substrate_id",
    description:
      "PERCEPTION (P8 §5.6): report this substrate's immutable self-derived substrate_id, the deterministic 32-byte hash established at genesis (P01c). This is the substrate knowing its own identity; the id binds spawn-cosign envelopes / federation FED_HELLO / DAG tips to THIS specific substrate, which is what makes cross-substrate replay attacks detectable. v0.9 keyless: the id is self-derived, not owner-minted. Read-only (inspects the genesis_event DAG node).",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
];

/** McpServer wraps a Server + lazy SubstrateClient. */
export class McpServer {
  private server: Server;
  private substrateConfig: SubstrateClientConfig;
  private substrate: SubstrateClient | null = null;
  private substrateSpawnPromise: Promise<SubstrateClient> | null = null;

  constructor(config: McpServerConfig = {}) {
    this.substrateConfig = config.substrate ?? {};
    this.server = new Server(
      {
        name: "myco-operator-claude-code",
        version: "0.9.0-alpha.2",
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );
    this._registerHandlers();
  }

  private _registerHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return { tools: TOOL_DEFINITIONS };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = (request.params.arguments ?? {}) as Record<string, unknown>;

      try {
        return await this._dispatchTool(toolName, args);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        return {
          content: [
            {
              type: "text" as const,
              text: `ERROR (${toolName}): ${message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private async _ensureSubstrate(): Promise<SubstrateClient> {
    if (this.substrate) return this.substrate;
    if (this.substrateSpawnPromise) return this.substrateSpawnPromise;
    this.substrateSpawnPromise = SubstrateClient.spawn(this.substrateConfig);
    this.substrate = await this.substrateSpawnPromise;
    return this.substrate;
  }

  private async _dispatchTool(
    name: string,
    args: Record<string, unknown>,
  ): Promise<{
    content: { type: "text"; text: string }[];
    isError?: boolean;
  }> {
    switch (name) {
      case "myco_register_axis": {
        const sub = await this._ensureSubstrate();
        await sub.registerAxis({
          name: String(args.name),
          axisClass: args.axis_class as "appetite" | "decay",
          fruitingThreshold: Number(args.fruiting_threshold),
          initialValue: Number(args.initial_value),
          decayRatePerCycle: Number(args.decay_rate_per_cycle),
          isMortalitySignal: Boolean(args.is_mortality_signal),
          updateRuleKind: args.update_rule_kind as "noop" | "decay",
        });
        return {
          content: [
            {
              type: "text" as const,
              text: `Registered axis "${args.name}" (class=${args.axis_class}, threshold=${args.fruiting_threshold})`,
            },
          ],
        };
      }
      case "myco_perturb_axis": {
        const sub = await this._ensureSubstrate();
        await sub.perturb(String(args.axis_name), Number(args.delta));
        return {
          content: [
            {
              type: "text" as const,
              text: `Perturbed "${args.axis_name}" by ${args.delta}`,
            },
          ],
        };
      }
      case "myco_advance_cycle": {
        const sub = await this._ensureSubstrate();
        const report = await sub.advance(BigInt(Number(args.current_cycle)));
        return {
          content: [
            {
              type: "text" as const,
              text: formatAdvance(report),
            },
          ],
        };
      }
      case "myco_snapshot": {
        const sub = await this._ensureSubstrate();
        const snap = await sub.snapshot();
        const lines = Array.from(snap.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([k, v]) => `${k} = ${v}`);
        return {
          content: [
            {
              type: "text" as const,
              text:
                snap.size === 0
                  ? "(no axes registered)"
                  : lines.join("\n"),
            },
          ],
        };
      }
      case "substrate_info": {
        const sub = await this._ensureSubstrate();
        const ack = sub.helloAck;
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `substrate_version: ${ack.substrateVersion || "(direct python)"}`,
                `kernel_tropism_version: ${ack.kernelTropismVersion}`,
                `python_version: ${ack.pythonVersion}`,
              ].join("\n"),
            },
          ],
        };
      }
      case "myco_shutdown_substrate": {
        if (!this.substrate) {
          return {
            content: [
              { type: "text" as const, text: "Substrate not yet spawned." },
            ],
          };
        }
        await this.substrate.shutdown();
        this.substrate = null;
        this.substrateSpawnPromise = null;
        return {
          content: [
            { type: "text" as const, text: "Substrate shut down gracefully." },
          ],
        };
      }
      case "myco_current_intent": {
        const sub = await this._ensureSubstrate();
        const radius =
          args.radius_cycles !== undefined
            ? BigInt(Number(args.radius_cycles))
            : 10n;
        const report = await sub.currentIntent({ radiusCycles: radius });
        return {
          content: [{ type: "text" as const, text: formatIntent(report) }],
        };
      }
      case "myco_query_recent_nodes": {
        const sub = await this._ensureSubstrate();
        const count =
          args.count !== undefined ? BigInt(Number(args.count)) : 50n;
        const report = await sub.queryRecentNodes(count);
        return {
          content: [
            { type: "text" as const, text: formatRecentNodes(report) },
          ],
        };
      }
      case "myco_run_immune_check": {
        const sub = await this._ensureSubstrate();
        const report = await sub.runImmuneCheck();
        return {
          content: [
            { type: "text" as const, text: formatImmuneCheck(report) },
          ],
          isError: report.failedChecks > 0n,
        };
      }
      case "myco_query_immune_events": {
        const sub = await this._ensureSubstrate();
        const count = args.count !== undefined ? BigInt(Number(args.count)) : 50n;
        const report = await sub.queryImmuneEvents(count);
        return {
          content: [
            { type: "text" as const, text: formatImmuneEvents(report) },
          ],
        };
      }
      case "myco_query_migration_pending": {
        const sub = await this._ensureSubstrate();
        const report = await sub.queryMigrationPending();
        const lines: string[] = [];
        if (!report.pending) {
          lines.push("no two-phase schema migration in flight");
          lines.push(`current_cycle=${report.currentCycle}`);
        } else {
          const elapsed = report.currentCycle - report.startedAtCycle;
          lines.push(`🔀 migration PENDING: op=${report.op}`);
          lines.push(
            `  started_at_cycle=${report.startedAtCycle}  window=${report.window}  current_cycle=${report.currentCycle}`,
          );
          lines.push(
            `  dual-validation progress: ${elapsed}/${report.window} cycles ` +
              `(${elapsed >= report.window ? "window complete — commits next equivalent cycle" : "validating"})`,
          );
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
        };
      }
      case "myco_sprout_child": {
        const sub = await this._ensureSubstrate();
        const childStateDir = String(args.child_state_dir);
        const depthOverride = Boolean(args.depth_override);

        // **P08 §3.5 / §5.1** (KEYLESS v0.9) — a child spawn is still a
        // CI-class doctrine event: `sproutChild` builds the required
        // myco-spawn-cosign-v1 envelope (parent replay-guard + I7(a)
        // spore-schema binding + §16.B anchor-clock throttle), which the
        // substrate decodes + checks before minting the child. The owner
        // Ed25519 co-signature gate was removed with the anchor surface, so no
        // operator identity is loaded.
        //
        // Assemble a well-formed 7-field spore-schema (L1/SCHEMA §3.1). The
        // gradient-derived fields summarise the parent's observed axes; the
        // substrate validates the SHAPE + bound hash (I7(a)) and rebuilds the
        // child's actual gradient from its own internal query.
        const { buildSporeSchemaCanonicalBytes } = await import(
          "./protocol/messages.ts"
        );
        const obs = await sub.querySubstrateObservatory();
        const parentId = await sub.querySubstrateId();
        const axisRegisterCount = obs.signal2?.axisRegisterCount ?? 0n;
        const immuneCount = await sub.queryImmuneEvents(50n).then(
          (r) => BigInt(r.events.length),
          () => 0n,
        );
        const sporeSchemaCanonicalBytes = buildSporeSchemaCanonicalBytes({
          schemaDefinitions: cbMap([
            ["parent_substrate_id", { type: "bytes", value: parentId }],
            ["axis_register_count", { type: "uint", value: axisRegisterCount }],
          ]),
          canonicalBytesSerializerSpec: {
            type: "string",
            value: "myco-canonical-bytes-v1",
          },
          sporocarpTypeTree: {
            type: "string",
            value: "myco-sporocarp-tree-v1",
          },
          classifierDimensionTable: {
            type: "string",
            value: "myco-classifier-i2-v1",
          },
          initialAppetiteAxisSchema: cbMap([
            ["axis_register_count", { type: "uint", value: axisRegisterCount }],
          ]),
          // v0.9 keyless: `anchor_surface_config` is a vestigial spore-schema
          // descriptor field that formerly carried the anchor/owner pubkey.
          // The anchor surface + owner key are gone, but the field NAME is a
          // retained WIRE CONTRACT: I7(a) requires all 7 named spore-schema
          // fields present and blake3(whole bytes) to match the envelope's
          // spore_schema_hash (the substrate validates the 7-field shape by
          // name; the parity vectors pin it). It carries a stable 32-zero-byte
          // marker — no key is encoded. Renaming/removing it would need a
          // coordinated substrate change, so it stays keyless-by-content.
          anchorSurfaceConfig: {
            type: "bytes",
            value: new Uint8Array(32),
          },
          parentImmuneSignalSummary: cbMap([
            ["unresolved_count", { type: "uint", value: immuneCount }],
          ]),
        });

        const result = await sub.sproutChild({
          childStateDir,
          sporeSchemaCanonicalBytes,
          depthOverride,
        });
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `🍄 Child substrate sprouted at ${result.childStateDir}`,
                `child_substrate_id = ${toHex(result.childSubstrateId)} (deterministically minted)`,
                `inherited_axis_count = ${result.childAxisCount}`,
                `spore_emission_hash = ${toHex(result.sporeEmissionHash).substring(0, 24)}…`,
                `genesis_attested_hash = ${toHex(result.genesisAttestedHash).substring(0, 24)}… (I7-closure record in parent DAG)`,
                depthOverride ? `depth_override = EXERCISED` : `depth_override = no`,
                `(spawn a separate substrate at this path via MYCO_STATE_DIR to bring the child to life; it will run its own I3 self-check on first boot)`,
              ].join("\n"),
            },
          ],
        };
      }
      case "myco_query_self_euthanasia_proposals": {
        const sub = await this._ensureSubstrate();
        const count = args.count !== undefined ? BigInt(Number(args.count)) : 50n;
        const report = await sub.queryRecentNodes(count, "self_euthanasia_proposal:");
        const lines: string[] = [];
        lines.push(
          `total_dag_size=${report.totalDagSize}  pending_proposals=${report.filteredTotal}`,
        );
        if (report.filteredTotal === 0n) {
          lines.push("  (no self-euthanasia proposals; substrate's mortality_signal axes are stable)");
        } else {
          lines.push(`  M19-MV: proposals are informational (v0.9 keyless: execution is gated at the CI human-in-the-loop level, not by an owner co-signature)`);
        }
        for (const node of report.nodes) {
          const axisName = node.nodeType.replace(/^self_euthanasia_proposal:/, "");
          lines.push(
            `  [cycle ${node.atCycle}] axis="${axisName}"  hash=${toHex(node.hash).substring(0, 24)}…`,
          );
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
          isError: report.filteredTotal > 0n,
        };
      }
      case "myco_evolve_schema": {
        const sub = await this._ensureSubstrate();
        const op = String(args.op);
        const axisName = String(args.axis_name);
        // Build the schema_diff canonical bytes per op.
        const { schemaDiffModifyAxisThresholdBytes, schemaDiffAddAxisBytes } =
          await import("./protocol/messages.ts");
        let diffBytes: Uint8Array;
        if (op === "modify_axis_threshold") {
          if (args.new_threshold === undefined) {
            throw new Error("modify_axis_threshold requires new_threshold");
          }
          diffBytes = schemaDiffModifyAxisThresholdBytes(
            axisName,
            Number(args.new_threshold),
          );
        } else if (op === "add_axis_to_gradient") {
          if (
            args.axis_class === undefined ||
            args.fruiting_threshold === undefined ||
            args.initial_value === undefined ||
            args.decay_rate_per_cycle === undefined ||
            args.is_mortality_signal === undefined ||
            args.update_rule_kind === undefined
          ) {
            throw new Error(
              "add_axis_to_gradient requires axis_class, fruiting_threshold, initial_value, decay_rate_per_cycle, is_mortality_signal, update_rule_kind",
            );
          }
          diffBytes = schemaDiffAddAxisBytes({
            axisName,
            axisClass: String(args.axis_class) as "appetite" | "decay",
            fruitingThreshold: Number(args.fruiting_threshold),
            initialValue: Number(args.initial_value),
            decayRatePerCycle: Number(args.decay_rate_per_cycle),
            isMortalitySignal: Boolean(args.is_mortality_signal),
            updateRuleKind: String(args.update_rule_kind) as "noop" | "decay",
          });
        } else {
          throw new Error(`unknown evolve_schema op: ${op}`);
        }
        // v0.9 keyless: the owner Ed25519 attestation over the schema_diff was
        // removed with the anchor surface; the Python classifier accepts the
        // schema_evolution mutation on its type + content (the schema-apply
        // invariants + the two-phase migration window remain the safety gates).
        const migrationMode = Boolean(args.migration_mode);
        const result = await sub.submitMutation({
          mutationType: "schema_evolution",
          contentCanonicalBytes: diffBytes,
          touchedMetaStructures: ["appetite_axis_schema"],
          migrationMode,
        });
        const lines: string[] = [];
        lines.push(
          `mutation accepted=${result.accepted}  classification=${result.classification}`,
        );
        if (!result.accepted) {
          lines.push(`rejection: ${result.rejectionReason}`);
        }
        // v3.1.1 Sprint 8.G: two-phase migration outcome (when migration_mode).
        let migrationFailed = false;
        if (result.migrationMode) {
          if (result.candidateBuilt) {
            lines.push(
              `🔀 two-phase migration STARTED: candidate validating across the dual-validation window. ` +
                `Poll myco_query_migration_pending to watch progress; advance cycles to drive it. ` +
                `On window completion (candidate equivalent throughout) it commits; on divergence it rolls back.`,
            );
            if (result.schemaMigrationStartedEventHash) {
              lines.push(
                `schema_migration_started_event_hash=${toHex(result.schemaMigrationStartedEventHash).substring(0, 32)}…`,
              );
            }
          } else {
            migrationFailed = true;
            lines.push(
              `✗ two-phase migration ROLLED BACK immediately: candidate could not be built — ${result.schemaApplyFailureReason}`,
            );
          }
        } else if (result.schemaApplyAttempted) {
          if (result.schemaApplySucceeded) {
            lines.push(`✓ schema evolution APPLIED: ${result.schemaApplySummary}`);
            if (result.evolutionEventHash) {
              lines.push(
                `evolution_event_hash=${toHex(result.evolutionEventHash).substring(0, 32)}…`,
              );
            }
          } else {
            lines.push(`✗ schema evolution FAILED (rolled back): ${result.schemaApplyFailureReason}`);
          }
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
          isError:
            !result.accepted ||
            migrationFailed ||
            (result.schemaApplyAttempted && !result.schemaApplySucceeded),
        };
      }
      case "myco_ingest_raw_material": {
        const sub = await this._ensureSubstrate();
        const kind = String(args.content_kind);
        const contentStr = String(args.content);
        const contentBytes = new TextEncoder().encode(contentStr);
        const sourceUri =
          typeof args.source_uri === "string" ? String(args.source_uri) : undefined;
        const result = await sub.ingestRawMaterial({
          contentKind: kind,
          contentBytes,
          sourceUri,
        });
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `Ingested raw_material:${kind} (${contentBytes.length} bytes${sourceUri ? `, source=${sourceUri}` : ""})`,
                `dag_node_hash=${toHex(result.dagNodeHash)}`,
                `total_dag_size=${result.totalDagSize}`,
              ].join("\n"),
            },
          ],
        };
      }
      case "myco_perturb_axis_from_raw_material": {
        const sub = await this._ensureSubstrate();
        const axisName = String(args.axis_name);
        const delta = Number(args.delta);
        const rawMaterialHash = hexTo32(
          String(args.raw_material_hash_hex),
          "raw_material_hash_hex",
        );
        const result = await sub.perturbAxisFromRawMaterial({
          axisName,
          delta,
          rawMaterialHash,
        });
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `Perturbed "${axisName}" by ${delta} (causally linked to raw_material)`,
                `causal_link_hash=${toHex(result.causalLinkHash)}`,
                `raw_material_hash=${toHex(result.rawMaterialHash)}`,
              ].join("\n"),
            },
          ],
        };
      }
      case "myco_query_raw_material": {
        const sub = await this._ensureSubstrate();
        const count = args.count !== undefined ? BigInt(Number(args.count)) : 50n;
        const kindFilter =
          typeof args.kind_filter === "string" && args.kind_filter.length > 0
            ? `raw_material:${args.kind_filter}`
            : "raw_material:";
        const report = await sub.queryRecentNodes(count, kindFilter);
        const lines: string[] = [];
        lines.push(
          `total_dag_size=${report.totalDagSize}  matching=${report.filteredTotal}  returned=${report.returnedCount}`,
        );
        for (const node of report.nodes) {
          lines.push(
            `  [${node.atCycle}] ${node.nodeType}  hash=${toHex(node.hash).substring(0, 16)}…  size=${node.contentCanonicalBytes.length}B`,
          );
        }
        if (report.filteredTotal === 0n) {
          lines.push("  (no raw_material ingested yet)");
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
        };
      }
      case "myco_forge_understanding": {
        const sub = await this._ensureSubstrate();
        const label = String(args.label);
        const understandingStr = String(args.understanding);
        const understanding = new TextEncoder().encode(understandingStr);
        const sourceRawMaterialHashes = Array.isArray(
          args.source_raw_material_hashes,
        )
          ? (args.source_raw_material_hashes as unknown[]).map((h, i) =>
              hexTo32(String(h), `source_raw_material_hashes[${i}]`),
            )
          : [];
        const supersedes = Array.isArray(args.supersedes)
          ? (args.supersedes as unknown[]).map((h, i) =>
              hexTo32(String(h), `supersedes[${i}]`),
            )
          : [];
        const value =
          args.value === undefined || args.value === null
            ? undefined
            : Number(args.value);
        const confidence =
          args.confidence === undefined || args.confidence === null
            ? undefined
            : Number(args.confidence);
        const result = await sub.depositForgedUnderstanding({
          label,
          understanding,
          sourceRawMaterialHashes,
          value,
          confidence,
          supersedes,
        });
        const discernment = [
          value !== undefined ? `value=${value}` : null,
          confidence !== undefined ? `confidence=${confidence}` : null,
          supersedes.length > 0 ? `supersedes=${supersedes.length}` : null,
        ].filter((s): s is string => s !== null);
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `Forged understanding forged_understanding:${label} (${understanding.length} bytes${sourceRawMaterialHashes.length > 0 ? `, forged from ${sourceRawMaterialHashes.length} raw_material source${sourceRawMaterialHashes.length === 1 ? "" : "s"}` : ""}${discernment.length > 0 ? `; ${discernment.join(", ")}` : ""})`,
                `dag_node_hash=${toHex(result.dagNodeHash)}`,
                `total_dag_size=${result.totalDagSize}`,
              ].join("\n"),
            },
          ],
        };
      }
      case "myco_read_node_content": {
        const sub = await this._ensureSubstrate();
        const targetHash = hexTo32(String(args.node_hash_hex), "node_hash_hex");
        // Amplifier step 2: fetch the node by hash directly (O(1) dag.get, ANY node),
        // not by scanning the recent window — so a forged_understanding plate older
        // than the window is readable again instead of "may not exist".
        const node = await sub.readNodeByHash(targetHash);
        if (!node) {
          return {
            content: [
              {
                type: "text" as const,
                text: `Node ${toHex(targetHash).substring(0, 16)}… does not exist in the substrate's DAG.`,
              },
            ],
          };
        }
        const text = await renderNodeContentText(node);
        return {
          content: [{ type: "text" as const, text }],
        };
      }
      case "myco_recall": {
        const sub = await this._ensureSubstrate();
        const report = await sub.listPlates();
        const lines: string[] = [];
        lines.push(
          `Your map: ${report.livePlates} live plate${report.livePlates === 1n ? "" : "s"} (of ${report.totalPlates} forged; superseded excluded), sorted by importance:`,
        );
        if (report.plates.length === 0) {
          lines.push(
            "  (none yet — forge understanding with myco_forge_understanding)",
          );
        }
        for (const p of report.plates) {
          const v = p.value === null ? "—" : String(p.value);
          lines.push(`  [value ${v.padStart(3)}] ${p.label}  ${toHex(p.hash)}`);
        }
        lines.push(
          "",
          "Pick the plates relevant to your current task, then myco_read_node_content their hashes to read the full understanding.",
        );
        return { content: [{ type: "text" as const, text: lines.join("\n") }] };
      }
      case "myco_orient": {
        const sub = await this._ensureSubstrate();
        const report = await sub.listPlates();
        const lines: string[] = [];
        // (1) Surface the self-model first, if the pilot has forged one.
        const selfEntry = report.plates.find((p) => p.label === "myco-self-model");
        if (selfEntry) {
          const node = await sub.readNodeByHash(selfEntry.hash);
          if (node) {
            lines.push("==== WHO YOU ARE (your self-model) ====");
            lines.push(await renderNodeContentText(node));
            lines.push("");
          }
        } else {
          lines.push(
            '(No self-model yet. Once you know what this cultivar is, forge a plate labeled "myco-self-model" so future pilots are oriented instantly.)',
            "",
          );
        }
        // (2) The compact map of live plates.
        lines.push(
          `==== YOUR MAP (${report.livePlates} live plate${report.livePlates === 1n ? "" : "s"}, sorted by importance) ====`,
        );
        if (report.plates.length === 0) {
          lines.push(
            "  (none yet — forge understanding with myco_forge_understanding)",
          );
        }
        for (const p of report.plates) {
          const v = p.value === null ? "—" : String(p.value);
          lines.push(`  [value ${v.padStart(3)}] ${p.label}  ${toHex(p.hash)}`);
        }
        lines.push(
          "",
          "This is your accumulated mind. Read the plates relevant to your task with myco_read_node_content, and stand on them instead of re-deriving.",
        );
        return { content: [{ type: "text" as const, text: lines.join("\n") }] };
      }
      case "myco_query_forged_understanding": {
        const sub = await this._ensureSubstrate();
        const count = args.count !== undefined ? BigInt(Number(args.count)) : 50n;
        const report = await sub.queryRecentNodes(count, "forged_understanding:");
        const lines: string[] = [];
        lines.push(
          `total_dag_size=${report.totalDagSize}  matching=${report.filteredTotal}  returned=${report.returnedCount}`,
        );
        for (const node of report.nodes) {
          const label = node.nodeType.replace(/^forged_understanding:/, "");
          lines.push(
            `  [${node.atCycle}] forged_understanding:${label}  hash=${toHex(node.hash).substring(0, 16)}…  size=${node.contentCanonicalBytes.length}B`,
          );
        }
        if (report.filteredTotal === 0n) {
          lines.push("  (no forged_understanding deposited yet)");
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
        };
      }
      case "myco_enumerate_dag_since": {
        const sub = await this._ensureSubstrate();
        let prevTip: Uint8Array | undefined;
        if (typeof args.prev_tip_hex === "string" && args.prev_tip_hex.length > 0) {
          prevTip = hexTo32(String(args.prev_tip_hex), "prev_tip_hex");
        }
        const report = await sub.enumerateDagSince(prevTip);
        const verifyErrors = await SubstrateClient.verifyEnumeration(report);
        return {
          content: [
            {
              type: "text" as const,
              text: formatEnumeration(report, verifyErrors),
            },
          ],
          isError: verifyErrors.length > 0,
        };
      }
      case "myco_submit_mutation": {
        const sub = await this._ensureSubstrate();
        const mutationType = String(args.mutation_type);
        const contentStr = String(args.content);
        const contentBytes = new TextEncoder().encode(contentStr);
        const touchedFields = Array.isArray(args.touched_fields)
          ? (args.touched_fields as unknown[]).map((s) => String(s))
          : [];
        const touchedMeta = Array.isArray(args.touched_meta_structures)
          ? (args.touched_meta_structures as unknown[]).map((s) => String(s))
          : [];
        // v0.9 keyless: no owner Ed25519 attestation — the substrate classifies
        // the mutation on type + content (the anchor signing surface is gone).
        const result = await sub.submitMutation({
          mutationType,
          touchedFields,
          touchedMetaStructures: touchedMeta,
          contentCanonicalBytes: contentBytes,
        });
        return {
          content: [
            { type: "text" as const, text: formatMutation(result) },
          ],
          isError: !result.accepted,
        };
      }
      // v0.9 owner-key removal: the `myco_cosign_dag_tip` + `myco_attest_l0_revision`
      // handlers were removed with their tool defs (the substrate no longer
      // accepts the dag_tip_cosign / l0_revision_attest CI mutation types).
      case "myco_declare_owner_objective": {
        const sub = await this._ensureSubstrate();
        const objectiveId = String(args.objective_id);
        const declaredAtCycle =
          args.declared_at_cycle !== undefined
            ? BigInt(Number(args.declared_at_cycle))
            : 0n;
        const weights = Array.isArray(args.weights)
          ? (args.weights as unknown[]).map((w) => {
              const obj = (w ?? {}) as Record<string, unknown>;
              return {
                prefix: String(obj.prefix),
                weight: Number(obj.weight),
              };
            })
          : [];
        // Build the OwnerObjective canonical-bytes (byte-parity with Rust
        // encode_owner_objective; repr-float weights via floatRepr).
        const { buildOwnerObjectiveCanonicalBytes } = await import(
          "./protocol/messages.ts"
        );
        const contentCanonicalBytes = buildOwnerObjectiveCanonicalBytes({
          objectiveId,
          declaredAtCycle,
          weights,
        });
        // v0.9 keyless: the owner Ed25519 attestation + the M13 anchor nonce
        // were removed with the anchor surface; the substrate records the
        // owner_objective_declaration on accept (it is the P14.c telos-drift
        // reference centroid — content-validated, not signature-gated).
        const result = await sub.submitMutation({
          mutationType: "owner_objective_declaration",
          contentCanonicalBytes,
        });
        const lines: string[] = [];
        lines.push(
          `owner_objective accepted=${result.accepted}  classification=${result.classification}`,
        );
        if (!result.accepted) {
          lines.push(`rejection: ${result.rejectionReason}`);
        } else {
          lines.push(
            `owner_objective_declared:${objectiveId} (${weights.length} weight${weights.length === 1 ? "" : "s"}, declared_at_cycle=${declaredAtCycle})`,
          );
          if (result.dagNodeHash) {
            lines.push(
              `dag_node_hash=${toHex(result.dagNodeHash).substring(0, 32)}…`,
            );
          }
        }
        return {
          content: [{ type: "text" as const, text: lines.join("\n") }],
          isError: !result.accepted,
        };
      }
      case "myco_query_substrate_observatory": {
        const sub = await this._ensureSubstrate();
        const windowBytes =
          args.operator_attested_context_window_bytes !== undefined
            ? BigInt(Number(args.operator_attested_context_window_bytes))
            : undefined;
        const obs = await sub.querySubstrateObservatory({
          operatorAttestedContextWindowBytes: windowBytes,
        });
        return {
          content: [{ type: "text" as const, text: formatObservatory(obs) }],
        };
      }
      case "myco_query_substrate_id": {
        const sub = await this._ensureSubstrate();
        const substrateId = await sub.querySubstrateId();
        return {
          content: [
            {
              type: "text" as const,
              text: `substrate_id=${toHex(substrateId)}  (self-derived, immutable, binding for replay guards)`,
            },
          ],
        };
      }
      default:
        throw new Error(`unknown tool: ${name}`);
    }
  }

  /** Start the MCP server on stdio. Blocks until the transport closes. */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }

  /** Shutdown the substrate (if any) — useful for tests. */
  async dispose(): Promise<void> {
    if (this.substrate) {
      try {
        await this.substrate.shutdown();
      } catch {
        // Ignore.
      }
      this.substrate = null;
      this.substrateSpawnPromise = null;
    }
  }

  /** Direct dispatch — used by tests to bypass the JSON-RPC transport.
   *  Mirrors the wrapped CallToolRequestSchema handler's error-catching behavior. */
  async _testDispatch(
    name: string,
    args: Record<string, unknown>,
  ): Promise<{
    content: { type: "text"; text: string }[];
    isError?: boolean;
  }> {
    try {
      return await this._dispatchTool(name, args);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      return {
        content: [
          {
            type: "text" as const,
            text: `ERROR (${name}): ${message}`,
          },
        ],
        isError: true,
      };
    }
  }
}
