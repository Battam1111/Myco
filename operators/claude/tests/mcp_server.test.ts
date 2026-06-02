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
import { killAllSpawnedHosts } from "../src/anchor_surface_client.ts";

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

function locateAnchorSurfaceBinary(): string {
  const fromEnv = process.env.MYCO_ANCHOR_SURFACE_BIN;
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const root = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(root, "target", "debug", `anchor-surface-host${exe}`);
  if (!existsSync(candidate)) {
    throw new Error(
      `anchor-surface-host binary not found at ${candidate}; build with: cargo build -p anchor-surface-host`,
    );
  }
  return candidate;
}

const ANCHOR_SURFACE_BIN = locateAnchorSurfaceBinary();

// M-anchor-1: SubstrateClient.spawn (called internally by McpServer.dispose's
// underlying SubstrateClient lifecycle) falls back to OperatorIdentity.loadOrCreate()
// when no explicit identity is provided. loadOrCreate now requires an anchor-surface-host
// binary path. Set the env var so the fallback chain finds the binary built in
// target/debug/. Also point at an isolated default dir so the tests don't pollute
// (or read from) the user's ~/.myco/anchor_surface/. All hosts spawned by
// anchor_surface_client.ts are tracked module-level and killed in exit handlers.
const SHARED_ANCHOR_DIR_FOR_TESTS = mkdtempSync(
  resolvePath(tmpdir(), "myco-mcp-test-anchor-"),
);
process.env.MYCO_ANCHOR_SURFACE_BIN = ANCHOR_SURFACE_BIN;
process.env.MYCO_ANCHOR_SURFACE_DIR = SHARED_ANCHOR_DIR_FOR_TESTS;
process.once("exit", () => {
  try {
    rmSync(SHARED_ANCHOR_DIR_FOR_TESTS, { recursive: true, force: true });
  } catch {
    // Ignore.
  }
});

// File-level teardown: McpServer creates SubstrateClient instances which
// auto-load OperatorIdentity (now closed by SubstrateClient.shutdown). This
// hook is a belt-and-suspenders cleanup for any anchor-surface-host children
// not killed by the normal path — without it, leftover hosts hold stdio
// pipes that keep the Node event loop alive and the test process hangs.
after(async () => {
  await killAllSpawnedHosts();
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

  // M-anchor-5 §3.2 / §3.4 + P14 §3.2 owner-attestation tools.
  // These exercise the anchor-surface signing path through the MCP surface
  // (OperatorIdentity.loadOrCreate() picks up MYCO_ANCHOR_SURFACE_BIN, set
  // file-level above), mirroring the substrate_client.test.ts e2e suite.

  it("myco_cosign_dag_tip with no args cosigns the current tip + emits tip_cosigned:", async () => {
    const server = newServer();
    try {
      // Bare call: defaults tip_hash to the substrate's current DAG tip.
      const result = await server._testDispatch("myco_cosign_dag_tip", {});
      assert.ok(
        !result.isError,
        `bare cosign must succeed; got: ${result.content[0]!.text}`,
      );
      const text = result.content[0]!.text;
      assert.match(text, /cosign accepted=true/);
      assert.match(text, /classification=contract_identity_level/);
      assert.match(text, /tip_cosign_event_hash=/);

      // A tip_cosigned:* node must now be in the DAG.
      const nodes = await server._testDispatch("myco_query_recent_nodes", {
        count: 50,
      });
      assert.match(nodes.content[0]!.text, /tip_cosigned:/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_cosign_dag_tip accepts explicit tip + enumerated + proposed hashes", async () => {
    const server = newServer();
    try {
      // The substrate co-signs whatever envelope the owner attests; it does
      // not require the tip_hash to equal its live tip. Pass an explicit tip
      // plus enumerated-node + proposed-mutation hashes (mirrors the
      // substrate_client.test.ts "with-proposed-mutation" e2e) and assert the
      // envelope is accepted.
      const fill = (seed: number) => {
        const b = new Uint8Array(32);
        for (let i = 0; i < 32; i++) b[i] = (i * seed + seed) & 0xff;
        return Array.from(b)
          .map((x) => x.toString(16).padStart(2, "0"))
          .join("");
      };
      const result = await server._testDispatch("myco_cosign_dag_tip", {
        tip_hash_hex: fill(5),
        enumerated_node_hashes_hex: [fill(1), fill(3)],
        proposed_mutation_hash_hex: fill(7),
      });
      assert.ok(
        !result.isError,
        `cosign(explicit) must succeed; got: ${result.content[0]!.text}`,
      );
      assert.match(result.content[0]!.text, /cosign accepted=true/);
      assert.match(result.content[0]!.text, /tip_cosign_event_hash=/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_cosign_dag_tip with malformed (non-64) hex returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_cosign_dag_tip", {
        tip_hash_hex: "deadbeef", // 8 chars, not 64
      });
      assert.equal(result.isError, true);
      assert.match(result.content[0]!.text, /tip_hash_hex must be 64 hex chars/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_attest_l0_revision emits l0_revision_attested:", async () => {
    const server = newServer();
    try {
      const prior = "ab".repeat(32);
      const next = "cd".repeat(32);
      const result = await server._testDispatch("myco_attest_l0_revision", {
        prior_l0_hash_hex: prior,
        new_l0_hash_hex: next,
        diff_summary: "Add §9.4 federation observatory (mcp test)",
      });
      assert.ok(
        !result.isError,
        `l0 revision must succeed; got: ${result.content[0]!.text}`,
      );
      const text = result.content[0]!.text;
      assert.match(text, /l0_revision accepted=true/);
      assert.match(text, /classification=contract_identity_level/);
      assert.match(text, /l0_revision_event_hash=/);

      const nodes = await server._testDispatch("myco_query_recent_nodes", {
        count: 50,
      });
      assert.match(nodes.content[0]!.text, /l0_revision_attested:abababab/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_attest_l0_revision with malformed prior hash returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_attest_l0_revision", {
        prior_l0_hash_hex: "ab", // too short
        new_l0_hash_hex: "cd".repeat(32),
        diff_summary: "bad",
      });
      assert.equal(result.isError, true);
      assert.match(
        result.content[0]!.text,
        /prior_l0_hash_hex must be 64 hex chars/,
      );
    } finally {
      await server.dispose();
    }
  });

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
