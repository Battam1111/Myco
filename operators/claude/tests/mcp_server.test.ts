// McpServer dispatch tests — go through the MCP tool surface as Claude Code would.
//
// Uses the internal _testDispatch entry point (bypasses the stdio JSON-RPC
// transport) so we can drive the tool surface in-process.

import { after, describe, it } from "node:test";
import assert from "node:assert/strict";
import { resolve as resolvePath } from "node:path";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";

import { McpServer } from "../src/mcp_server.ts";

function locateSubstrateBinary(): string {
  const fromEnv = process.env.MYCO_SUBSTRATE_BIN;
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const root = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(root, "target", "debug", `myco-substrate${exe}`);
  if (!existsSync(candidate)) {
    throw new Error(
      `myco-substrate binary not found at ${candidate}; build with: cargo build -p myco-substrate`,
    );
  }
  return candidate;
}

const SUBSTRATE_BIN = locateSubstrateBinary();

// v0.9 keyless: no anchor-surface-host binary / operator-identity env. The
// SubstrateClient handshake completes on session_secret alone, so there are no
// anchor-surface child processes to track or reap. This `after` hook is a no-op
// placeholder kept for suite-shape stability.
after(async () => {
  // nothing to tear down (keyless).
});

function freshStateDir(): string {
  return mkdtempSync(resolvePath(tmpdir(), "myco-mcp-test-"));
}

function newServer(stateDir?: string): McpServer {
  const dir = stateDir ?? freshStateDir();
  return new McpServer({
    substrate: {
      substrateBinary: SUBSTRATE_BIN,
      env: { MYCO_STATE_DIR: dir },
    },
  });
}

function cleanupDir(dir: string): void {
  try {
    rmSync(dir, { recursive: true, force: true });
  } catch {
    // Ignore.
  }
}

describe("McpServer tool dispatch", () => {
  it("substrate_info reports versions", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("substrate_info", {});
      assert.equal(result.isError, undefined);
      const text = result.content[0]!.text;
      assert.match(text, /substrate_version: 0\.9/);
      assert.match(text, /kernel_tropism_version: 0\.9/);
      assert.match(text, /python_version: \d+\.\d+/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_register_axis + myco_snapshot roundtrip", async () => {
    const server = newServer();
    try {
      const reg = await server._testDispatch("myco_register_axis", {
        name: "kev",
        axis_class: "appetite",
        fruiting_threshold: 3.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      assert.equal(reg.isError, undefined);
      assert.match(reg.content[0]!.text, /Registered axis "kev"/);

      await server._testDispatch("myco_perturb_axis", {
        axis_name: "kev",
        delta: 1.5,
      });
      const snap = await server._testDispatch("myco_snapshot", {});
      assert.equal(snap.isError, undefined);
      assert.match(snap.content[0]!.text, /kev = 1\.5/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_advance_cycle fires sporocarp", async () => {
    const server = newServer();
    try {
      await server._testDispatch("myco_register_axis", {
        name: "fast_appetite",
        axis_class: "appetite",
        fruiting_threshold: 1.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      await server._testDispatch("myco_perturb_axis", {
        axis_name: "fast_appetite",
        delta: 2.0,
      });
      const result = await server._testDispatch("myco_advance_cycle", {
        current_cycle: 1,
      });
      assert.equal(result.isError, undefined);
      const text = result.content[0]!.text;
      assert.match(text, /fruited_axes=\[fast_appetite\]/);
      assert.match(text, /sporocarps=1/);
      assert.match(text, /appetite_fruiting/);
    } finally {
      await server.dispose();
    }
  });

  it("unknown tool returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("nonexistent_tool", {});
      assert.equal(result.isError, true);
      assert.match(result.content[0]!.text, /unknown tool/);
    } finally {
      await server.dispose();
    }
  });

  it("perturb unknown axis returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_perturb_axis", {
        axis_name: "ghost",
        delta: 1.0,
      });
      assert.equal(result.isError, true);
    } finally {
      await server.dispose();
    }
  });

  it("myco_shutdown_substrate works idempotently when not yet spawned", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_shutdown_substrate", {});
      assert.equal(result.isError, undefined);
      assert.match(result.content[0]!.text, /not yet spawned/);
    } finally {
      await server.dispose();
    }
  });

  // M8 NEW tools.
  it("myco_current_intent on near-fresh substrate has small/empty intent", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_current_intent", {
        radius_cycles: 5,
      });
      assert.equal(result.isError, undefined);
      // M21.1: even a "fresh" substrate has init events (genesis_event,
      // operator_pinned), so cold_start is no longer guaranteed true. But the
      // cluster count should still be small (no sporocarps/mutations).
      assert.match(result.content[0]!.text, /clusters=[01]/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_query_recent_nodes on near-fresh substrate lists init events", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_query_recent_nodes", {
        count: 10,
      });
      assert.equal(result.isError, undefined);
      // M21.1: fresh substrate has genesis_event (and operator_pinned if
      // operator identity was loaded). total_dag_size >= 1.
      assert.match(result.content[0]!.text, /total_dag_size=[1-9]/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_query_recent_nodes after sporocarp emission lists them", async () => {
    const server = newServer();
    try {
      await server._testDispatch("myco_register_axis", {
        name: "mcp_dag",
        axis_class: "appetite",
        fruiting_threshold: 1.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      await server._testDispatch("myco_perturb_axis", {
        axis_name: "mcp_dag",
        delta: 2.0,
      });
      await server._testDispatch("myco_advance_cycle", { current_cycle: 1 });
      const result = await server._testDispatch("myco_query_recent_nodes", {
        count: 50,
      });
      assert.equal(result.isError, undefined);
      // M21.1: DAG contains init + axis_registered + axis_perturbed +
      // cycle_advanced + sporocarp events. Check sporocarp node_type appears.
      assert.match(result.content[0]!.text, /sporocarp:appetite_fruiting/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_current_intent after sporocarps returns clusters", async () => {
    const server = newServer();
    try {
      await server._testDispatch("myco_register_axis", {
        name: "intent_mcp",
        axis_class: "appetite",
        fruiting_threshold: 1.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      for (let c = 1; c <= 3; c++) {
        await server._testDispatch("myco_perturb_axis", {
          axis_name: "intent_mcp",
          delta: 2.0,
        });
        await server._testDispatch("myco_advance_cycle", { current_cycle: c });
      }
      const result = await server._testDispatch("myco_current_intent", {
        radius_cycles: 10,
      });
      assert.equal(result.isError, undefined);
      // Result should contain non-cold-start intent text.
      assert.match(result.content[0]!.text, /cold_start=false/);
    } finally {
      await server.dispose();
    }
  });

  // **v0.9 owner-key removal**: the `myco_cosign_dag_tip` (§3.2) +
  // `myco_attest_l0_revision` (§3.4) tools were removed with the anchor surface
  // (the substrate no longer accepts the dag_tip_cosign / l0_revision_attest CI
  // mutation types), so their MCP-surface tests were deleted. `myco_declare_owner_objective`
  // survives keyless (the substrate classifies it by mutation_type + content).

  it("myco_declare_owner_objective accepts + emits owner_objective_declared:{id}", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_declare_owner_objective", {
        objective_id: "mcp_e2e_objective",
        weights: [
          { prefix: "axis_perturbed:", weight: 0.75 },
          { prefix: "raw_material:", weight: 0.25 },
        ],
      });
      assert.ok(
        !result.isError,
        `owner objective must accept; got: ${result.content[0]!.text}`,
      );
      const text = result.content[0]!.text;
      assert.match(text, /owner_objective accepted=true/);
      assert.match(text, /classification=contract_identity_level/);
      assert.match(text, /owner_objective_declared:mcp_e2e_objective/);

      const nodes = await server._testDispatch("myco_query_recent_nodes", {
        count: 50,
      });
      assert.match(
        nodes.content[0]!.text,
        /owner_objective_declared:mcp_e2e_objective/,
      );
    } finally {
      await server.dispose();
    }
  });

  it("myco_declare_owner_objective with empty weights returns isError (C5)", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_declare_owner_objective", {
        objective_id: "empty_weights",
        weights: [],
      });
      assert.equal(
        result.isError,
        true,
        "empty-weights owner objective must be rejected",
      );
      assert.match(result.content[0]!.text, /weights array MUST be non-empty/i);
    } finally {
      await server.dispose();
    }
  });
});
