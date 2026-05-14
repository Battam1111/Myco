// MCP server — exposes substrate operations to Claude Code as MCP tools.
//
// This is the L4 M6 operator_bindings/<claude_code> binding per
// L3_PACKAGE_MAP §11. It maps Claude Code's MCP tool-call surface to the
// substrate's M5/M6 wire protocol.
//
// ## Tool surface (M6 v1)
//
// 6 tools exposed to Claude Code:
//
// 1. `myco_register_axis` — register a gradient axis (one-time per axis).
// 2. `myco_perturb_axis` — apply a delta to an axis (operator-initiated input).
// 3. `myco_advance_cycle` — run one metabolic cycle; returns sporocarps.
// 4. `myco_snapshot` — read current axis values.
// 5. `myco_substrate_info` — return substrate + python versions (handshake echo).
// 6. `myco_shutdown_substrate` — gracefully end the substrate (terminates session).
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
  RecentNodesReport,
} from "./protocol/messages.ts";
import { OperatorIdentity } from "./operator_identity.ts";

/** Configuration for the MCP server. */
export interface McpServerConfig {
  substrate?: SubstrateClientConfig;
}

/** Convert a Uint8Array to a hex string for tool responses. */
function toHex(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
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
          description: "Whether this axis is the substrate's mortality signal (CI-protected per L1_HARD_RULES F7)",
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
    name: "myco_substrate_info",
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
  {
    name: "myco_request_attestation_nonce",
    description:
      "Request an anchor-surface attestation nonce (M13). The substrate issues a 32-byte nonce bound to the SHA-256 of your proposed mutation content + the current DAG tip. Include this nonce in your subsequent myco_submit_mutation call (with the same content) to prove a fresh, non-replay intent. Nonces expire after 5 minutes and are one-time use. Returns: nonce, expiry_unix_ns, bound_dag_tip (all hex-encoded).",
    inputSchema: {
      type: "object",
      properties: {
        content: {
          type: "string",
          description:
            "The mutation content you intend to submit (UTF-8); the nonce is bound to its SHA-256 hash",
        },
      },
      required: ["content"],
    },
  },
  {
    name: "myco_run_immune_check",
    description:
      "Trigger an ad-hoc immune verification scan. The substrate runs comprehensive integrity checks (substrate_id well-formedness, DAG hash chain integrity, cycle counter monotonicity, pinned operator pubkey well-formedness, owner_keys consistency). For each failed check, the substrate emits a C9 cold_resume_invariant_failure immune sporocarp (visible via myco_query_immune_events). Returns a per-check report.",
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
    name: "myco_query_self_euthanasia_proposals",
    description:
      "P7 必朽 (Endogenous-pair Mortality): List the substrate's pending `self_euthanasia_proposal:*` DAG nodes. These are emitted automatically when a mortality_signal axis fruits (crosses its decay threshold) — the substrate proposing its own end. Per L0 P7, executing the proposal requires owner co-attestation (the pair has agency over its ending; owner retains veto). M19-MV: proposals are informational; M20+ will add owner co-attestation execution. Each entry includes the axis_name, fruiting_value, at_cycle, and triggering_sporocarp_hash.",
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
    name: "myco_enumerate_dag_since",
    description:
      "Enumerate DAG node hashes added since a given prev_tip (or from genesis if omitted), with full per-node metadata so the caller can independently reconstruct the substrate's Merkle chain (L1_HARD_RULES C6 dag_enumeration_unclosed closure). The substrate cannot hide parallel-branch forgery: every node's BLAKE3 hash is recomputed from declared parents+content and compared. On unknown prev_tip the substrate emits a C6 immune sporocarp. Returns: enumerated_count, current_tip, hash-chain verification result, and per-node summaries.",
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
      "Submit a mutation for the substrate to classify and (for contract-identity-level mutations) verify owner attestation. The substrate classifies via L1_GOVERNANCE rules: daily mutations are auto-accepted; CI mutations require owner attestation; untyped mutations are rejected. Accepted mutations are recorded as DAG nodes (causal history preserved). Rejected mutations trigger immune sporocarp emission (visible via myco_query_immune_events).",
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
        require_attestation: {
          type: "boolean",
          description:
            "When true, the operator's identity key (M9) signs the content as the owner attestation (for M10 operator==owner)",
        },
      },
      required: ["mutation_type", "content"],
    },
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
        version: "0.9.0-alpha.1",
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
      case "myco_substrate_info": {
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
      case "myco_request_attestation_nonce": {
        const sub = await this._ensureSubstrate();
        const contentStr = String(args.content);
        const contentBytes = new TextEncoder().encode(contentStr);
        const result = await sub.requestAttestationNonce(contentBytes);
        return {
          content: [
            {
              type: "text" as const,
              text: [
                `nonce=${toHex(result.nonce)}`,
                `bound_dag_tip=${toHex(result.boundDagTip)}`,
                `expiry_unix_ns=${result.expiryUnixNs}`,
                `ttl_seconds=${result.ttlSeconds}`,
                "(use this nonce in myco_submit_mutation with the SAME content)",
              ].join("\n"),
            },
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
          lines.push(`  M19-MV: proposals are informational; owner co-attestation execution is M20+`);
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
        // Operator IDENTITY signs the schema_diff bytes (M10 path; M17-MV
        // accepts both REVEAL and IDENTITY signatures via classifier rule).
        const identity = OperatorIdentity.loadOrCreate();
        const sig = identity.sign(diffBytes);
        const result = await sub.submitMutation({
          mutationType: "schema_evolution",
          contentCanonicalBytes: diffBytes,
          attestationSignature: sig,
          touchedMetaStructures: ["appetite_axis_schema"],
        });
        const lines: string[] = [];
        lines.push(
          `mutation accepted=${result.accepted}  classification=${result.classification}`,
        );
        if (!result.accepted) {
          lines.push(`rejection: ${result.rejectionReason}`);
        }
        if (result.schemaApplyAttempted) {
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
          isError: !result.accepted || (result.schemaApplyAttempted && !result.schemaApplySucceeded),
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
        const hex = String(args.raw_material_hash_hex);
        if (hex.length !== 64) {
          throw new Error(
            `raw_material_hash_hex must be 64 hex chars (32 bytes); got ${hex.length}`,
          );
        }
        const rawMaterialHash = new Uint8Array(32);
        for (let i = 0; i < 32; i++) {
          rawMaterialHash[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
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
      case "myco_enumerate_dag_since": {
        const sub = await this._ensureSubstrate();
        let prevTip: Uint8Array | undefined;
        if (typeof args.prev_tip_hex === "string" && args.prev_tip_hex.length > 0) {
          const hex = String(args.prev_tip_hex);
          if (hex.length !== 64) {
            throw new Error(
              `prev_tip_hex must be 64 hex chars (32 bytes); got ${hex.length}`,
            );
          }
          prevTip = new Uint8Array(32);
          for (let i = 0; i < 32; i++) {
            prevTip[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
          }
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
        let attestationSignature: Uint8Array | undefined;
        if (args.require_attestation === true) {
          // Sign the content with the operator's M9 identity key (which doubles
          // as the genesis owner key for M10 minimum).
          const identity = OperatorIdentity.loadOrCreate();
          attestationSignature = identity.sign(contentBytes);
        }
        const result = await sub.submitMutation({
          mutationType,
          touchedFields,
          touchedMetaStructures: touchedMeta,
          contentCanonicalBytes: contentBytes,
          attestationSignature,
        });
        return {
          content: [
            { type: "text" as const, text: formatMutation(result) },
          ],
          isError: !result.accepted,
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
