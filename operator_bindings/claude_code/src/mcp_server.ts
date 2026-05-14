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
import type { AdvanceReport } from "./protocol/messages.ts";

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
